# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

from Generazione_Dati import generate_mock_data, plot_graph, USER_SCENARIOS

import os
import math
import psutil

# ──────────────────────────────────────────────────────────────────────────────
# Calcolo worker ottimali (invariato)
# ──────────────────────────────────────────────────────────────────────────────

def calcola_worker_ottimali(n_users: int) -> int:
    ram_totale_gb   = psutil.virtual_memory().total / (1024 ** 3)
    cpu_cores       = psutil.cpu_count(logical=False) or os.cpu_count() or 4
    margine_os      = max(4.0, ram_totale_gb * 0.20)
    ram_sicura_gb   = ram_totale_gb - margine_os
    gb_per_worker   = max(16.0 * (n_users ** 2) / (1024 ** 3), 0.1)
    workers_by_ram  = math.floor(ram_sicura_gb / gb_per_worker)
    workers_by_cpu  = max(1, cpu_cores - 1)
    return max(1, min(workers_by_ram, workers_by_cpu))


# ──────────────────────────────────────────────────────────────────────────────
# Costanti
# ──────────────────────────────────────────────────────────────────────────────

X_VALUES = [x / 2 for x in range(1, 13)]   # [0.5, 1.0, … 6.0]

CSV_FIELDS = [
    "rifiuto", "X_r", "algoritmo", "is_best",
    "n_vehicles", "F_total", "F_insoddis", "F_costo_fisso",
    "F_viaggio", "F_lavoro", "algo_time_sec",
]

ALGO_LABELS: dict[str, str] = {
    "greedy":        "Greedy",
    "clarke_wright": "Clarke-Wright",
}

CARTELLA_OUT = Path("risultati_csv")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers generici
# ──────────────────────────────────────────────────────────────────────────────

def _ask(prompt: str, default, cast):
    raw = input(prompt).strip()
    return cast(raw) if raw else default

def _sep(char: str = "-", n: int = 56) -> None:
    print(char * n)

def _chiedi_algoritmo() -> str:
    while True:
        raw = input(
            "\nAlgoritmo  [g=Greedy | c=Clarke-Wright | Invio=entrambi] : "
        ).strip().lower()
        if raw in ("g", "c", ""):
            return raw
        print("  [!]  Inserisci 'g', 'c' oppure premi Invio.")


# ──────────────────────────────────────────────────────────────────────────────
# Stampe a console (invariate rispetto al main originale)
# ──────────────────────────────────────────────────────────────────────────────

def _stampa_riepilogo(algo_key, waste_types, results, elapsed):
    label = ALGO_LABELS[algo_key]
    _sep("=")
    print(f"  RIEPILOGO [{label.upper()}]  --  tempo: {elapsed:.4f} s")
    _sep("=")
    for r in waste_types:
        gs = results[r]
        if gs["best_X_r"] is None:
            print(f"\n  [{r.upper():>16}]  [!]  Nessuna soluzione fattibile.")
            continue
        bf = gs["best_F"]
        print(f"\n  [{r.upper()}]")
        print(f"    Miglior X_r     : {gs['best_X_r']}")
        print(f"    Camion attivi   : {gs['best_routes']['n_vehicles']}")
        print(f"    F totale        : {bf['F_total']:>12.2f}")
        print(f"      Insoddisfaz.  : {bf['F_insoddis']:>12.2f}")
        print(f"      Costo fisso   : {bf['F_costo_fisso']:>12.2f}")
        print(f"      Costo viaggio : {bf['F_viaggio']:>12.2f}")
        print(f"      Costo lavoro  : {bf['F_lavoro']:>12.2f}")
    _sep("=")


def _stampa_comparativa(waste_types, results_by_algo, times_by_algo):
    COL = 12
    def _estrai(gs, k):
        return gs["best_F"][k] if gs["best_F"] else float("nan")
    def _tabella(titolo, righe):
        print(f"\n  ── {titolo} {'─'*(45-len(titolo))}")
        print(f"  {'Rifiuto':<18}  {'Greedy':>{COL}}  {'CW':>{COL}}  "
              f"{'Risparmio CW':>{COL}}  {'%':>6}")
        print(f"  {'-'*18}  {'-'*COL}  {'-'*COL}  {'-'*COL}  {'-'*6}")
        tot_g = tot_cw = 0.0
        for lbl, fg, fcw in righe:
            d   = fg - fcw
            pct = d / fg * 100 if fg else float("nan")
            print(f"  {lbl:<18}  {fg:{COL}.2f}  {fcw:{COL}.2f}  "
                  f"{d:+{COL}.2f}  {pct:>+5.1f}%")
            if fg == fg: tot_g += fg; tot_cw += fcw
        dt  = tot_g - tot_cw
        pct = dt / tot_g * 100 if tot_g else float("nan")
        print(f"  {'-'*18}  {'-'*COL}  {'-'*COL}  {'-'*COL}  {'-'*6}")
        print(f"  {'TOTALE':<18}  {tot_g:{COL}.2f}  {tot_cw:{COL}.2f}  "
              f"{dt:+{COL}.2f}  {pct:>+5.1f}%")

    righe_ft, righe_fc = [], []
    for r in waste_types:
        gg  = results_by_algo["greedy"][r]
        cw  = results_by_algo["clarke_wright"][r]
        righe_ft.append((r, _estrai(gg,"F_total"),      _estrai(cw,"F_total")))
        righe_fc.append((r,
            _estrai(gg,"F_costo_fisso")+_estrai(gg,"F_viaggio")+_estrai(gg,"F_lavoro"),
            _estrai(cw,"F_costo_fisso")+_estrai(cw,"F_viaggio")+_estrai(cw,"F_lavoro"),
        ))
    _sep("="); print("  CONFRONTO  Greedy  vs  Clarke-Wright"); _sep("=")
    _tabella("F_Total  (insoddisfazione + costi)", righe_ft)
    _tabella("F Costi  (fisso + viaggio + lavoro)", righe_fc)
    tg, tcw   = times_by_algo["greedy"], times_by_algo["clarke_wright"]
    faster    = "Greedy" if tg < tcw else "CW"
    ratio     = max(tg, tcw) / max(min(tg, tcw), 1e-9)
    print(f"\n  {'Tempo (s)':<18}  {tg:{COL}.4f}  {tcw:{COL}.4f}  "
          f"  {faster} e' {ratio:.2f}x piu' veloce")
    _sep("=")


# ──────────────────────────────────────────────────────────────────────────────
# Export CSV  —  naming convention estesa per MATLAB
# ──────────────────────────────────────────────────────────────────────────────
#
#  Naming convention:
#    risultati_<N>u_<TAG>.csv
#
#  TAG per tipo analisi:
#    standard              →  std_seed<S>
#    tipologia utenti      →  tipo_<scenario>
#    rete fissa            →  rete_Nmax<M>_Nact<N>_seed<S>
#    densità spaziale      →  densita_<mode>[_K<clusters>]
#
# ──────────────────────────────────────────────────────────────────────────────

def _csv_path(n_users: int, tag: str) -> Path:
    CARTELLA_OUT.mkdir(parents=True, exist_ok=True)
    return CARTELLA_OUT / f"risultati_{n_users}u_{tag}.csv"


def _export_csv(waste_types, results_by_algo, times_by_algo, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for algo_key, results in results_by_algo.items():
            algo_time = times_by_algo[algo_key]
            for r in waste_types:
                gs       = results[r]
                best_X_r = gs["best_X_r"]
                for entry in gs["all_results"]:
                    writer.writerow({
                        "rifiuto":       r,
                        "X_r":           entry["X_r"],
                        "algoritmo":     algo_key,
                        "is_best":       1 if entry["X_r"] == best_X_r else 0,
                        "n_vehicles":    entry["n_vehicles"],
                        "F_total":       round(entry["F_total"],       4),
                        "F_insoddis":    round(entry["F_insoddis"],    4),
                        "F_costo_fisso": round(entry["F_costo_fisso"], 4),
                        "F_viaggio":     round(entry["F_viaggio"],     4),
                        "F_lavoro":      round(entry["F_lavoro"],      4),
                        "algo_time_sec": round(algo_time,              6),
                    })
    print(f"  → CSV: {path.resolve()}")


# ──────────────────────────────────────────────────────────────────────────────
# Runner per singolo algoritmo (invariato nella logica, firma estesa)
# ──────────────────────────────────────────────────────────────────────────────

def _run_algo(algo_key, grid_search_fn, data, waste_types):
    label = ALGO_LABELS[algo_key]
    _sep()
    print(f"  Avvio {label}...")
    _sep()
    results = {}
    t0 = time.perf_counter()
    for r in waste_types:
        print(f"  >> [{label}] '{r}' ...", end=" ", flush=True)
        gs = grid_search_fn(data, r, X_VALUES)
        results[r] = gs
        if gs["best_X_r"] is not None:
            print(f"best X={gs['best_X_r']}  F={gs['best_F']['F_total']:.1f}  "
                  f"camion={gs['best_routes']['n_vehicles']}")
        else:
            print("[!] nessuna soluzione fattibile")
    elapsed = time.perf_counter() - t0
    print(f"\n  Tempo {label}: {elapsed:.4f} s")
    return results, elapsed


def _esegui_run(data, scelta_algo, tag_csv, mostra_riepilogo=True, mostra_grafo_ui=False):
    """Esegue gli algoritmi su `data` e salva il CSV.

    Parameters
    ----------
    data:
        Output di generate_mock_data.
    scelta_algo:
        "g" | "c" | "" (entrambi).
    tag_csv:
        Stringa tag per il naming del CSV.
    mostra_riepilogo:
        Se True stampa riepilogo/comparativa a console.

    Returns
    -------
    path : Path  — percorso del CSV scritto
    """
    if scelta_algo in ("c", ""):
        from ClarkeWright import grid_search as cw_gs
    if scelta_algo in ("g", ""):
        from Greedy import grid_search as greedy_gs

    waste_types      = data["waste_types"]
    n_workers        = calcola_worker_ottimali(data["n_users"])
    results_by_algo  = {}
    times_by_algo    = {}

    if scelta_algo in ("g", ""):
        res, el = _run_algo(
            "greedy",
            lambda d, r, x: greedy_gs(d, r, x, max_workers=n_workers),
            data, waste_types,
        )
        results_by_algo["greedy"] = res
        times_by_algo["greedy"]   = el

    if scelta_algo in ("c", ""):
        res, el = _run_algo(
            "clarke_wright",
            lambda d, r, x: cw_gs(d, r, x, max_workers=n_workers),
            data, waste_types,
        )
        results_by_algo["clarke_wright"] = res
        times_by_algo["clarke_wright"]   = el

    if mostra_riepilogo:
        for ak, res in results_by_algo.items():
            _stampa_riepilogo(ak, waste_types, res, times_by_algo[ak])
        if len(results_by_algo) == 2:
            _stampa_comparativa(waste_types, results_by_algo, times_by_algo)

    # Costruzione nomi file
    csv_filename = f"risultati_{data['n_users']}u_{tag_csv}.csv"
    png_filename = f"grafo_{csv_filename.replace('.csv', '.png')}"
    
    # Salvataggio CSV
    path_csv = _csv_path(data["n_users"], tag_csv)
    _export_csv(waste_types, results_by_algo, times_by_algo, path_csv)

    # CHIAMATA AL PLOT: Salva sempre, mostra solo se richiesto
    plot_graph(data, save_name=png_filename, show_ui=mostra_grafo_ui)
    
    return path_csv


# ══════════════════════════════════════════════════════════════════════════════
#  ANALISI 1 — Standard (comportamento originale)
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_standard() -> None:
    _sep("="); print("  ANALISI STANDARD"); _sep("=")

    n_users  = _ask("Numero di utenti   (default 100) : ", 100,  int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    print("\nGenerazione dati...")
    data = generate_mock_data(n_users=n_users, seed=seed, r_factor=r_factor)
    print("Dati generati!")

    mostra_ui = input("\nMostrare il grafo a schermo? (s/n) : ").strip().lower() == "s"
    
    scelta = _chiedi_algoritmo()
    tag    = f"std_seed{seed}"
    
    # Passiamo la preferenza a _esegui_run
    _esegui_run(data, scelta, tag, mostra_riepilogo=True, mostra_grafo_ui=mostra_ui)


# ══════════════════════════════════════════════════════════════════════════════
#  ANALISI 2 — Variazione Tipologia Utenti
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_tipologia() -> None:
    _sep("="); print("  ANALISI 2 — VARIAZIONE TIPOLOGIA UTENTI"); _sep("=")

    print("\nScenari disponibili:")
    for k, v in USER_SCENARIOS.items():
        print(f"    {k:<20} → {v['description']}")

    n_users  = _ask("\nNumero di utenti   (default 100) : ", 100,  int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    raw_sc = input(
        "Scenari da testare (Invio=tutti | es. residenziale,villette) : "
    ).strip()
    if raw_sc:
        scenari = [s.strip() for s in raw_sc.split(",")]
        # Validazione
        invalidi = [s for s in scenari if s not in USER_SCENARIOS]
        if invalidi:
            print(f"  [!] Scenari non validi: {invalidi}")
            return
    else:
        scenari = list(USER_SCENARIOS.keys())

    scelta = _chiedi_algoritmo()

    print("\n  [Nota: verranno generati più grafi di fila]")
    mostra_ui = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower() == "s"

    print(f"\n  Esecuzione su {len(scenari)} scenari: {scenari}")
    _sep()

    paths = []
    for scenario in scenari:
        print(f"\n  ▶  Scenario: {USER_SCENARIOS[scenario]['description']}")
        data = generate_mock_data(
            n_users=n_users, seed=seed, r_factor=r_factor,
            user_scenario=scenario,
        )

        tag  = f"tipo_{scenario}"
        path = path = _esegui_run(data, scelta, tag, mostra_riepilogo=False, mostra_grafo_ui=mostra_ui)
        paths.append(path)

    _sep("=")
    print(f"  ANALISI TIPOLOGIA completata. {len(paths)} CSV generati:")
    for p in paths:
        print(f"    {p.name}")
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  ANALISI 3 — Variazione N su Rete Fissa
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_rete_fissa() -> None:
    _sep("="); print("  ANALISI 3 — VARIAZIONE N SU RETE FISSA"); _sep("=")

    n_max    = _ask("\nDimensione città base N_max  (default 200) : ", 200, int)
    seed     = _ask("Seed casuale                 (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio               (default 1.2) : ", 1.2, float)

    raw_n = input(
        "Valori di N attivi da testare (Invio=50,100,150 | es. 30,60,90,120) : "
    ).strip()
    if raw_n:
        n_list = [int(x.strip()) for x in raw_n.split(",")]
    else:
        n_list = [50, 100, 150]

    # Validazione
    if any(n > n_max for n in n_list):
        print(f"  [!] Tutti i valori N devono essere ≤ N_max ({n_max}).")
        return

    # Scenario tipologia (opzionale)
    print("\nScenari tipologia disponibili:")
    for k in USER_SCENARIOS:
        print(f"    {k}")
    scenario = _ask(
        "Scenario tipologia (Invio=residenziale) : ",
        "residenziale", str,
    )

    scelta = _chiedi_algoritmo()

    print("\n  [Nota: verranno generati più grafi di fila]")
    mostra_ui = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower() == "s"

    print(f"\n  Rete base: {n_max} utenti  |  N attivi: {n_list}")
    _sep()

    paths = []
    for n_act in n_list:
        print(f"\n  ▶  N attivi = {n_act}")
        data = generate_mock_data(
            n_users=n_act,
            seed=seed,
            r_factor=r_factor,
            user_scenario=scenario,
            n_max=n_max,
            # active_nodes=None → estrazione casuale riproducibile via seed
        )

        tag  = f"rete_Nmax{n_max}_Nact{n_act}_seed{seed}"
        path = path = _esegui_run(data, scelta, tag, mostra_riepilogo=False, mostra_grafo_ui=mostra_ui)
        paths.append(path)

    _sep("=")
    print(f"  ANALISI RETE FISSA completata. {len(paths)} CSV generati:")
    for p in paths:
        print(f"    {p.name}")
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  ANALISI 4 — Variazione Densità Spaziale
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_densita() -> None:
    _sep("="); print("  ANALISI 4 — VARIAZIONE DENSITÀ SPAZIALE"); _sep("=")

    n_users  = _ask("\nNumero di utenti   (default 100) : ", 100,  int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    # Scenario tipologia (opzionale)
    print("\nScenari tipologia disponibili:")
    for k in USER_SCENARIOS:
        print(f"    {k}")
    scenario = _ask(
        "Scenario tipologia (Invio=residenziale) : ",
        "residenziale", str,
    )

    # Sub-menu modalità spaziali
    print("\nModalità spaziali da testare:")
    print("  [1] Solo uniforme")
    print("  [2] Solo cluster")
    print("  [3] Entrambe (confronto diretto)  ← default")
    raw_mode = input("Scelta (1/2/3, Invio=3) : ").strip()
    mode_map = {"1": ["uniform"], "2": ["cluster"], "3": ["uniform", "cluster"]}
    modes    = mode_map.get(raw_mode, ["uniform", "cluster"])

    # Parametri cluster (attivi solo se "cluster" è nelle modalità)
    cluster_configs: list[tuple[int, float]] = []
    if "cluster" in modes:
        raw_k = input(
            "Numero di cluster da testare (Invio=2,4,6 | es. 3,5) : "
        ).strip()
        k_list = [int(x.strip()) for x in raw_k.split(",")] if raw_k else [2, 4, 6]
        std    = _ask("Deviazione standard cluster km (default 1.2) : ", 1.2, float)
        cluster_configs = [(k, std) for k in k_list]

    scelta = _chiedi_algoritmo()

    print("\n  [Nota: verranno generati più grafi di fila]")
    mostra_ui = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower() == "s"

    # ── Costruzione lista run ──────────────────────────────────────────────────
    # Ogni run è una tupla (spatial_mode, n_clusters, cluster_std, tag)
    runs: list[tuple[str, int, float, str]] = []
    if "uniform" in modes:
        runs.append(("uniform", 0, 0.0, "densita_uniform"))
    for k, s in cluster_configs:
        runs.append(("cluster", k, s, f"densita_cluster_K{k}"))

    print(f"\n  Esecuzione su {len(runs)} configurazioni spaziali")
    _sep()

    paths = []
    for sp_mode, n_k, std, tag in runs:
        label = f"uniforme" if sp_mode == "uniform" else f"cluster K={n_k}"
        print(f"\n  ▶  Modalità spaziale: {label}")
        data = generate_mock_data(
            n_users=n_users,
            seed=seed,
            r_factor=r_factor,
            user_scenario=scenario,
            spatial_mode=sp_mode,
            n_clusters=n_k,
            cluster_std=std,
        )

        path = _esegui_run(data, scelta, tag, mostra_riepilogo=False, mostra_grafo_ui=mostra_ui)
        paths.append(path)

    _sep("=")
    print(f"  ANALISI DENSITÀ completata. {len(paths)} CSV generati:")
    for p in paths:
        print(f"    {p.name}")
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — Menu principale
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "=" * 56)
    print("        SIMULATORE SPIL -- Raccolta Differenziata")
    print("=" * 56)
    print("""
  Quale analisi vuoi eseguire?

    [1]  Standard              (singola run, comportamento originale)
    [2]  Variazione Tipologia  (stesso grafo, scenari utente diversi)
    [3]  Variazione N          (rete fissa, sottoinsieme nodi attivi)
    [4]  Variazione Densità    (uniforme vs cluster gaussiani)
    [0]  Esci
""")
    _sep()

    while True:
        raw = input("  Scelta [0-4] : ").strip()
        if raw in ("0","1","2","3","4"):
            break
        print("  [!]  Inserisci un valore tra 0 e 4.")

    if   raw == "0": print("  Uscita."); return
    elif raw == "1": _analisi_standard()
    elif raw == "2": _analisi_tipologia()
    elif raw == "3": _analisi_rete_fissa()
    elif raw == "4": _analisi_densita()


if __name__ == "__main__":
    main()