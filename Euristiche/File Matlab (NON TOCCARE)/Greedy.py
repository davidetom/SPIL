from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any
import numpy as np
import time

# ---------------------------------------------------------
# 1. NUMPY HELPERS (calcolo vettorizzato)
# ---------------------------------------------------------

def _make_numpy_views(data: dict, r: str, X_r: float):
    """Pre-calcola array numpy per accesso O(1) vettorizzato."""
    n = data["n_users"]
    dist = data["dist_matrix"]
    time_mat = data["time_matrix"]
    user_types = data["user_types"]
    W = data["W"]
    tc = data["tc"]

    if isinstance(dist, np.ndarray):
        dist_np = dist.astype(np.float32)
        time_np = time_mat.astype(np.float32)
    else:
        size = n + 1
        dist_np = np.zeros((size, size), dtype=np.float32)
        time_np = np.zeros((size, size), dtype=np.float32)
        for (i, j), v in dist.items():
            dist_np[i, j] = v
        for (i, j), v in time_mat.items():
            time_np[i, j] = v

    Q_arr = np.zeros(n + 1, dtype=np.float32)
    TC_arr = np.zeros(n + 1, dtype=np.float32)

    for u in range(1, n + 1):
        t_u = user_types[u - 1]
        Q_arr[u] = W[(r, t_u)] / X_r
        TC_arr[u] = tc[(r, t_u)]

    return dist_np, time_np, Q_arr, TC_arr


def vectorized_delta_costs(
    cur: int,
    candidates: np.ndarray,
    dist_np: np.ndarray,
    time_np: np.ndarray,
    TC_arr: np.ndarray,
    cd: float,
    cm: float,
) -> np.ndarray:
    """Calcola delta_cost(cur, u) per tutti gli u in candidates in un colpo solo."""
    d_cur_u = dist_np[cur, candidates]
    d_u_0 = dist_np[candidates, 0]
    t_cur_u = time_np[cur, candidates]
    t_u_0 = time_np[candidates, 0]
    TC_u = TC_arr[candidates]

    compute = cd * (d_cur_u + d_u_0) + cm * (t_cur_u + TC_u + t_u_0)
    close = cd * dist_np[cur, 0] + cm * time_np[cur, 0]
    
    return compute - close


# ---------------------------------------------------------
# 2. BUILD ROUTES (Numpy Vectorized)
# ---------------------------------------------------------

def build_routes(data: dict, r: str, X_r: float) -> dict:
    if X_r <= 0:
        raise ValueError(f"X_r deve essere > 0, ricevuto {X_r}")

    n_users = data["n_users"]
    user_types = data["user_types"]
    C_r = data["C"][r]
    L = data["L"]
    c_fixed_r = data["c_fixed"][r]
    cd = data["cd"]
    cm = data["cm"]
    x_star = data["x_star"]
    alpha = data["alpha"]
    beta = data["beta"]

    dist_np, time_np, Q_arr, TC_arr = _make_numpy_views(data, r, X_r)
    user_nodes = np.arange(1, n_users + 1, dtype=np.int32)

    # 1. Insoddisfazione
    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u = user_types[u_idx]
        x_s = x_star[(r, t_u)]
        delta = X_r - x_s
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta

    # 2. Costo seed (Vettorizzato)
    d0u = dist_np[0, user_nodes]
    du0 = dist_np[user_nodes, 0]
    t0u = time_np[0, user_nodes]
    tu0 = time_np[user_nodes, 0]
    TCu = TC_arr[user_nodes]

    seed_costs = cd * (d0u + du0) + cm * (t0u + TCu + tu0)
    sorted_idx = np.argsort(seed_costs)
    sorted_users = user_nodes[sorted_idx].tolist()

    # 3. Helpers veicolo
    open_vehicles: list[dict] = []
    closed_routes: list[dict] = []

    def _apply_insert(veh: dict, u: int) -> None:
        cur = veh["current"]
        veh["route"].append(u)
        veh["load"] += Q_arr[u]
        veh["time_no_ret"] += time_np[cur, u] + TC_arr[u]
        veh["current"] = u

    def open_new_vehicle(seed: int) -> dict:
        return {
            "route": [seed],
            "load": Q_arr[seed],
            "time_no_ret": time_np[0, seed] + TC_arr[seed],
            "current": seed,
        }

    def _close_vehicle(veh: dict) -> None:
        closed_routes.append({
            "route": [0] + veh["route"] + [0],
            "load": veh["load"],
            "time": veh["time_no_ret"] + time_np[veh["current"], 0],
        })

    # 4. Filtra seed non fattibili
    feasible_seeds: list[int] = []
    for u in sorted_users:
        if (Q_arr[u] <= C_r and (time_np[0, u] + TC_arr[u] + time_np[u, 0]) <= L):
            feasible_seeds.append(u)
        else:
            print(f"[WARN] nodo {u} non fattibile da solo per '{r}' escluso")

    if not feasible_seeds:
        print(f"[WARN] nessun utente fattibile per '{r}', X_r={X_r}")
        return {"routes": [], "n_vehicles": 0, "loads": [], "times": []}

    unassigned: set[int] = set(feasible_seeds)

    # 5. Apri il primo veicolo
    f_partial = F_insoddis
    first_seed = feasible_seeds[0]
    unassigned.discard(first_seed)
    open_vehicles.append(open_new_vehicle(first_seed))
    f_partial += c_fixed_r * X_r

    # 6. Greedy competitivo (Numpy esatto, senza heap)
    while unassigned:
        best_option = None
        best_option_cost = float("inf")
        
        # Array di nodi rimanenti per calcolo vettorizzato in un solo colpo
        unassigned_arr = np.array(list(unassigned), dtype=np.int32)

        # Step A: miglior inserimento per ogni veicolo aperto
        still_open: list[int] = []
        
        for idx, veh in enumerate(open_vehicles):
            cur = veh["current"]
            
            # Calcola ESATTAMENTE tutti i delta_cost per i nodi rimasti in O(1) Python
            dcs = vectorized_delta_costs(cur, unassigned_arr, dist_np, time_np, TC_arr, cd, cm)
            
            # Ordina gli indici dal costo minore al maggiore per testare i migliori per primi
            sorted_candidates_idx = np.argsort(dcs)
            
            best_u = None
            best_cost = float("inf")

            for i in sorted_candidates_idx:
                u = int(unassigned_arr[i])
                dc_real = float(dcs[i])
                fo = f_partial + dc_real
                
                # Ottimizzazione: se il costo base è già peggiore della miglior opzione globale, skippa
                if fo >= best_option_cost:
                    break

                # Check fattibilità
                new_load = veh["load"] + Q_arr[u]
                new_time = veh["time_no_ret"] + time_np[cur, u] + TC_arr[u] + time_np[u, 0]

                if new_load <= C_r and new_time <= L:
                    best_u = u
                    best_cost = fo
                    break # Primo trovato è garantito essere il migliore per questo veicolo

            if best_u is None:
                _close_vehicle(veh)
            else:
                still_open.append(idx)
                if best_cost < best_option_cost:
                    best_option_cost = best_cost
                    best_option = ("insert", idx, best_u)

        open_vehicles = [open_vehicles[i] for i in still_open]

        # Step B: apertura nuovo veicolo
        next_seed = next((u for u in feasible_seeds if u in unassigned), None)
        if next_seed is not None:
            seed_cost = (cd * (dist_np[0, next_seed] + dist_np[next_seed, 0]) +
                         cm * (time_np[0, next_seed] + TC_arr[next_seed] + time_np[next_seed, 0]))
            fo_new = f_partial + c_fixed_r * X_r + seed_cost
            if fo_new < best_option_cost:
                best_option_cost = fo_new
                best_option = ("new", None, next_seed)

        # Guard: nessuna mossa disponibile
        if best_option is None:
            print(f"[WARN] utenti rimasti non assegnabili per '{r}': {unassigned}")
            break

        # Step C: applica mossa e aggiorna f_partial
        action, veh_idx, chosen_u = best_option
        unassigned.discard(chosen_u)

        if action == "insert":
            veh = open_vehicles[veh_idx]
            cur = veh["current"]
            _apply_insert(veh, chosen_u)
            f_partial += (cd * dist_np[cur, chosen_u] +
                          cm * (time_np[cur, chosen_u] + TC_arr[chosen_u]))
        else:
            new_veh = open_new_vehicle(chosen_u)
            f_partial += (c_fixed_r * X_r +
                          cd * dist_np[0, chosen_u] +
                          cm * (time_np[0, chosen_u] + TC_arr[chosen_u]))
            open_vehicles.append(new_veh)

    # 7. Chiudi tutti i veicoli ancora aperti
    for veh in open_vehicles:
        _close_vehicle(veh)

    return {
        "routes": [v["route"] for v in closed_routes],
        "n_vehicles": len(closed_routes),
        "loads": [v["load"] for v in closed_routes],
        "times": [v["time"] for v in closed_routes],
    }


# ---------------------------------------------------------
# 3. COMPUTE OBJECTIVE (Invariato, usa Numpy)
# ---------------------------------------------------------

def compute_objective(data: dict, r: str, X_r: float, routes_result: dict) -> dict:
    n_users = data["n_users"]
    user_types = data["user_types"]
    x_star = data["x_star"]
    alpha = data["alpha"]
    beta = data["beta"]
    cd = data["cd"]
    cm = data["cm"]
    c_fixed_r = data["c_fixed"][r]
    n_vehicles = routes_result["n_vehicles"]
    routes = routes_result["routes"]
    times = routes_result["times"]

    if isinstance(data["dist_matrix"], np.ndarray):
        dist_np = data["dist_matrix"].astype(np.float32)
    else:
        size = n_users + 1
        dist_np = np.zeros((size, size))
        for (i, j), v in data["dist_matrix"].items():
            dist_np[i, j] = v

    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u = user_types[u_idx]
        x_s = x_star[(r, t_u)]
        delta = X_r - x_s
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta

    F_costo_fisso = c_fixed_r * n_vehicles * X_r

    travel_cost_one_turn = 0.0
    for route in routes:
        arr = np.array(route, dtype=np.int32)
        travel_cost_one_turn += np.sum(dist_np[arr[:-1], arr[1:]])
    
    F_viaggio = X_r * cd * travel_cost_one_turn
    F_lavoro = X_r * cm * sum(times)
    
    F_total = F_insoddis + F_costo_fisso + F_viaggio + F_lavoro

    return {
        "F_total": F_total,
        "F_insoddis": F_insoddis,
        "F_costo_fisso": F_costo_fisso,
        "F_viaggio": F_viaggio,
        "F_lavoro": F_lavoro,
    }


# ---------------------------------------------------------
# 4. WORKER E GRID SEARCH (Invariato, ProcessPoolExecutor)
# ---------------------------------------------------------

def _evaluate_one(args: tuple) -> dict | None:
    data, r, X_r = args
    routes_result = build_routes(data, r, X_r)
    
    if routes_result["n_vehicles"] == 0:
        return None
        
    obj = compute_objective(data, r, X_r, routes_result)
    
    return {
        "X_r": X_r,
        "routes": routes_result,
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
    best_X_r = None
    best_F = None
    best_routes = None
    best_total = float("inf")
    all_results: list[dict] = []

    use_parallel = len(X_values) >= parallel_threshold

    if use_parallel:
        args_list = [(data, r, X_r) for X_r in X_values]
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_X = {executor.submit(_evaluate_one, args): args[2] for args in args_list}
            for future in as_completed(future_to_X):
                result = future.result()
                if result is None:
                    continue
                all_results.append(result)
                if result["F_total"] < best_total:
                    best_total = result["F_total"]
                    best_X_r = result["X_r"]
                    best_F = {k: result[k] for k in ("F_total", "F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro")}
                    best_routes = result["routes"]
        all_results.sort(key=lambda d: d["X_r"])
    else:
        for X_r in X_values:
            result = _evaluate_one((data, r, X_r))
            if result is None:
                continue
            all_results.append(result)
            if result["F_total"] < best_total:
                best_total = result["F_total"]
                best_X_r = result["X_r"]
                best_F = {k: result[k] for k in ("F_total", "F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro")}
                best_routes = result["routes"]

    return {
        "best_X_r": best_X_r,
        "best_F": best_F,
        "best_routes": best_routes,
        "all_results": all_results,
    }