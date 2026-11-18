"""
Fase 3.1 — Generatore e Runner di Scenari Sperimentali su Grafo Fisso di Fabriano (N = 3932).

Mantiene fissa la topologia stradale reale di Fabriano (3932 utenze + deposito Anconambiente)
e varia su 10 seed:
  Gruppo A (Composizione tipologica, distribuzione spaziale uniforme):
    1. reale_osm          (1 run deterministica, tipologie reali OSM)
    2. omogeneo_leggero   (10 seed, [0.40, 0.55, 0.05, 0.00] — single/famiglie al 95%)
    3. bimodale_70_30     (10 seed, [0.70, 0.00, 0.00, 0.30] — 70% single, 30% palazzina_grande)
    4. condomini_pesante  (10 seed, [0.05, 0.10, 0.25, 0.60] — palazzine/condomini all'85%)
  Gruppo B (Vincolo spaziale Centro vs Periferia a parita' di mix reale Fabriano):
    5. centro_pesante     (10 seed, palazzine grandi/piccole nel nucleo centrale, single in periferia)
    6. periferia_pesante  (10 seed, palazzine grandi/piccole in periferia, single nel centro)

Salva i CSV a 18 colonne (formato standard risultati_seed/) in src/risultati_fabriano/.

Uso (dalla cartella src/):
  python testing/batch_scenari_fabriano.py --modo info
  python testing/batch_scenari_fabriano.py --modo run --n-seed 10
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

TESTING_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTING_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from Generazione_Dati import generate_real_data
import Greedy
import ClarkeWright as CW
from main import GRAPHML_PATH, UTENTI_JSON, X_VALUES, calcola_worker_ottimali

OUT_DIR = SRC_DIR / "risultati_fabriano"
SEEDS_PATH = SRC_DIR / "seeds" / "seeds.json"

TIPI = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]
ORDINE_PESO_DECRESCENTE = ["palazzina_grande", "palazzina_piccola", "famiglia", "single"]

FIELDS = [
    "bench", "seed", "N", "scenario", "modo", "rifiuto", "X_r", "algoritmo",
    "n_vehicles", "n_utenti_serviti", "F_insoddis", "F_costo_fisso",
    "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo", "k_scala", "algo_time_sec",
]

SCENARI_CONFIG: dict[str, dict] = {
    "reale_osm": {
        "modo": "osm",
        "deterministic": True,
        "probs": None,
        "description": "Baseline reale OSM Fabriano (10.6% single, 58.1% famiglia, 26.7% pal. picc., 4.6% pal. gr.)",
    },
    "omogeneo_leggero": {
        "modo": "uniforme",
        "deterministic": False,
        "probs": np.array([0.40, 0.55, 0.05, 0.00], dtype=float),
        "description": "Omogeneo leggero / Villette (40% single, 55% famiglia, 5% pal. picc., 0% pal. gr.)",
    },
    "bimodale_70_30": {
        "modo": "uniforme",
        "deterministic": False,
        "probs": np.array([0.70, 0.00, 0.00, 0.30], dtype=float),
        "description": "Contrasto bimodale 2 tipologie (70% single, 30% palazzina_grande)",
    },
    "condomini_pesante": {
        "modo": "uniforme",
        "deterministic": False,
        "probs": np.array([0.05, 0.10, 0.25, 0.60], dtype=float),
        "description": "Condomini ad alto carico (5% single, 10% famiglia, 25% pal. picc., 60% pal. gr.)",
    },
    "centro_pesante": {
        "modo": "spaziale",
        "deterministic": False,
        "probs": None,
        "spatial_dir": "centro",
        "sigma_noise": 0.12,
        "description": "Mix reale vincolato: utenze pesanti nel centro storico, leggere in periferia",
    },
    "periferia_pesante": {
        "modo": "spaziale",
        "deterministic": False,
        "probs": None,
        "spatial_dir": "periferia",
        "sigma_noise": 0.12,
        "description": "Mix reale vincolato: utenze pesanti in periferia esterna, leggere nel centro",
    },
}


def get_seeds(n: int) -> list[int]:
    if SEEDS_PATH.exists():
        return json.loads(SEEDS_PATH.read_text(encoding="utf-8"))[:n]
    return [42, 665237, 451013, 533047, 710822, 677110, 829813, 385988, 278397, 563579][:n]


def csv_fname(scenario: str, modo: str, N: int, seed: int) -> Path:
    return OUT_DIR / f"FAB_N{N}_{scenario}_{modo}_seed{seed}.csv"


def load_utenti_meta() -> tuple[dict, list[dict], np.ndarray, np.ndarray, np.ndarray, dict[str, int]]:
    """Carica coordinate UTM, distanza dal centro urbano mediano e conteggi reali per tipologia."""
    utenti_path = SRC_DIR / UTENTI_JSON
    raw = json.loads(utenti_path.read_text(encoding="utf-8"))
    deposito = raw["deposito"]
    utenti = raw["utenti"]

    xy = np.array([[float(u["x_utm"]), float(u["y_utm"])] for u in utenti], dtype=float)
    center_xy = np.median(xy, axis=0)
    depot_xy = np.array([float(deposito["x_utm"]), float(deposito["y_utm"])], dtype=float)

    dist_center_m = np.linalg.norm(xy - center_xy, axis=1)
    dist_depot_eucl_m = np.linalg.norm(xy - depot_xy, axis=1)

    real_types = np.array([u["tipologia"] for u in utenti], dtype=object)
    real_counts = {t: int(np.sum(real_types == t)) for t in TIPI}

    return deposito, utenti, real_types, dist_center_m, dist_depot_eucl_m, real_counts


def assign_user_types(
    scenario: str,
    seed: int,
    real_types: np.ndarray,
    dist_center_m: np.ndarray,
    real_counts: dict[str, int],
) -> np.ndarray:
    """
    Genera il vettore user_types (lunghezza N=3932) per lo scenario e il seed specificati:
      - 'reale_osm': restituisce esattamente real_types.
      - 'uniforme' (omogeneo_leggero, bimodale_70_30, condomini_pesante): campionamento i.i.d. con p=probs.
      - 'spaziale' (centro_pesante, periferia_pesante): mantiene i conteggi esatti del mix reale
        (418 single, 2285 famiglia, 1049 palazzina_piccola, 180 palazzina_grande) ordinando i nodi
        per quantile di distanza dal centro urbano perturbato con rumore gaussiano N(0, sigma^2).
    """
    cfg = SCENARI_CONFIG[scenario]
    n_users = len(real_types)

    if scenario == "reale_osm":
        return real_types.copy()

    rng = np.random.default_rng(seed)

    if cfg["modo"] == "uniforme":
        probs = cfg["probs"].copy()
        probs /= probs.sum()
        idx = rng.choice(len(TIPI), size=n_users, p=probs)
        return np.array([TIPI[i] for i in idx], dtype=object)

    if cfg["modo"] == "spaziale":
        # Quantile normalizzato in [0, 1] della distanza dal centro urbano mediano
        order_base = np.argsort(dist_center_m, kind="stable")
        rank_norm = np.empty(n_users, dtype=float)
        rank_norm[order_base] = np.linspace(0.0, 1.0, n_users)

        sigma = float(cfg.get("sigma_noise", 0.12))
        noisy_score = rank_norm + rng.normal(0.0, sigma, size=n_users)

        if cfg["spatial_dir"] == "centro":
            # I punteggi piu' bassi (centro) ricevono le utenze piu' pesanti
            sorted_nodes = np.argsort(noisy_score, kind="stable")
        else:
            # I punteggi piu' alti (periferia) ricevono le utenze piu' pesanti
            sorted_nodes = np.argsort(-noisy_score, kind="stable")

        user_types = np.empty(n_users, dtype=object)
        cursor = 0
        for t in ORDINE_PESO_DECRESCENTE:
            cnt = real_counts[t]
            user_types[sorted_nodes[cursor : cursor + cnt]] = t
            cursor += cnt
        assert cursor == n_users, f"Conteggio utenti non corrispondente: {cursor} != {n_users}"
        return user_types

    raise ValueError(f"Modo non riconosciuto per lo scenario '{scenario}'")


def stampa_info_scenari(seeds: list[int]) -> None:
    """Stampa diagnostica completa dei 6 scenari senza lanciare il solver di routing."""
    deposito, utenti, real_types, dist_center_m, dist_depot_eucl_m, real_counts = load_utenti_meta()
    n_users = len(utenti)
    mult_w = {"single": 0.5, "famiglia": 1.0, "palazzina_piccola": 6.0, "palazzina_grande": 20.0}

    print("=" * 96)
    print(f"  DIAGNOSTICA SCENARI FABRIANO — N = {n_users} utenze fisse | Deposito: {deposito['via']}")
    print("=" * 96)

    for sc_name, cfg in SCENARI_CONFIG.items():
        s_test = 42 if cfg["deterministic"] else seeds[0]
        ut = assign_user_types(sc_name, s_test, real_types, dist_center_m, real_counts)
        counts = {t: int(np.sum(ut == t)) for t in TIPI}
        unita_eq = sum(counts[t] * mult_w[t] for t in TIPI)

        print(f"\n▶ Scenario: {sc_name:<20} | Modo: {cfg['modo']:<10} | Run previste: {1 if cfg['deterministic'] else len(seeds)}")
        print(f"  Descrizione : {cfg['description']}")
        print(f"  Carico eq.  : {unita_eq:,.1f} unita'-famiglia equivalenti (es. seed={s_test})")
        print(f"  {'Tipologia':<20} {'Conteggio':>10} {'Quota %':>9} {'Dist. Centro (m)':>18} {'Dist. Deposito (m)':>20}")
        print(f"  {'-'*20} {'-'*10} {'-'*9} {'-'*18} {'-'*20}")
        for t in TIPI:
            mask = (ut == t)
            cnt = counts[t]
            pct = cnt / n_users * 100.0
            mc = float(dist_center_m[mask].mean()) if cnt > 0 else 0.0
            md = float(dist_depot_eucl_m[mask].mean()) if cnt > 0 else 0.0
            print(f"  {t:<20} {cnt:>10d} {pct:>8.1f}% {mc:>17.0f}m {md:>19.0f}m")
    print("=" * 96)


def run_single_scenario_seed(
    base_data: dict,
    user_types: np.ndarray,
    scenario: str,
    modo: str,
    seed: int,
    n_workers: int,
) -> Path:
    """Esegue Greedy e Clarke-Wright per uno specifico (scenario, seed) e salva il CSV a 18 colonne."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_users = base_data["n_users"]
    out_path = csv_fname(scenario, modo, n_users, seed)
    if out_path.exists():
        return out_path

    # Clona il dizionario dati condividendo le matrici pesanti (read-only) e sostituendo user_types
    data = dict(base_data)
    data["user_types"] = user_types
    data["scenario_label"] = scenario
    data["spatial_mode"] = modo

    wt = data["waste_types"]
    res, times = {}, {}

    for algo_name, mod in (("greedy", Greedy), ("clarke_wright", CW)):
        t0 = time.perf_counter()
        res[algo_name] = {
            r: mod.grid_search(data, r, X_VALUES, max_workers=n_workers, gamma=0.5, k_scala=1.0)
            for r in wt
        }
        times[algo_name] = time.perf_counter() - t0

    # Calcolo k_scala M0 (somma su tutta la griglia di Greedy)
    entries_g = [e for r in wt for e in res["greedy"][r]["all_results"]]
    tot_ins = sum(e["F_insoddis"] for e in entries_g)
    tot_cost = sum(e["F_costo_fisso"] + e["F_viaggio"] + e["F_lavoro"] for e in entries_g)
    k_scala = tot_cost / tot_ins if tot_ins > 0 else 1.0

    tmp_path = out_path.with_suffix(".tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for algo_name in ("greedy", "clarke_wright"):
            for r in wt:
                for e in res[algo_name][r]["all_results"]:
                    served = sum(1 for route in e["routes"]["routes"] for u in route if u != 0)
                    writer.writerow({
                        "bench": "FAB",
                        "seed": seed,
                        "N": n_users,
                        "scenario": scenario,
                        "modo": modo,
                        "rifiuto": r,
                        "X_r": e["X_r"],
                        "algoritmo": algo_name,
                        "n_vehicles": e["n_vehicles"],
                        "n_utenti_serviti": served,
                        "F_insoddis": round(e["F_insoddis"], 6),
                        "F_costo_fisso": round(e["F_costo_fisso"], 6),
                        "F_viaggio": round(e["F_viaggio"], 6),
                        "F_lavoro": round(e["F_lavoro"], 6),
                        "sat_fisica": round(e["sat_fisica"], 4),
                        "sat_tempo": round(e["sat_tempo"], 4),
                        "k_scala": round(k_scala, 8),
                        "algo_time_sec": round(times[algo_name], 4),
                    })
    tmp_path.replace(out_path)
    return out_path


def run_batch(scenari_list: list[str], seeds: list[int]) -> None:
    _, _, real_types, dist_center_m, _, real_counts = load_utenti_meta()
    n_users = len(real_types)

    # Costruisce la coda di lavoro saltando i CSV gia' presenti
    tasks: list[tuple[str, str, int]] = []
    for sc in scenari_list:
        cfg = SCENARI_CONFIG[sc]
        sc_seeds = [42] if cfg["deterministic"] else seeds
        for s in sc_seeds:
            if not csv_fname(sc, cfg["modo"], n_users, s).exists():
                tasks.append((sc, cfg["modo"], s))

    if not tasks:
        print(f"Tutti i CSV richiesti esistono gia' in '{OUT_DIR}'. Nessuna nuova run necessaria.")
        return

    print(f"[1/2] Caricamento unico grafo reale Fabriano e matrici Dijkstra (N={n_users})...", flush=True)
    t_load = time.perf_counter()
    base_data = generate_real_data(
        graphml_path=str(SRC_DIR / GRAPHML_PATH),
        utenti_json_path=str(SRC_DIR / UTENTI_JSON),
        user_scenario=None,
        seed=42,
    )
    n_workers = calcola_worker_ottimali(n_users)
    print(f"      Grafo caricato in {time.perf_counter() - t_load:.1f} s | Worker paralleli: {n_workers}", flush=True)

    print(f"[2/2] Avvio {len(tasks)} esecuzioni su Fabriano...", flush=True)
    for idx, (sc, modo, s) in enumerate(tasks, 1):
        t0 = time.perf_counter()
        ut = assign_user_types(sc, s, real_types, dist_center_m, real_counts)
        out_p = run_single_scenario_seed(base_data, ut, sc, modo, s, n_workers)
        dt = time.perf_counter() - t0
        print(f"  [{idx:>2d}/{len(tasks)}] {sc:<20} | seed={s:<7d} -> {out_p.name} ({dt:.1f} s)", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generatore e runner scenari Fabriano (Fase 3.1)")
    ap.add_argument("--modo", choices=["info", "run"], default="run")
    ap.add_argument(
        "--scenari",
        default=",".join(SCENARI_CONFIG.keys()),
        help=f"Lista scenari separati da virgola (disponibili: {list(SCENARI_CONFIG.keys())})",
    )
    ap.add_argument("--n-seed", type=int, default=10, help="Numero di seed per gli scenari stocastici (default: 10)")
    ap.add_argument("--seeds", default="", help="Lista esplicita di seed separati da virgola (es. 42,665237)")
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",")] if args.seeds else get_seeds(args.n_seed)
    scenari_list = [s.strip() for s in args.scenari.split(",") if s.strip()]
    for sc in scenari_list:
        if sc not in SCENARI_CONFIG:
            raise SystemExit(f"Scenario '{sc}' non valido. Scegli tra: {list(SCENARI_CONFIG.keys())}")

    if args.modo == "info":
        stampa_info_scenari(seeds)
    else:
        run_batch(scenari_list, seeds)


if __name__ == "__main__":
    main()
