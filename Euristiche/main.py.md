```python ln:1 hl:43-70 hlt:F_Totale
// =====================================================================
// PSEUDOCODICE: GREEDY
// =====================================================================

Per ogni tipologia di rifiuto r in R:
    
    Miglior_F_r = INFINITO // Inizializzazione funzione obiettivo
    Miglior_X_r = 0 // Inizializzazione frequenza programmata
    Migliori_Routing_r = [] // Routing inizialmente vuoti

    Per ogni possibile frequenza X da 1 a X_max: // (o da 0.5 a X_max=6)

        // ---------------------------------------------------------
        // 1. INIZIALIZZAZIONE PARAMETRI DIPENDENTI DALLA FREQUENZA X
        // ---------------------------------------------------------
        
	    Insoddisfazione_Tot = CalcolaInsoddisfazioneTotale(X, r, U) //  Penalità per tutta la città
        Costi_Viaggio_Tot = 0
        Camion_Attivi = [] // Camion_Attivi.length è la variabile decisionale
        Routing_Camion = [] // Variabile decisionale
        Nodi_Non_Visitati = Copia(U)

        Per ogni utente u in U:
            // Calcolo il volume stimato prendendo in considerazione la tipologia dell utente e il numero di ritiri programmati
            u.carico_stimato = W[r][u.tipologia] / X  

        // ---------------------------------------------------------
        // 2. PRE-CALCOLO E ORDINAMENTO LISTA BASE (per i nuovi camion)
        // ---------------------------------------------------------
        
        // Lista dei costi di un viaggio deposito->utente->deposito per ogni utente u
        Lista_Costi_Base = []
        Per ogni utente u in Nodi_Non_Visitati:
            costo_base = CostoDist(deposito, u) + CostoDist(u, deposito) + CostoTemp(deposito, u) + CostoTemp(u, deposito) + CostoCarico(u)
            Lista_Costi_Base.aggiungi( Nodo: u, Costo: costo_base )
            
        OrdinaCrescente(Lista_Costi_Base, per: Costo)

        // ---------------------------------------------------------
        // 3. COSTRUZIONE DEI PERCORSI (Greedy Nearest Neighbor)
        // ---------------------------------------------------------
        
        Mentre Nodi_Non_Visitati non è vuoto:
	        Lista_Candidati = []
		    Per ogni c in Camion_Attivi: // per ogni c valuto tutte le possibili aggiunte ammissibili
			    Lista_Costi_Aggiunta = []
			    Per ogni utente u in Nodi_Non_Visitati:
				    Se (c.tempo + Tempo_Aggiunta(u)) <= L && (c.carico + Carico_Aggiunta(u)) <= C_r:
					    costo_aggiunta = CostoDist(c.nodoCorrente, u) + CostoDist(u, deposito) + CostoTemp(c.nodoCorrente, u) + CostoTemp(u, deposito) + CostoCarico(u)
					    Lista_Costi_Aggiunta.aggiungi(Nodo: u, Costo: costo_aggiunta)
				
				OrdinaCrescente(Lista_Costi_Aggiunta, per: Costo)
				SE NON Lista_Costi_Aggiunta.IsEmpty():
					nodo_candidato = EstraiPrimoNodo(Lista_Costi_Aggiunta)
					costo_candidato = EstraiPrimoCosto(Lista_Costi_Aggiunta)
					Lista_Candidati.aggiungi(Nodo: nodo_candidato, Costo: costo_candidato, Camion: c)
			
			// Caso iniziale in cui non ho nessun camion -> dovrò sicuramente attivarne uno usando il primo nodo di Lista_Costi_Base
			Se Lista_Candidati.IsEmpty():
				Lista_Candidati.aggiungi(Nodo: NuovoNodo(), Costo: INFINITO)
			OrdinaCrescente(Lista_Candidati, per: Costo)
			
			// Caso in cui scelgo il nuovo camion
			Se EstraiPrimoCosto(Lista_Costi_Base) + c_r <= EstraiPrimoCosto(Lista_Candidati):
				nodo_scelto = EstraiPrimoNodo(Lista_Costi_Base)
				nuovo_camion = Camion()
	            Nuovo_Percorso = [deposito, nodo_scelto]
	            nuovo_camion.routing = Nuovo_Percorso
	            Routing_Camion.aggiungi(Camion: nuovo_camion, Routing: nuovo_camion.routing)
	            nuovo_camion.tempo = CalcolaTempoAttuale()
			    nuovo_camion.carico = CalcolaCaricoAttuale()
			    Camion_Attivi.aggiungi(nuovo_camion)
            
            // Caso in cui aggiungo il nodo al percorso di un camion esistente
            Altrimenti:
		        nodo_scelto = EstraiPrimoNodo(Lista_Candidati)
		        camion = EstraiPrimoCamion(Lista_Candidati)
		        camion.routing.aggiungi(nodo_scelto)
		        camion.tempo = CalcolaTempoAttuale()
			    camion.carico = CalcolaCaricoAttuale()
			
			Lista_Costi_Base.rimuovi(nodo_scelto)
			Nodi_Non_Visitati.rimuovi(nodo_scelto)
			
		// Aggiungo alla fine di ogni routing il nodo deposito per concludere il percorso dei camion
		Per ogni c in Camion_Attivi:
			c.routing.aggiungi(deposito)
			
		// Calcolo il costo totale dei viaggi dei vari camion
		Per ogni c in Camion_Attivi:
			Costi_Viaggio_Tot += CalcolaCostiViaggio(c.routing)

        // ---------------------------------------------------------
        // 4. VALUTAZIONE FUNZIONE OBIETTIVO E SALVATAGGIO OTTIMO
        // ---------------------------------------------------------
        
        Costo_Fisso_Tot = c_r * Camion_Attivi.length * X
        
        // F = Insoddisfazione + Costi Fissi + (Passaggi Settimanali * Costi Operativi Singolo Turno)
        F_Totale = Insoddisfazione_Tot + Costo_Fisso_Tot + (X * Costi_Viaggio_Tot)

        Se F_Totale < Miglior_F_r:
            Miglior_F_r = F_Totale
            Miglior_X_r = X
            Miglior_Routing_r = Copia(Routing_Camion)

    // Fine iterazioni X per questo rifiuto: salva i dati
    SalvaRisultati(r, Miglior_X_r, Miglior_F_r, Miglior_Routing_r)
```
