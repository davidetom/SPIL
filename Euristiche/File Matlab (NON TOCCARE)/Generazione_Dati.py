import numpy as np
from scipy.sparse.csgraph import dijkstra
from scipy.sparse import csr_matrix
from scipy.spatial import KDTree
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter


def generate_mock_data(n_users: int, seed: int, r_factor: float) -> dict:
    """
    Parametri
    ---------
    edge_density : float in (0, 1]
        Frazione di archi aggiuntivi rispetto al massimo possibile,
        aggiunti sopra allo spanning tree. 0 = solo spanning tree (grafo
        sparso), 1 = grafo completo.
    """
    rng = np.random.default_rng(seed)

    n_nodes = n_users + 1
    coords  = rng.uniform(0, 10, size=(n_nodes, 2))
    coords[0] = [5.0, 5.0]

    # ── Costruzione grafo planare con Delaunay ────────────────────────────────

    # 1. Distanze euclidee — broadcasting NumPy, O(N²) vettorizzato.
    #    Evita il doppio loop Python della versione precedente.
    delta     = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    full_dist = np.sqrt((delta ** 2).sum(axis=2))   # shape (n_nodes, n_nodes)

    # 2. Triangolazione di Delaunay + filtraggio con soglia adattiva R.
    #    r_factor moltiplica la distanza media degli archi Delaunay:
    #      1.0 = solo archi nella media (rete sparsa)
    #      1.5 = archi fino al 50% sopra la media
    #      2.0 = rete più densa
    #      np.inf = tutti gli archi Delaunay
    tri = Delaunay(coords)

    all_delaunay_edges = set()
    for simplex in tri.simplices:
        for k in range(3):
            i = int(simplex[k])
            j = int(simplex[(k + 1) % 3])
            all_delaunay_edges.add((min(i, j), max(i, j)))

    mean_edge_dist = np.mean([full_dist[i, j] for (i, j) in all_delaunay_edges])
    R = r_factor * mean_edge_dist

    edges = {
        (i, j)
        for (i, j) in all_delaunay_edges
        if full_dist[i, j] <= R
    }

    # 3. Verifica connessione con Union-Find; ripristino con spanning tree
    #    se il filtraggio per R ha spezzato il grafo in componenti separate.
    parent = list(range(n_nodes))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression
            x = parent[x]
        return x

    def union(x, y):
        parent[find(x)] = find(y)

    for (i, j) in edges:
        union(i, j)

    if len({find(i) for i in range(n_nodes)}) > 1:
        print("  [INFO] Grafo disconnesso, ripristino con Minimum Spanning Tree (SciPy)...")
        from scipy.sparse.csgraph import minimum_spanning_tree
        
        # Calcola l'MST sull'intera matrice delle distanze usando il backend C
        mst = minimum_spanning_tree(full_dist)
        mst_coo = mst.tocoo()
        
        # Aggiunge gli archi dell'MST al nostro set di archi
        for i, j in zip(mst_coo.row, mst_coo.col):
            edges.add((min(i, j), max(i, j)))

    # 4. Costruzione CSR sparsa — direttamente dal set `edges`.
    #
    #    Perché NON usare np.full(..., np.inf) + csr_matrix():
    #      csr_matrix storifica np.inf come valori espliciti, producendo
    #      una matrice "sparsa" con N² elementi non-zero — stessa memoria
    #      e stesso costo computazionale di una matrice densa.
    #
    #    Costruendo da (rows, cols, data_vals) inseriamo solo le ~3N coppie
    #    con arco reale; le celle assenti restano implicitamente a 0, che
    #    Dijkstra interpreta correttamente come assenza di arco.
    #    Ogni arco (i,j) indiretto produce due entry simmetriche.
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

    # 5. Dijkstra multi-sorgente su grafo sparso.
    #
    #    Complessità: O(N · (E + N) log N)
    #    Su grafo planare E ≈ 3N  →  effettivamente O(N² log N)
    #    vs O(N³) di Floyd-Warshall — vantaggio crescente con N.
    #
    #    directed=False: scipy tratta il grafo come simmetrico senza
    #    dover duplicare manualmente gli archi nella logica di visita.
    dist_matrix = dijkstra(graph_csr, directed=False)

    # 6. Matrice dei tempi: derivata da dist_matrix (invariata rispetto prima).
    speed_km_per_min = 25.0 / 60.0
    time_matrix      = dist_matrix / speed_km_per_min

    # 7. Ricostruzione di adj_matrix densa per compatibilità con il resto
    #    del codice (Greedy.py e plot_graph la usano come riferimento).
    #    Le celle senza arco restano a np.inf, come prima.
    adj = np.full((n_nodes, n_nodes), np.inf)
    np.fill_diagonal(adj, 0.0)
    for (i, j) in edges:
        adj[i, j] = full_dist[i, j]
        adj[j, i] = full_dist[i, j]

    # ── Resto invariato dal Modulo 1 v2 ──────────────────────────
    user_type_list = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]
    type_probs     = np.array([0.25, 0.45, 0.20, 0.10])
    type_probs    /= type_probs.sum()
    type_indices   = rng.choice(len(user_type_list), size=n_users, p=type_probs)
    user_types     = [user_type_list[i] for i in type_indices]

    waste_types = ["organico", "carta", "plastica", "vetro", "indifferenziata"]

    W_base = {"organico": 3.0, "carta": 2.0, "plastica": 1.7,
              "vetro": 1.2, "indifferenziata": 2.5}
    type_multiplier = {"single": 0.5, "famiglia": 1.0,
                       "palazzina_piccola": 6.0, "palazzina_grande": 20.0}
    W = {(r, t): W_base[r] * type_multiplier[t]
         for r in waste_types for t in user_type_list}

    x_star_base = {"organico": 2.5, "carta": 1.0, "plastica": 1.7,
                "vetro": 0.5, "indifferenziata": 2.0}
    x_star_type_mult = {"single": 0.7, "famiglia": 1.0,
                        "palazzina_piccola": 1.5, "palazzina_grande": 2.0}
    x_star = {(r, t): x_star_base[r] * x_star_type_mult[t]
            for r in waste_types for t in user_type_list}

    C = {"organico": 1500.0, "carta": 1500.0, "plastica": 1000.0,
         "vetro": 2000.0, "indifferenziata": 2000.0}

    tc_base     = {"organico": 1.2, "carta": 1.0, "plastica": 1.0,
                   "vetro": 1.5, "indifferenziata": 1.2}
    tc_type_mult = {"single": 1.0, "famiglia": 1.0,
                    "palazzina_piccola": 3.0, "palazzina_grande": 3.0}
    tc = {(r, t): tc_base[r] * tc_type_mult[t]
          for r in waste_types for t in user_type_list}

    c_fixed = {"organico": 120.0, "carta": 80.0, "plastica": 70.0,
               "vetro": 110.0, "indifferenziata": 90.0}
    cd = 0.35
    cm = 15.0 / 60.0
    L  = 480.0

    alpha = 10.0
    beta  =  2.0

    return {
        "coords":         coords,
        "adj_matrix":     adj,          # matrice adiacenza originale (con inf)
        "dist_matrix":    dist_matrix,  # shortest path distances
        "time_matrix":    time_matrix,  # shortest path times (minuti)
        "edges":          edges,        # set di archi esistenti (i,j) con i<j
        "user_types":     user_types,
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


# ── Plot grafo ────────────────────────────────────────────────────

def plot_graph(data: dict) -> None:
    """
    Visualizza il grafo del problema:
    - Archi esistenti in grigio
    - Nodo 0 (deposito) in rosso, più grande
    - Nodi utente colorati per tipologia
    """
    coords     = data["coords"]
    edges      = data["edges"]
    user_types = data["user_types"]

    type_colors = {
        "single":           "#378ADD",   # blu
        "famiglia":         "#1D9E75",   # verde
        "palazzina_piccola":"#BA7517",   # ambra
        "palazzina_grande": "#D85A30",   # corallo
    }

    fig, ax = plt.subplots(figsize=(9, 9))

    # ── Archi ────────────────────────────────────────────────────
    for (i, j) in edges:
        x_vals = [coords[i, 0], coords[j, 0]]
        y_vals = [coords[i, 1], coords[j, 1]]
        ax.plot(x_vals, y_vals, color="#CCCCCC", linewidth=0.8, zorder=1)

    # ── Nodi utente ───────────────────────────────────────────────
    for u_idx in range(data["n_users"]):
        node_idx = u_idx + 1            # nodo 0 è il deposito
        t        = user_types[u_idx]
        x, y     = coords[node_idx]
        ax.scatter(x, y,
                   color=type_colors[t],
                   s=120, zorder=3, edgecolors="white", linewidths=0.8)
        ax.text(x + 0.12, y + 0.12, str(node_idx),
                fontsize=7, color="#444441", zorder=4)

    # ── Nodo deposito ─────────────────────────────────────────────
    ax.scatter(*coords[0],
               color="#E24B4A", s=280, zorder=5,
               marker="*", edgecolors="white", linewidths=0.8)
    ax.text(coords[0, 0] + 0.12, coords[0, 1] + 0.12, "Deposito",
            fontsize=8, fontweight="bold", color="#E24B4A", zorder=6)

    # ── Legenda ───────────────────────────────────────────────────
    legend_handles = [
        mpatches.Patch(color="#E24B4A", label="Deposito"),
    ] + [
        mpatches.Patch(color=c, label=t.replace("_", " ").capitalize())
        for t, c in type_colors.items()
    ]
    ax.legend(handles=legend_handles, loc="upper left", fontsize=9,
              framealpha=0.9, edgecolor="#CCCCCC")

    # ── Stile ─────────────────────────────────────────────────────
    n_edges     = len(edges)
    n_max_edges = (data["n_users"] + 1) * data["n_users"] // 2
    ax.set_title(
        f"Grafo urbano  —  {data['n_users']} utenti  |  "
        f"{n_edges}/{n_max_edges} archi  |  seed=42",
        fontsize=11, pad=14
    )
    ax.set_xlabel("x (km)", fontsize=9)
    ax.set_ylabel("y (km)", fontsize=9)
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 10.5)
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", linewidth=0.4, alpha=0.5)

    plt.tight_layout()
    plt.show()