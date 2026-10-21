import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

old, new = ROOT / "risultati_csv_old", ROOT / "risultati_csv"
cols = ["rifiuto","X_r","n_vehicles","F_total","F_insoddis","F_costo_fisso",
        "F_viaggio","F_lavoro","sat_fisica","sat_tempo"]
bad = 0
for f in sorted(new.glob("*_gamma*.csv")):
    a = pd.read_csv(old/f.name); b = pd.read_csv(f)
    a = a[a.algoritmo=="greedy"].sort_values(["rifiuto","X_r"])[cols].reset_index(drop=True)
    b = b[b.algoritmo=="greedy"].sort_values(["rifiuto","X_r"])[cols].reset_index(drop=True)
    ok = a.shape == b.shape and (a.drop(columns="rifiuto") - b.drop(columns="rifiuto")).abs().max().max() < 1e-3
    if not ok:
        bad += 1; print("DIVERSO:", f.name)
print("file Greedy diversi:", bad)
