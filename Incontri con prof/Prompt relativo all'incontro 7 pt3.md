Ciao! Ora che il codice Python genera correttamente tutti i CSV, ho bisogno di creare 5 script MATLAB separati, uno per ciascuna delle 5 analisi (Variazione N, Tipologia, Distribuzione, Mappa Reale, Standard).

Il Contesto dei Dati: Ogni script dovrà leggere i file da una cartella (es. risultati_csv/). I file CSV ora hanno il seguente formato per l'intestazione:rifiuto,X_r,algoritmo,is_best,n_vehicles,F_total,F_insoddis,F_costo_fisso,F_viaggio,F_lavoro,sat_fisica,sat_tempo,algo_time_sec

Inoltre, i file hanno una nomenclatura specifica che include il valore del parametro politico gamma (0.10, 0.50, 0.90) e il tag dell'analisi. Esempi di nomenclatura:

  

risultati_100u_varN_Nmax5000_Nact100_seed42_gamma0.50.csv

risultati_100u_tipo_residenziale_gamma0.90.csv

risultati_100u_distrib_cluster_gamma0.10.csv

risultati_4000u_mappa_reale_gamma0.50.csv

risultati_100u_std_seed42_gamma0.50.csv

Requisiti Generali per TUTTI i 5 script MATLAB:

  

Parsing robusto: Usa espressioni regolari (regexp) per estrarre dal nome del file le variabili indipendenti (es. Nact, tipologia, o gamma).

Lettura automatica: Filtra solo i file is_best == 1 per valutare le metriche della configurazione ottima.

Grafico 1: Transizione delle Politiche (γ): Un grafico (es. stacked bar) che mostri chiaramente come varia la scomposizione della Funzione Obiettivo (Finsoddis

​ scalata vs Costi Logistici) al variare del γ, confrontando Greedy e Clarke-Wright.

Grafico 2: Saturazione Camion (IL FOCUS): Un grafico a barre raggruppate dedicato a sat_fisica e sat_tempo(medie in %). Voglio vedere visivamente quanto i camion viaggiano vuoti o pieni, e quanto tempo sfruttano del loro turno lavorativo, confrontando i due algoritmi al variare del γ e della variabile dell'analisi in corso.

Grafico 3: Costi/Prestazioni rispetto alla variabile indipendente: (Ad esempio, per lo script 1 sarà Ftot

​ vs N, per lo script 2 sarà Ftot

​ vs Scenario).

Stile: Mantieni uno stile grafico accademico, con grid on, palette colori consistenti (es. blu per Greedy, arancio per CW), e legende chiare.

Dettaglio Script per Script:

  

Script 1 (Bench_1_VarN.m): X-axis principale = N attivi. Mostra l'evoluzione dei tempi di calcolo, dei veicoli usati e delle saturazioni al crescere di N, raggruppati per i 3 γ.

Script 2 (Bench_2_Tipologia.m): X-axis = Categoria (Residenziale, Villette, ecc.). Mostra come la saturazione crolla o sale in base alla densità di rifiuto generata dal tipo di utenza, per ogni γ.

Script 3 (Bench_3_Distribuzione.m): X-axis = Uniforme vs Cluster. Focus su come l'aggregazione spaziale migliori la saturazione fisica e abbatta i tempi di viaggio rispetto allo sparpagliamento uniforme.

Script 4 (Bench_4_Reale.m) & Script 5 (Bench_5_Standard.m): Poiché l'istanza è una sola, l'asse X deve essere interamente dedicato al parametro γ (Pro-Azienda, Neutro, Pro-Cittadino). Fai risaltare l'aumento vertiginoso del numero di camion e il crollo della saturazione quando γ=0.90 (Pro-Cittadino).

Per favore, generami il codice completo per i primi 3 script in questa risposta, usando funzioni di lettura riutilizzabili. Successivamente, in un altro messaggio, genereremo i restanti due. Includi abbondanti commenti in italiano.