# Progetto di Ottimizzazione Bi-Obiettivo: Logistica della Raccolta Differenziata

## 1. Introduzione

Il presente progetto affronta il problema dell'ottimizzazione della raccolta differenziata in un contesto urbano, modellandolo come un problema di ottimizzazione bi-obiettivo. L'approccio supera le logiche tradizionali basate sulla sola minimizzazione delle distanze, integrando un forte focus sulla qualità del servizio percepita dal cittadino.

L'algoritmo **decide proattivamente** la pianificazione settimanale (frequenze, veicoli attivi e routing), bilanciando due forze contrapposte:

1. **L'impatto sociale:** minimizzare l'insoddisfazione dell'utente, misurata come scostamento dalla frequenza di ritiro ideale (che varia in base al profilo dell'utenza).

2. **L'efficienza logistica:** minimizzare i costi operativi aziendali, composti dall'attivazione dei mezzi, dal consumo di carburante lungo i percorsi e dalle ore di lavoro degli operatori.


## 2. Legenda e Notazione Matematica

## Indici (Pedici)

- $i \in I$: Tipologia di rifiuto/frazione (organico, carta, plastica, vetro, indifferenziata).

- $w \in W$: Singolo utente o cluster di utenza (nodo della rete).

- $t \in T$: Giorno lavorativo della settimana ($t = 1, \dots, 6$). meglio dividere i giorni in 2 turni da 8 ore  ($t = 1, \dots, 12$)

- $k \in K$: Veicolo appartenente alla flotta aziendale.

## Parametri di Input (Dati Certi)

- $\rho_{iw}$: Frequenza ideale (ritiri settimanali desiderati/ideali) per il rifiuto $i$ dall'utente $w$.

- $Q_{iw}$: Quantità stimata (volume/peso) di rifiuto $i$ prodotta dall'utente $w$ al giorno.

- $C_k$: Capacità massima di carico del veicolo $k$.

- $D_{T}$: Matrice coppie (distanze, tempi di viaggio) = ($d_{uv}$, $tv_{uv}$) $\forall  (u,v)  \in V$

- $tv_{uv}$: Tempo di viaggio dal nodo $u$ al nodo $v$.

- $tc_{iw}$: Tempo di carico (svuotamento mastelli) presso l'utente $w$ per la frazione $i$.

- $\alpha$: Peso di penalità applicato in caso di sotto-servizio (mancato ritiro).

- $\beta$: Peso di penalità applicato in caso di sovra-servizio (ritiri in eccesso).

- $cf_k$: Costo fisso di attivazione per il turno lavorativo del veicolo $k$.

- $cd, ct$: Costo unitario per distanza percorsa ($cd$) e costo orario della manodopera ($ct$).

- $m$: Durata turno di lavoro.

## Variabili Decisionali (Intere e Vettoriali)

- $X_{iw} \in \mathbb{N}$: **Frequenza programmata.** Variabile intera $\ge 0$ che indica il numero di ritiri totali programmati nella settimana per l'utente $w$ e la frazione $i$.

- $N_{it} \in \mathbb{N}$: **Flotta attiva.** Variabile intera $\ge 0$ che indica il numero totale di camion attivati nel giorno $t$ per la frazione $i$.

- $R_{ikt}$: **Routing.** Un vettore ordinato di nodi (lista) che rappresenta la sequenza del percorso effettuato dal veicolo $k$ nel giorno $t$ per la frazione $i$. Vettore di coppie di nodi del percorso lungo $γ$ effettuato dal veicolo $k$ nel giorno $t$ per la frazione $i$. 

    - _Esempio:_ $R_{ikt} = [0, w_1, w_5, w_8, 0]$ (dove $0$ è il deposito).
    - Indichiamo con $(u,v) \in R_{ikt}$ gli archi (coppie di nodi consecutivi) attraversati nel percorso.


## 3. Funzioni Obiettivo

## Obiettivo 1: Minimizzazione dell'Insoddisfazione Sociale ($f_1$)

Si penalizza lo scostamento tra i ritiri programmati ($X_{iw}$) e quelli desiderati ($\rho_{iw}$). La funzione di disservizio $D$ è asimmetrica per punire severamente il sotto-servizio e disincentivare lievemente il sovra-servizio:

$$D(X_{iw}, \rho_{iw}) = \begin{cases} \alpha \cdot (\rho_{iw} - X_{iw})^2 & \text{se } X_{iw} < \rho_{iw} \\ 0 & \text{se } X_{iw} = \rho_{iw} \\ \beta \cdot (X_{iw} - \rho_{iw}) & \text{se } X_{iw} > \rho_{iw} \end{cases}$$

La prima funzione obiettivo aggrega il disservizio su tutti gli utenti e frazioni:

$$f_1 = \min \sum_{i \in I} \sum_{w \in W} D(X_{iw}, \rho_{iw})$$
                            INSODDISFAZIONE        

## Obiettivo 2: Minimizzazione dei Costi Logistici ($f_2$)

Il costo totale non si basa più su matrici binarie, ma estrae direttamente i dati dai vettori di routing e dalle variabili intere.

$$f_2 = \min \left[ \sum_{i \in I} \sum_{t \in T} (cf_k \cdot N_{it}) + \sum_{i,t,k} \sum_{(u,v) \in R_{ikt}} (cd \cdot d_{uv}) + \sum_{i,t,k} ct \cdot \left( \sum_{(u,v) \in R_{ikt}} tv_{uv} + \sum_{w \in R_{ikt}} tc_{iw} \right) \right]$$
             COSTO FISSO     COSTO DI VIAGGIO    COSTO DEL LAVORO


## 4. Vincoli di Sistema (Constraints)

I vincoli fisici e temporali vengono valutati direttamente sugli elementi contenuti all'interno dei vettori di routing $R_{ikt}$.

## 4.1 Vincolo di Capacità dei Veicoli

Per ogni percorso, la somma delle stime di carico nei nodi visitati non deve superare la capacità del veicolo.

$$\sum_{w \in R_{ikt}} Q_{iw} \le C_k \quad \forall i \in I, t \in T, k \in K$$

## 4.2 Vincolo Temporale del Turno Lavorativo

La somma dei tempi di viaggio sugli archi del percorso e dei tempi di sosta (carico) nei nodi non deve eccedere $m$.

$$\sum_{(u,v) \in R_{ikt}} tv_{uv} + \sum_{w \in R_{ikt}} tc_{iw} \le m \quad \forall i \in I, t \in T, k \in K$$

## 4.3 Vincolo di Flotta Massima

Il numero di veicoli attivati in un dato giorno per una frazione non può superare il numero totale di veicoli fisicamente disponibili per quella specifica mansione.

$$N_{it} \le |K_i| \quad \forall i \in I, t \in T$$

_(Dove $|K_i|$ è il numero totale di mezzi preposti alla raccolta della frazione $i$)._

## 4.4 Vincolo di Coerenza Frequenza-Routing

Il numero di volte in cui un utente $w$ compare all'interno di tutti i vettori di routing generati durante la settimana lavorativa per la frazione $i$, deve corrispondere esattamente al valore della frequenza intera decisa dall'algoritmo.

$$\sum_{t \in T} \sum_{k \in K} \text{Conteggio}(w \in R_{ikt}) = X_{iw} \quad \forall w \in W, i \in I$$