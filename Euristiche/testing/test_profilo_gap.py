# test_profilo_gap.py
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

R = pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("*.csv")], ignore_index=True)
R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
u = R[(R.bench == "B2") & (R.scenario == "residenziale")].copy()
u["bench"] = "B3"                                   # B3 uniform = B2 residenziale
R = pd.concat([R, u], ignore_index=True)
R = R[R.bench == "B3"]
key = ["modo", "seed", "rifiuto", "X_r"]
p = R.pivot_table(index=key, columns="algoritmo",
                  values=["F_costi", "n_vehicles", "sat_fisica", "sat_tempo"])
g = pd.DataFrame({
    "gap": (p["F_costi"]["greedy"] - p["F_costi"]["clarke_wright"]) / p["F_costi"]["clarke_wright"] * 100,
    "dV": p["n_vehicles"]["greedy"] - p["n_vehicles"]["clarke_wright"],
    "satf_G": p["sat_fisica"]["greedy"],
    "satt_G": p["sat_tempo"]["greedy"]}).reset_index()
t = g.groupby(["modo", "X_r"])[["gap", "dV", "satf_G", "satt_G"]].mean().round(2)
print(t.unstack("modo").to_string())
