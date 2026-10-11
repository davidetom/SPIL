"""
Confronto grado medio: grafo reale di Fabriano vs grafi sintetici.
Usa direttamente get_or_create_base_graph di Generazione_Dati.py con i valori
di default usati in main.py.

Eseguire dalla cartella Euristiche:
    python calcola_grado_medio.py
"""

import sys
from pathlib import Path
import pandas as pd

# ── Assicura che Generazione_Dati sia importabile ─────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from Generazione_Dati import get_or_create_base_graph

# ── Grafo REALE di Fabriano ───────────────────────────────────────────────────
BASE  = Path("Generazione_grafo_Fabriano/dati_reali/")
archi = pd.read_csv(BASE / "archi_stradali.csv")
nodi  = pd.read_csv(BASE / "nodi_stradali.csv")

n_real = len(nodi)
# Gli archi OSM nel CSV sono ORIENTATI (u→v già distinto da v→u).
# _build_graph genera archi NON-orientati (un solo (i,j) con i<j).
# Per confronto omogeneo contiamo gli archi come non-orientati:
#   - se il CSV ha già sia u→v che v→u  → dividiamo per 2
#   - verifichiamo guardando i duplicati simmetrici
pairs_directed  = set(zip(archi["u"], archi["v"]))
pairs_reversed  = {(v, u) for u, v in pairs_directed}
n_symmetric     = len(pairs_directed & pairs_reversed)
is_bidirectional = n_symmetric / len(pairs_directed) > 0.5   # >50% ha entrambe le direzioni

if is_bidirectional:
    e_real_undir = len(pairs_directed) // 2
    nota = "archi OSM bidirezionali → contati come non-orientati (/2)"
else:
    e_real_undir = len(pairs_directed)
    nota = "archi OSM prevalentemente monodirezionali → contati as-is"

degree_real = 2 * e_real_undir / n_real

print("=" * 58)
print("  GRAFO REALE DI FABRIANO")
print("=" * 58)
print(f"  nodi                : {n_real}")
print(f"  archi (CSV raw)     : {len(archi)}")
print(f"  archi non-orientati : {e_real_undir}  ({nota})")
print(f"  grado medio         : {degree_real:.3f}")

# ── Grafi SINTETICI — default di main.py ─────────────────────────────────────
# Analisi 1: N_max=5000, seed=42, r_factor=1.2
# Analisi 2/3: N_max=500 (default get_or_create_base_graph), seed=42, r_factor=1.2
configs = [
    dict(n_max=500,  seed=42, r_factor=1.2),   # default get_or_create_base_graph
    dict(n_max=5000, seed=42, r_factor=1.2),   # Analisi 1 di main.py
    dict(n_max=500,  seed=42, r_factor=1.0),   # r_factor alternativo
]

print()
print("=" * 58)
print("  GRAFI SINTETICI  (get_or_create_base_graph)")
print("=" * 58)

degree_syn_list = []
for cfg in configs:
    bg     = get_or_create_base_graph(**cfg)
    edges  = bg["edges_base"]          # set di tuple (i,j) con i<j → non-orientato
    n_syn  = cfg["n_max"] + 1          # nodi totali = n_max incroci + 1 deposito
    e_syn  = len(edges)
    deg    = 2 * e_syn / n_syn
    degree_syn_list.append(deg)
    print(f"  N_max={cfg['n_max']:5d} | r={cfg['r_factor']:.1f} | "
          f"nodi={n_syn:5d} | archi={e_syn:6d} | grado medio={deg:.3f}")

# ── Riepilogo ─────────────────────────────────────────────────────────────────
avg_syn = sum(degree_syn_list) / len(degree_syn_list)
delta   = degree_real - avg_syn

print()
print("=" * 58)
print(f"  Grado medio reale         : {degree_real:.3f}")
print(f"  Grado medio sintetico (μ) : {avg_syn:.3f}")
print(f"  Δ (reale − sintetico)     : {delta:+.3f}")

if abs(delta) > 0.5:
    if delta > 0:
        print("\n  → Il grafo REALE è più denso del sintetico:")
        print("    le euristiche potrebbero sottostimare la connettività reale.")
    else:
        print("\n  → Il grafo SINTETICO è più denso del reale:")
        print("    le euristiche calibrate sul sintetico operano su una rete")
        print("    strutturalmente più connessa di quella reale di Fabriano.")
else:
    print("\n  → Gradi medi comparabili: la struttura è simile.")
print("=" * 58)
