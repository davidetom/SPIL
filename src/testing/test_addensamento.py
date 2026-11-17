# test_addensamento.py
# Ipotesi: gli utenti reali di Fabriano non sono uniformi sull'inviluppo convesso; a N grande emergono
# gli addensamenti e l'area efficace scende, quindi r = km/sqrt(N*A) cala piu' in fretta che sul sintetico.
# Test: indice di Clark-Evans R = d_NN medio / (0.5/sqrt(N/A)), A = area dell'inviluppo del campione.
#   R ~ 1 uniforme, R < 1 addensato. Area efficace ~ A*R^2  ->  r atteso proporzionale a R.
# Confronto: R_reale/R_sintetico  contro  r_reale/r_sintetico (area e mix di Fabriano, rete 4000 nodi).
# Input : utenti reali (UTENTI_JSON di main.py), seeds/seeds.json, analisi_seed_estese/r_per_N.csv
# Output: analisi_seed_estese/test_addensamento.csv
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull, cKDTree
from scipy import stats

ROOT = Path(__file__).parent.parent            # cartella Euristiche/
sys.path.insert(0, str(ROOT))
OUT = ROOT / "analisi_seed_estese"
NS = [100, 250, 500, 750, 1000, 2000, 2500, 3000, 3500, 3932]
SCALA = 0.4058                                   # sintetico con area di Fabriano: quadrato di lato 10*SCALA km


def clark_evans(xy: np.ndarray) -> float:
    A = ConvexHull(xy).volume                    # in 2D .volume = area
    d = cKDTree(xy).query(xy, k=2)[0][:, 1]      # distanza dal vicino piu' prossimo
    return d.mean() / (0.5 / np.sqrt(len(xy) / A))


def ci95(x: np.ndarray) -> float:
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


def utenti_reali() -> np.ndarray:
    from main import UTENTI_JSON
    u = json.load(open(ROOT / UTENTI_JSON, encoding="utf-8"))["utenti"]
    return np.array([[x["x_utm"], x["y_utm"]] for x in u], dtype=float) / 1000.0   # km


def main() -> None:
    seeds = json.loads((ROOT / "seeds" / "seeds.json").read_text())[:30]   # stessi seed di batch_seed/batch_fabriano
    xy = utenti_reali()
    n = len(xy)
    print(f"utenti reali: {n} | area inviluppo: {ConvexHull(xy).volume:.2f} km2")
    righe = []
    for N in NS:
        Rr, Rs = [], []
        for s in (seeds if N < n else seeds[:1]):              # a N=n il campione e' unico
            rng = np.random.default_rng(s)
            idx = np.sort(rng.choice(n, size=N, replace=False)) if N < n else np.arange(n)
            Rr.append(clark_evans(xy[idx]))                    # stesso campionamento di batch_fabriano
            Rs.append(clark_evans(rng.uniform(0, 10 * SCALA, size=(N, 2))))
        Rr, Rs = np.array(Rr), np.array(Rs)
        righe.append(dict(N=N, R_reale=Rr.mean(), R_reale_ci95=ci95(Rr),
                          R_sint=Rs.mean(), R_sint_ci95=ci95(Rs), rapporto_R=Rr.mean() / Rs.mean()))
    T = pd.DataFrame(righe)

    f = OUT / "r_per_N.csv"
    if f.exists():
        r = pd.read_csv(f)
        fab = r[r.bench.isin(["B4sub", "B4"])].set_index("N")[["r_CW", "r_G"]]
        sin = r[r.bench == "B1SL"].set_index("N")[["r_CW", "r_G"]]
        T = T.join((fab / sin).add_prefix("rapporto_").rename(columns=lambda c: c.replace("_r_", "_r")), on="N")
        T["scarto_R_%"] = 100 * (T.rapporto_R - 1)
        T["scarto_rCW_%"] = 100 * (T.rapporto_rCW - 1)
        T["scarto_rG_%"] = 100 * (T.rapporto_rG - 1)
        ok = T.dropna(subset=["scarto_rCW_%"])
        print("\ncorrelazione tra scarto di R e scarto di r (CW, Greedy):",
              round(np.corrcoef(ok["scarto_R_%"], ok["scarto_rCW_%"])[0, 1], 3),
              round(np.corrcoef(ok["scarto_R_%"], ok["scarto_rG_%"])[0, 1], 3))
    OUT.mkdir(exist_ok=True)
    T.to_csv(OUT / "test_addensamento.csv", index=False)
    print(T.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
