Speaker 0:
Va bene. Che cosa metti a confronto? La funzione obiettivo, poi. Sì.
Speaker 1:
Immagino le variabili decisionali che trovo, perché comunque se ho una distribuzione con tanti condomini comunque I camion dovranno fa avanti e indietro molto più spesso immagino da
Speaker 0:
Quindi io devo dire che ne so, quanto viene utilizzato il camion nelle che ne so avete deciso che so 8 ore? Sì. Ok che ne so in percentuale di queste 8 ore quanto viene voi fate, non me lo ricordo, siete voi che fate più cicli?
Speaker 1:
No, so quelli di fuori che devono entrare dopo.
Speaker 0:
Voi fate solo
Speaker 1:
un ciclo. Noi facciamo sì un giro che appunto fa il controllo di carico e quindi. Cosa però quando torna non riesce?
Speaker 0:
Ok quindi voi c'avrete il numero di camion che sono più elevati.
Speaker 1:
Sì. Ok? Sì.
Speaker 0:
Però mi puoi dire quanto è pieno il camion e quanto utilizzato sul tempo. Quindi il camion c' una sua capacità e dice guarda questo camion ovviamente questi rientrano perché hanno riempito il camion.
Speaker 1:
Sì. A meno che non continuano a girare all'infinito che non
Speaker 0:
finito. No
Speaker 1:
che magari finiscono il tempo prima di
Speaker 0:
riempire il Sì appunto quando quando tu un camion quanto è utilizzato rispetto alle sue capacità? Perché quello un senso anche cioè utilizzo il camion per tutta la sua capacità o utilizzo il camion per tutto il suo tempo. Ok? No, mi girano I camion vuoti quindi sto facendo qualche cosa che non è efficiente. Ok.
E quindi può essere interessante vedere la capacità del camion come capacità fisica o come capacità temporale, nella soluzione.
Speaker 1:
Ok?
Speaker 0:
E quanto sono contenti I gli utenti. Ok. Ovviamente, ok? Che sono I 2 pezzi della funzione obiettivo, perché tu vedi l'unione Sì. Che può essere la curva Paredo, ma mi può interessare anche sapere, perché poi ho deciso un peso e quindi mi troverà una soluzione, però vedere I 2 termini come vanno, I miei 2 algoritmi, mi può interessare l'ottimo di uno e l'ottimo dell'altro mediamente a chi danno più valore, no?
Speaker 1:
Ma magari può essere interessante anche, come dice, cambiare gli alfa e beta che noi avevamo chiamato per l'insoddisfazione.
Speaker 0:
Vedere dopo. Cioè quando fate il primo lancio, dovete vedere quanto vi viene il peso del mi spiego meglio.
Speaker 1:
Voi
Speaker 0:
c'avete 2 termini della funzione obiettivo, posti e soddisfazione. Sì. Ok? Io adesso ho preso un peso, poi ho detto mo' stiamo zitti su sto peso, dobbiamo vedere prima quanto vale la soddisfazione, proprio il numero, numero. E quanto valgono I costi, numero, lo sapete solo quando fate l'istanza.
Sì. Quindi lanciate l'istanza, vedete quanto vale questo e quanto vale questo mediamente. Ok? Perché c'è dei diversi run. A quel punto scegliete I pesi per a, stesso valore, b, più importante I costi, C, più importante soddisfazione.
Ok. Quindi mi spiego. Se questo, che ne so, mi viene la soddisfazione che pesa ordine di 10 e questo I costi ordine di 1000, lo capite da soli che è una cosa sommata così, che cosa succede? Che questo veda questo non lo vede proprio. E quindi minimizza semplicemente I costi.
Speaker 1:
Sì.
Speaker 0:
Quale che sia leoristica dovrebbe ok. Quindi che cosa stesso valore, che cosa vuol dire? Che io I costi li divido per 100. Quindi uno c' un centesimo e l'altro vale uno. I 2 pesi.
Ok. Non è la combinazione convessa, in modo tale che io riesco a fare questa cosa. Ok. Ok? Quindi questo sarà 0 0 uno e se la somma deve fa' fa' uno sarà boh com'è?
0 99?
Speaker 1:
Sì.
Speaker 0:
Se volete fa' la combinazione convessa, ok? Se invece voglio dare più importanza costi, magari così un po' tanto faccio uno su 10, 10 unità di tempo in più. Mi viene 100 contro 10 che sto facendo valere di più, no?
Speaker 1:
E questo
Speaker 0:
sempre Sì. Se voglio fare il contrario questo lo moltiplicate per 1000.
Speaker 1:
Questo diciamo è l'ordine dei costi che cioè nel senso la
Speaker 0:
Quando fate l'istanza vedete quanto vi viene questa cosa e quanto vi viene questa.
Speaker 1:
Ok.
Speaker 0:
Quindi non mettete nessun peso. Potete fare lo studio per I pesi. Studio per provare I pesi.
Speaker 1:
Quindi teniamo tra virgolette a uno, nel senso
Speaker 0:
Voi adesso non ce li mettete?
Speaker 1:
Nel senso. Lasciandone il codice del parametro metti uno e poi si moltiplica un certo valore. Per bilanciare effettivamente la la funzione obiettivo.
Speaker 0:
Non so come vengono capito? Adesso tu avrai trovato dei costi per chilometro. Sì. O per tempo non lo so. Ok?
Speaker 1:
Sì, cioè l'avevamo approssimati un po' tipo per esempio.
Speaker 0:
Cercare in letteratura e vedere che cosa vi dicono per il costo, quanto vi danno questo. Sì. Vi assicuro che c'è un qualche cosa per la soddisfazione del dell'utente. Mh. Ok?
E quindi potete trasformare.
Speaker 1:
Anche dipende pure dall'unità di misura magari uno usa per soddisfazione, cioè come la come viene concettualizzata? Certo.
Speaker 0:
Questo qua in letteratura lo trovate e potete mettere quello e vedere con quei pesi che avete trovato in letteratura come vi viene la funzione obiettivo, cioè termine a e termine b, perché voi c'avete a più
Speaker 1:
b. Sì.
Speaker 0:
Se uno dei 2 è di un'unità di misura completamente diversa, è completamente sbilanciata questa? E la potete bilanciare se volete dargli la stessa importanza.
Speaker 1:
Ok.
Speaker 0:
Ma lo sapete solamente dopo che avete fatto il
Speaker 1:
Quindi diciamo appunto decidiamo un po'.
Speaker 0:
Anche perché questa magari dipende questa è la soddisfazione dipende dalla dagli input. Quanti clienti c'hai?
Speaker 1:
Sì.
Speaker 0:
Ok? Questo invece è una variabile decisionale. Quindi lo sapete solo una volta che avete lanciato. Però già lo sapete, se un camion vi costa 1000 e gli utenti la soddisfazione è uno, che ne so. So' 10, sapete già che si è sbilanciato.
A sto punto fa distanza per distanza e mette dei pesi diversi in base a com'è distanza. Ok.
Speaker 1:
Ok. Sì, quindi cioè diciamo praticamente noi come iter che possiamo seguire appunto è provare a fare questo intanto questo bilanciamento della funzione obiettivo.
Speaker 0:
E quella dipende dall'istanza? Le spiego, quindi voi fate, decidete l'istanza. Sì. Questo procedimento lo fate sempre?
Speaker 1:
Sì, cioè inizialmente facciamo questo e poi quando bilanciamo, poi facciamo valutazione su tutto il resto che diciamo prima magari quello dei camion, eccetera. Ok.
Speaker 0:
O quei pesi che avete trovato se sono sportemente sbilanciati. Quindi la prima cosa che devo fare è trovà allora per capirci, dato il problema con 30 clienti di cui sono fatti in questo modo, poi potete fare, che ne so, 5 run, 10 run di questa cosa qui, ok? Quindi decisa, la lanciate e vedete come vi viene. E quindi per l'istanza di questo tipo, I pesi sono così, per renderli bilanciati. Poi diventano 80 sti clienti, beh cambia perché se la somma è di più, quindi
Speaker 1:
Sì. Va bene.
Speaker 0:
Ok.
Speaker 1:
Sto pensando anche se c'ho altre domande e grazie. Prego. Va bene. Allora facciamo un po' di analisi di questo genere, nel senso che il grafo comunque lo teniamo fisso, cioè nel senso
Speaker 0:
Sì, sì, sì, se ci metto così, se ci metto cosà, che succede? Ok.
Speaker 1:
Va bene. Ok, grazie.
Speaker 0:
E di lì, ci siamo.
