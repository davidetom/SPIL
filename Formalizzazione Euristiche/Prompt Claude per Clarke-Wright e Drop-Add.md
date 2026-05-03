> **Ruolo e Obiettivo**
> 
> Agisci come un Senior Python Developer specializzato in Ricerca Operativa e logistica, e fammi da "coding coach". Il mio obiettivo è evolvere un progetto Python esistente per la risoluzione di un problema di ottimizzazione bi-obiettivo sulla raccolta differenziata, descritto nel documento "Formulazione SPIL".
> 
> **Il Contesto e le Novità**
> 
> Attualmente ho già implementato con successo un'euristica Greedy e uno script di generazione dati (`Generazione_Dati.py`) basato su triangolazione di Delaunay. Ora voglio fare un level-up:
> 
> 1. Implementare l'algoritmo di **Clarke-Wright (Savings algorithm)**.
>     
> 2. Integrare un **Selettore di Algoritmo** nel `main.py` per avviare il Greedy, il Clarke-Wright, o entrambi per fare benchmarking.
>     
> 3. Adeguare l'esportazione dati e gli script **MATLAB** di conseguenza.
>     
> 
> **VINCOLO ARCHITETTONICO CRITICO: Time-Space Tradeoff per Clarke-Wright**
> 
> Il target sono istanze con molti utenti. Ho 24 GB di RAM. L'obiettivo per il nuovo modulo Clarke-Wright è **minimizzare la complessità temporale a discapito di quella spaziale**:
> 
> - Usa **NumPy** massicciamente per vettorizzare l'intera matrice dei risparmi (formula: $S_{ij} = c_r + cd \cdot (d_{i0} + d_{0j} - d_{ij}) + cm \cdot (tv_{i0} + tv_{0j} - tv_{ij})$).
>     
> - Durante il ciclo di unione, **sono severamente vietate le ricerche lineari $O(N)$**. Usa dizionari/hash-maps per check in tempo $O(1)$ sulla "regola degli estremi" (unione possibile solo tra ultimo e primo nodo) e sui vincoli di capacità e tempo.
>     
> 
> **Come lavoreremo insieme**
> 
> Procederemo in modo strettamente modulare. Per ogni modulo, spiegami la logica, proponimi il codice e aspetta il mio via libera.
> 
> - **Modulo 5: Ottimizzazione `Generazione_Dati.py` esistente.** Non scriverlo da zero. Analizza il codice che ti fornirò e proponi ottimizzazioni mirate (es. type hinting, pulizia, assicurarsi che le matrici uscenti siano `numpy arrays` compatibili con la futura vettorizzazione di CW), mantenendo intatta la logica Delaunay/Dijkstra.
>     
> - **Modulo 6: Core Clarke-Wright (`CW.py`).** Vettorizzazione della matrice Savings, ordinamento $O(N \log N)$, e ciclo di unione con strutture dati $O(1)$. Deve esporre una funzione `grid_search` con la stessa firma di quella del file `Greedy.py` esistente.
>     
> - **Modulo 7: Refactoring `main.py`.** Aggiornare l'interfaccia utente. Se l'utente digita `g` avvia solo Greedy, se digita `c` avvia solo CW, se preme `Invio` (input vuoto) li avvia entrambi. Aggiungere la colonna `algoritmo` al CSV di output per tracciare chi ha generato i risultati.
>     
> - **Modulo 8: Aggiornamento MATLAB.** Adattare `analisi_pareto.m` e `RunPipeline.m` per leggere la nuova colonna `algoritmo`. Se il CSV contiene entrambi gli algoritmi, i grafici di Pareto e le curve $F\_total$ vs $X_r$ devono tracciare e confrontare le due curve (es. Greedy tratteggiato, CW linea continua).
>     
> 
> Hai letto e compreso tutto? Se sì, dammi una brevissima conferma di aver capito le regole d'ingaggio e dimmi di fornirti i file attuali per iniziare il **Modulo 5*.