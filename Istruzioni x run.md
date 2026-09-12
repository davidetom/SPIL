Ogni esecuzione di `_esegui_run` produce **3 CSV** (uno per gamma: 0.10, 0.50, 0.90). Ogni CSV contiene 2 algoritmi × 5 rifiuti × 12 valori X_r = 120 righe.

---

## Piano completo delle run

### Parametri fissi per tutte le analisi sintetiche

Questi non variano mai — sono la "rete stradale" del progetto:

- `n_max = 500` (grafo condiviso abbastanza grande ma veloce da generare)
- `r_factor = 1.2`
- Algoritmi: **entrambi** (`Invio`)
- Grafo a schermo: **no**

---

### ANALISI 1 — Variazione N (menu `[1]`)

**Una sola esecuzione**, che itera internamente su tutti gli N.

|Parametro|Valore|
|---|---|
|`n_max`|500|
|`seed`|42|
|`r_factor`|1.2|
|`N attivi`|`50, 100, 200, 350, 500`|
|Scenario tipologia|fisso: `residenziale`|
|Distribuzione|fisso: `uniforme`|
|Algoritmi|entrambi|

CSV prodotti: 5 N × 3 gamma = **15 CSV** Nomi: `risultati_50u_varN_Nmax500_Nact50_seed42_gamma0.10.csv` … fino a `_Nact500_…gamma0.90.csv`

---

### ANALISI 2 — Variazione Tipologia (menu `[2]`)

**Una sola esecuzione**, che itera su tutti gli scenari.

|Parametro|Valore|
|---|---|
|`n_users`|200|
|`n_max`|500|
|`seed`|42|
|`r_factor`|1.2|
|Scenari|`residenziale, suburbano, grandi_condomini, villette, misto_periferia` (tutti, premi Invio)|
|Distribuzione|fisso: `uniforme`|
|Algoritmi|entrambi|

CSV prodotti: 5 scenari × 3 gamma = **15 CSV** Nomi: `risultati_200u_tipo_residenziale_gamma0.10.csv` … `tipo_villette_gamma0.90.csv`

---

### ANALISI 3 — Variazione Distribuzione (menu `[3]`)

**Una sola esecuzione**, che confronta uniforme vs cluster.

|Parametro|Valore|
|---|---|
|`n_users`|200|
|`n_max`|500|
|`seed`|42|
|`r_factor`|1.2|
|Modalità|`3` (entrambe)|
|Scenario tipologia|fisso: `residenziale`|
|Algoritmi|entrambi|

CSV prodotti: 2 modalità × 3 gamma = **6 CSV** Nomi: `risultati_200u_distrib_uniform_gamma0.10.csv` … `distrib_cluster_gamma0.90.csv`

---

### ANALISI 4 — Mappa Reale Fabriano (menu `[4]`)

**Una sola esecuzione**. Non ha parametri configurabili: grafo e utenti vengono da `dati_reali/`, seed fisso a 42.

|Parametro|Valore|
|---|---|
|Grafo|`dati_reali/grafo_aumentato.graphml`|
|Utenti|`dati_reali/utenti.json` (~3932 utenti reali)|
|Algoritmi|entrambi|
|Grafo a schermo|no|

CSV prodotti: 3 gamma = **3 CSV** Nomi: `risultati_3932u_mappa_reale_gamma0.10.csv` … `_gamma0.90.csv`

⚠️ Questa è la run più pesante: ~3932 utenti con Dijkstra su grafo completo. Calcola i worker ottimali automaticamente. Stima: 10–40 minuti a seconda della macchina.

---

### ANALISI 5 — Standard (menu `[5]`)

**Tre esecuzioni separate**, una per seed, per la robustezza statistica che T1/T2 possono poi aggregare per media.

|Parametro|Run A|Run B|Run C|
|---|---|---|---|
|`n_users`|200|200|200|
|`seed`|42|123|7|
|`r_factor`|1.2|1.2|1.2|
|Scenario|`residenziale`|`residenziale`|`residenziale`|
|Algoritmi|entrambi|entrambi|entrambi|

CSV prodotti: 3 seed × 3 gamma = **9 CSV** Nomi: `risultati_200u_std_seed42_gamma0.10.csv` … `std_seed7_gamma0.90.csv`

---

### Riepilogo totale

|Analisi|Esecuzioni|CSV prodotti|
|---|---|---|
|B1 — Variazione N|1|15|
|B2 — Tipologia|1|15|
|B3 — Distribuzione|1|6|
|B4 — Mappa Reale|1|3|
|B5 — Standard (3 seed)|3|9|
|**Totale**|**7**|**48**|

T1 e T2 non richiedono run aggiuntive: leggono tutti i 48 CSV già prodotti.

---

### Ordine consigliato di esecuzione

1. **B5 Run A** (seed 42) — la più veloce, verifica che tutto funzioni prima di avviare le run lunghe
2. **B1** — richiede tempo (5 N × 3 gamma × 2 algoritmi)
3. **B2** e **B3** — parallelizzabili se hai due terminali
4. **B5 Run B e C** (seed 123 e 7)
5. **B4 Mappa Reale** — ultima, la più pesante, avviala quando non ti serve il PC