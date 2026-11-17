from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np

from Generazione_Dati import calcola_carico_utente


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
        Q_arr[u]  = calcola_carico_utente(W[(r, t_u)], X_r)
        TC_arr[u] = tc[(r, t_u)]

    return dist_np, time_np, Q_arr, TC_arr


# =============================================================================
# 2. BUILD ROUTES
# =============================================================================

def build_routes(data: dict, r: str, X_r: float, gamma: float = 0.5, k_scala: float = 1.0) -> dict:
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

    route_nodes:    dict[int, list[int]] = {}
    route_head:     dict[int, int]       = {}
    route_tail:     dict[int, int]       = {}
    route_load:     dict[int, float]     = {}
    route_time:     dict[int, float]     = {}
    route_time_rev: dict[int, float]     = {}
    route_of:       dict[int, int]       = {}   

    for local_idx in range(F):
        u   = int(fn[local_idx])
        rid = local_idx
        route_nodes[rid]    = [u]
        route_head[rid]     = u
        route_tail[rid]     = u
        route_load[rid]     = float(Q_arr[u])
        route_time[rid]     = float(t_base_feas[local_idx])
        route_time_rev[rid] = float(t_base_feas[local_idx])
        route_of[u]         = rid

    rid_next = F

    # ── Fase 2: matrice savings vettorizzata ──────────────────────────────────
    d_i0  = dist_np[fn, 0][:, None]
    d_0j  = dist_np[0,  fn][None, :]
    d_ij  = dist_np[np.ix_(fn, fn)]

    tv_i0 = time_np[fn, 0][:, None]
    tv_0j = time_np[0,  fn][None, :]
    tv_ij = time_np[np.ix_(fn, fn)]

    S = (c_fixed_r
         + cd * (d_i0 + d_0j - d_ij)
         + cm * (tv_i0 + tv_0j - tv_ij))
 
    np.fill_diagonal(S, -np.inf)                    # nessuna scalatura per (1-gamma)
    flat   = S.ravel()
    order  = np.argsort(-flat, kind="stable")       # a parità di saving: ordine di indice
    cutoff = int(np.searchsorted(-flat[order], 0.0))
    order  = order[:cutoff]

    rows = (order // F).tolist()
    cols = (order  % F).tolist()

    # ── Fase 4a: ciclo di fusione standard (coda-testa) ───────────────────────
    for a, b in zip(rows, cols):
        node_i = int(fn[a])
        node_j = int(fn[b])

        rid_i = route_of[node_i]
        rid_j = route_of[node_j]

        if rid_i == rid_j:
            continue

        if route_tail[rid_i] != node_i or route_head[rid_j] != node_j:
            continue

        new_load = route_load[rid_i] + route_load[rid_j]
        if new_load > C_r:
            continue

        new_time = (route_time[rid_i] + route_time[rid_j]
                    - float(time_np[node_i, 0])
                    - float(time_np[0, node_j])
                    + float(time_np[node_i, node_j]))
        if new_time > L:
            continue

        rid_c  = rid_next
        rid_next += 1
        merged = route_nodes[rid_i] + route_nodes[rid_j]

        route_nodes[rid_c] = merged
        route_head[rid_c]  = merged[0]
        route_tail[rid_c]  = merged[-1]
        route_load[rid_c]  = new_load
        route_time[rid_c]  = float(new_time)

        for u in merged:
            route_of[u] = rid_c

    # ── Helper: ricalcolo esatto tempo e costo variabile di una rotta ─────────
    def _calc_route_metrics(seq: list[int]) -> tuple[float, float]:
        arr = np.array([0] + seq + [0], dtype=np.int32)
        d_sum = float(dist_np[arr[:-1], arr[1:]].sum())
        t_sum = float(time_np[arr[:-1], arr[1:]].sum() + TC_arr[arr[1:-1]].sum())
        return t_sum, cd * d_sum + cm * t_sum

    # ── Helper: ottimizzazione orientamento tramite inversione segmenti (2-opt) ─
    def _inverti_segmenti_2opt(seq: list[int]) -> list[int]:
        if len(seq) < 2:
            return seq
        full = [0] + seq + [0]
        n_full = len(full)
        _, cur_cost = _calc_route_metrics(seq)
        improved = True
        while improved:
            improved = False
            for i in range(1, n_full - 2):
                u_prev = full[i - 1]
                u_i    = full[i]
                for j in range(i + 1, n_full - 1):
                    u_j    = full[j]
                    u_next = full[j + 1]
                    # Filtro O(1) sugli archi di raccordo prima/dopo l'inversione
                    old_edge_cost = (cd * (dist_np[u_prev, u_i] + dist_np[u_j, u_next])
                                     + cm * (time_np[u_prev, u_i] + time_np[u_j, u_next]))
                    new_edge_cost = (cd * (dist_np[u_prev, u_j] + dist_np[u_i, u_next])
                                     + cm * (time_np[u_prev, u_j] + time_np[u_i, u_next]))
                    if new_edge_cost + 1e-4 < old_edge_cost:
                        cand_seq = full[1:i] + full[i:j + 1][::-1] + full[j + 1:-1]
                        cand_t, cand_cost = _calc_route_metrics(cand_seq)
                        if cand_t <= L and cand_cost + 1e-4 < cur_cost:
                            full = [0] + cand_seq + [0]
                            cur_cost = cand_cost
                            improved = True
                            u_i = full[i]
        return full[1:-1]

    # ── Fase 4b: inversione di segmenti/orientamento sulle rotte attive ────────
    active_rids = sorted(set(route_of.values()))
    for rid in active_rids:
        seq_opt = _inverti_segmenti_2opt(route_nodes[rid])
        route_nodes[rid] = seq_opt
        route_head[rid]  = seq_opt[0]
        route_tail[rid]  = seq_opt[-1]
        route_time[rid], _ = _calc_route_metrics(seq_opt)

    # ── Fase 4c: fusione aggiuntiva con inversione completa di rotta ───────────
    # Grazie al tempo risparmiato con le inversioni e all'abilitazione di fusioni
    # testa-testa e coda-coda, eventuali rotte residue vengono fuse ulteriormente.
    for a, b in zip(rows, cols):
        node_i = int(fn[a])
        node_j = int(fn[b])

        rid_i = route_of[node_i]
        rid_j = route_of[node_j]

        if rid_i == rid_j:
            continue

        new_load = route_load[rid_i] + route_load[rid_j]
        if new_load > C_r:
            continue

        is_head_i = (route_head[rid_i] == node_i)
        is_tail_i = (route_tail[rid_i] == node_i)
        is_head_j = (route_head[rid_j] == node_j)
        is_tail_j = (route_tail[rid_j] == node_j)

        if not (is_head_i or is_tail_i) or not (is_head_j or is_tail_j):
            continue

        _, cost_i = _calc_route_metrics(route_nodes[rid_i])
        _, cost_j = _calc_route_metrics(route_nodes[rid_j])

        seq_i = route_nodes[rid_i] if is_tail_i else route_nodes[rid_i][::-1]
        seq_j = route_nodes[rid_j] if is_head_j else route_nodes[rid_j][::-1]
        merged = seq_i + seq_j

        new_time, new_var_cost = _calc_route_metrics(merged)
        if new_time > L:
            continue
        if new_var_cost >= c_fixed_r + cost_i + cost_j - 1e-4:
            continue

        rid_c = rid_next
        rid_next += 1
        merged = _inverti_segmenti_2opt(merged)
        new_time, _ = _calc_route_metrics(merged)

        route_nodes[rid_c] = merged
        route_head[rid_c]  = merged[0]
        route_tail[rid_c]  = merged[-1]
        route_load[rid_c]  = new_load
        route_time[rid_c]  = new_time

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

def compute_objective(data: dict, r: str, X_r: float, routes_result: dict, gamma: float = 0.5, k_scala: float = 1.0) -> dict:
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
    loads      = routes_result["loads"]

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
    
    # 1. Applicazione Bilanciamento Scenario
    F_costi = F_costo_fisso + F_viaggio + F_lavoro
    F_total = gamma * (F_insoddis * k_scala) + (1 - gamma) * F_costi

    # 2. Calcolo metriche di saturazione veicolare
    C_r = data["C"][r]
    L = data["L"]
    
    if n_vehicles > 0:
        sat_fisica = (sum(loads) / (n_vehicles * C_r)) * 100
        sat_tempo = (sum(times) / (n_vehicles * L)) * 100
    else:
        sat_fisica = 0.0
        sat_tempo = 0.0

    return {
        "F_total":       F_total,
        "F_insoddis":    F_insoddis,
        "F_costo_fisso": F_costo_fisso,
        "F_viaggio":     F_viaggio,
        "F_lavoro":      F_lavoro,
        "sat_fisica":    sat_fisica,
        "sat_tempo":     sat_tempo,
    }


# =============================================================================
# 4. WORKER E GRID SEARCH
# =============================================================================

def _evaluate_one(args: tuple) -> dict | None:
    data, r, X_r, gamma, k_scala = args
    routes_result = build_routes(data, r, X_r, gamma, k_scala)
    if routes_result["n_vehicles"] == 0:
        return None
    obj = compute_objective(data, r, X_r, routes_result, gamma, k_scala)
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
    gamma: float = 0.5,
    k_scala: float = 1.0,
) -> dict:
    best_X_r    = None
    best_F      = None
    best_routes = None
    best_total  = float("inf")
    all_results: list[dict] = []

    use_parallel = len(X_values) >= parallel_threshold

    if use_parallel:
        args_list = [(data, r, X_r, gamma, k_scala) for X_r in X_values]
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
                        "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo"
                    )}
                    best_routes = result["routes"]
        all_results.sort(key=lambda d: d["X_r"])

    else:
        for X_r in X_values:
            result = _evaluate_one((data, r, X_r, gamma, k_scala))
            if result is None:
                continue
            all_results.append(result)
            if result["F_total"] < best_total:
                best_total  = result["F_total"]
                best_X_r    = result["X_r"]
                best_F      = {k: result[k] for k in (
                    "F_total", "F_insoddis", "F_costo_fisso",
                    "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo"
                )}
                best_routes = result["routes"]

    return {
        "best_X_r":    best_X_r,
        "best_F":      best_F,
        "best_routes": best_routes,
        "all_results": all_results,
    }