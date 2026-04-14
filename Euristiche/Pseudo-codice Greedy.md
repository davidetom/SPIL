```python
ln:1 hl:43-70 hlt:F_Totale
// =====================================================================
// PSEUDOCODICE: GREEDY INSERTION (NEAREST NEIGHBOR) CON GRID SEARCH
// =====================================================================

Per ogni tipologia di rifiuto r in R:
    
    Miglior_F_r = INFINITO
    Miglior_X_r = 0
    Miglior_Routing_r = []

    Per ogni possibile frequenza X da 1 a X_max:

        // ---------------------------------------------------------
        // 1. INIZIALIZZAZIONE PARAMETRI DIPENDENTI DALLA FREQUENZA X
        // ---------------------------------------------------------
        
        Insoddisfazione_Tot = CalcolaInsoddisfazioneTotale(X, r, U) // Penalità per tutta la città
        Costi_Viaggio_Lavoro_Turno = 0
        Camion_Attivi = 0
        Routing_X = []
        Nodi_Non_Visitati = Copia(U)

        Per ogni utente u in U:
            // Applichiamo la formula del volume aggiornata
            u.carico_stimato = W[r][u.tipologia] / X  

        // ---------------------------------------------------------
        // 2. PRE-CALCOLO E ORDINAMENTO LISTA BASE (per i nuovi camion)
        // ---------------------------------------------------------
        
        Lista_Costi_Base = []
        Per ogni utente u in Nodi_Non_Visitati:
            costo_base = D[deposito][u].costo + D[u][deposito].costo
            Lista_Costi_Base.aggiungi( Nodo: u, Costo: costo_base )
            
        OrdinaCrescente(Lista_Costi_Base, per: Costo)

        // ---------------------------------------------------------
        // 3. COSTRUZIONE DEI PERCORSI (Greedy Nearest Neighbor)
        // ---------------------------------------------------------
        
        Mentre Nodi_Non_Visitati non è vuoto:
            
            Camion_Attivi = Camion_Attivi + 1
            Nuovo_Percorso = [deposito]
            Carico_Attuale = 0
            Tempo_Attuale = 0

            // 3.1 Scelta del primo nodo del nuovo camion in tempo O(1)
            nodo_partenza = EstraiPrimoNodoNonVisitato(Lista_Costi_Base, Nodi_Non_Visitati)
            Nuovo_Percorso.aggiungi(nodo_partenza)
            
            Carico_Attuale = Carico_Attuale + nodo_partenza.carico_stimato
            Tempo_Attuale = Tempo_Attuale + D[deposito][nodo_partenza].tempo + tc[r][nodo_partenza.tipologia]
            
            Nodi_Non_Visitati.rimuovi(nodo_partenza)
            nodo_corrente = nodo_partenza

            // 3.2 Riempimento del veicolo (Inserimento in coda)
            Mentre VERO:
                miglior_nodo_succ = NESSUNO
                min_costo_aggiunta = INFINITO

                Per ogni nodo_candidato in Nodi_Non_Visitati:
                    
                    // Controllo Vincoli di Capacità e Tempo
                    Carico_Simulato = Carico_Attuale + nodo_candidato.carico_stimato
                    Tempo_Simulato = Tempo_Attuale + D[nodo_corrente][nodo_candidato].tempo + tc[r][nodo_candidato.tipologia] + D[nodo_candidato][deposito].tempo
                    
                    Se (Carico_Simulato <= C_r) E (Tempo_Simulato <= L):
                        
                        // Calcolo costo Nearest Neighbor per accodarlo e poi tornare
                        costo_aggiunta = D[nodo_corrente][nodo_candidato].costo + D[nodo_candidato][deposito].costo

                        Se costo_aggiunta < min_costo_aggiunta:
                            min_costo_aggiunta = costo_aggiunta
                            miglior_nodo_succ = nodo_candidato

                Se miglior_nodo_succ != NESSUNO:
                    // Nodo valido trovato: lo accodo al percorso
                    Nuovo_Percorso.aggiungi(miglior_nodo_succ)
                    Carico_Attuale = Carico_Attuale + miglior_nodo_succ.carico_stimato
                    Tempo_Attuale = Tempo_Attuale + D[nodo_corrente][miglior_nodo_succ].tempo + tc[r][miglior_nodo_succ.tipologia]
                    
                    Nodi_Non_Visitati.rimuovi(miglior_nodo_succ)
                    nodo_corrente = miglior_nodo_succ
                Altrimenti:
                    // Camion pieno o non ha tempo per altre fermate
                    Interrompi il ciclo // Break

            // 3.3 Chiusura del percorso del camion
            Nuovo_Percorso.aggiungi(deposito)
            Routing_X.aggiungi(Nuovo_Percorso)

            // Aggiornamento costi operativi
            Costi_Viaggio_Lavoro_Turno = Costi_Viaggio_Lavoro_Turno + CalcolaCostiViaggioELavoro(Nuovo_Percorso)

        // ---------------------------------------------------------
        // 4. VALUTAZIONE FUNZIONE OBIETTIVO E SALVATAGGIO OTTIMO
        // ---------------------------------------------------------
        
        Costo_Fisso_Tot = c_r * Camion_Attivi * X
        
        // F = Insoddisfazione + Costi Fissi + (Passaggi Settimanali * Costi Operativi Singolo Turno)
        F_Totale = Insoddisfazione_Tot + Costo_Fisso_Tot + (X * Costi_Viaggio_Lavoro_Turno)

        Se F_Totale < Miglior_F_r:
            Miglior_F_r = F_Totale
            Miglior_X_r = X
            Miglior_Routing_r = Copia(Routing_X)

    // Fine iterazioni X per questo rifiuto: salva i dati
    SalvaRisultati(r, Miglior_X_r, Miglior_F_r, Miglior_Routing_r)
```
