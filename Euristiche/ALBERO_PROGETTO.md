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
│   ├── fig_gap_B1_B2.py             # Gap Greedy-CW vs N (B1) e per scenario (B2) a gamma=0.1, 0.5, 0.9
│   ├── fig_gap_vs_N.py              # Analisi dell'andamento del gap Greedy-CW su serie estese al variare di N
│   ├── fig_t1.py                    # Frontiere normalizzate costo-disservizio per 6 istanze di T1
│   ├── fig_t2.py                    # Figure T2: saturazioni V-X (Fabriano) e confronto camion/costo CW vs Greedy
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
│   ├── t1_generalita.py             # Verifica generalità risultati B4 sui benchmark (T1, test E1-E5)
│   ├── t2_profilo.py                # Profilo in X_r a frequenza fissata (T2, test P1-P4)
│   ├── test.py                      # Test di invarianza delle rotte e metriche globali
│   ├── test_addensamento.py         # Test indice Clark-Evans R vs fattore di scala r = km/sqrt(N*A)
│   ├── test_b4_gamma01.py           # Validazione comportamento B4 su gamma = 0.10
│   ├── test_csv_T3_T4.py            # Analisi delle scomposizioni T3 (gap) e T4 (tempi di viaggio)
│   ├── test_csv_greedy.py           # Confronto tra output di versioni successive dei CSV
│   ├── test_densita.py              # Calcolo densità areale e normalizzazione dei percorsi
│   ├── test_densita_sub.py          # Analisi densità sui sottocampioni di Fabriano
│   ├── test_due_fattori.py          # Scomposizione a due fattori (routing vs frequenza X*)
│   ├── test_gamma_postprocessing.py # Validazione della predizione a posteriori di gamma
│   ├── test_impacchettamento.py     # Verifica dei vincoli di capacità e saturazione dei veicoli
│   ├── test_impacchettamento_b4.py  # Verifica saturazione e carico per B4 reale
│   ├── test_nuovi_csv.py            # Verifica di regressione e integrità dei dati salvati
│   ├── test_profilo_gap.py          # Analisi di dettaglio del gap logistico su griglia X_r
│   ├── test_rotte.py                # Test di coerenza sulle rotte calcolate
│   ├── test_tempi.py                # Confronto sui tempi di calcolo Greedy vs Clarke-Wright
│   └── valida_seed42.py             # Validazione di conformità dei risultati su seed 42
│
├── algoritmo_ottimizzato/           # Proposta di ricerca potata della griglia di frequenze (T2)
│   ├── main_ottimizzato.py          # Ricerca potata: calcola F_ins a priori e instrada solo X <= X_min
│   └── test_ottimizzato.py          # Verifica di esattezza, riproducibilità (T1-T3) e benchmark tempi (T4)
│
├── risultati_ottimizzati/           # Output generati dalla ricerca potata
│   ├── potatura.csv                 # Punti di taglio X_min e numero di frequenze valutate per rifiuto
│   ├── righe.csv                    # Dettaglio rotte/costi delle soluzioni valutate (completa vs potata)
│   └── tempi.csv                    # Tempi di calcolo reali (wall) e CPU per algoritmo e tipo di ricerca
│
├── risultati_csv/                   # Output delle singole run sperimentali
│   └── (Contiene 48 file .csv: output dei benchmark B1-B5 su seed 42 con gamma = 0.10, 0.50, 0.90)
│
├── risultati_seed/                  # Output massivi dei benchmark multi-seed
│   └── (Contiene 1.260 file .csv: run complete per ciascun seed e benchmark B1, B1S, B1L, B1SL, B2, B3, B4sub, B5)
│
├── analisi_seed/                    # Risultati aggregati e figure generate dai batch multi-seed standard
│   ├── costo_marginale.csv          # Stime del trade-off economico marginale (€/disservizio evitato)
│   ├── gap_istanza.csv              # Gap calcolati per singola istanza
│   ├── metriche_istanza.csv         # Metriche di costo e disservizio per singola istanza
│   ├── plateau_istanza.csv          # Analisi di saturazione del gap
│   ├── riepilogo_gap.csv            # Sintesi del gap con intervalli di confidenza al 95%
│   ├── riepilogo_metriche.csv       # Medie e intervalli di confidenza di tutte le metriche
│   ├── riepilogo_plateau.csv        # Valori medi del gap a regime di tempo
│   ├── t1_E1.csv ... t1_E5_*.csv    # Tabelle numeriche generate dall'analisi di generalità T1
│   ├── t2_P1.csv ... t2_P4.csv      # Tabelle numeriche generate dall'analisi di profilo T2
│   └── (Contiene figure .png per la tesi: Pareto, profili X_r, gap vs N, regimi, algoritmi, etc.)
│
├── analisi_seed_estese/             # Risultati aggregati delle serie estese (B1L, B1SL, B4sub fino a N=4000)
│   ├── gap_istanza.csv              # Gap per le istanze estese
│   ├── metriche_istanza.csv         # Metriche per le istanze estese
│   ├── plateau_istanza.csv          # Plateau delle serie estese
│   ├── r_per_N.csv                  # Fattore di scala normalizzato r in funzione di N
│   ├── riepilogo_gap.csv            # Sintesi gap serie estese con IC95
│   ├── riepilogo_metriche.csv       # Sintesi metriche serie estese con IC95
│   ├── riepilogo_plateau.csv        # Plateau serie estese
│   ├── test_addensamento.csv        # Confronto indice Clark-Evans e fattore r
│   └── fig_gap_vs_N.png             # Grafico gap vs N log-scalato per le serie estese
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
Contiene gli script Python che leggono le metriche aggregate da `analisi_seed/`, `analisi_seed_estese/` o `risultati_seed/` e generano le figure ad alta risoluzione (300 DPI) per la tesi:
- **`fig_concetti.py`**: Relazioni concettuali $V-X$ e scomposizione del gap.
- **`fig_gap_B1_B2.py`**: Curve gap vs $N$ per B1 e gap a barre per gli scenari di B2 a $\gamma \in \{0.1, 0.5, 0.9\}$.
- **`fig_gap_vs_N.py`**: Andamento del gap sulle serie estese a confronto con Fabriano reale.
- **`fig_t1.py`**: Frontiere normalizzate costo-disservizio su 6 istanze rappresentative per l'analisi T1.
- **`fig_t2.py`**: Saturazioni temporale/fisica con soglie teoriche di regime e curve di vantaggio logistico per T2.
- **`figure_pareto.py`**: Curve di trade-off Pareto e profili delle metriche fisiche.

### 4. `script matlab/`
Contiene gli script MATLAB per le analisi statistiche descrittive dei singoli benchmark (da B1 a B5) e per le analisi trasversali (T1 su $\gamma$ e T2 sul profilo $X_r$). Ciascuno script legge i dati in modo relativo da `risultati_csv/`.

### 5. `testing/`
Raccoglie tutti gli script di esecuzione batch (`batch_seed.py`, `batch_fabriano.py`), gli script di analisi statistica e validazione:
- **`t1_generalita.py`**: Test di generalità delle evidenze di Fabriano sui benchmark sintetici (E1 grandezze adimensionali, E2 plateau, E3 dominanza a pari $\gamma$ e a pari $X_r$, E4 pendenza marginale, E5 soglie di cambio frequenza).
- **`t2_profilo.py`**: Analisi del profilo a frequenza fissata (P1 soglia capacità vs tempo, P2 unimodalità e ricerca a discesa, P3 sensibilità attorno a $X^*$, P4 confronto diretto Greedy vs Clarke-Wright).
- **`test_addensamento.py`**: Calcolo dell'indice spaziale di Clark-Evans $R$ su utenti reali e campioni uniformi sintetici per spiegare il decadimento del fattore $r = \text{km}/\sqrt{N \cdot A}$.
- Script di regressione, densità areale, impacchettamento e verifica coerenza rotte (`test_*.py`, `valida_seed42.py`).

### 6. `algoritmo_ottimizzato/`
Contiene la proposta metodologica di ottimizzazione computazionale (Benchmark Trasversale 2):
- **`main_ottimizzato.py`**: Esegue la ricerca con potatura a priori. Sfrutta il fatto che $F_{ins}(X_r)$ è indipendente dal routing e identifica $X_{min} = \arg\min F_{ins}$. Poiché per $X > X_{min}$ né il disservizio né i costi logistici diminuiscono, tali frequenze risultano dominate per qualsiasi $\gamma$ e vengono escluse dalla computazione VRP, risparmiando oltre il 60% delle chiamate di routing.
- **`test_ottimizzato.py`**: Validazione formale della ricerca potata (T1 verifica che il costo non cali oltre $X_{min}$, T2-T3 invarianza esatta delle soluzioni ottime rispetto ai dati completi, T4 quantificazione del risparmio di tempo reale e CPU).

### 7. `risultati_ottimizzati/`
Contiene gli output prodotti dall'esecuzione di `main_ottimizzato.py`:
- **`potatura.csv`**: Indici di taglio $X_{min}$ e numero di valutazioni effettive per ciascuna tipologia di rifiuto.
- **`righe.csv`**: Record dettagliati delle soluzioni valutate a confronto (ricerca completa vs potata).
- **`tempi.csv`**: Misurazioni dei tempi wall-clock e tempo CPU con conteggio dei worker paralleli.

### 8. `risultati_csv/`
Archivia **48 file CSV** corrispondenti ai risultati delle istanze deterministiche / benchmark principali con seed 42, calcolati su tre valori di compromesso sociale/economico ($\gamma \in \{0.10, 0.50, 0.90\}$).

### 9. `risultati_seed/`
Archivia **1.260 file CSV** prodotti dai lanci su griglie estese di semi casuali (30 seed per combinazione di scenario, tipologia, scala spaziale e algoritmo), utilizzati per l'analisi statistica a intervalli di confidenza (serie standard B1, B1S, B2, B3, B4sub, B5 e serie estese B1L, B1SL fino a 4.000 utenti).

### 10. `analisi_seed/` e `analisi_seed_estese/`
- **`analisi_seed/`**: Contiene i file CSV di riepilogo statistico (medie, deviazioni standard, intervalli di confidenza al 95%), i file di sintesi delle analisi T1 e T2 (`t1_*.csv`, `t2_*.csv`) e le relative figure salvate in formato PNG.
- **`analisi_seed_estese/`**: Archivia le aggregazioni statistiche specifiche per le serie ad alto numero di utenti (fino a $N=3.932$ per Fabriano e $N=4.000$ per sintetici), con i profili del fattore di scala $r$ e i test di addensamento spaziale.

### 11. `Generazione_grafo_Fabriano/`
Comprende l'intera pipeline geografica GIS/OSM: estrazione della mappa stradale di Fabriano, associazione degli edifici e generazione degli utenti geolocalizzati.

### 12. `grafi_png/` e `grafo_condiviso/`
- **`grafi_png/`**: Immagini rendering dei grafi generati e delle rotte calcolate.
- **`grafo_condiviso/`**: File binari (`.pkl`) dei grafi base sintetici pre-generati per velocizzare le esecuzioni multi-seed.
