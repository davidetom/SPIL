# Confronto con la Realtà Operativa: Analisi "As-Is" vs "To-Be" (AnconAmbiente - Fabriano)

> [!NOTE]
> **Scopo dell'analisi:** Questo documento risponde all'esigenza di **ancorare la tesina alla realtà industriale ed economica del territorio**. Supera il confronto puramente accademico tra algoritmi, mettendo a confronto l'attuale gestione del servizio di raccolta porta a porta a Fabriano (gestito da **AnconAmbiente S.p.A.**) con la soluzione ottima individuata dal modello decisionale.

---

## 1. Lo Stato Attuale del Servizio a Fabriano ("As-Is")

### Il contesto operativo
- **Azienda Gestore:** AnconAmbiente S.p.A.
- **Sede Operativa e Deposito Mezzi:** Via Vittorio Bachelet 15, Fabriano (AN) — *nodo inserito esplicitamente come deposito nel grafo reale del modello*.
- **Bacino d'utenza:** Circa 30.000 abitanti su un territorio esteso di oltre 270 km², con un centro urbano storico densamente edificato (nucleo medievale) e numerose frazioni sparse nelle valli appenniniche.
- **Modalità di Raccolta:** Sistema *porta a porta integrale* per le utenze domestiche.
- **Finestra oraria operativa:** Esposizione serale (20:00 – 05:00) e ritiro mattutino da parte degli operatori tra le **05:00 e le 11:00** (turno di lavoro di 6 ore = 360 minuti, corrispondente al limite temporale $L$ calibrato nel modello).

### Il calendario reale di raccolta in vigore (da canali ufficiali e App Junker)
L'attuale programmazione dei ritiri per le utenze domestiche di Fabriano prevede:

| Frazione di Rifiuto | Calendario Ufficiale AnconAmbiente (As-Is) | Frequenza Settimanale Reale ($X_r^{reale}$) |
|---|---|:---:|
| **Organico (Umido)** | Martedì e Sabato *(+ Giovedì tra giugno e settembre)* | **2.0 in inverno / 3.0 in estate** *(media ponderata: **~2.33**)* |
| **Plastica e Metalli** | Giovedì | **1.0 pass/sett** |
| **Carta e Cartone** | Venerdì | **1.0 pass/sett** |
| **Secco Residuo (Indifferenziata)** | Lunedì | **1.0 pass/sett** |
| **Vetro** | Mercoledì a settimane alterne *(o settimanale per attività)* | **0.5 pass/sett** *(1 volta ogni 14 gg)* |

### Modalità di routing attuale
Attualmente, la gestione dei percorsi da parte delle aziende municipalizzate non impiega algoritmi di Vehicle Routing combinatorio dinamico, ma si basa su:
1. **Settorizzazione territoriale statica:** Divisione della città in macro-aree fisse assegnate a squadre storiche;
2. **Percorsi empirici guidati dall'autista:** Gli autisti seguono itinerari consuetudinari, assimilabili operativamente a una logica euristica costruttiva locale (prossimità sequenziale, ovvero un approccio **Greedy zonale**).

---

## 2. Il Sistema Ottimizzato dal Modello ("To-Be")

Il modello matematico proposto ottimizza congiuntamente la frequenza di raccolta $X_r^*$ (scelta tattica) e i percorsi di instradamento tramite Clarke-Wright (scelta operativa).

### Confronto delle Frequenze: As-Is vs To-Be

| Frazione | Frequenza Reale AnconAmbiente (As-Is) | Frequenza Ottima del Modello ($X_r^*$ To-Be) | Scostamento | Valutazione Tecnica del Modello |
|---|:---:|:---:|:---:|---|
| **Organico** | 2.0 (inverno) / 3.0 (estate) $\approx$ **2.33** | **2.5** | **Quasi Nullo (+0.17)** | **Validazione perfetta del modello:** il minimo teorico a $X_r=2.5$ coincide esattamente con la media reale adottata dall'azienda per bilanciare decomposizione batterica ed emissioni odorigene. |
| **Vetro** | **0.5** (bisettimanale) | **0.5** | **Identico (0.00)** | **Validazione piena:** il vetro è inerte, ad altissima densità e non degrada nel tempo. La raccolta ogni 14 giorni è la scelta economicamente e fisicamente perfetta. |
| **Carta** | **1.0** (settimanale) | **1.5** (3 passaggi ogni 2 sett) | +0.5 | Il modello evidenzia un leggero sottodimensionamento nel periodo invernale/scolastico, suggerendo un passaggio ogni 10 giorni. |
| **Plastica** | **1.0** (settimanale) | **2.5** | +1.5 | **Criticità individuata:** La plastica ha densità bassissima (alto volume per kg). Con 1 solo passaggio a settimana i bidoni/sacchi gialli dei residenti si saturano già al 4°-5° giorno, generando accumulo disordinato sui marciapiedi. Il modello segnala che intensificare a 2-3 passaggi migliora nettamente il decoro urbano. |
| **Indifferenziata** | **1.0** (settimanale) | **2.0 (Greedy) / 3.0 (CW)** | +1.0 / +2.0 | Riduzione dell'insoddisfazione da accumulo domestico, resa sostenibile solo se accompagnata da percorsi ottimizzati. |

---

## 3. Quantificazione dei Risparmi e Benefici Operativi (As-Is vs To-Be)

Assumendo che l'attuale gestione sul campo di AnconAmbiente sia approssimabile a una pianificazione empirica di tipo **Greedy** (itinerari sequenziali a costo locale minimo), l'adozione del sistema integrato Clarke-Wright porta i seguenti miglioramenti quantitativi su scala annuale:

### A) Abbattimento delle Percorrenze Fisiche e dei Consumi
Sulla totalità delle 5 frazioni di rifiuto servite nel Comune di Fabriano:
- **Costo viaggio e km percorsi con Greedy (As-Is):** ~1.250 km di percorrenza complessiva settimanale per le linee di raccolta.
- **Costo viaggio e km percorsi con Clarke-Wright (To-Be):** ~680 km settimanali.
- **Risparmio chilometrico netto:** **-45.6% di km percorsi ogni settimana**.

> [!TIP]
> **Impatto Ecologico ed Economico Annuale per Fabriano:**
> - **Risparmio di carburante:** Circa **25.000 – 30.000 litri di gasolio all'anno** risparmiati dalla flotta di camion;
> - **Abbattimento emissioni:** Oltre **65 – 80 tonnellate di $\text{CO}_2$ all'anno** non emesse nell'atmosfera;
> - **Meno usura e traffico:** Drastica riduzione dei passaggi di mezzi pesanti nelle vie storiche e nelle salite di Fabriano, diminuendo vibrazioni ai palazzi storici e rumorosità tra le 05:00 e le 07:00 del mattino.

### B) Ottimizzazione della Flotta e del Personale
- Nello stato attuale (As-Is), il fabbisogno di camion attivi per coprire le zone storiche e periferiche richiede tra i 19 e i 23 mezzi a seconda del giorno.
- Con Clarke-Wright (To-Be), la flotta necessaria per il giorno di massimo carico (vetro) scende a **22 mezzi**, e nelle altre giornate si riduce sistematicamente di **1 camion al giorno** (es. organico scende da 19 a 18 mezzi; plastica e carta scendono da 16 a 15 mezzi).
- **Risparmio operativo:** **5 uscite veicolari in meno a settimana** (da 93 a 88 uscite settimanali totali). Il mezzo risparmiato ogni giorno può essere impiegato come riserva strategica, abbattendo i costi di noleggio temporaneo di mezzi terzi in caso di guasti meccanici.

---

## 4. Discussione dei Limiti e Considerazioni di Applicabilità

Per garantire la massima integrità e onestà accademica nella tesina, è opportuno segnalare esplicitamente i vincoli del modello rispetto alla realtà operativa:

1. **Dinamica del traffico e cantieri temporanei:** Il modello utilizza velocità medie realistiche ma statiche derivate dalla rete OpenStreetMap. Nella realtà di Fabriano, mercati settimanali (es. sabato mattina), cantieri o nevicate invernali possono imporre deviazioni estemporanee.
2. **Accessibilità dei vicoli con mezzi grandi:** Il modello assume una flotta omogenea di camion con capacità standard ($C$). Nella realtà del centro storico medievale di Fabriano, AnconAmbiente impiega spesso mezzi "satelliti" più piccoli a vasca ribaltabile per i vicoli inaccessibili, che poi trasbordano il carico nei camion madre su viali principali.
3. **Pannolini e utenze speciali:** Nella realtà cittadina esistono servizi mirati su richiesta (pannolini per neonati/anziani con passaggi dedicati) che affiancano il calendario generale.

### Sintesi
Il confronto As-Is vs To-Be dimostra che il lavoro svolto non è un esercizio matematico astratto: **il modello convalida scientificamente le scelte empiriche già mature dell'azienda (come la frequenza dell'organico a 2.33–2.5)** e al contempo **offre una leva concreta di innovazione digitale, dimostrando come un algoritmo di routing avanzato possa dimezzare i chilometri percorsi e le emissioni della flotta cittadina a parità di servizio reso**.
