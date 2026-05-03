from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np


# =============================================================================
# 1. PRE-CALCOLO ARRAY NUMPY  (identico helper di Greedy per coerenza)
# =============================================================================

def _make_numpy_views(
    data: dict,
    r: str,
    X_r: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Restituisce (dist_np, time_np, Q_arr, TC_arr) come float64.

    - ``dist_np``  shape (n_nodes, n_nodes) — distanze shortest-path (km)
    - ``time_np``  shape (n_nodes, n_nodes) — tempi shortest-path (min)
    - ``Q_arr``    shape (n_nodes,)         — carico stimato per passaggio (kg);
                                              indice 0 = deposito → 0
    - ``TC_arr``   shape (n_nodes,)         — tempo di carico (min);
                                              indice 0 = deposito → 0
    """
    n       = data["n_users"]
    dist_np = data["dist_matrix"].astype(np.float64)
    time_np = data["time_matrix"].astype(np.float64)

    user_types = data["user_types"]   # ndarray dtype=object dopo M5
    W          = data["W"]
    tc         = data["tc"]

    Q_arr  = np.zeros(n + 1, dtype=np.float64)
    TC_arr = np.zeros(n + 1, dtype=np.float64)

    for u in range(1, n + 1):
        t_u       = user_types[u - 1]
        Q_arr[u]  = W[(r, t_u)] / X_r
        TC_arr[u] = tc[(r, t_u)]

    return dist_np, time_np, Q_arr, TC_arr


# =============================================================================
# 2. BUILD ROUTES — Clarke-Wright Savings
# =============================================================================

def build_routes(data: dict, r: str, X_r: float) -> dict:
    """Costruisce i percorsi con l'algoritmo Clarke-Wright (Savings).

    Parameters
    ----------
    data:
        Dizionario restituito da ``generate_mock_data``.
    r:
        Tipologia di rifiuto (es. ``"organico"``).
    X_r:
        Frequenza settimanale programmata (ritiri/settimana).

    Returns
    -------
    dict con chiavi ``routes``, ``n_vehicles``, ``loads``, ``times``.
    Formato identico all'output di ``Greedy.build_routes``.

    Algorithm
    ---------
    Fase 1 — Soluzione iniziale
        Un camion dedicato per ogni utente fattibile:
        ``deposito → u → deposito``.

    Fase 2 — Matrice Savings vettorizzata  O(N²) NumPy
        ``S_ij = c_fixed_r + cd*(d_i0+d_0j-d_ij) + cm*(tv_i0+tv_0j-tv_ij)``

        Il termine ``c_fixed_r`` estende il CW classico: ogni fusione elimina
        un camion, risparmiando anche il suo costo fisso di attivazione.

    Fase 3 — Ordinamento  O(N² log N)  (argsort NumPy su array flat)

    Fase 4 — Ciclo di fusione  O(E) iterazioni, check O(1) via dizionari
        Per ogni coppia (i, j) in ordine decrescente di saving:
        - ``route_id[u]``    → id route corrente di u          O(1)
        - ``route_tail[rid]``→ ultimo utente della route rid   O(1)
        - ``route_head[rid]``→ primo utente della route rid    O(1)
        - ``route_load[rid]``→ carico totale della route rid   O(1)
        - ``route_time[rid]``→ tempo totale della route rid    O(1)
        Fusione approvata → aggiornamento O(|route_j|) per riassegnare
        ``route_id`` dei nodi assorbiti (costo inevitabile).
    """
    if X_r <= 0:
        raise ValueError(f"X_r deve essere > 0, ricevuto {X_r}")

    n_users   = data["n_users"]
    C_r       = data["C"][r]
    L         = data["L"]
    c_fixed_r = data["c_fixed"][r]
    cd        = data["cd"]
    cm        = data["cm"]

    dist_np, time_np, Q_arr, TC_arr = _make_numpy_views(data, r, X_r)

    # nodi utente: 1 … n_users  (0 = deposito)
    user_nodes = np.arange(1, n_users + 1, dtype=np.int32)

    # ── Fase 1: soluzione iniziale — un camion per utente ─────────────────────
    #
    # Strutture dati O(1) per il ciclo di fusione:
    #
    #   route_nodes[rid]  → lista ordinata dei nodi utente della route
    #                        (esclude il deposito: lo aggiungiamo solo in output)
    #   route_head[rid]   → primo utente della route  (per regola estremi)
    #   route_tail[rid]   → ultimo utente della route (per regola estremi)
    #   route_load[rid]   → carico totale (kg)
    #   route_time[rid]   → tempo totale inclusi ritorni al deposito (min)
    #   route_id[u]       → a quale route appartiene l'utente u
    #
    # rid è semplicemente un intero incrementale; le route eliminate vengono
    # marcate con route_alive[rid] = False invece di cancellarle dal dict
    # (cancellare richiederebbe di aggiornare route_id per tutti i nodi).

    route_nodes: dict[int, list[int]] = {}
    route_head:  dict[int, int]       = {}
    route_tail:  dict[int, int]       = {}
    route_load:  dict[int, float]     = {}
    route_time:  dict[int, float]     = {}
    route_alive: dict[int, bool]      = {}
    route_id:    dict[int, int]       = {}   # utente → rid

    # Pre-calcolo vettorizzato dei tempi base  dep→u→dep
    t_base = time_np[0, user_nodes] + TC_arr[user_nodes] + time_np[user_nodes, 0]

    feasible_mask = (Q_arr[user_nodes] <= C_r) & (t_base <= L)
    feasible_nodes = user_nodes[feasible_mask]

    if feasible_nodes.size == 0:
        print(f"[WARN] nessun utente fattibile per '{r}', X_r={X_r}")
        return {"routes": [], "n_vehicles": 0, "loads": [], "times": []}

    for rid, u in enumerate(feasible_nodes.tolist()):
        u = int(u)
        route_nodes[rid] = [u]
        route_head[rid]  = u
        route_tail[rid]  = u
        route_load[rid]  = float(Q_arr[u])
        route_time[rid]  = float(t_base[feasible_mask][list(feasible_nodes).index(u)]
                                  if False else   # evita doppio giro
                                  time_np[0, u] + TC_arr[u] + time_np[u, 0])
        route_alive[rid] = True
        route_id[u]      = rid

    # ── Fase 2: matrice Savings — tutto NumPy, zero loop Python ───────────────
    #
    # Lavoriamo su feasible_nodes (indici 0…F-1 nella sotto-matrice).
    # Mappiamo gli indici originali di nodo ↔ indice locale con un array.
    fn   = feasible_nodes                        # shape (F,)
    F    = len(fn)

    # Vettori 1-D  (F,)
    d_i0  = dist_np[fn, 0]                       # distanza utente → deposito
    d_0j  = dist_np[0, fn]                       # distanza deposito → utente
    tv_i0 = time_np[fn, 0]
    tv_0j = time_np[0, fn]

    # Sotto-matrici  (F, F)  — accesso diretto alla matrice shortest-path
    d_ij  = dist_np[np.ix_(fn, fn)]              # (F, F)
    tv_ij = time_np[np.ix_(fn, fn)]              # (F, F)

    # Savings matrix  S[a,b] = saving di unire fine(route_a) con inizio(route_b)
    # Broadcasting: (F,1) op (1,F) → (F,F)
    S = (c_fixed_r
         + cd  * (d_i0[:, None] + d_0j[None, :] - d_ij)
         + cm  * (tv_i0[:, None] + tv_0j[None, :] - tv_ij))

    # S_ii è priva di senso (auto-fusione) — la azzeriamo a -inf
    np.fill_diagonal(S, -np.inf)

    # ── Fase 3: ordinamento decrescente O(F² log F) ───────────────────────────
    flat      = S.ravel()                              # view, no copia
    order     = np.argsort(flat)[::-1]                 # indici dal saving maggiore
    rows_s, cols_s = np.unravel_index(order, (F, F))   # (F²,) coppie (a, b)

    # Scarta subito i saving non positivi: non portano mai a una fusione utile.
    # np.searchsorted trova il cut-off in O(log F²).
    flat_sorted = flat[order]
    cut = int(np.searchsorted(-flat_sorted, 0))        # primo indice con saving ≤ 0
    rows_s = rows_s[:cut]
    cols_s = cols_s[:cut]

    # ── Fase 4: ciclo di fusione O(E) con check O(1) ──────────────────────────
    #
    # fn[a] e fn[b] sono i nodi originali corrispondenti agli indici locali a, b.

    next_rid = F   # id per eventuali route create dalla fusione

    for a, b in zip(rows_s.tolist(), cols_s.tolist()):

        node_i = int(fn[a])   # candidato "coda" (ultimo della sua route)
        node_j = int(fn[b])   # candidato "testa" (primo della sua route)

        rid_i = route_id.get(node_i)
        rid_j = route_id.get(node_j)

        # Guard: uno dei due nodi potrebbe essere stato assorbito e rimosso
        if rid_i is None or rid_j is None:
            continue

        # CHECK 1 — route diverse (no cicli)
        if rid_i == rid_j:
            continue

        # CHECK 2 — regola degli estremi  O(1)
        #   node_i deve essere l'ULTIMO utente della sua route
        #   node_j deve essere il PRIMO utente della sua route
        if route_tail[rid_i] != node_i:
            continue
        if route_head[rid_j] != node_j:
            continue

        # CHECK 3 — capacità  O(1)
        new_load = route_load[rid_i] + route_load[rid_j]
        if new_load > C_r:
            continue

        # CHECK 4 — tempo  O(1)
        #   Tempo fusione = tempo_i + tempo_j
        #                   - archi eliminati (tail_i→dep, dep→head_j)
        #                   + arco aggiunto   (tail_i→head_j)
        new_time = (route_time[rid_i] + route_time[rid_j]
                    - time_np[node_i, 0]     # rimuovo ritorno di i al dep
                    - time_np[0, node_j]     # rimuovo partenza di j dal dep
                    + time_np[node_i, node_j])  # aggiungo arco diretto i→j
        if new_time > L:
            continue

        # ── FUSIONE APPROVATA ─────────────────────────────────────────────────
        #
        # Creiamo una nuova route  rid_new = rid_i + rid_j concatenati.
        # Usiamo un rid fresco per non dover "pulire" i vecchi dict.
        rid_new = next_rid
        next_rid += 1

        merged_nodes = route_nodes[rid_i] + route_nodes[rid_j]

        route_nodes[rid_new]  = merged_nodes
        route_head[rid_new]   = route_head[rid_i]
        route_tail[rid_new]   = route_tail[rid_j]
        route_load[rid_new]   = new_load
        route_time[rid_new]   = new_time
        route_alive[rid_new]  = True

        # Aggiorna route_id per tutti i nodi della route assorbita — O(|route_j|)
        # (unico costo lineare, inevitabile)
        for u in merged_nodes:
            route_id[u] = rid_new

        # Marca le vecchie route come morte
        route_alive[rid_i] = False
        route_alive[rid_j] = False

    # ── Fase 5: raccolta risultati ─────────────────────────────────────────────
    final_routes: list[list[int]] = []
    final_loads:  list[float]     = []
    final_times:  list[float]     = []

    seen_rids: set[int] = set()
    for u in feasible_nodes.tolist():
        rid = route_id[int(u)]
        if rid in seen_rids or not route_alive[rid]:
            continue
        seen_rids.add(rid)
        final_routes.append([0] + route_nodes[rid] + [0])
        final_loads.append(route_load[rid])
        final_times.append(route_time[rid])

    return {
        "routes":     final_routes,
        "n_vehicles": len(final_routes),
        "loads":      final_loads,
        "times":      final_times,
    }


# =============================================================================
# 3. COMPUTE OBJECTIVE  (identico a Greedy.compute_objective — stessa firma)
# =============================================================================

def compute_objective(data: dict, r: str, X_r: float, routes_result: dict) -> dict:
    """Calcola la funzione obiettivo SPIL dato un set di route.

    Firma e output identici a ``Greedy.compute_objective`` per garantire
    intercambiabilità nei confronti di benchmarking.
    """
    n_users    = data["n_users"]
    user_types = data["user_types"]
    x_star     = data["x_star"]
    alpha      = data["alpha"]
    beta       = data["beta"]
    cd         = data["cd"]
    cm         = data["cm"]
    c_fixed_r  = data["c_fixed"][r]
    n_vehicles = routes_result["n_vehicles"]
    routes     = routes_result["routes"]
    times      = routes_result["times"]

    dist_np = data["dist_matrix"].astype(np.float64)

    # Insoddisfazione
    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u   = user_types[u_idx]
        x_s   = x_star[(r, t_u)]
        delta = X_r - x_s
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta

    # Costo fisso
    F_costo_fisso = c_fixed_r * n_vehicles * X_r

    # Costo di viaggio — vettorizzato su ogni route
    travel_cost_one_turn = 0.0
    for route in routes:
        arr = np.array(route, dtype=np.int32)
        travel_cost_one_turn += float(np.sum(dist_np[arr[:-1], arr[1:]]))

    F_viaggio = X_r * cd * travel_cost_one_turn
    F_lavoro  = X_r * cm * sum(times)
    F_total   = F_insoddis + F_costo_fisso + F_viaggio + F_lavoro

    return {
        "F_total":      F_total,
        "F_insoddis":   F_insoddis,
        "F_costo_fisso": F_costo_fisso,
        "F_viaggio":    F_viaggio,
        "F_lavoro":     F_lavoro,
    }


# =============================================================================
# 4. WORKER E GRID SEARCH  (stessa firma di Greedy.grid_search)
# =============================================================================

def _evaluate_one(args: tuple) -> dict | None:
    """Worker per ProcessPoolExecutor: valuta un singolo (r, X_r)."""
    data, r, X_r = args
    routes_result = build_routes(data, r, X_r)

    if routes_result["n_vehicles"] == 0:
        return None

    obj = compute_objective(data, r, X_r, routes_result)

    return {
        "X_r":        X_r,
        "routes":     routes_result,
        "n_vehicles": routes_result["n_vehicles"],
        **obj,
    }


def grid_search(
    data: dict,
    r: str,
    X_values: list[float],
    *,
    max_workers: int | None = None,
    parallel_threshold: int = 6,
) -> dict:
    """Grid search su X_values per il rifiuto ``r`` con Clarke-Wright.

    Firma identica a ``Greedy.grid_search`` per completa intercambiabilità.

    Parameters
    ----------
    data:
        Output di ``generate_mock_data``.
    r:
        Tipologia di rifiuto.
    X_values:
        Lista di frequenze settimanali da testare.
    max_workers:
        Numero di processi paralleli (``None`` = auto).
    parallel_threshold:
        Soglia minima di ``len(X_values)`` per attivare il parallelismo.

    Returns
    -------
    dict con chiavi ``best_X_r``, ``best_F``, ``best_routes``, ``all_results``.
    """
    best_X_r    = None
    best_F      = None
    best_routes = None
    best_total  = float("inf")
    all_results: list[dict] = []

    use_parallel = len(X_values) >= parallel_threshold

    if use_parallel:
        args_list = [(data, r, X_r) for X_r in X_values]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_X = {
                executor.submit(_evaluate_one, args): args[2]
                for args in args_list
            }
            for future in as_completed(future_to_X):
                result = future.result()
                if result is None:
                    continue
                all_results.append(result)
                if result["F_total"] < best_total:
                    best_total  = result["F_total"]
                    best_X_r    = result["X_r"]
                    best_F      = {k: result[k] for k in (
                        "F_total", "F_insoddis", "F_costo_fisso",
                        "F_viaggio", "F_lavoro"
                    )}
                    best_routes = result["routes"]
        all_results.sort(key=lambda d: d["X_r"])

    else:
        for X_r in X_values:
            result = _evaluate_one((data, r, X_r))
            if result is None:
                continue
            all_results.append(result)
            if result["F_total"] < best_total:
                best_total  = result["F_total"]
                best_X_r    = result["X_r"]
                best_F      = {k: result[k] for k in (
                    "F_total", "F_insoddis", "F_costo_fisso",
                    "F_viaggio", "F_lavoro"
                )}
                best_routes = result["routes"]

    return {
        "best_X_r":    best_X_r,
        "best_F":      best_F,
        "best_routes": best_routes,
        "all_results": all_results,
    }