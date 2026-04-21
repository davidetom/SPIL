```python ln:1 hl:43-70 hlt:F_Totale
import csv

import time

from pathlib import Path

  

from Generazione_Dati import generate_mock_data, plot_graph

from Greedy import grid_search

  

# ──────────────────────────────────────────────────────────────────────────────

# Costanti configurabili

# ──────────────────────────────────────────────────────────────────────────────

  

X_VALUES = [x / 2 for x in range(1, 13)] # [0.5, 1.0, 1.5, ..., 6.0]

CSV_PATH = Path("risultati_spil.csv")

  

CSV_FIELDS = [

"rifiuto",

"X_r",

"is_best",

"n_vehicles",

"F_total",

"F_insoddis",

"F_costo_fisso",

"F_viaggio",

"F_lavoro",

"greedy_time_sec",

]

  
  

# ──────────────────────────────────────────────────────────────────────────────

# Helpers

# ──────────────────────────────────────────────────────────────────────────────

  

def _ask(prompt: str, default, cast):

"""Input con valore di default se l'utente preme Invio."""

raw = input(prompt).strip()

return cast(raw) if raw else default

  
  

def _stampa_separatore(char: str = "─", n: int = 52) -> None:

print(char * n)

  
  

def _stampa_riepilogo(waste_types: list[str], results: dict[str, dict]) -> None:

"""Stampa un riepilogo ordinato dei risultati best per ogni rifiuto."""

_stampa_separatore("═")

print(" RIEPILOGO RISULTATI OTTIMALI PER RIFIUTO")

_stampa_separatore("═")

  

for r in waste_types:

gs = results[r]

if gs["best_X_r"] is None:

print(f"\n[{r.upper():>16}] ⚠ Nessuna soluzione fattibile trovata.")

continue

  

bf = gs["best_F"]

print(f"\n [{r.upper()}]")

print(f" Miglior X_r : {gs['best_X_r']}")

print(f" Camion attivi : {gs['best_routes']['n_vehicles']}")

print(f" F totale : {bf['F_total']:>12.2f}")

print(f" Insoddisfaz. : {bf['F_insoddis']:>12.2f}")

print(f" Costo fisso : {bf['F_costo_fisso']:>12.2f}")

print(f" Costo viaggio : {bf['F_viaggio']:>12.2f}")

print(f" Costo lavoro : {bf['F_lavoro']:>12.2f}")

  

_stampa_separatore("═")

  
  

def _export_csv(

waste_types: list[str],

results: dict[str, dict],

greedy_time: float,

path: Path,

) -> None:

"""

Scrive un CSV con una riga per ogni (rifiuto, X_r) testato.

La colonna is_best segnala la soluzione ottimale per quel rifiuto.

"""

with path.open("w", newline="", encoding="utf-8") as f:

writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)

writer.writeheader()

  

for r in waste_types:

gs = results[r]

best_X_r = gs["best_X_r"]

all_results = gs["all_results"]

  

for entry in all_results:

writer.writerow({

"rifiuto": r,

"X_r": entry["X_r"],

"is_best": 1 if entry["X_r"] == best_X_r else 0,

"n_vehicles": entry["n_vehicles"],

"F_total": round(entry["F_total"], 4),

"F_insoddis": round(entry["F_insoddis"], 4),

"F_costo_fisso": round(entry["F_costo_fisso"], 4),

"F_viaggio": round(entry["F_viaggio"], 4),

"F_lavoro": round(entry["F_lavoro"], 4),

"greedy_time_sec": round(greedy_time, 6),

})

  

print(f"\n CSV salvato in: {path.resolve()}")

  
  

# ──────────────────────────────────────────────────────────────────────────────

# Main

# ──────────────────────────────────────────────────────────────────────────────

  

def main() -> None:

print("\n" + "═" * 54)

print(" SIMULATORE SPIL — Raccolta Differenziata")

print("═" * 54 + "\n")

  

# ── 1. Parametri di generazione ───────────────────────────────

n_users = _ask("Numero di utenti (default 100) : ", 100, int)

seed = _ask("Seed casuale (default 42) : ", 42, int)

r_factor = _ask("Fattore raggio (default 1.2) : ", 1.2, float)

  

# ── 2. Generazione dati (NON inclusa nel timer) ───────────────

print("\nGenerazione mappa e dati in corso...")

data = generate_mock_data(n_users=n_users, seed=seed, r_factor=r_factor)

print("Dati generati con successo!")

  

# ── 3. Plot opzionale (NON incluso nel timer) ─────────────────

mostra_plot = input("\nVuoi visualizzare il grafo della città? (s/n) : ").strip().lower()

if mostra_plot == "s":

print("Apertura grafico... (chiudi la finestra per continuare)")

plot_graph(data)

  

# ── 4. Loop multi-rifiuto con timer ───────────────────────────

print("\n" + "─" * 52)

print(" Avvio algoritmo greedy su tutti i rifiuti...")

print("─" * 52)

  

waste_types = data["waste_types"]

results: dict[str, dict] = {}

  

t_start = time.perf_counter() # ← TIMER START (solo greedy)

  

for r in waste_types:

print(f" › Grid search '{r}' ...", end=" ", flush=True)

gs = grid_search(data, r, X_VALUES)

results[r] = gs

  

if gs["best_X_r"] is not None:

print(f"best X={gs['best_X_r']} F={gs['best_F']['F_total']:.1f} "

f"camion={gs['best_routes']['n_vehicles']}")

else:

print("⚠ nessuna soluzione fattibile")

  

t_end = time.perf_counter() # ← TIMER STOP

greedy_time = t_end - t_start

  

print(f"\n Tempo greedy totale : {greedy_time:.4f} s")

  

# ── 5. Riepilogo a console ────────────────────────────────────

_stampa_riepilogo(waste_types, results)

  

# ── 6. Export CSV ─────────────────────────────────────────────

_export_csv(waste_types, results, greedy_time, CSV_PATH)

  
  

if __name__ == "__main__":

main()
```
