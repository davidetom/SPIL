"""
analisi_incroci.py
──────────────────
Estrae dai CSV di risultati il gap prestazionale F_total tra Clarke-Wright e
Greedy, lo confronta tra benchmark sintetici (B1-VarN) e grafo reale (B4),
e calcola il grado medio dei grafi per spiegare la differenza strutturale.

Eseguire dalla cartella Euristiche:
    python analisi_incroci.py

Output: stampa a console + file analisi_incroci.md
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

# ─────────────────────────────────────────────────────────────────────────────
# 1. CARICAMENTO CSV
# ─────────────────────────────────────────────────────────────────────────────
CSV_DIR = Path("risultati_csv")

def load_csvs(pattern: str) -> pd.DataFrame:
    files = sorted(CSV_DIR.glob(pattern))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

# B1 – Variazione N (sintetico, rete condivisa)
b1 = load_csvs("risultati_*u_varN_Nmax1000_Nact*_seed42_gamma0.50.csv")

# B2 – Tipologia urbanistica (sintetico)
b2 = load_csvs("risultati_400u_tipo_*_gamma0.50.csv")

# B3 – Distribuzione spaziale (sintetico)
b3 = load_csvs("risultati_400u_distrib_*_gamma0.50.csv")

# B4 – Mappa reale Fabriano
b4 = load_csvs("risultati_3932u_mappa_reale_gamma0.50.csv")

# Standard (seed multipli, per robustezza)
std = load_csvs("risultati_200u_std_seed*_gamma0.50.csv")

# ─────────────────────────────────────────────────────────────────────────────
# 2. CALCOLO GAP GREEDY vs CW
# ─────────────────────────────────────────────────────────────────────────────
def calcola_gap(df: pd.DataFrame, group_col: str = None) -> pd.DataFrame:
    """
    Per ogni (group_col, rifiuto, X_r): F_total_greedy - F_total_cw.
    Gap > 0  → CW migliore (risparmia costo totale).
    Gap in % rispetto al Greedy.
    """
    if df.empty:
        return pd.DataFrame()

    cols = ["rifiuto", "X_r", "algoritmo", "F_total"]
    if group_col and group_col in df.columns:
        cols = [group_col] + cols

    sub = df[cols].copy()
    pivot = sub.pivot_table(
        index=[c for c in cols if c not in ("algoritmo", "F_total")],
        columns="algoritmo",
        values="F_total",
    ).reset_index()

    if "greedy" not in pivot.columns or "clarke_wright" not in pivot.columns:
        return pd.DataFrame()

    pivot["gap_abs"]  = pivot["greedy"] - pivot["clarke_wright"]
    pivot["gap_pct"]  = 100 * pivot["gap_abs"] / pivot["greedy"]
    return pivot


# ─────────────────────────────────────────────────────────────────────────────
# 3. B4 vs B1  —  Gap Fabriano vs plateau scalabilità
# ─────────────────────────────────────────────────────────────────────────────
def sezione_b4_vs_b1():
    lines = []
    lines.append("## B4 (Fabriano) vs B1 (Scalabilità)")
    lines.append("")

    # Estrai n_utenti_serviti dal B1 come proxy di N
    b1_ext = b1.copy()
    # Il nome file contiene Nact → estraiamo dal campo n_utenti_serviti
    gap_b1 = calcola_gap(b1_ext, group_col="n_utenti_serviti")

    if gap_b1.empty:
        lines.append("  [DATI MANCANTI] CSV B1 non trovati o struttura diversa.")
        return "\n".join(lines)

    # Media gap % per N
    gap_b1_agg = (
        gap_b1.groupby("n_utenti_serviti")["gap_pct"]
        .mean()
        .reset_index()
        .rename(columns={"n_utenti_serviti": "N", "gap_pct": "gap_pct_medio"})
        .sort_values("N")
    )

    # Gap Fabriano
    gap_b4 = calcola_gap(b4)
    if gap_b4.empty:
        lines.append("  [DATI MANCANTI] CSV B4 non trovati.")
        return "\n".join(lines)

    gap_b4_medio = gap_b4["gap_pct"].mean()
    n_fabriano   = b4["n_utenti_serviti"].iloc[0] if not b4.empty else "?"

    lines.append(f"Gap medio CW vs Greedy (F_total, γ=0.5):\n")
    lines.append(f"| N utenti (sintetico) | Gap % medio |")
    lines.append(f"|----------------------|-------------|")
    for _, row in gap_b1_agg.iterrows():
        lines.append(f"| {int(row['N']):20d} | {row['gap_pct_medio']:10.2f}% |")
    lines.append(f"|")
    lines.append(f"| **Fabriano (N≈{n_fabriano})** | **{gap_b4_medio:.2f}%** |")
    lines.append("")

    # Interpretazione
    max_syn = gap_b1_agg["gap_pct_medio"].max()
    lines.append(
        f"**Osservazione:** Il gap sintetico raggiunge un picco di "
        f"**{max_syn:.1f}%** e tende a stabilizzarsi (plateau) all'aumentare di N. "
        f"Sul grafo reale di Fabriano il gap crolla a **{gap_b4_medio:.1f}%**, "
        f"ben al di sotto del plateau sintetico. Questo suggerisce che la topologia "
        f"reale — non il solo numero di utenti — limita il vantaggio di CW."
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 4. B4 vs B2  —  Distribuzione tipologica Fabriano
# ─────────────────────────────────────────────────────────────────────────────
def sezione_b4_vs_b2():
    lines = []
    lines.append("## B4 (Fabriano) vs B2 (Tipologia Urbanistica)")
    lines.append("")

    # Carica utenti.json per distribuzione reale
    import json
    utenti_path = Path("Generazione_grafo_Fabriano/dati_reali/utenti.json")
    try:
        with open(utenti_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        utenti = raw["utenti"] if isinstance(raw, dict) and "utenti" in raw else raw
        types = [u.get("tipologia", "?") for u in utenti]
        from collections import Counter
        counts = Counter(types)
        total  = sum(counts.values())
        lines.append("**Distribuzione tipologica reale di Fabriano:**\n")
        lines.append("| Tipo utenza | N | % |")
        lines.append("|-------------|---|---|")
        for t, c in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {t} | {c} | {100*c/total:.1f}% |")
        lines.append("")
    except Exception as e:
        lines.append(f"  [INFO] utenti.json non leggibile: {e}")

    # Gap per scenario B2
    if not b2.empty and "algoritmo" in b2.columns:
        # ricava il tag scenario dal nome file originale
        b2_files = sorted(CSV_DIR.glob("risultati_400u_tipo_*_gamma0.50.csv"))
        frames = []
        for f in b2_files:
            scenario = f.stem.replace("risultati_400u_tipo_", "").replace("_gamma0.50", "")
            tmp = pd.read_csv(f)
            tmp["scenario"] = scenario
            frames.append(tmp)
        b2_tagged = pd.concat(frames, ignore_index=True)
        gap_b2 = calcola_gap(b2_tagged, group_col="scenario")
        if not gap_b2.empty:
            gap_b2_agg = gap_b2.groupby("scenario")["gap_pct"].mean().reset_index()
            gap_b4 = calcola_gap(b4)
            gap_b4_medio = gap_b4["gap_pct"].mean() if not gap_b4.empty else float("nan")

            lines.append("**Gap CW vs Greedy per scenario tipologico sintetico:**\n")
            lines.append("| Scenario | Gap % medio |")
            lines.append("|----------|-------------|")
            for _, row in gap_b2_agg.sort_values("gap_pct").iterrows():
                lines.append(f"| {row['scenario']} | {row['gap_pct']:.2f}% |")
            lines.append(f"| **Fabriano (reale)** | **{gap_b4_medio:.2f}%** |")
            lines.append("")
            lines.append(
                "**Osservazione:** confrontando il gap reale con quello degli scenari "
                "sintetici è possibile identificare a quale scenario tipologico "
                "si avvicina maggiormente il comportamento del modello su Fabriano."
            )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 5. B4 vs B3  —  Distribuzione spaziale
# ─────────────────────────────────────────────────────────────────────────────
def sezione_b4_vs_b3():
    lines = []
    lines.append("## B4 (Fabriano) vs B3 (Distribuzione Spaziale)")
    lines.append("")

    if b3.empty:
        lines.append("  [DATI MANCANTI] CSV B3 non trovati.")
        return "\n".join(lines)

    b3_files = sorted(CSV_DIR.glob("risultati_400u_distrib_*_gamma0.50.csv"))
    frames = []
    for f in b3_files:
        mode = f.stem.replace("risultati_400u_distrib_", "").replace("_gamma0.50", "")
        tmp  = pd.read_csv(f)
        tmp["distrib"] = mode
        frames.append(tmp)
    b3_tagged = pd.concat(frames, ignore_index=True)
    gap_b3 = calcola_gap(b3_tagged, group_col="distrib")

    gap_b4 = calcola_gap(b4)
    gap_b4_medio = gap_b4["gap_pct"].mean() if not gap_b4.empty else float("nan")
    gap_b4_viaggio = b4[b4["algoritmo"]=="greedy"]["F_viaggio"].mean() if not b4.empty else float("nan")

    lines.append("**Gap CW vs Greedy per distribuzione spaziale sintetica:**\n")
    lines.append("| Distribuzione | Gap % medio |")
    lines.append("|---------------|-------------|")
    if not gap_b3.empty:
        for _, row in gap_b3.groupby("distrib")["gap_pct"].mean().reset_index().iterrows():
            lines.append(f"| {row['distrib']} | {row['gap_pct']:.2f}% |")
    lines.append(f"| **Fabriano (reale)** | **{gap_b4_medio:.2f}%** |")
    lines.append("")
    lines.append(
        "**Osservazione:** se il gap di Fabriano si avvicina alla distribuzione "
        "uniforme, la rete reale ha un'utenza spazialmente dispersa. "
        "Se si avvicina al cluster, è più concentrata. "
        "Questo incrocio permette di classificare Fabriano senza guardare la mappa."
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 6. SPIEGAZIONE TOPOLOGICA  —  Grado medio + gap
# ─────────────────────────────────────────────────────────────────────────────
def sezione_topologia():
    lines = []
    lines.append("## Spiegazione Topologica: grado medio e gap algoritmi")
    lines.append("")

    # Grado medio reale (già calcolato)
    archi = pd.read_csv("Generazione_grafo_Fabriano/dati_reali/archi_stradali.csv")
    nodi  = pd.read_csv("Generazione_grafo_Fabriano/dati_reali/nodi_stradali.csv")
    n_real = len(nodi)
    pairs  = set(zip(archi["u"], archi["v"]))
    rev    = {(v, u) for u, v in pairs}
    e_undir = len(pairs & rev) // 2 + len(pairs - rev)
    # più preciso: se >50% bidirezionale dividi per 2
    n_sym = len(pairs & rev)
    if n_sym / len(pairs) > 0.5:
        e_undir = len(pairs) // 2
    degree_real = 2 * e_undir / n_real

    # Grado medio sintetico
    from Generazione_Dati import get_or_create_base_graph
    bg = get_or_create_base_graph(n_max=500, seed=42, r_factor=1.2)
    e_syn  = len(bg["edges_base"])
    n_syn  = 501
    degree_syn = 2 * e_syn / n_syn

    # Gap
    gap_b4 = calcola_gap(b4)
    gap_b4_medio = gap_b4["gap_pct"].mean() if not gap_b4.empty else float("nan")
    gap_b1 = calcola_gap(b1)
    gap_syn_medio = gap_b1["gap_pct"].mean() if not gap_b1.empty else float("nan")

    lines.append("| Grafo | Nodi | Archi (non-dir.) | Grado medio | Gap CW-Greedy % |")
    lines.append("|-------|------|-----------------|-------------|-----------------|")
    lines.append(f"| Sintetico (N=500, r=1.2) | {n_syn} | {e_syn} | {degree_syn:.2f} | {gap_syn_medio:.2f}% |")
    lines.append(f"| Reale Fabriano (OSM)     | {n_real} | {e_undir} | {degree_real:.2f} | {gap_b4_medio:.2f}% |")
    lines.append("")
    lines.append(
        f"**Interpretazione:** con grado medio **{degree_syn:.2f}** il grafo sintetico "
        f"offre a Clarke-Wright molte alternative di fusione delle rotte, producendo "
        f"un gap di **{gap_syn_medio:.1f}%** rispetto al Greedy. "
        f"Il grafo reale di Fabriano ha grado medio **{degree_real:.2f}** "
        f"(−{degree_syn - degree_real:.2f} nodi/incrocio): la minore connettività "
        f"riduce le opzioni di fusione di CW, abbassando il vantaggio a "
        f"**{gap_b4_medio:.1f}%**. La correlazione grado↔gap supporta l'ipotesi "
        f"che sia la **topologia**, non la dimensione o la distribuzione spaziale, "
        f"la causa principale del crollo del gap su reti reali."
    )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 7. ASSEMBLAGGIO E OUTPUT
# ─────────────────────────────────────────────────────────────────────────────
sections = [
    "# Analisi Incroci: Sintetico vs Reale (Fabriano)\n",
    sezione_topologia(),
    "",
    sezione_b4_vs_b1(),
    "",
    sezione_b4_vs_b2(),
    "",
    sezione_b4_vs_b3(),
]

output = "\n".join(sections)
print(output)

out_dir = Path("Analisi aggiuntive")
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "Studio sul gap prestazionale.md"
out_path.write_text(output, encoding="utf-8")
print(f"\n→ Salvato in: {out_path.resolve()}")
