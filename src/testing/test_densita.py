# test_densita.py
import json, numpy as np, pandas as pd
from pathlib import Path
from scipy.spatial import ConvexHull

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

CD = 0.35
def km_giro(df):
    d = df[df.X_r == 4.0].copy()
    d["km_giro"] = d.F_viaggio / (CD * d.X_r)
    return d

B1 = km_giro(pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("B1_*.csv")]))
t = B1.groupby(["N","algoritmo","seed"]).km_giro.mean().reset_index()
t["r"] = t.km_giro / np.sqrt(t.N * 100.0)            # area 10x10 = 100 km^2
print(t.groupby(["N","algoritmo"]).agg(km_giro=("km_giro","mean"),
      r_mean=("r","mean"), r_std=("r","std")).round(3).to_string())

F = km_giro(pd.read_csv(ROOT / "risultati_csv/risultati_3932u_mappa_reale_gamma0.50.csv"))
u = json.load(open(ROOT / "Generazione_grafo_Fabriano/dati_reali/utenti.json"))["utenti"]
xy = np.array([[d["x_utm"], d["y_utm"]] for d in u]) / 1000.0
A = ConvexHull(xy).volume
N = len(xy)
print(f"\nFabriano: N={N}, area hull={A:.1f} km2, densita={N/A:.0f} utenti/km2")
for algo, g in F.groupby("algoritmo"):
    km = g.groupby("rifiuto").km_giro.mean().mean()
    print(f"  {algo:14s} km/giro={km:.1f}   r={km/np.sqrt(N*A):.3f}")
