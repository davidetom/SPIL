# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Callable

from Generazione_Dati import generate_mock_data, plot_graph

import os
import math
import psutil

# ──────────────────────────────────────────────────────────────────────────────
# Calcolo dei worker ottimali per la parallelizzazione (No saturazione RAM)
# ──────────────────────────────────────────────────────────────────────────────

def calcola_worker_ottimali(n_users: int) -> int:
    """
    Calcola dinamicamente i worker in base all'hardware reale della macchina.
    """
    # 1. Lettura dinamica dell'hardware
    ram_totale_bytes = psutil.virtual_memory().total
    ram_totale_gb = ram_totale_bytes / (1024 ** 3)
    
    # core fisici reali (su Apple Silicon di solito coincidono coi logici, ma su Intel/AMD no)
    cpu_cores_fisici = psutil.cpu_count(logical=False) or os.cpu_count() or 4
    
    # 2. RAM Sicura (Lasciamo al SO il 20% della RAM totale, o un minimo di 4 GB)
    margine_os = max(4.0, ram_totale_gb * 0.20)
    ram_sicura_gb = ram_totale_gb - margine_os
    
    # 3. Stima consumo per Worker (basato su float32)
    byte_per_worker = 16.0 * (n_users ** 2)
    gb_per_worker = max(byte_per_worker / (1024 ** 3), 0.1) 
    
    # 4. Calcolo limiti incrociati
    workers_by_ram = math.floor(ram_sicura_gb / gb_per_worker)
    workers_by_cpu = max(1, cpu_cores_fisici - 1) # Lasciamo 1 core libero
    
    # 5. Collo di bottiglia
    optimal_workers = max(1, min(workers_by_ram, workers_by_cpu))
    
    # Stampa di debug utilissima per capire cosa sta facendo il PC
    # print(f"  [Hardware] RAM: {ram_totale_gb:.1f} GB | Core: {cpu_cores_fisici}")
    # print(f"  [Allocazione] Worker: {optimal_workers} (Max RAM/worker: {gb_per_worker:.2f} GB)")
    
    return optimal_workers


# ──────────────────────────────────────────────────────────────────────────────
# Costanti configurabili
# ──────────────────────────────────────────────────────────────────────────────

X_VALUES = [x / 2 for x in range(1, 13)]   # [0.5, 1.0, 1.5, ..., 6.0]

# Colonna "greedy_time_sec" rinominata in "algo_time_sec" per generalità.
# La colonna "algoritmo" identifica chi ha generato ogni riga.
CSV_FIELDS = [
    "rifiuto",
    "X_r",
    "algoritmo",
    "is_best",
    "n_vehicles",
    "F_total",
    "F_insoddis",
    "F_costo_fisso",
    "F_viaggio",
    "F_lavoro",
    "algo_time_sec",
]

# Mappa: chiave interna → etichetta leggibile per console e CSV
ALGO_LABELS: dict[str, str] = {
    "greedy":        "Greedy",
    "clarke_wright": "Clarke-Wright",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers di I/O
# ──────────────────────────────────────────────────────────────────────────────

def _ask(prompt: str, default, cast):
    """Input con valore di default se l'utente preme Invio."""
    raw = input(prompt).strip()
    return cast(raw) if raw else default


def _stampa_separatore(char: str = "-", n: int = 56) -> None:
    print(char * n)


def _chiedi_algoritmo() -> str:
    """Chiede quale algoritmo eseguire.

    Returns
    -------
    str
        ``"g"`` = solo Greedy,
        ``"c"`` = solo Clarke-Wright,
        ``""``  = entrambi (benchmarking).
    """
    while True:
        raw = input(
            "\nAlgoritmo  [g=Greedy | c=Clarke-Wright | Invio=entrambi] : "
        ).strip().lower()
        if raw in ("g", "c", ""):
            return raw
        print("  [!]  Inserisci 'g', 'c' oppure premi Invio per entrambi.")


# ──────────────────────────────────────────────────────────────────────────────
# Stampa riepilogo
# ──────────────────────────────────────────────────────────────────────────────

def _stampa_riepilogo(
    algo_key: str,
    waste_types: list[str],
    results: dict[str, dict],
    elapsed: float,
) -> None:
    """Stampa il riepilogo ottimale per un singolo algoritmo."""
    label = ALGO_LABELS[algo_key]
    _stampa_separatore("=")
    print(f"  RIEPILOGO [{label.upper()}]  --  tempo: {elapsed:.4f} s")
    _stampa_separatore("=")

    for r in waste_types:
        gs = results[r]
        if gs["best_X_r"] is None:
            print(f"\n  [{r.upper():>16}]  [!]  Nessuna soluzione fattibile trovata.")
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

    _stampa_separatore("=")


# ──────────────────────────────────────────────────────────────────────────────
# Export CSV
# ──────────────────────────────────────────────────────────────────────────────

def _export_csv(
    waste_types: list[str],
    results_by_algo: dict[str, dict[str, dict]],
    times_by_algo: dict[str, float],
    path: Path,
) -> None:
    """Scrive il CSV con una riga per ogni (algoritmo, rifiuto, X_r) testato.

    Parameters
    ----------
    waste_types:
        Lista ordinata delle tipologie di rifiuto.
    results_by_algo:
        ``{ algo_key: { rifiuto: grid_search_result } }``
    times_by_algo:
        ``{ algo_key: elapsed_seconds }``
    path:
        Percorso del file CSV di output.
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()

        # Ordine di scrittura: prima tutti i risultati del primo algoritmo,
        # poi del secondo — così MATLAB trova blocchi contigui per algoritmo.
        for algo_key, results in results_by_algo.items():
            algo_time = times_by_algo[algo_key]

            for r in waste_types:
                gs          = results[r]
                best_X_r    = gs["best_X_r"]
                all_results = gs["all_results"]

                for entry in all_results:
                    writer.writerow({
                        "rifiuto":       r,
                        "X_r":           entry["X_r"],
                        "algoritmo":     algo_key,
                        "is_best":       1 if entry["X_r"] == best_X_r else 0,
                        "n_vehicles":    entry["n_vehicles"],
                        "F_total":       round(entry["F_total"],        4),
                        "F_insoddis":    round(entry["F_insoddis"],     4),
                        "F_costo_fisso": round(entry["F_costo_fisso"],  4),
                        "F_viaggio":     round(entry["F_viaggio"],      4),
                        "F_lavoro":      round(entry["F_lavoro"],       4),
                        "algo_time_sec": round(algo_time,               6),
                    })

    print(f"\n  CSV salvato in: {path.resolve()}")


# ──────────────────────────────────────────────────────────────────────────────
# Runner per singolo algoritmo
# ──────────────────────────────────────────────────────────────────────────────

def _run_algo(
    algo_key: str,
    grid_search_fn: Callable,
    data: dict,
    waste_types: list[str],
) -> tuple[dict[str, dict], float]:
    """Esegue la grid search per tutti i rifiuti con un algoritmo dato.

    Parameters
    ----------
    algo_key:
        Chiave interna dell'algoritmo (``"greedy"`` o ``"clarke_wright"``).
    grid_search_fn:
        Funzione ``grid_search`` del modulo corrispondente.
    data:
        Output di ``generate_mock_data``.
    waste_types:
        Lista delle tipologie di rifiuto da processare.

    Returns
    -------
    results : dict[str, dict]
        ``{ rifiuto: grid_search_result }``
    elapsed : float
        Secondi impiegati (timer perf_counter, solo calcolo).
    """
    label = ALGO_LABELS[algo_key]
    _stampa_separatore()
    print(f"  Avvio {label} su tutti i rifiuti...")
    _stampa_separatore()

    results: dict[str, dict] = {}

    t_start = time.perf_counter()          # TIMER START

    for r in waste_types:
        print(f"  >> [{label}] '{r}' ...", end=" ", flush=True)
        gs = grid_search_fn(data, r, X_VALUES)
        results[r] = gs

        if gs["best_X_r"] is not None:
            print(
                f"best X={gs['best_X_r']}  "
                f"F={gs['best_F']['F_total']:.1f}  "
                f"camion={gs['best_routes']['n_vehicles']}"
            )
        else:
            print("[!] nessuna soluzione fattibile")

    elapsed = time.perf_counter() - t_start   # TIMER STOP

    print(f"\n  Tempo {label}: {elapsed:.4f} s")
    return results, elapsed


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "=" * 56)
    print("        SIMULATORE SPIL -- Raccolta Differenziata")
    print("=" * 56 + "\n")

    # ── 1. Parametri di generazione ───────────────────────────────────────────
    n_users  = _ask("Numero di utenti   (default 100) : ", 100,  int)
    seed     = _ask("Seed casuale       (default  42) : ",  42,  int)
    r_factor = _ask("Fattore raggio     (default 1.2) : ", 1.2,  float)

    # ── CSV path dinamico ─────────────────────────────────────────────────────
    cartella_out = Path("risultati_csv")
    cartella_out.mkdir(parents=True, exist_ok=True) # Crea la cartella se non c'è
    
    csv_path = cartella_out / f"risultati_{n_users}_utenti.csv"
    if csv_path.exists():
        print(f"\n  [INFO] File '{csv_path}' già esistente — verrà sovrascritto.")
    else:
        print(f"\n  [INFO] Nuovo file CSV: '{csv_path}'")

    # ── 2. Generazione dati (NON inclusa nel timer) ───────────────────────────
    print("\nGenerazione mappa e dati in corso...")
    data = generate_mock_data(n_users=n_users, seed=seed, r_factor=r_factor)
    print("Dati generati con successo!")

    # ── 3. Plot opzionale (NON incluso nel timer) ─────────────────────────────
    mostra_plot = input("\nVuoi visualizzare il grafo della città? (s/n) : ").strip().lower()
    if mostra_plot == "s":
        print("Apertura grafico... (chiudi la finestra per continuare)")
        plot_graph(data)

    # ── 4. Selezione algoritmo ────────────────────────────────────────────────
    scelta = _chiedi_algoritmo()

    # Import condizionale: CW viene caricato solo se serve.
    # Evita overhead di import (e potenziali errori di dipendenza) quando
    # l'utente vuole girare solo Greedy.
    if scelta in ("c", ""):
        from ClarkeWright import grid_search as cw_grid_search

    if scelta in ("g", ""):
        from Greedy import grid_search as greedy_grid_search

    # ── 5. Esecuzione ─────────────────────────────────────────────────────────
    waste_types = data["waste_types"]

    # results_by_algo preserva l'ordine di inserimento (Python 3.7+):
    # greedy prima, CW dopo — coerente con l'ordine di scrittura nel CSV.
    results_by_algo: dict[str, dict[str, dict]] = {}
    times_by_algo:   dict[str, float]           = {}

    # Calcoliamo i worker ottimali una volta sola (vale per tutta la sessione)
    n_workers_safe = calcola_worker_ottimali(data["n_users"])

    if scelta in ("g", ""):
        res, elapsed = _run_algo(
            "greedy", 
            lambda d, r, x: greedy_grid_search(d, r, x, max_workers=n_workers_safe), 
            data, 
            waste_types
        )
        results_by_algo["greedy"] = res
        times_by_algo["greedy"]   = elapsed

    if scelta in ("c", ""):
        res, elapsed = _run_algo(
            "clarke_wright", 
            lambda d, r, x: cw_grid_search(d, r, x, max_workers=n_workers_safe), 
            data, 
            waste_types
        )
        results_by_algo["clarke_wright"] = res
        times_by_algo["clarke_wright"]   = elapsed

    # ── 6. Riepilogo a console ────────────────────────────────────────────────
    for algo_key, results in results_by_algo.items():
        _stampa_riepilogo(algo_key, waste_types, results, times_by_algo[algo_key])

    # Stampa comparativa tempi se entrambi presenti
    if len(results_by_algo) == 2:
        t_g  = times_by_algo["greedy"]
        t_cw = times_by_algo["clarke_wright"]
        faster, slower = ("Greedy", "CW") if t_g < t_cw else ("CW", "Greedy")
        ratio = max(t_g, t_cw) / max(min(t_g, t_cw), 1e-9)
        print(f"\n  [tempo] {faster} e' {ratio:.2f}x piu' veloce di {slower}  "
              f"({t_g:.4f}s vs {t_cw:.4f}s)")
        _stampa_separatore("-")

    # ── 7. Export CSV ─────────────────────────────────────────────────────────
    _export_csv(waste_types, results_by_algo, times_by_algo, csv_path)


if __name__ == "__main__":
    main()