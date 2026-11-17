"""
Output (nella cartella dati_reali/):
    grafo_stradale.graphml   — grafo NetworkX proiettato in UTM (EPSG:32633)
    nodi_stradali.csv        — tabella nodi con coordinate UTM e WGS84
    archi_stradali.csv       — tabella archi con lunghezza, nome via, geometria WKT

Pipeline interna:
    1. Lettura file OSM locale
    2. Filtraggio archi per tipo highway (solo strade percorribili da veicoli)
    3. Forzatura bidirezionalità
    4. Proiezione CRS WGS84 → UTM zona 33N (EPSG:32633, unità: metri)
    5. Semplificazione topologica (contrazione nodi di grado 2,
       geometria degli archi preservata come LineString)
    6. Estrazione componente connessa principale
    7. Salvataggio GraphML + CSV di ispezione
"""

from __future__ import annotations

import warnings
from pathlib import Path

import networkx as nx
import osmnx as ox
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMETRI CONFIGURABILI
# ─────────────────────────────────────────────────────────────────────────────

# Percorso al file OSM sorgente
OSM_FILE: str = "map_osm.xml"

# Cartella di output
OUTPUT_DIR: Path = Path("dati_reali")

# Tipi di strada percorribili da veicoli di raccolta rifiuti
KEEP_HIGHWAY: set[str] = {
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
    "unclassified",
    "living_street",
    "service",          # filtrato ulteriormente per sottotipo qui sotto
}

# Sottotipi 'service' da mantenere (alley = vicolo carrabile)
KEEP_SERVICE_SUBTYPE: set[str] = {"alley"}

# Velocità media veicolo raccolta (km/h) — usata per calcolare travel_time
SPEED_KMH: float = 25.0


# ─────────────────────────────────────────────────────────────────────────────
#  FUNZIONI
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_tag(value: object) -> str:
    """OSMnx può restituire tag come stringa o come lista: normalizziamo sempre a str."""
    if isinstance(value, list):
        return value[0]
    return str(value) if value is not None else ""


def carica_grafo_raw(osm_file: str) -> nx.MultiDiGraph:
    """Legge il file OSM e restituisce il grafo completo non semplificato."""
    print(f"  [1/6] Caricamento grafo da '{osm_file}'...")
    G = ox.graph_from_xml(
        osm_file,
        bidirectional=False,   # gestiremo noi la bidirezionalità al passo 3
        simplify=False,        # semplificheremo noi dopo il filtraggio
        retain_all=True,       # teniamo tutto, poi estraiamo la componente principale
    )
    print(f"        Grafo raw: {len(G.nodes):>5} nodi, {len(G.edges):>6} archi")
    return G


def filtra_archi(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Rimuove gli archi non percorribili (ferrovia, sentieri, ciclabili, ecc.)."""
    print("  [2/6] Filtraggio archi per tipo highway...")

    edges_to_remove: list[tuple] = []
    for u, v, key, data in G.edges(keys=True, data=True):
        hw = _normalise_tag(data.get("highway", ""))

        if hw not in KEEP_HIGHWAY:
            edges_to_remove.append((u, v, key))
            continue

        # Per 'service' manteniamo solo il sottotipo 'alley'
        if hw == "service":
            svc = _normalise_tag(data.get("service", ""))
            if svc not in KEEP_SERVICE_SUBTYPE:
                edges_to_remove.append((u, v, key))

    G.remove_edges_from(edges_to_remove)

    # Rimuovi nodi rimasti isolati dopo la rimozione degli archi
    isolati = list(nx.isolates(G))
    G.remove_nodes_from(isolati)

    print(f"        Dopo filtraggio: {len(G.nodes):>5} nodi, {len(G.edges):>6} archi")
    return G


def forza_bidirezionalita(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Aggiunge l'arco inverso per ogni arco privo di controparte.

    I veicoli di raccolta rifiuti non rispettano i sensi unici del traffico:
    ogni strada deve essere percorribile in entrambe le direzioni.
    Gli attributi dell'arco originale vengono copiati; viene aggiunto
    il flag reversed=True per tracciabilità.
    """
    print("  [3/6] Forzatura bidirezionalità...")

    edges_to_add: list[tuple[int, int, dict]] = []
    for u, v, data in list(G.edges(data=True)):
        if not G.has_edge(v, u):
            rev_data = dict(data)
            rev_data["reversed"] = True
            edges_to_add.append((v, u, rev_data))

    for u, v, d in edges_to_add:
        G.add_edge(u, v, **d)

    archi_aggiunti = len(edges_to_add)
    print(f"        Archi inversi aggiunti: {archi_aggiunti}")
    print(f"        Dopo bidirez:  {len(G.nodes):>5} nodi, {len(G.edges):>6} archi")
    return G


def proietta_e_semplifica(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Proietta in UTM e semplifica la topologia.

    La proiezione avviene PRIMA della semplificazione perché osmnx.simplify_graph
    usa le coordinate per calcolare le geometrie degli archi contratti,
    e le geometrie devono essere in metri per essere utili nei moduli successivi.
    """
    print("  [4/6] Proiezione WGS84 → UTM (EPSG:32633)...")
    G_proj = ox.project_graph(G)
    crs = G_proj.graph.get("crs", "N/A")
    print(f"        CRS risultante: {crs}")

    print("  [5/6] Semplificazione topologica (contrazione nodi grado-2)...")
    G_simp = ox.simplify_graph(G_proj)
    print(f"        Dopo simplify: {len(G_simp.nodes):>5} nodi, {len(G_simp.edges):>6} archi")
    return G_simp


def estrai_componente_principale(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Mantiene solo la componente connessa più grande."""
    print("  [6/6] Estrazione componente connessa principale...")
    G_und = G.to_undirected()
    componenti = sorted(nx.connected_components(G_und), key=len, reverse=True)

    print(f"        Componenti trovate: {len(componenti)}")
    for i, comp in enumerate(componenti[:3]):
        print(f"          #{i+1}: {len(comp)} nodi")

    nodi_principali = componenti[0]
    G_main = G.subgraph(nodi_principali).copy()
    print(f"        Grafo finale: {len(G_main.nodes):>5} nodi, {len(G_main.edges):>6} archi")
    return G_main


def aggiungi_travel_time(G: nx.MultiDiGraph, speed_kmh: float) -> nx.MultiDiGraph:
    """Aggiunge l'attributo travel_time_min a ogni arco.

    OSMnx calcola già 'length' in metri durante la proiezione.
    travel_time_min = length [m] / (speed_kmh * 1000/60) [m/min]
    """
    speed_m_per_min = speed_kmh * 1000.0 / 60.0
    for u, v, data in G.edges(data=True):
        length_m = data.get("length", 0.0)
        data["travel_time_min"] = length_m / speed_m_per_min
    return G


def salva_output(G: nx.MultiDiGraph, output_dir: Path) -> None:
    """Salva GraphML + CSV di ispezione."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── GraphML (formato principale, letto da Generazione_Dati.py) ────────────
    graphml_path = output_dir / "grafo_stradale.graphml"
    ox.save_graphml(G, filepath=graphml_path)
    print(f"\n  → GraphML salvato:  {graphml_path.resolve()}")

    # ── CSV nodi ─────────────────────────────────────────────────────────────
    nodes_records = []
    for node_id, data in G.nodes(data=True):
        nodes_records.append({
            "node_id":  node_id,
            "x_utm":    data.get("x", float("nan")),   # coordinate UTM (metri)
            "y_utm":    data.get("y", float("nan")),
            "lon_wgs84": data.get("lon", float("nan")), # coordinate geografiche
            "lat_wgs84": data.get("lat", float("nan")),
            "street_count": data.get("street_count", None),
        })
    df_nodes = pd.DataFrame(nodes_records)
    nodes_csv = output_dir / "nodi_stradali.csv"
    df_nodes.to_csv(nodes_csv, index=False)
    print(f"  → Nodi CSV salvato: {nodes_csv.resolve()}")

    # ── CSV archi ─────────────────────────────────────────────────────────────
    edges_records = []
    for u, v, data in G.edges(data=True):
        geom = data.get("geometry", None)
        edges_records.append({
            "u":               u,
            "v":               v,
            "osmid":           data.get("osmid", None),
            "name":            _normalise_tag(data.get("name", "")),
            "highway":         _normalise_tag(data.get("highway", "")),
            "length_m":        round(data.get("length", 0.0), 3),
            "travel_time_min": round(data.get("travel_time_min", 0.0), 4),
            "oneway_original": data.get("oneway", False),
            "reversed":        data.get("reversed", False),
            "geometry_wkt":    geom.wkt if geom is not None else "",
        })
    df_edges = pd.DataFrame(edges_records)
    edges_csv = output_dir / "archi_stradali.csv"
    df_edges.to_csv(edges_csv, index=False)
    print(f"  → Archi CSV salvato: {edges_csv.resolve()}")

    # ── Statistiche finali ────────────────────────────────────────────────────
    lengths = df_edges["length_m"].values
    print(f"\n  ── Statistiche grafo finale ──────────────────────────")
    print(f"     Nodi            : {len(G.nodes)}")
    print(f"     Archi           : {len(G.edges)}")
    print(f"     Lunghezza arco  : media={lengths.mean():.1f} m  "
          f"mediana={float(pd.Series(lengths).median()):.1f} m")
    print(f"     Totale rete     : {lengths.sum()/1000:.2f} km")
    print(f"     CRS             : {G.graph.get('crs', 'N/A')}")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def preprocessing_rete(
    osm_file: str = OSM_FILE,
    output_dir: Path = OUTPUT_DIR,
    speed_kmh: float = SPEED_KMH,
) -> nx.MultiDiGraph:
    """Esegue la pipeline completa e restituisce il grafo finale.

    Parameters
    ----------
    osm_file:
        Percorso al file .osm o .osm.xml sorgente.
    output_dir:
        Cartella dove salvare GraphML e CSV.
    speed_kmh:
        Velocità media veicoli di raccolta (km/h) per il calcolo travel_time.

    Returns
    -------
    nx.MultiDiGraph
        Grafo stradale proiettato in UTM, bidirezionale, semplificato.
    """
    print("\n" + "=" * 56)
    print("  SPIL — Preprocessing Rete Stradale (Modulo 13)")
    print("=" * 56 + "\n")

    G = carica_grafo_raw(osm_file)
    G = filtra_archi(G)
    G = forza_bidirezionalita(G)
    G = proietta_e_semplifica(G)
    G = estrai_componente_principale(G)
    G = aggiungi_travel_time(G, speed_kmh)
    salva_output(G, output_dir)

    print("\n  Preprocessing rete completato.\n")
    return G


if __name__ == "__main__":
    import sys

    osm_path = sys.argv[1] if len(sys.argv) > 1 else OSM_FILE
    preprocessing_rete(osm_file=osm_path)