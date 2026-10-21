# test_densita_sub.py
import json, numpy as np, pandas as pd
from pathlib import Path
from scipy.spatial import ConvexHull

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

CD = 0.35
u = json.load(open(ROOT / "Generazione_grafo_Fabriano/dati_reali/utenti.json"))["utenti"]
A = ConvexHull(np.array([[d["x_utm"], d["y_utm"]] for d in u]) / 1000.0).volume

def r_tab(files, area):
    R = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    R = R[R.X_r == 4.0].copy()
    R["km_giro"] = R.F_viaggio / (CD * R.X_r)
    t = R.groupby(["N", "algoritmo", "seed"]).km_giro.mean().reset_index()
    t["r"] = t.km_giro / np.sqrt(t.N * area)
    return t

sub = r_tab((ROOT / "risultati_seed").glob("B4sub_*.csv"), A)
syn = r_tab((ROOT / "risultati_seed").glob("B1_*.csv"), 100.0)
for nome, t in (("Fabriano campionato (A=%.1f km2)" % A, sub), ("sintetico (A=100 km2)", syn)):
    p = t.groupby(["N", "algoritmo"]).r.agg(["mean", "std"]).round(3)
    print("\n", nome, "\n", p.to_string())
    q = t.groupby(["N", "algoritmo"]).r.mean().unstack()
    print("rapporto Greedy/CW:", (q.greedy / q.clarke_wright).round(2).to_dict())
