# t1_generalita.py
# Verifica di generalita' dei risultati di B4 sulle istanze dei benchmark (T1).
# Input : analisi_seed/metriche_istanza.csv (E1, E2, E4), risultati_seed/*.csv (E3, E5),
#         ristretti alle stesse istanze (le serie estese B1L/B1SL e le N extra di B4sub sono escluse).
# Output: analisi_seed/t1_E1.csv ... t1_E5_*.csv + tabelle a video.
# Uso   : python t1_generalita.py            (tutte)   |   python t1_generalita.py E3 E5
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent            # cartella Euristiche/
OUT, RAW = ROOT / "analisi_seed", ROOT / "risultati_seed"
OUT.mkdir(exist_ok=True)
KS = ["bench", "N", "scenario", "modo"]        # istanza (si aggrega sui seed)
KI = KS + ["seed"]
X_COLS = ["X_organico", "X_indifferenziata", "X_plastica", "X_carta", "X_vetro"]
EVID = (0.1, 0.5, 0.9)
TOL = 1e-6
pd.set_option("display.width", 220, "display.max_columns", 50)


def istanze_indipendenti(df: pd.DataFrame) -> pd.DataFrame:
    """B3 'uniform' e' una copia di B2 'residenziale': si esclude per non contarla due volte."""
    return df[~((df.bench == "B3") & (df.modo == "uniform"))]


def carica_metriche() -> pd.DataFrame:
    return istanze_indipendenti(pd.read_csv(OUT / "metriche_istanza.csv"))


def carica_grezzi(M: pd.DataFrame) -> pd.DataFrame:
    """Griglie grezze ristrette alle stesse istanze di metriche_istanza.csv (esclude B1L, B1SL, N extra)."""
    files = sorted(RAW.glob("*.csv"))
    if not files:
        return pd.DataFrame()
    R = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    R = istanze_indipendenti(R).merge(M[KS].drop_duplicates(), on=KS)
    R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
    return R


def gamma_idx(d: pd.DataFrame) -> pd.DataFrame:
    return d.assign(gamma=d.gamma.round(2))


def mmm(s: pd.Series, f: str = "{:.2f}") -> str:
    return f"{f.format(s.median())} [{f.format(s.min())}-{f.format(s.max())}]"


# ---------------------------------------------------------------------------------
# E1: grandezze adimensionali, mediana [min-max] sulle istanze (media sui seed per istanza)
# ---------------------------------------------------------------------------------
def e1(M: pd.DataFrame) -> None:
    M = gamma_idx(M)
    dirette = X_COLS + ["sat_f", "sat_t", "quota_viaggio"]
    var = ["F_ins", "F_costi", "V", "km", "ore"]
    mi = M.groupby(KS + ["gamma", "algoritmo"])[dirette + var].mean().reset_index()
    ref = mi[mi.gamma == 0.1].set_index(KS + ["algoritmo"])[var]
    mi = mi.join(ref, on=KS + ["algoritmo"], rsuffix="_g01")
    for c in var:                                              # variazione % rispetto a gamma=0.1
        mi["d_" + c] = 100 * (mi[c] / mi[c + "_g01"] - 1)
    cols = dirette + ["d_" + c for c in var]
    mi = mi[mi.gamma.isin(EVID)]
    righe = []
    for (algo, g), d in mi.groupby(["algoritmo", "gamma"]):
        r = {"algoritmo": algo, "gamma": g, "n_istanze": len(d)}
        r.update({c: mmm(d[c], "{:.1f}" if c.startswith(("sat", "quota", "d_")) else "{:.2f}") for c in cols})
        righe.append(r)
    T = pd.DataFrame(righe)
    T.to_csv(OUT / "t1_E1.csv", index=False)
    print("\n=== E1: mediana [min-max] sulle istanze; d_* = variazione % rispetto a gamma=0.1 ===")
    print(T.set_index(["algoritmo", "gamma"]).T.to_string())


# ---------------------------------------------------------------------------------
# E2: soluzioni distinte sui 19 gamma e plateau piu' lungo
# ---------------------------------------------------------------------------------
def blocchi(s: pd.DataFrame) -> pd.DataFrame:
    chiave = s[["F_costi", "F_ins"]].round(3).astype(str).agg("|".join, axis=1)
    b = (chiave != chiave.shift()).cumsum()
    return s.groupby(b).agg(g0=("gamma", "min"), g1=("gamma", "max"), n=("gamma", "size"))


def e2(M: pd.DataFrame) -> None:
    M = gamma_idx(M).sort_values("gamma")
    righe = []
    for k, s in M.groupby(KI + ["algoritmo"]):
        b = blocchi(s)
        p = b.loc[b.n.idxmax()]
        righe.append(dict(zip(KI + ["algoritmo"], k), n_sol=len(b), plateau_n=p.n,
                          plateau_g0=p.g0, plateau_g1=p.g1))
    P = pd.DataFrame(righe)
    A = (P.groupby(KS + ["algoritmo"])[["n_sol", "plateau_n", "plateau_g0", "plateau_g1"]]
          .median().reset_index())
    A.to_csv(OUT / "t1_E2.csv", index=False)
    print("\n=== E2: mediana sui seed, poi mediana [min-max] sulle istanze ===")
    for algo, d in A.groupby("algoritmo"):
        print(f"{algo:14s} soluzioni distinte: {mmm(d.n_sol, '{:.0f}')} | gamma plateau piu' lungo: "
              f"da {mmm(d.plateau_g0)} a {mmm(d.plateau_g1)} ({mmm(d.plateau_n, '{:.0f}')} passi su 19)")
    print("\nsoluzioni distinte per istanza (mediana sui seed):")
    print(A.pivot_table(index=KS, columns="algoritmo", values="n_sol").to_string())


# ---------------------------------------------------------------------------------
# E3: dominanza a pari gamma (punti scelti) contro dominanza a pari X (stesse frequenze)
# ---------------------------------------------------------------------------------
def e3(M: pd.DataFrame, R: pd.DataFrame) -> None:
    M = gamma_idx(M)
    k = KI + ["gamma"]
    G = M[M.algoritmo == "greedy"].set_index(k)
    C = M[M.algoritmo == "clarke_wright"].set_index(k)
    d = pd.DataFrame({"dIns": G.F_ins - C.F_ins, "dCosti": G.F_costi - C.F_costi}).reset_index()
    cw_ok = (d.dIns >= -TOL) & (d.dCosti >= -TOL)
    cw_str = (d.dIns > TOL) | (d.dCosti > TOL)
    d["CW_domina"] = cw_ok & cw_str
    d["Greedy_domina"] = (d.dIns <= TOL) & (d.dCosti <= TOL) & ((d.dIns < -TOL) | (d.dCosti < -TOL))
    d["incomparabili"] = ~(d.CW_domina | d.Greedy_domina) & ((d.dIns.abs() > TOL) | (d.dCosti.abs() > TOL))
    d["CW_F_ins_minore"] = d.dIns > TOL
    d["CW_costo_minore"] = d.dCosti > TOL
    q = d.groupby("gamma")[["CW_domina", "Greedy_domina", "incomparabili",
                            "CW_F_ins_minore", "CW_costo_minore"]].mean().mul(100).round(1)
    q.to_csv(OUT / "t1_E3_pari_gamma.csv")
    print(f"\n=== E3a: % di coppie (istanza, seed) con i punti scelti a pari gamma (n={d.groupby('gamma').size().iloc[0]}) ===")
    print(q.to_string())

    # --- a pari X: servono i dati grezzi della griglia
    if R.empty:
        print("\nE3b saltato: nessun file in risultati_seed/")
        return
    print(f"\nistanze nei dati grezzi: {R.groupby(KS).ngroups} (B4 completa non e' in risultati_seed/)")
    p = R.pivot_table(index=KI + ["rifiuto", "X_r"], columns="algoritmo",
                      values=["F_insoddis", "F_costi", "n_vehicles"])
    ins_diversa = (p["F_insoddis"]["greedy"] - p["F_insoddis"]["clarke_wright"]).abs() > 1e-3
    print(f"\n=== E3b: a pari X (celle rifiuto x X: {len(p)}) ===")
    print(f"celle con F_insoddis diversa tra i due algoritmi (deve essere 0): {int(ins_diversa.sum())}")
    p = p.reset_index()
    c = pd.DataFrame({"X_r": p.X_r,
                      "CW_costo_minore": p["F_costi"]["clarke_wright"] < p["F_costi"]["greedy"] - TOL,
                      "CW_costo_maggiore": p["F_costi"]["clarke_wright"] > p["F_costi"]["greedy"] + TOL,
                      "CW_piu_camion": p["n_vehicles"]["clarke_wright"] > p["n_vehicles"]["greedy"],
                      "CW_meno_camion": p["n_vehicles"]["clarke_wright"] < p["n_vehicles"]["greedy"]})
    t = c.groupby("X_r").mean().mul(100).round(1)
    t.to_csv(OUT / "t1_E3_pari_X.csv")
    print("% di celle per X_r:")
    print(t.to_string())

    # --- punti scelti da Greedy rivalutati con CW alle stesse frequenze (= confronto a pari disservizio)
    S = pd.DataFrame(index=pd.MultiIndex.from_tuples([], names=k))
    righe = []
    GAM = np.round(np.arange(0.05, 0.951, 0.05), 2)
    for kk, g in R[R.algoritmo == "greedy"].groupby(KI + ["rifiuto"], sort=False):
        g = g.sort_values("X_r")
        kscala = g.k_scala.iloc[0]
        ft = (GAM[:, None] * kscala * g.F_insoddis.values[None, :]
              + (1 - GAM[:, None]) * g.F_costi.values[None, :])
        sel = g.iloc[ft.argmin(axis=1)]
        for gm, (_, r) in zip(GAM, sel.iterrows()):
            righe.append(dict(zip(KI + ["rifiuto"], kk), gamma=gm, X=r.X_r, C_G=r.F_costi))
    SG = pd.DataFrame(righe)
    cw = (R[R.algoritmo == "clarke_wright"][KI + ["rifiuto", "X_r", "F_costi"]]
          .rename(columns={"X_r": "X", "F_costi": "C_CW"}))
    m = SG.merge(cw, on=KI + ["rifiuto", "X"])
    tot = m.groupby(k)[["C_G", "C_CW"]].sum().reset_index()
    tot["CW_costo_minore"] = tot.C_CW < tot.C_G - TOL
    tot["risparmio_%"] = 100 * (tot.C_G - tot.C_CW) / tot.C_G
    s = tot.groupby("gamma").agg(CW_costo_minore=("CW_costo_minore", "mean"),
                                 risp_med=("risparmio_%", "median"),
                                 risp_min=("risparmio_%", "min"), risp_max=("risparmio_%", "max"))
    s["CW_costo_minore"] *= 100
    s.round(2).to_csv(OUT / "t1_E3_frontiera.csv")
    print("\n=== E3c: soluzione di Greedy rivalutata con CW alle stesse frequenze (stesso F_ins) ===")
    print(s.round(2).to_string())
    neg = tot[~tot.CW_costo_minore]
    if len(neg):
        print("\ncasi in cui CW costa di piu' alle frequenze di Greedy (istanza, n. casi):")
        print(neg.groupby(KS + ["gamma"]).size().to_string())


# ---------------------------------------------------------------------------------
# E5: soglie di gamma dei singoli passi di frequenza (inviluppo convesso inferiore per rifiuto)
#     il passo X_a -> X_b entra nella soluzione per gamma > s/(k+s), s = dC/dF_ins (euro per unita')
# ---------------------------------------------------------------------------------
def passi(g: pd.DataFrame) -> list[tuple]:
    g = g.sort_values("X_r")
    X, C, F = g.X_r.values, g.F_costi.values, g.F_insoddis.values
    i, out = int(np.argmin(C)), []
    while True:
        j_ok = np.flatnonzero(F < F[i] - TOL)
        if j_ok.size == 0:
            return out
        s = (C[j_ok] - C[i]) / (F[i] - F[j_ok])
        cand = j_ok[np.isclose(s, s.min(), rtol=0, atol=1e-12)]
        j = cand[np.argmin(F[cand])]                   # a pari pendenza: il punto con F minore
        out.append((X[i], X[j], C[j] - C[i], F[i] - F[j], s.min()))
        i = j


def e5(M: pd.DataFrame, R: pd.DataFrame) -> None:
    if R.empty:
        print("\nE5 saltato: nessun file in risultati_seed/")
        return
    righe = []
    for k, g in R.groupby(KI + ["algoritmo", "rifiuto"]):
        kk = g.k_scala.iloc[0]
        for xa, xb, dC, dF, s in passi(g):
            righe.append(dict(zip(KI + ["algoritmo", "rifiuto"], k), xa=xa, xb=xb,
                              dC=dC, dF=dF, s=s, g_sw=s / (kk + s)))
    H = pd.DataFrame(righe)
    H.to_csv(OUT / "t1_E5_passi.csv", index=False)

    # (a) stesso passo nei due algoritmi: CW lo anticipa?
    kp = KI + ["rifiuto", "xa", "xb"]
    m = (H[H.algoritmo == "clarke_wright"]
         .merge(H[H.algoritmo == "greedy"], on=kp, suffixes=("_C", "_G")))
    m["dg"] = m.g_sw_C - m.g_sw_G
    m["rDC"] = 100 * (m.dC_C / m.dC_G - 1)
    print(f"\n=== E5a: passi presenti in entrambi gli algoritmi: {len(m)} "
          f"(CW {int((H.algoritmo == 'clarke_wright').sum())}, Greedy {int((H.algoritmo == 'greedy').sum())}) ===")
    print(f"gamma* CW < gamma* Greedy: {100 * (m.dg < -1e-12).mean():.1f}% | "
          f"uguale: {100 * (m.dg.abs() <= 1e-12).mean():.1f}%")
    print("differenza gamma*_CW - gamma*_G e variazione % di dC (CW vs Greedy) per X di partenza:")
    print(m.groupby("xa").agg(n=("dg", "size"), dg_med=("dg", "median"), dg_min=("dg", "min"),
                              dg_max=("dg", "max"), rDC_med=("rDC", "median")).round(3).to_string())

    # (b) plateau = salto piu' ampio tra soglie consecutive (gamma <= 0.95) e passi che stanno sopra
    righe = []
    for k, g in H.groupby(KI + ["algoritmo"]):
        g = g[g.g_sw <= 0.95 + 1e-9].sort_values("g_sw")
        if len(g) < 2:
            continue
        s = g.g_sw.values
        i = int(np.diff(s).argmax())
        sopra = g.iloc[i + 1:]
        righe.append(dict(zip(KI + ["algoritmo"], k), g_lo=s[i], g_hi=s[i + 1],
                          passi_sopra=" ".join(f"{r.rifiuto}:{r.xa:g}-{r.xb:g}" for r in sopra.itertuples()),
                          dF_sopra_su_dF_sotto=sopra.dF.max() / g.iloc[:i + 1].dF.min()))
    P = pd.DataFrame(righe)
    P.to_csv(OUT / "t1_E5_plateau.csv", index=False)
    A = P.groupby(KS + ["algoritmo"])[["g_lo", "g_hi", "dF_sopra_su_dF_sotto"]].median().reset_index()
    print("\n=== E5b: intervallo di gamma senza soglie (mediana sui seed) ===")
    print(A.pivot_table(index=KS, columns="algoritmo", values=["g_lo", "g_hi"]).round(3).to_string())
    print("\npassi sopra il plateau (CW), frequenza dei casi:")
    print(P[P.algoritmo == "clarke_wright"].passi_sopra.value_counts().head(10).to_string())
    print("\nmax dF dei passi sopra / min dF dei passi sotto, CW (mediana [min-max] sulle istanze): "
          + mmm(A[A.algoritmo == "clarke_wright"].dF_sopra_su_dF_sotto, "{:.3f}"))


# ---------------------------------------------------------------------------------
# E4: costo marginale (euro per unita' di F_ins evitata) lungo la frontiera di ogni istanza
# ---------------------------------------------------------------------------------
def e4(M: pd.DataFrame) -> None:
    M = gamma_idx(M).sort_values("gamma")
    righe = []
    for k, s in M.groupby(KI + ["algoritmo"]):
        p = s.drop_duplicates(subset=["F_costi", "F_ins"], keep="first")
        p = p.assign(F_costi=p.F_costi.round(3), F_ins=p.F_ins.round(3))
        dI, dC = -p.F_ins.diff().values[1:], p.F_costi.diff().values[1:]
        ok = dI > TOL
        if ok.sum() < 2:
            righe.append(dict(zip(KI + ["algoritmo"], k), n_sol=len(p), n_pend=int(ok.sum())))
            continue
        pend = dC[ok] / dI[ok]
        gj = p.gamma.values[1:][ok]
        righe.append(dict(zip(KI + ["algoritmo"], k), n_sol=len(p), n_pend=int(ok.sum()),
                          pend_prima=pend[0], pend_ultima=pend[-1], rapporto=pend[-1] / pend[0],
                          crescente=bool(np.all(np.diff(pend) >= -1e-9)),
                          gamma_salto_max=gj[pend.argmax()], quota_max=pend.max() / pend[:-1].max()
                          if len(pend) > 1 else np.nan))
    P = pd.DataFrame(righe)
    A = (P.groupby(KS + ["algoritmo"])
          .agg(n_sol=("n_sol", "median"), pend_prima=("pend_prima", "median"),
               pend_ultima=("pend_ultima", "median"), rapporto=("rapporto", "median"),
               crescente_pct=("crescente", lambda x: 100 * x.mean()),
               gamma_salto=("gamma_salto_max", "median")).reset_index())
    A.to_csv(OUT / "t1_E4.csv", index=False)
    print("\n=== E4: pendenza (euro per unita' di F_ins evitata) lungo la frontiera; mediana sui seed ===")
    print(A.round(3).to_string(index=False))
    print("\nsintesi sulle istanze (mediana [min-max]):")
    for algo, d in A.groupby("algoritmo"):
        print(f"{algo:14s} prima: {mmm(d.pend_prima, '{:.3f}')} | ultima: {mmm(d.pend_ultima, '{:.2f}')} | "
              f"rapporto: {mmm(d.rapporto, '{:.0f}')} | % seed con pendenze crescenti: {mmm(d.crescente_pct, '{:.0f}')}")


def main() -> None:
    scelte = [a.upper() for a in sys.argv[1:]] or ["E1", "E2", "E3", "E4", "E5"]
    M = carica_metriche()
    print(f"istanze indipendenti: {M.groupby(KS).ngroups} | righe: {len(M)}")
    R = carica_grezzi(M) if {"E3", "E5"} & set(scelte) else pd.DataFrame()
    for nome, f in (("E1", e1), ("E2", e2), ("E3", e3), ("E4", e4), ("E5", e5)):
        if nome in scelte:
            f(M, R) if nome in ("E3", "E5") else f(M)


if __name__ == "__main__":
    main()