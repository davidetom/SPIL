# test_due_fattori.py
import numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

R = pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("*.csv")], ignore_index=True)
R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
u = R[(R.bench == "B2") & (R.scenario == "residenziale")].copy()
u["bench"] = "B3"                                    # B3 uniform = B2 residenziale
R = pd.concat([R, u], ignore_index=True)
KI = ["bench", "N", "scenario", "modo", "seed"]


def xstar(d, g, k):
    d = d.sort_values("X_r")
    ft = g * k * d.F_insoddis.values + (1 - g) * d.F_costi.values
    i = int(np.argmin(ft))
    return d.X_r.values[i], ft[i]


out = []
for ki, gi in R.groupby(KI):
    k = gi.k_scala.iloc[0]
    for g in (0.1, 0.5, 0.9):
        CG = CCW = tC = 0.0
        try:
            for r, gr in gi.groupby("rifiuto"):
                dG = gr[gr.algoritmo == "greedy"]
                dC = gr[gr.algoritmo == "clarke_wright"]
                xg, _ = xstar(dG, g, k)
                _, ftc = xstar(dC, g, k)
                CG += dG.loc[dG.X_r == xg, "F_costi"].iloc[0]
                CCW += dC.loc[dC.X_r == xg, "F_costi"].iloc[0]
                tC += ftc
        except IndexError:
            continue
        out.append(dict(zip(KI, ki), gamma=g, Lg=(CG - CCW) / CCW * 100, w=(1 - g) * CCW / tC))
O = pd.DataFrame(out)
O["gap_da_routing"] = O.Lg * O.w
print(O.groupby(["bench", "N", "scenario", "modo", "gamma"])[["Lg", "w", "gap_da_routing"]]
        .mean().round(2).to_string())
