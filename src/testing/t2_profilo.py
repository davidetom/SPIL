# t2_profilo.py
# Profilo in X_r a frequenza fissata (T2) sulle stesse istanze di T1 + Fabriano completa.
#   P1  soglia tra regime a capacita' e regime a tempo: osservata vs prevista X_pred = W_tot/(C*V_tempo)
#   P2  unimodalita' di F_tot(X_r) sulla griglia e costo di una ricerca "a discesa" da X_r=0.5
#   P3  sensibilita' attorno all'ottimo: X* -/+ 0.5 (costo, disservizio, F_tot)
#   P4  confronto algoritmi lungo X_r: vantaggio logistico di CW e differenza di camion per giro
# Input : risultati_seed/*.csv, risultati_csv/risultati_3932u_mappa_reale_gamma0.50.csv,
#         analisi_seed/metriche_istanza.csv (solo per l'elenco delle istanze)
# Output: analisi_seed/t2_P1.csv ... t2_P4.csv + tabelle a video
# Uso   : python t2_profilo.py   |   python t2_profilo.py P1 P3
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent            # cartella Euristiche/
OUT, RAW = ROOT / "analisi_seed", ROOT / "risultati_seed"
OUT.mkdir(exist_ok=True)
B4_CSV = ROOT / "risultati_csv" / "risultati_3932u_mappa_reale_gamma0.50.csv"
KS = ["bench", "N", "scenario", "modo"]
KI = KS + ["seed"]
KC = KI + ["algoritmo", "rifiuto"]               # un profilo in X_r
CAP = {"organico": 1500.0, "carta": 1500.0, "plastica": 1000.0, "vetro": 2000.0, "indifferenziata": 2000.0}
GAMMAS = np.round(np.arange(0.05, 0.951, 0.05), 2)
EVID = (0.1, 0.5, 0.9)
pd.set_option("display.width", 220, "display.max_columns", 40)


def mmm(s: pd.Series, f: str = "{:.2f}") -> str:
    s = s.dropna()
    return f"{f.format(s.median())} [{f.format(s.min())}; {f.format(s.max())}]" if len(s) else "--"


def carica() -> pd.DataFrame:
    ist = pd.read_csv(OUT / "metriche_istanza.csv")[KS].drop_duplicates()
    R = pd.concat([pd.read_csv(f) for f in sorted(RAW.glob("*.csv"))], ignore_index=True)
    R = R.merge(ist, on=KS)                                  # esclude B1L, B1SL e le N extra di B4sub
    R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
    if B4_CSV.exists():
        d = pd.read_csv(B4_CSV)
        d["F_costi"] = d.F_costo_fisso + d.F_viaggio + d.F_lavoro
        d["k_scala"] = ((d.F_total - 0.5 * d.F_costi) / (0.5 * d.F_insoddis)).median()   # come analisi_gamma
        d["bench"], d["N"], d["scenario"], d["modo"], d["seed"] = "B4", 3932, "reale", "reale", 0
        R = pd.concat([R, d[R.columns.intersection(d.columns)]], ignore_index=True)
    R = R.sort_values(KC + ["X_r"]).reset_index(drop=True)
    print(f"istanze: {R.groupby(KS).ngroups} | profili (istanza, seed, algoritmo, rifiuto): {R.groupby(KC).ngroups}")
    return R


# ---------------------------------------------------------------------------------
# P1: soglia di regime. V_tempo = camion per giro a X=6 (regime a tempo).
#     Carico settimanale W = X * sat_f/100 * V * C  ->  X_pred = W/(C*V_tempo) = 6 * sat_f(6)/100
#     X_obs = minima X da cui V resta uguale a V_tempo
# ---------------------------------------------------------------------------------
def p1(R: pd.DataFrame) -> None:
    righe = []
    for k, g in R.groupby(KC, sort=False):
        X, V = g.X_r.values, g.n_vehicles.values
        Vt = V[-1]
        diverso = np.flatnonzero(V != Vt)
        x_obs = X[diverso[-1] + 1] if diverso.size else X[0]
        x_pred = X[-1] * g.sat_fisica.values[-1] / 100
        x_pred_griglia = max(0.5, np.ceil(x_pred / 0.5 - 1e-9) * 0.5)
        righe.append(dict(zip(KC, k), V_tempo=Vt, X_obs=x_obs, X_pred=x_pred, X_pred_griglia=x_pred_griglia,
                          sat_f_a_Xobs=g.sat_fisica.values[X == x_obs][0]))
    P = pd.DataFrame(righe)
    P["uguale"] = np.isclose(P.X_obs, P.X_pred_griglia)
    P["oltre"] = P.X_obs > P.X_pred_griglia + 1e-9
    P.to_csv(OUT / "t2_P1.csv", index=False)
    print("\n=== P1: soglia tra regime a capacita' e a tempo (per rifiuto e algoritmo, su tutti i profili) ===")
    t = P.groupby(["rifiuto", "algoritmo"]).agg(
        X_obs=("X_obs", lambda s: mmm(s, "{:.1f}")), X_pred=("X_pred", lambda s: mmm(s, "{:.2f}")),
        uguale_pct=("uguale", lambda s: round(100 * s.mean(), 1)),
        oltre_pct=("oltre", lambda s: round(100 * s.mean(), 1)),
        sat_f_soglia=("sat_f_a_Xobs", lambda s: mmm(s, "{:.0f}")))
    print(t.to_string())
    print(f"\nX_obs = griglia(X_pred): {100 * P.uguale.mean():.1f}% | X_obs oltre: {100 * P.oltre.mean():.1f}% | "
          f"X_obs prima: {100 * (~P.uguale & ~P.oltre).mean():.1f}%")


# ---------------------------------------------------------------------------------
# P2: F_tot(X) unimodale sulla griglia? Ricerca a discesa: valuta X=0.5,1.0,... e si ferma
#     al primo aumento -> valutazioni = indice del minimo + 2 (al massimo 12).
# ---------------------------------------------------------------------------------
def p2(R: pd.DataFrame) -> None:
    righe = []
    for k, g in R.groupby(KC, sort=False):
        F, C, kk = g.F_insoddis.values, g.F_costi.values, g.k_scala.iloc[0]
        n = len(F)
        ft = GAMMAS[:, None] * kk * F[None, :] + (1 - GAMMAS[:, None]) * C[None, :]
        for gm, f in zip(GAMMAS, ft):
            i = int(f.argmin())
            d = np.diff(f)
            # discesa: primo indice in cui F_tot aumenta
            sal = np.flatnonzero(d > 1e-9)
            stop = sal[0] if sal.size else n - 1
            righe.append(dict(zip(KC, k), gamma=gm, i_min=i, unimodale=bool(np.all(d[:i] <= 1e-9) and np.all(d[i:] >= -1e-9)),
                              discesa_ok=(stop == i), valutazioni=min(stop + 2, n), n=n))
    P = pd.DataFrame(righe)
    P.to_csv(OUT / "t2_P2.csv", index=False)
    print("\n=== P2: unimodalita' di F_tot(X_r) e ricerca a discesa ===")
    t = P.groupby("gamma").agg(unimodale=("unimodale", "mean"), discesa_ok=("discesa_ok", "mean"),
                               valutazioni=("valutazioni", "mean"))
    t[["unimodale", "discesa_ok"]] *= 100
    print(t.loc[list(EVID)].round(2).to_string())
    print(f"tutti i gamma: unimodale {100 * P.unimodale.mean():.2f}% | discesa trova il minimo {100 * P.discesa_ok.mean():.2f}% "
          f"| valutazioni medie {P.valutazioni.mean():.2f} su {P.n.iloc[0]}")
    # per coprire tutti i 19 gamma basta arrivare al minimo di gamma=0.95 + 1
    cop = P.groupby(KC).apply(lambda g: min(g.i_min.max() + 2, g.n.iloc[0])).rename("valutazioni_tutti_gamma")
    print(f"per coprire i 19 gamma: {cop.mean():.2f} valutazioni medie su 12 "
          f"({100 * (1 - cop.mean() / 12):.1f}% di esecuzioni di routing risparmiate)")
    print("valutazioni per rifiuto (tutti i gamma):")
    print(cop.groupby("rifiuto").mean().round(2).to_string())


# ---------------------------------------------------------------------------------
# P3: sensibilita' attorno all'ottimo, X* -/+ 0.5, a gamma = 0.1, 0.5, 0.9
#     variazioni % di costo, disservizio e F_tot rispetto a X*; media sui seed, poi sulle istanze
# ---------------------------------------------------------------------------------
def p3(R: pd.DataFrame) -> None:
    righe = []
    for k, g in R.groupby(KC, sort=False):
        X, F, C, kk = g.X_r.values, g.F_insoddis.values, g.F_costi.values, g.k_scala.iloc[0]
        for gm in EVID:
            ft = gm * kk * F + (1 - gm) * C
            i = int(ft.argmin())
            for lato, j in (("-0.5", i - 1), ("+0.5", i + 1)):
                if 0 <= j < len(X):
                    righe.append(dict(zip(KC, k), gamma=gm, lato=lato, X_star=X[i],
                                      dC=100 * (C[j] / C[i] - 1), dF=100 * (F[j] / F[i] - 1) if F[i] > 0 else np.nan,
                                      dFtot=100 * (ft[j] / ft[i] - 1)))
    P = pd.DataFrame(righe)
    P.to_csv(OUT / "t2_P3.csv", index=False)
    A = P.groupby(KS + ["algoritmo", "rifiuto", "gamma", "lato"])[["dC", "dF", "dFtot"]].mean().reset_index()
    print("\n=== P3: spostarsi di mezzo ritiro dall'ottimo (CW; variazioni %, mediana [min; max] sulle istanze) ===")
    s = A[A.algoritmo == "clarke_wright"].groupby(["gamma", "lato", "rifiuto"]).agg(
        n=("dC", "size"), dCosto=("dC", mmm), dDisservizio=("dF", mmm), dFtot=("dFtot", mmm))
    print(s.to_string())


# ---------------------------------------------------------------------------------
# P4: CW vs Greedy lungo X_r (somma sui rifiuti): vantaggio logistico e camion per giro
# ---------------------------------------------------------------------------------
def p4(R: pd.DataFrame) -> None:
    t = R.groupby(KI + ["X_r", "algoritmo"])[["F_costi", "n_vehicles"]].sum().unstack("algoritmo")
    d = pd.DataFrame({"L_g": 100 * (t["F_costi"]["greedy"] / t["F_costi"]["clarke_wright"] - 1),
                      "dV_pct": 100 * (t["n_vehicles"]["clarke_wright"] / t["n_vehicles"]["greedy"] - 1)}).reset_index()
    A = d.groupby(KS + ["X_r"])[["L_g", "dV_pct"]].mean().reset_index()
    A.to_csv(OUT / "t2_P4.csv", index=False)
    print("\n=== P4: CW vs Greedy a pari X_r (somma sui rifiuti; media sui seed, mediana [min; max] sulle istanze) ===")
    print("L_g = costo Greedy / costo CW - 1 (%); dV = camion per giro CW / Greedy - 1 (%)")
    print(A.groupby("X_r").agg(L_g=("L_g", mmm), dV=("dV_pct", mmm)).to_string())


def main() -> None:
    scelte = [a.upper() for a in sys.argv[1:]] or ["P1", "P2", "P3", "P4"]
    R = carica()
    for nome, f in (("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4)):
        if nome in scelte:
            f(R)


if __name__ == "__main__":
    main()