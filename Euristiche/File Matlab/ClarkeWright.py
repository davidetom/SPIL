from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np


# =============================================================================
# 1. PRE-CALCOLO ARRAY NUMPY
# =============================================================================

def _make_numpy_views(
    data: dict,
    r: str,
    X_r: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n          = data["n_users"]
    dist_np    = data["dist_matrix"].astype(np.float32)
    time_np    = data["time_matrix"].astype(np.float32)
    user_types = data["user_types"]
    W          = data["W"]
    tc         = data["tc"]

    Q_arr  = np.zeros(n + 1, dtype=np.float32)
    TC_arr = np.zeros(n + 1, dtype=np.float32)

    for u in range(1, n + 1):
        t_u       = user_types[u - 1]
        Q_arr[u]  = W[(r, t_u)] / X_r
        TC_arr[u] = tc[(r, t_u)]

    return dist_np, time_np, Q_arr, TC_arr


# =============================================================================
# 2. BUILD ROUTES
# =============================================================================

def build_routes(data: dict, r: str, X_r: float) -> dict:
    """Clarke-Wright con savings statici, argsort flat e check O(1).

    Paradigma
    ---------
    La matrice dei savings viene calcolata UNA SOLA VOLTA sui nodi fattibili
    prima di qualsiasi fusione.  E' matematicamente equivalente al ricalcolo
    dinamico perche' il saving tra i e j dipende solo dalle distanze nel grafo,
    che sono fisse.  Cio' che cambia ad ogni iterazione e' solo il RUOLO dei
    nodi (estremo o interno), controllato in O(1) dai dizionari.

    Struttura
    ---------
    Fase 1  O(F)          Rotte singleton + dizionari O(1).
    Fase 2  O(F^2 NumPy)  Matrice savings vettorizzata.
    Fase 3  O(F^2 log F)  argsort flat decrescente; taglio savings <= 0.
    Fase 4  O(F^2) worst  Ciclo: CHECK 1-4 in O(1), fusione in O(|rotta_j|).

    Lazy deletion
    -------------
    Non serve un set valid_pairs separato.  I CHECK 1 e 2 fungono da lazy
    deletion naturale: se node_i o node_j sono finiti all'interno di una rotta
    in una fusione precedente, route_tail/route_head non puntano piu' a loro
    e la coppia viene scartata in O(1).
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
    user_nodes = np.arange(1, n_users + 1, dtype=np.int32)

    # ── Fase 1: soluzione iniziale ────────────────────────────────────────────

    t_base        = time_np[0, user_nodes] + TC_arr[user_nodes] + time_np[user_nodes, 0]
    feasible_mask = (Q_arr[user_nodes] <= C_r) & (t_base <= L)
    feasible_nodes = user_nodes[feasible_mask]
    t_base_feas    = t_base[feasible_mask]

    if feasible_nodes.size == 0:
        print(f"[WARN] nessun utente fattibile per '{r}', X_r={X_r}")
        return {"routes": [], "n_vehicles": 0, "loads": [], "times": []}

    F  = int(feasible_nodes.size)
    fn = feasible_nodes

    route_nodes: dict[int, list[int]] = {}
    route_head:  dict[int, int]       = {}
    route_tail:  dict[int, int]       = {}
    route_load:  dict[int, float]     = {}
    route_time:  dict[int, float]     = {}
    route_of:    dict[int, int]       = {}   # nodo -> rid corrente

    for local_idx in range(F):
        u   = int(fn[local_idx])
        rid = local_idx
        route_nodes[rid] = [u]
        route_head[rid]  = u
        route_tail[rid]  = u
        route_load[rid]  = float(Q_arr[u])
        route_time[rid]  = float(t_base_feas[local_idx])
        route_of[u]      = rid

    rid_next = F

    # ── Fase 2: matrice savings vettorizzata ──────────────────────────────────
    #
    # S[a, b] = saving di fondere la rotta il cui tail e' fn[a]
    #           con la rotta il cui head e' fn[b].
    # La matrice e' asimmetrica: S[a,b] != S[b,a] in generale.

    d_i0  = dist_np[fn, 0][:, None]
    d_0j  = dist_np[0,  fn][None, :]
    d_ij  = dist_np[np.ix_(fn, fn)]

    tv_i0 = time_np[fn, 0][:, None]
    tv_0j = time_np[0,  fn][None, :]
    tv_ij = time_np[np.ix_(fn, fn)]

    S = (c_fixed_r
         + cd * (d_i0 + d_0j - d_ij)
         + cm * (tv_i0 + tv_0j - tv_ij))

    np.fill_diagonal(S, -np.inf)

    # ── Fase 3: ordinamento flat decrescente con un solo argsort ─────────────

    flat   = S.ravel()
    order  = np.argsort(flat)[::-1]
    cutoff = int(np.searchsorted(-flat[order], 0))
    order  = order[:cutoff]

    rows = (order // F).tolist()
    cols = (order  % F).tolist()

    # ── Fase 4: ciclo di fusione ──────────────────────────────────────────────

    for a, b in zip(rows, cols):

        node_i = int(fn[a])
        node_j = int(fn[b])

        rid_i = route_of[node_i]
        rid_j = route_of[node_j]

        # CHECK 1 — rotte diverse
        if rid_i == rid_j:
            continue

        # CHECK 2 — regola degli estremi (lazy deletion implicita)
        if route_tail[rid_i] != node_i or route_head[rid_j] != node_j:
            continue

        # CHECK 3 — capacita'
        new_load = route_load[rid_i] + route_load[rid_j]
        if new_load > C_r:
            continue

        # CHECK 4 — tempo
        new_time = (route_time[rid_i] + route_time[rid_j]
                    - time_np[node_i, 0]
                    - time_np[0, node_j]
                    + time_np[node_i, node_j])
        if new_time > L:
            continue

        # ── FUSIONE APPROVATA ─────────────────────────────────────────────────

        rid_c  = rid_next
        rid_next += 1
        merged = route_nodes[rid_i] + route_nodes[rid_j]

        route_nodes[rid_c] = merged
        route_head[rid_c]  = route_head[rid_i]
        route_tail[rid_c]  = route_tail[rid_j]
        route_load[rid_c]  = new_load
        route_time[rid_c]  = float(new_time)

        for u in merged:
            route_of[u] = rid_c

    # ── Fase 5: raccolta risultati ─────────────────────────────────────────────

    final_routes: list[list[int]] = []
    final_loads:  list[float]     = []
    final_times:  list[float]     = []

    seen_rids: set[int] = set()
    for u in fn.tolist():
        rid = route_of[int(u)]
        if rid in seen_rids:
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
# 3. COMPUTE OBJECTIVE
# =============================================================================

def compute_objective(data: dict, r: str, X_r: float, routes_result: dict) -> dict:
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

    dist_np = data["dist_matrix"].astype(np.float32)

    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u   = user_types[u_idx]
        x_s   = x_star[(r, t_u)]
        delta = X_r - x_s
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta

    F_costo_fisso = c_fixed_r * n_vehicles * X_r

    travel_cost_one_turn = 0.0
    for route in routes:
        arr = np.array(route, dtype=np.int32)
        travel_cost_one_turn += float(np.sum(dist_np[arr[:-1], arr[1:]]))

    F_viaggio = X_r * cd * travel_cost_one_turn
    F_lavoro  = X_r * cm * sum(times)
    F_total   = F_insoddis + F_costo_fisso + F_viaggio + F_lavoro

    return {
        "F_total":       F_total,
        "F_insoddis":    F_insoddis,
        "F_costo_fisso": F_costo_fisso,
        "F_viaggio":     F_viaggio,
        "F_lavoro":      F_lavoro,
    }


# =============================================================================
# 4. WORKER E GRID SEARCH
# =============================================================================

def _evaluate_one(args: tuple) -> dict | None:
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
    """Grid search su X_values per il rifiuto r con Clarke-Wright.

    Firma identica a Greedy.grid_search per completa intercambiabilita'.
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