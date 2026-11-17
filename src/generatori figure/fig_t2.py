# fig_t2.py
# Figure del Benchmark Trasversale 2.
#   fig_t2_regimi.png    : Fabriano (istanza completa, CW): saturazione temporale e fisica in funzione di X_r
#                          per rifiuto, con la soglia prevista X_pred = 6 * sat_fisica(6) / 100
#   fig_t2_algoritmi.png : CW vs Greedy a pari X_r sulle 23 istanze (da analisi_seed/t2_P4.csv):
#                          vantaggio logistico e variazione dei camion per giro, mediana e min-max
# Input : risultati_csv/risultati_3932u_mappa_reale_gamma0.50.csv, analisi_seed/t2_P4.csv (t2_profilo.py)
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
OUT = ROOT / "analisi_seed"
B4_CSV = ROOT / "risultati_csv" / "risultati_3932u_mappa_reale_gamma0.50.csv"
RIF = ["organico", "indifferenziata", "plastica", "carta", "vetro"]
C_T, C_F = "#d95f0e", "#6a51a3"       # saturazione temporale, fisica
C_ALGO = "#d95f0e"


def stile(ax):
    ax.grid(alpha=0.25, lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)


def fig_regimi():
    d = pd.read_csv(B4_CSV)
    d = d[d.algoritmo == "clarke_wright"].sort_values("X_r")
    fig, axs = plt.subplots(1, 5, figsize=(17, 3.9), sharey=True)
    for ax, r in zip(axs, RIF):
        g = d[d.rifiuto == r]
        ax.plot(g.X_r, g.sat_tempo, "-", color=C_T, lw=2, marker="o", ms=4, mec="white", label="saturazione temporale")
        ax.plot(g.X_r, g.sat_fisica, "--", color=C_F, lw=2, marker="s", ms=4, mec="white", label="saturazione fisica")
        x_pred = g.X_r.iloc[-1] * g.sat_fisica.iloc[-1] / 100
        V = g.n_vehicles.values
        cambia = np.flatnonzero(V != V[-1])
        x_obs = g.X_r.values[cambia[-1] + 1] if cambia.size else g.X_r.values[0]
        ax.axvline(x_pred, color="#555555", lw=1, ls=":")
        ax.text(x_pred, 103, f"$\\bar X$={x_pred:.2f}", ha="center", fontsize=8.5, color="#333333")
        ax.set_title(f"{r}  (V costante da X={x_obs:g})", fontsize=10)
        ax.set_xlabel("$X_r$ (ritiri a settimana)")
        ax.set_ylim(0, 110)
        stile(ax)
    axs[0].set_ylabel("%")
    axs[0].legend(frameon=False, fontsize=8.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "fig_t2_regimi.png", dpi=300)
    plt.close(fig)


def fig_algoritmi():
    A = pd.read_csv(OUT / "t2_P4.csv")
    s = A.groupby("X_r").agg(Lm=("L_g", "median"), L0=("L_g", "min"), L1=("L_g", "max"),
                             Vm=("dV_pct", "median"), V0=("dV_pct", "min"), V1=("dV_pct", "max")).reset_index()
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, (m, lo, hi, tit, yl) in zip(axs, [
            ("Lm", "L0", "L1", "Vantaggio logistico di CW", "costo Greedy / costo CW $-$ 1 (%)"),
            ("Vm", "V0", "V1", "Camion per giro di CW rispetto a Greedy", "camion CW / camion Greedy $-$ 1 (%)")]):
        ax.fill_between(s.X_r, s[lo], s[hi], color=C_ALGO, alpha=0.15, lw=0, label="minimo-massimo sulle istanze")
        ax.plot(s.X_r, s[m], "-", color=C_ALGO, lw=2, marker="o", ms=5, mec="white", label="mediana sulle istanze")
        ax.axhline(0, color="#777777", lw=0.8)
        ax.set_title(tit, fontsize=11)
        ax.set_xlabel("$X_r$ (ritiri a settimana)")
        ax.set_ylabel(yl)
        stile(ax)
    axs[0].legend(frameon=False, fontsize=9, loc="center right")
    fig.tight_layout()
    fig.savefig(OUT / "fig_t2_algoritmi.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    fig_regimi()
    fig_algoritmi()
    print("salvate:", OUT / "fig_t2_regimi.png", OUT / "fig_t2_algoritmi.png")