"""
preprocessing_edifici.py
========================
Modulo 14 — Estrazione Edifici e Stima Tipologia Utente.

Legge il file OSM sorgente, estrae i poligoni building=*,
applica i filtri di esclusione (tag non residenziali, area < 20 m²)
e assegna a ogni edificio superstite una tipologia utente SPIL.

Dipende da: nessun output del Modulo 13 (opera direttamente sull'OSM).
Produce per il Modulo 15:
    dati_reali/edifici_candidati.gpkg   — GeoDataFrame in UTM (EPSG:32633)
    dati_reali/edifici_candidati.csv    — tabella per ispezione

Logica di assegnazione tipologia
---------------------------------
    area < 80 m²        →  'single_famiglia'   (poi split 50/50 nel Modulo 15)
    80  – 300 m²        →  'famiglia'
    300 – 800 m²        →  'palazzina_piccola'
    > 800 m²            →  'palazzina_grande'
    + override          →  building=apartments → min 'palazzina_piccola'
                           (indipendentemente dall'area)

Filtri di esclusione (tag)
--------------------------
    industrial, church, cathedral, oratory, school, kindergarten,
    sports_hall, retail, supermarket, hospital, office,
    transformer_tower, train_station, grandstand, stable,
    theatre, hotel, warehouse, greenhouse, carport,
    garage, garages, hut, tower, roof, service

Filtro geometrico
-----------------
    area < AREA_MIN_M2  (default 20 m²)  →  scartato
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon
import xml.etree.ElementTree as ET

# ─────────────────────────────────────────────────────────────────────────────
#  PARAMETRI CONFIGURABILI
# ─────────────────────────────────────────────────────────────────────────────

OSM_FILE:    str   = "map_osm.xml"
OUTPUT_DIR:  Path  = Path("dati_reali")
AREA_MIN_M2: float = 20.0

# Tag building=* da escludere (non residenziali)
SKIP_BUILDING: frozenset[str] = frozenset({
    "industrial", "church", "cathedral", "oratory",
    "school", "kindergarten", "sports_hall",
    "retail", "supermarket", "hospital", "office",
    "transformer_tower", "train_station", "grandstand",
    "stable", "theatre", "hotel", "warehouse",
    "greenhouse", "carport", "garage", "garages",
    "hut", "tower", "roof", "service",
})

# Soglie area → tipologia (ordinate crescenti, ultima è il catch-all)
AREA_THRESHOLDS: list[tuple[float, str]] = [
    (80.0,        "single_famiglia"),
    (300.0,       "famiglia"),
    (800.0,       "palazzina_piccola"),
    (float("inf"), "palazzina_grande"),
]

# Tag che forzano la tipologia minima a 'palazzina_piccola'
APARTMENTS_TAGS: frozenset[str] = frozenset({"apartments"})

# CRS sorgente (WGS84) e destinazione (UTM zona 33N)
CRS_SOURCE = "EPSG:4326"
CRS_TARGET = "EPSG:32633"


# ─────────────────────────────────────────────────────────────────────────────
#  FUNZIONI
# ─────────────────────────────────────────────────────────────────────────────

def _assegna_tipologia(area_m2: float, building_tag: str) -> str:
    """Restituisce la tipologia SPIL in base all'area e al tag OSM."""
    for soglia, label in AREA_THRESHOLDS:
        if area_m2 < soglia:
            tipologia = label
            break

    # Override: condomini espliciti → almeno palazzina_piccola
    if building_tag in APARTMENTS_TAGS and tipologia in ("single_famiglia", "famiglia"):
        tipologia = "palazzina_piccola"

    return tipologia


def estrai_edifici(osm_file: str) -> gpd.GeoDataFrame:
    """Legge il file OSM, estrae i poligoni building e restituisce un GeoDataFrame.

    Pipeline interna:
        1. Parsing XML — raccoglie coordinate di tutti i nodi attivi
        2. Iterazione sulle way con tag building=*
        3. Costruzione Polygon Shapely in WGS84
        4. Creazione GeoDataFrame WGS84 → riproiezione UTM
        5. Calcolo area m² in UTM (preciso)
        6. Filtro tag non residenziali + filtro area < AREA_MIN_M2
        7. Calcolo centroide UTM e coordinate WGS84 del centroide
        8. Assegnazione tipologia

    Returns
    -------
    GeoDataFrame con CRS EPSG:32633, un record per edificio superstite.
    """
    print(f"\n  [1/4] Parsing XML: '{osm_file}'...")
    tree = ET.parse(osm_file)
    root = tree.getroot()

    # Raccogliamo le coordinate (WGS84) di tutti i nodi attivi
    node_coords: dict[str, tuple[float, float]] = {}
    for elem in root:
        if elem.tag == "node" and elem.get("action", "") != "delete":
            node_coords[elem.get("id")] = (
                float(elem.get("lon")),   # Shapely vuole (lon, lat) → (x, y)
                float(elem.get("lat")),
            )

    print(f"        Nodi attivi caricati: {len(node_coords):,}")

    # Itera sui way con building=*
    print("  [2/4] Estrazione poligoni building=*...")
    records: list[dict] = []
    skipped_tag  = 0
    skipped_geom = 0

    for elem in root:
        if elem.tag != "way" or elem.get("action", "") == "delete":
            continue

        tags   = {t.get("k"): t.get("v") for t in elem.findall("tag")}
        btype  = tags.get("building")
        if not btype:
            continue

        # Filtro tag non residenziali — prima di costruire la geometria (più veloce)
        if btype in SKIP_BUILDING:
            skipped_tag += 1
            continue

        # Costruzione poligono Shapely in WGS84
        nd_refs = [nd.get("ref") for nd in elem.findall("nd")]
        ring    = [node_coords[r] for r in nd_refs if r in node_coords]

        if len(ring) < 3:
            skipped_geom += 1
            continue

        poly = Polygon(ring)
        if not poly.is_valid:
            poly = poly.buffer(0)   # correzione topologica standard

        records.append({
            "way_id":       int(elem.get("id")),
            "building_tag": btype,
            "geometry":     poly,
        })

    print(f"        Edifici estratti     : {len(records):,}")
    print(f"        Scartati (tag)       : {skipped_tag:,}")
    print(f"        Scartati (geometria) : {skipped_geom:,}")

    # Costruzione GeoDataFrame WGS84
    gdf_wgs = gpd.GeoDataFrame(records, crs=CRS_SOURCE)

    # Riproiezione in UTM — da qui in poi tutte le misure sono in metri
    print(f"  [3/4] Riproiezione {CRS_SOURCE} → {CRS_TARGET}...")
    gdf_utm = gdf_wgs.to_crs(CRS_TARGET)

    # Calcolo area m² (in UTM, preciso)
    gdf_utm["area_m2"] = gdf_utm.geometry.area

    # Filtro area minima
    before = len(gdf_utm)
    gdf_utm = gdf_utm[gdf_utm["area_m2"] >= AREA_MIN_M2].copy()
    skipped_area = before - len(gdf_utm)
    print(f"        Scartati (area < {AREA_MIN_M2} m²): {skipped_area:,}")
    print(f"        Edifici candidati    : {len(gdf_utm):,}")

    print("  [4/4] Calcolo centroidi e assegnazione tipologie...")

    # Centroide UTM
    centroidi_utm = gdf_utm.geometry.centroid
    gdf_utm["cx_utm"] = centroidi_utm.x
    gdf_utm["cy_utm"] = centroidi_utm.y

    # Centroide in WGS84 (per riferimento geografico e debug)
    transformer = Transformer.from_crs(CRS_TARGET, CRS_SOURCE, always_xy=True)
    lons, lats  = transformer.transform(
        gdf_utm["cx_utm"].values,
        gdf_utm["cy_utm"].values,
    )
    gdf_utm["lon"] = lons
    gdf_utm["lat"] = lats

    # Tipologia
    gdf_utm["tipologia"] = gdf_utm.apply(
        lambda row: _assegna_tipologia(row["area_m2"], row["building_tag"]),
        axis=1,
    )

    # Riordina le colonne per leggibilità
    gdf_utm = gdf_utm[[
        "way_id", "building_tag", "area_m2",
        "cx_utm", "cy_utm", "lon", "lat",
        "tipologia", "geometry",
    ]]

    return gdf_utm.reset_index(drop=True)


def salva_edifici(gdf: gpd.GeoDataFrame, output_dir: Path) -> None:
    """Salva GeoPackage + CSV di ispezione e stampa statistiche."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # GeoPackage — formato principale per il Modulo 15
    gpkg_path = output_dir / "edifici_candidati.gpkg"
    gdf.to_file(gpkg_path, driver="GPKG")
    print(f"\n  → GeoPackage salvato : {gpkg_path.resolve()}")

    # CSV — per ispezione umana (senza colonna geometry)
    csv_path = output_dir / "edifici_candidati.csv"
    gdf.drop(columns=["geometry"]).to_csv(csv_path, index=False)
    print(f"  → CSV salvato        : {csv_path.resolve()}")

    # Statistiche
    counts = gdf["tipologia"].value_counts()
    order  = ["single_famiglia", "famiglia", "palazzina_piccola", "palazzina_grande"]
    total  = len(gdf)

    print(f"\n  ── Distribuzione tipologie ({'edifici candidati: ' + str(total)}) ──")
    for t in order:
        cnt = counts.get(t, 0)
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"     {t:<22}  {cnt:>5}  ({pct:5.1f}%)  {bar}")

    areas = gdf["area_m2"].values
    print(f"\n  ── Statistiche area (m²) ──────────────────────────────")
    for p in [10, 25, 50, 75, 90, 95]:
        print(f"     p{p:>2}  =  {np.percentile(areas, p):>8.1f} m²")
    print(f"     media =  {areas.mean():>8.1f} m²")
    print(f"     min   =  {areas.min():>8.1f} m²")
    print(f"     max   =  {areas.max():>8.1f} m²")


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def preprocessing_edifici(
    osm_file:   str  = OSM_FILE,
    output_dir: Path = OUTPUT_DIR,
) -> gpd.GeoDataFrame:
    """Esegue la pipeline completa e restituisce il GeoDataFrame finale.

    Parameters
    ----------
    osm_file:
        Percorso al file .osm o .osm.xml sorgente.
    output_dir:
        Cartella dove salvare GeoPackage e CSV.

    Returns
    -------
    gpd.GeoDataFrame
        Un record per edificio candidato, CRS EPSG:32633.
    """
    print("\n" + "=" * 56)
    print("  SPIL — Preprocessing Edifici (Modulo 14)")
    print("=" * 56)

    gdf = estrai_edifici(osm_file)
    salva_edifici(gdf, output_dir)

    print("\n  Preprocessing edifici completato.\n")
    return gdf


if __name__ == "__main__":
    import sys

    osm_path = sys.argv[1] if len(sys.argv) > 1 else OSM_FILE
    preprocessing_edifici(osm_file=osm_path)