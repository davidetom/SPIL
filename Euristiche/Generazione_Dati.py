from __future__ import annotations

# ── Import ────────────────────────────────────────────────────────────────────────────
import json
import pickle
import warnings
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import Delaunay


# ─────────────────────────────────────────────────────────────────────────────
#  SCENARIO REGISTRY  —  Distribuzione tipologie utente predefinite
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

DEFAULT_USER_SCENARIO = "residenziale"


# ─────────────────────────────────────────────────────────────────────────────
#  _build_graph  —  Logica di costruzione grafo, riusabile per rete fissa
# ─────────────────────────────────────────────────────────────────────────────

def _build_graph(
    coords: np.ndarray,
    r_factor: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, set[tuple[int, int]]]:
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
            i = int(simplex[k])
            j = int(simplex[(k + 1) % 3])
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
    rows = []
    cols = []
    vals = []
    
    for i, j in edges:
        d = full_dist[i, j]
        rows.extend([i, j])
        cols.extend([j, i])
        vals.extend([d, d])

    graph_csr   = csr_matrix((vals, (rows, cols)), shape=(n_nodes, n_nodes))
    dist_matrix = dijkstra(graph_csr, directed=False)
    time_matrix = dist_matrix / speed

    adj = np.full((n_nodes, n_nodes), np.inf)
    np.fill_diagonal(adj, 0.0)
    for i, j in edges:
        adj[i, j] = full_dist[i, j]
        adj[j, i] = full_dist[i, j]

    return dist_matrix, time_matrix, adj, edges


# ─────────────────────────────────────────────────────────────────────────────
#  _build_problem_params  —  Generazione parametri indipendenti dal grafo
# ─────────────────────────────────────────────────────────────────────────────

def _build_problem_params(
    n_users: int,
    rng: np.random.Generator,
    user_scenario: str,
    custom_type_probs: np.ndarray | None,
    fixed_user_types: np.ndarray | None = None,
) -> dict:
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

    if fixed_user_types is not None:
        user_types = np.asarray(fixed_user_types, dtype=object)
        if custom_type_probs is None:
            scenario_label = scenario_label
        else:
            scenario_label = "custom"
    else:
        probs /= probs.sum()   
        type_indices = rng.choice(len(user_type_list), size=n_users, p=probs)
        user_types   = np.array([user_type_list[i] for i in type_indices], dtype=object)

    waste_types = ["organico", "carta", "plastica", "vetro", "indifferenziata"]

    W_base = {
        "organico": 3.0, 
        "carta": 2.0, 
        "plastica": 1.7,
        "vetro": 1.2,    
        "indifferenziata": 2.5,
    }
    type_multiplier = {
        "single": 0.5, 
        "famiglia": 1.0,
        "palazzina_piccola": 6.0, 
        "palazzina_grande": 20.0,
    }
    W = {
        (r, t): W_base[r] * type_multiplier[t]
        for r in waste_types for t in user_type_list
    }

    x_star_base = {
        "organico": 2.5, 
        "carta": 1.0, 
        "plastica": 1.7,
        "vetro": 0.5,    
        "indifferenziata": 2.0,
    }
    x_star_type_mult = {
        "single": 0.7, 
        "famiglia": 1.0,
        "palazzina_piccola": 1.5, 
        "palazzina_grande": 2.0,
    }
    x_star = {
        (r, t): x_star_base[r] * x_star_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    C = {
        "organico": 1500.0, 
        "carta": 1500.0, 
        "plastica": 1000.0,
        "vetro": 2000.0,    
        "indifferenziata": 2000.0,
    }

    tc_base = {
        "organico": 1.2, 
        "carta": 1.0, 
        "plastica": 1.0,
        "vetro": 1.5,    
        "indifferenziata": 1.2,
    }
    tc_type_mult = {
        "single": 1.0, 
        "famiglia": 1.0,
        "palazzina_piccola": 3.0, 
        "palazzina_grande": 3.0,
    }
    tc = {
        (r, t): tc_base[r] * tc_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    c_fixed = {
        "organico": 120.0, 
        "carta": 80.0, 
        "plastica": 70.0,
        "vetro": 110.0,    
        "indifferenziata": 90.0,
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
#  get_or_create_base_graph — Gestione Grafo Condiviso Unico e relativo PNG
# ─────────────────────────────────────────────────────────────────────────────

def get_or_create_base_graph(n_max: int = 500, seed: int = 42, r_factor: float = 1.2) -> dict:
    """Carica o genera un grafo stradale di base costante per N_max nodi."""
    folder = Path("grafo_condiviso")
    folder.mkdir(exist_ok=True)
    file_path = folder / f"base_graph_N{n_max}_seed{seed}.pkl"

    if file_path.exists():
        print(f"  [Grafo Condiviso] Caricamento da disco ({file_path.name})...")
        with open(file_path, "rb") as f:
            base_graph = pickle.load(f)
    else:
        print(f"  [Grafo Condiviso] Generazione nuovo grafo base stradale ({n_max} incroci max)...")
        rng = np.random.default_rng(seed)
        
        n_nodes_max = n_max + 1
        coords_base = rng.uniform(0, 10, size=(n_nodes_max, 2))
        coords_base[0] = [5.0, 5.0] 

        dist_base, time_base, adj_base, edges_base = _build_graph(coords_base, r_factor)

        base_graph = {
            "coords_base": coords_base,
            "dist_base": dist_base,
            "time_base": time_base,
            "adj_base": adj_base,
            "edges_base": edges_base,
            "n_max": n_max,
            "seed": seed
        }

        with open(file_path, "wb") as f:
            pickle.dump(base_graph, f)
            
        print("  [Grafo Condiviso] Salvataggio completato.")

    # Assicura il salvataggio del PNG del grafo stradale puro (uno per dimensione)
    _salva_png_grafo_base(base_graph["coords_base"], base_graph["edges_base"], n_max)
    
    return base_graph


def _salva_png_grafo_base(coords_base: np.ndarray, edges_base: set[tuple[int, int]], n_max: int) -> None:
    """Disegna ed esporta esclusivamente la rete stradale mock pura in grafi_png."""
    folder = Path("grafi_png")
    folder.mkdir(exist_ok=True)
    save_path = folder / f"grafo_base_Nmax{n_max}.png"
    
    # Se esiste già, evitiamo di rieseguire l'esportazione grafica rallentando i test
    if save_path.exists():
        return
        
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Layer 1: Rete di archi stradali
    for (i, j) in edges_base:
        ax.plot([coords_base[i, 0], coords_base[j, 0]],
                [coords_base[i, 1], coords_base[j, 1]],
                color="#CCCCCC", 
                linewidth=0.8, 
                zorder=1)
                
    # Layer 2: Tutti i nodi incrocio strutturali (senza differenziazione utenti)
    ax.scatter(coords_base[1:, 0], coords_base[1:, 1],
               color="white", 
               edgecolors="black", 
               s=30, 
               zorder=2)
               
    # Layer 3: Deposito di base
    ax.scatter(*coords_base[0], 
               color="#E24B4A", 
               s=250, 
               zorder=3, 
               marker="*")
    
    ax.set_title(f"Rete Stradale di Base Condivisa (N_max = {n_max})", pad=15)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close(fig)
    print(f"  → PNG Grafo Base Stradale salvato correttamente: {save_path}")


# ─────────────────────────────────────────────────────────────────────────────
#  generate_mock_data  —  Aggiornato per il Grafo Condiviso
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
    base_graph_dict:   dict | None       = None,
) -> dict:
    rng = np.random.default_rng(seed)

    coords_base_out = None
    edges_base_out  = None
    keep_idx_out    = None
    centroids_out   = None

    # ── LOGICA 1: Usiamo un Grafo di Base condiviso (Analisi 1, 2, 3) ──
    if base_graph_dict is not None:
        coords_base = base_graph_dict["coords_base"]
        dist_base   = base_graph_dict["dist_base"]
        time_base   = base_graph_dict["time_base"]
        adj_base    = base_graph_dict["adj_base"]
        edges_base  = base_graph_dict["edges_base"]
        g_n_max     = base_graph_dict["n_max"]

        if n_users > g_n_max:
            raise ValueError(f"n_users ({n_users}) non può superare n_max ({g_n_max}) nel Grafo Condiviso.")

        all_user_indices = np.arange(1, g_n_max + 1)
        
        if spatial_mode == "cluster":
            # Distribuzione Aggregata: 1 centroide fisso a [5.0, 5.0]
            centroid = np.array([5.0, 5.0])
            centroids_out = np.array([centroid])
            
            user_coords = coords_base[1:]
            dists = np.sum((user_coords - centroid)**2, axis=1)
            
            closest_idx = np.argsort(dists)[:n_users]
            chosen = np.sort(closest_idx + 1) 
        else:
            # Distribuzione Uniforme
            chosen = rng.choice(all_user_indices, size=n_users, replace=False)
            chosen = np.sort(chosen)

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

        coords_base_out = coords_base
        edges_base_out  = edges_base
        keep_idx_out    = keep_idx

    # ── LOGICA 2: Grafo generato da zero (Analisi Standard) ──
    else:
        n_nodes = n_users + 1

        if spatial_mode == "cluster":
            min_dist = 10.0 / n_clusters 
            centroids = []
            max_tentativi = 500
            
            for _ in range(n_clusters):
                for tentativo in range(max_tentativi):
                    candidato = rng.uniform(1, 9, size=2)
                    
                    if len(centroids) == 0:
                        centroids.append(candidato)
                        break
                        
                    distanze = np.sqrt(np.sum((np.array(centroids) - candidato)**2, axis=1))
                    
                    if np.all(distanze >= min_dist):
                        centroids.append(candidato)
                        break
                else:
                    centroids.append(candidato)
            
            centroids = np.array(centroids)
            centroids_out = centroids
            
            cluster_ids = rng.integers(0, n_clusters, size=n_users)
            user_coords = np.empty((n_users, 2))
            
            for c in range(n_clusters):
                mask = cluster_ids == c
                cnt  = mask.sum()
                if cnt > 0:
                    user_coords[mask] = rng.normal(loc=centroids[c], scale=cluster_std, size=(cnt, 2))
                    
            user_coords = np.clip(user_coords, 0.0, 10.0)

            coords      = np.empty((n_nodes, 2))
            coords[0]   = [5.0, 5.0]
            coords[1:]  = user_coords

        else:
            coords    = rng.uniform(0, 10, size=(n_nodes, 2))
            coords[0] = [5.0, 5.0]

        dist_matrix, time_matrix, adj_matrix, edges = _build_graph(coords, r_factor)
        g_n_max = None

    params = _build_problem_params(n_users, rng, user_scenario, custom_type_probs)

    spatial_mode_str = spatial_mode
    if base_graph_dict is not None:
        spatial_mode_str = f"fixed_net_{spatial_mode}"

    return {
        "coords":         coords,
        "adj_matrix":     adj_matrix,
        "dist_matrix":    dist_matrix,
        "time_matrix":    time_matrix,
        "edges":          edges,
        **params,
        "n_users":        n_users,
        "spatial_mode":   spatial_mode_str,
        "n_max":          g_n_max,
        "coords_base":    coords_base_out,
        "edges_base":     edges_base_out,
        "keep_idx":       keep_idx_out,
        "centroids":      centroids_out,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  generate_real_data  —  Caricamento da mappa reale (Fabriano OSM)
# ─────────────────────────────────────────────────────────────────────────────

def generate_real_data(
    graphml_path:      str | Path = "dati_reali/grafo_aumentato.graphml",
    utenti_json_path:  str | Path = "dati_reali/utenti.json",
    user_scenario:     str | None = None,
    custom_type_probs: np.ndarray | None = None,
    seed:              int = 42,
) -> dict:
    try:
        import osmnx as ox
    except ImportError:
        raise ImportError(
            "osmnx non trovato. Installa con: pip install osmnx"
        )

    warnings.filterwarnings("ignore")

    print(f"  [Reale] Caricamento grafo: '{graphml_path}'...")
    G = ox.load_graphml(str(graphml_path))

    with open(utenti_json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    if isinstance(json_data, dict) and "utenti" in json_data:
        utenti_list: list[dict] = json_data["utenti"]
        depot_meta  = json_data.get("deposito", {})
        depot_osmid = depot_meta.get("node_id", None)
    else:
        utenti_list = json_data
        depot_meta  = {}
        depot_osmid = None

    n_users = len(utenti_list)

    if depot_osmid is not None and G.has_node(depot_osmid):
        pass
    else:
        road_nodes = [
            (n, d) for n, d in G.nodes(data=True)
            if d.get("is_user") != "True" and d.get("is_depot") != "True"
        ]
        
        xs = np.array([float(d["x"]) for _, d in road_nodes])
        ys = np.array([float(d["y"]) for _, d in road_nodes])
        cx = xs.mean()
        cy = ys.mean()
        
        dists_to_center = (xs - cx) ** 2 + (ys - cy) ** 2
        depot_osmid = road_nodes[int(np.argmin(dists_to_center))][0]

    user_osmids = [u["node_id"] for u in utenti_list]   
    spil_nodes  = [depot_osmid] + user_osmids            
    n_spil      = len(spil_nodes)                        

    osmid_to_spil: dict = {osmid: idx for idx, osmid in enumerate(spil_nodes)}

    all_nodes      = list(G.nodes())
    n_all          = len(all_nodes)
    node_to_global = {n: i for i, n in enumerate(all_nodes)}

    rows_d = []
    cols_d = []
    vals_d = []
    
    rows_t = []
    cols_t = []
    vals_t = []

    for u, v, data in G.edges(data=True):
        i = node_to_global[u]
        j = node_to_global[v]
        
        length_m = float(data.get("length", 0.0))
        tt_min   = float(data.get("travel_time_min", 0.0))
        
        rows_d.append(i)
        cols_d.append(j)
        vals_d.append(length_m)
        
        rows_t.append(i)
        cols_t.append(j)
        vals_t.append(tt_min)

    graph_dist_full = csr_matrix((vals_d, (rows_d, cols_d)), shape=(n_all, n_all))
    graph_time_full = csr_matrix((vals_t, (rows_t, cols_t)), shape=(n_all, n_all))

    spil_global_indices = np.array([node_to_global[n] for n in spil_nodes], dtype=np.int32)
    
    dist_full_m   = dijkstra(graph_dist_full, directed=True, indices=spil_global_indices)
    time_full_min = dijkstra(graph_time_full, directed=True, indices=spil_global_indices)

    dist_m   = dist_full_m[:, spil_global_indices]
    time_min = time_full_min[:, spil_global_indices]
    dist_km  = dist_m / 1000.0

    adj_matrix = np.full((n_spil, n_spil), np.inf)
    np.fill_diagonal(adj_matrix, 0.0)
    
    edges: set[tuple[int, int]] = set()
    spil_set = set(spil_nodes)   

    for u, v, data in G.edges(data=True):
        if u not in spil_set or v not in spil_set:
            continue
            
        i = osmid_to_spil[u]
        j = osmid_to_spil[v]
        length_km = float(data.get("length", 0.0)) / 1000.0
        
        if length_km < adj_matrix[i, j]:
            adj_matrix[i, j] = length_km
            
        edges.add((min(i, j), max(i, j)))

    all_nodes_list = list(G.nodes())
    all_x_full = np.array([float(G.nodes[n]["x"]) for n in all_nodes_list])
    all_y_full = np.array([float(G.nodes[n]["y"]) for n in all_nodes_list])
    x_min = all_x_full.min()
    y_min = all_y_full.min()
    span  = max(all_x_full.max() - x_min, all_y_full.max() - y_min)

    spil_x = np.array([float(G.nodes[n]["x"]) for n in spil_nodes])
    spil_y = np.array([float(G.nodes[n]["y"]) for n in spil_nodes])
    
    coords = np.column_stack([
        (spil_x - x_min) / span * 10.0,
        (spil_y - y_min) / span * 10.0,
    ])

    coords_full = np.column_stack([
        (all_x_full - x_min) / span * 10.0,
        (all_y_full - y_min) / span * 10.0,
    ])

    node_to_plot_idx = {n: i for i, n in enumerate(all_nodes_list)}
    
    seen_plot_edges: set[tuple[int, int]] = set()
    edges_full: set[tuple[int, int]] = set()
    
    for u, v in G.edges():
        i = node_to_plot_idx[u]
        j = node_to_plot_idx[v]
        key = (min(i, j), max(i, j))
        
        if key not in seen_plot_edges:
            seen_plot_edges.add(key)
            edges_full.add(key)

    spil_to_full_idx = {n: node_to_plot_idx[n] for n in spil_nodes}

    rng = np.random.default_rng(seed)
    use_real_types = (user_scenario is None and custom_type_probs is None)

    if use_real_types:
        fixed_types = np.array([u["tipologia"] for u in utenti_list], dtype=object)
        scenario_label = "mappa_reale"
    else:
        fixed_types    = None
        scenario_label = user_scenario or "custom"

    params = _build_problem_params(
        n_users           = n_users,
        rng               = rng,
        user_scenario     = user_scenario or DEFAULT_USER_SCENARIO,
        custom_type_probs = custom_type_probs,
        fixed_user_types  = fixed_types,
    )
    params["scenario_label"] = scenario_label

    return {
        "coords":           coords,
        "adj_matrix":       adj_matrix,
        "dist_matrix":      dist_km,
        "time_matrix":      time_min,
        "edges":            edges,
        **params,
        "n_users":          n_users,
        "spatial_mode":     "mappa_reale",
        "n_max":            None,
        "coords_base":      None,
        "edges_base":       None,
        "keep_idx":         None,
        "centroids":        None,
        "coords_full":      coords_full,       
        "edges_full":       edges_full,        
        "spil_to_full_idx": spil_to_full_idx,  
        "_depot_osmid":     depot_osmid,
        "_spil_nodes":      spil_nodes,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  plot_graph_reale — Invariato
# ─────────────────────────────────────────────────────────────────────────────

def plot_graph_reale(data: dict, save_name: str | None = None, show_ui: bool = True) -> None:
    coords     = data["coords"]        
    user_types = data["user_types"]
    n_users    = data["n_users"]

    coords_full      = data.get("coords_full")       
    edges_full       = data.get("edges_full")        
    spil_to_full_idx = data.get("spil_to_full_idx")  

    use_full_bg = (coords_full is not None and edges_full is not None and spil_to_full_idx is not None)
    
    type_colors = {
        "single": "#378ADD", 
        "famiglia": "#1D9E75", 
        "palazzina_piccola": "#BA17AC", 
        "palazzina_grande":  "#DDC616"
    }

    fig, ax = plt.subplots(figsize=(14, 12))

    if use_full_bg:
        import matplotlib.collections as mc
        segments = []
        for i, j in edges_full:
            segments.append([coords_full[i], coords_full[j]])
            
        lc = mc.LineCollection(segments, colors="#CCCCCC", linewidths=0.5, zorder=1)
        ax.add_collection(lc)
    else:
        for (i, j) in data.get("edges", set()):
            ax.plot([coords[i, 0], coords[j, 0]], 
                    [coords[i, 1], coords[j, 1]], 
                    color="#CCCCCC", 
                    linewidth=0.5, 
                    zorder=1)

    if use_full_bg:
        spil_full_indices = set(spil_to_full_idx.values())
        road_mask = np.array([i not in spil_full_indices for i in range(len(coords_full))])
        
        if road_mask.any():
            ax.scatter(coords_full[road_mask, 0], 
                       coords_full[road_mask, 1], 
                       color="white", 
                       edgecolors="#AAAAAA", 
                       s=8, 
                       linewidths=0.4, 
                       zorder=2)

    for u_idx in range(n_users):
        x = coords[u_idx + 1][0]
        y = coords[u_idx + 1][1]
        t = user_types[u_idx]
        
        ax.scatter(x, y, 
                   color=type_colors.get(t, "#999999"), 
                   s=25, 
                   zorder=3, 
                   edgecolors="white", 
                   linewidths=0.3)

    ax.scatter(*coords[0], 
               color="#E24B4A", 
               s=350, 
               zorder=11, 
               marker="*", 
               edgecolors="white", 
               linewidths=0.8)
               
    ax.text(coords[0, 0] + 0.05, 
            coords[0, 1] + 0.05, 
            "Deposito", 
            fontweight="bold", 
            color="#E24B4A", 
            zorder=11, 
            fontsize=9)

    legend_handles = [
        plt.Line2D([0], [0], marker="*", color="w", markerfacecolor="#E24B4A", markersize=14, label="Deposito")
    ]
    
    for t, c in type_colors.items():
        legend_handles.append(mpatches.Patch(color=c, label=t.replace("_", " ").capitalize()))
        
    if use_full_bg:
        legend_handles.append(
            plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="white", markeredgecolor="#AAAAAA", markersize=6, label="Incrocio stradale")
        )

    ax.legend(handles=legend_handles, loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_title(f"Grafo reale Fabriano: {n_users} utenti | {data['spatial_mode']}", pad=15)
    ax.autoscale()
    plt.tight_layout()

    if save_name:
        folder = Path("grafi_png")
        folder.mkdir(exist_ok=True)
        plt.savefig(folder / save_name, dpi=300)

    if show_ui:
        plt.show()
    else:
        plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
#  plot_graph — Invariato
# ─────────────────────────────────────────────────────────────────────────────

def plot_graph(data: dict, save_name: str | None = None, show_ui: bool = True) -> None:
    coords:     np.ndarray = data["coords"]
    edges:      set        = data["edges"]
    user_types: np.ndarray = data["user_types"]
    
    coords_base = data.get("coords_base")
    edges_base  = data.get("edges_base")
    keep_idx    = data.get("keep_idx")
    centroids   = data.get("centroids")

    type_colors = {
        "single": "#378ADD", 
        "famiglia": "#1D9E75", 
        "palazzina_piccola": "#BA17AC", 
        "palazzina_grande": "#DDC616"
    }
    
    fig, ax = plt.subplots(figsize=(10, 10))

    if edges_base is not None:
        edges_to_plot = edges_base
    else:
        edges_to_plot = edges
        
    if coords_base is not None:
        coords_for_edges = coords_base
    else:
        coords_for_edges = coords
        
    for (i, j) in edges_to_plot:
        ax.plot([coords_for_edges[i, 0], coords_for_edges[j, 0]], 
                [coords_for_edges[i, 1], coords_for_edges[j, 1]], 
                color="#CCCCCC", 
                linewidth=0.8, 
                zorder=1)

    if coords_base is not None and keep_idx is not None:
        inactive_mask = np.ones(len(coords_base), dtype=bool)
        inactive_mask[keep_idx] = False
        incroci_coords = coords_base[inactive_mask]
        
        if len(incroci_coords) > 0:
            ax.scatter(incroci_coords[:, 0], 
                       incroci_coords[:, 1], 
                       color="white", 
                       edgecolors="black", 
                       s=40, 
                       zorder=2)

    for u_idx in range(data["n_users"]):
        t = user_types[u_idx]
        x = coords[u_idx + 1][0]
        y = coords[u_idx + 1][1]
        
        ax.scatter(x, y, color=type_colors[t], s=120, zorder=3, edgecolors="white")

    if centroids is not None:
        ax.scatter(centroids[:, 0], 
                   centroids[:, 1], 
                   color="#FF3300", 
                   marker="X", 
                   s=200, 
                   zorder=10, 
                   edgecolors="black", 
                   label="Centri Cluster")

    ax.scatter(*coords[0], color="#E24B4A", s=300, zorder=11, marker="*", edgecolors="white")
    ax.text(coords[0,0]+0.1, coords[0,1]+0.1, "Deposito", fontweight="bold", color="#E24B4A", zorder=11)

    legend_handles = [
        plt.Line2D([0], [0], marker='*', color='w', markerfacecolor='#E24B4A', markersize=15, label="Deposito")
    ]
    
    for t, c in type_colors.items():
        legend_handles.append(mpatches.Patch(color=c, label=t.replace("_", " ").capitalize()))
        
    if coords_base is not None:
        legend_handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='white', markeredgecolor='black', label="Incrocio"))
        
    if centroids is not None:
        legend_handles.append(plt.Line2D([0], [0], marker='X', color='w', markerfacecolor='#FF3300', markeredgecolor='black', label="Centroide Cluster"))

    ax.legend(handles=legend_handles, loc="upper left", fontsize=9, framealpha=0.9)
    ax.set_title(f"Grafo: {data['n_users']} utenti | {data['spatial_mode']}", pad=15)
    plt.tight_layout()

    if save_name:
        folder = Path("grafi_png")
        folder.mkdir(exist_ok=True)
        plt.savefig(folder / save_name, dpi=300)

    if show_ui:
        plt.show()
    else:
        plt.close(fig)