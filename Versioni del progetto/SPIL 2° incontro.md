# Progetto di Ottimizzazione Bi-Obiettivo: Logistica della Raccolta Differenziata

## 1. Introduzione

Il presente progetto affronta il problema dell'ottimizzazione della raccolta differenziata in un contesto urbano, modellandolo come un problema di ottimizzazione bi-obiettivo. L'approccio supera le logiche tradizionali basate sulla sola minimizzazione delle distanze, integrando un forte focus sulla qualità del servizio percepita dal cittadino.

L'algoritmo **decide proattivamente** la pianificazione settimanale (frequenze, veicoli attivi e routing), bilanciando due forze contrapposte:

1. **L'impatto sociale:** minimizzare l'insoddisfazione dell'utente, misurata come scostamento dalla frequenza di ritiro ideale (che varia in base al profilo dell'utenza).

2. **L'efficienza logistica:** minimizzare i costi operativi aziendali, composti dall'attivazione dei mezzi, dal consumo di carburante lungo i percorsi e dalle ore di lavoro degli operatori.

## 2. Legenda e Notazione Matematica

## Indici

- $r \in R$: Tipologia di rifiuto: organico, carta, plastica, vetro, indifferenziata.

- $u \in U$: Singolo utente o cluster per palazzi (nodo della rete). [per i palazzi è un cluster perché consideri che non ci abita solo una famiglia all'interno]

- $v \in V$: Veicolo appartenente alla flotta aziendale.

## Parametri

- G($\Lambda$, E): grafo cittadino.

- $U$: vettore di utenti, all'indice u ci sarà la tipologia f di quell'utente (single, famiglia piccola, famiglia numerosa, palazzina).

- $\rho_{r}$: Frequenza ideale (ritiri settimanali desiderati/ideali) per il rifiuto $r$.

- $Q_{ru}$: Quantità stimata (volume/peso) di rifiuto $r$ prodotta dalla tipologia di utente $u$. 

- $C_r$: Capacità massima di carico del veicolo che raccoglie $r$.

- $D_{T}$: Matrice coppie (distanze, tempi di viaggio) = ($d_{ab}$, $t_{ab}$) $\forall  (a,b)  \in \Lambda$

- $tv_{ab}$: Tempo di viaggio dal nodo $a$ al nodo $b$.

- $tc_{ru}$: Tempo di carico (svuotamento mastelli) presso l'utente $u$ per il rifiuto $r$. tempo di carico dipende dal tipo di rifiuto e dal tipo di utente.

- $\alpha$: Peso di penalità applicato in caso di sotto-servizio (mancato ritiro).

- $\beta$: Peso di penalità applicato in caso di sovra-servizio (ritiri in eccesso).

- $c_v$: Costo fisso di attivazione del veicolo $v$.

- $cd, ct$: Costo unitario per distanza percorsa ($cd$) e costo orario della manodopera ($ct$).

- $L$: Durata turno di lavoro.

---

### Variabile di raccolta

- $\chi_{ru}$: **Frequenza effettiva**. Variabile che indica il numero di ritiri effettivi (settimanali) per ogni utente $u$ del rifiuto $r$.

---

## Variabili Decisionali 

- $X_{r} \in \mathbb{R}$: **Frequenza programmata.** Variabile $\ge 0$ che indica il numero di ritiri totali programmati per il rifiuto $r$ (ritiri settimanali).  

- $N_{r} \in \mathbb{N}$: **Flotta attiva.** Variabile intera $\ge 0$ che indica il numero totale di camion attivati per il rifiuto $r$. 

- $P_{v}$: **Percorso (Routing).** Un vettore ordinato di nodi (lista) che rappresenta la sequenza di nodi del percorso lungo $γ$ effettuato dal veicolo $v$. 

## 3. Funzioni Obiettivo
$$F = \min \left[ \sum_{r \in R} \sum_{u \in U} I_{ru} + \sum_{r \in R} (c_v \cdot N_{r}) + \sum_{v \in V} \sum_{(a,b) \in P_{v}} (cd \cdot d_{ab}) + \sum_{v \in V} ct \cdot T_{v} \right]$$
INSODDISFAZIONE + COSTO FISSO  + COSTO DI VIAGGIO + COSTO DEL LAVORO

---
### Funzione di Insoddisfazione

Si penalizza lo scostamento tra i ritiri effettivi ($\chi_{ru}$) e quelli desiderati ($\rho_{ru}$). La funzione di disservizio $I_{ru}$ è asimmetrica per punire severamente il sotto-servizio e disincentivare lievemente il sovra-servizio.

$$I_{ru} = \begin{cases} \alpha \cdot (\rho_{r} - \chi_{ru}) & \text{se } \chi_{ru} < \rho_{r} \\ 0 & \text{se } \chi_{ru} = \rho_{r} \\ \beta \cdot (\chi_{ru} - \rho_{r}) & \text{se } \chi_{ru} > \rho_{r} \end{cases}$$
---
### Tempo totale di attività per veicolo

$$T_{v} = \sum_{(a,b) \in P_{v}} tv_{ab} + \sum_{u \in P_{v}} \left( tc_{ru} \cdot Q_{ru} \right)$$
## 4. Vincoli di Sistema

I vincoli fisici e temporali vengono valutati direttamente sugli elementi contenuti all'interno dei vettori di routing $P_{v}$.

## 4.1 Vincolo di Capacità dei Veicoli

Per ogni percorso, la somma delle stime di carico nei nodi visitati non deve superare la capacità del veicolo.
$$\sum_{u \in P_{v}} Q_{ru} \le C_r \quad \forall r \in R, v \in V$$

## 4.2 Vincolo Temporale del Turno Lavorativo

La somma dei tempi di viaggio sugli archi del percorso e dei tempi di sosta (carico) nei nodi non deve eccedere $L$.
$$T_{v} \le L \quad \forall v \in V$$

