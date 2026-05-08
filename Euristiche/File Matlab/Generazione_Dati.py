from __future__ import annotations

# ── Import ────────────────────────────────────────────────────────────────────
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path # Assicurati che sia importato a inizio file


# ─────────────────────────────────────────────────────────────────────────────
#  SCENARIO REGISTRY  —  Distribuzione tipologie utente predefinite
# ─────────────────────────────────────────────────────────────────────────────
#  Ogni scenario è una dict con:
#    "probs"       : array di probabilità (somma = 1.0) per
#                    [single, famiglia, palazzina_piccola, palazzina_grande]
#    "description" : etichetta leggibile (per CSV naming e stampe)
#
#  I valori sono stati scelti per massimizzare il contrasto nei benchmark:
#
#  "residenziale"     → quartiere tipico italiano:
#                        famiglie e single dominano, pochi palazzi
#  "suburbano"        → mix equilibrato, leggera prevalenza famiglie
#  "grandi_condomini" → quasi tutto palazzi grandi (alto carico kg/ritiro)
#  "villette"         → solo single/famiglie, nessun condominio
#                        (caso estremo bassa densità di rifiuto)
#  "misto_periferia"  → molte palazzine piccole, pochi grandi condomini
# ─────────────────────────────────────────────────────────────────────────────

USER_SCENARIOS: dict[str, dict] = {
    "residenziale": {
        "probs":       np.array([0.25, 0.45, 0.20, 0.10]),
        "description": "Residenziale (famiglie + single predominanti)",
    },
    "suburbano": {
        "probs":       np.array([0.20, 0.35, 0.30, 0.15]),
        "description": "Suburbano (mix bilanciato)",
    },
    "grandi_condomini": {
        "probs":       np.array([0.05, 0.10, 0.25, 0.60]),
        "description": "Grandi Condomini (alto carico per utente)",
    },
    "villette": {
        "probs":       np.array([0.40, 0.55, 0.05, 0.00]),
        "description": "Villette (bassa densità di rifiuto, nessun palazzo)",
    },
    "misto_periferia": {
        "probs":       np.array([0.15, 0.25, 0.45, 0.15]),
        "description": "Misto Periferia (palazzine piccole dominanti)",
    },
}

# Scenario di default (retrocompatibilità con chiamate senza argomento)
DEFAULT_USER_SCENARIO = "residenziale"


# ─────────────────────────────────────────────────────────────────────────────
#  _build_graph  —  Logica di costruzione grafo, riusabile per rete fissa
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph(
    coords: np.ndarray,
    r_factor: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, set[tuple[int, int]]]:
    """Costruisce il grafo planare e calcola le matrici di distanza/tempo.

    Incapsula l'intera pipeline:
      coords → Delaunay → filtraggio R → MST fallback → CSR → Dijkstra

    Estratto da ``generate_mock_data`` per permettere il riuso nella
    modalità **Rete Fissa** (grafo generato su N_max nodi, poi subsetting).

    Parameters
    ----------
    coords:
        Array ``(n_nodes, 2)`` delle coordinate km.
    r_factor:
        Moltiplicatore soglia archi Delaunay.

    Returns
    -------
    dist_matrix : ndarray (n_nodes, n_nodes)
    time_matrix : ndarray (n_nodes, n_nodes)
    adj_matrix  : ndarray (n_nodes, n_nodes)  — inf=assenza arco
    edges       : set[tuple[int,int]]
    """
    n_nodes   = len(coords)
    speed     = 25.0 / 60.0          # km/min

    # ── Distanze euclidee ─────────────────────────────────────────────────────
    delta     = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    full_dist = np.sqrt((delta ** 2).sum(axis=2))

    # ── Triangolazione di Delaunay ────────────────────────────────────────────
    tri = Delaunay(coords)
    all_delaunay_edges: set[tuple[int, int]] = set()
    for simplex in tri.simplices:
        for k in range(3):
            i, j = int(simplex[k]), int(simplex[(k + 1) % 3])
            all_delaunay_edges.add((min(i, j), max(i, j)))

    edge_arr       = np.array(list(all_delaunay_edges), dtype=np.int32)
    mean_edge_dist = full_dist[edge_arr[:, 0], edge_arr[:, 1]].mean()
    R              = r_factor * mean_edge_dist

    edge_dists = full_dist[edge_arr[:, 0], edge_arr[:, 1]]
    kept_edges = edge_arr[edge_dists <= R]
    edges: set[tuple[int, int]] = {
        (int(kept_edges[k, 0]), int(kept_edges[k, 1]))
        for k in range(len(kept_edges))
    }

    # ── Connessione — Union-Find con path compression ─────────────────────────
    parent = list(range(n_nodes))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        parent[find(a)] = find(b)

    for i, j in edges:
        union(i, j)

    if len({find(i) for i in range(n_nodes)}) > 1:
        print("  [INFO] Grafo disconnesso, ripristino con MST (SciPy)...")
        from scipy.sparse.csgraph import minimum_spanning_tree
        mst = minimum_spanning_tree(full_dist)
        for i, j in zip(mst.tocoo().row, mst.tocoo().col):
            edges.add((min(int(i), int(j)), max(int(i), int(j))))

    # ── CSR sparsa → Dijkstra ─────────────────────────────────────────────────
    rows, cols, vals = [], [], []
    for i, j in edges:
        d = full_dist[i, j]
        rows.extend([i, j]); cols.extend([j, i]); vals.extend([d, d])

    graph_csr   = csr_matrix((vals, (rows, cols)), shape=(n_nodes, n_nodes))
    dist_matrix = dijkstra(graph_csr, directed=False)
    time_matrix = dist_matrix / speed

    adj = np.full((n_nodes, n_nodes), np.inf)
    np.fill_diagonal(adj, 0.0)
    for i, j in edges:
        adj[i, j] = adj[j, i] = full_dist[i, j]

    return dist_matrix, time_matrix, adj, edges


# ─────────────────────────────────────────────────────────────────────────────
#  _build_problem_params  —  Generazione parametri indipendenti dal grafo
# ─────────────────────────────────────────────────────────────────────────────

def _build_problem_params(
    n_users: int,
    rng: np.random.Generator,
    user_scenario: str,
    custom_type_probs: np.ndarray | None,
) -> dict:
    """Genera user_types e tutti i dizionari W, x_star, C, tc, c_fixed.

    Separato da ``_build_graph`` perché nella modalità **Rete Fissa**
    i parametri vengono rigenerati per il sottoinsieme attivo, mentre
    il grafo rimane quello della città base.

    Parameters
    ----------
    n_users:
        Numero di utenti attivi (dimensione del sottoinsieme estratto).
    rng:
        Generatore NumPy già inizializzato con il seed corretto.
    user_scenario:
        Chiave in ``USER_SCENARIOS`` (ignorata se ``custom_type_probs`` è fornito).
    custom_type_probs:
        Array ``(4,)`` di probabilità custom. Ha priorità su ``user_scenario``.

    Returns
    -------
    dict
        Sotto-dizionario con: user_types, user_type_list, W, x_star,
        C, tc, c_fixed, waste_types, cd, cm, L, alpha, beta, scenario_label.
    """
    user_type_list = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]

    # ── Selezione probabilità ──────────────────────────────────────────────────
    if custom_type_probs is not None:
        probs = np.asarray(custom_type_probs, dtype=float)
        scenario_label = "custom"
    else:
        if user_scenario not in USER_SCENARIOS:
            raise ValueError(
                f"Scenario '{user_scenario}' non valido. "
                f"Scegli tra: {list(USER_SCENARIOS.keys())}"
            )
        probs          = USER_SCENARIOS[user_scenario]["probs"].copy()
        scenario_label = user_scenario

    probs /= probs.sum()   # normalizzazione difensiva
    type_indices = rng.choice(len(user_type_list), size=n_users, p=probs)
    user_types   = np.array([user_type_list[i] for i in type_indices], dtype=object)

    waste_types = ["organico", "carta", "plastica", "vetro", "indifferenziata"]

    W_base = {
        "organico": 3.0, "carta": 2.0, "plastica": 1.7,
        "vetro": 1.2,    "indifferenziata": 2.5,
    }
    type_multiplier = {
        "single": 0.5, "famiglia": 1.0,
        "palazzina_piccola": 6.0, "palazzina_grande": 20.0,
    }
    W = {
        (r, t): W_base[r] * type_multiplier[t]
        for r in waste_types for t in user_type_list
    }

    x_star_base = {
        "organico": 2.5, "carta": 1.0, "plastica": 1.7,
        "vetro": 0.5,    "indifferenziata": 2.0,
    }
    x_star_type_mult = {
        "single": 0.7, "famiglia": 1.0,
        "palazzina_piccola": 1.5, "palazzina_grande": 2.0,
    }
    x_star = {
        (r, t): x_star_base[r] * x_star_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    C = {
        "organico": 1500.0, "carta": 1500.0, "plastica": 1000.0,
        "vetro": 2000.0,    "indifferenziata": 2000.0,
    }

    tc_base = {
        "organico": 1.2, "carta": 1.0, "plastica": 1.0,
        "vetro": 1.5,    "indifferenziata": 1.2,
    }
    tc_type_mult = {
        "single": 1.0, "famiglia": 1.0,
        "palazzina_piccola": 3.0, "palazzina_grande": 3.0,
    }
    tc = {
        (r, t): tc_base[r] * tc_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    c_fixed = {
        "organico": 120.0, "carta": 80.0, "plastica": 70.0,
        "vetro": 110.0,    "indifferenziata": 90.0,
    }

    return {
        "user_types":      user_types,
        "user_type_list":  user_type_list,
        "W":               W,
        "x_star":          x_star,
        "C":               C,
        "tc":              tc,
        "c_fixed":         c_fixed,
        "waste_types":     waste_types,
        "cd":              0.35,
        "cm":              15.0 / 60.0,
        "L":               480.0,
        "alpha":           10.0,
        "beta":            2.0,
        "scenario_label":  scenario_label,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  generate_mock_data  —  Entry point principale (retrocompatibile)
# ─────────────────────────────────────────────────────────────────────────────

def generate_mock_data(
    n_users:           int,
    seed:              int,
    r_factor:          float,
    user_scenario:     str               = DEFAULT_USER_SCENARIO,
    custom_type_probs: np.ndarray | None = None,
    spatial_mode:      str               = "uniform",
    n_clusters:        int               = 4,
    cluster_std:       float             = 1.2,
    n_max:             int | None        = None,
    active_nodes:      list[int] | None  = None,
) -> dict:
    rng = np.random.default_rng(seed)

    # Variabili di appoggio per il plot
    coords_base_out = None
    edges_base_out  = None
    keep_idx_out    = None
    centroids_out   = None

    if n_max is not None:
        if n_users > n_max:
            raise ValueError(f"n_users ({n_users}) non può superare n_max ({n_max}) in Rete Fissa.")

        n_nodes_max = n_max + 1
        coords_base        = rng.uniform(0, 10, size=(n_nodes_max, 2))
        coords_base[0]     = [5.0, 5.0]

        print(f"  [Rete Fissa] Generazione grafo base: {n_max} utenti ({n_nodes_max} nodi)...")
        dist_base, time_base, adj_base, edges_base = _build_graph(coords_base, r_factor)

        all_user_indices = np.arange(1, n_nodes_max)
        if active_nodes is None:
            chosen = rng.choice(all_user_indices, size=n_users, replace=False)
            chosen = np.sort(chosen)
        else:
            chosen = np.array(active_nodes, dtype=int)

        keep_idx = np.concatenate([[0], chosen])

        dist_matrix = dist_base[np.ix_(keep_idx, keep_idx)]
        time_matrix = time_base[np.ix_(keep_idx, keep_idx)]
        adj_matrix  = adj_base [np.ix_(keep_idx, keep_idx)]
        coords      = coords_base[keep_idx]

        idx_map   = {old: new for new, old in enumerate(keep_idx)}
        edges_sub = set()
        for i, j in edges_base:
            if i in idx_map and j in idx_map:
                edges_sub.add((idx_map[i], idx_map[j]))
        edges = edges_sub

        # Salviamo i dati originali per il plot
        coords_base_out = coords_base
        edges_base_out  = edges_base
        keep_idx_out    = keep_idx

        print(f"  [Rete Fissa] Sottoinsieme attivo: {n_users} utenti (nodi originali: {chosen.tolist()})")

    else:
        n_nodes = n_users + 1

        if spatial_mode == "cluster":
            # --- NUOVA LOGICA: Distanza di Sicurezza tra Centroidi ---
            # Distanza inversamente proporzionale (10.0 è un buon fattore base)
            # - 2 cluster -> 5.0 km minimi
            # - 4 cluster -> 2.5 km minimi
            # - 6 cluster -> 1.6 km minimi
            min_dist = 10.0 / n_clusters 
            
            centroids = []
            max_tentativi = 500 # Salvaguardia contro i loop infiniti
            
            for _ in range(n_clusters):
                for tentativo in range(max_tentativi):
                    candidato = rng.uniform(1, 9, size=2)
                    
                    if len(centroids) == 0:
                        centroids.append(candidato)
                        break # Il primo centroide va sempre bene
                        
                    # Calcola le distanze tra il candidato e tutti i centri già approvati
                    distanze = np.sqrt(np.sum((np.array(centroids) - candidato)**2, axis=1))
                    
                    if np.all(distanze >= min_dist):
                        centroids.append(candidato)
                        break # Distanza rispettata, usciamo dal loop dei tentativi
                else:
                    # Questo blocco 'else' si attiva SOLO se il loop dei tentativi fallisce 500 volte.
                    # Invece di far crashare il programma, accettiamo il candidato lo stesso.
                    centroids.append(candidato)
            
            centroids = np.array(centroids)
            centroids_out = centroids # Salviamo per il plot
            
            # --- RESTO DEL CODICE ORIGINALE PER I CLUSTER ---
            cluster_ids = rng.integers(0, n_clusters, size=n_users)
            user_coords = np.empty((n_users, 2))
            for c in range(n_clusters):
                mask = cluster_ids == c
                cnt  = mask.sum()
                if cnt > 0:
                    user_coords[mask] = rng.normal(loc=centroids[c], scale=cluster_std, size=(cnt, 2))
            # Clip: nessun nodo fuori dalla griglia [0,10]²
            user_coords = np.clip(user_coords, 0.0, 10.0)

            coords      = np.empty((n_nodes, 2))
            coords[0]   = [5.0, 5.0]
            coords[1:]  = user_coords

        else:
            coords    = rng.uniform(0, 10, size=(n_nodes, 2))
            coords[0] = [5.0, 5.0]

        dist_matrix, time_matrix, adj_matrix, edges = _build_graph(coords, r_factor)
        n_max = None

    params = _build_problem_params(n_users, rng, user_scenario, custom_type_probs)

    return {
        "coords":         coords,
        "adj_matrix":     adj_matrix,
        "dist_matrix":    dist_matrix,
        "time_matrix":    time_matrix,
        "edges":          edges,
        **params,
        "n_users":        n_users,
        "spatial_mode":   spatial_mode if n_max is None else "fixed_net",
        "n_max":          n_max,
        # --- Nuovi campi per il Plot ---
        "coords_base":    coords_base_out,
        "edges_base":     edges_base_out,
        "keep_idx":       keep_idx_out,
        "centroids":      centroids_out,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  plot_graph  —  Invariata (zero modifiche, retrocompatibile)
# ─────────────────────────────────────────────────────────────────────────────

def plot_graph(data: dict, save_name: str | None = None, show_ui: bool = True) -> None:
    """Visualizza il grafo e lo salva opzionalmente come PNG."""
    coords:     np.ndarray = data["coords"]
    edges:      set        = data["edges"]
    user_types: np.ndarray = data["user_types"]
    
    coords_base = data.get("coords_base")
    edges_base  = data.get("edges_base")
    keep_idx    = data.get("keep_idx")
    centroids   = data.get("centroids")

    type_colors: dict[str, str] = {
        "single":            "#378ADD",
        "famiglia":          "#1D9E75",
        "palazzina_piccola": "#BA17AC",
        "palazzina_grande":  "#DDC616",
    }

    fig, ax = plt.subplots(figsize=(10, 10))

    # 1. Archi (zorder=1)
    edges_to_plot = edges_base if edges_base is not None else edges
    coords_for_edges = coords_base if coords_base is not None else coords
    for (i, j) in edges_to_plot:
        ax.plot([coords_for_edges[i, 0], coords_for_edges[j, 0]],
                [coords_for_edges[i, 1], coords_for_edges[j, 1]],
                color="#CCCCCC", linewidth=0.8, zorder=1)

    # 2. Nodi Incrocio (zorder=2)
    if coords_base is not None and keep_idx is not None:
        inactive_mask = np.ones(len(coords_base), dtype=bool)
        inactive_mask[keep_idx] = False
        incroci_coords = coords_base[inactive_mask]
        if len(incroci_coords) > 0:
            ax.scatter(incroci_coords[:, 0], incroci_coords[:, 1],
                       color="white", edgecolors="black", s=40, zorder=2)

    # 3. Utenti Attivi (zorder=3-4)
    for u_idx in range(data["n_users"]):
        node_idx = u_idx + 1
        t, (x, y) = user_types[u_idx], coords[node_idx]
        ax.scatter(x, y, color=type_colors[t], s=120, zorder=3, edgecolors="white")
        #ax.text(x + 0.12, y + 0.12, str(node_idx), fontsize=7, zorder=4)

    # 4. CENTROIDI (zorder=10 - ALZATO PER VISIBILITÀ)
    if centroids is not None:
        ax.scatter(centroids[:, 0], centroids[:, 1], color="#FF3300", 
                   marker="X", s=200, zorder=10, edgecolors="black", label="Centri Cluster")

    # 5. DEPOSITO (zorder=11)
    ax.scatter(*coords[0], color="#E24B4A", s=300, zorder=11, marker="*", edgecolors="white")
    ax.text(coords[0,0]+0.1, coords[0,1]+0.1, "Deposito", fontweight="bold", color="#E24B4A", zorder=11)

    # Legenda e Titolo
    legend_handles = [plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#E24B4A', markersize=15, label="Deposito")]
    for t, c in type_colors.items():
        legend_handles.append(mpatches.Patch(color=c, label=t.replace("_", " ").capitalize()))
    if coords_base is not None:
        legend_handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markeredgecolor='black', label="Incrocio"))
    if centroids is not None:
        legend_handles.append(plt.Line2D([0], [0], marker='X', color='w', markerfacecolor='#FF3300', markeredgecolor='black', label="Centroide Cluster"))

    ax.legend(handles=legend_handles, loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_title(f"Grafo: {data['n_users']} utenti | {data['spatial_mode']}", pad=15)
    plt.tight_layout()

    # SALVATAGGIO AUTOMATICO
    if save_name:
        folder = Path("grafi_png")
        folder.mkdir(exist_ok=True)
        plt.savefig(folder / save_name, dpi=300)
        print(f"  → Grafo salvato: {folder / save_name}")

    if show_ui:
        plt.show()
    else:
        plt.close(fig) # Chiude la figura per liberare memoria