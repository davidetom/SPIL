# Correlazione Grado Medio ↔ Gap CW−Greedy

Parametri: N_users=99, seed=42, γ=0.5, scenario=residenziale, X_values=[0.5…3.0]

## Dati sperimentali

| Configurazione | Grado medio | Gap CW−Greedy % |
|----------------|-------------|-----------------|
| Sintetico r=0.6 | 2.400 | 13.64% |
| Sintetico r=0.7 | 2.680 | 20.79% |
| Sintetico r=0.8 | 2.840 | 21.23% |
| Sintetico r=0.9 | 3.080 | 21.57% |
| Sintetico r=1.0 | 3.380 | 21.12% |
| Sintetico r=1.1 | 3.640 | 20.68% |
| Sintetico r=1.2 | 3.980 | 25.81% |
| Sintetico r=1.4 | 4.660 | 18.84% |
| Sintetico r=1.6 | 5.000 | 17.07% |
| Sintetico r=2.0 | 5.480 | 9.90% |
| **Fabriano (reale)** *(OSM)* | **2.587** | **3.53%** |

## Regressione lineare e calcolo di R²

```
gap% = -0.018 × grado_medio + 17.717
R²   = 0.0000
```

### Come è calcolato matematicamente $R^2$:
Il coefficiente di determinazione è definito dal rapporto tra devianza residua e devianza totale:
$$R^2 = 1 - \frac{SS_{res}}{SS_{tot}} = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

Nel nostro campione:
1. **Pendenza nulla ($m = -0.018 \approx 0$):** La retta di regressione è orizzontale e coincide con la media dei gap ($\bar{y} \approx 17.7\%$).
2. **Residui identici alla devianza totale:** L'errore residuo della retta ($SS_{res} = 403.116$) eguaglia la varianza complessiva attorno alla media ($SS_{tot} = 403.119$).
   $$R^2 = 1 - \frac{403.116}{403.119} = 1 - 0.99999 \approx \mathbf{0.0000}$$
Un valore $R^2 = 0$ certifica che **il grado medio non ha alcuna capacità predittiva lineare** sul gap prestazionale.

## La vera dinamica: andamento a campana ($R^2_{\text{quadratico}} = 0.8412$)

Il fallimento del modello lineare è dovuto al fatto che i grafi sintetici descrivono una **parabola a campana (concava)**:
- **Reti sparse ($r \le 0.7$, grado < 2.5):** Pochi bivi e alternative $\rightarrow$ CW non riesce a creare fusioni $\rightarrow$ gap contenuto (~13–14%);
- **Reti intermedie ($r \in [0.9, 1.2]$, grado 3.1–4.0):** Massima flessibilità locale $\rightarrow$ CW sfrutta appieno i savings $\rightarrow$ **picco massimo del vantaggio (~22–26%)**;
- **Reti iper-dense ($r \ge 1.6$, grado > 5.0):** Quasi grafi completi $\rightarrow$ la scelta greedy di prossimità è già quasi ottimale $\rightarrow$ il vantaggio di CW scende (~10–17%).

> [!NOTE]
> Adottando un modello polinomiale di 2° grado (parabola) sui sintetici:
> $$\text{gap}\% = -4.358 \cdot \bar{k}^2 + 32.580 \cdot \bar{k} - 37.544$$
> il coefficiente di determinazione balza all'**$84.1\%$ ($R^2 = 0.8412$)**. La relazione nei sintetici esiste ed è fortissima, ma è quadratica e non lineare.

## Il punto anomalo: Fabriano reale

Il grafo reale di Fabriano ha grado medio **2.587**, direttamente confrontabile con il grafo sintetico a grado medio simile (**2.680**). Tuttavia il gap è radicalmente diverso:

| Configurazione | Grado medio | Gap CW−Greedy |
|---|---|---|
| Sintetico a grado ~2.68 | 2.68 | **20.79%** |
| Fabriano (OSM)  | 2.59 | **3.53%** |

A parità di grado medio, gap **fino a 6× inferiore** sul reale.

> [!IMPORTANT]
> Il grado medio **non è un predittore sufficiente** del vantaggio di Clarke-Wright su reti reali. Due grafi con lo stesso grado possono avere comportamenti algoritmici radicalmente diversi.

## Conclusione: limiti strutturali delle reti stradali reali

Il gap di Fabriano è basso non perché la rete sia poco connessa in senso metrico, ma per ragioni strutturali **non catturate dal grado medio**:

1. **Strade obbligate e dead-end**: in una rete OSM molti nodi sono gradi 1 o 2 (vicoli ciechi, accessi privati). Il grado medio aggregato nasconde questa eterogeneità — che invece blocca le fusioni di CW esattamente dove servirebbero.

2. **Geometria planare irregolare**: la triangolazione di Delaunay produce grafi planari con distribuzione dei gradi omogenea. Le reti stradali reali hanno distribuzione eterogenea (alcuni incroci con grado 4–5, molti con grado 1–2), riducendo le opzioni di fusione locale.

3. **Vincoli di percorrenza**: in OSM i percorsi tra nodi non sono euclidei. CW costruisce i savings su distanze stradali reali, che limitano la convenienza delle fusioni rispetto al caso sintetico euclideo.

**Implicazione per la tesina:** le analisi sui grafi sintetici (B1–B3) sovrastimano sistematicamente il vantaggio di Clarke-Wright rispetto a Greedy. Il trasferimento diretto delle conclusioni sintetiche al caso reale richiede cautela. Il benchmark B4 (Fabriano) non è solo una "verifica" — è un correttore essenziale che ridimensiona le aspettative sugli algoritmi in contesti operativi reali.