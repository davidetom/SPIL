"""
Test preliminare Soluzione A per la calibrazione di k_scala su istanze piccole/medie
(Sintetico N=200, Fabriano campionato N=300 e N=600) prima del test su Fabriano completo (N=3932).
"""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np

TESTING_DIR = Path(__file__).resolve().parent
SRC_DIR = TESTING_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from Generazione_Dati import generate_mock_data, generate_real_data
from Greedy import grid_search as greedy_gs
from ClarkeWright import grid_search as cw_gs
from main import X_VALUES, GRAPHML_PATH, UTENTI_JSON, calcola_worker_ottimali

KEYS = ["W", "x_star", "C", "tc", "c_fixed", "waste_types", "cd", "cm", "L", "alpha", "beta"]


def subsample(full: dict, N: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    chosen = np.sort(rng.choice(full["n_users"], size=N, replace=False))
    keep = np.concatenate([[0], chosen + 1])
    d = {k: full[k] for k in KEYS}
    d["dist_matrix"] = full["dist_matrix"][np.ix_(keep, keep)]
    d["time_matrix"] = full["time_matrix"][np.ix_(keep, keep)]
    d["user_types"] = np.asarray(full["user_types"], dtype=object)[chosen]
    d["n_users"] = N
    return d


def compute_k_methods(gs_by_r: dict[str, dict]) -> dict[str, float]:
    """Calcola k_scala secondo M0 (somma griglia), M1 (mediana), M2 (fascia centrale), M3 (punto fisso a gamma=0.5)."""
    # M0: Somma su tutta la griglia (attuale)
    tot_c_all, tot_i_all = 0.0, 0.0
    # M1: Mediana sulla griglia per ciascun rifiuto
    tot_c_med, tot_i_med = 0.0, 0.0
    # M2: Somma sulla fascia centrale X_r in [1.5, 2.0, 2.5]
    tot_c_cent, tot_i_cent = 0.0, 0.0

    for r, gs in gs_by_r.items():
        res_list = gs["all_results"]
        costs = [x["F_costo_fisso"] + x["F_viaggio"] + x["F_lavoro"] for x in res_list]
        ins = [x["F_insoddis"] for x in res_list]

        tot_c_all += sum(costs)
        tot_i_all += sum(ins)

        tot_c_med += float(np.median(costs))
        tot_i_med += float(np.median(ins))

        for x, c_val, i_val in zip(res_list, costs, ins):
            if 1.5 - 1e-9 <= x["X_r"] <= 2.5 + 1e-9:
                tot_c_cent += c_val
                tot_i_cent += i_val

    k_m0 = tot_c_all / tot_i_all if tot_i_all > 0 else 1.0
    k_m1 = tot_c_med / tot_i_med if tot_i_med > 0 else 1.0
    k_m2 = tot_c_cent / tot_i_cent if tot_i_cent > 0 else 1.0

    # M3: Punto fisso sull'ottimo a gamma = 0.5 (partendo da k_m1)
    k_cur = k_m1
    for _ in range(10):
        c_opt_sum, i_opt_sum = 0.0, 0.0
        for r, gs in gs_by_r.items():
            best_item = min(
                gs["all_results"],
                key=lambda item: 0.5 * k_cur * item["F_insoddis"]
                + 0.5 * (item["F_costo_fisso"] + item["F_viaggio"] + item["F_lavoro"]),
            )
            c_opt_sum += (best_item["F_costo_fisso"] + best_item["F_viaggio"] + best_item["F_lavoro"])
            i_opt_sum += best_item["F_insoddis"]
        k_next = c_opt_sum / i_opt_sum if i_opt_sum > 0 else 1.0
        if abs(k_next - k_cur) < 1e-6:
            k_cur = k_next
            break
        k_cur = 0.5 * k_cur + 0.5 * k_next

    return {
        "M0_somma_tot": k_m0,
        "M1_mediana": k_m1,
        "M2_centrale": k_m2,
        "M3_punto_fisso": k_cur,
    }


def evaluate_k(gs_g_by_r: dict, gs_cw_by_r: dict, k_val: float) -> dict:
    """Valuta per un dato k_scala i pesi % a gamma=0.5 e le X_r* medie a gamma=0.1, 0.5, 0.9."""
    out = {}
    for algo_label, gs_dict in [("Greedy", gs_g_by_r), ("CW", gs_cw_by_r)]:
        for gamma in (0.1, 0.5, 0.9):
            tot_c, tot_i = 0.0, 0.0
            x_stars = []
            for r, gs in gs_dict.items():
                best_item = min(
                    gs["all_results"],
                    key=lambda item: gamma * k_val * item["F_insoddis"]
                    + (1.0 - gamma) * (item["F_costo_fisso"] + item["F_viaggio"] + item["F_lavoro"]),
                )
                c_val = best_item["F_costo_fisso"] + best_item["F_viaggio"] + best_item["F_lavoro"]
                i_val = best_item["F_insoddis"]
                tot_c += c_val
                tot_i += i_val
                x_stars.append(best_item["X_r"])
            w_ins = gamma * k_val * tot_i
            w_cost = (1.0 - gamma) * tot_c
            f_tot = w_ins + w_cost
            pct_ins = (w_ins / f_tot * 100.0) if f_tot > 0 else 0.0
            out[(algo_label, gamma)] = {
                "tot_c": tot_c,
                "tot_i": tot_i,
                "pct_ins": pct_ins,
                "pct_cost": 100.0 - pct_ins,
                "mean_X": float(np.mean(x_stars)),
                "x_stars": x_stars,
            }
    return out


def main() -> None:
    import os
    os.chdir(SRC_DIR)
    print("Caricamento grafo reale Fabriano per campionamento...")
    full_fab = generate_real_data(
        graphml_path=str(SRC_DIR / GRAPHML_PATH),
        utenti_json_path=str(SRC_DIR / UTENTI_JSON),
        user_scenario=None,
        seed=42,
    )

    instances = [
        ("Sintetico N=200", generate_mock_data(n_users=200, seed=42, r_factor=1.2, user_scenario="residenziale")),
        ("Fabriano sub N=300", subsample(full_fab, 300, seed=42)),
        ("Fabriano sub N=600", subsample(full_fab, 600, seed=42)),
    ]

    for label, data in instances:
        n_w = calcola_worker_ottimali(data["n_users"])
        gs_g = {r: greedy_gs(data, r, X_VALUES, max_workers=n_w, gamma=0.5, k_scala=1.0) for r in data["waste_types"]}
        gs_cw = {r: cw_gs(data, r, X_VALUES, max_workers=n_w, gamma=0.5, k_scala=1.0) for r in data["waste_types"]}

        k_dict = compute_k_methods(gs_g)
        print("\n" + "=" * 112)
        print(f"  ISTANZA: {label}")
        print("=" * 112)
        print(
            f"  {'Metodo':<16} | {'k_scala':>7} | {'%Ins (g=0.5 G)':>14} {'%Cost (g=0.5 G)':>15} | "
            f"{'%Ins (g=0.5 CW)':>15} | {'X* medio G (0.1 / 0.5 / 0.9)':<28} | {'X* medio CW (0.1 / 0.5 / 0.9)'}"
        )
        print("  " + "-" * 108)
        for m_name, k_val in k_dict.items():
            ev = evaluate_k(gs_g, gs_cw, k_val)
            g05 = ev[("Greedy", 0.5)]
            cw05 = ev[("CW", 0.5)]
            xg_str = f"{ev[('Greedy', 0.1)]['mean_X']:.2f} / {g05['mean_X']:.2f} / {ev[('Greedy', 0.9)]['mean_X']:.2f}"
            xcw_str = f"{ev[('CW', 0.1)]['mean_X']:.2f} / {cw05['mean_X']:.2f} / {ev[('CW', 0.9)]['mean_X']:.2f}"
            print(
                f"  {m_name:<16} | {k_val:>7.4f} | {g05['pct_ins']:>13.1f}% {g05['pct_cost']:>14.1f}% | "
                f"{cw05['pct_ins']:>14.1f}% | {xg_str:<28} | {xcw_str}"
            )


if __name__ == "__main__":
    main()
