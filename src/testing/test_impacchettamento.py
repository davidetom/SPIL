import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

C = {"organico":1500, "carta":1500, "plastica":1000, "vetro":2000, "indifferenziata":2000}
R = pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("*.csv")], ignore_index=True)
R = R[R.X_r == 0.5].copy()
R["cap"] = R.rifiuto.map(C)
R["carico"] = R.sat_fisica / 100 * R.n_vehicles * R.cap
R["V_lb"] = np.ceil(R.carico / R.cap - 1e-6)
R["eccesso"] = R.n_vehicles - R.V_lb
chk = R.pivot_table(index=["bench","N","scenario","modo","seed","rifiuto"],
                    columns="algoritmo", values="carico")
print("max |carico G - carico CW| (kg):", (chk.greedy - chk.clarke_wright).abs().max())
e = (R.groupby(["bench","N","scenario","modo","seed","algoritmo"]).eccesso.sum().unstack("algoritmo"))
print(e.groupby(["bench","N","scenario","modo"]).mean().round(2).to_string())
