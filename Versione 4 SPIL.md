# Progetto di Ottimizzazione Bi-Obiettivo: Logistica della Raccolta Differenziata

## 1. Introduzione

Il progetto affronta il problema dell'ottimizzazione della raccolta differenziata in un contesto urbano. 
L'approccio non si basa sulla sola minimizzazione delle distanze, ma prende in considerazione anche la qualità del servizio percepita dal cittadino.

L'algoritmo **decide proattivamente** la pianificazione settimanale (frequenze, veicoli attivi e routing), bilanciando due forze contrapposte:

1. **L'impatto sociale:** minimizzare l'insoddisfazione dell'utente, misurata come scostamento dalla frequenza di ritiro ideale (che varia in base alla tipologia di rifiuto).

2. **L'efficienza logistica:** minimizzare i costi operativi aziendali, composti dall'attivazione dei mezzi, dal consumo di carburante lungo i percorsi e dalle ore di lavoro degli operatori.

## 2. Legenda e Notazione Matematica

### 2.1 Indici e insiemi

- $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.

- $u \in U$: Singolo utente o cluster per palazzine (nodo della rete).

- $v \in V_{r}$: Veicolo appartenente alla flotta aziendale dedicata alla raccolta della tipologia di rifiuto $r$.

- $V = \sum_{r \in R}V_{r}$: Flotta aziendale complessiva.

### 2.2 Parametri

- G($\Lambda$, E): grafo cittadino.

- $U$: insieme di utenti, all'indice u ci sarà la tipologia di quell'utente (single, famiglia, palazzina).

- $\rho_{r}$: Frequenza ideale (ritiri settimanali desiderati/ideali) per il rifiuto $r$.

- $Q_{ru}$: Quantità stimata (volume/peso) di rifiuto $r$ prodotta dalla tipologia di utente $u$. 

- $C_r$: Capacità massima di carico del veicolo che raccoglie $r$.

- $D$: Matrice coppie (distanze, tempi di viaggio) = ($d_{ab}$, $t_{ab}$) $\forall  (a,b)  \in E$

- $tv_{ab}$: Tempo di viaggio dal nodo $a$ al nodo $b$.

- $tc_{ru}$: Tempo di carico per unità (svuotamento mastelli) presso l'utente $u$ per il rifiuto $r$. tempo di carico dipende dal tipo di rifiuto e dal tipo di utente.

- $\alpha$: Peso di penalità applicato in caso di sotto-servizio (mancato ritiro).

- $\beta$: Peso di penalità applicato in caso di sovra-servizio (ritiri in eccesso).

- $c_r$: Costo fisso di attivazione del veicolo adibito alla raccolta del rifiuto di tipo $r$.

- $cd, ct$: Costo unitario per distanza percorsa ($cd$) e costo orario della manodopera ($ct$).

- $L$: Durata turno di lavoro.

### 2.3 Variabili Decisionali 

- $X_{r} \in \mathbb{R}$: **Frequenza programmata.** Variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).

- $N_{r} \in \mathbb{N}$: **Flotta attiva.** Variabile intera $\ge 0$ che indica il numero totale di camion attivati per il rifiuto $r$.

- $P_{rv}$: **Percorso (Routing).** Un vettore ordinato di nodi (lista) che rappresenta la sequenza di nodi del percorso effettuato dal veicolo $v$.

## 3. Funzione Obiettivo

$$F = \min \left\{ \sum_{r \in R} \sum_{u \in U} I_{r} + \sum_{r \in R} (c_r \cdot N_{r} \cdot X_{r}) + \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} \sum_{(a,b) \in P_{rv}} (cd \cdot d_{ab}) \right) + \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} ct \cdot T_{v} \right) \right\}$$

==INSODDISFAZIONE== + ==COSTO FISSO==  + ==COSTO DI VIAGGIO== + ==COSTO DEL LAVORO==

### 3.1 Funzione di Insoddisfazione

Si penalizza lo scostamento tra i ritiri programmati ($X_{r}$) e quelli desiderati ($\rho_{ru}$). La funzione di disservizio $I_{ru}$ punisce più severamente il sotto-servizio rispetto al sovra-servizio ($\alpha > \beta$).

$$I_{r} = \begin{cases} \alpha \cdot (\rho_{r} - X_{r}) & \text{se } X_{r} < \rho_{r} \\ 0 & \text{se } X_{r} = \rho_{r} \\ \beta \cdot (X_{r} - \rho_{r}) & \text{se } X_{r} > \rho_{r} \end{cases}$$

### 3.2 Tempo totale di attività per veicolo

Il tempo di attività totale del veicolo $v$ è dato dalla somma del tempo di viaggio su tutti gli archi del routing $P_{v}$ e del tempo di carico per tutti i mastelli degli utenti del routing $P_{v}$.

$$T_{v} = \sum_{(a,b) \in P_{rv}} tv_{ab} + \sum_{u \in P_{rv}} \left( tc_{ru} \cdot Q_{ru} \right)$$
## 4. Vincoli di Sistema

I vincoli fisici e temporali vengono valutati direttamente sugli elementi contenuti all'interno dei vettori di routing $P_{rv}$.

### 4.1 Vincolo di Capacità dei Veicoli

Per ogni percorso, la somma delle stime di carico nei nodi visitati non deve superare la capacità del veicolo.

$$\sum_{u \in P_{rv}} Q_{ru} \le C_r \quad \forall r \in R, v \in V$$

### 4.2 Vincolo Temporale del Turno Lavorativo

La somma dei tempi di viaggio sugli archi del percorso e dei tempi di sosta (carico) nei nodi non deve eccedere la durata $L$ del turno lavorativo.

$$T_{v} \le L \quad \forall v \in V$$

# Dubbi

## 1. Copertura delle Utenze e Vincoli di Servizio

Lei ci ha consigliato di considerare un routing fisso e uguale per tutti i giorni di raccolta di una specifica tipologia di rifiuto (es. stesso percorso tutti i giorni per la plastica, stesso per la carta).
In questo modo però se un utente viene mancato dal routing questo non verrà mai servito...

Se adottiamo questo approccio di routing fisso, per evitare che l'algoritmo salti alcuni utenti (e quindi faccia in modo che quegli utenti non vengano mai serviti) , è necessario introdurre un vincolo di copertura di tutti i nodi?

### Vincolo di copertura

L'unione dei nodi di tutti i routing dei camion adibiti ad un tipo di rifiuto deve essere uguale all'insieme degli utenti, e questa relazione deve valere per tutti i tipi di rifiuto:
$$ \bigcup_{v \in V_{r}} \{ u_i \in P_{rv} \} = U \quad \forall r \in R $$

## 5. Euristiche 

Un'euristica è una strategia di risoluzione dei problemi che rinuncia a cercare la soluzione ottima in cambio di una soluzione buona trovata in tempi rapidi.

Nel nostro progetto è necessario, infatti, l'uso delle euristiche, in quanto in numero di combinazioni possibili da esplorare cresce esponenzialmente all'aumentare dei nodi sulla mappa e non è calcolabile in tempi utili.

L'algoritmo che cerchiamo deve decidere proattivamente la pianificazione per l'azienda, che ha bisogno di un piano logistico pronto in poco tempo senza aspettare mesi di calcoli per risparmiare piccole somme di denaro.

### Greedy

Nearest Neighbor con Vincoli Capacitivi e Temporali:
costruisce la soluzione passo dopo passo, compiendo la scelta localmente ottimale in ogni istante; si concentra sulla costruzione rapida dei percorsi $P_{rv}$. 
Funzionamento:
1. per ogni rifiuto $r$, si imposta inizialmente la frequenza programmata $X_r$ in modo che sia uguale alla frequenza ideale $\rho_{r}$. Questo porta immediatamente a zero la funzione di insoddisfazione $I_r$. 
2. Si attiva un veicolo $v$ ($N_r$ = 1) e lo si fa partire dal deposito.
3. Dal nodo corrente, l'algoritmo valuta tutti i nodi utente $u$ non ancora visitati e seleziona quello con la distanza/tempo di viaggio ($tv_ab$)

### Clarke-Wright (per routing) + Drop/Add (per esplorare curva Pareto)

### Clarke-Wright

Questa è una delle euristiche costruttive più famose e performanti per il Vehicle Routing Problem (VRP). Invece di partire dal deposito e cercare il nodo più vicino (come la Greedy), parte dall'ipotesi peggiore e cerca di "unire" i percorsi per risparmiare strada.

**Come funziona:**

- **Soluzione base (Pessimistica):** Si ipotizza inizialmente di usare un veicolo dedicato per ogni singolo utente u. Il veicolo parte dal deposito, serve l'utente e torna indietro.
    
- **Calcolo dei Risparmi (Savings):** Per ogni coppia di utenti (nodo a e nodo b), l'algoritmo calcola il "risparmio" di distanza (e quindi di costo cd) che si otterrebbe unendo i due utenti in un unico percorso, invece di servirli con due viaggi separati dal deposito.
    
- **Ordinamento e Fusione:** Si ordinano tutti i risparmi in modo decrescente (dal più grande al più piccolo).
    
- **Verifica dei Vincoli:** Seguendo l'elenco dei risparmi, si uniscono progressivamente i nodi nello stesso vettore di routing Prv​. Prima di confermare l'unione, l'algoritmo deve verificare tassativamente che:
    
    - La somma dei carichi non superi la capacità Cr​.
        
    - Il tempo totale Tv​ (viaggio + tempi di carico tcru​) non superi la durata del turno L.
        
- **Chiusura:** Se i vincoli vengono violati, l'unione viene scartata e si passa alla coppia successiva. Questo processo continua fino a quando tutti i nodi sono assegnati, garantendo naturalmente il vincolo di copertura.

### Drop/Add

Mentre le altre euristiche si concentrano sul routing, questa è un'euristica di _miglioramento_ pensata esplicitamente per aggredire la tua funzione bi-obiettivo, lavorando sul compromesso tra costi aziendali e insoddisfazione Ir​.

**Come funziona:**

- **Inizializzazione a Massimo Servizio:** Si imposta la frequenza programmata Xr​ uguale alla frequenza ideale ρr​ per ogni rifiuto. Si calcola il routing con una delle euristiche precedenti. In questo momento, l'insoddisfazione per sotto-servizio è zero, ma i costi (flotta Nr​, distanza cd, lavoro ct) sono ai massimi livelli.
    
- **Fase di "Drop" (Taglio):** L'algoritmo prova a ridurre iterativamente di 1 la frequenza Xr​ per una specifica tipologia di rifiuto r.
    
- **Valutazione del Trade-off:** Riducendo Xr​, l'algoritmo ricalcola l'intera funzione F. Da un lato, ci sarà un enorme risparmio sui costi operativi (cr​⋅Nr​, meno chilometri, meno ore di lavoro). Dall'altro lato, scatterà la penalità α per il sotto-servizio.
    
- **Accettazione:** Se il nuovo valore della funzione obiettivo F è _minore_ del precedente (significa che il risparmio economico supera la penalità di insoddisfazione generata), la modifica della frequenza viene accettata in modo permanente.
    
- **Fase di "Add" (Aggiunta):** Similmente, si può testare l'aumento di Xr​ oltre ρr​ se i costi operativi sono marginali rispetto al vantaggio di evitare sovra-accumuli (penalità β). L'algoritmo si ferma quando nessuna variazione di Xr​riesce più a diminuire il valore totale di F.