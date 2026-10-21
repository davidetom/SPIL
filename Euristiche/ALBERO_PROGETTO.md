# Struttura del Progetto Euristiche

Questo documento descrive l'organizzazione logica e l'albero delle directory e dei file del modulo `Euristiche/`.

---

## Albero delle Cartelle

```text
Euristiche/
│
├── ClarkeWright.py                  # Euristica Clarke-Wright Savings per VRP
├── Generazione_Dati.py              # Generazione scenari sintetici e caricamento dati reali
├── Greedy.py                        # Euristica Greedy per Vehicle Routing
├── main.py                          # Script principale di esecuzione e grid search
│
├── Generazione_grafo_Fabriano/      # Pipeline estrazione e preprocessing mappa reale di Fabriano
│   ├── map_osm.xml                  # Dati cartografici OpenStreetMap grezzi
│   ├── preprocessing_edifici.py     # Estrazione e filtraggio degli edifici
│   ├── preprocessing_rete.py        # Costruzione e pulizia del grafo stradale
│   ├── preprocessing_proiezione.py  # Proiezione degli edifici e utenti sulla rete
│   ├── schema.mat                   # Schema di supporto
│   └── dati_reali/                  # Dati elaborati pronti per le euristiche
│       ├── grafo_stradale.graphml   # Rete stradale filtrata
│       ├── grafo_aumentato.graphml  # Rete con connessioni deposito/utenze
│       ├── nodi_stradali.csv        # Coordinate dei nodi stradali
│       ├── archi_stradali.csv       # Distanze e tempi degli archi stradali
│       ├── edifici_candidati.csv    # Edifici identificati
│       ├── edifici_candidati.gpkg   # Layer geografico GeoPackage degli edifici
│       └── utenti.json              # Anagrafica e coordinate dei 3.932 utenti reali
│
├── grafo_condiviso/                 # Cache dei grafi base sintetici per replicabilità
│   └── (Contiene 3 file .pkl: grafi con N_max = 500, 1000, 5000 utenti su seed 42)
│
├── seeds/                           # Gestione dei seed di randomizzazione
│   └── seeds.json                   # Elenco ordinato dei seed utilizzati per i benchmark multi-run
│
├── generatori figure/               # Script dedicati alla generazione dei grafici per la tesi
│   ├── fig_concetti.py              # Grafici concettuali su relazioni V-X e scomposizione gap
│   ├── fig_gap_vs_N.py              # Analisi dell'andamento del gap Greedy-CW al variare di N
│   └── figure_pareto.py             # Curve di trade-off Pareto e profili delle metriche fisiche
│
├── script matlab/                   # Script MATLAB per analisi statistiche e figure
│   ├── Bench_1_VarN.m               # Benchmark 1: impatto della variazione del numero di utenti
│   ├── Bench_2_Tipologia.m          # Benchmark 2: impatto della tipologia abitativa
│   ├── Bench_3_Distribuzione.m      # Benchmark 3: impatto della distribuzione spaziale (cluster)
│   ├── Bench_4_Reale.m              # Benchmark 4: scenario su mappa reale di Fabriano
│   ├── Bench_5_Standard.m           # Benchmark 5: caso standard di riferimento
│   ├── T1_gammaTradeOff.m           # Analisi trasversale del parametro di compromesso gamma
│   └── T2_profiloXr.m               # Analisi del profilo di costo al variare della frequenza X_r
│
├── testing/                         # Script di test, batch di simulazione e validazione
│   ├── batch_seed.py                # Esecutore batch su benchmark sintetici B1-B5 e multi-seed
│   ├── batch_fabriano.py            # Esecutore batch su campionamenti di Fabriano (B4sub, B1S)
│   ├── riepilogo.py                 # Stampa tabelle riassuntive da terminale
│   ├── test.py                      # Test di invarianza delle rotte e metriche globali
│   ├── test_csv_T3_T4.py            # Analisi delle scomposizioni T3 (gap) e T4 (tempi di viaggio)
│   ├── test_csv_greedy.py           # Confronto tra output di versioni successive dei CSV
│   ├── test_densita.py              # Calcolo densità areale e normalizzazione dei percorsi
│   ├── test_densita_sub.py          # Analisi densità sui sottocampioni di Fabriano
│   ├── test_due_fattori.py          # Scomposizione a due fattori (routing vs frequenza X*)
│   ├── test_gamma_postprocessing.py # Validazione della predizione a posteriori di gamma
│   ├── test_impacchettamento.py     # Verifica dei vincoli di capacità e saturazione dei veicoli
│   ├── test_nuovi_csv.py            # Verifica di regressione e integrità dei dati salvati
│   ├── test_profilo_gap.py          # Analisi di dettaglio del gap logistico su griglia X_r
│   ├── test_rotte.py                # Test di coerenza sulle rotte calcolate
│   ├── test_tempi.py                # Confronto sui tempi di calcolo Greedy vs Clarke-Wright
│   └── valida_seed42.py             # Validazione di conformità dei risultati su seed 42
│
├── risultati_csv/                   # Output delle singole run sperimentali
│   └── (Contiene 48 file .csv: output dei benchmark B1-B5 su seed 42 con gamma = 0.10, 0.50, 0.90)
│
├── risultati_seed/                  # Output massivi dei benchmark multi-seed
│   └── (Contiene oltre 660 file .csv: run complete per ciascun seed e benchmark B1, B1S, B2, B3, B4sub, B5)
│
├── analisi_seed/                    # Risultati aggregati e figure generate dai batch multi-seed
│   ├── costo_marginale.csv          # Stime del trade-off economico marginale (€/disservizio evitato)
│   ├── gap_istanza.csv              # Gap calcolati per singola istanza
│   ├── metriche_istanza.csv         # Metriche di costo e disservizio per singola istanza
│   ├── plateau_istanza.csv          # Analisi di saturazione del gap
│   ├── riepilogo_gap.csv            # Sintesi del gap con intervalli di confidenza al 95%
│   ├── riepilogo_metriche.csv       # Medie e intervalli di confidenza di tutte le metriche
│   ├── riepilogo_plateau.csv        # Valori medi del gap a regime di tempo
│   └── (Contiene 12 figure .png generate per la tesi: Pareto, profili X_r, gap vs N, etc.)
│
└── grafi_png/                       # Esportazioni grafiche delle reti e dei grafi
    └── (Contiene 8 file .png: visualizzazioni delle mappe sintetiche e reali con rotte)
```

---

## Descrizione delle Cartelle

### 1. Root (`/`)
Contiene i quattro file Python fondamentali che implementano il modello di ottimizzazione e la generazione delle istanze:
- **`ClarkeWright.py`**: Algoritmo euristico per il Vehicle Routing Problem basato sulla matrice dei risparmi (*savings*).
- **`Greedy.py`**: Algoritmo euristico greedy basato sulla ricerca del vicino più prossimo con vincoli di capacità fisica e temporale.
- **`Generazione_Dati.py`**: Modulo per la generazione probabilistica della domanda, matrice distanze/tempi e scenari di densità.
- **`main.py`**: Entry-point per eseguire griglie di test e confronto tra le euristiche.

### 2. `seeds/`
Contiene il file JSON [`seeds.json`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/Euristiche/seeds/seeds.json) con la sequenza di seed di randomizzazione impiegati per garantire la riproducibilità di tutti i test stocastici.

### 3. `generatori figure/`
Contiene gli script Python che leggono le metriche aggregate da `analisi_seed/` o `risultati_seed/` e generano le figure ad alta risoluzione (300 DPI) utilizzate nella tesi.

### 4. `script matlab/`
Contiene gli script MATLAB per le analisi statistiche descrittive dei singoli benchmark (da B1 a B5) e per le analisi trasversali (T1 su $\gamma$ e T2 sul profilo $X_r$). Ciascuno script legge i dati in modo relativo da `risultati_csv/`.

### 5. `testing/`
Raccoglie tutti gli script di esecuzione batch (`batch_seed.py`, `batch_fabriano.py`) e gli script di validazione, regressione, calcolo densità e test di robustezza.

### 6. `risultati_csv/`
Archivia **48 file CSV** corrispondenti ai risultati delle istanze deterministiche / benchmark principali con seed 42, calcolati su tre valori di compromesso sociale/economico ($\gamma \in \{0.10, 0.50, 0.90\}$).

### 7. `risultati_seed/`
Archivia **oltre 660 file CSV** prodotti dai lanci su griglie estese di semi casuali (30 seed per combinazione di scenario, tipologia, scala spaziale e algoritmo), utilizzati per l'analisi statistica a intervalli di confidenza.

### 8. `analisi_seed/`
Contiene i file CSV di riepilogo statistico (medie, deviazioni standard, intervalli di confidenza al 95% calcolati con la $t$ di Student) e le relative figure salvate in formato PNG.

### 9. `Generazione_grafo_Fabriano/`
Comprende l'intera pipeline geografica GIS/OSM: estrazione della mappa stradale di Fabriano, associazione degli edifici e generazione degli utenti geolocalizzati.

### 10. `grafi_png/` e `grafo_condiviso/`
- **`grafi_png/`**: Immagini rendering dei grafi generati e delle rotte calcolate.
- **`grafo_condiviso/`**: File binari (`.pkl`) dei grafi base sintetici pre-generati per velocizzare le esecuzioni multi-seed.
