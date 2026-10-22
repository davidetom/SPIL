# fig_t1.py
# Frontiere normalizzate per sei istanze (T1): costo logistico e disservizio rispetto alla
# soluzione a gamma=0.05 di Greedy (tutte le frequenze a 0.5). Media sui seed dei valori normalizzati.
# Input: analisi_seed/metriche_istanza.csv   Output: analisi_seed/fig_t1_frontiere.png
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent   # cartella Euristiche/
OUT = ROOT / "analisi_seed"
COL = {"greedy": "#2171b5", "clarke_wright": "#d95f0e"}
NAME = {"greedy": "Greedy", "clarke_wright": "Clarke-Wright"}
LS = {"greedy": "--", "clarke_wright": "-"}
CASI = [("Fabriano, tutti gli utenti (N=3932)", ("B4", 3932, "reale", "reale")),
        ("Fabriano, sottocampioni (N=1000)", ("B4sub", 1000, "reale", "reale")),
        ("B1 residenziale (N=1000)", ("B1", 1000, "residenziale", "uniform")),
        ("B5 grafo standard (N=200)", ("B5", 200, "residenziale", "std")),
        ("B2 villette (N=400)", ("B2", 400, "villette", "uniform")),
        ("B2 grandi condomini (N=400)", ("B2", 400, "grandi_condomini", "uniform"))]
EVID = (0.1, 0.5, 0.9)

M = pd.read_csv(OUT / "metriche_istanza.csv").assign(gamma=lambda d: d.gamma.round(2))
fig, axs = plt.subplots(2, 3, figsize=(15, 8.6))
for ax, (titolo, (b, N, sc, mo)) in zip(axs.flat, CASI):
    d = M[(M.bench == b) & (M.N == N) & (M.scenario == sc) & (M.modo == mo)]
    ref = (d[(d.algoritmo == "greedy") & (d.gamma == 0.05)]
           .set_index("seed")[["F_costi", "F_ins"]])
    d = d.join(ref, on="seed", rsuffix="_ref")
    d["c"] = d.F_costi / d.F_costi_ref
    d["i"] = d.F_ins / d.F_ins_ref
    for algo in ("greedy", "clarke_wright"):
        s = d[d.algoritmo == algo].groupby("gamma")[["c", "i"]].mean().reset_index()
        ax.plot(s.c, s.i, LS[algo], color=COL[algo], lw=2, marker="o", ms=4.5,
                mec="white", mew=0.8, label=NAME[algo], zorder=3)
        if algo == "clarke_wright":
            # politiche che danno lo stesso punto -> un'unica etichetta
            e = s[s.gamma.isin(EVID)].round({"c": 4, "i": 4})
            for (c, i), grp in e.groupby(["c", "i"], sort=False):
                lab = "γ=" + ", ".join(f"{g:g}" for g in grp.gamma)
                sotto = grp.gamma.iloc[0] == 0.5 and len(grp) == 1   # 0.5 sotto la curva, 0.9 sopra
                ax.annotate(lab, (c, i), xytext=(-6, -14) if sotto else (6, 6),
                            textcoords="offset points", ha="right" if sotto else "left",
                            fontsize=8.5, color="#333333")
    ax.set_title(titolo, fontsize=10.5)
    ax.grid(alpha=0.25, lw=0.6)
    ax.set_ylim(bottom=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
for ax in axs[1]:
    ax.set_xlabel("costo logistico / costo Greedy a γ=0.05")
for ax in axs[:, 0]:
    ax.set_ylabel("disservizio / disservizio a γ=0.05")
axs[0, 0].legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "fig_t1_frontiere.png", dpi=300)
print("salvato", OUT / "fig_t1_frontiere.png")