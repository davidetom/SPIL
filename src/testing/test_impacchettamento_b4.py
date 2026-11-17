# test_impacchettamento_b4.py
# A X_r=0.5 (regime a capacita') confronta, per B4sub N=2000..3500, i camion usati da Greedy e CW
# con il limite inferiore di capacita' ceil(carico/capacita'), sommato sui rifiuti.
import pandas as pd, numpy as np
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

C = {"organico": 1500, "carta": 1500, "plastica": 1000, "vetro": 2000, "indifferenziata": 2000}
R = pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("B4sub_*.csv")], ignore_index=True)
R = R[(R.X_r == 0.5) & R.N.isin([2000, 2500, 3000, 3500])].copy()
R["cap"] = R.rifiuto.map(C)
R["carico"] = R.sat_fisica / 100 * R.n_vehicles * R.cap
R["V_lb"] = np.ceil(R.carico / R.cap - 1e-6)
R["eccesso"] = R.n_vehicles - R.V_lb

k = ["N", "seed"]
t = R.groupby(k + ["algoritmo"]).agg(V=("n_vehicles", "sum"), lb=("V_lb", "sum"), ecc=("eccesso", "sum"))
t = t.unstack("algoritmo")
out = pd.DataFrame({
    "V_G": t[("V", "greedy")], "V_CW": t[("V", "clarke_wright")],
    "LB_G": t[("lb", "greedy")], "LB_CW": t[("lb", "clarke_wright")],
    "ecc_G": t[("ecc", "greedy")], "ecc_CW": t[("ecc", "clarke_wright")]})
out["dV"] = out.V_G - out.V_CW
print(out.groupby("N").mean().round(2).to_string())
print("\nquota di seed con CW che usa piu' camion di Greedy (dV<0):")
print((out.dV < 0).groupby("N").mean().round(2).to_string())
print("\nmedia e deviazione standard di dV per N:")
print(out.groupby("N").dV.agg(["mean", "std"]).round(2).to_string())