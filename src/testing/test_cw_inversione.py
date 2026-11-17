# test_cw_inversione.py
# ------------------------------------------------------------------------------
# Confronto tra ClarkeWright (standard, solo coda-testa) e ClarkeWright_inv
# (con inversione di rotta abilitata per fusioni testa-testa e coda-coda),
# utilizzando la nuova legge sub-lineare Q_ru(X_r) e la griglia X_VALUES <= 4.0.
# ------------------------------------------------------------------------------
from __future__ import annotations

import pickle
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent  # src/
sys.path.insert(0, str(ROOT))

import ClarkeWright as CW_old
import ClarkeWright_inv as CW_new
from Generazione_Dati import fattore_riempimento, generate_mock_data, generate_real_data
from main import GRAPHML_PATH, UTENTI_JSON, X_VALUES


def verifica_ammissibilita(data: dict, r: str, X_r: float, res_routes: dict) -> tuple[bool, str]:
    """Controlla che ogni rotta rispetti C_r, L e che il tempo ricalcolato coincida."""
    dist_np, time_np, Q_arr, TC_arr = CW_new._make_numpy_views(data, r, X_r)
    C_r = data["C"][r]
    L = data["L"]
    seen = set()
    for idx, route in enumerate(res_routes["routes"]):
        if route[0] != 0 or route[-1] != 0:
            return False, f"Rotta {idx} non parte/torna al deposito"
        internal = route[1:-1]
        for u in internal:
            if u in seen:
                return False, f"Utente {u} visitato due volte"
            seen.add(u)
        load_calc = float(sum(Q_arr[u] for u in internal))
        time_calc = 0.0
        for a, b in zip(route[:-1], route[1:]):
            time_calc += float(time_np[a, b])
        for u in internal:
            time_calc += float(TC_arr[u])
        if load_calc > C_r + 1e-4:
            return False, f"Rotta {idx} supera capacita': {load_calc:.2f} > {C_r}"
        if time_calc > L + 1e-3:
            return False, f"Rotta {idx} supera turno L: {time_calc:.2f} > {L}"
        if abs(time_calc - res_routes["times"][idx]) > 1e-2:
            return False, f"Rotta {idx} mismatch tempo: {time_calc:.3f} vs {res_routes['times'][idx]:.3f}"
    return True, "OK"


def confronta_istanza(nome_istanza: str, data: dict, rifiuti: list[str] | None = None) -> None:
    if rifiuti is None:
        rifiuti = data["waste_types"]

    print("\n" + "=" * 96)
    print(f" ISTANZA: {nome_istanza} (N = {data['n_users']} utenti)")
    print("=" * 96)
    header = (
        f"{'Rifiuto':<16} {'X_r':>4} | "
        f"{'V_old':>5} {'V_new':>5} | "
        f"{'F_costi_old (€)':>15} {'F_costi_new (€)':>15} {'Delta (€)':>11} {'Delta %':>8} | "
        f"{'Check':>5}"
    )
    print(header)
    print("-" * 96)

    tot_old = 0.0
    tot_new = 0.0
    n_migliorati = 0
    n_uguali = 0
    n_peggiorati = 0

    for r in rifiuti:
        for X_r in X_VALUES:
            r_old = CW_old.build_routes(data, r, X_r)
            o_old = CW_old.compute_objective(data, r, X_r, r_old)

            r_new = CW_new.build_routes(data, r, X_r)
            o_new = CW_new.compute_objective(data, r, X_r, r_new)

            ok, msg = verifica_ammissibilita(data, r, X_r, r_new)
            check_str = "OK" if ok else f"ERR:{msg}"

            c_old = o_old["F_costo_fisso"] + o_old["F_viaggio"] + o_old["F_lavoro"]
            c_new = o_new["F_costo_fisso"] + o_new["F_viaggio"] + o_new["F_lavoro"]
            delta = c_new - c_old
            delta_pct = (delta / c_old * 100.0) if c_old > 0 else 0.0

            tot_old += c_old
            tot_new += c_new
            if delta < -1e-4:
                n_migliorati += 1
            elif delta > 1e-4:
                n_peggiorati += 1
            else:
                n_uguali += 1

            print(
                f"{r:<16} {X_r:>4.1f} | "
                f"{r_old['n_vehicles']:>5d} {r_new['n_vehicles']:>5d} | "
                f"{c_old:>15.2f} {c_new:>15.2f} {delta:>+11.2f} {delta_pct:>+7.2f}% | "
                f"{check_str:>5}"
            )
        print("-" * 96)

    diff_tot = tot_new - tot_old
    diff_pct = (diff_tot / tot_old * 100.0) if tot_old > 0 else 0.0
    print(
        f" RIEPILOGO {nome_istanza}: "
        f"Migliorati={n_migliorati}, Uguali={n_uguali}, Peggiorati={n_peggiorati} | "
        f"Somma F_costi: {tot_old:,.2f} € -> {tot_new:,.2f} € ({diff_tot:+,.2f} €, {diff_pct:+.2f}%)"
    )


def main() -> None:
    print("Griglia X_VALUES attiva:", X_VALUES)
    print("Fattore di riempimento phi(X_r):")
    for x in X_VALUES:
        print(f"  X_r = {x:3.1f} -> phi(X_r) = {fattore_riempimento(x)*100:5.1f}%")

    # Istanza 1: Grafo condiviso N=400 (seed=42, scenario residenziale)
    pkl_path = ROOT / "grafo_condiviso" / "base_graph_N500_seed42.pkl"
    with open(pkl_path, "rb") as f:
        bg = pickle.load(f)
    data_1 = generate_mock_data(
        n_users=400, seed=42, r_factor=1.2,
        user_scenario="residenziale", spatial_mode="uniform",
        base_graph_dict=bg,
    )
    confronta_istanza("Istanza 1 — Sintetica Residenziale (N=400, seed=42)", data_1, ["organico", "indifferenziata", "vetro"])

    # Istanza 2: Mappa Reale di Fabriano (sottocampione N=500 e/o mappa completa N=3932)
    try:
        t0 = time.perf_counter()
        data_fab = generate_real_data(
            graphml_path=ROOT / GRAPHML_PATH,
            utenti_json_path=ROOT / UTENTI_JSON,
            user_scenario=None,
            seed=42,
        )
        print(f"\n[Fabriano caricata in {time.perf_counter() - t0:.1f} s]")
        confronta_istanza("Istanza 2 — Mappa Reale Fabriano (N=3932, mix reale)", data_fab, ["organico", "indifferenziata"])
    except Exception as e:
        print(f"\n[Fallback Istanza 2 su grafo N=1000 per: {e}]")
        pkl_1000 = ROOT / "grafo_condiviso" / "base_graph_N1000_seed42.pkl"
        with open(pkl_1000, "rb") as f:
            bg1000 = pickle.load(f)
        data_2 = generate_mock_data(
            n_users=800, seed=7, r_factor=1.2,
            user_scenario="grandi_condomini", spatial_mode="uniform",
            base_graph_dict=bg1000,
        )
        confronta_istanza("Istanza 2 — Sintetica Grandi Condomini (N=800, seed=7)", data_2, ["organico", "indifferenziata", "vetro"])


if __name__ == "__main__":
    main()
