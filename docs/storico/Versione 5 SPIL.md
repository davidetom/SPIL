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

- $u \in U$:  Utente (nodo) del grafo cittadino.

- $v \in V_r$: Veicolo della flotta attiva.

### 2.2 Parametri

- $t_u$ : tipologia dell'utente u: single, famiglia, palazzina piccola, palazzina grande.

- $x^*_{ru}$: Frequenza ideale di ritiro settimanale per il rifiuto $r$.

- $W_{rt_u}$:​ Quantità totale settimanale stimata di rifiuto (waste) per l'utente u e il rifiuto r.

- $Q_{ru}(X_{r})$: Quantità stimata di volume di rifiuto $r$ che ci si aspetta ad ogni passaggio del camion prodotta dalla tipologia di utente $u$ $\rightarrow$ dipende dal numero di passaggi settimanali.

- $C_r$: Capacità massima di carico del veicolo che raccoglie $r$.

- $d_{ab}$: Distanza di viaggio dal nodo $a$ al nodo $b$.

- $tv_{ab}$: Tempo di viaggio dal nodo $a$ al nodo $b$.

- $tc_{rt_u}$: Tempo di carico per unità (svuotamento mastelli) presso l'utente $u$ per il rifiuto $r$.

- $\alpha$: Peso di penalità applicato in caso di sotto-servizio (mancato ritiro).

- $\beta$: Peso di penalità applicato in caso di sovra-servizio (ritiri in eccesso).

- $c_r$: Costo fisso di attivazione del veicolo adibito alla raccolta del rifiuto di tipo $r$.

- $cd, cm$: Costo unitario per distanza percorsa ($cd$) e costo orario della manodopera ($cm$).

- $L$: Durata turno di lavoro.

### 2.3 Variabili Decisionali 

- $X_{r} \in \mathbb{R} \rightarrow$ **Frequenza programmata:** variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).

- $V_{r} \in \mathbb{N} \rightarrow$ **Flotta attiva:** variabile intera $\ge 0$ che indica il numero totale di camion attivati per il rifiuto $r$.

- $P_{v} \rightarrow$ **Routing:** un vettore ordinato di nodi (lista) che rappresenta la sequenza di nodi del percorso effettuato dal veicolo $v$.

## 3. Funzione Obiettivo

$$F = \min \left\{ \sum_{r \in R} \sum_{u \in U} I_{ru} + \sum_{r \in R} (c_r \cdot V_{r} \cdot X_{r}) + \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} \sum_{(a,b) \in P_{v}} (cd \cdot d_{ab}) \right) + \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} cm \cdot T_{v} \right) \right\}$$

==INSODDISFAZIONE== + ==COSTO FISSO==  + ==COSTO DI VIAGGIO== + ==COSTO DEL LAVORO==

### 3.1 Funzione di Insoddisfazione

Si penalizza lo scostamento tra i ritiri programmati ($X_{r}$) e quelli desiderati ($x^*_{ru}$). La funzione di disservizio $I_{ru}$ punisce più severamente il sotto-servizio rispetto al sovra-servizio ($\alpha > \beta$).

$$I_{ru} = \begin{cases} \alpha \cdot (x^*_{ru} - X_{r}) & \text{se } X_{r} < x^*_{ru} \\ 0 & \text{se } X_{r} = x^*_{ru} \\ \beta \cdot (X_{r} - x^*_{ru}) & \text{se } X_{r} > x^*_{ru} \end{cases}$$
### 3.2 Tempo totale di attività per veicolo

Il tempo di attività totale del veicolo $v$ è dato dalla somma del tempo di viaggio su tutti gli archi del routing $P_{v}$ e del tempo di carico per tutti i mastelli degli utenti del routing $P_{v}$.

$$T_{v} = \sum_{(a,b) \in P_{v}} tv_{ab} + \sum_{u \in P_{v}} \left( tc_{rt_u} \cdot Q_{ru}(X_r) \right)$$
$Q_{ru}(X_{r}) = \frac{W_{rt_u}}{X_{r}}$: la quantità stimata di rifiuto $r$ che ci si aspetta ad ogni passaggio del camion prodotta dalla tipologia di utente $u$ dipende dalla quantità $W_{rt_u}$ ed è inversamente proporzionale al numero di passaggi settimanali $X_{r}$.
## 4. Vincoli di Sistema
### 4.1 Vincolo di Capacità dei Veicoli

Per ogni percorso, la somma delle stime di carico nei nodi visitati non deve superare la capacità del veicolo.

$$\sum_{u \in P_{v}} Q_{ru}(X_r) \le C_r \quad \forall v \in V_{r} , r \in R$$
### 4.2 Vincolo Temporale del Turno Lavorativo

La somma dei tempi di viaggio sugli archi del percorso e dei tempi di sosta (carico) nei nodi non deve eccedere la durata $L$ del turno lavorativo.

$$T_{v} \le L \quad \forall v \in V$$

## 5. Euristiche 
### Greedy
Si procede per comparti (si lavora inizialmente per un rifiuto alla volta):
- Si inizializza $X_{r} = 1$;
- Si inizializza $V_{r} = 1$;
- Si inizializza $P_{v} = \emptyset$;
For $u = 1; u \in U; u++$:

costruisce la soluzione passo dopo passo, compiendo la scelta localmente ottimale in ogni istante; si concentra sulla costruzione rapida dei percorsi $P_{v}$. 
Funzionamento:
1. per ogni rifiuto $r$, si imposta inizialmente la frequenza programmata $X_r$ in modo che sia uguale alla frequenza ideale $x^*_{ru}$. Questo porta immediatamente a zero la funzione di insoddisfazione $I_r$. 
2. Si attiva un veicolo $v$ ($V_r$ = 1) e lo si fa partire dal deposito.
3. Dal nodo corrente, l'algoritmo valuta tutti i nodi utente $u$ adiacenti non ancora visitati e seleziona quello con la distanza/tempo di viaggio ($tv_{ab}$) minore.

### Clarke-Wright (per routing) + Drop/Add (per esplorare curva Pareto)

### Clarke-Wright

Questa è una delle euristiche costruttive più famose e performanti per il Vehicle Routing Problem (VRP). Invece di partire dal deposito e cercare il nodo più vicino (come la Greedy), parte dall'ipotesi peggiore e cerca di "unire" i percorsi per risparmiare strada.

**Come funziona:**

- **Soluzione base (Pessimistica):** Si ipotizza inizialmente di usare un veicolo dedicato per ogni singolo utente u. Il veicolo parte dal deposito, serve l'utente e torna indietro.
    
- **Calcolo dei Risparmi (Savings):** Per ogni coppia di utenti (nodo a e nodo b), l'algoritmo calcola il "risparmio" di distanza NON SOLO, TUTTO (e quindi di costo cd) che si otterrebbe unendo i due utenti in un unico percorso, invece di servirli con due viaggi separati dal deposito.
    
- **Ordinamento e Fusione:** Si ordinano tutti i risparmi in modo decrescente (dal più grande al più piccolo).
    
- **Verifica dei Vincoli:** Seguendo l'elenco dei risparmi, si uniscono progressivamente i nodi nello stesso vettore di routing $P_{rv}$​. Prima di confermare l'unione, l'algoritmo deve verificare tassativamente che:
    
    - La somma dei carichi non superi la capacità $C_r$​.
        
    - Il tempo totale $T_v$​ (viaggio + tempi di carico $tc_{ru}$​) non superi la durata del turno L.
        
- **Chiusura:** Se i vincoli vengono violati, l'unione viene scartata e si passa alla coppia successiva. Questo processo continua fino a quando tutti i nodi sono assegnati, garantendo naturalmente il vincolo di copertura.

### Drop/Add

Mentre le altre euristiche si concentrano sul routing, questa è un'euristica di _miglioramento_ pensata esplicitamente per aggredire la tua funzione bi-obiettivo, lavorando sul compromesso tra costi aziendali e insoddisfazione $I_r$​.

**Come funziona:**

- **Inizializzazione a Massimo Servizio:** Si imposta la frequenza programmata $X_r​$ uguale alla frequenza ideale ρr​ per ogni rifiuto. Si calcola il routing con una delle euristiche precedenti. In questo momento, l'insoddisfazione per sotto-servizio è zero, ma i costi (flotta $N_r$​, distanza cd, lavoro ct) sono ai massimi livelli.
    
- **Fase di "Drop" (Taglio):** L'algoritmo prova a ridurre iterativamente di 1 la frequenza $X_r​$ per una specifica tipologia di rifiuto r.
    
- **Valutazione del Trade-off:** Riducendo $X_r​$​, l'algoritmo ricalcola l'intera funzione F. Da un lato, ci sarà un enorme risparmio sui costi operativi ($c_r \cdot ​N_r$​, meno chilometri, meno ore di lavoro). Dall'altro lato, scatterà la penalità α per il sotto-servizio.
    
- **Accettazione:** Se il nuovo valore della funzione obiettivo F è _minore_ del precedente (significa che il risparmio economico supera la penalità di insoddisfazione generata), la modifica della frequenza viene accettata in modo permanente.
    
- **Fase di "Add" (Aggiunta):** Similmente, si può testare l'aumento di $X_r​$​ oltre $\rho_r$​ se i costi operativi sono marginali rispetto al vantaggio di evitare sovra-accumuli (penalità $\beta$). L'algoritmo si ferma quando nessuna variazione di $X_r​$ ​riesce più a diminuire il valore totale di F.