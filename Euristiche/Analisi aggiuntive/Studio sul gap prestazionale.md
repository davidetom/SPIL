# Studio sul Gap Prestazionale: Incroci Benchmark Sintetici vs Reale (Fabriano)

Questo documento analizza in modo incrociato i risultati dei benchmark sintetici (**B1, B2, B3**) e il benchmark su rete reale del Comune di Fabriano (**B4**), isolando le cause del crollo del gap tra Clarke-Wright e Greedy.

---

## 1. B4 (Fabriano) vs B1 (Scalabilità dimensionale)

Confronto del gap medio percentuale $F_{total}$ ($\gamma = 0.50$):

| N utenti (Grafo Sintetico) | Gap % medio (CW vs Greedy) |
|:---:|:---:|
| 100 | 17.22% |
| 250 | 11.58% |
| 500 | 6.93% |
| 750 | 9.02% |
| 1000 | 8.74% |
| **Fabriano Reale (N = 3932)** | **3.53%** |

### Analisi e Interpretazione
- Nei grafi sintetici, all'aumentare del numero di utenti $N$, il vantaggio di Clarke-Wright raggiunge un picco a reti piccole ($17.2\%$) per poi stabilizzarsi in un **plateau asintotico tra il 7% e il 9%** per $N \ge 500$.
- Sul grafo reale di Fabriano, nonostante la scala sia quasi quadrupla ($N = 3.932$), il gap scende a **3.53%**, collocandosi nettamente al di sotto del plateau sintetico.
- **Deduzione:** La dimensione della popolazione servita ($N$) non è responsabile della perdita di efficienza relativa di Clarke-Wright. Esiste un vincolo strutturale nel grafo reale che riduce le opzioni di fusione delle rotte.

---

## 2. B4 (Fabriano) vs B2 (Tipologia Urbanistica ed Edilizia)

### Distribuzione tipologica reale delle utenze di Fabriano (da `utenti.json`):

| Tipo utenza | Numero utenze | Quota % |
|---|:---:|:---:|
| **Famiglia** | 2.285 | 58.1% |
| **Palazzina piccola** | 1.049 | 26.7% |
| **Single** | 418 | 10.6% |
| **Palazzina grande / Condominio** | 180 | 4.6% |
| **Totale** | **3.932** | **100.0%** |

### Gap CW vs Greedy per gli scenari tipologici sintetici di B2:

| Scenario Sintetico (B2) | Profilo Abitativo | Gap % medio |
|---|---|:---:|
| `villette` | Bassa densità, prevalenza monofamiliari | 6.82% |
| `grandi_condomini` | Alta concentrazione di carico per nodo | 7.06% |
| `misto_periferia` | Palazzine piccole predominanti | 8.94% |
| `residenziale` | Mix famiglie e single | 9.26% |
| `suburbano` | Mix bilanciato | 9.40% |
| **Fabriano Reale** | **Prevalenza famiglie e palazzine basse** | **3.53%** |

### Analisi e Interpretazione
- Dal punto di vista urbanistico, Fabriano si colloca a cavallo tra lo scenario **`residenziale`** (58% famiglie) e lo scenario **`villette`** (pochissimi grandi condomini, solo il 4.6%).
- Nei modelli sintetici, questi scenari generano un gap favorevole a Clarke-Wright compreso tra il **6.82% e il 9.26%**.
- Il valore effettivo registrato su Fabriano (**3.53%**) è inferiore di quasi la metà anche rispetto allo scenario sintetico a minor vantaggio (`villette`).
- **Deduzione:** La composizione demografica o la volumetria dei fabbricati urbani **non spiega il dimezzamento del gap**. Anche isolando l'effetto tipologico, la rete reale oppone una resistenza intrinseca all'ottimizzazione delle rotte.

---

## 3. B4 (Fabriano) vs B3 (Distribuzione Spaziale: Cluster vs Uniforme)

### Gap CW vs Greedy per le distribuzioni spaziali sintetiche di B3:

| Distribuzione Sintetica (B3) | Configurazione Territoriale | Gap % medio | $F_{total}$ Greedy medio |
|---|---|:---:|:---:|
| `cluster` | Addensamenti densi e nuclei isolati | **9.20%** | 2.305,5 |
| `uniform` | Dispersione omogenea sul territorio | **9.26%** | 2.744,1 |
| **Fabriano Reale** | **Morfologia mista (centro storico + frazioni)** | **3.53%** | **6.049,9** |

### Analisi e Interpretazione
- Morfologicamente, il Comune di Fabriano presenta una configurazione mista:
  - Un **centro storico compatto e denso** (struttura clusterizzata nel fondovalle);
  - Quartieri residenziali e frazioni periferiche allungate lungo le direttrici montane (struttura dispersa).
- Il benchmark sintetico B3 rivela un fatto cruciale: **il gap tra Clarke-Wright e Greedy è praticamente identico tra cluster e uniforme (9.20% vs 9.26%, scarto di soli 0.06 punti percentuali)**.
- **Deduzione Risolutiva:** Poiché l'efficacia relativa di Clarke-Wright nei benchmark sintetici è totalmente insensibile alla dispersione spaziale delle utenze, **la geometria spaziale dei clienti non è la causa del crollo a 3.53% su Fabriano**. 
- Questo risultato isola definitivamente la **topologia del grafo stradale** (connettività, sensi unici, vicoli ciechi) come unico fattore causale.

---

## 4. Spiegazione Topologica Conclusiva

| Grafo | Nodi | Archi (non-orientati) | Grado Medio ($\bar{k}$) | Gap CW-Greedy % |
|---|:---:|:---:|:---:|:---:|
| **Sintetico Standard (N=500, r=1.2)** | 501 | 1.083 | **4.32** | 9.54% |
| **Reale Fabriano (OSM)** | 808 | 1.045 | **2.59** | 3.53% |

Escludendo la dimensione ($N$, B1), la tipologia d'utenza (B2) e la distribuzione geografica (B3), la causa univoca del crollo del gap su reti reali è la **struttura topologica della rete stradale**:
1. **Grado medio significativamente inferiore:** $2.59$ nodi/incrocio su Fabriano contro $4.32$ nel sintetico ($-40\%$ di connettività locale).
2. **Presenza massiccia di nodi a grado 1 e 2 (dead-end e vicoli ciechi):** In una città storica reale, molti rami stradali hanno un unico punto di ingresso e uscita. Ciò costringe qualsiasi veicolo a percorrere la stessa identica sequenza di archi per entrare e uscire, annullando la libertà combinatoria su cui Clarke-Wright costruisce il proprio vantaggio rispetto a una logica Greedy.
3. **Colli di bottiglia e ponti obbligati:** I collegamenti tra sponde fluviali o quartieri storici obbligano tutti i percorsi a convergere sui medesimi varchi, riducendo drasticamente le combinazioni di fusione delle rotte.