"""
preprocessing_proiezione.py
===========================
Modulo 15 — Proiezione Edifici su Archi e Grafo Aumentato.

Ogni edificio candidato (output Modulo 14) viene proiettato
sull'arco stradale più vicino (output Modulo 13) e inserito
come nodo utente nel grafo, spezzando l'arco in due sotto-archi.

Dipende da:
    dati_reali/grafo_stradale.graphml   (Modulo 13)
    dati_reali/edifici_candidati.gpkg   (Modulo 14)

Produce:
    dati_reali/grafo_aumentato.graphml  — grafo con nodi utente inseriti
    dati_reali/utenti.json              — lista nodi utente con tipologia

Convenzioni sui nodi
---------------------
    Nodi stradali originali : ID OSM interi (es. 1469850360)
    Nodi utente inseriti    : ID sintetici negativi (-1, -2, ...)
                              per evitare collisioni con gli ID OSM

Spezzamento arco
----------------
    Arco originale (u → v), lunghezza L, geometria G.
    Edificio proiettato in posizione t lungo G (0 ≤ t ≤ L).
    Risultato: (u → w) con lunghezza t  +  (w → v) con lunghezza L-t.
    Attributi (travel_time_min, highway, name, ...) scalati/copiati.

    Se più edifici proiettano sullo stesso arco (u,v), vengono
    ordinati per posizione lineare e l'arco viene spezzato in una
    sola passata, producendo la catena u → w1 → w2 → ... → v.
    Questo evita di cercare un arco già rimosso dal grafo.

    Gli archi bidirezionali (u→v e v→u) vengono gestiti
    indipendentemente: ogni direzione viene spezzata separatamente,
    mantenendo la simmetria.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points, substring
import warnings

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMETRI
# ─────────────────────────────────────────────────────────────────────────────

GRAPHML_IN:  Path = Path("dati_reali/grafo_stradale.graphml")
GPKG_IN:     Path = Path("dati_reali/edifici_candidati.gpkg")
OUTPUT_DIR:  Path = Path("dati_reali")

# Velocità per ricalcolo travel_time sui sotto-archi
SPEED_KMH: float = 25.0

# Seed per il campionamento 50/50 single/famiglia
SEED_TIPOLOGIA: int = 42


# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _edge_geometry(G: nx.MultiDiGraph, u: int, v: int, data: dict) -> LineString:
    """Restituisce la geometria LineString dell'arco (u,v).

    Se l'arco non ha geometria esplicita (archi brevi tra nodi adiacenti
    senza forma intermedia), costruisce una linea retta dai nodi.
    """
    geom = data.get("geometry")
    if geom is not None:
        return geom
    xu, yu = G.nodes[u]["x"], G.nodes[u]["y"]
    xv, yv = G.nodes[v]["x"], G.nodes[v]["y"]
    return LineString([(xu, yu), (xv, yv)])


def _split_attributes(data: dict, geom: LineString) -> dict:
    """Costruisce gli attributi di un sotto-arco dalla sua geometria effettiva.

    La lunghezza viene sempre calcolata direttamente dalla geometria Shapely,
    evitando errori numerici da differenze aritmetiche di posizioni lineari.

    Parameters
    ----------
    data:
        Attributi dell'arco originale (per copiare campi non geometrici).
    geom:
        Geometria LineString del sotto-arco già ritagliata.

    Returns
    -------
    dict : attributi del sotto-arco, pronti per G.add_edge().
    """
    speed_m_per_min = SPEED_KMH * 1000.0 / 60.0
    length_m        = max(geom.length, 0.01)   # floor 1 cm per evitare div/0

    attr = {k: v for k, v in data.items()
            if k not in ("geometry", "length", "travel_time_min")}
    attr["geometry"]         = geom
    attr["length"]           = length_m
    attr["travel_time_min"]  = length_m / speed_m_per_min
    return attr


def _risolvi_tipologia(tipologia_raw: str, rng: np.random.Generator) -> str:
    """Risolve 'single_famiglia' in 'single' o 'famiglia' con prob. 50/50."""
    if tipologia_raw == "single_famiglia":
        return rng.choice(["single", "famiglia"])
    return tipologia_raw


# ─────────────────────────────────────────────────────────────────────────────
#  CORE — costruzione indice spaziale e proiezione
# ─────────────────────────────────────────────────────────────────────────────

def _build_edge_index(G: nx.MultiDiGraph) -> tuple[list, list]:
    """Costruisce la lista degli archi con geometria per l'indice spaziale STRtree.

    Considera solo una direzione per arco (u < v o la prima trovata)
    per evitare di proiettare lo stesso edificio due volte sullo stesso
    segmento fisico. La simmetria viene ripristinata durante lo spezzamento.

    Returns
    -------
    edges_list : list of (u, v, data, geom)
    geoms      : list of LineString (stesso ordine, per STRtree)
    """
    seen: set[frozenset] = set()
    edges_list = []
    geoms      = []

    for u, v, data in G.edges(data=True):
        key = frozenset([u, v])
        if key in seen:
            continue
        seen.add(key)
        geom = _edge_geometry(G, u, v, data)
        edges_list.append((u, v, data, geom))
        geoms.append(geom)

    return edges_list, geoms


def proietta_edifici(
    G:   nx.MultiDiGraph,
    gdf: gpd.GeoDataFrame,
    rng: np.random.Generator,
) -> tuple[nx.MultiDiGraph, list[dict]]:
    """Proietta ogni edificio sull'arco più vicino e inserisce il nodo nel grafo.

    Parameters
    ----------
    G:
        Grafo stradale (verrà modificato in-place).
    gdf:
        GeoDataFrame edifici candidati (Modulo 14).
    rng:
        Generatore NumPy per il campionamento single/famiglia.

    Returns
    -------
    G:
        Grafo aumentato con i nodi utente inseriti.
    utenti:
        Lista di dict con metadati di ogni nodo utente.
    """
    from shapely.strtree import STRtree

    print("  [1/3] Costruzione indice spaziale archi...")
    edges_list, geoms = _build_edge_index(G)
    tree = STRtree(geoms)
    print(f"        Archi indicizzati (unici): {len(edges_list)}")

    print("  [2/3] Proiezione centroidi edifici sugli archi...")

    # Raggruppa edifici per arco più vicino.
    # edge_to_buildings[edge_idx] = lista di (pos_lineare, way_id, tipologia_raw, cx, cy)
    edge_to_buildings: dict[int, list] = defaultdict(list)

    for _, row in gdf.iterrows():
        pt        = row.geometry.centroid
        edge_idx  = tree.nearest(pt)
        edge_geom = geoms[edge_idx]

        # Punto più vicino sull'arco (gestisce correttamente qualsiasi LineString)
        pt_on_edge = nearest_points(edge_geom, pt)[0]
        pos_linear = edge_geom.project(pt_on_edge)   # metri dall'inizio arco

        edge_to_buildings[edge_idx].append((
            pos_linear,
            int(row["way_id"]),
            row["tipologia"],
            pt_on_edge.x,
            pt_on_edge.y,
        ))

    print(f"        Archi con almeno un edificio: {len(edge_to_buildings)}")

    # ── Spezzamento archi e inserimento nodi ──────────────────────────────────
    print("  [3/3] Inserimento nodi utente nel grafo...")

    utenti:    list[dict] = []
    user_id_counter = -1     # ID sintetici negativi per i nodi utente

    for edge_idx, items in edge_to_buildings.items():
        u_orig, v_orig, data_orig, geom_orig = edges_list[edge_idx]
        length_total = geom_orig.length

        # Ordina gli edifici per posizione lineare crescente
        items_sorted = sorted(items, key=lambda x: x[0])

        # ── Spezza l'arco in una sola passata ────────────────────────────────
        #
        # Catena: u_orig → w1 → w2 → ... → wN → v_orig
        # I nodi sintetici wI vengono inseriti nell'ordine delle posizioni.
        # Gestiamo entrambe le direzioni (u→v e v→u) del grafo bidirezionale.

        current_start_node  = u_orig
        current_pos_offset  = 0.0   # offset accumulato lungo l'arco

        for (pos, way_id, tipologia_raw, wx, wy) in items_sorted:

            # Clamp: pos deve stare in (offset, length_total)
            # Soglia minima 1.0 m per evitare sotto-archi degeneri
            MIN_SEGMENT = 1.0
            pos_clamped = max(current_pos_offset + MIN_SEGMENT,
                              min(pos, length_total - MIN_SEGMENT))
            t_local = pos_clamped - current_pos_offset

            # Se il sotto-arco risultante è ancora degenere (edificio
            # proiettato esattamente su un estremo), collegalo direttamente
            # al nodo stradale corrente senza spezzare l'arco.
            if t_local < MIN_SEGMENT:
                wid = user_id_counter
                user_id_counter -= 1
                tipologia = _risolvi_tipologia(tipologia_raw, rng)
                G.add_node(wid, x=wx, y=wy,
                           tipologia=tipologia,
                           way_id=way_id,
                           is_user=True)
                utenti.append({
                    "node_id":   wid,
                    "way_id":    way_id,
                    "tipologia": tipologia,
                    "x_utm":     wx,
                    "y_utm":     wy,
                })
                # Arco diretto nodo_stradale ↔ nodo_utente (1 m simbolico)
                stub_attr = {k: v for k, v in data_orig.items()
                             if k not in ("geometry", "length", "travel_time_min")}
                stub_attr["length"]          = 1.0
                stub_attr["travel_time_min"] = 1.0 / (SPEED_KMH * 1000.0 / 60.0)
                stub_attr["geometry"]        = LineString([
                    (G.nodes[current_start_node]["x"], G.nodes[current_start_node]["y"]),
                    (wx, wy)
                ])
                G.add_edge(current_start_node, wid, **stub_attr)
                G.add_edge(wid, current_start_node, **{**stub_attr, "reversed": True})
                continue  # non aggiorna current_start_node né current_pos_offset

            # Crea nodo utente
            wid = user_id_counter
            user_id_counter -= 1

            tipologia = _risolvi_tipologia(tipologia_raw, rng)

            G.add_node(wid, x=wx, y=wy,
                       tipologia=tipologia,
                       way_id=way_id,
                       is_user=True)

            utenti.append({
                "node_id":   wid,
                "way_id":    way_id,
                "tipologia": tipologia,
                "x_utm":     wx,
                "y_utm":     wy,
            })

            # Geometria del sotto-arco current_start → w
            # substring() usa offset assoluti lungo la geometria originale.
            try:
                geom_sw = substring(geom_orig, current_pos_offset, pos_clamped)
                if geom_sw is None or geom_sw.is_empty or geom_sw.length < 0.01:
                    raise ValueError("geometria degenere")
            except Exception:
                geom_sw = LineString([
                    (G.nodes[current_start_node]["x"], G.nodes[current_start_node]["y"]),
                    (wx, wy),
                ])

            # Attributi calcolati direttamente dalla geometria ritagliata
            attr_sw = _split_attributes(data_orig, geom_sw)

            # Aggiunge archi bidirezionali current_start ↔ w
            G.add_edge(current_start_node, wid, **attr_sw)
            G.add_edge(wid, current_start_node, **{**attr_sw, "reversed": True})

            current_start_node = wid
            current_pos_offset = pos_clamped

        # ── Arco finale: ultimo nodo utente → v_orig ─────────────────────────
        try:
            geom_final = substring(geom_orig, current_pos_offset, length_total)
            if geom_final is None or geom_final.is_empty or geom_final.length < 0.01:
                raise ValueError("geometria degenere")
        except Exception:
            xw = G.nodes[current_start_node]["x"]
            yw = G.nodes[current_start_node]["y"]
            xv = G.nodes[v_orig]["x"]
            yv = G.nodes[v_orig]["y"]
            geom_final = LineString([(xw, yw), (xv, yv)])

        attr_final = _split_attributes(data_orig, geom_final)
        G.add_edge(current_start_node, v_orig, **attr_final)
        G.add_edge(v_orig, current_start_node, **{**attr_final, "reversed": True})

        # ── Rimozione arco originale (entrambe le direzioni) ──────────────────
        if G.has_edge(u_orig, v_orig):
            G.remove_edge(u_orig, v_orig)
        if G.has_edge(v_orig, u_orig):
            G.remove_edge(v_orig, u_orig)

    return G, utenti


# ─────────────────────────────────────────────────────────────────────────────
#  SALVATAGGIO
# ─────────────────────────────────────────────────────────────────────────────

def salva_output(
    G:          nx.MultiDiGraph,
    utenti:     list[dict],
    output_dir: Path,
) -> None:
    """Salva grafo aumentato (GraphML) e lista utenti (JSON)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # GraphML — attributi geometry devono essere serializzati come WKT
    # osmnx.save_graphml gestisce automaticamente la geometria Shapely
    graphml_path = output_dir / "grafo_aumentato.graphml"
    ox.save_graphml(G, filepath=graphml_path)
    print(f"\n  → GraphML aumentato : {graphml_path.resolve()}")

    # JSON utenti
    json_path = output_dir / "utenti.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(utenti, f, ensure_ascii=False, indent=2)
    print(f"  → JSON utenti       : {json_path.resolve()}")

    # Statistiche
    n_utenti = len(utenti)
    from collections import Counter
    tip_counts = Counter(u["tipologia"] for u in utenti)
    order = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]

    print(f"\n  ── Nodi utente inseriti: {n_utenti} ─────────────────────────")
    for t in order:
        cnt = tip_counts.get(t, 0)
        pct = cnt / n_utenti * 100 if n_utenti else 0
        bar = "█" * int(pct / 2)
        print(f"     {t:<22}  {cnt:>5}  ({pct:5.1f}%)  {bar}")

    print(f"\n  ── Grafo aumentato ────────────────────────────────────────")
    print(f"     Nodi totali  : {G.number_of_nodes():>6}  "
          f"(stradali: {G.number_of_nodes() - n_utenti}, utenti: {n_utenti})")
    print(f"     Archi totali : {G.number_of_edges():>6}")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def preprocessing_proiezione(
    graphml_in:  Path = GRAPHML_IN,
    gpkg_in:     Path = GPKG_IN,
    output_dir:  Path = OUTPUT_DIR,
    seed:        int  = SEED_TIPOLOGIA,
) -> tuple[nx.MultiDiGraph, list[dict]]:
    """Esegue la pipeline completa e restituisce grafo aumentato + lista utenti.

    Parameters
    ----------
    graphml_in:
        Percorso al grafo stradale (output Modulo 13).
    gpkg_in:
        Percorso agli edifici candidati (output Modulo 14).
    output_dir:
        Cartella di output.
    seed:
        Seed per il campionamento stocastico single/famiglia.

    Returns
    -------
    G_aug : nx.MultiDiGraph — grafo con nodi utente inseriti
    utenti : list[dict]     — metadati nodi utente
    """
    print("\n" + "=" * 56)
    print("  SPIL — Proiezione Edifici su Grafo (Modulo 15)")
    print("=" * 56 + "\n")

    print(f"  Caricamento grafo stradale: '{graphml_in}'...")
    G = ox.load_graphml(graphml_in)
    print(f"  Grafo base: {G.number_of_nodes()} nodi, {G.number_of_edges()} archi")

    print(f"\n  Caricamento edifici candidati: '{gpkg_in}'...")
    gdf = gpd.read_file(gpkg_in)
    print(f"  Edifici candidati: {len(gdf)}")

    rng = np.random.default_rng(seed)

    G_aug, utenti = proietta_edifici(G, gdf, rng)
    salva_output(G_aug, utenti, output_dir)

    print("\n  Proiezione completata.\n")
    return G_aug, utenti


if __name__ == "__main__":
    import sys

    graphml_path = Path(sys.argv[1]) if len(sys.argv) > 1 else GRAPHML_IN
    gpkg_path    = Path(sys.argv[2]) if len(sys.argv) > 2 else GPKG_IN
    preprocessing_proiezione(graphml_in=graphml_path, gpkg_in=gpkg_path)