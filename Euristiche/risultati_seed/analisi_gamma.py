# analisi_gamma.py
#   python analisi_gamma.py                  # analisi completa -> analisi_seed/
#   python analisi_gamma.py --estese         # solo B1L, B1SL, B4sub (tutte le N presenti) -> analisi_seed_estese/
#   python analisi_gamma.py --estese --con-b4   # come sopra, piu' l'istanza completa di Fabriano
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

IN, OUT = Path("risultati_seed"), Path("analisi_seed")
B4_CSV = Path("risultati_csv/risultati_3932u_mappa_reale_gamma0.50.csv")
CD, CM, MIN_PER_KM = 0.35, 0.25, 60 / 25
# modalita' --estese: solo questi CSV
BENCH_ESTESE = ["B1L", "B1SL", "B4sub"]
GAMMAS = np.round(np.arange(0.05, 0.951, 0.05), 2)
KI = ["bench", "N", "scenario", "modo", "seed"]     # istanza
KS = ["bench", "N", "scenario", "modo"]             # scenario (si aggrega sui seed)


def carica(estese: bool = False, con_b4: bool = False) -> pd.DataFrame:
    R = pd.concat([pd.read_csv(f) for f in sorted(IN.glob("*.csv"))], ignore_index=True)
    if estese:
        R = R[R.bench.isin(BENCH_ESTESE)].reset_index(drop=True)
        if R.empty:
            raise SystemExit("Nessun CSV di B1L/B1SL/B4sub in risultati_seed/")
    else:
        u = R[(R.bench == "B2") & (R.scenario == "residenziale")].copy()   # B3 uniform = B2 residenziale
        u["bench"] = "B3"
        R = pd.concat([R, u], ignore_index=True)
    R["F_costi"] = R.F_costo_fisso + R.F_viaggio + R.F_lavoro
    if (not estese or con_b4) and B4_CSV.exists():
        d = pd.read_csv(B4_CSV)
        d["F_costi"] = d.F_costo_fisso + d.F_viaggio + d.F_lavoro
        d["k_scala"] = ((d.F_total - 0.5 * d.F_costi) / (0.5 * d.F_insoddis)).median()
        d["bench"], d["N"], d["scenario"], d["modo"], d["seed"] = "B4", 3932, "reale", "reale", 0
        R = pd.concat([R, d[R.columns.intersection(d.columns)]], ignore_index=True)
    return R


def seleziona(R: pd.DataFrame) -> pd.DataFrame:
    """Riga a X* per ogni (istanza, algoritmo, rifiuto, gamma)."""
    out = []
    for _, g in R.groupby(KI + ["algoritmo", "rifiuto"], sort=False):
        g = g.sort_values("X_r")
        k = g.k_scala.iloc[0]
        ft = (GAMMAS[:, None] * k * g.F_insoddis.values[None, :]
              + (1 - GAMMAS[:, None]) * g.F_costi.values[None, :])
        idx = ft.argmin(axis=1)
        s = g.iloc[idx].copy()
        s["gamma"] = GAMMAS
        s["F_tot"] = ft[np.arange(len(GAMMAS)), idx]
        out.append(s)
    return pd.concat(out, ignore_index=True)


def metriche(S: pd.DataFrame) -> pd.DataFrame:
    S = S.copy()
    S["km_sett"] = S.F_viaggio / CD
    S["min_sett"] = S.F_lavoro / CM
    S["VxX"] = S.n_vehicles * S.X_r
    S["quota_viaggio"] = 100 * MIN_PER_KM * S.km_sett / S.min_sett
    keys = KI + ["gamma", "algoritmo"]
    agg = S.groupby(keys).agg(
        V=("n_vehicles", "sum"), VxX=("VxX", "sum"), km=("km_sett", "sum"),
        ore=("min_sett", lambda s: s.sum() / 60), F_ins=("F_insoddis", "sum"),
        F_fisso=("F_costo_fisso", "sum"), F_viaggio=("F_viaggio", "sum"),
        F_lavoro=("F_lavoro", "sum"), F_costi=("F_costi", "sum"), F_tot=("F_tot", "sum"),
        sat_f=("sat_fisica", "mean"), sat_t=("sat_tempo", "mean"),
        quota_viaggio=("quota_viaggio", "mean"), n_serv=("n_utenti_serviti", "sum"))
    xs = S.pivot_table(index=keys, columns="rifiuto", values="X_r").add_prefix("X_")
    return agg.join(xs).reset_index()


def gap(M: pd.DataFrame, S: pd.DataFrame, R: pd.DataFrame) -> pd.DataFrame:
    G = M[M.algoritmo == "greedy"].set_index(KI + ["gamma"])
    C = M[M.algoritmo == "clarke_wright"].set_index(KI + ["gamma"])
    out = pd.DataFrame(index=G.index)
    out["gap_tot"] = (G.F_tot - C.F_tot) / np.minimum(G.F_tot, C.F_tot) * 100
    for c in ["F_ins", "F_costi", "V", "VxX", "km", "ore"]:       # CW rispetto a Greedy, %
        out["d_" + c] = (C[c] - G[c]) / G[c] * 100
    sg = (S[S.algoritmo == "greedy"][KI + ["rifiuto", "gamma", "X_r", "F_tot"]]
          .rename(columns={"X_r": "X_G", "F_tot": "Ft_G"}))
    sc = (S[S.algoritmo == "clarke_wright"][KI + ["rifiuto", "gamma", "F_tot"]]
          .rename(columns={"F_tot": "Ft_C"}))
    cw = (R[R.algoritmo == "clarke_wright"][KI + ["rifiuto", "X_r", "F_insoddis", "F_costi", "k_scala"]]
          .rename(columns={"X_r": "X_G"}))
    m = sg.merge(sc, on=KI + ["rifiuto", "gamma"]).merge(cw, on=KI + ["rifiuto", "X_G"], how="left")
    m["Ft_C_at_XG"] = m.gamma * m.k_scala * m.F_insoddis + (1 - m.gamma) * m.F_costi
    m["routing"] = m.Ft_G - m.Ft_C_at_XG
    m["shiftX"] = m.Ft_C_at_XG - m.Ft_C
    t = m.groupby(KI + ["gamma"]).agg(routing=("routing", "sum"), shiftX=("shiftX", "sum"),
                                      FtC=("Ft_C", "sum"))
    out["da_routing"] = t.routing / t.FtC * 100
    out["da_shiftX"] = t.shiftX / t.FtC * 100
    return out.reset_index()


def plateau(R: pd.DataFrame) -> pd.DataFrame:
    """Diagnostica a X fissato (indipendente da gamma)."""
    p = R.pivot_table(index=KI + ["rifiuto", "X_r"], columns="algoritmo",
                      values=["F_costi", "F_costo_fisso", "n_vehicles"])
    gx = pd.DataFrame({
        "gap": (p["F_costi"]["greedy"] - p["F_costi"]["clarke_wright"]) / p["F_costi"]["clarke_wright"] * 100,
        "dV": p["n_vehicles"]["greedy"] - p["n_vehicles"]["clarke_wright"],
        "dFisso": p["F_costo_fisso"]["greedy"] - p["F_costo_fisso"]["clarke_wright"],
        "dCosti": p["F_costi"]["greedy"] - p["F_costi"]["clarke_wright"]}).reset_index()
    hi = gx[gx.X_r >= 3]
    a = hi.groupby(KI).agg(gap_plateau=("gap", "mean"), dFisso=("dFisso", "sum"), dCosti=("dCosti", "sum"))
    a["quota_fisso"] = 100 * a.dFisso / a.dCosti
    a["dV_plateau"] = hi.groupby(KI + ["X_r"]).dV.sum().groupby(KI).mean()
    lo = gx[gx.X_r == 0.5].groupby(KI).agg(gap_X05=("gap", "mean"), dV_X05=("dV", "sum"))
    return a.join(lo).reset_index()


def ci95(x: pd.Series) -> float:
    x = x.dropna()
    return stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else np.nan


def riepiloga(df: pd.DataFrame, keys: list[str], cols: list[str]) -> pd.DataFrame:
    g = df.groupby(keys)[cols]
    return pd.concat([g.mean().add_suffix("_mean"), g.std(ddof=1).add_suffix("_std"),
                      g.agg(ci95).add_suffix("_ci95"), g.size().rename("n_seed")],
                     axis=1).reset_index()


def main() -> None:
    global OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("--estese", action="store_true",
                    help="usa solo B1L, B1SL e B4sub (tutte le N presenti); output in analisi_seed_estese/")
    ap.add_argument("--con-b4", action="store_true",
                    help="con --estese: aggiunge anche l'istanza completa di Fabriano (CSV principale)")
    a = ap.parse_args()
    if a.estese:
        OUT = Path("analisi_seed_estese")
    OUT.mkdir(exist_ok=True)
    R = carica(a.estese, a.con_b4)
    print("seed distinti per scenario:")
    print(R.groupby(KS).seed.nunique().to_string())
    S = seleziona(R)
    M = metriche(S)
    print("\nistanze con utenti serviti < 5N:", int((M.n_serv < 5 * M.N).sum()))
    G = gap(M, S, R)
    P = plateau(R)
    M.to_csv(OUT / "metriche_istanza.csv", index=False)
    G.to_csv(OUT / "gap_istanza.csv", index=False)
    P.to_csv(OUT / "plateau_istanza.csv", index=False)

    mcols = (["V", "VxX", "km", "ore", "F_ins", "F_costi", "sat_f", "sat_t", "quota_viaggio"]
             + [c for c in M.columns if c.startswith("X_")])
    gcols = ["gap_tot", "da_routing", "da_shiftX", "d_F_ins", "d_F_costi", "d_V", "d_VxX", "d_km", "d_ore"]
    pcols = ["gap_plateau", "quota_fisso", "dV_plateau", "gap_X05", "dV_X05"]
    riepiloga(M, KS + ["gamma", "algoritmo"], mcols).to_csv(OUT / "riepilogo_metriche.csv", index=False)
    rg = riepiloga(G, KS + ["gamma"], gcols)
    rg.to_csv(OUT / "riepilogo_gap.csv", index=False)
    riepiloga(P, KS, pcols).to_csv(OUT / "riepilogo_plateau.csv", index=False)

    if not a.estese:
        # controllo sul seed 42: attesi B5 -> (3.12, 3.04, 0.07), (8.18, 7.98, 0.20), (2.91, 2.91, 0.00)
        print("\nCONTROLLO seed 42 (B5):")
        c = G[(G.seed == 42) & (G.bench == "B5") & G.gamma.isin([0.1, 0.5, 0.9])]
        print(c[["gamma", "gap_tot", "da_routing", "da_shiftX"]].round(2).to_string(index=False))
        print("CONTROLLO seed 42 (B1, N=100, gamma=0.5): atteso gap_tot 29.05")
        c = G[(G.seed == 42) & (G.bench == "B1") & (G.N == 100) & (G.gamma == 0.5)]
        print(c[["gamma", "gap_tot"]].round(2).to_string(index=False))

    print("\nRIEPILOGO GAP (media, CI95 sui seed)")
    s = rg[rg.gamma.isin([0.1, 0.5, 0.9])]
    print(s[KS + ["gamma", "n_seed", "gap_tot_mean", "gap_tot_ci95", "da_routing_mean",
                  "da_shiftX_mean", "d_F_costi_mean", "d_F_ins_mean", "d_V_mean"]]
          .round(2).to_string(index=False))


if __name__ == "__main__":
    main()