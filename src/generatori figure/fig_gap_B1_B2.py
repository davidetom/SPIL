# fig_gap_B1_B2.py
# Produce: analisi_seed/fig_gap_vs_N_B1.png  (B1: gap vs N, 3 politiche)
#          analisi_seed/fig_gap_B2.png       (B2: gap per scenario, 3 politiche)
# Fonte: analisi_seed/riepilogo_gap.csv (media e IC95 su 30 seed)
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
OUT = ROOT / "analisi_seed"

G = pd.read_csv(OUT / "riepilogo_gap.csv")
G["gamma"] = G["gamma"].round(2)

POL = {0.1: ("Pro-Azienda (γ=0.1)", "#1f78b4", "o"),
       0.5: ("Neutra (γ=0.5)",      "#e31a1c", "s"),
       0.9: ("Pro-Cittadino (γ=0.9)", "#33a02c", "^")}

# ---------------- B1: gap vs N ----------------
fig, ax = plt.subplots(figsize=(7.2, 4.4))
for g, (lab, col, mk) in POL.items():
    d = G[(G.bench == "B1") & (G.gamma == g)].sort_values("N")
    ax.errorbar(d.N, d.gap_tot_mean, yerr=d.gap_tot_ci95, color=col, marker=mk,
                capsize=3, lw=1.6, label=lab)
ax.set_xlabel("N utenti"); ax.set_ylabel("Gap $F_{tot}$ Greedy–CW (%)")
ax.set_xticks([100, 250, 500, 750, 1000]); ax.grid(alpha=.3); ax.legend(fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "fig_gap_vs_N_B1.png", dpi=300); plt.close(fig)

# ---------------- B2: gap per scenario ----------------
ordine = ["residenziale", "suburbano", "misto_periferia", "grandi_condomini", "villette"]
etich  = ["Residenziale", "Suburbano", "Misto\nperiferia", "Grandi\ncondomini", "Villette"]
fig, ax = plt.subplots(figsize=(8.2, 4.4))
w = 0.26
x = np.arange(len(ordine))
for k, (g, (lab, col, mk)) in enumerate(POL.items()):
    m, e = [], []
    for sc in ordine:
        r = G[(G.bench == "B2") & (G.scenario == sc) & (G.gamma == g)]
        m.append(r.gap_tot_mean.iloc[0]); e.append(r.gap_tot_ci95.iloc[0])
    ax.bar(x + (k - 1) * w, m, w, yerr=e, capsize=3, color=col, alpha=.85, label=lab)
ax.set_xticks(x); ax.set_xticklabels(etich)
ax.set_ylabel("Gap $F_{tot}$ Greedy–CW (%)"); ax.grid(axis="y", alpha=.3); ax.legend(fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "fig_gap_B2.png", dpi=300); plt.close(fig)
print("ok")
