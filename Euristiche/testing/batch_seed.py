# batch_seed.py
from __future__ import annotations
import argparse, csv, json, time
from pathlib import Path
import numpy as np
import sys

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
sys.path.insert(0, str(ROOT))

from Generazione_Dati import generate_mock_data, _build_graph, USER_SCENARIOS
from main import calcola_worker_ottimali, X_VALUES
import Greedy
import ClarkeWright as CW

OUT = ROOT / "risultati_seed"
N_MAX, R_FACTOR = 1000, 1.2
B1_N = [100, 250, 500, 750, 1000]
FIELDS = ["bench", "seed", "N", "scenario", "modo", "rifiuto", "X_r", "algoritmo",
          "n_vehicles", "n_utenti_serviti", "F_insoddis", "F_costo_fisso",
          "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo", "k_scala", "algo_time_sec"]


def get_seeds(n: int, path: Path = None) -> list[int]:
    if path is None:
        path = ROOT / "seeds" / "seeds.json"
    if path.exists():
        return json.loads(path.read_text())[:n]
    rng = np.random.default_rng(20261017)
    extra = [int(s) for s in rng.choice(np.arange(1, 1_000_000), size=n, replace=False) if s != 42]
    seeds = [42] + extra[:n - 1]
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(seeds))
    return seeds


def make_base_graph(seed: int, scale: float = 1.0) -> dict:
    rng = np.random.default_rng(seed)
    coords = rng.uniform(0, 10, size=(N_MAX + 1, 2)) * scale
    coords[0] = [5.0 * scale, 5.0 * scale]
    dist, tim, adj, edges = _build_graph(coords, R_FACTOR)
    return {"coords_base": coords, "dist_base": dist, "time_base": tim,
            "adj_base": adj, "edges_base": edges, "n_max": N_MAX, "seed": seed}


def run_instance(data: dict, bench: str, seed: int, N: int, scenario: str, modo: str) -> None:
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{bench}_N{N}_{scenario}_{modo}_seed{seed}.csv"
    if path.exists():
        return
    wt = data["waste_types"]
    nw = calcola_worker_ottimali(data["n_users"])
    res, times = {}, {}
    for name, mod in (("greedy", Greedy), ("clarke_wright", CW)):
        t0 = time.perf_counter()
        res[name] = {r: mod.grid_search(data, r, X_VALUES, max_workers=nw,
                                        gamma=0.5, k_scala=1.0) for r in wt}
        times[name] = time.perf_counter() - t0

    entries = [e for r in wt for e in res["greedy"][r]["all_results"]]
    tot_ins = sum(e["F_insoddis"] for e in entries)
    tot_cost = sum(e["F_costo_fisso"] + e["F_viaggio"] + e["F_lavoro"] for e in entries)
    k = tot_cost / tot_ins if tot_ins else 1.0

    tmp = path.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for name in res:
            for r in wt:
                for e in res[name][r]["all_results"]:
                    served = sum(1 for route in e["routes"]["routes"] for u in route if u != 0)
                    w.writerow({
                        "bench": bench, "seed": seed, "N": N, "scenario": scenario,
                        "modo": modo, "rifiuto": r, "X_r": e["X_r"], "algoritmo": name,
                        "n_vehicles": e["n_vehicles"], "n_utenti_serviti": served,
                        "F_insoddis": round(e["F_insoddis"], 6),
                        "F_costo_fisso": round(e["F_costo_fisso"], 6),
                        "F_viaggio": round(e["F_viaggio"], 6),
                        "F_lavoro": round(e["F_lavoro"], 6),
                        "sat_fisica": round(e["sat_fisica"], 4),
                        "sat_tempo": round(e["sat_tempo"], 4),
                        "k_scala": round(k, 8),
                        "algo_time_sec": round(times[name], 4)})
    tmp.replace(path)


def mix_fabriano() -> np.ndarray:
    from main import UTENTI_JSON
    u = json.load(open(UTENTI_JSON))["utenti"]
    ordine = ["single", "famiglia", "palazzina_piccola", "palazzina_grande"]
    c = np.array([sum(1 for x in u if x["tipologia"] == t) for t in ordine], float)
    return c / c.sum()


def run_seed(seed: int, only: set[str], scale: float = 1.0) -> None:
    bg = make_base_graph(seed, scale) if only & {"B1", "B2", "B3"} else None
    kw = dict(seed=seed, r_factor=R_FACTOR, base_graph_dict=bg)
    if "B1" in only:
        nome, scen, probs = ("B1", "residenziale", None) if scale == 1.0 else ("B1S", "mix_fabriano", mix_fabriano())
        for n in B1_N:
            d = generate_mock_data(n_users=n, user_scenario="residenziale",
                                   custom_type_probs=probs, spatial_mode="uniform", **kw)
            run_instance(d, nome, seed, n, scen, "uniform")
    if "B2" in only:
        for sc in USER_SCENARIOS:
            d = generate_mock_data(n_users=400, user_scenario=sc, spatial_mode="uniform", **kw)
            run_instance(d, "B2", seed, 400, sc, "uniform")
    if "B3" in only:
        d = generate_mock_data(n_users=400, user_scenario="residenziale", spatial_mode="cluster", **kw)
        run_instance(d, "B3", seed, 400, "residenziale", "cluster")
    if "B5" in only:
        d = generate_mock_data(n_users=200, seed=seed, r_factor=R_FACTOR, user_scenario="residenziale")
        run_instance(d, "B5", seed, 200, "residenziale", "std")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-seed", type=int, default=30)
    ap.add_argument("--seeds", default="", help="lista esplicita, es. 42,7")
    ap.add_argument("--bench", default="B1,B2,B3,B5")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else get_seeds(a.n_seed)
    only = set(a.bench.split(","))
    if a.scale != 1.0 and only - {"B1"}: raise SystemExit("con --scale usa solo --bench B1")
    for i, s in enumerate(seeds, 1):
        t0 = time.perf_counter()
        print(f"[{i}/{len(seeds)}] seed {s}", flush=True)
        run_seed(s, only, a.scale)
        print(f"    completato in {time.perf_counter() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
