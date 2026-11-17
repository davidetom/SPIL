```python
ln:1 hl:43-70 hlt:F_Totale
// =====================================================================
// PSEUDOCODICE: CLARKE-WRIGHT (SAVINGS ALGORITHM) CON GRID SEARCH
// =====================================================================

Per ogni tipologia di rifiuto r in R:
    
    Miglior_F_r = INFINITO // Inizializzazione funzione obiettivo[cite: 8]
    Miglior_X_r = 0 // Inizializzazione frequenza programmata[cite: 8]
    Migliori_Routing_r = [] // Routing inizialmente vuoti[cite: 8]

    Per ogni possibile frequenza X da 1 a X_max: // (o da 0.5 a X_max=6)[cite: 8]

        // ---------------------------------------------------------
        // 1. INIZIALIZZAZIONE PARAMETRI DIPENDENTI DALLA FREQUENZA X[cite: 8]
        // ---------------------------------------------------------
        
        Insoddisfazione_Tot = CalcolaInsoddisfazioneTotale(X, r, U) // Penalità per tutta la città[cite: 8]
        Costi_Viaggio_Tot = 0[cite: 8]
        Camion_Attivi = [] // Variabile decisionale sui mezzi[cite: 8]
        
        Per ogni utente u in U:
            // Calcolo il volume stimato inversamente proporzionale alla frequenza[cite: 8]
            u.carico_stimato = W[r][u.tipologia] / X  

        // ---------------------------------------------------------
        // 2. INIZIALIZZAZIONE PERCORSI BASE (1 Camion per Utente) E DIZIONARI O(1)
        // ---------------------------------------------------------
        
        Dizionario_Percorsi = Vuoto() // Map: Utente -> Camion che lo serve
        
        Per ogni utente u in U:
            Se u.carico_stimato <= C_r E (CostoTemp(deposito, u) + CostoTemp(u, deposito) + CostoCarico(u)) <= L:
                nuovo_camion = Camion()
                nuovo_camion.routing = [deposito, u, deposito] // Percorso base: dep -> u -> dep
                nuovo_camion.carico = u.carico_stimato
                nuovo_camion.tempo = CostoTemp(deposito, u) + CostoTemp(u, deposito) + CostoCarico(u)
                
                Camion_Attivi.aggiungi(nuovo_camion)
                
                // Mappiamo i dati per check istantanei nel Modulo 4
                Dizionario_Percorsi[u] = nuovo_camion
                u.stato = "ESTREMO" // In un percorso di un solo nodo, il nodo è sia il primo che l ultimo

        // ---------------------------------------------------------
        // 3. CALCOLO E ORDINAMENTO MATRICE DEI RISPARMI (SAVINGS)
        // ---------------------------------------------------------
        
        Lista_Risparmi = []
        Per ogni coppia di utenti (i, j) in U (con i != j):
            // S_ij calcola il risparmio generato unendo la fine di i con l inizio di j
            Risparmio_Fisso = c_r
            Risparmio_Dist  = cd * (Distanza(i, deposito) + Distanza(deposito, j) - Distanza(i, j))
            Risparmio_Tempo = cm * (Tempo(i, deposito) + Tempo(deposito, j) - Tempo(i, j))
            S_ij = Risparmio_Fisso + Risparmio_Dist + Risparmio_Tempo
            
            // Per ottimizzare la memoria, scartiamo sùbito i risparmi negativi o irrilevanti
            Se S_ij > 0:
                Lista_Risparmi.aggiungi(Nodo_Uscita: i, Nodo_Entrata: j, Valore: S_ij)
                
        OrdinaDecrescente(Lista_Risparmi, per: Valore)

        // ---------------------------------------------------------
        // 4. COSTRUZIONE DEI PERCORSI (MERGE ITERATIVO)
        // ---------------------------------------------------------
        
        Per ogni elemento (i, j, S_ij) in Lista_Risparmi:
            Camion_i = Dizionario_Percorsi[i]
            Camion_j = Dizionario_Percorsi[j]
            
            // CHECK 1: Evitare cicli (non devono essere già nello stesso percorso)
            Se Camion_i == Camion_j:
                Continua // Salta alla prossima coppia
                
            // CHECK 2: Regola degli Estremi
            // 'i' non deve essere intrappolato e deve essere l ultimo utente del suo percorso
            // 'j' non deve essere intrappolato e deve essere il primo utente del suo percorso
            Se i.stato != "INTERNO" E j.stato != "INTERNO":
                Se i == Ultimo_Utente(Camion_i.routing) E j == Primo_Utente(Camion_j.routing):
                    
                    // CHECK 3: Vincoli di Capacità e Tempo
                    Nuovo_Carico = Camion_i.carico + Camion_j.carico
                    // Ricalcolo vettoriale del tempo (Sottrai i viaggi col deposito eliminati, aggiungi l arco i->j)
                    Nuovo_Tempo = Camion_i.tempo + Camion_j.tempo - Tempo(i, deposito) - Tempo(deposito, j) + Tempo(i, j)
                    
                    Se Nuovo_Carico <= C_r E Nuovo_Tempo <= L:
                        
                        // FUSIONE APPROVATA
                        Nuovo_Routing = Unisci(Camion_i.routing_senza_deposito_finale, Camion_j.routing_senza_deposito_iniziale)
                        
                        Camion_Unito = Camion()
                        Camion_Unito.routing = Nuovo_Routing
                        Camion_Unito.carico = Nuovo_Carico
                        Camion_Unito.tempo = Nuovo_Tempo
                        
                        // Aggiorna lo stato dei nodi appena fusi: ora sono all interno del percorso
                        i.stato = "INTERNO"
                        j.stato = "INTERNO"
                        
                        // Aggiorna il dizionario per tutti gli utenti del nuovo percorso in O(1)
                        Per ogni nodo_u in Camion_Unito.routing (escluso deposito):
                            Dizionario_Percorsi[nodo_u] = Camion_Unito
                            
                        // Aggiorna la flotta attiva
                        Camion_Attivi.rimuovi(Camion_i)
                        Camion_Attivi.rimuovi(Camion_j)
                        Camion_Attivi.aggiungi(Camion_Unito)

        // ---------------------------------------------------------
        // 5. VALUTAZIONE FUNZIONE OBIETTIVO E SALVATAGGIO OTTIMO[cite: 8]
        // ---------------------------------------------------------
        
        Per ogni c in Camion_Attivi:[cite: 8]
            Costi_Viaggio_Tot += CalcolaCostiViaggio(c.routing)[cite: 8]

        Costo_Fisso_Tot = c_r * Camion_Attivi.length * X[cite: 8]
        
        // F = Insoddisfazione + Costi Fissi + (Passaggi Settimanali * Costi Operativi Singolo Turno)[cite: 8]
        F_Totale = Insoddisfazione_Tot + Costo_Fisso_Tot + (X * Costi_Viaggio_Tot)[cite: 8]

        Se F_Totale < Miglior_F_r:[cite: 8]
            Miglior_F_r = F_Totale[cite: 8]
            Miglior_X_r = X[cite: 8]
            Migliori_Routing_r = Copia(Camion_Attivi)[cite: 8]

    // Fine iterazioni X per questo rifiuto: salva i dati[cite: 8]
    SalvaRisultati(r, Miglior_X_r, Miglior_F_r, Migliori_Routing_r)[cite: 8]
```
