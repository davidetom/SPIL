import pandas as pd
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

pd.set_option("display.width", 260)
m = pd.read_csv(ROOT / "analisi_seed/riepilogo_metriche.csv")
m = m[m.gamma.isin([0.1, 0.5, 0.9])]
c = ["bench","N","scenario","modo","gamma","algoritmo","V_mean","VxX_mean","km_mean","ore_mean",
     "F_ins_mean","F_costi_mean","sat_f_mean","sat_t_mean","quota_viaggio_mean"] \
    + [x for x in m.columns if x.startswith("X_") and x.endswith("_mean")]
print(m[c].round(1).to_string(index=False))
print(pd.read_csv(ROOT / "analisi_seed/riepilogo_plateau.csv").round(2).to_string(index=False))
