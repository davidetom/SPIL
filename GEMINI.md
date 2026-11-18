# GEMINI.md — Istruzioni Permanenti & Protocollo Operativo (Progetto SPIL)

Questo file governa il comportamento di Antigravity CLI su questo repository per la tesina di **Simulazione dei Processi Industriali e Logistici** (*Prof.ssa Ludovica Adacher*, Università degli Studi Roma Tre — autori: **Davide Tommasino** e **Sofia Garofoli**).

---

## Sezione 1 — Dynamic Model Routing & Token Optimization Protocol (OBBLIGATORIO AD OGNI PROMPT)

### 1.1 Classificazione Preliminare in 3 Tier
Prima di eseguire qualsiasi operazione, classifica il task richiesto dall'utente in uno dei seguenti 3 Tier:

- **Tier 1 (Routine / Esplorazione / Formattazione — Basso consumo):**
  - *Ambito:* ricerca file (`grep`, `find`), controlli sintattici e anti-artefatti su `.tex`, aggiornamento tabelle LaTeX con numeri già estratti, aggiornamento di [`STATO_PROGETTO.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/STATO_PROGETTO.md), operazioni Git (`status`, `add`, `commit`, `branch`, `merge`).
  - *Modello ideale:* **Flash** o **Hydrogen** per entrambi (Davide e Sofia), oppure delega a sub-agenti leggeri (`flash` / `flash_lite`).
- **Tier 2 (Implementazione Standard & Data Processing — Medio consumo):**
  - *Ambito:* modifiche standard agli script Python ([`Greedy.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Greedy.py), [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py), [`Generazione_Dati.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_Dati.py), [`main.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/main.py)), script di generazione grafici in Python (`matplotlib`), estrazione statistiche da CSV con `pandas`, stesura di bozze di testo tecnico già delineate.
  - *Modello ideale:* **Flash** / **Hydrogen** (o modello intermedio bilanciato).
- **Tier 3 (Ragionamento Critico, Matematica & Architettura — Alto consumo):**
  - *Ambito:* interpretazione metodologica delle critiche della Prof.ssa Adacher ([`Incontro 7.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%207.md)), progettazione e verifica formale di equazioni/vincoli/soglie (nuova legge sub-lineare/logaritmica $Q_{ru}(X_r)$, inversioni di rotta in Clarke-Wright, calibrazione di $k_{\text{scala}}$ e $\gamma$, dominanza di Pareto), design dei nuovi scenari sperimentali su Fabriano (tipologie vincolate centro/periferia), debug algoritmico complesso.
  - *Modello ideale:* **Argon** per Davide (`/model argon`) | **Gemini 3.1 Pro** su piano Plus per Sofia (`/model gemini-3.1-pro`), da attivare **solo dopo** aver raccolto il contesto necessario in Tier 1/2.

### 1.2 Pre-Flight Check (Obbligatorio in testa a ogni risposta)
All'inizio di **ogni** risposta operativa, stampa sempre come prima riga:

```text
[ROUTING: Tier <1|2|3> | Task: <breve descrizione> | Modello ideale: <Flash/Hydrogen | Argon (Davide) / Gemini 3.1 Pro (Sofia)> — <azione>]
```

- **Regola di Escalation (Tier 3 su modello leggero):** Se il task è classificato **Tier 3** e la sessione corrente gira su un modello leggero, **fermati** dopo aver raccolto il contesto preliminare e suggerisci esplicitamente:
  - a Davide: `/model argon`
  - a Sofia: `/model gemini-3.1-pro`
- **Regola di De-escalation (Tier 1 su modello costoso):** Se il task è **Tier 1** e la sessione corrente è su Argon / Pro, rispondi in modo ultra-conciso (o delega a un sub-agente `flash`) e segnala che per i task successivi di routine conviene passare a `/model flash` o `/model hydrogen`.

### 1.3 Context Hygiene (Risparmio Token)
1. **Zero dump di `.csv` o `.pdf` nel contesto:** È severamente vietato leggere per intero file CSV o PDF compilati con `read_file`. Per ispezionare i CSV usa esclusivamente one-liner Python/pandas o `head -n 5` via terminale. Per la tesi, leggi sempre e solo i sorgenti `.tex` in [`latex/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex).
2. **Lettura mirata:** Usa `StartLine` e `EndLine` in `read_file` per leggere solo le sezioni `.tex` o le funzioni Python pertinenti al task.
3. **Output chirurgici:** Proponi e applica sempre diff/patch locali (`edit_file`). Non riscrivere mai interi file o interi capitoli se non esplicitamente richiesto.
4. **Reset frequente del contesto:** Al termine di ogni sotto-task significativo, aggiorna [`STATO_PROGETTO.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/STATO_PROGETTO.md) (massimo 10 righe per voce di changelog) e suggerisci all'utente di eseguire `/clear` (o `/compact`) per ripartire a contesto pulito.

---

## Sezione 2 — Mappa del Repository, Stack Tecnologico e Convenzioni Operative

### 2.1 Organizzazione del Team e Workflow Git
- **Divisione compiti:**
  - **Davide Tommasino:** sviluppo principale (architettura e refactoring codice Python, esecuzione simulazioni, analisi dati, grafici Python e stesura LaTeX).
  - **Sofia Garofoli:** interventi mirati principalmente sulla stesura/revisione LaTeX in [`latex/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex).
- **Gestione Git:**
  - Il lavoro attivo sul branch `emergenza` (creato per isolare un problema di push precedente) va riunificato in sicurezza su `main`.
  - Prima di ogni modifica strutturale, verificare `git status` e mantenere commit atomici e descrittivi.

### 2.2 Stack Tecnologico e Convenzione di Esecuzione
- **Python 3.12.4:** `numpy`, `scipy` (`csr_matrix`, `dijkstra`, `Delaunay`, `ConvexHull`, `cKDTree`, `stats`), `pandas`, `matplotlib`, `osmnx`, `geopandas`, `psutil`, `concurrent.futures.ProcessPoolExecutor`.
- **Working Directory Obbligatoria (`src/`):** Tutti gli script Python devono essere eseguiti con directory di lavoro [`src/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src) oppure risolvere i percorsi tramite `ROOT = Path(__file__).resolve().parent` (puntando a `src/`). Gli script accessori oltre ai 4 moduli core nella root di `src/` devono essere organizzati in sottocartelle tematiche per funzionalità.
- **LaTeX:** Classe [`latex/TesiDiaUniroma3.cls`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/TesiDiaUniroma3.cls), entry-point [`latex/MainTESINA.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/MainTESINA.tex). Il PDF ufficiale compilato da mantenere aggiornato è **`tesinaTommasinoGarofoli.pdf`** (in [`latex/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/tesinaTommasinoGarofoli.pdf) e [`docs/attivo/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/tesinaTommasinoGarofoli.pdf)).
- **Grafici (Python standard, MATLAB deprecato):**
  - Tutti i **nuovi grafici** vengono generati in **Python** (`matplotlib`, export a `300 dpi`).
  - Gli script MATLAB R2025a in [`src/script matlab (old)/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/script%20matlab%20(old)) sono **legacy/deprecati** (qualora toccati per manutenzione storica, mantenere: path cross-platform `char(java.lang.System.getProperty('user.home'))` invece di `getenv('HOME')`, regex `'gamma(\d+\.\d+)'` invece di `'gamma([\d.]+)'`, e `exportgraphics(..., 'Resolution', 300)`).
  - **Palette colori vincolante per coerenza visiva:**
    - **Greedy:** Blu profondo — Hex `#2171b5` (o `#1f77b4`) / RGB `[0.13, 0.47, 0.71]`
    - **Clarke-Wright:** Arancio bruciato — Hex `#d95f0e` (o `#d95f02`) / RGB `[0.84, 0.37, 0.05]`

### 2.3 Mappa delle Directory (Attive vs Archivio Read-Only)
- **Percorsi ATTIVI:**
  - [`latex/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex): [`MainTESINA.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/MainTESINA.tex), [`introduzione.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/introduzione.tex), [`capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex), [`capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex), [`capitolo-3.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-3.tex), [`conclusioni.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/conclusioni.tex) e le figure attive in [`latex/immagini/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/immagini).
  - [`docs/attivo/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo): **unica cartella documentale di riferimento**, contenente [`Versione 7 SPIL.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Versione%207%20SPIL.md), [`Incontro 7.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%207.md), [`Incontro 6.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%206.md) e [`tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/tesinaTommasinoGarofoli.pdf).
  - [`src/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src):
    - Core: [`main.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/main.py), [`Greedy.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Greedy.py), [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py), [`Generazione_Dati.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_Dati.py).
    - Rete reale OSM Fabriano: [`src/Generazione_grafo_Fabriano/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_grafo_Fabriano) (`dati_reali/grafo_aumentato.graphml`, `dati_reali/utenti.json` con $3932$ utenze e deposito `node_id = -99999` in Via Vittorio Bachelet 15, Anconambiente S.p.A.).
    - Sottocartelle operative: [`src/testing/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/testing), [`src/algoritmo_ottimizzato/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/algoritmo_ottimizzato), [`src/generatori figure/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/generatori%20figure), [`src/seeds/seeds.json`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/seeds/seeds.json).
    - Formato CSV di riferimento: convenzione di [`src/risultati_seed/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/risultati_seed) (`bench, seed, N, scenario, modo, rifiuto, X_r, algoritmo, n_vehicles, n_utenti_serviti, F_insoddis, F_costo_fisso, F_viaggio, F_lavoro, sat_fisica, sat_tempo, k_scala, algo_time_sec`), con selezione dell'ottimo $X_r^*(\gamma)$ in post-elaborazione.
- **Percorsi ARCHIVIO (Read-Only, da non usare né modificare):**
  - [`docs/storico/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/storico) e [`docs/altro/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/altro)
  - [`latex/immagini/old/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/immagini/old) (vecchie figure v1)
  - [`src/script matlab (old)/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/script%20matlab%20(old))

### 2.4 Regole di Qualità del Lavoro e Controlli LaTeX
- **Approccio modulare (*confirm-before-proceeding*):** Spiega la modifica, proponi lo snippet chirurgico e attendi conferma prima di riscritture invasive.
- **Zero spiegazioni non verificate:** Non inventare mai giustificazioni "plausibili a occhio" per spiegare l'andamento di una curva o di una tabella; ogni affermazione nel Capitolo 3 deve essere dimostrata dai numeri estratti dai CSV o dalla formulazione matematica.
- **Controlli `grep` pre-consegna su LaTeX:** Prima di compilare o chiudere modifiche ai file `.tex`, eseguire sempre un `grep -rnE "oaicite|\[cite"` su [`latex/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex) per garantire l'assenza totale di artefatti di citazione AI invisibili, e verificare la coerenza dei riferimenti incrociati (`\ref`, `\label`).

---

## Sezione 3 — Notazione Matematica e Parametri Vincolanti

L'unica fonte di verità matematica è costituita da [`latex/capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex) + [`latex/capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex) (riassunti in [`docs/attivo/Versione 7 SPIL.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Versione%207%20SPIL.md)).

### 3.1 Variabili Decisionali e Funzione Obiettivo
- **Variabili decisionali (per ciascun rifiuto $r \in R$):**
  1. $X_r \in \mathcal{X}$: frequenza di ritiro settimanale;
  2. $V_r \in \mathbb{N}$: numero di camion attivati per singolo giro (attivazioni settimanali $= V_r \cdot X_r$);
  3. $P_v$: sequenza di routing del veicolo $v \in V_r$.
- **Funzione obiettivo pesata (usata nella Grid Search per selezionare $X_r^*$):**
  $$F_{\text{total}}(X_r) = \gamma \cdot \left(F_{\text{insoddis}}(X_r) \cdot k_{\text{scala}}\right) + (1 - \gamma) \cdot F_{\text{costi}}(X_r)$$
  dove:
  - $F_{\text{insoddis}}(X_r) = \sum_{u \in U_G} \left[\alpha \max(0, x^*_{r t_u} - X_r) + \beta \max(0, X_r - x^*_{r t_u})\right]$
  - $F_{\text{costi}}(X_r) = F_{\text{costo\_fisso}}(X_r) + F_{\text{viaggio}}(X_r) + F_{\text{lavoro}}(X_r) = c_r V_r X_r + X_r cd \sum_{v \in V_r} \sum_{(a,b) \in P_v} d_{ab} + X_r cm \sum_{v \in V_r} T_v$
  - $T_v = \sum_{(a,b) \in P_v} \tau_{ab} + \sum_{u \in P_v} s_{r t_u} \le L$ *(il tempo di servizio per fermata $s_{r t_u}$ è fisso per rifiuto e tipologia di utenza, NON moltiplicato per $Q_{ru}(X_r)$)*.
  - $\sum_{u \in P_v} Q_{ru}(X_r) \le C_r$.
- **Nota sul refactoring in corso (post-Incontro 7):**
  - La legge di carico $Q_{ru}(X_r)$ viene modificata da $W_{r t_u}/X_r$ a un andamento **non lineare / logaritmico** (decrescita meno che proporzionale al crescere della frequenza $X_r$), restringendo la griglia $\mathcal{X}$ a frequenze operative realistiche.
  - Nelle analisi del Capitolo 3 è **vietato** usare il Gap % su $F_{\text{total}}$ o il confronto a $X_r$ fissato come indicatori principali: il confronto tra Greedy e Clarke-Wright va sempre condotto **sulle soluzioni ottime scelte da ciascun algoritmo** $(X_r^*, V_r^*, \text{km}, \text{ore})$ e sui **valori grezzi non pesati** $(F_{\text{costi}}, F_{\text{insoddis}})$ nel piano bi-criterio.

### 3.2 Parametri Globali e Tabelle Merceologiche / Utenze
- **Costanti globali:**
  - $cd = 2.0\text{ €/km}$ | $cm = 0.25\text{ €/min}$ ($15\text{ €/h}$) | $L = 480\text{ min}$ ($8\text{ h}$) | Velocità media $= 25\text{ km/h}$ ($\tau_{ab} = d_{ab} \cdot \frac{60}{25}\text{ min}$)
  - $\alpha = 10.0$ (penalità sotto-servizio) | $\beta = 2.0$ (penalità sovra-servizio)
  - Politiche di riferimento: $\gamma \in \{0.10\text{ (Pro-Azienda)},\, 0.50\text{ (Bilanciata)},\, 0.90\text{ (Pro-Cittadino)}\}$
  - Legge di carico sub-lineare: $Q_{ru}(X_r) = W_{r t_u} \cdot \max(0.10,\, 0.95 - 0.25\ln(X_r + 0.5))$, con $\mathcal{X} = [0.5, 1.0, \dots, 4.0]$.

- **Parametri per Tipologia di Rifiuto ($r \in R$):**

| Rifiuto (`r`) | Capacità $C_r$ (kg) | Costo fisso $c_r$ (€) | Produzione base $W_{\text{base}}$ (kg/sett.) | Freq. ideale base $x^*_{\text{base}}$ (ritiri/sett.) | Servizio base $s_{\text{base}}$ (min) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `organico` | $1500$ | $120/3 = 40.0$ | $3.0$ | $2.5$ | $1.2/3 = 0.40$ |
| `carta` | $1500$ | $80/3 \approx 26.67$ | $2.0$ | $1.0$ | $1.0/3 \approx 0.33$ |
| `plastica` | $1000$ | $70/3 \approx 23.33$ | $1.7$ | $1.7$ | $1.0/3 \approx 0.33$ |
| `vetro` | $2000$ | $110/3 \approx 36.67$ | $1.2$ | $0.5$ | $1.5/3 = 0.50$ |
| `indifferenziata` | $2000$ | $90/3 = 30.0$ | $2.5$ | $2.0$ | $1.2/3 = 0.40$ |

- **Moltiplicatori per Tipologia di Utenza ($t_u \in T$):**
  *(dove $W_{r t_u} = W_{\text{base},r} \cdot \text{Molt}_W$, $x^*_{r t_u} = x^*_{\text{base},r} \cdot \text{Molt}_{x^*}$, $s_{r t_u} = s_{\text{base},r} \cdot \text{Molt}_s$)*

| Tipologia (`t_u`) | Molt. Produzione ($\text{Molt}_W$) | Molt. Freq. Ideale ($\text{Molt}_{x^*}$) | Molt. Tempo Servizio ($\text{Molt}_s$) | Mix Reale Fabriano ($N=3932$) |
| :--- | :---: | :---: | :---: | :---: |
| `single` | $0.5$ | $0.7$ | $1.0$ | $10.6\%$ |
| `famiglia` | $1.0$ | $1.0$ | $1.0$ | $58.1\%$ |
| `palazzina_piccola` | $6.0$ | $1.5$ | $3.0$ | $26.7\%$ |
| `palazzina_grande` | $20.0$ | $2.0$ | $3.0$ | $4.6\%$ |

---

## Sezione 4 — Regola di Aggiornamento Memoria

1. **Lettura preliminare obbligatoria:** All'inizio di ogni nuova sessione o prima di intraprendere un task, leggi sempre [`STATO_PROGETTO.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/STATO_PROGETTO.md) per conoscere lo stato di avanzamento, le decisioni attive e il prossimo step in coda.
2. **Aggiornamento post-task:** Al termine di ogni modifica significativa (al codice, ai CSV o ai file `.tex`), aggiorna lo stato dei task e aggiungi una voce datata nella sezione **Changelog** di [`STATO_PROGETTO.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/STATO_PROGETTO.md) (massimo 10 righe, concisa e con link ai file toccati), suggerendo poi `/clear` per mantenere pulito il contesto.
