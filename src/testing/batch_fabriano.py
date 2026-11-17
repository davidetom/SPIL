# batch_fabriano.py
# ------------------------------------------------------------------------------
# Uso:
#   python batch_fabriano.py --modo info        # stampa area, densita' e mix tipologico (nessuna run)
#   python batch_fabriano.py                    # B4sub: campioni di utenti reali
#   python batch_fabriano.py --modo sintetico   # B1S: sintetico con area e mix tipologico di Fabriano
# Opzioni:  --N 100,250,500,1000   --n-seed 30
# Le modalita' campioni e sintetico saltano i file gia' presenti in risultati_seed/.
# ------------------------------------------------------------------------------
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
sys.path.insert(0, str(ROOT))

from Generazione_Dati import generate_real_data, generate_mock_data, _build_graph
from main import GRAPHML_PATH, UTENTI_JSON
from batch_seed import get_seeds, run_instance, OUT, R_FACTOR

KEYS = ["W", "x_star", "C", "tc", "c_fixed", "waste_types",
        "cd", "cm", "L", "alpha", "beta"]
TIPI = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]


def fname(bench: str, N: int, scenario: str, modo: str, seed: int):
    return OUT / f"{bench}_N{N}_{scenario}_{modo}_seed{seed}.csv"


def carica_utenti() -> list[dict]:
    with open(UTENTI_JSON, "r", encoding="utf-8") as f:
        return json.load(f)["utenti"]


def area_hull_km2(utenti: list[dict]) -> float:
    xy = np.array([[u["x_utm"], u["y_utm"]] for u in utenti], dtype=float) / 1000.0
    return float(ConvexHull(xy).volume)               # in 2D .volume = area


def mix_tipologico(utenti: list[dict]) -> np.ndarray:
    c = np.array([sum(1 for u in utenti if u["tipologia"] == t) for t in TIPI], dtype=float)
    return c / c.sum()


def stampa_info() -> None:
    utenti = carica_utenti()
    area = area_hull_km2(utenti)
    probs = mix_tipologico(utenti)
    n = len(utenti)
    print(f"Utenti: {n} | area inviluppo = {area:.2f} km2 | densita' = {n / area:.0f} utenti/km2")
    for t, p in zip(TIPI, probs):
        print(f"  {t:<20s} {p * 100:5.1f}%  ({int(round(p * n))} utenti)")


# ------------------------------------------------------------------------------
# Modalita' campioni: sottoinsiemi di utenti reali (B4sub)
# ------------------------------------------------------------------------------
def subsample(full: dict, N: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    chosen = np.sort(rng.choice(full["n_users"], size=N, replace=False))
    keep = np.concatenate([[0], chosen + 1])          # 0 = deposito
    d = {k: full[k] for k in KEYS}
    d["dist_matrix"] = full["dist_matrix"][np.ix_(keep, keep)]
    d["time_matrix"] = full["time_matrix"][np.ix_(keep, keep)]
    d["user_types"] = np.asarray(full["user_types"], dtype=object)[chosen]
    d["n_users"] = N
    return d


def run_campioni(Ns: list[int], seeds: list[int]) -> None:
    todo = [(s, N) for s in seeds for N in Ns
            if not fname("B4sub", N, "reale", "reale", s).exists()]
    if not todo:
        print("Niente da fare: tutti i file B4sub esistono gia'.")
        return
    print("Caricamento mappa reale (30-90 s)...", flush=True)
    full = generate_real_data(graphml_path=GRAPHML_PATH, utenti_json_path=UTENTI_JSON,
                              user_scenario=None, seed=42)
    for i, s in enumerate(seeds, 1):
        t0 = time.perf_counter()
        for N in Ns:
            if fname("B4sub", N, "reale", "reale", s).exists():
                continue
            run_instance(subsample(full, N, s), "B4sub", s, N, "reale", "reale")
        print(f"[{i}/{len(seeds)}] seed {s}: {time.perf_counter() - t0:.0f} s", flush=True)


# ------------------------------------------------------------------------------
# Modalita' sintetico: area e mix tipologico di Fabriano (B1S)
# ------------------------------------------------------------------------------
def base_graph(seed: int, n_max: int, scale: float) -> dict:
    """Come get_or_create_base_graph, ma in memoria e con coordinate scalate."""
    rng = np.random.default_rng(seed)
    coords = rng.uniform(0, 10, size=(n_max + 1, 2)) * scale
    coords[0] = [5.0 * scale, 5.0 * scale]
    dist, tim, adj, edges = _build_graph(coords, R_FACTOR)
    return {"coords_base": coords, "dist_base": dist, "time_base": tim,
            "adj_base": adj, "edges_base": edges, "n_max": n_max, "seed": seed}


def run_sintetico(Ns: list[int], seeds: list[int]) -> None:
    utenti = carica_utenti()
    area = area_hull_km2(utenti)
    scale = (area / 100.0) ** 0.5
    probs = mix_tipologico(utenti)
    n_max = max(Ns)
    print(f"Area Fabriano = {area:.2f} km2 -> scala {scale:.4f} | "
          f"mix {dict(zip(TIPI, np.round(probs, 3).tolist()))} | N_max = {n_max}", flush=True)
    for i, s in enumerate(seeds, 1):
        mancanti = [N for N in Ns if not fname("B1S", N, "mix_fabriano", "uniform", s).exists()]
        if not mancanti:
            continue
        t0 = time.perf_counter()
        bg = base_graph(s, n_max, scale)
        for N in mancanti:
            d = generate_mock_data(n_users=N, seed=s, r_factor=R_FACTOR,
                                   user_scenario="residenziale",
                                   custom_type_probs=probs.copy(),
                                   spatial_mode="uniform", base_graph_dict=bg)
            run_instance(d, "B1S", s, N, "mix_fabriano", "uniform")
        print(f"[{i}/{len(seeds)}] seed {s}: {time.perf_counter() - t0:.0f} s", flush=True)


# ------------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modo", choices=["campioni", "sintetico", "info"], default="campioni")
    ap.add_argument("--N", default=None)
    ap.add_argument("--n-seed", type=int, default=30)
    a = ap.parse_args()
    if a.modo == "info":
        stampa_info()
        return
    default_N = "100,250,500,1000,2000" if a.modo == "campioni" else "100,250,500,1000"
    Ns = [int(x) for x in (a.N or default_N).split(",")]
    seeds = get_seeds(a.n_seed)
    if a.modo == "campioni":
        run_campioni(Ns, seeds)
    else:
        run_sintetico(Ns, seeds)


if __name__ == "__main__":
    main()
