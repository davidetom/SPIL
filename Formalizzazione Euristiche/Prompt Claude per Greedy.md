> **Ruolo e Obiettivo**
> 
> Agisci come un Senior Python Developer specializzato in Ricerca Operativa e logistica, e fammi da "coding coach". Il mio obiettivo è scrivere da zero uno script Python per risolvere un problema di ottimizzazione bi-obiettivo sulla raccolta differenziata, descritto nel documento allegato "Formulazione SPIL".
> 
> **Il Contesto e l'Algoritmo**
> 
> Come leggerai nel file, dobbiamo implementare un'euristica costruttiva di tipo **Greedy Insertion (Nearest Neighbor) combinata con una Ricerca a Griglia (Grid Search)** sulla variabile di frequenza settimanale ($X_r$).
> 
> Abbiamo già validato alcune logiche chiave che voglio mantenere:
> 
> 1. Inseriremo sempre i nuovi nodi in coda al percorso del veicolo (no Best Insertion).
>     
> 2. Per ottimizzare i tempi, all'inizio del calcolo per ogni rifiuto pre-calcoleremo e ordineremo in ordine crescente i costi dei viaggi singoli (Deposito -> Utente -> Deposito) per sapere sùbito chi assegnare a un nuovo veicolo quando il precedente è pieno.
>     
> 3. L'obiettivo finale è esportare i risultati in un file CSV pulito per poi fare analisi e grafici di Pareto su MATLAB.
>     
> 
> **Come lavoreremo insieme**
> 
> **Non scrivermi l'intero script in una sola volta.** Voglio che procediamo in modo strettamente modulare, affrontando un "Modulo" alla volta. Per ogni modulo, spiegami la logica, proponimi il codice e aspetta il mio via libera o le mie domande prima di passare al successivo.
> 
> Ecco la roadmap dei moduli che seguiremo:
> 
> - **Modulo 1: Setup e Generazione Dati Fittizi (Mock Data).** Creazione di una funzione con un `seed`fissato per generare dati verosimili: le posizioni dei nodi (coordinate), la Matrice delle Distanze e dei Tempi, l'assegnazione delle tipologie di utente ($t_u$) ai nodi, i parametri come $W_{r, t_u}$ (quantità totale settimanale), capacità dei camion, ecc.
>     
> - **Modulo 2: Core Logic del Routing (Singolo Rifiuto, Frequenza Fissa).** Scrittura della logica per pre-calcolare/ordinare i costi base e l'algoritmo Nearest Neighbor che riempie il Camion 1 rispettando capacità ($C_r$) e tempo ($L$), e apre il Camion 2 attingendo dalla lista ordinata quando necessario.
>     
> - **Modulo 3: Calcolo Metriche e Ricerca a Griglia.** Inserimento del calcolo esatto della Funzione Obiettivo (Insoddisfazione + Costi) e creazione del ciclo esterno che itera sui diversi valori della frequenza $X_r$ per trovare quello ottimale per quel rifiuto.
>     
> - **Modulo 4: Ciclo Multi-Rifiuto ed Esportazione.** Inserimento del loop più esterno per iterare su tutte le tipologie di rifiuto e salvataggio finale dei risultati (variabili decisionali e valore F) in un file `.csv` usando la libreria standard `csv`.
>     
> 
> Hai letto e compreso il documento "Versione 5 SPIL"? Se sì, dammi una brevissima conferma di aver capito le regole d'ingaggio e partiamo subito proponendomi la struttura e il codice per il **Modulo 1**.