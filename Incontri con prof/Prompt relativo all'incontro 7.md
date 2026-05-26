Ciao! Devo modificare la mia codebase (main.py, Greedy.py, ClarkeWright.py) per implementare un sistema di bilanciamento della Funzione Obiettivo tramite run di prova e l'esecuzione di 3 scenari politici (tramite un parametro `gamma`), oltre a tracciare la saturazione dei veicoli. Partiamo dalla codebase vergine allegata.

Ecco i requisiti architetturali:

**1. La Logica della Run di Prova e del parametro Kscala​ (`main.py`)** Ogni volta che si definisce una nuova istanza (dati generati o caricati), e prima di eseguire le analisi finali, crea una funzione `_calcola_fattore_scala(data, waste_types)` che:

- Esegue una Grid Search rapida usando solo l'algoritmo Greedy con parametri "neutri" (`gamma=0.5`, `k_scala=1.0`).
    
- Raccoglie tutti i valori base di Finsoddis​ e Fcosti​ (somma di costo fisso, viaggio e lavoro) per tutti i rifiuti e per tutti i valori di Xr​.
    
- Calcola Kscala​= $$ \frac{\sum_{r \in Rifiuti} F_{costi}}{\sum_{r \in Rifiuti} F_{insoddisfazione}}​ $$

**2. Modifica della Funzione Obiettivo e Logica Interna (`Greedy.py` e `ClarkeWright.py`)**

- Aggiungi i parametri opzionali `gamma` (default 0.5) e `k_scala` (default 1.0) alle funzioni `grid_search`, `compute_objective` e, **fondamentale**, a `build_routes` nel Greedy.
    
- Il calcolo finale in `compute_objective` deve essere: Ftot​=γ⋅(Finsoddis​⋅Kscala​)+(1−γ)⋅(Fcosti​)
    
- **Nel `Greedy.py` (Logica interna):** La professoressa richiede che la funzione obiettivo _completa_ venga valutata a ogni passo. Pertanto, la variabile `f_partial` (o il calcolo di `fo` e `fo_new`) deve inizializzarsi includendo la componente dell'insoddisfazione pesata e scalata: γ⋅(Finsoddis​⋅Kscala​). Ogni volta che aggiungi un costo logistico (inserimento o nuovo veicolo), quel costo logistico deve essere moltiplicato per (1−γ).
    
- **Nel `ClarkeWright.py`:** Poiché si basa sui risparmi (Savings = Costo A + Costo B - Costo AB), l'insoddisfazione si elide matematicamente dalla matrice S. Pertanto, scala semplicemente la matrice dei savings moltiplicandola per (1−γ) per coerenza formale.
    

**3. Metriche di Saturazione Camion (`Greedy.py` e `ClarkeWright.py`)** Le funzioni `build_routes` restituiscono già liste per `loads` e `times`. Fai in modo che `compute_objective` calcoli e aggiunga al dizionario di output la saturazione media percentuale:

- `sat_fisica_media`: (Somma di tutti i `loads` / (Numero camion * Capacità Massima Cr​)) * 100
    
- `sat_tempo_media`: (Somma di tutti i `times` / (Numero camion * Limite Lavorativo L)) * 100 _(Gestisci accuratamente le divisioni per zero)._
    

**4. Esecuzione Multi-Scenario (`main.py`)** Modifica `_esegui_run` in modo che:

1. Riceva `k_scala` calcolato in precedenza.
    
2. Esegua automaticamente gli algoritmi scelti per **3 scenari sequenziali**:
    
    - **Neutro:** `gamma = 0.50`
        
    - **Pro-Azienda:** `gamma = 0.1` (priorità ai costi, peso insoddisfazione basso)
        
    - **Pro-Cittadino:** `gamma = 0.9` (priorità all'insoddisfazione, peso costi basso)
        
3. Stampi un riepilogo a console raggruppato per scenario, includendo nei log il numero di camion e le due nuove percentuali di saturazione. I CSV generati dovranno avere nel nome l'indicazione dello scenario (es. `_gamma0.50.csv`).

Procedi fornendomi il codice aggiornato, senza dirmi "sostituisci questa riga" ma passandomi direttamente le intere funzioni modificate, mostrando chiaramente dove avvengono i cambiamenti e come hai aggiornato le formule.