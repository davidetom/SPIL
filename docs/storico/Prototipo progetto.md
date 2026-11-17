# Definizione del Problema: Raccolta Differenziata Porta a Porta

## 1. Contesto e Risorse

Il problema mira a ottimizzare la logistica della raccolta differenziata su scala cittadina, considerando rate di riempimento differenti per i vari rifiuti.

La città di Fabriano è suddivisa in **3 settori operativi** basati sulla distanza, che influenzano la tolleranza dei cittadini ai disservizi: Centro (entro 500m), Zona Mediana (tra 500m e 1000m) e Periferia (oltre 1000m).

**Risorse Logistiche:**

- $x$ operatori totali.
- $y$ camion totali.

## 2. Fase 1: Modello Teorico Esatto (Basato sulle Singole Palazzine)

In questa prima formulazione, l'insoddisfazione è calcolata per ogni singola palazzina della città.

**Funzione Obiettivo:**

$$\min \left[ \sum_{i=1}^{5} \sum_{j=1}^{n} b_j v_{ij} g_{ij}^2, \sum_{i=1}^{5} \sum_{k=1}^{y} p c d_{ik} + \sum_{i=1}^{5} \sum_{h=1}^{x} t_{ih} s \right]$$

**Legenda degli Indici:**

- $i \in \{1, \dots, 5\}$: Tipo di rifiuto (1 = plastica, 2 = indifferenziato, 3 = umido, 4 = carta, 5 = vetro).
- $j \in \{1, \dots, n\}$: Indice della generica palazzina (con $n$ = numero totale di palazzine).
- $k \in \{1, \dots, y\}$: Indice del generico camion.
- $h \in \{1, \dots, x\}$: Indice del generico operatore.

**Legenda delle Variabili e Parametri:**

- $b_j$: Costante di intolleranza della singola palazzina $j$ in base al settore in cui ricade.
- $v_{ij}$: Volume normalizzato di spazzatura nei secchi associati alla palazzina $j$ per il rifiuto $i$ 
	($v_{ij} \in [0, 1]$). Essendo limitato dall'upperbound della capienza del secchio, è calcolato come:
$$v_{ij} = \frac{\min(q_{ij}, C_{ij})}{C_{ij}}$$
	- $C_{ij}$: Capienza massima del secchio assegnato alla palazzina $j$ per la tipologia di rifiuto $i$.
	- $q_{ij}$: Quantità reale di spazzatura prodotta e accumulata dalla palazzina $j$ per il rifiuto $i$.
- $g_{ij}$: Giorni di ritardo nella raccolta per la palazzina $j$ e per il rifiuto $i$.
- $p$: Prezzo del carburante (al litro).
- $c$: Consumo del camion (litri per km).
- $d_{ik}$: Distanza percorsa dal camion $k$ per la raccolta del rifiuto $i$.
- $t_{ih}$: Ore di lavoro dell'operatore $h$ dedicate alla raccolta del rifiuto $i$.
- $s$: Stipendio orario del personale.

## 3. Fase 2: Modello Approssimato (Basato sui Nodi di Raccolta)

Per ridurre la complessità computazionale (rendendo il problema scalabile e gestibile in tempo reale), si applica un clustering spaziale. Le $n$ palazzine vengono aggregate nel nodo stradale più vicino (punto di raccolta o set di secchi).

Se definiamo $m$ come il numero totale di nodi di raccolta sul grafo stradale, e $P_w$ come l'insieme dei palazzi assegnati al nodo $w$, le variabili di insoddisfazione vengono ricalcolate per il singolo nodo.

**Variabili aggiornate per il Nodo $w$:**

- **Volume Aggregato e Normalizzato ($V_{iw}$):** Il livello di riempimento del set di secchi al nodo $w$, limitato dal suo upper bound (capienza massima) e normalizzato tra 0 (vuoto) e 1 (pieno).
$$V_{iw} = \frac{\min(Q_{iw}, C_{iw})}{C_{iw}}$$
- **Capienza Aggregata ($C_{iw}$):** La capienza massima totale del set di secchi posizionati al nodo $w$ per il rifiuto $i$.
- **Quantità Reale Aggregata ($Q_{iw}$):** La somma della spazzatura reale prodotta da tutti i palazzi assegnati al nodo $w$.
$$Q_{iw} = \sum_{j \in P_w} q_{ij}$$
- **Intolleranza Aggregata ($B_w$):** L'intolleranza base del settore moltiplicata per il numero di utenze (palazzi) che scaricano in quel nodo, in modo da pesare maggiormente i nodi densamente popolati.
$$B_w = |P_w| \cdot b_{settore}$$

# **Funzione Obiettivo Aggiornata:**

I costi rimangono strutturalmente identici, ma i percorsi logistici $d_{ik}$ vengono calcolati iterando sugli $m$ nodi di raccolta invece che sulle $n$ palazzine.

$$\min \left[ \sum_{i=1}^{5} \sum_{w=1}^{m} B_w V_{iw} G_{iw}^2, \sum_{i=1}^{5} \sum_{k=1}^{y} p c d_{ik} + \sum_{i=1}^{5} \sum_{h=1}^{x} t_{ih} s \right]$$

$G_{iw}$ rappresenta i giorni di ritardo per lo svuotamento del nodo di raccolta $w$ per il rifiuto $i$

## 4. Domande Aperte per il Professore

- **Orizzonte temporale:** L'ottimizzazione deve essere pensata per minimizzare la funzione obiettivo considerando una singola giornata, una settimana, un mese, oppure in modo continuativo (simulazione rolling-horizon)?
- **Validazione dell'approssimazione:** L'aggregazione spaziale ai nodi di raccolta (clustering delle utenze sul grafo stradale) è considerata un'assunzione accettabile per la risoluzione del modello ai fini dell'esame/progetto?


## 5. Strategia di Risoluzione: Metodo $\epsilon$-vincolo ed Euristica Greedy

Poiché il problema presenta due funzioni obiettivo contrastanti ($f_1 = \text{Insoddisfazione Totale}$ e $f_2 = \text{Costi Logistici}$), l'obiettivo del solutore sarà quello di approssimare la **Frontiera di Pareto** delle soluzioni ottime.

### L'approccio $\epsilon$-vincolo
Per risolvere la natura bi-obiettivo, si adotta il metodo $\epsilon$-vincolo. L'idea è quella di trasformare l'obiettivo dei Costi in un vincolo rigido parametrato da un valore $\epsilon$ (budget massimo), per poi minimizzare unicamente l'Insoddisfazione.

**Modello Monobiettivo Riformulato:**
$$\min \left[ \sum_{i=0}^{4} \sum_{w=1}^{m} B_w V_{iw} G_{iw}^2 \right]$$

**Soggetto al nuovo vincolo di Budget ($\epsilon$):**
$$\sum_{i=0}^{4} \sum_{k=1}^{y} p c d_{ik} + \sum_{i=0}^{4} \sum_{h=1}^{x} t_{ih} s \le \epsilon$$

L'algoritmo verrà eseguito iterativamente variando il valore del budget $\epsilon$ (es. partendo dal costo logistico minimo indispensabile, aumentandolo gradualmente) per generare diverse soluzioni strategiche. Questo fornirà ai decisori politici (il Comune) un ventaglio di opzioni: *Quanto budget extra serve per azzerare i ritardi in periferia?*

### Euristica di Routing (Ispirata alla Regola di Smith)
Per la costruzione effettiva dei percorsi (routing) all'interno di ogni iterazione, si propone un'euristica costruttiva ispirata alla regola di Smith dello scheduling. 
Invece di minimizzare il tempo di completamento pesato su una singola macchina, il camion sceglierà il prossimo nodo $w$ verso cui dirigersi valutando uno *score* che massimizza il rapporto tra il "peso" del disservizio e il costo per coprirlo:

$$\text{Score}_w = \frac{B_w \cdot V_{iw} \cdot G_{iw}^2}{d_{k, w}}$$

Dove $d_{k, w}$ è la distanza tra la posizione attuale del camion $k$ e il nodo target $w$. Il camion prediligerà i nodi con altissima insoddisfazione e vicini alla sua posizione.

Nell'ottica di un algoritmo *greedy*, l'insoddisfazione attuale di un nodo rappresenta il **beneficio** (il "premio") che si ottiene servendolo. 
Svuotare il secchio al nodo $w$ significa *sottrarre* quel valore di insoddisfazione dal totale cittadino. Pertanto, lo $\text{Score}_w$ indica l'efficienza della mossa. Massimizzando questo rapporto, il camion sceglie sempre il nodo che garantisce il massimo abbattimento del disservizio cittadino per ogni singolo chilometro percorso (logica *Bang-for-the-buck* analoga al rapporto $w_j/p_j$ della Regola di Smith).




# MODIFICHE E MIGLIORAMENTI
### 1. Unity e la gestione del Grafo (Visivo vs Logico)

In termini di fattibilità e prestazioni, **l'approccio standard e di gran lunga più efficiente è mantenere una netta separazione tra la logica e la geometria**. Non ti conviene usare un grafo unico con un flag "shadow", perché obbligheresti comunque l'algoritmo di routing (o il solutore del modello) a caricare in memoria e scorrere migliaia di nodi inutili, appesantendo il calcolo.

Ecco come si fa di solito nei sistemi GIS (Geographic Information Systems) e nei motori grafici:

1. **Il Grafo Logico (Per l'algoritmo):** Ha solo i nodi essenziali (incroci stradali e punti di raccolta/secchi). Gli archi (edges) che collegano questi nodi contengono il peso (distanza in km o tempo di percorrenza). L'algoritmo di ottimizzazione lavora _esclusivamente_ su questo grafo ridotto, calcolando il percorso ottimo in frazioni di secondo.

2. **La Geometria degli Archi (Per Unity):** All'interno di ogni arco del grafo logico (es. l'arco che va dall'Incrocio A al Secchio B), salvi un array di coordinate (i famosi nodi di curvatura).

Quando l'algoritmo decide che il camion deve andare da A a B, Unity non fa altro che leggere quell'array di coordinate e far muovere (interpolando) il modello 3D del camion lungo quei punti. In questo modo separi l'intelligenza artificiale (routing logico) dall'animazione (rendering visivo).

### 2. Attenzione ai nodi di OpenStreetMap (.osm)

I file `.osm` generano grafi molto densi. Ci sono nodi che rappresentano incroci reali, ma anche nodi che servono solo a curvare una strada ("shape nodes").

- **Miglioramento:** Ti consiglio di fare una pulizia (semplificazione del grafo) mantenendo solo le intersezioni reali e i vicoli ciechi. Se usi Python, la libreria **OSMnx** ha una funzione nativa `ox.simplify_graph()` che fa esattamente questo, restituendoti un grafo perfetto per la logistica.


### 3. Il Rate di Riempimento Stocastico e le Simulazioni

Assolutamente sì, nella realtà la spazzatura non si accumula in modo deterministico. Il giovedì piove e si butta meno carta, la domenica c'è il pranzo in famiglia e si fa più umido.

Se vuoi consegnare un paper operativo, l'approccio standard e più elegante è diviso in **due fasi (Ottimizzazione + Simulazione Monte Carlo)**:

1. **Generazione della Frontiera (Fase Deterministica):** Fai girare il tuo algoritmo (l'euristica greedy con il metodo $\epsilon$-vincolo) usando il _valore atteso_ (la media) del rate di riempimento. Trovi ad esempio 5 soluzioni (5 set di percorsi e turni) lungo la curva di Pareto.

2. **Validazione (Fase Stocastica):** Prendi quelle 5 soluzioni e le testi su un simulatore in cui il rate di riempimento varia secondo una distribuzione di probabilità (es. Distribuzione Normale o di Poisson). Fai girare 100 "settimane simulate" per ogni soluzione.

In questo modo puoi dire al Comune: _"La Soluzione A costa poco, ma se c'è un picco imprevisto di rifiuti fallisce miseramente (non è robusta). La Soluzione B costa il 10% in più, ma assorbe le variazioni stocastiche senza generare insoddisfazione."_

### 4. Come implementare i Turni e il Personale nel Greedy

Per inserire i lavoratori, devi trasformare il tuo algoritmo spaziale in un **algoritmo spazio-temporale** (in gergo: VRP with Time Windows and Shift Constraints).

Invece di far muovere il camion all'infinito finché non ha finito i soldi del budget, devi dotare ogni camion di un "orologio interno" e di una "capacità residua".

Il trucco più semplice per l'euristica è la **Pre-assegnazione dei turni (Rostering)**:

- Dividi la giornata in turni (es. Mattina 06-14, Pomeriggio 14-22).

- Assegni un lavoratore (o una coppia) a un camion per uno specifico turno. Da quel momento, il camion $k$ ha a disposizione un tempo massimo $T_{max}$ (es. 8 ore).

A questo punto, modifichi l'euristica Greedy. Quando il camion valuta lo "Score" dei nodi, deve fare un **Controllo di Fattibilità (Feasibility Check)** prima di muoversi:

1. Ha abbastanza spazio nel cassone per svuotare il secchio $w$?
2. Ha abbastanza tempo nel suo turno per andare a $w$, svuotare, e tornare alla discarica/deposito prima che scada l'ottava ora lavorativa?

Se la risposta è no a una delle due, il camion deve svuotarsi o tornare al deposito e passare il testimone al turno successivo.