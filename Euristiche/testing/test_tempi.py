# test_tempi.py
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

R = pd.concat([pd.read_csv(f) for f in (ROOT / "risultati_seed").glob("*.csv")], ignore_index=True)
t = (R.groupby(["bench", "N", "scenario", "modo", "seed", "algoritmo"])
       .algo_time_sec.first().reset_index())
s = (t.groupby(["bench", "N", "scenario", "modo", "algoritmo"]).algo_time_sec
       .agg(["mean", "std"]).unstack("algoritmo"))
s[("rapporto", "CW/Greedy")] = s[("mean", "clarke_wright")] / s[("mean", "greedy")]
print(s.round(2).to_string())
