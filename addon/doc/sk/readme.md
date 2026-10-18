# Sledovanie obsahu na pozadí

[Čeština](../cs/readme.md) | [Deutsch](../de/readme.md) | [English](../../../readme.md) | [Italiano](../it/readme.md) | **Slovenčina**

* Autor: Lukáš Hosnedl
* Minimálna verzia NVDA: 2026.3
* Posledná testovaná verzia NVDA: 2027.1

**Vytvorené umelou inteligenciou, navrhnuté a dôkladne otestované ľuďmi.**

## Popis

Doplnok Sledovanie obsahu na pozadí sleduje okno alebo jednotlivý prvok a dá vám vedieť, hneď ako sa v ňom objaví nový obsah. Môžete tak ďalej pracovať v jednom okne, zatiaľ čo doplnok stráži iné.

Keď vidiaci ľudia pracujú v jednom okne, okamžite zaznamenajú, že vo vedľajšom okne niečo vyskočilo alebo sa zmenilo, a dokážu odhadnúť, či si to vyžaduje pozornosť hneď, alebo až o chvíľu. NVDA vie oznamovať upozornenia a živé regióny, ale zvyčajne len vo chvíli, keď je dané okno v popredí, takže zmeny, ku ktorým došlo, zatiaľ čo ste pracovali inde, vám môžu ľahko uniknúť.

Sledovanie obsahu na pozadí vám dáva presne tento prehľad: Vyberiete si, čo sa má sledovať a ako chcete byť upozornení, a NVDA vás na zmenu obsahu upozorní bez toho, aby ste museli opustiť to, čo práve robíte.

Tento doplnok je veľmi silný a prispôsobiteľný nástroj, ktorý dokáže z neprístupných okien alebo prvkov v podstate urobiť hovoriace živé regióny, ktoré fungujú všade. Prekvapivo dobre si rozumie napríklad s:

- Terminálmi,
- Dynamickými správami vnútri jedného zoznamu, textovej oblasti alebo iného kontajnera,
- Webovými stránkami, ktoré sa priebežne aktualizujú,
- Komunikačnými aplikáciami, ktoré samy nečítajú nové prichádzajúce správy,
- A tiež s aplikáciami postavenými na Electrone, ako je nový ChatGPT, ktoré dlho mlčia a potom začnú chrliť veľké kusy textu, zakaždým na inom mieste v okne.

Doplnok však najskôr ocenia len pokročilí používatelia, ktorí potrebujú zrýchliť a zefektívniť svoju prácu, napríklad:

- Tí, ktorí bežne používajú AI na tvorbu niečoho rozsiahlejšieho,
- Tí, ktorí často spúšťajú dlhotrvajúce automatizované úlohy a potrebujú v reálnom čase sledovať ich výstup,
- Tí, ktorí musia často prepínať medzi niekoľkými rôznymi oknami s dynamickým výstupom,
- Alebo tí, ktorí sa podieľajú na čiastočne či plne automatizovaných procesoch, v ktorých beží niekoľko úloh naraz.

Ak ho potrebujete, najskôr to už viete. Ostatným sa môže zdať zahlcujúci, preplnený alebo mätúci.

## Použitie

Vytvoríte si zoznam cieľov na sledovanie – celých okien alebo jednotlivých prvkov, napríklad editačných polí či zoznamov správ v chatoch – a doplnok vás upozorní zakaždým, keď sa v niektorom z nich objaví nový obsah. Môžete sledovať viac cieľov naraz a každý z nich začať alebo prestať sledovať nezávisle od ostatných.

### Príklady použitia

- **Čakanie na dlhú úlohu v inej aplikácii.** Zadáte úlohu AI asistentovi, napríklad Claudovi, a namiesto toho, aby ste čakali v jeho okne, prepnete sa inam a venujete sa niečomu inému. Doplnok sleduje okno asistenta a dá vám vedieť, hneď ako sa objaví nový výstup, takže spoznáte, že odpovedal, bez toho, aby ste sa museli znova a znova vracať a kontrolovať to.
- **Sledovanie webovej stránky, zatiaľ čo píšete inde.** Píšete v chate, napríklad vo WhatsAppe, a vedľa máte pritom otvorenú webovú stránku. Keď sa táto stránka na pozadí aktualizuje, doplnok vám to oznámi – takže si to všimnete rovnako ako vidiaci používateľ.

### Typický postup

1. Prejdite na okno alebo prvok, ktorý chcete sledovať: Presuňte naň fokus, nabehnite naň myšou alebo naň presuňte navigačný objekt či prezerací kurzor.
2. Začnite ho sledovať – buď príslušnou [klávesovou skratkou](#klávesové-skratky), alebo výberom z [ponuky cieľov](#ponuka-cieľov).
3. Prepnite sa na to, čomu sa chcete venovať. Keď sa v sledovanom cieli objaví nový obsah, NVDA vás upozorní tak, ako ste si [nastavili](#globálne-nastavenia).
4. Keď daný cieľ už nebudete potrebovať, prestaňte ho sledovať alebo vymažte celý zoznam cieľov naraz.

## Klávesové skratky

Doplnok sa ovláda jediným **vrstveným príkazom**: Stlačíte klávesovú skratku, uvoľníte ju a potom stlačíte ešte jednu klávesu, ktorou zvolíte požadovanú akciu. Po stlačení samotnej hlavnej klávesovej skratky sa nič nestane, takže príkazy doplnku nikdy nekolidujú s NVDA ani inými aplikáciami.

Predvolená klávesová skratka je NVDA+; (bodkočiarka – na slovenskej klávesnici klávesa naľavo od číslice 1).

Po stlačení hlavnej klávesovej skratky doplnok otvorí **virtuálne prekrytie**. Kým je prekrytie otvorené, považuje sa každé stlačenie klávesy za jeden z nižšie uvedených príkazov. Otvorenie ani zatvorenie prekrytia nepresúva fokus, takže príkazy doplnku nikdy nenarušia to, čo práve robíte.

Po stlačení hlavnej klávesovej skratky stlačte jednu z nasledujúcich kláves:

- `H` – **nápoveda**: Stručne vysvetlí, na čo slúži každá klávesa dostupná v prekrytí. Dvojitým stlačením zobrazíte text nápovedy v dialógovom okne na pohodlnejšie čítanie.
- `F1` – **otvorí túto dokumentáciu** v predvolenom webovom prehliadači. Tento príkaz je kontextový: V prekrytí prejde na túto kapitolu, v ponuke na kapitolu [Ponuka cieľov](#ponuka-cieľov), pri otvorenom dialógu nastavení na kapitolu [Globálne nastavenia](#globálne-nastavenia) a tak ďalej.
- `W` – začne alebo prestane sledovať aktuálne **okno**.
- `F` – začne alebo prestane sledovať prvok, ktorý má práve **fokus** klávesnice.
- `M` – začne alebo prestane sledovať prvok pod ukazovateľom **myši**.
- `N` – začne alebo prestane sledovať aktuálny **navigačný objekt** (tam, kde je prezerací kurzor).
- `T` – otvorí **[ponuku cieľov](#ponuka-cieľov)**.
- `1` až `0` – **oznámi informácie o príslušnom cieli** podľa jeho poradia v zozname (pozri nižšie). Dvojitým stlačením toho istého čísla sa na daný cieľ presunie fokus, trojitým sa otvorí priamo jeho [história nedávnych zmien](#história-nedávnych-zmien).
- `Control`+číslo (`1` až `0`) – **prestane sledovať** cieľ v danom slote.
- `Alt`+číslo (`1` až `0`) – **[otvorí ponuku](#ponuka-cieľov)** priamo pre cieľ v danom slote.
- `Medzerník` alebo `enter` – to isté ako číselné skratky, ale vždy pre **naposledy pridaný** cieľ: Prvým stlačením si o ňom necháte oznámiť informácie, druhým sa naň presunie fokus, tretím sa otvorí jeho história.
- `Backspace` – **prestane sledovať naposledy pridaný** cieľ.
- `Delete` – **prestane sledovať všetky ciele** (vymaže celý zoznam naraz).
- `P` – **pozastaví alebo obnoví** všetko sledovanie (prepína prepínač [*Povoliť sledovanie*](#povoliť-sledovanie-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté)).
- `S` – otvorí **[nastavenia](#globálne-nastavenia)** doplnku (rovnaká karta ako ponuka NVDA → Možnosti → Nastavenia → Sledovanie obsahu na pozadí).
- `I` – otvorí dialóg **Klávesové skratky** NVDA priamo na kategórii Sledovanie obsahu na pozadí, takže môžete hlavnú klávesovú skratku zmeniť bez toho, aby ste ju museli hľadať.
- `Escape` – **zatvorí prekrytie** a nevykoná nič iné.

Príkazy pre okno, fokus, myš a navigačný objekt fungujú ako prepínače: Prvým stlačením daný cieľ pridáte do zoznamu, opätovným stlačením ho odoberiete, ak je to stále aktuálne okno, prvok, ktorý má fokus, a podobne. Sledovať môžete ľubovoľný počet cieľov súčasne.

Tieto štyri príkazy zohľadňujú aj klávesy `shift` a `control`, ktoré určujú, ako sa má cieľ sledovať: `Shift` si daný cieľ zapamätá, `control` ho nechá čítať aj vo chvíli, keď je jeho aplikácia v popredí, a s oboma klávesami naraz platí oboje. Ide o [nastavenia pre jednotlivý cieľ](#nastavenia-cieľa) zadané priamo tomuto cieľu pri jeho pridaní namiesto toho, aby sa prevzali z [globálnych nastavení](#globálne-nastavenia) alebo dodatočne ručne menili v [ponuke cieľov](#ponuka-cieľov). Globálne nastavenie sa pritom nezmení. Príkaz, ktorý sledovanie cieľa *ukončuje*, namiesto toho, aby ho pridal, tieto modifikačné klávesy jednoducho ignoruje. Modifikačné klávesy sa hodia len vtedy, keď máte možnosť [**Pamätať si ciele**](#pamätať-si-ciele-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté) alebo [**Sledovať aj ciele v popredí**](#sledovať-aj-ciele-v-popredí-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté) globálne vypnutú, ale pre tento konkrétny cieľ dané správanie potrebujete.

Číselné skratky odkazujú na **sloty** v zozname cieľov, nie na pevne dané pozície. V predvolenom nastavení je `1` naposledy pridaný cieľ, `2` ten predposledný a tak ďalej až po `0` – desiaty slot. [Nastavenie **Zoradenie cieľov v slotoch**](#zoradenie-cieľov) môže sloty zoradiť inak, napríklad od najstaršieho cieľa, od naposledy zmeneného cieľa alebo abecedne. Keď niektorý cieľ zmizne – pretože ste ho prestali sledovať alebo prestal existovať –, ciele za ním sa posunú a medzeru vyplnia, takže číslo `2` vždy oznámi ten cieľ, ktorý je práve teraz v zozname ako druhý.

Ak cieľ existuje, doplnok v predvolenom nastavení oznámi jeho typ (rolu), názov a zmenený obsah cieľa, napríklad *Okno: Claude, Editing readme.md* alebo *Zoznam: Zoznam správ, Povedali ste: Tak dobre*. Úroveň podrobnosti týchto oznámení možno [upraviť v nastaveniach doplnku](#do-oznámenia-o-zmene-zahrnúť-zoskupenie).

Hlavnú klávesovú skratku môžete zmeniť v dialógu Klávesové skratky (ponuka NVDA → Možnosti → Klávesové skratky), kde sa príkaz doplnku nachádza v kategórii **Sledovanie obsahu na pozadí**. Nasledujúce klávesy sú súčasťou samotného príkazového prekrytia.

## Ponuka cieľov

**Ponuka cieľov** (hlavná klávesová skratka nasledovaná klávesou `t`) zobrazuje všetky sledované ciele ako zoradené položky ponuky, takže si nemusíte pamätať aktuálne poradie cieľa v zozname ani žiadnu z ostatných kláves.

Každá položka presne pomenúva, čoho sa týka, napríklad *Okno: Claude, pred 3 minútami, 3 tasks running*. Cieľ, ktorý práve neexistuje – zapamätaný cieľ, ktorého okno nie je otvorené –, uvádza *Nenájdené* a v ponuke zostáva, pretože ho stále môžete prestať sledovať, zmeniť jeho nastavenia alebo počkať, kým sa objaví. Poradie, v ktorom sú ciele zobrazené, sa riadi [nastavením **Zoradenie cieľov v ponuke**](#zoradenie-cieľov).

Každý cieľ je podponukou. Keď ju rozbalíte, môžete:

- Cieľ *Prestať sledovať*,
- *Presunúť fokus* naň (ak ho už nemá),
- Zmeniť jeho [*Nastavenia cieľa*](#nastavenia-cieľa),
- Alebo prechádzať jeho [históriu **nedávnych zmien**](#história-nedávnych-zmien) (nezobrazí sa, ak sa zatiaľ v cieli nič nezmenilo alebo ak je [veľkosť histórie](#koľko-zmien-uchovávať-pre-každý-cieľ-editačné-pole-v-predvolenom-nastavení-50) nastavená na 0).

Všetko, čo už sledujete, sa v ponuke zobrazí ako prvé, takže sa na daný cieľ môžete rýchlo presunúť alebo ho prestať sledovať. Ďalej sa zobrazia ciele, ktoré môžete začať sledovať zo svojej aktuálnej pozície (okno, fokus, ukazovateľ myši alebo navigačný objekt). Položka, ktorou prestanete sledovať všetky aktuálne ciele, je na konci ponuky.

### Nastavenia cieľa

Každá položka v podponuke *Nastavenia cieľa* je začiarkavacie políčko a ukazuje to, čo cieľ skutočne robí: Jeho vlastnú hodnotu tam, kde ste ju nastavili, a všade inde [globálne nastavenie](#globálne-nastavenia). Začiarknutím alebo zrušením začiarknutia nastavíte cieľu vlastnú hodnotu práve pre toto jedno nastavenie, a to okamžite; všetky ostatné nastavenia ďalej rešpektujú globálnu hodnotu.

- *Pri oznamovaní novej zmeny prerušiť predchádzajúcu reč* sa zobrazuje pri všetkých cieľoch, ak je zapnutá [globálna možnosť *Oznámiť*](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté).
- *Aktualizovať históriu, keď je otvorená* sa zobrazuje pri všetkých cieľoch, ak [veľkosť histórie](#koľko-zmien-uchovávať-pre-každý-cieľ-editačné-pole-v-predvolenom-nastavení-50) nie je 0.
- *Pri otvorenej histórii oznamovať nové zmeny* sa zobrazuje pri všetkých cieľoch, ak [veľkosť histórie](#koľko-zmien-uchovávať-pre-každý-cieľ-editačné-pole-v-predvolenom-nastavení-50) nie je 0 a je zapnutá globálna možnosť [*Oznámiť*](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté).
- Možnosti *Ignorovať indikátory priebehu*, *Ignorovať počítadlá, krokovače a časovače*, *Považovať zmenu názvu za zmiznutie cieľa* a *Ignorovať známe generické prvky* sa zobrazujú len pri tých cieľoch, ktoré sú okná.
- *Sledovať tento cieľ aj v popredí* sa zobrazuje pri všetkých cieľoch.
- *Ignorovať prvok pod fokusom* sa zobrazuje, ak je cieľ okno a zároveň je pri ňom [nastavené, že sa má sledovať aj v popredí](#sledovať-aj-ciele-v-popredí-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté).
- *Pamätať si tento cieľ* sa zobrazuje pri všetkých cieľoch.
- *Zabudnúť tento cieľ, keď prestane existovať* sa zobrazuje len pri cieľoch, ktoré si doplnok pamätá.

Zmena [globálneho nastavenia](#globálne-nastavenia) sa prejaví aj pri existujúcich cieľoch, ak ste rovnaké nastavenie nezmenili osobitne práve pre tento cieľ. Panel nastavení zadáva výhradne globálne hodnoty: Nič, čo v ňom urobíte, cieľu jeho vlastnú hodnotu nevezme. Všetky vlastné hodnoty vymaže až to, že cieľ prestanete sledovať a pridáte ho znova, alebo že zapamätaný cieľ zabudnete.

### História nedávnych zmien

Táto podponuka uvádza toľko nedávnych zmien, ku ktorým v danom cieli došlo, koľko ste nastavili v možnosti [*Koľko zmien uchovávať pre každý cieľ*](#koľko-zmien-uchovávať-pre-každý-cieľ-editačné-pole-v-predvolenom-nastavení-50), v poradí určenom [*zoradením histórie zmien*](#zoradenie-cieľov) a s nastavenou [úrovňou podrobnosti](#do-popisov-v-ponuke-zahrnúť-zoskupenie). Ak je *Koľko zmien uchovávať pre každý cieľ* nastavené na 0, podponuka sa vôbec nezobrazí. Staršie zmeny nad tento počet sa odstraňujú. Toto nastavenie je iba globálne. Výberom ktorejkoľvek položky v tejto podponuke zobrazíte celú históriu v dialógovom okne na pohodlnejšie čítanie.

História zmizne, keď cieľ prestanete sledovať, keď je cieľ automaticky [zabudnutý potom, čo zmizne](#zabúdať-zapamätané-ciele-keď-prestanú-existovať-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté), alebo na konci relácie, a nikam sa neukladá. Keď je [sledovanie pozastavené](#povoliť-sledovanie-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté), história sa tiež neaktualizuje.

## Globálne nastavenia

Nastavenia doplnku nájdete v kategórii **Sledovanie obsahu na pozadí** v dialógu Nastavenia NVDA (ponuka NVDA → Možnosti → Nastavenia). Doplnok podporuje viacero konfiguračných profilov.

Súvisiace možnosti sú zoskupené. Všetky dostupné možnosti sú opísané nižšie v poradí, v akom sa v dialógu zobrazujú. Možnosti na najvyššej úrovni a celé zoskupenia sú nadpisy úrovne 3, jednotlivé možnosti vnútri zoskupení sú nadpisy úrovne 4.

### **Povoliť sledovanie** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Ak nie je začiarknuté, doplnok vás prestane upozorňovať, ale zachová celý zoznam cieľov aj všetky nastavenia, takže ho môžete umlčať (napríklad počas stretnutia) a neskôr znova zapnúť presne v tom stave, v akom bol. Ide o rovnaký prepínač, ktorý prepína [klávesová skratka na pozastavenie a obnovenie](#klávesové-skratky).

Toto nastavenie sa ako jediné nikdy neukladá: Pri spustení NVDA je sledovanie vždy povolené.

### **Interval sledovania** (editačné pole, v predvolenom nastavení 1)

Možno zapísať iba celé čísla. Nastavuje, ako často má doplnok kontrolovať zmeny vo všetkých existujúcich cieľoch, v sekundách. 0 znamená nikdy neoznamovať zmeny cieľov automaticky, iba ich zobrazovať v [ponuke cieľov](#ponuka-cieľov).

### **Koľko zmien oznámiť naraz (len ciele na pozadí)** (editačné pole, v predvolenom nastavení 5)

Možno zapísať iba celé čísla. Nastavuje, koľko po sebe idúcich zmien v rovnakom cieli má doplnok oznámiť v rade, kým budete musieť na cieľ znova presunúť fokus a potom sa opäť prepnúť inam, aby sa znova začali oznamovať nasledujúce zmeny. 0 znamená oznamovať každú zmenu.

Cieľov v popredí sa táto možnosť nikdy netýka. Ak je [sledovanie zapnuté aj pre ciele v popredí](#sledovať-aj-ciele-v-popredí-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté), oznamujú sa pri nich vždy všetky zmeny.

### **Čas do zatvorenia prekrytia** (editačné pole, v predvolenom nastavení 10)

Možno zapísať iba celé čísla. Určuje, koľko sekúnd bez stlačenia klávesy musí uplynúť, kým sa prekrytie samo zatvorí. Pri hodnote 0 sa prekrytie samo nezatvorí nikdy: Zostane otvorené, kým ho nezatvoríte klávesou escape alebo príkazom, ktorý presunie fokus inam, napríklad otvorením [ponuky cieľov](#ponuka-cieľov).

### **Sledovať aj ciele v popredí** (začiarkavacie políčko, v predvolenom nastavení nezačiarknuté)

V predvolenom stave sa zmeny v cieli čítajú len vo chvíli, keď pracujete niekde inde: Hneď ako jeho aplikácia získa fokus, doplnok si ju prestane všímať. Ak je táto možnosť povolená, nový obsah v cieli sa oznamuje aj vtedy, keď práve pracujete s týmto oknom alebo jednotlivým prvkom.

Ak aplikácia cieľa komunikuje s čítačmi obrazovky priamo (prostredníctvom živých regiónov ARIA alebo iných udalostí prístupnosti), môžu sa pri práci v jej okne rovnaké oznámenia niekedy ohlásiť dvakrát – raz samotnou aplikáciou a raz doplnkom. Ak chcete v takom prípade počuť len vlastné oznámenia aplikácie, môžete v [nastaveniach daného cieľa](#nastavenia-cieľa) zrušiť začiarknutie *Sledovať tento cieľ aj v popredí*, dočasne pozastaviť sledovanie, alebo cieľ odobrať a neskôr ho pridať znova. Ak chcete počuť len oznámenia doplnku, vypnite v NVDA možnosť „Oznamovať dynamicky menený obsah“ (v predvolenom nastavení NVDA+5).

### **História nedávnych zmien** (zoskupenie)

Možnosti v tomto zoskupení určujú správanie [histórie nedávnych zmien](#história-nedávnych-zmien) uchovávanej osobitne pre každý cieľ.

#### **Koľko zmien uchovávať pre každý cieľ** (editačné pole, v predvolenom nastavení 50)

Možno zapísať iba celé čísla. Nastavuje, koľko nedávnych zmien sa má uchovávať v [histórii každého cieľa](#história-nedávnych-zmien). Staršie zmeny sa zahadzujú. 0 znamená žiadnu históriu a ostatné možnosti v tomto zoskupení sú potom nedostupné.

Pri zapamätaných cieľoch, ktoré zmizli, sa história tiež uchováva a zostáva dostupná, kým cieľ neodoberiete, alebo do konca relácie.

#### **Aktualizovať históriu, keď je otvorená** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Ak je začiarknuté, do otvoreného dialógu s históriou sa budú priebežne pridávať nové zmeny. Ak nie, dialóg zostane v takom stave, v akom bol po otvorení.

#### **Pri otvorenej histórii oznamovať nové zmeny** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Táto možnosť je dostupná, iba ak je začiarknuté políčko [**Oznámiť**](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté). Ak je zakázaná, nové zmeny v cieli sa nebudú oznamovať, kým je otvorený dialóg histórie.

### Zoradenie cieľov

Tri sady prepínačov, jedna za druhou: *Zoradenie cieľov v slotoch*, *Zoradenie cieľov v ponuke* a *Zoradenie histórie zmien*. Všetky ponúkajú rovnaké možnosti uvedené nižšie (až na niekoľko výnimiek) a možno ich nastaviť buď zhodne, alebo nezávisle od seba. Určujú, v akom poradí sa ciele umiestňujú do desiatich dostupných číslovaných slotov (pozri [Klávesové skratky](#klávesové-skratky)), zobrazujú v [ponuke cieľov](#ponuka-cieľov), respektíve zoraďujú v [histórii nedávnych zmien jednotlivých cieľov](#história-nedávnych-zmien).

- *Najnovší cieľ prvý / najnovšia zmena prvá* (predvolené nastavenie pri všetkých typoch zoradenia)
- *Najstarší cieľ prvý / najstaršia zmena prvá*
- *Naposledy zmenený cieľ prvý* (pri zoradení histórie nie je k dispozícii)
- *Najdlhšie nezmenený cieľ prvý* (pri zoradení histórie nie je k dispozícii)
- *Abecedne, A až Z*
- *Abecedne, Z až A*

### **Pamätať si ciele** (začiarkavacie políčko, v predvolenom nastavení nezačiarknuté)

Ak je začiarknuté, zoznam cieľov zostane zachovaný aj po reštarte NVDA a doplnok sa k cieľu znova pripojí zakaždým, keď sa cieľ znova objaví. Sleduje tak napríklad okno asistenta pri každom jeho otvorení bez toho, aby ste to museli znova nastavovať. Ak začiarknuté nie je, začína zoznam cieľov pri každom spustení prázdny a ukladajú sa iba vaše nastavenia.

### **Zabúdať zapamätané ciele, keď prestanú existovať** (začiarkavacie políčko, v predvolenom nastavení nezačiarknuté)

Táto možnosť je dostupná, iba ak je začiarknuté [**Pamätať si ciele**](#pamätať-si-ciele-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté). Určuje, či sa má zapamätaný cieľ zabudnúť, hneď ako prestane existovať – zatvorili ste jeho okno alebo zmizlo samo. Ak je povolená, budete musieť každý cieľ začať sledovať znova zakaždým, keď zmizne.

Ciele, ktoré prestanete sledovať ručne, budú zabudnuté vždy, nech je táto možnosť nastavená akokoľvek.

### **Správanie pri sledovaní okien** (zoskupenie)

Možnosti v tomto zoskupení spresňujú, ako má doplnok oznamovať zmeny v sledovaných oknách.

#### **Ignorovať indikátory priebehu** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Ak je začiarknutá, táto možnosť potlačí oznamovanie meniacich sa indikátorov priebehu v okne. Samotné NVDA vie ohlasovať natívne indikátory priebehu slovne alebo pípaním, aj na pozadí, takže nemusí byť žiaduce, aby vás tento doplnok zahlcoval dvojitým hlásením neustále sa meniaceho indikátora priebehu v konkrétnej aplikácii.

#### **Ignorovať počítadlá, krokovače a časovače** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Ak je začiarknuté, doplnok sleduje, či sa pri niektorom prvku nemení nič iné ako čísla – časovač alebo odpočet tikajúci každú sekundu, počítadlo krokov či položiek, percentá, ako napríklad aplikácia Claude počítajúca, ako dlho modelu trvalo premýšľanie. Tieto prvky bývajú často skôr na príťaž než na úžitok, pretože samy osebe neposkytujú žiadnu užitočnú informáciu a hlavne nevypovedajú o žiadnej skutočnej zmene – len naznačujú, že úloha stále beží. Hneď ako doplnok taký prvok pristihne, umlčí ho na celý čas, kým je cieľ sledovaný.

#### **Považovať zmenu názvu za zmiznutie cieľa** (začiarkavacie políčko, v predvolenom nastavení nezačiarknuté)

Ak je začiarknuté a zmení sa názov okna, ktoré sledujete, doplnok ho začne považovať za iné okno, a teda sa zachová rovnako, ako keby pôvodný cieľ zmizol, hoci fyzické okno v systéme je stále rovnaké.

#### **Ignorovať známe generické prvky** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Ak je začiarknuté, potlačí oznamovanie generických prvkov, ako napríklad keď sa tlačidlo „Minimalizovať“ v príslušnom okne zmení na „Maximalizovať“ a naopak. Patria sem:

- Panel ponúk aplikácie (zvyčajne sa naň prechádza klávesou alt)
- Tlačidlá „Minimalizovať“, „Obnoviť“, „Maximalizovať“ a „Zavrieť“
- Tlačidlá „OK“, „Zrušiť“, „Prerušiť“, „Opakovať“, „Pokračovať“, „Ďalej“, „Predchádzajúce“, „Späť“, „Dokončiť“ a „Teraz nie“
- A tlačidlá „Áno“ a „Nie“.

#### **Pri sledovaní okna v popredí ignorovať prvok pod fokusom** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Táto možnosť je dostupná, iba ak je začiarknuté [Sledovať aj ciele v popredí](#sledovať-aj-ciele-v-popredí-začiarkavacie-políčko-v-predvolenom-nastavení-nezačiarknuté), pretože sa prejaví len pri okne, ktoré sa číta vo chvíli, keď v ňom práve pracujete. Okien na pozadí ani cieľov, ktoré sledujú jednotlivé prvky, sa tak či tak netýka.

Ak je povolená, prvok, ktorý má práve fokus, sa nikdy neoznámi ako zmena, takže sa vám napríklad znaky, ktoré píšete do editačného poľa, nebudú hlásiť ako nový obsah.

### **Pri zmene cieľa** (zoskupenie)

Čo sa stane, keď sa v sledovanom cieli objaví nový obsah.

#### **Pípnuť** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Prehrá tón, keď sa cieľ zmení.

#### **Oznámiť** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Oznámi, čo sa kde zmenilo, napríklad „Okno: Claude“ alebo „Zoznam: Zoznam správ“. Úroveň podrobnosti oznámenia možno ďalej upraviť nižšie.

#### **Pri oznamovaní novej zmeny prerušiť predchádzajúcu reč** (začiarkavacie políčko, v predvolenom nastavení nezačiarknuté)

Táto možnosť je dostupná, iba ak je začiarknuté vyššie uvedené políčko [**Oznámiť**](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté). Ak je povolená, oznámenie o zmene preruší aktuálnu reč NVDA a prečíta sa ihneď. Ak je zakázaná, oznámenie o zmene počká, kým NVDA dohovorí.

#### **Pri po sebe idúcich zmenách v rovnakom cieli zopakovať jeho názov** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Táto možnosť je dostupná, iba ak je zapnuté [slovné oznamovanie ako také](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté). Ak je povolená, názov cieľa zaznie v každom oznámení zmeny, aj keď v tom istom cieli došlo k niekoľkým zmenám po sebe. Ak je zakázaná, názov cieľa sa oznámi len pri prvej zmene v rovnakom cieli.

### **Parametre pípnutia** (zoskupenie)

Možnosti v tomto zoskupení sú dostupné, iba ak je začiarknuté vyššie uvedené políčko [**Pípnuť**](#pípnuť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté).

#### **Dĺžka** (editačné pole, v predvolenom nastavení 50)

Možno zapísať iba celé čísla. Nastavuje, ako dlho má pípnutie trvať, v milisekundách.

#### **Výška** (editačné pole, v predvolenom nastavení 440)

Možno zapísať iba celé čísla. Nastavuje, s akou frekvenciou sa má pípnutie prehrávať, v hertzoch.

#### **Otestovať** (tlačidlo)

Prehrá testovacie pípnutie s aktuálne nastavenými parametrami, aby ste si mohli overiť, či znie tak, ako chcete.

### **Do oznámenia o zmene zahrnúť** (zoskupenie)

Možnosti v tomto zoskupení sú dostupné, iba ak je začiarknuté vyššie uvedené políčko [**Oznámiť**](#oznámiť-začiarkavacie-políčko-v-predvolenom-nastavení-začiarknuté). Určujú, z čoho presne sa oznámenie o zmene skladá.

#### **Typ cieľa** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Či oznamovať typ (rolu) cieľa (napríklad **okno**, **zoznam** alebo **editačné pole**).

#### **Zmenený obsah** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Či oznamovať nový obsah v cieli po poslednej zmene.

### **Do popisov v ponuke zahrnúť** (zoskupenie)

Možnosti v tomto zoskupení určujú, ako budú vyzerať popisy položiek v [ponuke cieľov](#ponuka-cieľov). Ovplyvňujú tiež, ako sa zapisujú položky do [histórie zmien](#história-nedávnych-zmien) jednotlivých cieľov.

#### **Typ cieľa** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Či v texte príslušnej položky daného cieľa zobrazovať typ (rolu) cieľa (napríklad **okno**, **zoznam** alebo **editačné pole**).

#### **Čas od poslednej zmeny** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Či v texte príslušnej položky daného cieľa zobrazovať relatívny čas od poslednej zmeny (napríklad pred 3 minútami).

#### **Zmenený obsah** (začiarkavacie políčko, v predvolenom nastavení začiarknuté)

Či v texte príslušnej položky daného cieľa zobrazovať nový obsah po poslednej zmene.

## Známe obmedzenia (treba prepísať)

- **Karty prehliadačov na pozadí nemožno sledovať.** Webové prehliadače udržiavajú čitateľnú iba tú kartu, na ktorú sa práve pozeráte. Ak chcete niektorú stránku sledovať, zatiaľ čo pracujete inde, otvorte si ju vo vlastnom okne namiesto na karte na pozadí. Vidiaci používatelia kartu na pozadí tiež nevidia.
- **Niektoré aplikácie toho na pozadí zobrazujú len veľmi málo.** Koľko toho aplikácia prezradí čítaču obrazovky o obsahu, na ktorom nie je fokus, riadi výhradne ona sama. Moderné aplikácie postavené na technológii UIA – Terminál, Nastavenia, Kalkulačka, Fotografie a väčšina aplikácií z Microsoft Storu – a aplikácie vykresľované ako webová stránka – desktopové aplikácie Claude a ChatGPT, nový Outlook, Visual Studio Code, Discord, Slack, Signal, WhatsApp pre Windows, Spotify aj skutočné webové stránky – sa v tomto ohľade značne líšia. Ak aplikácia nový obsah nesprístupňuje ako text, doplnok ho ohlásiť nedokáže.
- **Počíta sa len to, čo sa v okne práve zobrazuje.** Dlhé zoznamy – história chatu, zoznamy súborov, výsledky hľadania – existujú zvyčajne len ako tých niekoľko riadkov, ktoré sú práve zobrazené. Doplnok nevidí položky posunuté mimo obrazovku, rovnako ako ich nevidia vidiaci používatelia, a minimalizované okno môže prestať svoj obsah zobrazovať úplne, kým ho neobnovíte – podľa toho, ako je daná aplikácia naprogramovaná.

Ak často potrebujete vedieť o aktualizáciách z aplikácie, ktorú používate na pozadí, býva zvyčajne spoľahlivejšie a jednoduchšie nastaviť samotnú aplikáciu tak, aby vám posielala oznámenia, ak to daná aplikácia umožňuje. Tiež keď aplikáciu minimalizujete do systémovej lišty, prestane zobrazovať viditeľné okno, takže ju doplnok už nemôže sledovať. Ak však ikona na systémovej lište zobrazuje užitočné informácie vo forme textu, môžete sledovať priamo túto ikonu.

## Spolupráca

Ak by ste chceli prispieť k vývoju doplnku – či už prekladom, hlásením chýb alebo vytvorením pull requestu – a viete, ako na to, môžete to urobiť v jeho [repozitári na GitHube](https://github.com/4sensegaming/background-content-tracker). Akúkoľvek pomoc vítam a vážim si ju.

## História zmien

### Verzia 1.0, 18. októbra 2026
* Prvá verzia
