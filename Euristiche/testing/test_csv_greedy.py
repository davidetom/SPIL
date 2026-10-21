import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

old, new = ROOT / "risultati_csv_old", ROOT / "risultati_csv"
key = ["rifiuto","X_r"]
num = ["n_vehicles","F_total","F_insoddis","F_costo_fisso","F_viaggio",
       "F_lavoro","sat_fisica","sat_tempo","k_scala"]
rep = []
for f in sorted(new.glob("*_gamma*.csv")):
    a = pd.read_csv(old/f.name); b = pd.read_csv(f)
    a = a[a.algoritmo=="greedy"].set_index(key).sort_index()
    b = b[b.algoritmo=="greedy"].set_index(key).sort_index()
    com = a.index.intersection(b.index)
    row = {"file": f.name.replace("risultati_","")[:42],
           "old": len(a), "new": len(b), "comuni": len(com)}
    for c in num:
        row[c] = (a.loc[com, c] - b.loc[com, c]).abs().max()
    rep.append(row)
pd.set_option("display.width", 250)
print(pd.DataFrame(rep).round(4).to_string(index=False))
