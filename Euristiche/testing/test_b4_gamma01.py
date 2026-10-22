# test_b4_gamma01.py  (eseguire dopo: python analisi_gamma.py --estese --con-b4)
# Obiettivo: capire perche' a gamma=0.1 il gap di B4sub a N=3500 (3.31) e' sotto B4 (3.88) mentre N=3000 (3.89) coincide.
import pandas as pd

D = "analisi_seed_estese/"
M = pd.read_csv(D + "metriche_istanza.csv")
M = M[(M.gamma.round(2) == 0.1) & ((M.bench == "B4") | ((M.bench == "B4sub") & M.N.isin([2000, 2500, 3000, 3500])))]
xc = [c for c in M.columns if c.startswith("X_")]

print("1) X* (media sui seed), camion per giro V e km, a gamma=0.1")
print(M.groupby(["bench", "N", "algoritmo"])[xc + ["V", "km"]].mean().round(2).to_string())

M = M.assign(vec=M[xc].round(2).astype(str).agg("-".join, axis=1))
print("\n2) vettori di X* distinti tra i seed e quota del piu' frequente")
print(M.groupby(["bench", "N", "algoritmo"]).vec.agg(
    distinti="nunique", quota_modale=lambda s: round(s.value_counts(normalize=True).iloc[0], 2)).to_string())

P = pd.read_csv(D + "riepilogo_plateau.csv")
P = P[(P.bench == "B4") | ((P.bench == "B4sub") & P.N.isin([2000, 2500, 3000, 3500]))]
print("\n3) gap logistico a X fissato (non dipende da gamma): X_r=0.5 e plateau (X_r>=3)")
print(P[["bench", "N", "gap_X05_mean", "dV_X05_mean", "gap_plateau_mean", "dV_plateau_mean"]].round(2).to_string(index=False))