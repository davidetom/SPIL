import pandas as pd, re
from pathlib import Path

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

CD, CM = 0.35, 0.25

dfs = []
for f in (ROOT / "risultati_csv").glob("*_gamma*.csv"):
    d = pd.read_csv(f)
    d["gamma"] = float(re.search(r"gamma(\d+\.\d+)", f.name).group(1))
    d["bench"] = f.name.split("_gamma")[0]
    dfs.append(d)
D = pd.concat(dfs, ignore_index=True)

D["F_costi"]   = D.F_costo_fisso + D.F_viaggio + D.F_lavoro
D["V_x_X"]     = D.n_vehicles * D.X_r            # attivazioni settimanali
D["km_sett"]   = D.F_viaggio / CD
D["km_giro"]   = D.km_sett / D.X_r
D["min_sett"]  = D.F_lavoro / CM
D["min_giro"]  = D.min_sett / D.X_r

# TEST 0a: a X_r fissato le rotte sono invarianti rispetto a gamma?
key = ["bench", "algoritmo", "rifiuto", "X_r"]
spread = D.groupby(key)[["n_vehicles","F_viaggio","F_lavoro","F_costo_fisso"]].agg(lambda s: s.max()-s.min())
print("righe con differenza tra gamma:", (spread.abs() > 1e-3).any(axis=1).sum(), "su", len(spread))

# --- 0a-bis: quanto e dove differiscono le rotte tra gamma ---
sp = (D.groupby(key)
        .agg(dV=("n_vehicles", lambda s: s.max()-s.min()),
             rel_costi=("F_costi", lambda s: (s.max()-s.min())/s.max()))
        .reset_index())
sp["diff"] = (sp.dV > 0) | (sp.rel_costi > 1e-6)
print(sp.groupby("algoritmo")["diff"].agg(["sum","count"]))
print(sp.groupby("bench")["diff"].agg(["sum","count"]))
print(sp[sp["diff"]].groupby("algoritmo")[["dV","rel_costi"]].describe().T.round(5))

# --- tabella fisica Fabriano ---
BENCH = "risultati_3932u_mappa_reale"
cols = ["X_r","n_vehicles","V_x_X","km_sett","min_sett","F_costo_fisso",
        "F_insoddis","sat_fisica","sat_tempo"]
best = (D[D.is_best == 1]
        .set_index(["bench","algoritmo","gamma","rifiuto"])[cols].sort_index())
print(best.loc[BENCH].round(2).to_string())

# --- 0c: gap logistico a X fissato, per ciascun gamma ---
p = (D[D.bench == BENCH]
     .pivot_table(index=["gamma","rifiuto","X_r"], columns="algoritmo",
                  values=["F_costi","n_vehicles"]))
gap = pd.DataFrame({
    "gap_costi_%": (p["F_costi"]["greedy"] - p["F_costi"]["clarke_wright"])
                   / p["F_costi"]["clarke_wright"] * 100,
    "dV": p["n_vehicles"]["greedy"] - p["n_vehicles"]["clarke_wright"]})
print(gap.round(2).to_string())
