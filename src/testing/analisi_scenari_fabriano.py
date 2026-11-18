"""
Fase 3.1 (Post-Processing) — Analisi Multi-Seed degli Scenari su Grafo Fisso di Fabriano (N = 3932).

Legge i CSV a 18 colonne da src/risultati_fabriano/ ed estrae per ciascuno scenario,
ciascuna politica gamma in {0.1, 0.5, 0.9}, ciascun rifiuto r e ciascun algoritmo (Greedy vs Clarke-Wright)
la soluzione ottima scelta dall'algoritmo (X_r*, V_r*, V_r*X_r*, km/sett, ore/sett, sat_fisica, sat_tempo,
F_costo_fisso, F_viaggio, F_lavoro, F_costi, F_insoddis), aggregando media e deviazione standard sui seed.

Esporta:
  - src/risultati_fabriano/riepilogo_ottimi_per_seed.csv
  - src/risultati_fabriano/riepilogo_aggregato_scenari.csv
  - src/risultati_fabriano/report_scenari_fabriano.md

Uso (dalla cartella src/):
  python testing/analisi_scenari_fabriano.py
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def _std(vals: list[float]) -> float:
    if not vals:
        return 0.0
    m = _mean(vals)
    return math.sqrt(sum((x - m) ** 2 for x in vals) / len(vals))

TESTING_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTING_DIR.parent
IN_DIR = SRC_DIR / "risultati_fabriano"

GAMMA_LIST = [0.1, 0.5, 0.9]
GAMMA_LABELS = {0.1: "Pro-Azienda", 0.5: "Bilanciata", 0.9: "Pro-Cittadino"}
WASTE_ORDER = ["organico", "carta", "plastica", "vetro", "indifferenziata"]
SCENARIO_ORDER = [
    "reale_osm",
    "omogeneo_leggero",
    "bimodale_70_30",
    "condomini_pesante",
    "centro_pesante",
    "periferia_pesante",
]
CD_EUR_KM = 2.0
CM_EUR_MIN = 0.25


def load_all_csvs() -> list[dict]:
    files = sorted(IN_DIR.glob("FAB_N*.csv"))
    if not files:
        raise SystemExit(f"Nessun file FAB_N*.csv trovato in '{IN_DIR}'. Esegui prima batch_scenari_fabriano.py.")
    rows: list[dict] = []
    for fp in files:
        with fp.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                f_fisso = float(r["F_costo_fisso"])
                f_viaggio = float(r["F_viaggio"])
                f_lavoro = float(r["F_lavoro"])
                f_costi = f_fisso + f_viaggio + f_lavoro
                f_ins = float(r["F_insoddis"])
                rows.append({
                    "bench": r["bench"],
                    "seed": int(r["seed"]),
                    "N": int(r["N"]),
                    "scenario": r["scenario"],
                    "modo": r["modo"],
                    "rifiuto": r["rifiuto"],
                    "X_r": float(r["X_r"]),
                    "algoritmo": r["algoritmo"],
                    "n_vehicles": int(r["n_vehicles"]),
                    "n_utenti_serviti": int(r["n_utenti_serviti"]),
                    "F_insoddis": f_ins,
                    "F_costo_fisso": f_fisso,
                    "F_viaggio": f_viaggio,
                    "F_lavoro": f_lavoro,
                    "F_costi": f_costi,
                    "km_sett": f_viaggio / CD_EUR_KM,
                    "ore_sett": (f_lavoro / CM_EUR_MIN) / 60.0,
                    "sat_fisica": float(r["sat_fisica"]),
                    "sat_tempo": float(r["sat_tempo"]),
                    "k_scala": float(r["k_scala"]),
                    "algo_time_sec": float(r["algo_time_sec"]),
                })
    return rows


def select_optima(rows: list[dict]) -> list[dict]:
    """Seleziona per ogni (scenario, seed, gamma, rifiuto, algoritmo) la frequenza ottima X_r*."""
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["scenario"], r["modo"], r["seed"], r["rifiuto"], r["algoritmo"])
        grouped[key].append(r)

    opt_rows: list[dict] = []
    for (scenario, modo, seed, rifiuto, algoritmo), candidates in grouped.items():
        k_scala = candidates[0]["k_scala"]
        for gamma in GAMMA_LIST:
            best = min(
                candidates,
                key=lambda c: (
                    gamma * (c["F_insoddis"] * k_scala) + (1.0 - gamma) * c["F_costi"],
                    c["X_r"],
                ),
            )
            term_ins = gamma * (best["F_insoddis"] * k_scala)
            term_cost = (1.0 - gamma) * best["F_costi"]
            opt_rows.append({
                "scenario": scenario,
                "modo": modo,
                "seed": seed,
                "gamma": gamma,
                "politica": GAMMA_LABELS[gamma],
                "rifiuto": rifiuto,
                "algoritmo": algoritmo,
                "X_r_star": best["X_r"],
                "V_r_star": best["n_vehicles"],
                "V_X_star": best["n_vehicles"] * best["X_r"],
                "km_sett": best["km_sett"],
                "ore_sett": best["ore_sett"],
                "sat_fisica": best["sat_fisica"],
                "sat_tempo": best["sat_tempo"],
                "F_costo_fisso": best["F_costo_fisso"],
                "F_viaggio": best["F_viaggio"],
                "F_lavoro": best["F_lavoro"],
                "F_costi": best["F_costi"],
                "F_insoddis": best["F_insoddis"],
                "k_scala": k_scala,
                "term_ins_pesato": term_ins,
                "term_cost_pesato": term_cost,
                "F_total": term_ins + term_cost,
                "algo_time_sec": best["algo_time_sec"],
            })
    return opt_rows


def aggregate_and_export(opt_rows: list[dict]) -> None:
    # 1. Salva CSV degli ottimi per singolo seed
    per_seed_path = IN_DIR / "riepilogo_ottimi_per_seed.csv"
    if opt_rows:
        with per_seed_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(opt_rows[0].keys()))
            writer.writeheader()
            writer.writerows(opt_rows)

    # 2. Aggrega a livello Citta' (somma sui 5 rifiuti per ciascun seed) per confronto globale tra scenari
    city_by_seed: dict[tuple, dict] = {}
    for r in opt_rows:
        key = (r["scenario"], r["modo"], r["seed"], r["gamma"], r["algoritmo"])
        if key not in city_by_seed:
            city_by_seed[key] = {
                "X_list": [],
                "V_sum": 0.0,
                "VX_sum": 0.0,
                "km_sum": 0.0,
                "ore_sum": 0.0,
                "sat_fis_list": [],
                "sat_tem_list": [],
                "F_fisso": 0.0,
                "F_viaggio": 0.0,
                "F_lavoro": 0.0,
                "F_costi": 0.0,
                "F_insoddis": 0.0,
                "k_scala": r["k_scala"],
                "term_ins_pesato": 0.0,
                "term_cost_pesato": 0.0,
                "F_total": 0.0,
            }
        acc = city_by_seed[key]
        acc["X_list"].append(r["X_r_star"])
        acc["V_sum"] += r["V_r_star"]
        acc["VX_sum"] += r["V_X_star"]
        acc["km_sum"] += r["km_sett"]
        acc["ore_sum"] += r["ore_sett"]
        acc["sat_fis_list"].append(r["sat_fisica"])
        acc["sat_tem_list"].append(r["sat_tempo"])
        acc["F_fisso"] += r["F_costo_fisso"]
        acc["F_viaggio"] += r["F_viaggio"]
        acc["F_lavoro"] += r["F_lavoro"]
        acc["F_costi"] += r["F_costi"]
        acc["F_insoddis"] += r["F_insoddis"]
        acc["term_ins_pesato"] += r["term_ins_pesato"]
        acc["term_cost_pesato"] += r["term_cost_pesato"]
        acc["F_total"] += r["F_total"]

    # Raggruppa per (scenario, gamma, algoritmo) sui seed
    scen_groups: dict[tuple, list[dict]] = defaultdict(list)
    for (scenario, modo, seed, gamma, algoritmo), vals in city_by_seed.items():
        scen_groups[(scenario, gamma, algoritmo)].append({
            "seed": seed,
            "X_mean": float(_mean(vals["X_list"])),
            "V_sum": vals["V_sum"],
            "VX_sum": vals["VX_sum"],
            "km_sum": vals["km_sum"],
            "ore_sum": vals["ore_sum"],
            "sat_fis_mean": float(_mean(vals["sat_fis_list"])),
            "sat_tem_mean": float(_mean(vals["sat_tem_list"])),
            "F_fisso": vals["F_fisso"],
            "F_viaggio": vals["F_viaggio"],
            "F_lavoro": vals["F_lavoro"],
            "F_costi": vals["F_costi"],
            "F_insoddis": vals["F_insoddis"],
            "k_scala": vals["k_scala"],
            "term_ins_pesato": vals["term_ins_pesato"],
            "term_cost_pesato": vals["term_cost_pesato"],
            "F_total": vals["F_total"],
        })

    agg_rows: list[dict] = []
    md_lines = [
        "# Report Campagna Sperimentale su Grafo Fisso di Fabriano ($N = 3932$)",
        "",
        "Valori aggregati a livello città (somma dei 5 rifiuti per costi, km, ore, attivazioni $V_r^* X_r^*$ e insoddisfazione; media per $X_r^*$ e saturazioni) mediati sui seed dello scenario.",
        "",
    ]

    for gamma in GAMMA_LIST:
        md_lines.append(f"## Politica $\\gamma = {gamma:.1f}$ ({GAMMA_LABELS[gamma]})")
        md_lines.append("")
        md_lines.append(
            "| Scenario | N.Seed | Algoritmo | $\\bar{X}_r^*$ | $\\sum V_r^* X_r^*$ | km/sett | ore/sett | Sat.Fis% | Sat.Tem% | $F_{\\text{fisso}}$ (€) | $F_{\\text{viaggio}}$ (€) | $F_{\\text{lavoro}}$ (€) | $F_{\\text{costi}}$ (€) | $F_{\\text{insoddis}}$ | $\\gamma k F_{\\text{ins}}$ | $(1-\\gamma) F_{\\text{costi}}$ | $F_{\\text{total}}$ | $\\Delta F_{\\text{costi}}$ CW | $\\Delta$ km CW |"
        )
        md_lines.append(
            "| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        )

        for sc in SCENARIO_ORDER:
            g_list = scen_groups.get((sc, gamma, "greedy"), [])
            cw_list = scen_groups.get((sc, gamma, "clarke_wright"), [])
            if not g_list or not cw_list:
                continue

            g_cost_mean = float(_mean([x["F_costi"] for x in g_list]))
            g_km_mean = float(_mean([x["km_sum"] for x in g_list]))

            for algo_key, algo_label, item_list in [
                ("greedy", "Greedy", g_list),
                ("clarke_wright", "Clarke-Wright", cw_list),
            ]:
                n_s = len(item_list)
                xm = float(_mean([x["X_mean"] for x in item_list]))
                vxm = float(_mean([x["VX_sum"] for x in item_list]))
                kmm = float(_mean([x["km_sum"] for x in item_list]))
                orem = float(_mean([x["ore_sum"] for x in item_list]))
                sfm = float(_mean([x["sat_fis_mean"] for x in item_list]))
                stm = float(_mean([x["sat_tem_mean"] for x in item_list]))
                ffm = float(_mean([x["F_fisso"] for x in item_list]))
                fvm = float(_mean([x["F_viaggio"] for x in item_list]))
                flm = float(_mean([x["F_lavoro"] for x in item_list]))
                fcm = float(_mean([x["F_costi"] for x in item_list]))
                fcs = float(_std([x["F_costi"] for x in item_list]))
                fim = float(_mean([x["F_insoddis"] for x in item_list]))
                km_scala = float(_mean([x["k_scala"] for x in item_list]))
                tipm = float(_mean([x["term_ins_pesato"] for x in item_list]))
                tcpm = float(_mean([x["term_cost_pesato"] for x in item_list]))
                ftm = float(_mean([x["F_total"] for x in item_list]))

                d_cost_pct = ((fcm - g_cost_mean) / g_cost_mean * 100.0) if (algo_key == "clarke_wright" and g_cost_mean > 0) else 0.0
                d_km_pct = ((kmm - g_km_mean) / g_km_mean * 100.0) if (algo_key == "clarke_wright" and g_km_mean > 0) else 0.0

                agg_rows.append({
                    "scenario": sc,
                    "gamma": gamma,
                    "politica": GAMMA_LABELS[gamma],
                    "n_seeds": n_s,
                    "algoritmo": algo_label,
                    "X_star_mean": round(xm, 3),
                    "VX_star_sum_mean": round(vxm, 2),
                    "km_sett_mean": round(kmm, 2),
                    "ore_sett_mean": round(orem, 2),
                    "sat_fisica_mean": round(sfm, 2),
                    "sat_tempo_mean": round(stm, 2),
                    "F_fisso_mean": round(ffm, 2),
                    "F_viaggio_mean": round(fvm, 2),
                    "F_lavoro_mean": round(flm, 2),
                    "F_costi_mean": round(fcm, 2),
                    "F_costi_std": round(fcs, 2),
                    "F_insoddis_mean": round(fim, 2),
                    "k_scala_mean": round(km_scala, 6),
                    "term_ins_pesato_mean": round(tipm, 2),
                    "term_cost_pesato_mean": round(tcpm, 2),
                    "F_total_mean": round(ftm, 2),
                    "delta_costi_cw_pct": round(d_cost_pct, 2),
                    "delta_km_cw_pct": round(d_km_pct, 2),
                })

                d_cost_str = f"{d_cost_pct:+.1f}%" if algo_key == "clarke_wright" else "-"
                d_km_str = f"{d_km_pct:+.1f}%" if algo_key == "clarke_wright" else "-"
                md_lines.append(
                    f"| {sc} | {n_s} | {algo_label} | {xm:.2f} | {vxm:.1f} | {kmm:.1f} | {orem:.1f} | {sfm:.1f}% | {stm:.1f}% | {ffm:.0f} | {fvm:.0f} | {flm:.0f} | {fcm:.0f} ± {fcs:.0f} | {fim:.0f} | {tipm:.0f} | {tcpm:.0f} | {ftm:.0f} | {d_cost_str} | {d_km_str} |"
                )
        md_lines.append("")

    agg_path = IN_DIR / "riepilogo_aggregato_scenari.csv"
    if agg_rows:
        with agg_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(agg_rows[0].keys()))
            writer.writeheader()
            writer.writerows(agg_rows)

    md_path = IN_DIR / "report_scenari_fabriano.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Esportati:\n  - {per_seed_path}\n  - {agg_path}\n  - {md_path}")
    print("\n" + "\n".join(md_lines))


def main() -> None:
    rows = load_all_csvs()
    opt_rows = select_optima(rows)
    aggregate_and_export(opt_rows)


if __name__ == "__main__":
    main()
