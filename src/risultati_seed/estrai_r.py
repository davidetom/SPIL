# estrai_r.py
# Chilometri per giro normalizzati r = km/giro / sqrt(N*A) nel regime a tempo (X_r = 4, media sui rifiuti),
# per B1 (rete 1000 nodi), B1L/B1SL (rete 4000 nodi), B4sub (sottocampioni reali), B4 (tutti gli utenti).
# Stampa anche il gap di B4sub a N=750 (da analisi_seed_estese/riepilogo_gap.csv).
# Output: analisi_seed_estese/r_per_N.csv
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent            # cartella Euristiche/
RAW = ROOT / "risultati_seed"
B4_CSV = ROOT / "risultati_csv" / "risultati_3932u_mappa_reale_gamma0.50.csv"
OUT = ROOT / "analisi_seed_estese"
CD, X4 = 0.35, 4.0
A_FAB = 16.47
AREA = {"B1": 100.0, "B1L": 100.0, "B1SL": 0.4058 ** 2 * 100, "B4sub": A_FAB, "B4": A_FAB}
pd.set_option("display.width", 200)


def km_giro_x4(R: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    d = R[np.isclose(R.X_r, X4)].copy()
    d["km_giro"] = d.F_viaggio / (CD * X4)
    return d.groupby(keys).km_giro.mean().reset_index()      # media sui rifiuti


def main() -> None:
    files = [f for f in sorted(RAW.glob("*.csv")) if f.name.split("_")[0] in AREA]
    R = pd.concat([pd.read_csv(f, usecols=["bench", "seed", "N", "rifiuto", "X_r", "algoritmo", "F_viaggio"])
                   for f in files], ignore_index=True)
    per = km_giro_x4(R, ["bench", "N", "seed", "algoritmo"])
    if B4_CSV.exists():
        b4 = pd.read_csv(B4_CSV).assign(bench="B4", N=3932, seed=0)
        per = pd.concat([per, km_giro_x4(b4, ["bench", "N", "seed", "algoritmo"])], ignore_index=True)
    per["r"] = per.km_giro / np.sqrt(per.N * per.bench.map(AREA))
    t = per.pivot_table(index=["bench", "N", "seed"], columns="algoritmo", values=["r", "km_giro"])
    t = pd.DataFrame({"r_CW": t["r"]["clarke_wright"], "r_G": t["r"]["greedy"],
                      "G_su_CW": t["r"]["greedy"] / t["r"]["clarke_wright"],
                      "km_CW": t["km_giro"]["clarke_wright"], "km_G": t["km_giro"]["greedy"]}).reset_index()
    s = t.groupby(["bench", "N"]).agg(n_seed=("seed", "size"), r_CW=("r_CW", "mean"), r_G=("r_G", "mean"),
                                      G_su_CW=("G_su_CW", "mean"), km_CW=("km_CW", "mean"),
                                      km_G=("km_G", "mean")).reset_index()

    # legge di potenza r_CW = a N^b: sul B1 (N <= 1000, come nel testo) e su B1L (tutte le N)
    leggi = {}
    for b in ("B1", "B1L", "B1SL"):
        d = s[s.bench == b]
        if len(d) >= 3:
            bb, la = np.polyfit(np.log(d.N), np.log(d.r_CW), 1)
            leggi[b] = (np.exp(la), bb)
            res = 100 * (d.r_CW / (np.exp(la) * d.N ** bb) - 1)
            print(f"legge {b}: r_CW = {np.exp(la):.3f} N^{bb:.4f}  (residui max {res.abs().max():.2f}%)")
    for b, (a, bb) in leggi.items():
        s[f"pred_{b}"] = a * s.N ** bb
    # scarto della rete reale rispetto ai sintetici a pari N (stessa normalizzazione)
    ref = s[s.bench.isin(["B4sub", "B4"])][["N", "r_CW", "r_G"]].rename(columns={"r_CW": "rCW_fab", "r_G": "rG_fab"})
    for b in ("B1", "B1L", "B1SL"):
        x = s[s.bench == b][["N", "r_CW", "r_G"]].merge(ref, on="N")
        if len(x):
            x["scarto_CW_%"] = 100 * (x.rCW_fab / x.r_CW - 1)
            x["scarto_G_%"] = 100 * (x.rG_fab / x.r_G - 1)
            print(f"\nFabriano rispetto a {b} a pari N (%):")
            print(x[["N", "scarto_CW_%", "scarto_G_%"]].round(1).to_string(index=False))
    OUT.mkdir(exist_ok=True)
    s.to_csv(OUT / "r_per_N.csv", index=False)
    print("\n", s.round(3).to_string(index=False))

    g = OUT / "riepilogo_gap.csv"
    if g.exists():
        G = pd.read_csv(g)
        c = ["bench", "N", "gamma", "gap_tot_mean", "gap_tot_ci95", "d_V_mean"]
        print("\nGAP B4sub, N=750 e N=1000:")
        print(G[(G.bench == "B4sub") & G.N.isin([750, 1000]) & G.gamma.round(2).isin([0.1, 0.5, 0.9])][c]
              .round(2).to_string(index=False))


if __name__ == "__main__":
    main()