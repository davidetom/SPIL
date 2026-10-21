# figure_pareto.py
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
OUT = ROOT / "analisi_seed"

M = pd.read_csv(OUT / "riepilogo_metriche.csv")
CASI = {"Fabriano (reale, N=3932)": ("B4", 3932, "reale", "reale"),
        "B1, N=1000 (30 seed)": ("B1", 1000, "residenziale", "uniform"),
        "B5, N=200 (30 seed)": ("B5", 200, "residenziale", "std")}
COL = {"greedy": "#2171b5", "clarke_wright": "#d95f0e"}
NAME = {"greedy": "Greedy", "clarke_wright": "Clarke-Wright"}
GAMMAS = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]
EVID = (0.1, 0.5, 0.9)
RIF = ["carta", "indifferenziata", "organico", "plastica", "vetro"]


def caso(b, N, sc, mo):
    return M[(M.bench == b) & (M.N == N) & (M.scenario == sc) & (M.modo == mo)]


def sel(d):
    return d[np.isclose(d.gamma.values[:, None], GAMMAS).any(axis=1)].sort_values("gamma")


def fig_pareto():
    fig, axs = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (titolo, k) in zip(axs, CASI.items()):
        d = caso(*k)
        for algo in COL:
            s = sel(d[d.algoritmo == algo])
            ax.errorbar(s.F_costi_mean, s.F_ins_mean,
                        xerr=s.F_costi_ci95.fillna(0), yerr=s.F_ins_ci95.fillna(0),
                        marker="o", ms=4, lw=1.3, capsize=2, color=COL[algo], label=NAME[algo])
            for _, r in s.iterrows():
                if any(np.isclose(r.gamma, g) for g in EVID):
                    ax.scatter(r.F_costi_mean, r.F_ins_mean, s=70, color=COL[algo],
                               edgecolor="k", zorder=5)
                    ax.annotate(f"γ={r.gamma:.1f}", (r.F_costi_mean, r.F_ins_mean),
                                textcoords="offset points",
                                xytext=(8, 8) if algo == "greedy" else (-8, -14),
                                ha="left" if algo == "greedy" else "right", fontsize=8)
        ax.set_title(titolo)
        ax.set_xlabel("Costo logistico settimanale grezzo (€)")
        ax.set_ylabel("Disservizio F_ins grezzo")
        ax.grid(alpha=.3); ax.legend()
        ax.margins(x=0.08, y=0.14)
    fig.suptitle("Frontiere di Pareto empiriche al variare di γ (barre = IC95 sui seed)")
    fig.tight_layout(); fig.savefig(OUT / "fig_pareto.png", dpi=300); plt.close(fig)


def linea(ax, d, col, titolo):
    for algo in COL:
        s = d[d.algoritmo == algo].sort_values("gamma")
        ci = s[col + "_ci95"].fillna(0)
        ax.plot(s.gamma, s[col + "_mean"], color=COL[algo], lw=1.6, marker="o", ms=3, label=NAME[algo])
        ax.fill_between(s.gamma, s[col + "_mean"] - ci, s[col + "_mean"] + ci,
                        color=COL[algo], alpha=.18)
    ax.set_title(titolo, fontsize=10); ax.set_xlabel("γ"); ax.grid(alpha=.3)


def fig_fisica(titolo, k, nome):
    d = caso(*k)
    fig, axs = plt.subplots(2, 3, figsize=(16, 8))
    spec = [("V", "Camion per giro (V)"), ("VxX", "Attivazioni settimanali (V·X)"),
            ("km", "km settimanali"), ("ore", "Ore di lavoro settimanali"),
            ("F_ins", "Disservizio F_ins (grezzo)")]
    for ax, (c, t) in zip(axs.ravel(), spec):
        linea(ax, d, c, t)
    axs[0, 0].legend()
    ax = axs[1, 2]
    cm = plt.cm.tab10
    for i, r in enumerate(RIF):
        for algo, ls in (("clarke_wright", "-"), ("greedy", "--")):
            s = d[d.algoritmo == algo].sort_values("gamma")
            ax.plot(s.gamma, s[f"X_{r}_mean"], ls, color=cm(i), lw=1.3,
                    label=r if algo == "clarke_wright" else None)
    ax.set_title("Frequenza ottima X* (CW continuo, Greedy tratteggiato)", fontsize=10)
    ax.set_xlabel("γ"); ax.grid(alpha=.3); ax.legend(fontsize=8)
    fig.suptitle(titolo); fig.tight_layout()
    fig.savefig(OUT / f"fig_fisica_{nome}.png", dpi=300); plt.close(fig)


def marginale():
    rows = []
    for (b, N, sc, mo, algo), d in M.groupby(["bench", "N", "scenario", "modo", "algoritmo"]):
        d = d.assign(g=np.round(d.gamma, 2)).set_index("g")
        if not {0.1, 0.5, 0.9} <= set(d.index):
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            c1 = ((d.loc[0.5, "F_costi_mean"] - d.loc[0.1, "F_costi_mean"])
                  / (d.loc[0.1, "F_ins_mean"] - d.loc[0.5, "F_ins_mean"]))
            c2 = ((d.loc[0.9, "F_costi_mean"] - d.loc[0.5, "F_costi_mean"])
                  / (d.loc[0.5, "F_ins_mean"] - d.loc[0.9, "F_ins_mean"]))
        rows.append(dict(bench=b, N=N, scenario=sc, modo=mo, algoritmo=algo,
                         euro_per_unita_01_05=c1, euro_per_unita_05_09=c2, rapporto=c2 / c1))
    return pd.DataFrame(rows)

I = pd.read_csv(OUT / "metriche_istanza.csv")

def fig_intervalli(b="B4", nome="Fabriano"):
    d = I[I.bench == b].sort_values(["algoritmo", "gamma"])
    fig, ax = plt.subplots(figsize=(9, 6))
    for algo in COL:
        s = d[d.algoritmo == algo].reset_index(drop=True)
        chiave = s[["F_costi", "F_ins"]].round(1).astype(str).agg("|".join, axis=1)
        blocco = (chiave != chiave.shift()).cumsum()
        g = s.groupby(blocco).agg(g0=("gamma", "min"), g1=("gamma", "max"),
                                  F_costi=("F_costi", "first"), F_ins=("F_ins", "first"))
        ax.plot(g.F_costi, g.F_ins, "-", color=COL[algo], lw=1, alpha=.6)
        ax.scatter(g.F_costi, g.F_ins, s=45, color=COL[algo], label=NAME[algo], zorder=3)
        for i, (_, r) in enumerate(g.iterrows()):
            et = f"{r.g0:.2f}" if r.g0 == r.g1 else f"{r.g0:.2f}–{r.g1:.2f}"
            dy = 6 + 10 * (i % 2) if algo == "greedy" else -12 - 10 * (i % 2)
            ax.annotate(et, (r.F_costi, r.F_ins), textcoords="offset points", fontsize=7,
                        xytext=(6, dy) if algo == "greedy" else (-6, dy),
                        ha="left" if algo == "greedy" else "right")
    ax.set_xlabel("Costo logistico settimanale grezzo (€)"); ax.set_ylabel("Disservizio F_ins grezzo")
    ax.set_title(f"{nome}: soluzioni distinte e intervalli di γ per cui sono ottime")
    ax.grid(alpha=.3); ax.legend(); fig.tight_layout()
    fig.savefig(OUT / f"fig_intervalli_{b}.png", dpi=300); plt.close(fig)

if __name__ == "__main__":
    fig_pareto()
    fig_intervalli()
    for titolo, k in CASI.items():
        fig_fisica(titolo, k, k[0])
    mg = marginale()
    mg.to_csv(OUT / "costo_marginale.csv", index=False)
    print(mg.round(3).to_string(index=False))
