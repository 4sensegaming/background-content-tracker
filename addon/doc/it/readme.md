# Monitoraggio contenuti in background

* Autore: Lukáš Hosnedl
* Versione minima di NVDA: 2026.3
* Ultima versione di NVDA testata: 2027.1

**Creato dall'IA, progettato e testato a fondo da esseri umani.**

## Descrizione

Monitoraggio contenuti in background monitora una finestra o un singolo controllo e ti avvisa non appena vi compare nuovo contenuto. Puoi continuare a lavorare in una finestra mentre il componente aggiuntivo ne sorveglia un'altra.

Quando le persone vedenti lavorano in una finestra, notano subito se compare un pop-up o se qualcosa cambia in una finestra accanto, e possono valutare se richiede attenzione adesso o più tardi. NVDA può annunciare avvisi e regioni live, ma di solito solo mentre la finestra interessata è in primo piano, per cui le modifiche che avvengono mentre lavori altrove ti sfuggono facilmente.

Monitoraggio contenuti in background ti offre proprio questa consapevolezza: scegli cosa monitorare e come vuoi essere avvisato, e NVDA ti avvisa quando il contenuto cambia, senza che tu debba allontanarti da ciò che stavi facendo.

Questo componente aggiuntivo è uno strumento molto potente e personalizzabile che in sostanza può trasformare finestre o controlli inaccessibili in regioni live parlanti che funzionano ovunque. Ad esempio, funziona sorprendentemente bene con:

- Terminali in esecuzione in background,
- Messaggi dinamici brevi e in rapido cambiamento in un singolo elenco, area di testo od oggetto di NVDA,
- Pagine web inaccessibili con modifiche dinamiche,
- App di messaggistica che non leggono automaticamente i nuovi messaggi in arrivo,
- Nonché app Electron come il nuovo ChatGPT, che lasciano molto a desiderare in termini di accessibilità: possono restare in silenzio a lungo e poi iniziare a riversare grandi blocchi di testo in una posizione che si sposta e che potrebbe essere difficile da trovare.

Tuttavia, con ogni probabilità il componente aggiuntivo sarà apprezzato solo da utenti esperti che sentono il bisogno di aumentare la propria velocità ed efficienza nel lavoro, come:

- Chi usa abitualmente l'IA per creare qualcosa di consistente,
- Chi esegue spesso processi automatizzati di lunga durata e deve monitorarne l'output in tempo reale,
- Chi deve passare spesso tra diverse finestre con output dinamico,
- O chi partecipa a flussi di lavoro parzialmente o completamente automatizzati, con più attività in esecuzione contemporaneamente.

Se ne hai bisogno, probabilmente lo sai già. Altri potrebbero trovarlo opprimente, sovraccarico o confuso.

## Utilizzo

Crei un elenco di obiettivi da monitorare – finestre intere o singoli controlli, come un campo editazione o l'elenco dei messaggi di una chat – e il componente aggiuntivo ti avvisa ogni volta che in uno di essi compare nuovo contenuto. Puoi monitorare più obiettivi contemporaneamente e avviare o interrompere il monitoraggio di ciascuno in modo indipendente.

### Scenari di esempio

- **Attendere un'attività lunga in un'altra app.** Affidi un compito a un assistente IA come Claude e, invece di aspettare in quella finestra, passi altrove per dedicarti ad altro. Il componente aggiuntivo monitora la finestra dell'assistente e ti avvisa non appena compare nuovo output, così sai che ha risposto senza dover tornare a controllare più e più volte.
- **Tenere d'occhio una pagina web mentre scrivi altrove.** Stai scrivendo in una chat come WhatsApp mentre accanto è aperta una pagina web. Quando quella pagina in background si aggiorna, il componente aggiuntivo ti avvisa, così te ne accorgi proprio come farebbe una persona vedente.

### Un flusso di lavoro tipico

1. Vai alla finestra o al controllo che vuoi monitorare: portaci il focus, puntaci il mouse oppure spostaci il navigatore ad oggetti o il cursore di controllo.
2. Avvia il monitoraggio, con il [comando da tastiera](#comandi-da-tastiera) corrispondente oppure scegliendolo dal [menu degli obiettivi](#il-menu-degli-obiettivi).
3. Passa a ciò su cui vuoi lavorare. Quando nell'obiettivo monitorato compare nuovo contenuto, NVDA ti avvisa nel modo che hai [configurato](#impostazioni-globali).
4. Interrompi il monitoraggio di un obiettivo quando non ti serve più, oppure cancella l'intero elenco degli obiettivi in una volta.

## Comandi da tastiera

Il componente aggiuntivo si usa tramite un unico **comando a livelli**: premi il comando da tastiera che fa da prefisso, lo rilasci e poi premi un altro tasto per scegliere cosa fare. Il prefisso da solo non fa nulla, quindi i comandi del componente aggiuntivo non interferiscono mai con NVDA o con altre app.

Il prefisso predefinito è NVDA+; (punto e virgola). Sulla tastiera italiana il punto e virgola si digita con Maiusc+virgola, quindi lì il prefisso è NVDA+Maiusc+virgola.

Quando premi il prefisso, il componente aggiuntivo apre un **overlay virtuale**. Finché l'overlay è aperto, ogni tasto che premi viene interpretato come uno dei comandi seguenti. Aprire e chiudere l'overlay non sposta mai il focus, che resta esattamente dov'era, quindi i comandi del componente aggiuntivo non disturbano mai ciò che stai facendo.

Dopo aver premuto il prefisso, premi uno dei tasti seguenti:

- `h` – **guida**: spiega brevemente cosa fa ogni tasto disponibile nell'overlay. Premilo due volte per visualizzare il testo della guida in un messaggio esplorabile.
- `f1` – **apre questa documentazione** nel browser web predefinito. Questo comando è contestuale: nell'overlay salta a questo capitolo, nel menu al capitolo [Il menu degli obiettivi](#il-menu-degli-obiettivi), quando è aperta la finestra delle impostazioni al capitolo [Impostazioni globali](#impostazioni-globali), e così via.
- `w` – avvia o interrompe il monitoraggio della **finestra** corrente.
- `f` – avvia o interrompe il monitoraggio del controllo che ha attualmente il **focus** della tastiera.
- `m` – avvia o interrompe il monitoraggio del controllo sotto il puntatore del **mouse**.
- `n` – avvia o interrompe il monitoraggio del **navigatore ad oggetti** corrente (dove si trova il cursore di controllo).
- `t` – apre il **[menu degli obiettivi](#il-menu-degli-obiettivi)**.
- Da `1` a `0` – **annuncia le informazioni su un obiettivo** in base alla sua posizione nell'elenco (vedi sotto). Premi lo stesso numero una seconda volta per impostare il focus su quell'obiettivo.
- `Spazio` o `Invio` – come i tasti numerici, ma sempre per l'obiettivo **aggiunto più di recente**: premi una volta per sentire le informazioni, due volte per impostarvi il focus.
- `Control`+un numero (da `1` a `0`) – **interrompe il monitoraggio** dell'obiettivo in quello slot.
- `Alt`+un numero (da `1` a `0`) – **apre il [menu degli obiettivi](#il-menu-degli-obiettivi)** direttamente per l'obiettivo in quello slot.
- `Backspace` – **interrompe il monitoraggio dell'obiettivo aggiunto più di recente**.
- `Canc` – **interrompe il monitoraggio di tutti gli obiettivi** (cancella l'intero elenco in una volta).
- `p` – **sospende o riprende** tutto il monitoraggio (attiva o disattiva l'opzione [*Attiva il monitoraggio*](#attiva-il-monitoraggio-casella-di-controllo-attivata-per-impostazione-predefinita)).
- `s` – apre le **[impostazioni](#impostazioni-globali)** del componente aggiuntivo (lo stesso pannello di menu NVDA → Preferenze → Impostazioni → Monitoraggio contenuti in background).
- `i` – apre la finestra **Gesti di immissione** di NVDA direttamente sulla categoria Monitoraggio contenuti in background, così puoi riassegnare il prefisso senza doverlo cercare.
- `Escape` – **chiude l'overlay** senza fare nient'altro.

I comandi per finestra, focus, mouse e navigatore ad oggetti funzionano come interruttori: premine uno una volta per aggiungere quell'obiettivo all'elenco, e premilo di nuovo per rimuoverlo, purché sia ancora la finestra corrente, abbia ancora il focus e così via. Puoi monitorare un numero qualsiasi di obiettivi contemporaneamente.

Questi quattro comandi accettano anche `Maiusc` e `Control`, che indicano come deve essere monitorato l'obiettivo che stai aggiungendo: `Maiusc` ricorda proprio quell'obiettivo, `Control` lo legge anche mentre la sua app è in primo piano, e tenendoli premuti entrambi si ottengono entrambe le cose. Si tratta di [impostazioni del singolo obiettivo](#impostazioni-obiettivo), applicate a quello specifico obiettivo nel momento in cui viene aggiunto invece di essere ereditate dalle [impostazioni globali](#impostazioni-globali) o configurate manualmente in seguito nel [menu degli obiettivi](#il-menu-degli-obiettivi), e non modificano l'impostazione globale. Una pressione che *interrompe* il monitoraggio dell'obiettivo invece di aggiungerlo ignora semplicemente i modificatori. I modificatori sono utili solo se hai disattivato a livello globale le opzioni [**Ricorda gli obiettivi**](#ricorda-gli-obiettivi-casella-di-controllo-disattivata-per-impostazione-predefinita) o [**Monitora anche gli obiettivi in primo piano**](#monitora-anche-gli-obiettivi-in-primo-piano-casella-di-controllo-disattivata-per-impostazione-predefinita), ma ti serve questo comportamento proprio per questo obiettivo.

I tasti numerici si riferiscono agli **slot** del tuo elenco di obiettivi, non a obiettivi fissi. Per impostazione predefinita, `1` è l'obiettivo aggiunto più di recente, `2` quello aggiunto prima e così via fino a `0`, il decimo slot. L'impostazione [**Ordinamento degli obiettivi negli slot**](#ordinamento-degli-obiettivi) può disporre gli slot in un ordine diverso, ad esempio prima l'obiettivo più vecchio, prima quello modificato più di recente o in ordine alfabetico. Se un obiettivo viene rimosso, perché ne hai interrotto il monitoraggio o perché non esiste più, gli obiettivi successivi avanzano per colmare il vuoto, quindi `2` annuncia sempre l'obiettivo che in quel momento si trova al secondo posto nell'elenco.

Quando un obiettivo è presente, per impostazione predefinita il componente aggiuntivo ne annuncia il tipo (ruolo), il nome e il contenuto modificato, ad esempio *Finestra: Claude, Editing readme.md* oppure *Elenco: Elenco messaggi, Hai detto: Va bene*. Il livello di dettaglio di questi annunci può essere [configurato nelle impostazioni del componente aggiuntivo](#includi-nellannuncio-delle-modifiche-gruppo).

Puoi cambiare il prefisso dalla finestra Gesti di immissione di NVDA (menu NVDA → Preferenze → Gesti e tasti di immissione), dove il comando del componente aggiuntivo compare nella categoria **Monitoraggio contenuti in background**. I tasti successivi fanno parte del comando a livelli stesso.

## Il menu degli obiettivi

Il **menu degli obiettivi** (il prefisso seguito da `t`) elenca tutti gli obiettivi monitorati come voci di menu ordinate, così non devi ricordare la posizione attuale dell'obiettivo nell'elenco né nessuno degli altri tasti.

Ogni voce indica esattamente su cosa agisce, ad esempio *Finestra: Claude, 3 minuti fa, 3 tasks running*. Un obiettivo che al momento non esiste (uno ricordato la cui finestra non è ancora stata riaperta) mostra *non trovato* al posto del tempo e del contenuto, e resta nel menu, perché puoi comunque interromperne il monitoraggio, modificarne le impostazioni oppure lasciarlo lì e aspettare che ritorni. L'ordine in cui gli obiettivi vengono visualizzati rispetta l'impostazione [**Ordinamento degli obiettivi nel menu**](#ordinamento-degli-obiettivi).

Ogni obiettivo è un sottomenu. Quando lo espandi, puoi:

- Interromperne il monitoraggio con *Interrompi monitoraggio*,
- Impostarvi il focus con *Imposta focus* (a meno che non lo abbia già),
- Modificarne le [*Impostazioni obiettivo*](#impostazioni-obiettivo),
- Oppure sfogliarne la [**cronologia delle modifiche recenti**](#cronologia-delle-modifiche-recenti).

Tutto ciò che stai già monitorando compare per primo nel menu, così puoi spostarti rapidamente sull'obiettivo che ti interessa o interromperne il monitoraggio. Sotto si trovano gli obiettivi di cui puoi avviare il monitoraggio dalla tua posizione attuale (finestra, focus, puntatore del mouse o navigatore ad oggetti). La voce per interrompere il monitoraggio di tutti gli obiettivi attuali si trova alla fine del menu.

### Impostazioni obiettivo

Ogni voce di *Impostazioni obiettivo* è una casella di controllo, e ciò che mostra è ciò che l'obiettivo fa realmente: il suo valore personale dove gliene hai assegnato uno, e l'[impostazione globale](#impostazioni-globali) in tutti gli altri casi. Selezionarne o deselezionarne una assegna a quell'obiettivo un valore proprio per quella sola impostazione, con effetto immediato; tutte le altre impostazioni continuano a seguire quella globale.

- *Interrompi il parlato precedente all'annuncio di una nuova modifica* viene mostrata per tutti gli obiettivi, purché l'[opzione globale *Annuncia*](#annuncia-casella-di-controllo-attivata-per-impostazione-predefinita) sia attivata.
- Le opzioni *Ignora le barre di avanzamento*, *Ignora contatori, progressioni e timer*, *Considera un titolo cambiato come obiettivo scomparso* e *Ignora i controlli generici noti* vengono mostrate solo per gli obiettivi che sono finestre.
- *Monitora questo obiettivo anche in primo piano* viene mostrata per tutti gli obiettivi.
- *Ignora il controllo con il focus* viene mostrata se l'obiettivo è una finestra ed è anche [impostato per essere monitorato anche in primo piano](#monitora-anche-gli-obiettivi-in-primo-piano-casella-di-controllo-disattivata-per-impostazione-predefinita).
- *Ricorda questo obiettivo* viene mostrata per tutti gli obiettivi.
- *Dimentica questo obiettivo quando scompare* viene mostrata solo per gli obiettivi ricordati.

La modifica di un'[impostazione globale](#impostazioni-globali) ha effetto anche sugli obiettivi esistenti, a meno che quell'impostazione non sia stata sovrascritta localmente. Il pannello delle impostazioni modifica solo i valori globali: nulla di ciò che fai lì toglie a un obiettivo il suo valore personale. Tutti i valori locali vengono cancellati solo interrompendo il monitoraggio dell'obiettivo e aggiungendolo di nuovo, oppure dimenticando un obiettivo ricordato.

### Cronologia delle modifiche recenti

Questo sottomenu elenca tante modifiche recenti avvenute nell'obiettivo quante ne hai impostate in [*Conserva la cronologia delle modifiche recenti per obiettivo*](#conserva-la-cronologia-delle-modifiche-recenti-per-obiettivo-campo-editazione-50-per-impostazione-predefinita), nell'ordine stabilito dall'[*ordinamento della cronologia delle modifiche*](#ordinamento-degli-obiettivi) e con il [livello di dettaglio](#includi-nelle-descrizioni-del-menu-gruppo) configurato. Se *Conserva la cronologia delle modifiche recenti per obiettivo* è impostata su 0, il sottomenu non viene mostrato affatto. Le modifiche più vecchie oltre quel numero vengono rimosse. Tieni presente che questa impostazione è solo globale. Scegliendo una qualsiasi voce di questo sottomenu, quella modifica si apre in un messaggio esplorabile.

La cronologia scompare quando interrompi il monitoraggio di un obiettivo, quando un obiettivo viene automaticamente [dimenticato dopo essere scomparso](#dimentica-gli-obiettivi-ricordati-quando-scompaiono-casella-di-controllo-disattivata-per-impostazione-predefinita) o alla fine della sessione, e non viene salvata da nessuna parte. Quando il [monitoraggio è sospeso](#attiva-il-monitoraggio-casella-di-controllo-attivata-per-impostazione-predefinita), anche la cronologia non viene aggiornata.

## Impostazioni globali

Le opzioni del componente aggiuntivo si trovano nella categoria **Monitoraggio contenuti in background** della finestra Impostazioni di NVDA (menu NVDA → Preferenze → Impostazioni). Il componente aggiuntivo supporta più profili di configurazione.

Le opzioni correlate sono raggruppate. Tutte le opzioni disponibili sono descritte di seguito, nell'ordine in cui compaiono nel pannello. Le opzioni di primo livello e i gruppi interi sono intestazioni di livello 3; le singole opzioni all'interno dei gruppi sono intestazioni di livello 4.

### **Attiva il monitoraggio** (casella di controllo, attivata per impostazione predefinita)

Quando è disattivata, il componente aggiuntivo smette di avvisarti ma conserva l'intero elenco degli obiettivi e tutte le tue impostazioni, così puoi silenziarlo (ad esempio durante una riunione) e in seguito riattivarlo esattamente com'era. È lo stesso interruttore azionato dal [comando da tastiera per sospendere e riprendere](#comandi-da-tastiera).

È l'unica opzione che non viene mai salvata: all'avvio di NVDA il monitoraggio è sempre attivato.

### **Intervallo di monitoraggio** (campo editazione, 1 per impostazione predefinita)

Accetta solo numeri interi. Imposta ogni quanti secondi il componente aggiuntivo deve controllare tutti gli obiettivi esistenti alla ricerca di modifiche. 0 significa non annunciare mai automaticamente le modifiche agli obiettivi, ma solo mostrarle nel [menu degli obiettivi](#il-menu-degli-obiettivi).

### **Modifiche da annunciare in una volta (solo obiettivi in background)** (campo editazione, 5 per impostazione predefinita)

Accetta solo numeri interi. Imposta quante modifiche consecutive dello stesso obiettivo il componente aggiuntivo deve annunciare di seguito prima che tu debba riportare il focus sull'obiettivo e poi spostarti di nuovo altrove perché vengano annunciate ulteriori modifiche. 0 significa annunciare ogni modifica.

Questa opzione non riguarda mai gli obiettivi in primo piano. Se il [monitoraggio è attivato anche per gli obiettivi in primo piano](#monitora-anche-gli-obiettivi-in-primo-piano-casella-di-controllo-disattivata-per-impostazione-predefinita), per questi vengono sempre annunciate tutte le modifiche.

### **Conserva la cronologia delle modifiche recenti per obiettivo** (campo editazione, 50 per impostazione predefinita)

Accetta solo numeri interi. Imposta quante modifiche recenti conservare nella [cronologia di ciascun obiettivo](#cronologia-delle-modifiche-recenti). Le modifiche più vecchie vengono scartate. 0 significa nessuna cronologia.

Per gli obiettivi ricordati che sono scomparsi, anche la cronologia viene ricordata e resta disponibile finché l'obiettivo non viene rimosso o fino alla fine della sessione.

### **Timeout dell'overlay** (campo editazione, 10 per impostazione predefinita)

Accetta solo numeri interi. Imposta quanti secondi senza pressione di tasti devono trascorrere prima che l'overlay si chiuda da solo. 0 significa che l'overlay non si chiude mai da solo: resta aperto finché non lo chiudi con Escape o con un comando che sposta il focus altrove, come l'apertura del [menu degli obiettivi](#il-menu-degli-obiettivi).

### **Monitora anche gli obiettivi in primo piano** (casella di controllo, disattivata per impostazione predefinita)

Normalmente un obiettivo viene letto solo mentre lavori altrove, quindi quando la sua app passa in primo piano il componente aggiuntivo lo lascia stare. Se attivata, il nuovo contenuto di un obiettivo viene annunciato anche mentre stai lavorando proprio con quella finestra o quel singolo controllo.

Tieni presente che se l'app dell'obiettivo comunica direttamente con gli screen reader (tramite regioni live ARIA o altri eventi di accessibilità), gli stessi annunci potrebbero a volte essere segnalati due volte mentre lavori nella sua finestra: una volta dall'app stessa e una dal componente aggiuntivo. In tal caso, per sentire solo gli annunci dell'app, puoi deselezionare *Monitora questo obiettivo anche in primo piano* nelle [Impostazioni obiettivo](#impostazioni-obiettivo) di quell'obiettivo, sospendere temporaneamente il monitoraggio oppure rimuovere l'obiettivo e aggiungerlo di nuovo più tardi. Per sentire solo gli annunci del componente aggiuntivo, disattiva in NVDA l'opzione «Leggi i cambiamenti dei contenuti dinamici» (NVDA+5 per impostazione predefinita).

### Ordinamento degli obiettivi

Ci sono tre serie di pulsanti radio, uno dopo l'altro: *Ordinamento degli obiettivi negli slot*, *Ordinamento degli obiettivi nel menu* e *Ordinamento della cronologia delle modifiche*. Tutti offrono le stesse opzioni elencate di seguito (con alcune eccezioni) e possono essere impostati allo stesso modo o indipendentemente l'uno dall'altro. Determinano rispettivamente in quale ordine gli obiettivi vengono assegnati ai dieci slot numerati disponibili (vedi [Comandi da tastiera](#comandi-da-tastiera)), mostrati nel [menu degli obiettivi](#il-menu-degli-obiettivi) od ordinati nella [cronologia delle modifiche recenti di ciascun obiettivo](#cronologia-delle-modifiche-recenti).

- *Prima l'obiettivo / la modifica più recente* (predefinito per tutti i tipi di ordinamento)
- *Prima l'obiettivo più vecchio / la modifica più vecchia*
- *Prima l'obiettivo modificato più di recente* (non disponibile per l'ordinamento della cronologia)
- *Prima l'obiettivo modificato meno di recente* (non disponibile per l'ordinamento della cronologia)
- *In ordine alfabetico, dalla A alla Z*
- *In ordine alfabetico, dalla Z alla A*

### **Ricorda gli obiettivi** (casella di controllo, disattivata per impostazione predefinita)

Se attivata, il tuo elenco di obiettivi viene conservato tra un riavvio di NVDA e l'altro, e il componente aggiuntivo si ricollega a un obiettivo ogni volta che questo ricompare. Ad esempio, monitora la finestra dell'assistente ogni volta che quella finestra si apre, senza che tu debba configurarlo di nuovo. Se disattivata, l'elenco degli obiettivi parte vuoto a ogni sessione e vengono salvate solo le tue impostazioni.

### **Dimentica gli obiettivi ricordati quando scompaiono** (casella di controllo, disattivata per impostazione predefinita)

Stabilisce se un obiettivo ricordato debba essere dimenticato quando non esiste più, perché hai chiuso la sua finestra o perché è scomparso da solo. Se attivata, dovrai riavviare manualmente il monitoraggio dello stesso obiettivo ogni volta che scompare. Gli obiettivi di cui interrompi manualmente il monitoraggio vengono sempre dimenticati, indipendentemente da come è impostata questa opzione.

### **Comportamento del monitoraggio delle finestre** (gruppo)

Le opzioni di questo gruppo affinano il modo in cui il componente aggiuntivo deve annunciare le modifiche negli obiettivi che sono finestre intere.

#### **Ignora le barre di avanzamento** (casella di controllo, attivata per impostazione predefinita)

Se attivata, questa opzione sopprime gli annunci delle barre di avanzamento che cambiano nella finestra. NVDA stesso può annunciare le barre di avanzamento native a voce e/o con dei bip, anche in background, quindi potresti non volere che questo componente aggiuntivo ti sommerga segnalando una seconda volta una barra di avanzamento in continuo cambiamento in una determinata app.

#### **Ignora contatori, progressioni e timer** (casella di controllo, attivata per impostazione predefinita)

Se attivata, il componente aggiuntivo individua i controlli che cambiano solo nei valori numerici: un timer o un conto alla rovescia che scatta ogni secondo, un contatore di passaggi o di elementi, una percentuale, come l'app Claude che conta per quanto tempo il modello ha riflettuto. Questi controlli spesso sono più fastidiosi che utili, perché da soli non forniscono informazioni utili e, soprattutto, non comunicano alcuna modifica reale: indicano solo che l'attività è ancora in corso. Non appena un controllo del genere viene individuato, si zittisce e resta in silenzio per tutto il tempo in cui l'obiettivo è monitorato.

#### **Considera un titolo cambiato come obiettivo scomparso** (casella di controllo, disattivata per impostazione predefinita)

Se attivata e il titolo di una finestra monitorata cambia, il componente aggiuntivo la considera una finestra diversa e si comporta quindi come se l'obiettivo originale fosse scomparso, anche se fisicamente nel sistema la finestra è sempre la stessa.

#### **Ignora i controlli generici noti** (casella di controllo, attivata per impostazione predefinita)

Se attivata, questa opzione sopprime gli annunci dei controlli generici, come il pulsante «Riduci a icona» di una finestra che diventa «Ingrandisci» e viceversa. Sono inclusi:

- La barra dei menu dell'applicazione (di solito raggiungibile con il tasto Alt)
- I pulsanti «Riduci a icona», «Ripristina», «Ingrandisci» e «Chiudi»
- I pulsanti «OK», «Annulla», «Interrompi», «Riprova», «Continua», «Avanti», «Precedente», «Indietro», «Fine» e «Non ora»
- E i pulsanti «Sì» e «No».

#### **Ignora il controllo con il focus durante il monitoraggio della finestra in primo piano** (casella di controllo, attivata per impostazione predefinita)

Questa opzione è disponibile solo quando [Monitora anche gli obiettivi in primo piano](#monitora-anche-gli-obiettivi-in-primo-piano-casella-di-controllo-disattivata-per-impostazione-predefinita) è attivata, poiché fa differenza solo per la finestra che viene letta mentre ci stai lavorando. Le finestre in background e gli obiettivi che sono singoli controlli non ne sono comunque interessati.

Se attivata, il controllo che ha attualmente il focus non viene mai annunciato come modifica, quindi, ad esempio, i caratteri che digiti in un campo editazione non vengono letti come nuovo contenuto.

### **Quando l'obiettivo cambia** (gruppo)

Cosa succede quando in un obiettivo compare nuovo contenuto.

#### **Bip** (casella di controllo, attivata per impostazione predefinita)

Riproduce un tono quando l'obiettivo è cambiato.

#### **Annuncia** (casella di controllo, attivata per impostazione predefinita)

Annuncia cosa è cambiato e dove, ad esempio «Finestra: Claude» o «Elenco: Elenco messaggi». Il livello di dettaglio dell'annuncio può essere ulteriormente personalizzato più sotto.

#### **Interrompi il parlato precedente all'annuncio di una nuova modifica** (casella di controllo, disattivata per impostazione predefinita)

Questa opzione è disponibile solo quando la casella [**Annuncia**](#annuncia-casella-di-controllo-attivata-per-impostazione-predefinita) qui sopra è attivata. Se attivata, l'annuncio di una modifica interrompe qualsiasi cosa NVDA stia dicendo in quel momento e viene pronunciato subito. Se disattivata, attende che NVDA abbia finito di parlare.

#### **Ripeti il nome dell'obiettivo per modifiche consecutive nello stesso obiettivo** (casella di controllo, attivata per impostazione predefinita)

Questa opzione è disponibile solo quando sono attivati [gli annunci vocali in quanto tali](#annuncia-casella-di-controllo-attivata-per-impostazione-predefinita). Se attivata, il nome dell'obiettivo viene incluso in ogni singolo annuncio di modifica, anche se nello stesso obiettivo si sono verificate più modifiche di seguito. Se disattivata, il nome dell'obiettivo viene annunciato solo per la prima delle modifiche consecutive nello stesso obiettivo.

### **Parametri del bip** (gruppo)

Le opzioni di questo gruppo sono disponibili solo quando la casella [**Bip**](#bip-casella-di-controllo-attivata-per-impostazione-predefinita) qui sopra è attivata.

#### **Durata** (campo editazione, 50 per impostazione predefinita)

Accetta solo numeri interi. Imposta quanto deve durare il bip, in millisecondi.

#### **Altezza** (campo editazione, 440 per impostazione predefinita)

Accetta solo numeri interi. Imposta a quale frequenza deve essere riprodotto il bip, in hertz.

#### **Prova** (pulsante)

Riproduce un bip di prova con i parametri attualmente impostati, così puoi verificare se suona come desideri.

### **Includi nell'annuncio delle modifiche** (gruppo)

Le opzioni di questo gruppo sono disponibili solo quando la casella [**Annuncia**](#annuncia-casella-di-controllo-attivata-per-impostazione-predefinita) qui sopra è attivata. Determinano esattamente di cosa è composto l'annuncio di una modifica.

#### **Tipo di obiettivo** (casella di controllo, attivata per impostazione predefinita)

Se annunciare il tipo (ruolo) dell'obiettivo (ad esempio **finestra**, **elenco** o **campo editazione**).

#### **Contenuto modificato** (casella di controllo, attivata per impostazione predefinita)

Se annunciare il nuovo contenuto dell'obiettivo dopo la modifica più recente.

### **Includi nelle descrizioni del menu** (gruppo)

Le opzioni di questo gruppo specificano come vengono etichettate le voci del [menu degli obiettivi](#il-menu-degli-obiettivi). Influiscono anche sul modo in cui vengono scritte le voci della [cronologia delle modifiche](#cronologia-delle-modifiche-recenti) dei singoli obiettivi.

#### **Tipo di obiettivo** (casella di controllo, attivata per impostazione predefinita)

Se mostrare il tipo (ruolo) dell'obiettivo (ad esempio **finestra**, **elenco** o **campo editazione**) nella descrizione della voce di menu corrispondente.

#### **Tempo dall'ultima modifica** (casella di controllo, attivata per impostazione predefinita)

Se mostrare il tempo trascorso dall'ultima modifica avvenuta nell'obiettivo (ad esempio 3 minuti fa) nella descrizione della voce di menu corrispondente.

#### **Contenuto modificato** (casella di controllo, attivata per impostazione predefinita)

Se mostrare il nuovo contenuto dell'obiettivo dopo la modifica più recente nella descrizione della voce di menu corrispondente.

## Limitazioni note

- **Le schede del browser in background non vengono mai monitorate.** Un browser web mantiene leggibile solo la scheda che stai guardando. Per tenere d'occhio una pagina mentre lavori altrove, aprila in una finestra separata invece di lasciarla in una scheda in background. Nemmeno gli utenti vedenti possono vedere una scheda in background.
- **Alcune app rivelano pochissimo quando non sono in primo piano.** Quanto un'app comunica a uno screen reader sui contenuti senza focus dipende esclusivamente dall'app stessa. Le app UIA moderne (Terminale, Impostazioni, Calcolatrice, Foto e la maggior parte delle app del Microsoft Store) e le app visualizzate come viste web (le app desktop di Claude e ChatGPT, il nuovo Outlook, Visual Studio Code, Discord, Slack, Signal, WhatsApp per Windows, Spotify, oltre ai siti web veri e propri) differiscono notevolmente sotto questo aspetto. Se un'app non espone il nuovo contenuto come testo accessibile, il componente aggiuntivo non può segnalarlo.
- **Conta solo ciò che una finestra mostra in quel momento.** Gli elenchi lunghi (cronologia delle chat, elenchi di file, risultati di ricerca) di solito esistono solo come le poche righe visualizzate in quel momento. Il componente aggiuntivo non può vedere le voci che sono scorse fuori dalla parte visibile, proprio come non possono vederle gli utenti vedenti, e una finestra ridotta a icona può smettere del tutto di mostrare il proprio contenuto finché non la ripristini, a seconda di come è programmata l'app in questione.

Se hai bisogno di essere informato sugli aggiornamenti frequenti di un'app che usi in background, di solito è più affidabile e semplice configurare l'app stessa perché ti invii notifiche, se è in grado di farlo. Inoltre, se riduci l'app nell'area di notifica, non mostra più una finestra visibile, quindi il componente aggiuntivo non può più monitorarla. Tuttavia, se l'icona nell'area di notifica espone informazioni utili sotto forma di testo, puoi monitorare l'icona stessa.

## Contribuire

Se vuoi contribuire allo sviluppo del componente aggiuntivo fornendo traduzioni, segnalando problemi o aprendo una pull request, e sai come farlo, puoi [farlo nel suo repository GitHub](https://github.com/4sensegaming/background-content-tracker). Ogni contributo è benvenuto e apprezzato.

## Registro delle modifiche

### Versione 1.0, 12/10/2026
* Versione iniziale
