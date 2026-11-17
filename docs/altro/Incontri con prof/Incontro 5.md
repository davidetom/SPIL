Speaker 0:
Partecipare a routing diversi, però tu vai a unire I canoni. Mhmm. Perché vai a unire I routing, non I clienti. Ok. In questo caso specifico non ci vai mai 2 volte allo stesso utente.
Quindi non c'è manco bisogno di andare a confrontare se già ci 6 passato.
Speaker 1:
Ok.
Speaker 0:
Perché questi qua c'hanno il secchionetto, o c'entrano o non c'entra, punto. Non è che ne prendi una parte, per cui potresti andarci 2 volte. Mettici quello che O c'entra o non c'entra. Quindi o raggiungi o non raggiungi? Ok.
All'inizio lo cambio con un cliente solo e li incomincio a fondere. Se unisco gli AJ il routing sarà I0IJ0. Se faccio j I il routing sarà 0JI0.
Speaker 1:
Sì.
Speaker 0:
Ok? E ci metto dentro quei 2 utenti. Per buy col routing diventa così dopo le prime fusioni, no? Fra coppie.
Speaker 1:
Mhmm. Poi
Speaker 0:
c'avrà qualcuno che c' 2 utenti, qualcuno che ce ne uno, rifai il il merge diciamo, quindi che ne so, poi fatto eejay e ck. Allora se fai il camion uno col camion 2, EJK. Se fai il camion 2 col camion uno, è KIJ.
Speaker 1:
Ok. Però facendo così, cioè noi c'abbiamo all'inizio le coppie diciamo che I percorsi son singoli diciamo, quindi tutti I camion diversi.
Speaker 0:
Tutti I camion diversi, tutti I clienti diversi.
Speaker 1:
Se io prendo la prima coppia fuso Li
Speaker 0:
devi calcolare tutti e prendi il migliore.
Speaker 1:
Sì, e prende il migliore. Cioè nel senso fondo I 2 migliori diventano un camion, ma poi devo ricalcularmi diciamo tutte le possibili coppie con quel camion? Cioè nel senso di possibili scambi tra quel camion nuovo e tutti gli altri rimanenti?
Speaker 0:
Finché finché trovi scambi convenienti. Cioè quelli tutti I saving, no?
Speaker 1:
Ok. Cioè quindi ogni volta ricalcolo diciamo questa lista diciamo di di scambi ordinata, ok.
Speaker 0:
Tu poi pure fa' prendola più conveniente se sono IEJ, lì puoi fare questo con ho capito che allora forse che controllo volevi fare? Allora che cosa succede? Tu fai per ogni coppia I j con I diverso da j. All'inizio questi so' tutti da solo. Ok.
Prendi il migliore e ti dice che è LM. Sì. Quindi da questo ti esce LM.
Speaker 1:
Sì.
Speaker 0:
Con camion solo, ok?
Speaker 1:
Mhmm.
Speaker 0:
Allora tu puoi benissimo fare di tutti questi altri prendi tutti dove non c'è lm e falli quelli più convenienti. Lo fai e poi in modo che così li fai di più alla volta.
Speaker 1:
Ok ok.
Speaker 0:
Ok? E fai quelli a 2. Dopo dopo
Speaker 1:
Sì, infatti, cioè per questo così non calcolo ogni volta.
Speaker 0:
Intanto è per ogni in realtà so I camion, so I nodi Ok. Questo è per I camion quindi a un certo punto se non ti prendi il camion, facciamo che so uno 2, so 10 camion, faccio uno con 2, uno con 3, uno con 4, uno con 5, uno con 6, uno 2 co uno, 2 co 3, 2 co 3, li faccio tutte, ok? Tutte le coppie, prendo il migliore, Il migliore me lo dà 4 o 5. Io adesso 4 o 5 non lo considero più in tutte quelle coppie. Riprendo il migliore in modo che così l'hai calcolato solo una volta, no?
Ok, se non c' 4 o 5 facciamo che 2 o 3, quindi unito 4 o 5.2 o 3, intanto sono cicli vado avanti riprendo il migliore senza considerare, se non ci stanno se non chiamano nessuno dei camion che è già unito vado avanti su sta lista.
Speaker 1:
Però non potrebbe capitare che magari cioè nel senso all'inizio faccio uno 2 e li li fondo, quindi mi viene il camion uno 2. Se io magari nella lista rimanente quello migliore sarebbe 5 6.
Speaker 0:
5 6 lo posso fare, non c'entra niente con Però
Speaker 1:
non potrebbe essere che cioè ricontrollando magari mi conviene più fare uno 2 fonderlo con magari con 5 o con 6?
Speaker 0:
No no quello questo è come vuoi o ne prendi solo uno e quindi fai uno 2 cioè fai uno alla volta prendi solo il migliore fai quello la fusione e poi quello lì diventa uno 2 quindi ricalcoli tutte le coppie con il camion che con tutti I camion dove il camion 2 l'hai buttato. Mi spiego meglio.
Speaker 1:
No, quello, perché appunto se non rifai questa cosa magari può capitare che
Speaker 0:
Puoi decidere
Speaker 1:
saltiamo una coppia da Esatto,
Speaker 0:
puoi decidere sia di fare un merge fatto così, sia invece che ti prendi tutte le coppie da uno e le fonde tutte quelle possibili, che è come viene, senza riprendere lo stesso nodo e poi li rilanci. Oppure lo fai un merge alla volta. Ok. Quello che stai dicendo te è un merge alla volta, quindi prendo io il migliore, lo faccio. E poi comunque divento il nuovo camion e rifaccio tutti I camion.
Ok. Togliendo quello che ho chiuso. Mi son spiegata?
Speaker 1:
Sì sì. Ok.
Speaker 0:
Se vuoi altro?
Speaker 1:
No vabbè se vogliamo rivedere al volo il gridi la logica ma comunque ce l'aveva data buona a parte il fatto che all'inizio calcolavamo soltanto I costi e invece giustamente dobbiamo metterci anche l'insoddisfazione per fare tutta la funzione obiettivo insieme. Però a parte quello mi sembra che andava tutto bene. Poi una domanda, una volta che facciamo effettivamente gli algoritmi che funzionano, perché il GREATER l'abbiamo già implementato in realtà. Poi cioè nel senso come possiamo proseguire? Facciamo dei Facciamo dei
Speaker 0:
mi chiedete l'istanza cioè
Speaker 1:
senso Facciamo dei dai,
Speaker 0:
Fate solamente una rete che rappresenta il paese. Ok. O dentro gli utenti.
Speaker 1:
Quindi prendiamo un tot di utenti e lo fissiamo?
Speaker 0:
Sì. Ok. Quindi c'avete la rete e ci buttate dentro gli utenti. Ok. Poi potete giocare su, ci sono tanti utenti di tipo uno, so' tutti utenti di tipo uno e c'è un 10 per 100 di tipo 5, ok?
Che cosa succede? No, so' così cambiate ste cose qua.
Speaker 1:
Ok.
Speaker 0:
Ok?
Speaker 1:
Quindi cioè cambiamo più magari la tipologia di utenti mantenendo il numero diciamo totale invariato?
Speaker 0:
Sì, perché quelli sono oppure se risorse. Potreste anche vedere se ci sono pochi utenti come funziona l'algoritmo, come funzionano gli algoritmi, altri utenti se so sparsi, se stanno lontani, se stanno vicini?
Speaker 1:
Perché io ho pensato anche a una cosa del genere, magari di prendere
Speaker 0:
cioè la rete rimane
Speaker 1:
Graffi cittadini magari con meno utenti o più utenti?
Speaker 0:
Certo. Ok. Però la rete la fate la generavi solo una volta. Sono I nodi che poi cambiano. Sì.
Non su tutti I nodi ci sono gli utenti.
Speaker 1:
Ok. Va bene. Ok.
Speaker 0:
No volevo fare una domanda. Ce la faccio da punto interrogativo.
Speaker 1:
No no sto pensando come cioè nel senso questa cosa qui di magari generare una rete però non considerare tutti I nodi come utenti lì poi cioè bisogna capire un attimo come implementarlo. No era solo questa la cosa però quindi vabbè mo sistemiamo Clark e poi appunto facciamo un po' di diciamo di cioè giochiamo un po' qui I dati. Ci
Speaker 0:
vediamo prima?
Speaker 1:
Sì sì sì. Va bene.
