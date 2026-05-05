> **Ruolo e Obiettivo**
> 
> Agisci sempre come un Senior Python Developer e Data Analyst esperto in Ricerca Operativa, e continua a farmi da "coding coach". Il mio obiettivo ora è soddisfare le richieste specifiche della professoressa per il benchmarking finale del progetto SPIL (raccolta differenziata), stressando gli algoritmi (Greedy e Clarke-Wright) in vari scenari.
> 
> **Il Contesto e le Novità**
> 
> Attualmente ho un `main.py` e un `Generazione_Dati.py` funzionanti, e due script MATLAB base per l'analisi a singola run e multi-run per scalabilità. Ora devo implementare tre direttive precise di benchmarking richieste per il colloquio:
> 
> 1. **Variazione della Tipologia di Utenti:** Mantenere fisso $N$ e variare la distribuzione delle probabilità dei tipi di utente (es. scenario "residenziale", scenario "grandi condomini").
>     
> 2. **Variazione del Numero di Utenti su Rete Fissa:** Generare il grafo/distanze una sola volta (es. per 200 nodi) e fare test estraendo un sottoinsieme variabile di nodi attivi (es. 50, 100, 150), mantenendo inalterati i percorsi sottostanti.
>     
> 3. **Variazione della Densità Spaziale:** Verificare il comportamento con utenti sparsi in modo uniforme vs utenti raggruppati in cluster ("stanno vicini").
>     
> 
> **VINCOLO ARCHITETTONICO CRITICO: Zero-Touch Code e Parametrizzazione**
> 
> Voglio che l'esecuzione dei test sia **completamente guidata da console**. Non voglio dover aprire e modificare `Generazione_Dati.py` o `main.py` a mano per ogni run. Il `main.py` dovrà proporre un menù interattivo da cui selezionare il tipo di analisi, passando dinamicamente i parametri di generazione. I CSV in output dovranno avere una naming convention chiara per facilitare l'importazione in MATLAB.
> 
> **Come lavoreremo insieme**
> 
> Procederemo in modo strettamente modulare, un passo alla volta.
> 
> - **Modulo 9: Refactoring Parametrico di `Generazione_Dati.py`.** Modificheremo la funzione `generate_mock_data`. Dovrà accettare nuovi argomenti opzionali: un array custom per `type_probs` (per eludere l'hardcoding attuale), un flag per la generazione di coordinate a cluster invece che uniformi, e una logica per generare un grafo di base largo ($N_{max}$) ma restituire i dati attivando solo un sottoinsieme $N$ di clienti.
>     
> - **Modulo 10: Refactoring del Menù in `main.py`.** Aggiorneremo la CLI. All'avvio, chiederà: "Quale analisi vuoi eseguire? 1) Standard, 2) Variazione Tipologia Utenti, 3) Variazione N su Rete Fissa, 4) Variazione Densità Spaziale". A seconda della scelta, eseguirà un ciclo per generare in automatico i CSV multipli necessari allo scenario.
>     
> - **Modulo 11: Script MATLAB - Benchmarking Tipologia e Densità.** Creerai nuovi script MATLAB che automatizzino la lettura dei CSV generati dal Modulo 10. Per le tipologie di utenti voglio un grafico a barre raggruppate per F_total (confronto algoritmi vs scenario). Per la densità, grafici specifici che mostrino il crollo del parametro `F_viaggio` e `n_vehicles` usando Clarke-Wright nei cluster.
>     
> - **Modulo 12: Script MATLAB - Scalabilità su Rete Fissa.** Adatterai il concetto dello script `confronto_runs.m` esistente affinché legga specificamente i CSV generati dall'analisi di rete fissa, tracciando la complessità computazionale e l'andamento dei costi.
>     
> 
> Hai letto e compreso tutto? Se sì, dammi una brevissima conferma di aver capito le regole d'ingaggio e dimmi di fornirti i file attuali per iniziare il **Modulo 9**.