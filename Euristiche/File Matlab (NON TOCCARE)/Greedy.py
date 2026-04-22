def build_routes(data: dict, r: str, X_r: float) -> dict:
    """
    Costruisce i percorsi per il rifiuto `r` con frequenza fissa `X_r`.
    Algoritmo: Greedy competitivo multi-veicolo con inserimento in coda.

    Parametri
    ---------
    data  : dict restituito da generate_mock_data()
    r     : tipo di rifiuto (es. "organico")
    X_r   : frequenza settimanale programmata (ritiri/settimana)

    Restituisce
    -----------
    dict con chiavi:
        routes     : list[list[int]]  - ogni percorso include deposito (0)
                                        in testa e in coda
        n_vehicles : int
        loads      : list[float]      - carico (kg) per veicolo
        times      : list[float]      - tempo totale (min) per veicolo,
                                        ritorno al deposito incluso
    """
    if X_r <= 0:
        raise ValueError(f"X_r deve essere > 0, ricevuto {X_r}")

    n_users    = data["n_users"]
    dist       = data["dist_matrix"]
    time_mat   = data["time_matrix"]
    user_types = data["user_types"]
    W          = data["W"]
    tc         = data["tc"]
    C_r        = data["C"][r]
    L          = data["L"]
    c_fixed_r  = data["c_fixed"][r]
    cd         = data["cd"]
    cm         = data["cm"]

    # ── 1. Pre-calcolo Q e TC per ogni nodo utente ───────────────────────────

    user_nodes = list(range(1, n_users + 1))

    Q  = {}
    TC = {}
    for u in user_nodes:
        t_u   = user_types[u - 1]
        Q[u]  = W[(r, t_u)] / X_r
        TC[u] = tc[(r, t_u)]

    # ── 2. Insoddisfazione (costante per X_r fissato) ───────────────────────
    # Calcolata una volta sola e inclusa in f_partial dal primo passo.
    # Essendo identica in tutti gli scenari si semplifica nel confronto,
    # ma la includiamo per rendere ogni valutazione una vera stima della F.O.

    x_star = data["x_star"]
    alpha  = data["alpha"]
    beta   = data["beta"]

    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u   = user_types[u_idx]
        xs    = x_star[(r, t_u)]
        delta = X_r - xs
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta

    # ── 3. Funzione di costo operativo ───────────────────────────────────────
    # compute_cost(cur, u): costo marginale del tratto cur→u→deposito.
    # Usata come costo marginale da sommare a f_partial in fase di valutazione.
    # delta_cost(cur, u): costo incrementale netto rispetto a chiudere in cur.

    def compute_cost(cur: int, u: int) -> float:
        """Costo operativo del tratto cur→u→deposito (distanza + lavoro)."""
        return (cd * (dist[cur, u] + dist[u, 0])
                + cm * (time_mat[cur, u] + TC[u] + time_mat[u, 0]))

    def delta_cost(cur: int, u: int) -> float:
        """Costo incrementale di aggiungere u in coda rispetto a chiudere ora."""
        return compute_cost(cur, u) - cd * dist[cur, 0] - cm * time_mat[cur, 0]

    # ── 4. Lista ordinata per costo seed crescente ───────────────────────────

    sorted_users = sorted(user_nodes, key=lambda u: compute_cost(0, u))

    # ── 5. Helpers sui veicoli ───────────────────────────────────────────────

    def check_and_insert(veh: dict, u: int) -> tuple[bool, float]:
        """
        Verifica se u può essere inserito in coda al veicolo veh.
        Restituisce (fattibile, delta_cost).
        """
        cur      = veh["current"]
        new_load = veh["load"] + Q[u]
        new_time = veh["time_no_ret"] + time_mat[cur, u] + TC[u] + time_mat[u, 0]

        if new_load > C_r or new_time > L:
            return False, float("inf")

        return True, delta_cost(cur, u)

    def apply_insert(veh: dict, u: int) -> None:
        """Inserisce u in coda al veicolo veh, aggiornandone lo stato."""
        cur = veh["current"]
        veh["route"].append(u)
        veh["load"]        += Q[u]
        veh["time_no_ret"] += time_mat[cur, u] + TC[u]
        veh["current"]      = u

    def open_new_vehicle(seed: int) -> dict:
        """Apre un nuovo veicolo inizializzato col nodo seed."""
        return {
            "route":       [seed],
            "load":        Q[seed],
            "time_no_ret": time_mat[0, seed] + TC[seed],
            "current":     seed,
        }

    def close_vehicle(veh: dict) -> None:
        """Chiude il veicolo aggiungendo deposito in testa e in coda."""
        closed_routes.append({
            "route": [0] + veh["route"] + [0],
            "load":  veh["load"],
            "time":  veh["time_no_ret"] + time_mat[veh["current"], 0],
        })

    # ── 6. Guard clause: filtra utenti inattuabili da soli ───────────────────

    open_vehicles = []
    closed_routes = []
    unassigned    = set(user_nodes)

    feasible_seeds = []
    for u in sorted_users:
        if Q[u] <= C_r and (time_mat[0, u] + TC[u] + time_mat[u, 0]) <= L:
            feasible_seeds.append(u)
        else:
            print(f"  [WARN] nodo {u} non fattibile da solo per '{r}' → escluso")
            unassigned.discard(u)

    if not feasible_seeds:
        print(f"  [WARN] nessun utente fattibile per '{r}', X_r={X_r}")
        return {"routes": [], "n_vehicles": 0, "loads": [], "times": []}

    # f_partial: F.O. parziale accumulata fino al passo corrente.
    # Include F_insoddis (costante) e il costo fisso di ogni veicolo aperto
    # (c_fixed_r * X_r per veicolo). Cresce a ogni apertura di un nuovo veicolo.
    # I costi marginali operativi (viaggio + lavoro) vengono sommati a f_partial
    # in fase di valutazione di ogni mossa, non qui.
    f_partial = F_insoddis

    # Apri il primo veicolo col seed più economico
    first_seed = feasible_seeds[0]
    unassigned.discard(first_seed)
    open_vehicles.append(open_new_vehicle(first_seed))
    f_partial += c_fixed_r * X_r   # costo fisso del primo veicolo

    # ── 7. Greedy competitivo ────────────────────────────────────────────────

    while unassigned:

        best_option      = None
        best_option_cost = float("inf")

        # ── Step A: miglior inserimento per ogni veicolo aperto ──────────────
        # Per ogni veicolo troviamo il nodo u che minimizza:
        #   f_partial + delta_cost(cur, u)
        # f_partial è costante nel confronto tra candidati dello stesso veicolo,
        # ma la sommiamo esplicitamente per valutare la F.O. parziale completa.
        still_open = []
        for idx, veh in enumerate(open_vehicles):
            best_u    = None
            best_cost = float("inf")

            for u in unassigned:
                feasible, dc = check_and_insert(veh, u)
                if feasible:
                    fo = f_partial + dc   # F.O. parziale completa per questa mossa
                    if fo < best_cost:
                        best_cost = fo
                        best_u    = u

            if best_u is None:
                # Nessun utente entra: chiudi definitivamente
                close_vehicle(veh)
            else:
                still_open.append(idx)
                if best_cost < best_option_cost:
                    best_option_cost = best_cost
                    best_option      = ("insert", idx, best_u)

        open_vehicles = [open_vehicles[i] for i in still_open]

        # ── Step B: F.O. parziale apertura nuovo veicolo ─────────────────────
        # Ipotesi NEW: f_partial + c_fixed_r * X_r (costo fisso nuovo veicolo)
        #             + compute_cost(0, seed) (costo operativo del primo tratto).
        next_seed = next((u for u in feasible_seeds if u in unassigned), None)

        if next_seed is not None:
            fo_new = f_partial + c_fixed_r * X_r + compute_cost(0, next_seed)
            if fo_new < best_option_cost:
                best_option_cost = fo_new
                best_option      = ("new", None, next_seed)

        # ── Guard: nessuna mossa disponibile ─────────────────────────────────
        if best_option is None:
            print(f"  [WARN] utenti rimasti non assegnabili per '{r}': {unassigned}")
            break

        # ── Step C: applica la mossa scelta e aggiorna f_partial ─────────────
        # f_partial viene aggiornato con il costo del tratto appena percorso,
        # ESCLUSO il ritorno al deposito (già incluso nella valutazione tramite
        # compute_cost/delta_cost, non va salvato per evitare doppio conteggio).
        action, veh_idx, chosen_u = best_option

        if action == "insert":
            cur = open_vehicles[veh_idx]["current"]   # nodo corrente prima dell'inserimento
            apply_insert(open_vehicles[veh_idx], chosen_u)
            # Aggiorna f_partial con il tratto cur→chosen_u (senza ritorno deposito)
            f_partial += cd * dist[cur, chosen_u] + cm * (time_mat[cur, chosen_u] + TC[chosen_u])
        else:
            open_vehicles.append(open_new_vehicle(chosen_u))
            # Aggiorna f_partial con: costo fisso nuovo veicolo
            #                       + tratto deposito→seed (senza ritorno deposito)
            f_partial += (c_fixed_r * X_r
                          + cd * dist[0, chosen_u]
                          + cm * (time_mat[0, chosen_u] + TC[chosen_u]))

        unassigned.discard(chosen_u)

    # ── 8. Chiudi tutti i veicoli ancora aperti ──────────────────────────────
    for veh in open_vehicles:
        close_vehicle(veh)

    return {
        "routes":     [v["route"] for v in closed_routes],
        "n_vehicles": len(closed_routes),
        "loads":      [v["load"]  for v in closed_routes],
        "times":      [v["time"]  for v in closed_routes],
    }



def compute_objective(data: dict, r: str, X_r: float, routes_result: dict) -> dict:
    n_users    = data["n_users"]
    user_types = data["user_types"]
    x_star     = data["x_star"]        # ora dict (r, t) → float
    alpha      = data["alpha"]
    beta       = data["beta"]
    cd         = data["cd"]
    cm         = data["cm"]
    c_fixed_r  = data["c_fixed"][r]
    dist       = data["dist_matrix"]

    n_vehicles = routes_result["n_vehicles"]
    routes     = routes_result["routes"]
    times      = routes_result["times"]

    # ── Insoddisfazione ──────────────────────────────────────────────────────
    # x_star dipende da (r, t_u): iteriamo su ogni utente
    F_insoddis = 0.0
    for u_idx in range(n_users):
        t_u    = user_types[u_idx]
        xs     = x_star[(r, t_u)]
        delta  = X_r - xs
        if delta < 0:
            F_insoddis += alpha * (-delta)
        elif delta > 0:
            F_insoddis += beta * delta
        # se delta == 0: contributo nullo

    # ── Costo fisso ──────────────────────────────────────────────────────────
    F_costo_fisso = c_fixed_r * n_vehicles * X_r

    # ── Costo viaggio (singolo turno * X_r) ──────────────────────────────────
    travel_cost_one_turn = 0.0
    for route in routes:
        for k in range(len(route) - 1):
            a, b = route[k], route[k + 1]
            travel_cost_one_turn += cd * dist[a, b]

    F_viaggio = X_r * travel_cost_one_turn

    # ── Costo lavoro (singolo turno * X_r) ───────────────────────────────────
    F_lavoro = X_r * cm * sum(times)

    # ── Totale ───────────────────────────────────────────────────────────────
    F_total = F_insoddis + F_costo_fisso + F_viaggio + F_lavoro

    return {
        "F_total":       F_total,
        "F_insoddis":    F_insoddis,
        "F_costo_fisso": F_costo_fisso,
        "F_viaggio":     F_viaggio,
        "F_lavoro":      F_lavoro,
    }


def grid_search(data: dict, r: str, X_values: list[float]) -> dict:
    """
    Esegue la grid search sulla frequenza X_r per il rifiuto r.
    Per ogni X in X_values chiama build_routes + compute_objective
    e tiene traccia del minimo di F_total.

    Parametri
    ---------
    data     : dict da generate_mock_data()
    r        : tipo di rifiuto (es. "organico")
    X_values : lista di frequenze candidate (es. [0.5, 1.0, 1.5, ..., 6.0])

    Restituisce
    -----------
    dict con:
        best_X_r       : float
        best_F         : dict (le 5 componenti di compute_objective)
        best_routes    : dict (output di build_routes per il best X_r)
        all_results    : list[dict] - una entry per ogni X provato (per Pareto)
    """
    best_X_r    = None
    best_F      = None
    best_routes = None
    best_total  = float("inf")
    all_results = []

    for X_r in X_values:
        routes_result = build_routes(data, r, X_r)

        # Se nessun utente è fattibile salta questa frequenza
        if routes_result["n_vehicles"] == 0:
            continue

        obj = compute_objective(data, r, X_r, routes_result)

        all_results.append({
            "X_r":         X_r,
            "n_vehicles":  routes_result["n_vehicles"],
            **obj,
        })

        if obj["F_total"] < best_total:
            best_total  = obj["F_total"]
            best_X_r    = X_r
            best_F      = obj
            best_routes = routes_result

    return {
        "best_X_r":    best_X_r,
        "best_F":      best_F,
        "best_routes": best_routes,
        "all_results": all_results,
    }