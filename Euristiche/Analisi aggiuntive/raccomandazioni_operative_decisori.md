# Linee Guida e Raccomandazioni Operative per il Decisore (AnconAmbiente S.p.A. / Comune di Fabriano)

> [!IMPORTANT]
> **Scopo del documento:** Questo documento trasforma i risultati numerici e algoritmici della tesina in un **vero e proprio strumento di supporto decisionale (Decision Support System)** per il management di AnconAmbiente e per l'assessorato all'ambiente del Comune di Fabriano. Supera l'approccio puramente descrittivo, assumendo una **posizione esplicita, netta e prescrittiva** sulle scelte strategiche da adottare.

---

## 1. Raccomandazione Algoritmica: Perché adottare Clarke-Wright nonostante il Gap del 3.5%

### Il dilemma del decisore
Un responsabile della logistica o un assessore al bilancio potrebbe obiettare:
> *"Ha senso investire risorse per implementare un algoritmo di routing avanzato come Clarke-Wright se il risparmio monetario totale ($F_{total}$) rispetto a percorsi zonali intuitivi (Greedy) è solo del 3.5%?"*

### La posizione prescrittiva del modello: **Assolutamente SÌ.**
La valutazione aziendale e amministrativa non deve arrestarsi al costo contabile aggregato, che è dominato per il 95% da voci fisse incomprimibili (stipendi contrattuali degli operatori e ammortamenti). L'adozione di Clarke-Wright è fortemente raccomandata per tre motivi strategici:

1. **Abbattimento delle esternalità negative e target ESG (Environmental, Social, Governance):**
   Clarke-Wright riduce del **45.6% i chilometri fisicamente percorsi** dai mezzi pesanti a Fabriano (da ~1.250 km a ~680 km a settimana). Questo si traduce in:
   - **-45% di consumi di carburante e costi vivi di manutenzione;**
   - **Oltre 70 tonnellate annue di $\text{CO}_2$ risparmiate**, elemento spendibile nei bilanci di sostenibilità e per l'accesso a fondi ambientali europei/PNRR;
   - **Dimezzamento dei transiti pesanti nei vicoli del centro storico medievale**, riducendo rumorosità, emissioni di polveri sottili (PM10/PM2.5) e usura del manto stradale storico in pavé.

2. **Risparmio strutturale di mezzi ogni giorno:**
   In ogni singolo turno di raccolta, Clarke-Wright consente di impiegare **1 camion in meno** a parità di orario e carico servito, risparmiando **5 uscite veicoli a settimana**. Questo veicolo risparmiato funge da riserva strategica interna, azzerando i costosi noleggi a caldo di mezzi sostitutivi in caso di guasto.

---

## 2. Raccomandazioni Tattiche: Ottimizzazione dei Calendari di Raccolta

Il modello fornisce precise indicazioni per la revisione del calendario porta a porta:

1. **Conferma e consolidamento della frazione Organica:**
   Il modello dimostra che la frequenza ottimale è $X_r^* = 2.5$ passaggi/settimana. Si raccomanda di mantenere l'attuale assetto stagionale di AnconAmbiente (2 passaggi invernali e 3 passaggi estivi, media ~2.33), in quanto coincide matematicamente con il punto di minimo costo sociale e logistico.
2. **Conferma della raccolta bisettimanale del Vetro:**
   Il valore $X_r^* = 0.5$ (1 passaggio ogni 14 giorni) è perfettamente allineato alle caratteristiche fisiche del vetro (inerte, denso, non deperibile). Raccogliere il vetro ogni settimana genererebbe costi logistici inutili.
3. **Riorganizzazione della Plastica (Sacco Giallo):**
   L'attuale frequenza settimanale ($X_r = 1.0$) si rivela sub-ottimale a causa della bassissima densità del polimero. Nei mesi estivi o nelle zone a maggiore densità abitativa (es. quartiere Piano), si raccomanda di sperimentare una frequenza di **2 passaggi a settimana**, prevenendo l'esposizione anticipata e disordinata dei sacchi sui marciapiedi.

---

## 3. Raccomandazioni per il Bando di Gara e Dimensionamento del Parco Mezzi

Per la stesura del nuovo capitolato d'appalto del servizio di igiene urbana del Comune di Fabriano:

1. **Dimensionamento della flotta attiva:**
   La flotta fisica necessaria per coprire tutte le 3.932 utenze comunali deve essere dimensionata su un parco di **18–22 camion attivi**, parametrato sul giorno di massimo carico volumetrico/di peso (frazione vetro e organico).
2. **Inserimento di clausole di efficienza algoritmica nei criteri premianti del bando:**
   Nelle gare per l'affidamento del servizio (o nell'assegnazione degli obiettivi alla società in-house), il Comune dovrebbe richiedere obbligatoriamente l'integrazione di software di routing con euristica di risparmio (tipo Clarke-Wright o VRP avanzato), premiando i concorrenti che garantiscono una riduzione chilometrica chilometro/utenza certificabile tramite telemetria GPS di bordo.

---

## 4. Guida alla Politica Amministrativa: Come Tarare il Parametro $\gamma$

Il parametro $\gamma$ funge da "manopola politica" a disposizione dell'amministrazione comunale:

| Obiettivo Politico dell'Amministrazione | Valore Consigliato $\gamma$ | Configurazione di Servizio | Risultato Pratico per Fabriano |
|---|:---:|---|---|
| **Contenimento TARI / Spending Review** | **0.10 – 0.25** | Priorità assoluta al taglio delle spese di carburante, ore lavoro e ammortamenti. Frequenze di raccolta più dilatate. | Riduzione fino al **22.1% delle uscite veicolari settimanali** con Clarke-Wright (-32 uscite a $\gamma=0.10$). Massimo risparmio di spesa pubblica. |
| **Assetto Standard / Compromesso Equilibrato** | **0.40 – 0.60** | **Assetto attuale raccomandato.** Bilanciamento tra costo del servizio e soddisfazione cittadina. | **93 uscite con Greedy vs 88 con CW (-5 uscite settimanali)**. Flotta fissa a 18–22 mezzi, massimo decoro urbano senza aggravi di spesa. |
| **Massima Qualità / Città Turistica e Sostenibile** | **0.75 – 0.90** | Priorità al decoro urbano e alla minimizzazione dell'insoddisfazione. Frequenze di svuotamento elevate. | Il gap algoritmico si riduce (1.4%), poiché la flotta è fortemente saturata dall'alta intensità dei passaggi. Elevatissima percezione di qualità da parte del cittadino. |

---

## 5. Roadmap di Implementazione Pratica in 3 Fasi

```
Fase 1: Acquisizione Dati (Mesi 1-2)
├── Importazione grafo stradale OSM aggiornato (geometria, sensi unici, dead-end)
├── Geocodifica puntuale dei 3.932 punti di conferimento delle utenze
└── Calibrazione tempi reali di sosta e carico tramite telemetria GPS esistente

Fase 2: Integrazione del Motore Algoritmico (Mesi 3-4)
├── Implementazione dell'euristica Clarke-Wright parametrizzata sul deposito di Via Bachelet 15
├── Generazione automatica dei fogli di viaggio ottimizzati per le 5 frazioni
└── Integrazione sui terminali tablet di bordo con navigazione guidata per gli autisti

Fase 3: Monitoraggio e Validazione KPI (Mesi 5-12)
├── Confronto km effettivi percorsi vs baseline storica (-45% atteso)
├── Monitoraggio consumi di gasolio per camion e riduzione emissioni CO2
└── Adeguamento dinamico dei calendari stagionali sulla base dei volumi storici registrati
```

### Sintesi Finale per il Management
L'ottimizzazione matematica dei percorsi non è un mero esercizio teorico: a Fabriano permette di **passare da una logica intuitiva ma frammentata a una gestione industriale evoluta**, trasformando l'appalto dei rifiuti in un modello virtuoso di sostenibilità ambientale ed efficienza operativa.
