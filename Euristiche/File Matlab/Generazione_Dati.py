from __future__ import annotations

# ── Import ────────────────────────────────────────────────────────────────────
# [M5-INT4] Rimossi KDTree e Counter: importati ma mai usati nella versione
#            precedente. Li togliamo per tenere il namespace pulito.
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


# ─────────────────────────────────────────────────────────────────────────────
#  generate_mock_data
# ─────────────────────────────────────────────────────────────────────────────

def generate_mock_data(n_users: int, seed: int, r_factor: float) -> dict:
    """Genera i dati sintetici del problema SPIL.

    Costruisce un grafo planare sparso tramite triangolazione di Delaunay,
    lo filtra con una soglia adattiva proporzionale a ``r_factor``, ripristina
    la connessione con un MST se necessario, e calcola le distanze minime
    con Dijkstra multi-sorgente su matrice CSR.

    Parameters
    ----------
    n_users:
        Numero di utenti (nodi cliente). Il nodo 0 è il deposito.
    seed:
        Seme del generatore casuale NumPy (riproducibilità).
    r_factor:
        Moltiplicatore della distanza media degli archi Delaunay usato come
        soglia di filtraggio ``R = r_factor * mean_edge_dist``.

        - ``1.0``  → solo archi nella media (grafo sparso)
        - ``1.5``  → archi fino al 50 % sopra la media
        - ``2.0``  → rete più densa
        - ``np.inf`` → tutti gli archi Delaunay

    Returns
    -------
    dict
        Struttura dati completa del problema. Le chiavi principali sono:

        ``coords``         — ``ndarray (n_nodes, 2)`` coordinate km  \n
        ``dist_matrix``    — ``ndarray (n_nodes, n_nodes)`` distanze SP (km)  \n
        ``time_matrix``    — ``ndarray (n_nodes, n_nodes)`` tempi SP (min)  \n
        ``adj_matrix``     — ``ndarray (n_nodes, n_nodes)`` adiacenza densa (inf = assenza)  \n
        ``edges``          — ``set[tuple[int,int]]`` archi (i<j) del grafo  \n
        ``user_types``     — ``ndarray (n_users,)`` dtype object, tipologia per utente  \n
        ``W``              — ``dict[(rifiuto, tipo)] → kg/settimana``  \n
        ``x_star``         — ``dict[(rifiuto, tipo)] → ritiri ideali/settimana``  \n
        ``C``              — ``dict[rifiuto] → capacità veicolo (kg)``  \n
        ``tc``             — ``dict[(rifiuto, tipo)] → tempo carico (min)``  \n
        ``c_fixed``        — ``dict[rifiuto] → costo fisso attivazione (€)``  \n
        ``cd``             — costo per km (€/km)  \n
        ``cm``             — costo manodopera (€/min)  \n
        ``L``              — durata turno (min)  \n
        ``alpha``          — penalità sotto-servizio  \n
        ``beta``           — penalità sovra-servizio  \n
        ``waste_types``    — ``list[str]`` nomi rifiuti  \n
        ``user_type_list`` — ``list[str]`` nomi tipologie utente  \n
        ``n_users``        — numero utenti
    """
    rng = np.random.default_rng(seed)

    n_nodes = n_users + 1
    coords  = rng.uniform(0, 10, size=(n_nodes, 2))
    coords[0] = [5.0, 5.0]

    # ── 1. Distanze euclidee — broadcasting NumPy O(N²) ──────────────────────
    delta     = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    full_dist = np.sqrt((delta ** 2).sum(axis=2))          # (n_nodes, n_nodes)

    # ── 2. Triangolazione di Delaunay ────────────────────────────────────────
    tri = Delaunay(coords)

    all_delaunay_edges: set[tuple[int, int]] = set()
    for simplex in tri.simplices:
        for k in range(3):
            i = int(simplex[k])
            j = int(simplex[(k + 1) % 3])
            all_delaunay_edges.add((min(i, j), max(i, j)))

    # [M5-INT2] Calcolo vettorizzato di mean_edge_dist.
    #   Versione precedente: list comprehension Python → lista intermedia O(E).
    #   Versione nuova: fancy indexing NumPy → zero loop Python, zero alloc
    #   intermedia. Riusiamo edge_arr anche per il filtraggio con R.
    edge_arr       = np.array(list(all_delaunay_edges), dtype=np.int32)  # (E, 2)
    mean_edge_dist = full_dist[edge_arr[:, 0], edge_arr[:, 1]].mean()
    R              = r_factor * mean_edge_dist

    # Filtraggio: manteniamo solo gli archi Delaunay con distanza <= R.
    # Ancora vettorizzato: maschera booleana sull'array edge_arr.
    edge_dists  = full_dist[edge_arr[:, 0], edge_arr[:, 1]]   # (E,)
    keep_mask   = edge_dists <= R
    kept_edges  = edge_arr[keep_mask]                          # (E', 2)
    edges: set[tuple[int, int]] = {
        (int(kept_edges[k, 0]), int(kept_edges[k, 1]))
        for k in range(len(kept_edges))
    }

    # ── 3. Verifica connessione — Union-Find con path compression ─────────────
    parent = list(range(n_nodes))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    for (i, j) in edges:
        union(i, j)

    if len({find(i) for i in range(n_nodes)}) > 1:
        print("  [INFO] Grafo disconnesso, ripristino con Minimum Spanning Tree (SciPy)...")
        from scipy.sparse.csgraph import minimum_spanning_tree
        mst     = minimum_spanning_tree(full_dist)
        mst_coo = mst.tocoo()
        for i, j in zip(mst_coo.row, mst_coo.col):
            edges.add((min(int(i), int(j)), max(int(i), int(j))))

    # ── 4. Costruzione CSR sparsa da set edges ────────────────────────────────
    #   Solo ~3N valori espliciti → Dijkstra lavora su grafo realmente sparso.
    rows, cols, data_vals = [], [], []
    for (i, j) in edges:
        d = full_dist[i, j]
        rows.extend([i, j])
        cols.extend([j, i])
        data_vals.extend([d, d])

    graph_csr = csr_matrix(
        (data_vals, (rows, cols)),
        shape=(n_nodes, n_nodes),
    )

    # ── 5. Dijkstra multi-sorgente ────────────────────────────────────────────
    #   O(N · (E + N) log N) su grafo planare E ≈ 3N → O(N² log N).
    dist_matrix: np.ndarray = dijkstra(graph_csr, directed=False)

    # ── 6. Matrice dei tempi ──────────────────────────────────────────────────
    speed_km_per_min        = 25.0 / 60.0
    time_matrix: np.ndarray = dist_matrix / speed_km_per_min

    # ── 7. adj_matrix densa per compatibilità (plot_graph, Greedy) ───────────
    adj = np.full((n_nodes, n_nodes), np.inf)
    np.fill_diagonal(adj, 0.0)
    for (i, j) in edges:
        adj[i, j] = full_dist[i, j]
        adj[j, i] = full_dist[i, j]

    # ── Parametri problema ────────────────────────────────────────────────────
    user_type_list = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]
    type_probs     = np.array([0.25, 0.45, 0.20, 0.10])
    type_probs    /= type_probs.sum()
    type_indices   = rng.choice(len(user_type_list), size=n_users, p=type_probs)

    # [M5-INT3] user_types come ndarray dtype=object invece di list Python.
    #   Retrocompatibile con Greedy.py (usa user_types[u - 1] con indice intero).
    #   Clarke-Wright sfrutterà fancy indexing vettorizzato su questo array
    #   per costruire Q_arr e TC_arr in un colpo solo senza loop Python.
    user_types: np.ndarray = np.array(
        [user_type_list[i] for i in type_indices], dtype=object
    )

    waste_types = ["organico", "carta", "plastica", "vetro", "indifferenziata"]

    W_base = {
        "organico": 3.0, "carta": 2.0, "plastica": 1.7,
        "vetro": 1.2,    "indifferenziata": 2.5,
    }
    type_multiplier = {
        "single": 0.5, "famiglia": 1.0,
        "palazzina_piccola": 6.0, "palazzina_grande": 20.0,
    }
    W: dict[tuple[str, str], float] = {
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
    x_star: dict[tuple[str, str], float] = {
        (r, t): x_star_base[r] * x_star_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    C: dict[str, float] = {
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
    tc: dict[tuple[str, str], float] = {
        (r, t): tc_base[r] * tc_type_mult[t]
        for r in waste_types for t in user_type_list
    }

    c_fixed: dict[str, float] = {
        "organico": 120.0, "carta": 80.0, "plastica": 70.0,
        "vetro": 110.0,    "indifferenziata": 90.0,
    }

    cd: float = 0.35
    cm: float = 15.0 / 60.0
    L:  float = 480.0

    alpha: float = 10.0
    beta:  float =  2.0

    return {
        "coords":         coords,           # ndarray (n_nodes, 2)
        "adj_matrix":     adj,              # ndarray (n_nodes, n_nodes), inf = assenza arco
        "dist_matrix":    dist_matrix,      # ndarray (n_nodes, n_nodes), shortest-path km
        "time_matrix":    time_matrix,      # ndarray (n_nodes, n_nodes), shortest-path min
        "edges":          edges,            # set[tuple[int,int]], archi (i<j)
        "user_types":     user_types,       # ndarray (n_users,) dtype=object  ← [M5-INT3]
        "W":              W,
        "x_star":         x_star,
        "C":              C,
        "tc":             tc,
        "c_fixed":        c_fixed,
        "cd":             cd,
        "cm":             cm,
        "L":              L,
        "alpha":          alpha,
        "beta":           beta,
        "waste_types":    waste_types,
        "user_type_list": user_type_list,
        "n_users":        n_users,
    }


# ─────────────────────────────────────────────────────────────────────────────
#  plot_graph
# ─────────────────────────────────────────────────────────────────────────────

def plot_graph(data: dict) -> None:
    """Visualizza il grafo del problema SPIL.

    Parameters
    ----------
    data:
        Dizionario restituito da :func:`generate_mock_data`.

    Notes
    -----
    - Archi esistenti in grigio chiaro.
    - Nodo 0 (deposito) come stella rossa.
    - Nodi utente colorati per tipologia.
    """
    coords:     np.ndarray = data["coords"]
    edges:      set        = data["edges"]
    user_types: np.ndarray = data["user_types"]   # ndarray dopo [M5-INT3]

    type_colors: dict[str, str] = {
        "single":            "#378ADD",   # blu
        "famiglia":          "#1D9E75",   # verde
        "palazzina_piccola": "#BA7517",   # ambra
        "palazzina_grande":  "#D85A30",   # corallo
    }

    fig, ax = plt.subplots(figsize=(9, 9))

    # ── Archi ─────────────────────────────────────────────────────────────────
    for (i, j) in edges:
        ax.plot(
            [coords[i, 0], coords[j, 0]],
            [coords[i, 1], coords[j, 1]],
            color="#CCCCCC", linewidth=0.8, zorder=1,
        )

    # ── Nodi utente ───────────────────────────────────────────────────────────
    for u_idx in range(data["n_users"]):
        node_idx = u_idx + 1
        t        = user_types[u_idx]          # accesso ndarray — retrocompatibile
        x, y     = coords[node_idx]
        ax.scatter(x, y, color=type_colors[t],
                   s=120, zorder=3, edgecolors="white", linewidths=0.8)
        ax.text(x + 0.12, y + 0.12, str(node_idx),
                fontsize=7, color="#444441", zorder=4)

    # ── Nodo deposito ─────────────────────────────────────────────────────────
    ax.scatter(*coords[0], color="#E24B4A", s=280, zorder=5,
               marker="*", edgecolors="white", linewidths=0.8)
    ax.text(coords[0, 0] + 0.12, coords[0, 1] + 0.12, "Deposito",
            fontsize=8, fontweight="bold", color="#E24B4A", zorder=6)

    # ── Legenda ───────────────────────────────────────────────────────────────
    legend_handles = [mpatches.Patch(color="#E24B4A", label="Deposito")] + [
        mpatches.Patch(color=c, label=t.replace("_", " ").capitalize())
        for t, c in type_colors.items()
    ]
    ax.legend(handles=legend_handles, loc="upper left",
              fontsize=9, framealpha=0.9, edgecolor="#CCCCCC")

    # ── Stile ─────────────────────────────────────────────────────────────────
    n_edges     = len(edges)
    n_max_edges = (data["n_users"] + 1) * data["n_users"] // 2
    ax.set_title(
        f"Grafo urbano  —  {data['n_users']} utenti  |  "
        f"{n_edges}/{n_max_edges} archi  |  seed={data.get('seed', '?')}",
        fontsize=11, pad=14,
    )
    ax.set_xlabel("x (km)", fontsize=9)
    ax.set_ylabel("y (km)", fontsize=9)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 10.5)
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    plt.show()