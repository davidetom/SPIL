### 1. La Funzione Obiettivo e la Normalizzazione (main.py)
Poiché l'insoddisfazione degli utenti ($F_{insoddis}$) e i costi operativi ($F_{costi} = F_{costo\_fisso} + F_{viaggio} + F_{lavoro}$) hanno ordini di grandezza e unità di misura completamente diversi, non possono essere sommati direttamente. 

Il sistema risolve questo problema con una **combinazione convessa normalizzata**:
1. **Run Esplorativa:** Il `main.py` esegue una prima simulazione "neutra" per calcolare i valori medi di insoddisfazione (`scala_ins`) e dei costi (`scala_cost`).
2. **Weighted Score:** Nei file `Greedy.py` e `ClarkeWright.py` (nella funzione `weighted_score`), la funzione obiettivo totale valutata per scegliere la soluzione migliore diventa:
   $$F_{tot} = \alpha \cdot \left(\frac{F_{insoddis}}{\text{scala\_ins}}\right) + (1 - \alpha) \cdot \left(\frac{F_{costi}}{\text{scala\_cost}}\right)$$
 
 I parametri `scala_ins` e dei costi `scala_cost` vengono calcolati facendo la **media aritmetica** rispettivamente tra la somma dei valori dell'insoddisfazione per tutti i rifiuti e la somma dei valori dei costi per tutti i rifiuti:
*   **`scala_ins`** = `sum(ins_vals) / len(ins_vals)`   
*   **`scala_cost`** = `sum(cost_vals) / len(cost_vals)`

### 2. L'Impatto di $\alpha$ sugli Algoritmi (Costruzione Rotte)
Un aspetto matematico fondamentale dell'implementazione è che **a parità di frequenza di raccolta ($X_r$)**, il parametro $\alpha$ **non altera la forma delle rotte** costruite dai due algoritmi.

*   **Nel Greedy.py:** La penalità per l'inserimento di un nodo o l'apertura di un nuovo veicolo è proporzionale ai costi di routing moltiplicati per $\frac{1-\alpha}{\text{scala\_cost}}$. Poiché questo è un moltiplicatore costante per un dato $\alpha$, l'ordinamento relativo dei costi marginali (il `best_option_cost`) non cambia. Il Greedy farà sempre le stesse scelte di inserimento.
*   **Nel ClarkeWright.py:** La matrice dei risparmi (Savings `S`) viene scalata dallo stesso fattore moltiplicativo. Di conseguenza, l'ordine dei risparmi (l'`argsort` in fase 3) e il taglio dei risparmi negativi rimangono identici. Le rotte fuse saranno le stesse.

### 3. Il Vero Ruolo di $\alpha$: La scelta della Frequenza $X_r$ (Grid Search)
$\alpha$ non cambia le rotte a parità di $X_r$, **ma gisce nella Grid Search**, per la scelta finale della frequenza ottima da adottare per un dato rifiuto.

Dato che $F_{insoddis}$ dipende esclusivamente dalla differenza tra la frequenza imposta $X_r$ e le frequenze desiderata degli utenti ($x^*$), il bilanciamento guidato da $\alpha$ decide quale configurazione far vincere:

*   **Scenario A (Bilanciato, $\alpha = 0.50$):** Cerca il compromesso perfetto. Accetta una lieve insoddisfazione se permette di risparmiare un intero camion, ma non sacrifica gli utenti per risparmiare pochi chilometri.
*   **Scenario B (Pro-Costi, $\alpha = 0.15$):** Il peso preponderante $(1-\alpha) = 0.85$ è sui costi. La Grid Search tenderà a scegliere un $X_r$ basso e molto efficiente logisticamente (pienamente saturato, meno camion), ignorando quasi del tutto se questo genera una forte penalità di insoddisfazione negli utenti.
*   **Scenario C (Pro-Insoddisfazione, $\alpha = 0.95$):** Il costo logistico diventa quasi irrilevante. La Grid Search sceglierà un $X_r$ altissimo che ricalca il più possibile le frequenze ideali degli utenti $x^*$, anche se questo significa far viaggiare molti camion semi-vuoti e far esplodere $F_{costi}$.

**In sintesi:** I due algoritmi euristicamente si occupano di trovare sempre la *migliore logistica possibile* per un dato $X_r$, mentre il parametro $\alpha$ interviene come "decisore politico" finale che confronta i risultati per i vari $X_r$ e decreta il vincitore tra il benessere del cittadino e il budget dell'azienda.

### Perché questo approccio è fondamentale?
Senza questa normalizzazione empirica, i costi operativi (che possono facilmente ammontare a migliaia di euro tra benzina, usura e stipendi) "schiaccerebbero" matematicamente l'insoddisfazione (che invece è un punteggio astratto tipicamente molto più basso in valore assoluto). 

Dividendo ogni componente per la sua rispettiva media generata dalla run esplorativa, le due grandezze diventano **adimensionali e normalizzate intorno al valore 1**. A questo punto:
*   $\frac{F_{insoddis}}{\text{scala\_ins}}$ vale circa $1$ per una soluzione "nella media".
*   $\frac{F_{costi}}{\text{scala\_cost}}$ vale circa $1$ per una soluzione "nella media".

Solo con questo bilanciamento preliminare la combinazione convessa ha senso, permettendo al parametro $\alpha \in [0, 1]$ di comportarsi come un vero e proprio "selettore percentuale" tra le due priorità, senza essere distorto dalle unità di misura sottostanti.

## Bilanciamento alternativo della Funzione Obiettivo

- La funzione obiettivo su cui stiamo lavorando è composta da due parametri fondamentali: i costi e l'insoddisfazione degli utenti.

- Va messo a confronto l'ottimo di un termine con l'ottimo dell'altro per valutare a chi viene dato maggior valore mediamente dai due algoritmi.

- È assolutamente necessario bilanciare i due termini per evitare che uno "schiacci" l'altro a causa di ordini di grandezza o unità di misura completamente diversi (ad esempio, se l'insoddisfazione vale 10 e i costi valgono 1000, l'algoritmo minimizzerà solo i costi ignorando il resto).

- Prima di assegnare dei pesi definitivi, vanno effettuati dei lanci di prova (istanze) senza pesi per capire quanto valgono numericamente i costi e l'insoddisfazione in termini assoluti.

- Successivamente, vanno applicati dei fattori di conversione (moltiplicando o dividendo, ad esempio dividendo i costi per 100) in modo da portare i due termini a un peso paragonabile (es. 1 a 1).

- Una volta bilanciata la funzione di base, vanno testati tre diversi scenari di pesi: dare lo stesso valore a entrambi i termini, dare maggiore importanza ai costi, oppure dare maggiore importanza all'insoddisfazione.


### 4. L'Utilizzo dei Camion

- Valutare quanto viene utilizzato il camion rispetto alla sua capacità totale.
- Questa analisi deve considerare due aspetti distinti: la capacità fisica (quanto effettivamente è pieno il veicolo) e la capacità temporale (quanto viene impiegato sul tempo totale a disposizione).

## Simulazioni e Test sul Grafo

- Il grafo della rete (che sia un paese reale o una griglia generata su Matlab) deve rimanere fisso durante le simulazioni.
- Vanno variati i parametri di input, come il numero totale dei clienti, la tipologia, ...?