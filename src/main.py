from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

from Generazione_Dati import (
    generate_mock_data, generate_real_data,
    plot_graph, plot_graph_reale,
    get_or_create_base_graph,
    USER_SCENARIOS,
)

import os
import math
import psutil

# ──────────────────────────────────────────────────────────────────────────────
# Calcolo worker ottimali
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

# ✅ CORREZIONE 1: Aggiunta di "gamma" e "k_scala" ai CSV_FIELDS
CSV_FIELDS = [
    "rifiuto", "X_r", "algoritmo", "is_best",
    "n_vehicles", "n_utenti_serviti", "F_total", "F_insoddis", "F_costo_fisso",
    "F_viaggio", "F_lavoro", "sat_fisica", "sat_tempo",
    "gamma", "k_scala", "algo_time_sec",
]

ALGO_LABELS: dict[str, str] = {
    "greedy":        "Greedy",
    "clarke_wright": "Clarke-Wright",
}

CARTELLA_OUT = Path("risultati_csv")
GRAPHML_PATH = Path("Generazione_grafo_Fabriano/dati_reali/grafo_aumentato.graphml")
UTENTI_JSON  = Path("Generazione_grafo_Fabriano/dati_reali/utenti.json")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers generici
# ──────────────────────────────────────────────────────────────────────────────

def _ask(prompt: str, default, cast):
    raw = input(prompt).strip()
    if raw:
        return cast(raw)
    else:
        return default

def _sep(char: str = "-", n: int = 56) -> None:
    print(char * n)

def _chiedi_algoritmo() -> str:
    while True:
        raw = input("\nAlgoritmo  [g=Greedy | c=Clarke-Wright | Invio=entrambi] : ").strip().lower()
        if raw in ("g", "c", ""):
            return raw
        print("  [!]  Inserisci 'g', 'c' oppure premi Invio.")


# ──────────────────────────────────────────────────────────────────────────────
# Stampe a console e Export CSV
# ──────────────────────────────────────────────────────────────────────────────

def _stampa_riepilogo(algo_key, waste_types, results, elapsed, gamma, sc_label):
    label = ALGO_LABELS[algo_key]
    _sep("=")
    print(f"  RIEPILOGO [{label.upper()}]  -- Scenario {sc_label} (γ={gamma}) -- tempo: {elapsed:.4f} s")
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
        n_serviti = sum(1 for route in gs["best_routes"]["routes"] for u in route if u != 0)
        print(f"    Utenti serviti  : {n_serviti}")
        print(f"    Saturaz. Fisica : {bf['sat_fisica']:.1f}%")
        print(f"    Saturaz. Tempo  : {bf['sat_tempo']:.1f}%")
        print(f"    F totale        : {bf['F_total']:>12.2f}")
        print(f"      Insoddisfaz.  : {bf['F_insoddis']:>12.2f}")
        print(f"      Costo fisso   : {bf['F_costo_fisso']:>12.2f}")
        print(f"      Costo viaggio : {bf['F_viaggio']:>12.2f}")
        print(f"      Costo lavoro  : {bf['F_lavoro']:>12.2f}")
        
    _sep("=")


def _stampa_comparativa(waste_types, results_by_algo, times_by_algo):
    COL = 12
    
    def _estrai(gs, k): 
        if gs["best_F"]:
            return gs["best_F"][k]
        else:
            return float("nan")
            
    def _tabella(titolo, righe):
        print(f"\n  ── {titolo} {'─'*(45-len(titolo))}")
        print(f"  {'Rifiuto':<18}  {'Greedy':>{COL}}  {'CW':>{COL}}  {'Risparmio CW':>{COL}}  {'%':>6}")
        print(f"  {'-'*18}  {'-'*COL}  {'-'*COL}  {'-'*COL}  {'-'*6}")
        
        tot_g = 0.0
        tot_cw = 0.0
        
        for lbl, fg, fcw in righe:
            d = fg - fcw
            
            if fg:
                pct = d / fg * 100
            else:
                pct = float("nan")
                
            print(f"  {lbl:<18}  {fg:{COL}.2f}  {fcw:{COL}.2f}  {d:+{COL}.2f}  {pct:>+5.1f}%")
            
            if fg == fg: 
                tot_g += fg
                tot_cw += fcw
                
        dt  = tot_g - tot_cw
        
        if tot_g:
            pct = dt / tot_g * 100
        else:
            pct = float("nan")
            
        print(f"  {'-'*18}  {'-'*COL}  {'-'*COL}  {'-'*COL}  {'-'*6}")
        print(f"  {'TOTALE':<18}  {tot_g:{COL}.2f}  {tot_cw:{COL}.2f}  {dt:+{COL}.2f}  {pct:>+5.1f}%")

    righe_ft = []
    righe_fc = []
    
    for r in waste_types:
        gg  = results_by_algo["greedy"][r]
        cw  = results_by_algo["clarke_wright"][r]
        
        # 1. Popolamento riga per la tabella F_Total assoluta
        righe_ft.append((r, _estrai(gg, "F_total"), _estrai(cw, "F_total")))
        
        # 2. Calcolo costo operativo giornaliero per l'algoritmo Greedy
        if gg.get("best_F") and gg.get("best_X_r") and gg["best_X_r"] > 0:
            costi_g_operativi = _estrai(gg, "F_costo_fisso") + _estrai(gg, "F_viaggio") + _estrai(gg, "F_lavoro")
            costi_g_giorn = costi_g_operativi / gg["best_X_r"]
        else:
            costi_g_giorn = float("nan")
            
        # 3. Calcolo costo operativo giornaliero per l'algoritmo Clarke-Wright
        if cw.get("best_F") and cw.get("best_X_r") and cw["best_X_r"] > 0:
            costi_cw_operativi = _estrai(cw, "F_costo_fisso") + _estrai(cw, "F_viaggio") + _estrai(cw, "F_lavoro")
            costi_cw_giorn = costi_cw_operativi / cw["best_X_r"]
        else:
            costi_cw_giorn = float("nan")
            
        # Aggiunta dei costi normalizzati per singola run alla lista
        righe_fc.append((r, costi_g_giorn, costi_cw_giorn))
        
    _sep("=")
    print("  CONFRONTO  Greedy  vs  Clarke-Wright")
    _sep("=")
    
    # Stampe finali delle due tabelle comparative con i nuovi titoli scientifici
    _tabella("F_Total  (insoddisfazione + costi)", righe_ft)
    _tabella("F Costi Giornalieri (costi operativi / best_X_r)", righe_fc)
    
    tg = times_by_algo["greedy"]
    tcw = times_by_algo["clarke_wright"]
    
    if tg < tcw:
        faster = "Greedy"
    else:
        faster = "CW"
        
    ratio = max(tg, tcw) / max(min(tg, tcw), 1e-9)
    print(f"\n  {'Tempo (s)':<18}  {tg:{COL}.4f}  {tcw:{COL}.4f}    {faster} e' {ratio:.2f}x piu' veloce")
    _sep("=")


def _csv_path(n_users: int, tag: str) -> Path:
    CARTELLA_OUT.mkdir(parents=True, exist_ok=True)
    return CARTELLA_OUT / f"risultati_{n_users}u_{tag}.csv"


# ✅ CORREZIONE 2: Modifica firma di _export_csv per ricevere gamma e k_scala
def _export_csv(waste_types, results_by_algo, times_by_algo, path: Path, gamma: float, k_scala: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        
        for algo_key, results in results_by_algo.items():
            algo_time = times_by_algo[algo_key]
            
            for r in waste_types:
                gs = results[r]
                best_X_r = gs["best_X_r"]
                
                for entry in gs["all_results"]:
                    
                    if entry["X_r"] == best_X_r:
                        is_best_val = 1
                    else:
                        is_best_val = 0
                    
                    routes_list = entry["routes"]["routes"]
                    n_serviti = sum(1 for route in routes_list for u in route if u != 0)

                    writer.writerow({
                        "rifiuto":       r,
                        "X_r":           entry["X_r"],
                        "algoritmo":     algo_key,
                        "is_best":       is_best_val,
                        "n_vehicles":    entry["n_vehicles"],
                        "n_utenti_serviti": n_serviti,
                        "F_total":       round(entry["F_total"],       4),
                        "F_insoddis":    round(entry["F_insoddis"],    4),
                        "F_costo_fisso": round(entry["F_costo_fisso"], 4),
                        "F_viaggio":     round(entry["F_viaggio"],     4),
                        "F_lavoro":      round(entry["F_lavoro"],      4),
                        "sat_fisica":    round(entry["sat_fisica"],    2),
                        "sat_tempo":     round(entry["sat_tempo"],     2),
                        "gamma":         round(gamma,                  4),
                        "k_scala":       round(k_scala,                4),
                        "algo_time_sec": round(algo_time,              6),
                    })
                    
    print(f"  → CSV: {path.resolve()}")


# ──────────────────────────────────────────────────────────────────────────────
# Funzioni Base e Multi-Scenario Esecuzione 
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
            print(f"best X={gs['best_X_r']}  F={gs['best_F']['F_total']:.1f}  camion={gs['best_routes']['n_vehicles']}")
        else:
            print("[!] nessuna soluzione fattibile")
            
    elapsed = time.perf_counter() - t0
    print(f"\n  Tempo {label}: {elapsed:.4f} s")
    
    return results, elapsed

def _calcola_fattore_scala(data: dict, waste_types: list[str]) -> float:
    from Greedy import grid_search as greedy_gs
    print("\n  [!] Calcolo K_scala (run di prova Greedy)...")
    
    n_workers = calcola_worker_ottimali(data["n_users"])
    tot_insoddis = 0.0
    tot_costi = 0.0

    for r in waste_types:
        gs = greedy_gs(data, r, X_VALUES, max_workers=n_workers, gamma=0.5, k_scala=1.0)
        for res in gs["all_results"]:
            tot_insoddis += res["F_insoddis"]
            tot_costi += (res["F_costo_fisso"] + res["F_viaggio"] + res["F_lavoro"])

    if tot_insoddis == 0:
        k_scala = 1.0
    else:
        k_scala = tot_costi / tot_insoddis

    print(f"      K_scala calcolato: {k_scala:.4f}")
    return k_scala


def _esegui_run(data, scelta_algo, tag_csv, k_scala, mostra_riepilogo=True, mostra_grafo_ui=False, plot_fn=None, salva_png=True):
    if plot_fn is None:
        plot_fn = plot_graph
        
    if scelta_algo in ("c", ""):
        from ClarkeWright import grid_search as cw_gs
        
    if scelta_algo in ("g", ""):
        from Greedy import grid_search as greedy_gs

    waste_types = data["waste_types"]
    n_workers   = calcola_worker_ottimali(data["n_users"])
    
    scenari_politici = [
        (0.50, "Neutro"), 
        (0.10, "Pro-Azienda"), 
        (0.90, "Pro-Cittadino")
    ]
    paths = []

    for gamma, sc_label in scenari_politici:
        print(f"\n  [--- AVVIO SCENARIO: {sc_label} (gamma={gamma:.2f}) ---]")
        results_by_algo  = {}
        times_by_algo    = {}

        if scelta_algo in ("g", ""):
            res, el = _run_algo("greedy", lambda d, r, x: greedy_gs(d, r, x, max_workers=n_workers, gamma=gamma, k_scala=k_scala), data, waste_types)
            results_by_algo["greedy"] = res
            times_by_algo["greedy"]   = el

        if scelta_algo in ("c", ""):
            res, el = _run_algo("clarke_wright", lambda d, r, x: cw_gs(d, r, x, max_workers=n_workers, gamma=gamma, k_scala=k_scala), data, waste_types)
            results_by_algo["clarke_wright"] = res
            times_by_algo["clarke_wright"]   = el

        if mostra_riepilogo:
            for ak, res in results_by_algo.items():
                _stampa_riepilogo(ak, waste_types, res, times_by_algo[ak], gamma, sc_label)
                
            if len(results_by_algo) == 2:
                _stampa_comparativa(waste_types, results_by_algo, times_by_algo)

        tag_scenario = f"{tag_csv}_gamma{gamma:.2f}"
        path_csv = _csv_path(data["n_users"], tag_scenario)
        # ✅ CORREZIONE 4: Aggiorna la chiamata a _export_csv per passare gamma e k_scala
        _export_csv(waste_types, results_by_algo, times_by_algo, path_csv, gamma, k_scala)
        paths.append(path_csv)

    csv_filename_base = f"risultati_{data['n_users']}u_{tag_csv}.csv"
    
    if salva_png:
        png_filename = f"grafo_{csv_filename_base.replace('.csv', '.png')}"
    else:
        png_filename = None
    
    if png_filename is not None or mostra_grafo_ui:
        plot_fn(data, save_name=png_filename, show_ui=mostra_grafo_ui)
    
    return paths


# ══════════════════════════════════════════════════════════════════════════════
#  [1] ANALISI 1 — Variazione N su Rete Fissa
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_variazione_N() -> None:
    _sep("=")
    print("  ANALISI 1 — VARIAZIONE N (RETE STRADALE CONDIVISA)")
    _sep("=")

    n_max    = _ask("\nDimensione città base N_max  (default 5000) : ", 5000, int)
    seed     = _ask("Seed casuale                 (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio               (default 1.2) : ", 1.2, float)

    bg = get_or_create_base_graph(n_max=n_max, seed=seed, r_factor=r_factor)

    raw_n = input("Valori di N attivi da testare (Invio=50,100,200 | es. 50,150) : ").strip()
    
    if raw_n:
        n_list = [int(x.strip()) for x in raw_n.split(",")]
    else:
        n_list = [50, 100, 200]

    for n in n_list:
        if n > n_max:
            print(f"  [!] Tutti i valori N devono essere ≤ N_max ({n_max}).")
            return

    scenario = "residenziale"
    print(f"  [Variabili Isolate] Scenario tipologia = '{scenario}' | Distribuzione = 'uniforme'")

    scelta = _chiedi_algoritmo()

    print("\n  [Nota: verranno eseguiti multipli run]")
    
    mostra_ui_raw = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower()
    if mostra_ui_raw == "s":
        mostra_ui = True
    else:
        mostra_ui = False

    paths = []
    
    for n_act in n_list:
        print(f"\n  ▶  N attivi = {n_act}")
        data = generate_mock_data(
            n_users=n_act, 
            seed=seed, 
            r_factor=r_factor,
            user_scenario=scenario, 
            spatial_mode="uniform", 
            base_graph_dict=bg
        )
        
        k_scala = _calcola_fattore_scala(data, data["waste_types"])
        tag  = f"varN_Nmax{n_max}_Nact{n_act}_seed{seed}"
        
        run_paths = _esegui_run(
            data, 
            scelta, 
            tag, 
            k_scala, 
            mostra_riepilogo=True, 
            mostra_grafo_ui=mostra_ui, 
            salva_png=False
        )
        paths.extend(run_paths)

    _sep("=")
    print(f"  ANALISI VARIAZIONE N completata. {len(paths)} CSV generati:")
    
    for p in paths:
        print(f"    {p.name}")
        
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  [2] ANALISI 2 — Variazione Tipologia Utenti
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_tipologia() -> None:
    _sep("=")
    print("  ANALISI 2 — VARIAZIONE TIPOLOGIA UTENTI")
    _sep("=")

    print("\nScenari disponibili:")
    for k, v in USER_SCENARIOS.items():
        print(f"    {k:<20} → {v['description']}")

    n_users  = _ask("\nNumero di utenti attivi (default 100) : ", 100,  int)
    n_max    = _ask("Dimensione città base N_max (default 5000) : ", 5000, int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    if n_users > n_max:
        print(f"  [!] N_users ({n_users}) deve essere ≤ N_max ({n_max}).")
        return

    bg = get_or_create_base_graph(n_max=n_max, seed=seed, r_factor=r_factor)

    raw_sc = input("Scenari da testare (Invio=tutti | es. residenziale,villette) : ").strip()
    
    if raw_sc:
        scenari = [s.strip() for s in raw_sc.split(",")]
        invalidi = []
        for s in scenari:
            if s not in USER_SCENARIOS:
                invalidi.append(s)
                
        if invalidi:
            print(f"  [!] Scenari non validi: {invalidi}")
            return
    else:
        scenari = list(USER_SCENARIOS.keys())

    print(f"  [Variabili Isolate] Distribuzione = 'uniforme'")

    scelta = _chiedi_algoritmo()
    
    mostra_ui_raw = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower()
    if mostra_ui_raw == "s":
        mostra_ui = True
    else:
        mostra_ui = False

    paths = []
    
    for scenario in scenari:
        print(f"\n  ▶  Scenario: {USER_SCENARIOS[scenario]['description']}")
        data = generate_mock_data(
            n_users=n_users, 
            seed=seed, 
            r_factor=r_factor,
            user_scenario=scenario, 
            spatial_mode="uniform", 
            base_graph_dict=bg
        )
        
        k_scala = _calcola_fattore_scala(data, data["waste_types"])
        tag  = f"tipo_{scenario}"
        
        run_paths = _esegui_run(
            data, 
            scelta, 
            tag, 
            k_scala, 
            mostra_riepilogo=True, 
            mostra_grafo_ui=mostra_ui, 
            salva_png=False
        )
        paths.extend(run_paths)

    _sep("=")
    print(f"  ANALISI TIPOLOGIA completata. {len(paths)} CSV generati:")
    
    for p in paths:
        print(f"    {p.name}")
        
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  [3] ANALISI 3 — Variazione Distribuzione (Uniforme vs Aggregata)
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_distribuzione() -> None:
    _sep("=")
    print("  ANALISI 3 — VARIAZIONE DISTRIBUZIONE SPAZIALE")
    _sep("=")

    n_users  = _ask("\nNumero di utenti attivi (default 100) : ", 100,  int)
    n_max    = _ask("Dimensione città base N_max (default 5000) : ", 5000, int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    if n_users > n_max:
        print(f"  [!] N_users ({n_users}) deve essere ≤ N_max ({n_max}).")
        return

    bg = get_or_create_base_graph(n_max=n_max, seed=seed, r_factor=r_factor)

    print("\nModalità spaziali da testare:")
    print("  [1] Solo uniforme")
    print("  [2] Solo aggregata al centro (cluster singolo)")
    print("  [3] Entrambe (confronto diretto)  ← default")
    raw_mode = input("Scelta (1/2/3, Invio=3) : ").strip()
    
    modes = []
    if raw_mode in ("1", "3", ""): 
        modes.append("uniform")
    if raw_mode in ("2", "3", ""): 
        modes.append("cluster")

    scenario = "residenziale"
    print(f"  [Variabili Isolate] Scenario tipologia = '{scenario}'")

    scelta = _chiedi_algoritmo()
    
    mostra_ui_raw = input("  Mostrare i grafi a schermo ad ogni step? (s/n) : ").strip().lower()
    if mostra_ui_raw == "s":
        mostra_ui = True
    else:
        mostra_ui = False

    paths = []
    
    for sp_mode in modes:
        if sp_mode == "uniform":
            label = "Uniforme"
        else:
            label = "Aggregata al Centro"
            
        print(f"\n  ▶  Modalità spaziale: {label}")
        
        data = generate_mock_data(
            n_users=n_users, 
            seed=seed, 
            r_factor=r_factor,
            user_scenario=scenario, 
            spatial_mode=sp_mode, 
            base_graph_dict=bg
        )

        k_scala = _calcola_fattore_scala(data, data["waste_types"])
        tag = f"distrib_{sp_mode}"
        
        run_paths = _esegui_run(
            data, 
            scelta, 
            tag, 
            k_scala, 
            mostra_riepilogo=True, 
            mostra_grafo_ui=mostra_ui, 
            salva_png=False
        )
        paths.extend(run_paths)

    _sep("=")
    print(f"  ANALISI DISTRIBUZIONE completata. {len(paths)} CSV generati:")
    
    for p in paths:
        print(f"    {p.name}")
        
    _sep("=")


# ══════════════════════════════════════════════════════════════════════════════
#  [4] ANALISI 4 — Mappa Reale Fabriano (Ottimizzata e completamente Reale)
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_mappa_reale() -> None:
    _sep("=")
    print("  ANALISI 4 — MAPPA REALE FABRIANO")
    _sep("=")
    
    print(f"\n  Grafo    : {GRAPHML_PATH}")
    print(f"  Utenti   : {UTENTI_JSON}")
    print(f"  Deposito : Via Vittorio Bachelet 15, Fabriano (Anconambiente S.p.A.)")

    for p in (GRAPHML_PATH, UTENTI_JSON):
        if not p.exists():
            print(f"  [!] File non trovato: {p}")
            return

    _sep()
    print("  [INFO] Caricamento mappa reale in corso... (richiede tipicamente 30-90 s)")
    _sep()

    # Caricamento vincolato interamente ai dati reali (niente seed o scelte stocastiche)
    data = generate_real_data(
        graphml_path=GRAPHML_PATH, 
        utenti_json_path=UTENTI_JSON,
        user_scenario=None, 
        seed=42
    )

    print(f"\n  Dati caricati: {data['n_users']} utenti  |  tipologie: reali (estratte da utenti.json)")

    scelta = _chiedi_algoritmo()
    
    mostra_ui_raw = input("\n  Mostrare il grafo a schermo? (s/n) : ").strip().lower()
    if mostra_ui_raw == "s":
        mostra_ui = True
    else:
        mostra_ui = False
        
    tag = "mappa_reale"

    k_scala = _calcola_fattore_scala(data, data["waste_types"])
    
    _esegui_run(
        data, 
        scelta, 
        tag, 
        k_scala, 
        mostra_riepilogo=True, 
        mostra_grafo_ui=mostra_ui, 
        plot_fn=plot_graph_reale, 
        salva_png=True
    )


# ══════════════════════════════════════════════════════════════════════════════
#  [5] ANALISI 5 — Standard (Grafo generato da zero)
# ══════════════════════════════════════════════════════════════════════════════

def _analisi_standard() -> None:
    _sep("=")
    print("  ANALISI 5 — STANDARD (GRAFO DA ZERO)")
    _sep("=")

    n_users  = _ask("Numero di utenti   (default 100) : ", 100,  int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)
    scenario = _ask("Scenario tipologia (Invio=residenziale) : ", "residenziale", str)

    print("\nGenerazione dati...")
    data = generate_mock_data(
        n_users=n_users, 
        seed=seed, 
        r_factor=r_factor, 
        user_scenario=scenario
    )
    print("Dati generati!")
    
    k_scala = _calcola_fattore_scala(data, data["waste_types"])
    
    mostra_ui_raw = input("\nMostrare il grafo a schermo? (s/n) : ").strip().lower()
    if mostra_ui_raw == "s":
        mostra_ui = True
    else:
        mostra_ui = False
        
    scelta = _chiedi_algoritmo()
    
    _esegui_run(
        data, 
        scelta, 
        f"std_seed{seed}", 
        k_scala, 
        mostra_riepilogo=True, 
        mostra_grafo_ui=mostra_ui, 
        salva_png=True
    )


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN — Menu principale
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "=" * 56)
    print("        SIMULATORE SPIL -- Raccolta Differenziata")
    print("=" * 56)
    print("""
  Quale analisi vuoi eseguire?

    [1] Variazione Numero Utenti (N)
    [2] Variazione Tipologia Utenti
    [3] Variazione Distribuzione (Uniforme vs Aggregata al Centro)
    [4] Mappa Reale Fabriano
    [5] Standard (Grafo generato da zero)
    [0] Esci
""")
    _sep()

    while True:
        raw = input("  Scelta [0-5] : ").strip()
        if raw in ("0","1","2","3","4","5"):
            break
        print("  [!]  Inserisci un valore tra 0 e 5.")

    if raw == "0": 
        print("  Uscita.")
        return
    elif raw == "1": 
        _analisi_variazione_N()
    elif raw == "2": 
        _analisi_tipologia()
    elif raw == "3": 
        _analisi_distribuzione()
    elif raw == "4": 
        _analisi_mappa_reale()
    elif raw == "5": 
        _analisi_standard()


if __name__ == "__main__":
    main()