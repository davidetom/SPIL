> Ciao! Ora che la logica matematica dei pesi (γ), del fattore di scala (Kscala​) e delle metriche di saturazione è perfettamente implementata, dobbiamo fare un refactoring di `main.py` e `Generazione_Dati.py` per strutturare gli esperimenti in modo rigoroso.
> 
> Il requisito principale è che le prime 3 analisi devono operare su un **singolo grafo stradale mock di base condiviso**, in modo che la rete stradale (le distanze e i tempi tra gli "incroci") sia identica per tutti i test. Solo gli utenti attivi cambieranno.
> 
> Ecco i requisiti precisi per il refactoring:
> 
> **1. Gestione del Grafo Condiviso (`Generazione_Dati.py`)**
> 
> - Crea una cartella `grafo_condiviso` (allo stesso livello degli script).
>     
> - Crea una nuova funzione `get_or_create_base_graph(n_max=500, seed=42, r_factor=1.2)`:
>     
>     - Controlla se nella cartella esiste un file salvato (es. `base_graph.pkl` usando la libreria `pickle`).
>         
>     - Se esiste, lo carica e lo restituisce.
>         
>     - Se non esiste, genera un set di coordinate `(n_max + 1, 2)`, chiama `_build_graph`, costruisce un dizionario con i dati del grafo base (`coords_base`, `dist_base`, `time_base`, `adj_base`, `edges_base`) e lo salva su disco prima di restituirlo.
>         
> 
> **2. Modifica di `generate_mock_data` (`Generazione_Dati.py`)** Modifica la firma e la logica interna affinché accetti un argomento opzionale `base_graph_dict`.
> 
> - Se `base_graph_dict` NON è fornito (Caso Standard), genera il grafo da zero normalmente (comportamento attuale).
>     
> - Se `base_graph_dict` E' fornito, salta la generazione di Delaunay/Dijkstra. Estrai il sottoinsieme di `n_users`nodi attivi (da `1` a `n_max`) in base alla stringa `spatial_mode` (di default a "uniform"):
>     
>     - se `"uniform"`: campiona casualmente `n_users` nodi tra gli `n_max` disponibili (usando un seed).
>         
>     - se `"cluster"` (Distribuzione aggregata/Centro città): scegli un centroide fisso al centro `[5,5]` nello spazio, calcola la distanza euclidea tra il centroide e tutti i nodi stradali del `base_graph`, e attiva gli `n_users` nodi più vicini al centroide.
>         
> - Ricostruisci le matrici `dist_matrix`, `time_matrix` estraendo le righe/colonne dei nodi attivati, ed emetti il dizionario di output SPIL.
>     
> 
> **3. Riordino e Refactoring del Menu (`main.py`)** Riordina le voci del menu principale così: `[1] Variazione Numero Utenti (N)` `[2] Variazione Tipologia Utenti` `[3] Variazione Distribuzione (Uniforme vs Aggregata al Centro)` `[4] Mappa Reale Fabriano``[5] Standard (Grafo generato da zero)` `[0] Esci`
> 
> **4. Logica delle Singole Analisi (`main.py`)**
> 
> - **Analisi 1, 2 e 3:** All'inizio della funzione corrispondente, chiama `get_or_create_base_graph()`. Passa il risultato come argomento a `generate_mock_data`.
>     
>     - L'Analisi 3 chiederà all'utente se testare distribuzione uniforme, aggregata (cluster) o entrambe, passando la corretta `spatial_mode` a `generate_mock_data`.
>         
> - **Analisi 4 (Fabriano):** Lasciala intatta.
>     
> - **Analisi 5 (Standard):** Chiama `generate_mock_data` senza passare il grafo base (così ne crea uno on-the-fly, utile per test veloci).
>     
> - **Regola ferrea per tutte le analisi:** Assicurati che TUTTE richiamino `_calcola_fattore_scala(data, waste_types)` per determinare il `k_scala` dinamico e poi utilizzino `_esegui_run` in modo che iteri ciclicamente gli scenari γ (Neutro, Pro-Azienda, Pro-Cittadino), preservando rigorosamente le stampe delle metriche di saturazione introdotte nel refactoring precedente.
>     
> 
> Procedi riscrivendo e fornendomi `Generazione_Dati.py` e `main.py` aggiornati. Assicurati che non venga toccata in alcun modo la logica di `Greedy.py` e `ClarkeWright.py`.