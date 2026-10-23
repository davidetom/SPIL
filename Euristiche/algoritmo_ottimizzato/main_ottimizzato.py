# main_ottimizzato.py
# ------------------------------------------------------------------------------
# Ricerca potata della griglia di frequenze (proposta di miglioramento, Benchmark Trasversale 2).
#
# Idea: F_insoddis(X_r) dipende solo da X_r e dalle frequenze ideali degli utenti, quindi si calcola
# su tutta la griglia SENZA routing. Sia X_min il punto della griglia con disservizio minimo.
# Per X > X_min il disservizio non diminuisce; se nemmeno il costo logistico diminuisce, ogni X > X_min
# e' dominata da X_min per qualunque gamma e k_scala e non serve instradarla.
# Si instradano quindi solo le X <= X_min (la condizione sul costo e' verificata da test_ottimizzato.py).
#
# Per ogni istanza gia' calcolata (stesso seed -> stessa istanza di batch_seed/batch_fabriano):
#   - "completa": tutte le 12 X di tutti i rifiuti in un unico pool di processi
#   - "potata"  : solo le X <= X_min, stesso pool  -> stesso overhead, confronto di tempi equo
# Output (cartella risultati_ottimizzati/): righe.csv, tempi.csv, potatura.csv
#
# Uso (dalla cartella Euristiche/, come batch_seed.py):
#   python algoritmo_ottimizzato/main_ottimizzato.py                # piano standard (stima a video prima di partire)
#   python algoritmo_ottimizzato/main_ottimizzato.py --stima        # solo stima dei tempi, nessun calcolo
#   python algoritmo_ottimizzato/main_ottimizzato.py --solo-potata  # salta la griglia completa (meta' tempo, niente confronto tempi)
#   python algoritmo_ottimizzato/main_ottimizzato.py --max-minuti 50
# ------------------------------------------------------------------------------
from __future__ import annotations

import argparse
import csv
import json
import resource
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent            # cartella Euristiche/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "testing"))

import Greedy
import ClarkeWright as CW
from Generazione_Dati import generate_mock_data
from main import calcola_worker_ottimali, X_VALUES
from testing.batch_seed import make_base_graph, R_FACTOR

RAW = ROOT / "risultati_seed"
B4_CSV = ROOT / "risultati_csv" / "risultati_3932u_mappa_reale_gamma0.50.csv"
OUT = ROOT / "risultati_ottimizzati"
ALGO = {"greedy": Greedy, "clarke_wright": CW}
CHIAVI_DATI = ("n_users", "dist_matrix", "time_matrix", "user_types", "W", "tc", "C", "L",
               "c_fixed", "cd", "cm", "x_star", "alpha", "beta", "waste_types")
CAMPI = ("n_vehicles", "F_insoddis", "F_costo_fisso", "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo")
KI = ["bench", "N", "scenario", "modo", "seed"]

# (bench, N, scenario, modo, numero di seed): 29 istanze, circa 20-30 minuti su un portatile
PIANO = [("B1", 100, "residenziale", "uniform", 4),
         ("B1", 500, "residenziale", "uniform", 4),
         ("B1", 1000, "residenziale", "uniform", 4),
         ("B2", 400, "residenziale", "uniform", 3),
         ("B2", 400, "villette", "uniform", 3),
         ("B2", 400, "grandi_condomini", "uniform", 3),
         ("B5", 200, "residenziale", "std", 3),
         ("B4sub", 1000, "reale", "reale", 2),
         ("B4sub", 2000, "reale", "reale", 2),
         ("B4", 3932, "reale", "reale", 1)]


# ------------------------------------------------------------------------------
# Istanze: ricostruzione identica a batch_seed / batch_fabriano
# ------------------------------------------------------------------------------
def csv_riferimento(bench: str, N: int, scenario: str, modo: str, seed: int) -> Path:
    return B4_CSV if bench == "B4" else RAW / f"{bench}_N{N}_{scenario}_{modo}_seed{seed}.csv"


class Istanze:
    def __init__(self) -> None:
        self._bg: dict[int, dict] = {}
        self._fabriano: dict | None = None

    def _base(self, seed: int) -> dict:
        if seed not in self._bg:
            self._bg[seed] = make_base_graph(seed)            # rete da 1000 nodi, circa 25 MB per seed
        return self._bg[seed]

    def _reale(self) -> dict:
        if self._fabriano is None:
            from Generazione_Dati import generate_real_data
            from main import GRAPHML_PATH, UTENTI_JSON
            print("  caricamento mappa reale (30-90 s)...", flush=True)
            self._fabriano = generate_real_data(graphml_path=ROOT / GRAPHML_PATH, utenti_json_path=ROOT / UTENTI_JSON,
                                                user_scenario=None, seed=42)
        return self._fabriano

    def dati(self, bench: str, N: int, scenario: str, modo: str, seed: int) -> dict:
        if bench == "B1":
            d = generate_mock_data(n_users=N, user_scenario="residenziale", custom_type_probs=None,
                                   spatial_mode="uniform", seed=seed, r_factor=R_FACTOR,
                                   base_graph_dict=self._base(seed))
        elif bench in ("B2", "B3"):
            d = generate_mock_data(n_users=N, user_scenario=scenario, spatial_mode=modo,
                                   seed=seed, r_factor=R_FACTOR, base_graph_dict=self._base(seed))
        elif bench == "B5":
            d = generate_mock_data(n_users=N, seed=seed, r_factor=R_FACTOR, user_scenario="residenziale")
        elif bench == "B4sub":
            from testing.batch_fabriano import subsample
            d = subsample(self._reale(), N, seed)
        elif bench == "B4":
            d = self._reale()
        else:
            raise ValueError(bench)
        return {k: d[k] for k in CHIAVI_DATI}                # solo cio' che serve al routing


# ------------------------------------------------------------------------------
# Potatura: X_min = argmin del disservizio sulla griglia (nessun routing)
# ------------------------------------------------------------------------------
def disservizio(data: dict, r: str, X: float) -> float:
    xs = np.array([data["x_star"][(r, t)] for t in data["user_types"]])
    return float(data["alpha"] * np.maximum(0.0, xs - X).sum() + data["beta"] * np.maximum(0.0, X - xs).sum())


def griglia_potata(data: dict) -> dict[str, list[float]]:
    out = {}
    for r in data["waste_types"]:
        F = [disservizio(data, r, X) for X in X_VALUES]
        i_min = int(np.argmin(F))                             # a parita' il primo (X piu' bassa)
        out[r] = X_VALUES[: i_min + 1]
    return out


# ------------------------------------------------------------------------------
# Valutazione in un unico pool: i dati passano una volta per worker (initializer)
# ------------------------------------------------------------------------------
_DATI: dict | None = None


def _init(dati: dict) -> None:
    global _DATI
    _DATI = dati


def _valuta(task: tuple[str, str, float]) -> tuple[str, float, dict | None]:
    algo, r, X = task
    res = ALGO[algo]._evaluate_one((_DATI, r, X, 0.5, 1.0))  # come batch_seed: gamma=0.5, k=1 (rotte indipendenti da gamma)
    if res is None:
        return r, X, None
    riga = {k: float(res[k]) for k in CAMPI}
    riga["n_utenti_serviti"] = sum(1 for route in res["routes"]["routes"] for u in route if u != 0)
    return r, X, riga


def esegui(dati: dict, algo: str, griglia: dict[str, list[float]], n_workers: int) -> tuple[list, float, float]:
    tasks = [(algo, r, X) for r, xs in griglia.items() for X in xs]
    ru0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=n_workers, initializer=_init, initargs=(dati,)) as ex:
        out = list(ex.map(_valuta, tasks, chunksize=1))
    wall = time.perf_counter() - t0
    ru1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = (ru1.ru_utime - ru0.ru_utime) + (ru1.ru_stime - ru0.ru_stime)
    return out, wall, cpu


# ------------------------------------------------------------------------------
# Stima dei tempi dai CSV esistenti (algo_time_sec = griglia completa dei due algoritmi)
# ------------------------------------------------------------------------------
def tempo_csv(path: Path) -> float | None:
    if not path.exists():
        return None
    d = pd.read_csv(path, usecols=["algoritmo", "algo_time_sec"])
    return float(d.groupby("algoritmo").algo_time_sec.first().sum())


def lista_istanze(seeds: list[int]) -> list[tuple]:
    out = []
    for bench, N, sc, mo, n_seed in PIANO:
        for s in ([0] if bench == "B4" else seeds[:n_seed]):
            out.append((bench, N, sc, mo, s))
    return out


def gia_fatte() -> set[tuple]:
    f = OUT / "tempi.csv"
    if not f.exists():
        return set()
    t = pd.read_csv(f)
    return set(map(tuple, t[KI].drop_duplicates().astype({"N": int, "seed": int}).values.tolist()))


def scrivi(path: Path, righe: list[dict]) -> None:
    nuovo = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(righe[0]))
        if nuovo:
            w.writeheader()
        w.writerows(righe)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stima", action="store_true", help="stampa solo la stima dei tempi")
    ap.add_argument("--solo-potata", action="store_true", help="non riesegue la griglia completa")
    ap.add_argument("--max-minuti", type=float, default=60.0, help="non avvia nuove istanze oltre questo tempo")
    ap.add_argument("--seeds", default="", help="seed espliciti, es. 42,7 (default: i primi di seeds/seeds.json)")
    a = ap.parse_args()

    seeds = ([int(s) for s in a.seeds.split(",")] if a.seeds
             else json.loads((ROOT / "seeds" / "seeds.json").read_text()))
    istanze = [i for i in lista_istanze(seeds) if csv_riferimento(*i).exists()]
    fatte = gia_fatte()
    da_fare = [i for i in istanze if (i[0], i[1], i[2], i[3], i[4]) not in fatte]

    # stima: completa ~ tempo dei CSV; potata ~ quota di X valutate (circa 40%)
    fattore = 0.45 if a.solo_potata else 1.45
    stime = [(tempo_csv(csv_riferimento(*i)) or 0.0) * fattore for i in da_fare]
    extra_mappa = 75.0 if any(i[0] in ("B4", "B4sub") for i in da_fare) else 0.0
    print(f"istanze nel piano con CSV di riferimento: {len(istanze)} | gia' fatte: {len(istanze) - len(da_fare)} "
          f"| da fare: {len(da_fare)}")
    print(f"stima: {(sum(stime) + extra_mappa) / 60:.0f} minuti (dai tempi registrati nei CSV, "
          f"{'solo potata' if a.solo_potata else 'completa + potata'})")
    if a.stima or not da_fare:
        return

    OUT.mkdir(exist_ok=True)
    ist = Istanze()
    t_inizio = time.perf_counter()
    for n, (bench, N, sc, mo, seed) in enumerate(da_fare, 1):
        trascorsi = (time.perf_counter() - t_inizio) / 60
        if trascorsi > a.max_minuti:
            print(f"limite di {a.max_minuti:.0f} minuti raggiunto: mi fermo (rilancia per continuare)")
            break
        print(f"[{n}/{len(da_fare)}] {bench} N={N} {sc} seed {seed}  ({trascorsi:.1f} min)", flush=True)
        dati = ist.dati(bench, N, sc, mo, seed)
        nw = calcola_worker_ottimali(dati["n_users"])
        potata = griglia_potata(dati)
        completa = {r: list(X_VALUES) for r in dati["waste_types"]}
        chiave = dict(bench=bench, N=N, scenario=sc, modo=mo, seed=seed)

        righe, tempi = [], []
        ricerche = [("potata", potata)] if a.solo_potata else [("completa", completa), ("potata", potata)]
        for algo in ALGO:
            for nome, griglia in ricerche:
                out, wall, cpu = esegui(dati, algo, griglia, nw)
                tempi.append({**chiave, "algoritmo": algo, "ricerca": nome, "n_valutazioni": len(out),
                              "wall_s": round(wall, 4), "cpu_s": round(cpu, 4), "n_workers": nw})
                for r, X, riga in out:
                    if riga is not None:
                        righe.append({**chiave, "algoritmo": algo, "ricerca": nome, "rifiuto": r, "X_r": X, **riga})
                print(f"    {algo:13s} {nome:8s} {len(out):2d} valutazioni  {wall:7.1f} s", flush=True)
        scrivi(OUT / "potatura.csv", [{**chiave, "rifiuto": r, "X_min": xs[-1], "n_X": len(xs)}
                                      for r, xs in potata.items()])
        scrivi(OUT / "righe.csv", righe)
        scrivi(OUT / "tempi.csv", tempi)                     # per ultimo: segna l'istanza come completata
    print(f"fatto in {(time.perf_counter() - t_inizio) / 60:.1f} minuti -> {OUT}")


if __name__ == "__main__":
    main()