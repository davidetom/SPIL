## Problematiche Evidenziate

La professoressa ha individuato un errore di fondo nell'impostazione iniziale del vostro lavoro, legato alla confusione tra input, indici di performance e variabili decisionali vere e proprie.

- Senza aver definito prima le variabili decisionali corrette, è impossibile formulare la funzione obiettivo.
- C'è stata confusione tra gli indici di performance e le variabili che l'euristica deve effettivamente "sputare fuori" come decisione.
- Il coefficiente di saturazione dei mastelli, i giorni di ritardo e la distanza complessiva non sono variabili decisionali.
- La dislocazione degli utenti, la posizione di partenza del camion (deposito) e le distanze della rete stradale sono dati che si possiedono già a priori e rappresentano degli input, non delle variabili.

## Le Variabili Decisionali Richieste

Per correggere il tiro, la professoressa ha indicato chiaramente che il vostro modello deve basarsi su tre variabili decisionali principali:
- **Giorni di prelievo:** Dovete decidere in quali giorni effettuare la raccolta, stabilendo quante volte a settimana passare per ogni tipologia di rifiuto (es. umido, carta).
- **Numero di camion:** Dovete stabilire quanti camion attivare per ogni giornata e per ogni tipologia di prodotto da raccogliere.
- **Routing:** Dovete definire il percorso specifico che ogni camion attivato dovrà effettuare per minimizzare i costi.

## Struttura della Funzione Obiettivo (Bi-Obiettivo)

L'obiettivo del progetto è duplice: minimizzare i costi operativi e massimizzare la soddisfazione dell'utente.

- **Minimizzazione dei Costi:** Questa componente deve includere i costi di uscita dei camion (eventuali costi fissi), i chilometri percorsi (consumo di benzina) e il tempo di lavoro retribuito agli operatori.
- **Massimizzazione della Soddisfazione (o Minimizzazione dell'Insoddisfazione):** Si basa su quanto la frequenza di raccolta offerta dal vostro modello si discosta dalla richiesta ideale dell'utente.
- **Differenziazione dell'Utenza:** La funzione di soddisfazione deve variare in base al nucleo familiare, poiché un single che produce meno immondizia potrebbe accontentarsi di un solo passaggio settimanale, riducendo i costi rispetto a una famiglia numerosa.
- **Ponderazione:** Le due componenti (costi e soddisfazione) andranno sommate su tutti gli utenti e pesate opportunamente per trovare la soluzione ottima.

## Input, Parametri e Vincoli Operativi

Infine, la professoressa ha chiarito come gestire i dati e i limiti fisici del problema.

- **Parametri:** Il numero massimo di giorni lavorativi settimanali (es. 5 o 6 giorni) e le distanze tra i nodi sono parametri che definiscono la singola istanza del problema.
- **Vincoli di Tempo:** Esiste un limite massimo di 8 ore lavorative per turno, all'interno del quale bisogna calcolare sia il tempo di viaggio per raggiungere i nodi, sia il tempo fisico impiegato per caricare i rifiuti.
- **Vincoli di Capacità:** Il camion ha un limite capacitativo fisico su quanta immondizia può contenere.
- **Stima dei Rifiuti:** Per non pianificare il routing "alla cieca", è necessario stimare a priori la quantità di rifiuti in base alla tipologia di utenza conosciuta, ipotizzando ad esempio un mastello pieno al 30% per i single e al 70% o più per famiglie numerose.