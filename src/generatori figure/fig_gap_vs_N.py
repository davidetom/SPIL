# fig_gap_vs_N.py
# Legge solo analisi_seed_estese/riepilogo_gap.csv (prodotto da: python analisi_gamma.py --estese)
# e salva analisi_seed_estese/fig_gap_vs_N.png.
# Serie: B1L (sintetico originale), B1SL (sintetico con area e mix di Fabriano),
#        B4sub (Fabriano, utenti reali campionati, tutte le N presenti).
# Se il riepilogo contiene anche B4 (analisi_gamma.py --estese --con-b4) aggiunge la stella N=3932.
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
DIR = ROOT / "analisi_seed_estese"

G = pd.read_csv(DIR / "riepilogo_gap.csv")
serie = {"B1L": ("Sintetico originale (A=100 km²)", "#6a3d9a", "o"),
         "B1SL": ("Sintetico con area e mix di Fabriano", "#33a02c", "s"),
         "B4sub": ("Fabriano, utenti reali campionati", "#e31a1c", "^")}
fig, axs = plt.subplots(1, 3, figsize=(16, 4.6), sharey=True)
for ax, g in zip(axs, (0.1, 0.5, 0.9)):
    for b, (lab, col, mk) in serie.items():
        d = G[(G.bench == b) & (G.gamma.round(2) == g)].sort_values("N")
        if d.empty:
            continue
        ax.errorbar(d.N, d.gap_tot_mean, yerr=d.gap_tot_ci95, color=col, marker=mk,
                    capsize=3, lw=1.5, label=lab)
    f = G[(G.bench == "B4") & (G.gamma.round(2) == g)]
    if not f.empty:
        ax.scatter(f.N, f.gap_tot_mean, color="k", marker="*", s=130, zorder=5,
                   label="Fabriano, tutti gli utenti (N=3932)")
    ax.set_xscale("log"); ax.set_title(f"γ = {g}")
    ax.set_xlabel("N utenti"); ax.grid(alpha=.3)
axs[0].set_ylabel("Gap F_tot Greedy–CW (%)"); axs[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(DIR / "fig_gap_vs_N.png", dpi=300)
print("salvato", DIR / "fig_gap_vs_N.png")