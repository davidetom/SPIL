"""
Fase 2 — Report su singola istanza reale di Fabriano (N=3932) per ricevimento Prof.ssa Adacher.

Esegue Greedy e Clarke-Wright su tutti i 5 rifiuti con la nuova legge sub-lineare Q_ru(X_r)
e griglia X_VALUES = [0.5, 1.0, ..., 4.0] per gamma in {0.1, 0.5, 0.9}.
Stampa ed esporta:
  1. Tabella completa con variabili decisionali ottime (X_r*, V_r*, V_r*X_r*, km, ore, sat_fis, sat_tempo),
     valori grezzi non pesati (F_costo_fisso, F_viaggio, F_lavoro, F_costi, F_insoddis),
     k_scala e termini pesati a gamma = 0.1, 0.5, 0.9.
  2. Grafici bi-criterio non pesati (F_costi, F_insoddis) a 300 DPI per evidenziare
     la dominanza di Pareto tra Greedy (#2171b5) e Clarke-Wright (#d95f0e).
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Risoluzione path rispetto a src/
TESTING_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTING_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from Generazione_Dati import generate_real_data
from Greedy import grid_search as greedy_gs
from ClarkeWright import grid_search as cw_gs
from main import (
    X_VALUES,
    GRAPHML_PATH,
    UTENTI_JSON,
    calcola_worker_ottimali,
    _calcola_fattore_scala,
)

OUTPUT_DIR = TESTING_DIR / "output_fase2"
GAMMA_LIST = [0.1, 0.5, 0.9]
GAMMA_LABELS = {0.1: "Pro-Azienda", 0.5: "Bilanciata", 0.9: "Pro-Cittadino"}
COLOR_GREEDY = "#2171b5"
COLOR_CW = "#d95f0e"


def _extract_metrics(gs_res: dict, X_r: float, cd: float, cm: float, gamma: float, k_scala: float) -> dict:
    """Estrae tutte le metriche grezze, pesate e decisionali per una singola valutazione."""
    # Trova la entry corrispondente a X_r in all_results
    obj = next(item for item in gs_res["all_results"] if abs(item["X_r"] - X_r) < 1e-9)
    n_veh = obj["n_vehicles"]
    f_fisso = obj["F_costo_fisso"]
    f_viaggio = obj["F_viaggio"]
    f_lavoro = obj["F_lavoro"]
    f_costi = f_fisso + f_viaggio + f_lavoro
    f_insoddis = obj["F_insoddis"]
    term_ins = gamma * (f_insoddis * k_scala)
    term_cost = (1.0 - gamma) * f_costi
    f_total = obj["F_total"]

    km_sett = f_viaggio / cd if cd > 0 else 0.0
    ore_sett = (f_lavoro / cm) / 60.0 if cm > 0 else 0.0

    return {
        "X_r": X_r,
        "V_r": n_veh,
        "V_X": n_veh * X_r,
        "km_sett": km_sett,
        "ore_sett": ore_sett,
        "sat_fisica": obj["sat_fisica"],
        "sat_tempo": obj["sat_tempo"],
        "F_costo_fisso": f_fisso,
        "F_viaggio": f_viaggio,
        "F_lavoro": f_lavoro,
        "F_costi": f_costi,
        "F_insoddis": f_insoddis,
        "k_scala": k_scala,
        "term_ins_pesato": term_ins,
        "term_cost_pesato": term_cost,
        "F_total": f_total,
    }


def run_single_instance(seed: int = 42) -> tuple[dict, float, list[dict], list[dict]]:
    """Esegue Greedy e CW su Fabriano reale per gamma in {0.1, 0.5, 0.9}."""
    graphml_abs = SRC_DIR / GRAPHML_PATH
    utenti_abs = SRC_DIR / UTENTI_JSON

    print(f"[1/4] Caricamento istanza reale Fabriano (seed={seed})...")
    t0 = time.perf_counter()
    data = generate_real_data(
        graphml_path=str(graphml_abs),
        utenti_json_path=str(utenti_abs),
        user_scenario=None,
        seed=seed,
    )
    print(f"      Utenti: N={data['n_users']} | Rifiuti: {data['waste_types']} ({time.perf_counter() - t0:.2f} s)")

    waste_types = data["waste_types"]
    n_workers = calcola_worker_ottimali(data["n_users"])

    print("[2/4] Calcolo k_scala sull'istanza...")
    k_scala = _calcola_fattore_scala(data, waste_types)

    opt_rows: list[dict] = []
    grid_rows: list[dict] = []

    print("[3/4] Esecuzione Grid Search per gamma in {0.1, 0.5, 0.9}...")
    for gamma in GAMMA_LIST:
        for r in waste_types:
            t_g = time.perf_counter()
            gs_g = greedy_gs(data, r, X_VALUES, max_workers=n_workers, gamma=gamma, k_scala=k_scala)
            el_g = time.perf_counter() - t_g

            t_cw = time.perf_counter()
            gs_cw = cw_gs(data, r, X_VALUES, max_workers=n_workers, gamma=gamma, k_scala=k_scala)
            el_cw = time.perf_counter() - t_cw

            for algo_name, gs_res, el in [("Greedy", gs_g, el_g), ("Clarke-Wright", gs_cw, el_cw)]:
                best_x = gs_res["best_X_r"]
                m_opt = _extract_metrics(gs_res, best_x, data["cd"], data["cm"], gamma, k_scala)
                opt_rows.append({
                    "gamma": gamma,
                    "politica": GAMMA_LABELS[gamma],
                    "rifiuto": r,
                    "algoritmo": algo_name,
                    "tempo_sec": el,
                    **m_opt,
                })

                # Salva la griglia completa solo una volta (es. per gamma=0.5) per il grafico Pareto
                if abs(gamma - 0.5) < 1e-9:
                    for item in gs_res["all_results"]:
                        m_x = _extract_metrics(gs_res, item["X_r"], data["cd"], data["cm"], gamma, k_scala)
                        grid_rows.append({
                            "rifiuto": r,
                            "algoritmo": algo_name,
                            **m_x,
                        })

    return data, k_scala, opt_rows, grid_rows


def print_and_save_tables(data: dict, k_scala: float, opt_rows: list[dict], grid_rows: list[dict]) -> None:
    """Stampa la tabella trasparente a console ed esporta CSV + report Markdown."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Export CSV ottimi e griglia
    csv_opt = OUTPUT_DIR / "singola_istanza_ottimi.csv"
    with open(csv_opt, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(opt_rows[0].keys()))
        writer.writeheader()
        writer.writerows(opt_rows)

    csv_grid = OUTPUT_DIR / "singola_istanza_griglia_X.csv"
    with open(csv_grid, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(grid_rows[0].keys()))
        writer.writeheader()
        writer.writerows(grid_rows)

    # 2. Stampa a console + costruzione Markdown
    md_lines = [
        "# Report Singola Istanza Reale — Fabriano ($N = 3932$, seed = 42)",
        "",
        f"- **Legge di carico:** $Q_{{ru}}(X_r) = W_{{r t_u}} \\cdot \\max(0.10,\\, 0.95 - 0.25\\ln(X_r + 0.5))$",
        f"- **Griglia frequenze:** $\\mathcal{{X}} = {X_VALUES}$",
        f"- **Fattore di bilanciamento:** $k_{{\\text{{scala}}}} = {k_scala:.4f}$",
        "",
    ]

    print("\n" + "=" * 128)
    print(f"  REPORT SINGOLA ISTANZA FABRIANO (N={data['n_users']}) | k_scala = {k_scala:.4f}")
    print("=" * 128)

    for gamma in GAMMA_LIST:
        sub = [row for row in opt_rows if abs(row["gamma"] - gamma) < 1e-9]
        hdr = f"\n  >>> POLITICA gamma = {gamma:.1f} ({GAMMA_LABELS[gamma]})"
        print(hdr)
        print(
            f"  {'Rifiuto':<14} {'Algo':<13} | {'X_r*':>4} {'V_r*':>4} {'V*X':>5} "
            f"{'km/sett':>8} {'ore/s':>6} {'SatF%':>6} {'SatT%':>6} | "
            f"{'F_fisso':>9} {'F_viagg':>8} {'F_lav':>8} {'F_costi':>9} {'F_insod':>9} | "
            f"{'g*k*Ins':>9} {'(1-g)*C':>9} {'F_total':>9}"
        )
        print("  " + "-" * 145)

        md_lines.extend([
            f"## Politica $\\gamma = {gamma:.1f}$ ({GAMMA_LABELS[gamma]})",
            "",
            "| Rifiuto | Algoritmo | $X_r^*$ | $V_r^*$ | $V_r^* X_r^*$ | km/sett | ore/sett | Sat. Fis. | Sat. Tempo | $F_{\\text{fisso}}$ (€) | $F_{\\text{viaggio}}$ (€) | $F_{\\text{lavoro}}$ (€) | $F_{\\text{costi}}$ (€) | $F_{\\text{insoddis}}$ | $\\gamma k F_{\\text{ins}}$ | $(1-\\gamma) F_{\\text{costi}}$ | $F_{\\text{total}}$ |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ])

        for row in sub:
            print(
                f"  {row['rifiuto']:<14} {row['algoritmo']:<13} | "
                f"{row['X_r']:>4.1f} {row['V_r']:>4d} {row['V_X']:>5.1f} "
                f"{row['km_sett']:>8.1f} {row['ore_sett']:>6.1f} {row['sat_fisica']:>5.1f}% {row['sat_tempo']:>5.1f}% | "
                f"{row['F_costo_fisso']:>9.2f} {row['F_viaggio']:>8.2f} {row['F_lavoro']:>8.2f} "
                f"{row['F_costi']:>9.2f} {row['F_insoddis']:>9.1f} | "
                f"{row['term_ins_pesato']:>9.2f} {row['term_cost_pesato']:>9.2f} {row['F_total']:>9.2f}"
            )
            md_lines.append(
                f"| {row['rifiuto']} | {row['algoritmo']} | {row['X_r']:.1f} | {row['V_r']} | {row['V_X']:.1f} | "
                f"{row['km_sett']:.1f} | {row['ore_sett']:.1f} | {row['sat_fisica']:.1f}% | {row['sat_tempo']:.1f}% | "
                f"{row['F_costo_fisso']:.2f} | {row['F_viaggio']:.2f} | {row['F_lavoro']:.2f} | "
                f"{row['F_costi']:.2f} | {row['F_insoddis']:.1f} | "
                f"{row['term_ins_pesato']:.2f} | {row['term_cost_pesato']:.2f} | {row['F_total']:.2f} |"
            )

        # Totali aggregati per algoritmo
        print("  " + "-" * 145)
        for algo_name in ("Greedy", "Clarke-Wright"):
            a_rows = [r for r in sub if r["algoritmo"] == algo_name]
            tot_vx = sum(r["V_X"] for r in a_rows)
            tot_km = sum(r["km_sett"] for r in a_rows)
            tot_ore = sum(r["ore_sett"] for r in a_rows)
            tot_fisso = sum(r["F_costo_fisso"] for r in a_rows)
            tot_viagg = sum(r["F_viaggio"] for r in a_rows)
            tot_lav = sum(r["F_lavoro"] for r in a_rows)
            tot_costi = sum(r["F_costi"] for r in a_rows)
            tot_ins = sum(r["F_insoddis"] for r in a_rows)
            tot_t_ins = sum(r["term_ins_pesato"] for r in a_rows)
            tot_t_cost = sum(r["term_cost_pesato"] for r in a_rows)
            tot_ftot = sum(r["F_total"] for r in a_rows)
            mean_sf = float(np.mean([r["sat_fisica"] for r in a_rows]))
            mean_st = float(np.mean([r["sat_tempo"] for r in a_rows]))

            print(
                f"  {'TOTALE/MEDIA':<14} {algo_name:<13} | "
                f"{'-':>4} {'-':>4} {tot_vx:>5.1f} "
                f"{tot_km:>8.1f} {tot_ore:>6.1f} {mean_sf:>5.1f}% {mean_st:>5.1f}% | "
                f"{tot_fisso:>9.2f} {tot_viagg:>8.2f} {tot_lav:>8.2f} "
                f"{tot_costi:>9.2f} {tot_ins:>9.1f} | "
                f"{tot_t_ins:>9.2f} {tot_t_cost:>9.2f} {tot_ftot:>9.2f}"
            )
            md_lines.append(
                f"| **TOTALE / MEDIA** | **{algo_name}** | - | - | **{tot_vx:.1f}** | "
                f"**{tot_km:.1f}** | **{tot_ore:.1f}** | **{mean_sf:.1f}%** | **{mean_st:.1f}%** | "
                f"**{tot_fisso:.2f}** | **{tot_viagg:.2f}** | **{tot_lav:.2f}** | "
                f"**{tot_costi:.2f}** | **{tot_ins:.1f}** | "
                f"**{tot_t_ins:.2f}** | **{tot_t_cost:.2f}** | **{tot_ftot:.2f}** |"
            )
        md_lines.append("")

    md_path = OUTPUT_DIR / "report_singola_istanza.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print("\n" + "=" * 128)
    print(f"  File esportati in: {OUTPUT_DIR}")


def plot_bicriterion(opt_rows: list[dict], grid_rows: list[dict], waste_types: list[str]) -> None:
    """Genera i grafici bi-criterio non pesati (F_costi, F_insoddis) a 300 DPI."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    gamma_markers = {0.1: ("o", r"$\gamma=0.1$"), 0.5: ("s", r"$\gamma=0.5$"), 0.9: ("D", r"$\gamma=0.9$")}

    # --- Grafico 1: Aggregato totale (somma sui 5 rifiuti) ---
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    for algo, color in [("Greedy", COLOR_GREEDY), ("Clarke-Wright", COLOR_CW)]:
        # Curva parametrica su X_r uniforme (per riferimento della frontiera)
        xs_curve, ys_curve = [], []
        for x_val in X_VALUES:
            sub_x = [r for r in grid_rows if r["algoritmo"] == algo and abs(r["X_r"] - x_val) < 1e-9]
            xs_curve.append(sum(r["F_costi"] for r in sub_x))
            ys_curve.append(sum(r["F_insoddis"] for r in sub_x))
        ax.plot(xs_curve, ys_curve, "--", color=color, alpha=0.45, linewidth=1.3, label=f"{algo} (griglia $X_r$)")
        ax.scatter(xs_curve, ys_curve, color=color, alpha=0.35, s=22)

        # Soluzioni ottime scelte alle 3 politiche gamma
        for gamma, (marker, glabel) in gamma_markers.items():
            sub_g = [r for r in opt_rows if r["algoritmo"] == algo and abs(r["gamma"] - gamma) < 1e-9]
            fc = sum(r["F_costi"] for r in sub_g)
            fi = sum(r["F_insoddis"] for r in sub_g)
            ax.scatter(
                fc, fi,
                color=color, marker=marker, s=95, edgecolors="black", linewidths=0.8, zorder=5,
                label=f"{algo} ({glabel})",
            )

    ax.set_title("Piano Bi-Criterio Non Pesato — Totale 5 Rifiuti (Fabriano $N=3932$)", fontsize=12, fontweight="bold")
    ax.set_xlabel(r"$F_{\mathrm{costi}}$ grezzo settimanale (€)", fontsize=11)
    ax.set_ylabel(r"$F_{\mathrm{insoddis}}$ grezzo (penalità non pesata)", fontsize=11)
    ax.grid(True, linestyle=":", alpha=0.55)
    ax.legend(fontsize=8.5, ncol=2, loc="upper right", frameon=True)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "pareto_singola_istanza_totale.png", dpi=300)
    plt.close(fig)

    # --- Grafico 2: Dettaglio per singolo rifiuto (2x3) ---
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.5))
    axes_flat = axes.flatten()

    for idx, r in enumerate(waste_types):
        ax = axes_flat[idx]
        for algo, color in [("Greedy", COLOR_GREEDY), ("Clarke-Wright", COLOR_CW)]:
            sub_grid = sorted(
                [row for row in grid_rows if row["rifiuto"] == r and row["algoritmo"] == algo],
                key=lambda row: row["X_r"],
            )
            ax.plot(
                [row["F_costi"] for row in sub_grid],
                [row["F_insoddis"] for row in sub_grid],
                "-o", color=color, alpha=0.55, markersize=3.5, linewidth=1.3,
                label=algo if idx == 0 else None,
            )
            for gamma, (marker, glabel) in gamma_markers.items():
                row_opt = next(
                    row for row in opt_rows
                    if row["rifiuto"] == r and row["algoritmo"] == algo and abs(row["gamma"] - gamma) < 1e-9
                )
                ax.scatter(
                    row_opt["F_costi"], row_opt["F_insoddis"],
                    color=color, marker=marker, s=75, edgecolors="black", linewidths=0.7, zorder=5,
                )
                # Annotazione discreta di X_r* per gamma=0.5
                if abs(gamma - 0.5) < 1e-9:
                    dy = 6 if algo == "Greedy" else -12
                    ax.annotate(
                        f"$X^*={row_opt['X_r']:.1f}$",
                        (row_opt["F_costi"], row_opt["F_insoddis"]),
                        textcoords="offset points", xytext=(5, dy),
                        fontsize=7.5, color=color, fontweight="bold",
                    )

        ax.set_title(r.capitalize(), fontsize=11, fontweight="bold")
        ax.set_xlabel(r"$F_{\mathrm{costi}}$ (€)", fontsize=9.5)
        ax.set_ylabel(r"$F_{\mathrm{insoddis}}$", fontsize=9.5)
        ax.grid(True, linestyle=":", alpha=0.55)

    # Pannello 6: legenda esplicativa
    ax_leg = axes_flat[5]
    ax_leg.axis("off")
    handles = [
        plt.Line2D([0], [0], color=COLOR_GREEDY, lw=2, label="Greedy (#2171b5)"),
        plt.Line2D([0], [0], color=COLOR_CW, lw=2, label="Clarke-Wright (#d95f0e)"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor="gray", markeredgecolor="k", markersize=8, label=r"Ottimo $\gamma=0.1$ (Pro-Azienda)"),
        plt.Line2D([0], [0], marker="s", color="w", markerfacecolor="gray", markeredgecolor="k", markersize=8, label=r"Ottimo $\gamma=0.5$ (Bilanciata)"),
        plt.Line2D([0], [0], marker="D", color="w", markerfacecolor="gray", markeredgecolor="k", markersize=8, label=r"Ottimo $\gamma=0.9$ (Pro-Cittadino)"),
    ]
    ax_leg.legend(handles=handles, loc="center", fontsize=10, frameon=True, title="Legenda Bi-Criterio")

    fig.suptitle("Confronto Bi-Criterio Non Pesato per Tipologia di Rifiuto — Fabriano ($N=3932$)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(OUTPUT_DIR / "pareto_singola_istanza_per_rifiuto.png", dpi=300)
    plt.close(fig)
    print(f"[4/4] Grafici salvati a 300 DPI in: {OUTPUT_DIR}")


if __name__ == "__main__":
    data, k_scala, opt_rows, grid_rows = run_single_instance(seed=42)
    print_and_save_tables(data, k_scala, opt_rows, grid_rows)
    plot_bicriterion(opt_rows, grid_rows, data["waste_types"])
