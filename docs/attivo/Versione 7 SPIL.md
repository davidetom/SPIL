# Progetto di Ottimizzazione Bi-Obiettivo: Logistica della Raccolta Differenziata (Versione 7)

> **Stato documento:** Versione 7 attiva (allineata a [`latex/capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex), [`latex/capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex) e alle direttive dell'[`Incontro 7.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%207.md) del 17/11/2026).

---

## 1. Introduzione

Il progetto affronta il problema della pianificazione della raccolta differenziata porta a porta in un contesto urbano (caso studio reale: Comune di Fabriano, $3932$ utenze residenziali su rete stradale OpenStreetMap).
L'algoritmo determina la pianificazione settimanale del servizio per ciascuna frazione merceologica (frequenza di raccolta, flotta attiva per giro e percorsi dei veicoli), bilanciando due obiettivi contrapposti:

1. **L'impatto sociale ($F_{\text{insoddis}}$):** minimizzare l'insoddisfazione degli utenti, misurata come scostamento asimmetrico dalla frequenza di ritiro ideale associata a ciascuna tipologia di rifiuto e di utenza.
2. **L'efficienza logistica ($F_{\text{costi}}$):** minimizzare i costi operativi settimanali dell'azienda, composti dai costi fissi di attivazione dei veicoli ($F_{\text{fisso}}$), dai costi chilometrici di percorrenza ($F_{\text{viaggio}}$) e dai costi della manodopera ($F_{\text{lavoro}}$).

---

## 2. Legenda e Notazione Matematica

### 2.1 Indici e Insiemi

- $r \in R$: Tipologia di rifiuto (`organico`, `carta`, `plastica`, `vetro`, `indifferenziata`).
- $u \in U_G$: Utente (nodo cliente) del grafo cittadino $G$ (con nodo $0$ corrispondente al deposito centrale).
- $v \in V_r$: Veicolo della flotta attivata per un giro di raccolta del rifiuto $r$.
- $t_u \in T$: Tipologia dell'utente $u$ (`single`, `famiglia`, `palazzina_piccola`, `palazzina_grande`).
- $(a,b) \in E_G$: Arco del grafo cittadino $G$ che collega i nodi $a$ e $b$.

### 2.2 Parametri

- $x^*_{r t_u}$: Frequenza ideale di ritiro settimanale per il rifiuto $r$ e la tipologia di utente $t_u$ [ritiri/settimana].
- $W_{r t_u}$: Quantità settimanale base stimata di rifiuto (*waste*) per la tipologia di utente $t_u$ e il rifiuto $r$ [kg/settimana].
- $Q_{ru}(X_r)$: Quantità stimata di rifiuto $r$ raccolta presso l'utente $u$ a ogni singolo passaggio del veicolo, in funzione della frequenza settimanale $X_r$ [kg/passaggio].
- $C_r$: Capacità massima di carico del veicolo adibito alla raccolta del rifiuto $r$ [kg].
- $d_{ab}$: Distanza di viaggio più breve sulla rete stradale dal nodo $a$ al nodo $b$ [km].
- $\tau_{ab}$: Tempo di percorrenza dal nodo $a$ al nodo $b$ [min] (calcolato a velocità media $25\text{ km/h}$).
- $s_{r t_u}$ (nel codice `tc[(r, t_u)]`): Tempo fisso di servizio per fermata (svuotamento mastelli/contenitori) presso l'utente $u$ di tipologia $t_u$ per il rifiuto $r$ [min]. Non dipende dalla quantità $Q_{ru}(X_r)$ raccolta nel singolo passaggio.
- $\alpha, \beta$: Pesi di penalità applicati rispettivamente in caso di sotto-servizio ($X_r < x^*_{r t_u}$) e di sovra-servizio ($X_r > x^*_{r t_u}$), con $\alpha = 10.0 > \beta = 2.0$.
- $c_r$: Costo fisso di attivazione di un veicolo per un giro di raccolta del rifiuto $r$ [€].
- $cd, cm$: Costo unitario per distanza percorsa ($cd = 0.35\text{ €/km}$) e costo della manodopera per unità di tempo ($cm = 0.25\text{ €/min}$, pari a $15\text{ €/ora}$).
- $L$: Durata massima del turno di lavoro per veicolo ($L = 480\text{ min} = 8\text{ ore}$).
- $\gamma \in (0, 1)$: Parametro decisionale che governa il peso relativo nella combinazione convessa tra disservizio e costi logistici (riferimenti standard: $\gamma = 0.10$ Pro-Azienda, $\gamma = 0.50$ Neutro, $\gamma = 0.90$ Pro-Cittadino).
- $k_{\text{scala}}$: Fattore di normalizzazione per equiparare l'ordine di grandezza di $F_{\text{insoddis}}$ e $F_{\text{costi}}$.

### 2.3 Variabili Decisionali

- $X_r \in \mathcal{X} \subset \mathbb{R}_{>0}$: **Frequenza programmata** (numero di ritiri settimanali per il rifiuto $r$).
- $V_r \in \mathbb{N}$: **Flotta per giro** (numero di veicoli attivati per completare un singolo giro di raccolta del rifiuto $r$; le attivazioni settimanali sono $V_r \cdot X_r$).
- $P_v = (0, u_1, u_2, \dots, u_k, 0)$: **Routing** (sequenza ordinata di nodi visitati dal veicolo $v \in V_r$, con partenza e rientro al deposito $0$).

---

## 3. Funzione Obiettivo

La funzione obiettivo bi-criterio combina le componenti non pesate di insoddisfazione ($F_{\text{insoddis}}$) e di costo logistico settimanale ($F_{\text{costi}} = F_{\text{fisso}} + F_{\text{viaggio}} + F_{\text{lavoro}}$):

$$F_{\text{total}} = \min \Biggl\{ \gamma \cdot k_{\text{scala}} \cdot F_{\text{insoddis}} + (1 - \gamma) \cdot F_{\text{costi}} \Biggr\}$$

dove le quattro componenti grezze (non pesate), sommate sulle tipologie di rifiuto $r \in R$, sono definite come:

$$F_{\text{insoddis}} = \sum_{r \in R} \sum_{u \in U_G} I_{ru}(X_r)$$

$$F_{\text{costi}} = \underbrace{\sum_{r \in R} \left( c_r \cdot V_r \cdot X_r \right)}_{F_{\text{fisso}}} + \underbrace{\sum_{r \in R} \left( X_r \cdot \sum_{v \in V_r} \sum_{(a,b) \in P_v} cd \cdot d_{ab} \right)}_{F_{\text{viaggio}}} + \underbrace{\sum_{r \in R} \left( X_r \cdot \sum_{v \in V_r} cm \cdot T_v \right)}_{F_{\text{lavoro}}}$$

### 3.1 Funzione di Insoddisfazione ($I_{ru}$)

$$I_{ru}(X_r) = \begin{cases} \alpha \cdot \left(x^*_{r t_u} - X_r\right) & \text{se } X_r < x^*_{r t_u} \\ 0 & \text{se } X_r = x^*_{r t_u} \\ \beta \cdot \left(X_r - x^*_{r t_u}\right) & \text{se } X_r > x^*_{r t_u} \end{cases}$$

### 3.2 Tempo di Attività del Veicolo ($T_v$) e Carico per Passaggio ($Q_{ru}(X_r)$)

Il tempo totale di attività del veicolo $v$ su un singolo giro (incluso il rientro al deposito) è:

$$T_v = \sum_{(a,b) \in P_v} \tau_{ab} + \sum_{u \in P_v} s_{r t_u}$$

- **Formulazione v2 (baseline attuale nel codice):**
  $$Q_{ru}(X_r) = \frac{W_{r t_u}}{X_r}$$
- **Evoluzione v7 (Incontro 7 — in fase di implementazione):**
  Sostituzione della legge inversamente proporzionale $W_{r t_u}/X_r$ con una funzione decrescente **sub-lineare / logaritmica** (o coefficienti tabellati decrescenti meno che proporzionalmente, es. $100\% \to 90\% \to 75\% \to 60\%$) su una griglia $\mathcal{X}$ con limite superiore ridotto a frequenze operative realistiche.

---

## 4. Vincoli di Sistema

1. **Filtro di fattibilità individuale:** Ogni utente $u$ deve soddisfare individualmente $Q_{ru}(X_r) \le C_r$ e $\tau_{0,u} + s_{r t_u} + \tau_{u,0} \le L$ per poter essere servito.
2. **Vincolo di Capacità dei Veicoli:**
   $$\sum_{u \in P_v} Q_{ru}(X_r) \le C_r \qquad \forall v \in V_r, \; \forall r \in R$$
3. **Vincolo Temporale del Turno Lavorativo:**
   $$T_v \le L \qquad \forall v \in V_r, \; \forall r \in R$$

---

## 5. Architettura Risolutiva: Grid Search + Euristiche di Routing

Il problema è decomposto per rifiuto $r \in R$ in due pipeline indipendenti e alternative messe a confronto (*benchmarking*):

1. **Livello superiore — Grid Search su $X_r \in \mathcal{X}$:** Per ciascun valore candidato $X_r \in \mathcal{X}$, si ricostruiscono da zero le rotte ammissibili tramite l'euristica di routing scelta, si calcolano le componenti grezze $F_{\text{insoddis}}(X_r)$ e $F_{\text{costi}}(X_r)$ e si seleziona l'ottimo $X_r^* = \arg\min_{X_r \in \mathcal{X}} F_{\text{total}}(X_r)$.
2. **Euristica 1 — Greedy (*cheapest insertion* competitiva multi-rotta):**
   - Apre il primo veicolo sull'utente fattibile con minor costo del percorso elementare $\{0, u, 0\}$.
   - Ad ogni iterazione valuta simultaneamente, per tutti i veicoli aperti $v \in O$, il costo marginale economico di inserimento in coda:
     $$\Delta_{cur_v, u} = cd\,(d_{cur_v, u} + d_{u, 0} - d_{cur_v, 0}) + cm\,(\tau_{cur_v, u} + s_{r t_u} + \tau_{u, 0} - \tau_{cur_v, 0})$$
     confrontandolo con il costo di apertura di un nuovo veicolo $c_r X_r + cd(d_{0, u_{\text{next}}} + d_{u_{\text{next}}, 0}) + cm(\tau_{0, u_{\text{next}}} + s_{r t_{u_{\text{next}}}} + \tau_{u_{\text{next}}, 0})$, ed esegue la mossa ammissibile più economica.
3. **Euristica 2 — Clarke-Wright Savings:**
   - Parte dalla soluzione elementare $P_u = \{0, u, 0\}$ per ogni $u \in U_{\text{feas}}$.
   - Calcola una sola volta in forma vettorizzata la matrice dei risparmi economici completi:
     $$S_{ij} = c_r + cd\,(d_{0i} + d_{0j} - d_{ij}) + cm\,(\tau_{0i} + \tau_{0j} - \tau_{ij})$$
   - Ordina le coppie con $S_{ij} > 0$ in senso decrescente (ordinamento stabile) e fonde iterativamente le rotte distinte $r_i \neq r_j$ che rispettano la regola degli estremi e i vincoli di capacità $C_r$ e turno $L$ *(in valutazione l'estensione con inversione di rotta simmetrica per fusioni testa-testa / coda-coda)*.
