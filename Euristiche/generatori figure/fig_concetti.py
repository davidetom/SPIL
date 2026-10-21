# fig_concetti.py
# Tre figure "di concetto" per il Capitolo 3.
# Produce (in analisi_seed/):
#   fig_V_vs_X.png            camion per giro contro frequenza X_r (paradosso dei camion)
#   fig_gap_profilo_B1.png / _B3.png / _B4.png
#                             gap logistico di CW a X_r comune (regimi capacita' / tempo)
#   fig_gap_scomposizione.png gap su F_tot = routing a pari X + spostamento di X*
#
# Input: risultati_seed/*.csv (colonne di batch_seed.py) e analisi_seed/riepilogo_gap.csv.
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

COL = {"greedy": "#1f77b4", "clarke_wright": "#d95f02"}
LAB = {"greedy": "Greedy", "clarke_wright": "Clarke-Wright"}
COSTI = ["F_costo_fisso", "F_viaggio", "F_lavoro"]
USE = ["bench", "seed", "N", "scenario", "modo", "rifiuto", "X_r", "algoritmo",
       "n_vehicles"] + COSTI


def ci95(x: pd.Series) -> float:
    x = x.dropna()
    n = len(x)
    return float(stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n)) if n > 1 else np.nan


def carica() -> pd.DataFrame:
    files = sorted((ROOT / "risultati_seed").glob("*.csv"))
    if not files:
        sys.exit(f"Nessun CSV in {ROOT / 'risultati_seed'}: verificare la cartella.")
    parts = []
    for f in files:
        d = pd.read_csv(f, usecols=USE)
        parts.append(d)
    D = pd.concat(parts, ignore_index=True)
    return D[D.bench.isin(["B1", "B1S", "B2", "B3", "B4sub"])]


def sel(D: pd.DataFrame, bench: str, N: int, scenario: str | None = None,
        modo: str | None = None) -> pd.DataFrame:
    m = (D.bench == bench) & (D.N == N)
    if scenario is not None:
        m &= D.scenario == scenario
    if modo is not None:
        m &= D.modo == modo
    return D[m]


# ----------------------------------------------------------------------------
# Figura 1: camion per giro contro X_r
# ----------------------------------------------------------------------------
def fig_V_vs_X(D: pd.DataFrame, rifiuto: str) -> None:
    pannelli = [("B1: N=1000, residenziale", sel(D, "B1", 1000)),
                ("B2: grandi condomini, N=400", sel(D, "B2", 400, "grandi_condomini")),
                ("B2: villette, N=400", sel(D, "B2", 400, "villette"))]
    if rifiuto not in set(D.rifiuto):
        sys.exit(f"Rifiuto '{rifiuto}' assente. Disponibili: {sorted(set(D.rifiuto))}")
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
    for ax, (tit, d) in zip(axs, pannelli):
        d = d[d.rifiuto == rifiuto]
        if d.empty:
            ax.set_title(tit + " (dati assenti)"); continue
        ymax = 0
        for alg in ("greedy", "clarke_wright"):
            g = d[d.algoritmo == alg].groupby("X_r").n_vehicles
            m, e = g.mean(), g.apply(ci95)
            ax.plot(m.index, m.values, "-o", ms=4, color=COL[alg], label=LAB[alg])
            ax.fill_between(m.index, m - e, m + e, color=COL[alg], alpha=.2)
            ymax = max(ymax, float((m + e).max()))
            if alg == "greedy":
                x0, v0 = float(m.index.min()), float(m.iloc[0])
        xs = np.linspace(x0, float(d.X_r.max()), 100)
        ax.plot(xs, v0 * x0 / xs, "--", color="gray", lw=1.2,
                label=f"$V\\cdot X$ = costante ({v0 * x0:.1f})")
        ax.set_ylim(0, ymax * 1.1)
        ax.set_title(tit, fontsize=10)
        ax.set_xlabel("Frequenza settimanale $X_r$")
        ax.grid(alpha=.3)
    axs[0].set_ylabel(f"Camion per giro $V_r$ ({rifiuto})")
    axs[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "analisi_seed/fig_V_vs_X.png", dpi=300)
    plt.close(fig)


# ----------------------------------------------------------------------------
# Figura 2: gap logistico a X_r comune
# gap per seed = (C_G - C_CW) / min(C_G, C_CW), con C = costo logistico settimanale
# (fisso + viaggio + lavoro) sommato sui rifiuti, tutti alla stessa X_r.
# ----------------------------------------------------------------------------
def profilo(d: pd.DataFrame) -> pd.DataFrame:
    """Gap logistico a X_r comune, stessa definizione di test_profilo_gap.py:
    per ogni (seed, rifiuto, X_r)  gap = (C_G - C_CW) / C_CW * 100, con C = fisso+viaggio+lavoro;
    media sui rifiuti entro ogni seed, poi media sui seed e IC95 (t di Student) sui seed."""
    d = d.assign(C=d[COSTI].sum(axis=1))
    c = d.pivot_table(index=["seed", "rifiuto", "X_r"], columns="algoritmo", values="C")
    gap = (c["greedy"] - c["clarke_wright"]) / c["clarke_wright"] * 100
    per_seed = gap.groupby(["seed", "X_r"]).mean().unstack("X_r")
    m = per_seed.mean()
    e = per_seed.apply(ci95)
    return pd.DataFrame({"m": m, "lo": m - e, "hi": m + e})


def fig_gap_profilo(D: pd.DataFrame) -> None:
    def traccia(ax, d, lab, col, mk):
        if d.empty:
            return
        p = profilo(d)
        ax.plot(p.index, p.m, color=col, marker=mk, ms=4, lw=1.5, label=lab)
        ax.fill_between(p.index, p.lo, p.hi, color=col, alpha=.15)

    def chiudi(fig, ax, nome):
        ax.set_xlabel("Frequenza comune $X_r$ (tutti i rifiuti)")
        ax.set_ylabel("Gap logistico Greedy–CW (%)")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(ROOT / f"analisi_seed/{nome}", dpi=300)
        plt.close(fig)

    # B1: al variare di N
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    cm = plt.get_cmap("viridis")
    for k, N in enumerate((100, 250, 500, 1000)):
        traccia(ax, sel(D, "B1", N), f"N={N}", cm(k / 3.2), "o")
    chiudi(fig, ax, "fig_gap_profilo_B1.png")

    # B3: uniforme contro aggregata
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    traccia(ax, sel(D, "B2", 400, "residenziale"), "Uniforme (= B2 residenziale)", "#6a3d9a", "o")
    traccia(ax, sel(D, "B3", 400, modo="cluster"), "Aggregata (cluster)", "#e31a1c", "s")
    chiudi(fig, ax, "fig_gap_profilo_B3.png")

    # Sintetico contro Fabriano a N=1000
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    traccia(ax, sel(D, "B1", 1000), "Sintetico, $A$=100 km² (B1)", "#6a3d9a", "o")
    traccia(ax, sel(D, "B1S", 1000), "Sintetico, area e mix di Fabriano (B1S)", "#33a02c", "s")
    traccia(ax, sel(D, "B4sub", 1000), "Fabriano, utenti reali (B4sub)", "#e31a1c", "^")
    chiudi(fig, ax, "fig_gap_profilo_B4.png")


# ----------------------------------------------------------------------------
# Figura 3: scomposizione del gap su F_tot
# gap_tot = da_routing (a pari X) + da_shiftX (spostamento di X*)
# ----------------------------------------------------------------------------
def fig_scomposizione() -> None:
    G = pd.read_csv(ROOT / "analisi_seed/riepilogo_gap.csv")
    G["gamma"] = G["gamma"].round(2)
    gam = {0.1: "#1f78b4", 0.5: "#e31a1c", 0.9: "#33a02c"}
    pann = [("B1: al variare di $N$", "B1", "N", [100, 250, 500, 750, 1000], 5),
            ("B2: per scenario ($N=400$)", "B2", "scenario",
             ["residenziale", "suburbano", "misto_periferia", "grandi_condomini", "villette"], 5),
            ("B5 ($N=200$)", "B5", "N", [200], 1.3)]
    etic = {"misto_periferia": "misto", "grandi_condomini": "grandi\ncond.",
            "residenziale": "resid.", "suburbano": "suburb.", "villette": "villette"}
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6),
                            gridspec_kw={"width_ratios": [5, 5, 1.6]})
    w = 0.26
    for ax, (tit, b, chiave, cats, _) in zip(axs, pann):
        for i, c in enumerate(cats):
            for k, (g, col) in enumerate(gam.items()):
                r = G[(G.bench == b) & (G[chiave] == c) & (G.gamma == g)]
                if r.empty:
                    continue
                r = r.iloc[0]
                x = i + (k - 1) * w
                ax.bar(x, r.da_routing_mean, w, color=col, alpha=.9)
                ax.bar(x, r.da_shiftX_mean, w, bottom=r.da_routing_mean, color=col,
                       alpha=.45, hatch="///", edgecolor="white")
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels([etic.get(c, str(c)) for c in cats], fontsize=9)
        ax.set_title(tit, fontsize=10)
        ax.grid(axis="y", alpha=.3)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.1)
    axs[0].set_ylabel("Gap $F_{tot}$ (punti percentuali)")
    from matplotlib.patches import Patch
    leg = [Patch(color=c, label=f"$\\gamma$={g}") for g, c in gam.items()]
    leg += [Patch(facecolor="gray", alpha=.9, label="routing a pari $X$"),
            Patch(facecolor="gray", alpha=.45, hatch="///", edgecolor="white",
                  label="spostamento di $X^*$")]
    axs[0].legend(handles=leg, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(ROOT / "analisi_seed/fig_gap_scomposizione.png", dpi=300)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rifiuto", default="organico")
    a = ap.parse_args()
    D = carica()
    fig_V_vs_X(D, a.rifiuto)
    fig_gap_profilo(D)
    fig_scomposizione()
    print(f"ok: {ROOT / 'analisi_seed/fig_V_vs_X'}, fig_gap_profilo_B1/B3/B4, fig_gap_scomposizione (analisi_seed/)")


if __name__ == "__main__":
    main()
