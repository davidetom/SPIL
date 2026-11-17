# STATO_PROGETTO.md — Memoria Viva del Progetto SPIL

> **Ultimo aggiornamento:** 2026-11-17
> **Branch corrente:** `emergenza` (da riunificare in `main`)
> **PDF di riferimento:** [`latex/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/tesinaTommasinoGarofoli.pdf) / [`docs/attivo/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/tesinaTommasinoGarofoli.pdf)
> **Formulazione matematica attiva:** [`latex/capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex) + [`latex/capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex) + [`docs/attivo/Versione 7 SPIL.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Versione%207%20SPIL.md)

---

## 1. Evoluzione Storica del Progetto (v1 $\rightarrow$ Incontro 6 $\rightarrow$ v2)

### 1.1 Fase 1 — Baseline v1 e Voto 27 (Settembre–Ottobre 2026)
- Sviluppo completo del simulatore in Python ([`Generazione_Dati.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_Dati.py), [`Greedy.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Greedy.py), [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py), [`main.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/main.py)) e della pipeline GIS/OSM per la mappa reale di Fabriano ($3932$ utenti residenziali, $808$ nodi stradali, deposito Anconambiente in Via Bachelet 15).
- Prima versione della tesina ([`docs/storico/tesinaTommasinoGarofoli_old.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/storico/tesinaTommasinoGarofoli_old.pdf)) basata su singola run (seed 42) per i Benchmark B1–B4, 3 seed per B5, e 2 Benchmark Trasversali (T1, T2) con grafici generati in MATLAB ([`src/script matlab (old)/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/script%20matlab%20(old))).
- Valutazione iniziale della docente: **voto 27**, con osservazione che i Capitoli 1 e 2 erano approvati ma il Capitolo 3 presentava i risultati in modo troppo descrittivo su $F_{\text{total}}$ senza trarre conclusioni fisiche e gestionali rilevanti.

### 1.2 Fase 2 — Incontro 6 e Sviluppo della v2 (Ottobre–Novembre 2026)
- Nell'[`Incontro 6.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%206.md) la Prof.ssa Adacher ha chiesto di esplicitare l'uso fisico dei camion (saturazione fisica e temporale sul turno di 8 ore), le componenti non pesate di costo e insoddisfazione e il bilanciamento dei pesi della funzione obiettivo.
- Interventi tecnici eseguiti per la **v2**:
  - **Fix determinismo e invarianza a $\gamma$ in [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py):** rimossa la scalatura superflua per $(1-\gamma)$ sui savings e introdotto `kind="stable"` in `np.argsort`, garantendo che a parità di $X_r$ le rotte siano rigorosamente indipendenti da $\gamma$.
  - **Allineamento matematico di $T_v$ in [`latex/capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex) e [`latex/capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex):** corretta l'equazione del tempo del veicolo $T_v = \sum \tau_{ab} + \sum s_{r t_u}$ (senza moltiplicare $s_{r t_u}$ per $Q_{ru}(X_r)$, in pieno accordo col codice Python).
  - **Campagna multi-seed (30 seed) e post-processing in Python:** creati [`batch_seed.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/testing/batch_seed.py), [`batch_fabriano.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/testing/batch_fabriano.py) ($1260$ CSV in [`src/risultati_seed/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/risultati_seed)), [`analisi_gamma.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/risultati_seed/analisi_gamma.py), [`t1_generalita.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/testing/t1_generalita.py), [`t2_profilo.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/testing/t2_profilo.py) e la ricerca potata in [`main_ottimizzato.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/algoritmo_ottimizzato/main_ottimizzato.py).

> [!WARNING]
> **REGOLE DEPRECATE / ARCHIVIATE DOPO L'INCONTRO 7:**
> Tutte le analisi e regole della v2 incentrate sui **benchmark sintetici (B1, B2, B3, B5)**, sull'uso del **Gap % su $F_{\text{total}}$** come metrica guida e sui **profili di confronto tra algoritmi a frequenza $X_r$ fissata** sono ufficialmente **deprecate e superate** dalle direttive dell'Incontro 7.

---

## 2. Direttive dell'Incontro 7 (17 Novembre 2026) — Obiettivi Attivi

Dall'analisi di [`docs/attivo/Incontro 7.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Incontro%207.md) emergono 5 richieste vincolanti della Prof.ssa Adacher:

1. **Modifica della legge del carico $Q_{ru}(X_r)$ e della griglia $\mathcal{X}$:**
   - La relazione inversamente proporzionale $Q_{ru}(X_r) = W_{r t_u} / X_r$ dimezza esattamente il rifiuto al raddoppiare della frequenza, rendendo la variazione tra frequenze e la differenza tra le euristiche troppo proporzionale/piatta.
   - **Azione:** Sostituire $W_{r t_u}/X_r$ in [`Greedy.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Greedy.py), [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py) (o centralmente in [`Generazione_Dati.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_Dati.py)) con una **funzione decrescente sub-lineare / logaritmica** (es. riduzioni del tipo $100\% \to 90\% \to 75\% \to 60\%$ al crescere dei passaggi) e limitare la griglia delle frequenze $\mathcal{X}$ a un massimo realistico (es. fino a $3$–$4$ o max $5$ ritiri/settimana).
2. **Valutazione miglioramento Clarke-Wright (inversioni di rotta):**
   - Valutare l'introduzione della possibilità di **invertire l'orientamento di una rotta** durante la fase di merge in [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py) (consentendo fusioni testa-testa e coda-coda oltre a coda-testa, dato che il grafo stradale di raccolta è reso bidirezionale/simmetrico).
3. **Stop al confronto a frequenza $X_r$ fissata e al Gap % come indicatore principale:**
   - $X_r$ è una delle 3 variabili decisionali ($X_r, V_r, P_v$): Greedy e Clarke-Wright devono essere confrontati **sulla soluzione ottima che ciascuno restituisce** $(X_r^{*,G}, V_r^{*,G}, P_v^{*,G})$ vs $(X_r^{*,CW}, V_r^{*,CW}, P_v^{*,CW})$, mostrando quante volte ciascuno decide di passare, quanti camion usa, quanto sono saturi e quanto costano le componenti.
4. **Trasparenza sui pesi ($\gamma, k_{\text{scala}}$) e analisi Bi-Criterio non pesata:**
   - Mostrare esplicitamente i valori numerici grezzi (non pesati) di **$F_{\text{costi}}$ (€)** e **$F_{\text{insoddis}}$**, verificando l'ordine di grandezza dei due termini prima e dopo il bilanciamento, e rappresentare le soluzioni dei due algoritmi come punti nel piano cartesiano $(F_{\text{costi}}, F_{\text{insoddis}})$ per evidenziare visivamente la dominanza di Pareto.
5. **Focus esclusivo sul grafo fisso di Fabriano con variazione di tipologie e disposizione spaziale:**
   - Abbandonare i benchmark su grafi sintetici e la variazione di $N$.
   - Mantenere **fisso il grafo reale di Fabriano** (e fisso il numero di utenti), usando il seed ($\sim 10$ run per scenario) per variare la **composizione tipologica** e la **distribuzione spaziale delle tipologie** (es. scenari eterogenei o vincolati geometricamente: **famiglie/condomini ad alto carico tutti in centro e single in periferia, oppure utenti pesanti lontani dal deposito**), così da evidenziare dove la miopia locale di Greedy entra in crisi rispetto a Clarke-Wright.

---

## 3. Roadmap Operativa Prioritaria

- [ ] **FASE 1 — Refactoring del Modello e delle Euristiche (`src/`):**
  - [ ] **1.1:** Definire e implementare la nuova legge sub-lineare/logaritmica per $Q_{ru}(X_r)$ e aggiornare la griglia $\mathcal{X}$ (`X_VALUES`) in [`Generazione_Dati.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Generazione_Dati.py), [`Greedy.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/Greedy.py), [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py) e [`main.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/main.py).
  - [ ] **1.2:** Analizzare e testare l'impatto dell'inversione di rotta nei merge di [`ClarkeWright.py`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/ClarkeWright.py).
  - [ ] **1.3:** Riunificare in sicurezza il branch `emergenza` su `main`.
- [ ] **FASE 2 — Script e Report su Singola Istanza per Ricevimento Prof.ssa Adacher:**
  - [ ] **2.1:** Creare uno script dedicato in `src/` che esegua Greedy e Clarke-Wright su **una singola istanza** di Fabriano e stampi/esporti una tabella completa e trasparente con: valori grezzi di $F_{\text{costi}}$ (scomposto in fisso, viaggio, lavoro) e $F_{\text{insoddis}}$, valore di $k_{\text{scala}}$, termini pesati a $\gamma \in \{0.1, 0.5, 0.9\}$, e variabili decisionali ottime scelte dai due algoritmi ($X_r^*, V_r^*, V_r^*\cdot X_r^*, \text{km}, \text{ore}, \text{Sat}_{\text{fis}}, \text{Sat}_{\text{tempo}}$), più grafico bi-criterio non pesato $(F_{\text{costi}}, F_{\text{insoddis}})$.
- [ ] **FASE 3 — Nuova Campagna Sperimentale su Fabriano & Ristrutturazione Capitolo 3 (`latex/`):**
  - [ ] **3.1:** Implementare il generatore di scenari su grafo fisso di Fabriano (variazione proporzioni tipologiche e posizionamento spaziale vincolato Centro vs Periferia su ~10 seed, salvataggio CSV secondo lo standard di [`src/risultati_seed/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/src/risultati_seed)).
  - [ ] **3.2:** Generare le nuove figure in Python (`matplotlib`, 300 DPI) focalizzate su: punti/frontiere di Pareto non pesate $(F_{\text{costi}}, F_{\text{insoddis}})$, frequenze ottime $X_r^*$, flotta $V_r^*$, saturazioni e costi.
  - [ ] **3.3:** Aggiornare [`latex/capitolo-1.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-1.tex) (formula $Q_{ru}(X_r)$), eventuale [`latex/capitolo-2.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-2.tex) (se modificato CW), e riscrivere [`latex/capitolo-3.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/capitolo-3.tex) e [`latex/conclusioni.tex`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/conclusioni.tex), ricompilando [`latex/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/tesinaTommasinoGarofoli.pdf).

---

## 4. Changelog

- **2026-11-17 — Inizializzazione Memoria Persistente e Allineamento Post-Incontro 7:**
  - Eseguita ricognizione completa di codice, CSV, `.tex` (v1 e v2), `Incontro 6.md`, `Incontro 7.md` e note storiche Obsidian.
  - Creati [`GEMINI.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/GEMINI.md) (con protocollo Dynamic Model Routing a 3 Tier, Context Hygiene, mappa repo e parametri vincolanti) e [`STATO_PROGETTO.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/STATO_PROGETTO.md).
  - Archiviato `Versione 6 SPIL.md` in [`docs/storico/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/storico/Versione%206%20SPIL.md) e creato [`docs/attivo/Versione 7 SPIL.md`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/docs/attivo/Versione%207%20SPIL.md) allineato ai `.tex` e all'Incontro 7.
  - Spostate le 30 figure obsolete della v1 in [`latex/immagini/old/`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/immagini/old) e rimosso il duplicato `latex/MainTESINA.pdf`, mantenendo [`latex/tesinaTommasinoGarofoli.pdf`](file:///Users/davide_tom/Documents/Obsidian%20Note/SPIL/latex/tesinaTommasinoGarofoli.pdf) come unico PDF target.
