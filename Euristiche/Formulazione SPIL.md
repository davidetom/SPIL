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

- $W_{rt_u}$:​ Quantità totale settimanale stimata di rifiuto (waste) per l'utente u e il rifiuto r. (per tipologia di utente $t_u$ e il rifiuto $r$).

- $Q_{ru}(X_{r})$: Quantità stimata di volume di rifiuto $r$ che ci si aspetta ad ogni passaggio del camion prodotta dalla tipologia di utente $u$ $\rightarrow$ dipende dal numero di passaggi settimanali.

- $C_r$: Capacità massima di carico del veicolo che raccoglie $r$.

- $d_{ab}$: Distanza di viaggio dal nodo $a$ al nodo $b$.

- $tv_{ab}$: Tempo di viaggio dal nodo $a$ al nodo $b$.

- $tc_{rt_u}$: Tempo di carico per unità (svuotamento mastelli) presso l'utente $u$ per il rifiuto $r$. (tipologia di utente tu)

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

$$F = \min \left\{ ...\sum_{r \in R} \sum_{u \in U} I_{ru} + ... \right\}$$
*Legenda*:
 - $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.
 - $u \in U$:  Utente (nodo) del grafo cittadino.

Si penalizza lo scostamento tra i ritiri programmati ($X_{r}$) e quelli desiderati ($x^*_{ru}$). La funzione di disservizio $I_{ru}$ punisce più severamente il sotto-servizio rispetto al sovra-servizio ($\alpha > \beta$).

$$I_{ru} = \begin{cases} \alpha \cdot (x^*_{ru} - X_{r}) & \text{se } X_{r} < x^*_{ru} \\ 0 & \text{se } X_{r} = x^*_{ru} \\ \beta \cdot (X_{r} - x^*_{ru}) & \text{se } X_{r} > x^*_{ru} \end{cases}$$
### 3.2 Costo Fisso

$$F = \min \left\{ ...+ \sum_{r \in R} (c_r \cdot V_{r} \cdot X_{r}) + ... \right\}$$
*Legenda*:
 - $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.
 - $c_r$: Costo fisso di attivazione del veicolo adibito alla raccolta del rifiuto di tipo $r$.
 - $V_{r} \in \mathbb{N} \rightarrow$ **Flotta attiva:** variabile intera $\ge 0$ che indica il numero totale di camion attivati per il rifiuto $r$.
 - $X_{r} \in \mathbb{R} \rightarrow$ **Frequenza programmata:** variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).

Nella funzione obiettivo il Costo Fisso è espresso come la moltiplicazione del costo fisso del veicolo della tipologia di rifiuto r per il numero totale di camion attivati per il rifiuto r, per il numero di ritiri programmati per il rifiuto r, eseguita per ogni tipologia di rifiuto.

### 3.3 Costo di Viaggio

$$F = \min \left\{...+ \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} \sum_{(a,b) \in P_{v}} (cd \cdot d_{ab}) \right) + ... \right\}$$
*Legenda*:
 - $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.
 - $X_{r} \in \mathbb{R} \rightarrow$ **Frequenza programmata:** variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).
 - $v \in V_r$: Veicolo della flotta attiva.
 - $P_{v} \rightarrow$ **Routing:** un vettore ordinato di nodi (lista) che rappresenta la sequenza di nodi del percorso effettuato dal veicolo $v$.
 - $(a,b) \in P_v$: Arco tra il nodo $a$ e il nodo $b$ del percorso $P_v$ del veicolo $r$.
 - $cd$: Costo unitario per distanza percorsa.
 - $d_{ab}$: Distanza di viaggio dal nodo $a$ al nodo $b$.

Il Costo di Viaggio è la sommatoria, per ogni rifiuto, del il numero di ritiri totali programmati per il rifiuto r moltiplicato per la sommatoria per ogni veicolo e per ogni nodo da a a b del percorso di quel veicolo del prodotto tra il costo unitario per la distanza percorsa e la distanza da a a b.

### 3.4 Costo del Lavoro

$$F = \min \left\{...+ \sum_{r \in R} \left( X_{r} \cdot \sum_{v \in V_{r}} cm \cdot T_{v} \right) \right\}$$
*Legenda*:
 - $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.
 - $X_{r} \in \mathbb{R} \rightarrow$ **Frequenza programmata:** variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).
 - $v \in V_r$: Veicolo della flotta attiva.
 - $cm$: Costo orario della manodopera ($cm$).
 - $T_v$ : Tempo totale di attività per veicolo.
 
Il Costo del Lavoro è la sommatoria per ogni tipologia di rifiuto del numero di ritiri totali programmati per il rifiuto r, per la sommatoria per ogni veicolo del prodotto tra il costo orario della manodopera e il tempo totale di attività per veicolo.

### 3.4.1 Tempo totale di attività per veicolo

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

- **Greedy**

- **Clarke-Wright** (per routing) + **Drop/Add** (per esplorare curva Pareto)