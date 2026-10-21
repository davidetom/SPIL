# fig_gap_vs_N.py
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # cartella Euristiche/

G = pd.read_csv(ROOT / "analisi_seed/riepilogo_gap.csv")
serie = {"B1": ("Sintetico originale (A=100 km²)", "#6a3d9a", "o"),
         "B1S": ("Sintetico con area e mix di Fabriano", "#33a02c", "s"),
         "B4sub": ("Fabriano, utenti reali campionati", "#e31a1c", "^")}
fig, axs = plt.subplots(1, 3, figsize=(16, 4.6), sharey=True)
for ax, g in zip(axs, (0.1, 0.5, 0.9)):
    for b, (lab, col, mk) in serie.items():
        d = G[(G.bench == b) & (G.gamma.round(2) == g)].sort_values("N")
        ax.errorbar(d.N, d.gap_tot_mean, yerr=d.gap_tot_ci95, color=col, marker=mk,
                    capsize=3, lw=1.5, label=lab)
    f = G[(G.bench == "B4") & (G.gamma.round(2) == g)]
    ax.scatter(f.N, f.gap_tot_mean, color="k", marker="*", s=130, zorder=5,
               label="Fabriano, tutti gli utenti (N=3932)")
    ax.set_xscale("log"); ax.set_title(f"γ = {g}")
    ax.set_xlabel("N utenti"); ax.grid(alpha=.3)
axs[0].set_ylabel("Gap F_tot Greedy–CW (%)"); axs[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(ROOT / "analisi_seed/fig_gap_vs_N.png", dpi=300)
