# Sledování obsahu na pozadí

**Čeština** | [Deutsch](../de/readme.md) | [English](../../../readme.md) | [Italiano](../it/readme.md) | [Slovenčina](../sk/readme.md)

* Autor: Lukáš Hosnedl
* Minimální verze NVDA: 2026.3
* Poslední testovaná verze NVDA: 2027.1

**Vytvořeno umělou inteligencí, navrženo a důkladně otestováno lidmi.**

## Popis

Doplněk Sledování obsahu na pozadí sleduje okno nebo jednotlivý prvek a dá vám vědět, jakmile se v něm objeví nový obsah. Můžete tak dál pracovat v jednom okně, zatímco doplněk hlídá jiné.

Když vidící lidé pracují v jednom okně, okamžitě zaznamenají, že ve vedlejším okně něco vyskočilo nebo se změnilo, a dokážou odhadnout, jestli to vyžaduje pozornost hned, nebo až za chvíli. NVDA umí oznamovat upozornění a živé regiony, ale obvykle jen ve chvíli, kdy je dané okno v popředí, takže změny, ke kterým došlo, zatímco jste pracovali jinde, vám mohou snadno uniknout.

Sledování obsahu na pozadí vám dává přesně tento přehled: Vyberete si, co se má sledovat a jak chcete být upozorněni, a NVDA vás na změnu obsahu upozorní, aniž byste museli opustit to, co právě děláte.

Tento doplněk je velmi silný a přizpůsobitelný nástroj, který dokáže z nepřístupných oken nebo prvků v podstatě udělat mluvící živé regiony, které fungují všude. Překvapivě dobře si rozumí například s:

- Terminály,
- Dynamickými zprávami uvnitř jednoho seznamu, textové oblasti nebo jiného kontejneru,
- Webovými stránkami, které se průběžně aktualizují,
- Komunikačními aplikacemi, které samy nečtou nové příchozí zprávy,
- A také s aplikacemi postavenými na Electronu, jako je nový ChatGPT, které dlouho mlčí a pak začnou chrlit velké kusy textu, pokaždé na jiné pozici v okně.

Doplněk ale nejspíš ocení jen pokročilí uživatelé, kteří potřebují zrychlit a zefektivnit svou práci, například:

- Ti, kdo běžně používají AI k tvorbě něčeho rozsáhlejšího,
- Ti, kdo často spouštějí dlouhotrvající automatizované úlohy a potřebují v reálném čase sledovat jejich výstup,
- Ti, kdo musí často přepínat mezi několika různými okny s dynamickým výstupem,
- Nebo ti, kdo se podílejí na částečně či plně automatizovaných procesech, v nichž běží několik úloh naráz.

Pokud ho potřebujete, nejspíš to už víte. Ostatním může připadat zahlcující, přeplácaný nebo matoucí.

## Použití

Vytvoříte si seznam cílů ke sledování – celých oken nebo jednotlivých prvků, třeba editačních polí či seznamů zpráv v chatech – a doplněk vás upozorní pokaždé, když se v některém z nich objeví nový obsah. Můžete sledovat více cílů najednou a každý z nich začít nebo přestat sledovat nezávisle na ostatních.

### Příklady použití

- **Čekání na dlouhou úlohu v jiné aplikaci.** Zadáte úkol AI asistentovi, například Claudovi, a místo abyste čekali v jeho okně, přepnete se jinam a věnujete se něčemu jinému. Doplněk sleduje okno asistenta a dá vám vědět, jakmile se objeví nový výstup, takže poznáte, že odpověděl, aniž byste se museli znovu a znovu vracet a kontrolovat to.
- **Sledování webové stránky, zatímco píšete jinde.** Píšete v chatu, například ve WhatsAppu, a vedle máte přitom otevřenou webovou stránku. Když se tato stránka na pozadí aktualizuje, doplněk vám to oznámí – takže si toho všimnete stejně jako vidící uživatel.

### Typický postup

1. Přejděte na okno nebo prvek, který chcete sledovat: Přesuňte na něj fokus, najeďte na něj myší nebo na něj přesuňte objektovou navigaci či prohlížecí kurzor.
2. Začněte ho sledovat – buď příslušnou [klávesovou zkratkou](#klávesové-příkazy), nebo výběrem z [nabídky cílů](#nabídka-cílů).
3. Přepněte se na to, čemu se chcete věnovat. Když se ve sledovaném cíli objeví nový obsah, NVDA vás upozorní tak, jak jste si [nastavili](#globální-nastavení).
4. Až daný cíl nebudete potřebovat, přestaňte ho sledovat, nebo vymažte celý seznam cílů najednou.

## Klávesové příkazy

Doplněk se ovládá jediným **vrstveným příkazem**: Stisknete klávesovou zkratku, uvolníte ji a poté stisknete ještě jednu klávesu, kterou zvolíte požadovanou akci. Po stisku samotné hlavní klávesové zkratky se nic nestane, takže příkazy doplňku nikdy nekolidují s NVDA ani jinými aplikacemi.

Výchozí klávesová zkratka je NVDA+; (středník – na české klávesnici klávesa nalevo od číslice 1).

Po stisku hlavní klávesové zkratky doplněk otevře **virtuální překrytí**. Dokud je překrytí otevřené, považuje se každý stisk klávesy za jeden z níže uvedených příkazů. Otevření ani zavření překrytí nepřesouvá fokus, takže příkazy doplňku nikdy nenaruší to, co právě děláte.

Po stisku hlavní klávesové zkratky stiskněte jednu z následujících kláves:

- `H` – **nápověda**: Stručně vysvětlí, k čemu slouží každá klávesa dostupná v překrytí. Dvojím stiskem zobrazíte text nápovědy v dialogovém okně pro pohodlnější čtení.
- `F1` – **otevře tuto dokumentaci** ve výchozím webovém prohlížeči. Tento příkaz je kontextový: V překrytí přejde na tuto kapitolu, v nabídce na kapitolu [Nabídka cílů](#nabídka-cílů), při otevřeném dialogu nastavení na kapitolu [Globální nastavení](#globální-nastavení) a tak dále.
- `W` – začne nebo přestane sledovat aktuální **okno**.
- `F` – začne nebo přestane sledovat prvek, který má právě **fokus** klávesnice.
- `M` – začne nebo přestane sledovat prvek pod ukazatelem **myši**.
- `N` – začne nebo přestane sledovat aktuální **prohlížený objekt** (tam, kde je prohlížecí kurzor).
- `T` – otevře **[nabídku cílů](#nabídka-cílů)**.
- `1` až `0` – **oznámí informace o příslušném cíli** podle jeho pořadí v seznamu (viz níže). Dvojím stiskem téhož čísla se na daný cíl přesune fokus, trojím se otevře přímo jeho [historie nedávných změn](#historie-nedávných-změn).
- `Control`+číslo (`1` až `0`) – **přestane sledovat** cíl v daném slotu.
- `Alt`+číslo (`1` až `0`) – **[otevře nabídku](#nabídka-cílů)** přímo pro cíl v daném slotu.
- `Mezerník` nebo `enter` – totéž jako číselné zkratky, ale vždy pro **naposledy přidaný** cíl: Prvním stiskem si o něm necháte oznámit informace, druhým se na něj přesune fokus, třetím se otevře jeho historie.
- `Backspace` – **přestane sledovat naposledy přidaný** cíl.
- `Delete` – **přestane sledovat všechny cíle** (vymaže celý seznam najednou).
- `P` – **pozastaví nebo obnoví** veškeré sledování (přepíná přepínač [*Povolit sledování*](#povolit-sledování-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto)).
- `S` – otevře **[nastavení](#globální-nastavení)** doplňku (stejná záložka jako nabídka NVDA → Možnosti → Nastavení → Sledování obsahu na pozadí).
- `I` – otevře dialog **Klávesové příkazy** NVDA přímo na kategorii Sledování obsahu na pozadí, takže můžete hlavní klávesovou zkratku přenastavit, aniž byste ji museli hledat.
- `Escape` – **zavře překrytí** a neprovede nic jiného.

Příkazy pro okno, fokus, myš a prohlížený objekt fungují jako přepínače: Prvním stisknutím daný cíl přidáte do seznamu, opětovným stisknutím ho odeberete, pokud je to pořád aktuální okno, prvek s fokusem a podobně. Sledovat můžete libovolný počet cílů současně.

Tyto čtyři příkazy zohledňují i klávesy `shift` a `control`, které určují, jak se má cíl sledovat: `Shift` si daný cíl zapamatuje, `control` ho nechá číst i ve chvíli, kdy je jeho aplikace v popředí, a s oběma klávesami najednou platí obojí. Jde o [volby pro jednotlivý cíl](#nastavení-cíle) zadané přímo tomuto cíli při jeho přidání místo toho, aby se přejaly z [globálních nastavení](#globální-nastavení) nebo dodatečně ručně měnily v [nabídce cílů](#nabídka-cílů). Globální nastavení se přitom nezmění. Příkaz, který sledování cíle *ukončuje*, místo aby ho přidal, tyto modifikační klávesy prostě ignoruje. Modifikační klávesy se hodí jen tehdy, když máte možnost [**Pamatovat si cíle**](#pamatovat-si-cíle-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto) nebo [**Sledovat i cíle v popředí**](#sledovat-i-cíle-v-popředí-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto) globálně vypnutou, ale pro tento konkrétní cíl dané chování potřebujete.

Číselné zkratky odkazují na **sloty** v seznamu cílů, nikoli na pevně dané pozice. Ve výchozím nastavení je `1` naposledy přidaný cíl, `2` ten předposlední a tak dál až po `0` – desátý slot. [Nastavení **Řazení cílů ve slotech**](#řazení-cílů) může sloty seřadit jinak, třeba od nejstaršího cíle, od naposledy změněného cíle nebo abecedně. Když některý cíl zmizí – protože jste ho přestali sledovat nebo přestal existovat – cíle za ním se posunou a mezeru zaplní, takže číslo `2` vždy oznámí ten cíl, který je právě teď v seznamu jako druhý.

Pokud cíl existuje, doplněk ve výchozím nastavení oznámí jeho typ (roli), název a změněný obsah cíle, například *Okno: Claude, Editing readme.md* nebo *Seznam: Seznam zpráv, Řekli jste: Tak jo*. Úroveň podrobnosti těchto oznámení lze [upravit v nastavení doplňku](#do-oznámení-o-změně-zahrnout-skupina).

Hlavní klávesovou zkratku můžete změnit v dialogu Klávesové příkazy (nabídka NVDA → Možnosti → Klávesové příkazy), kde se příkaz doplňku nachází v kategorii **Sledování obsahu na pozadí**. Následné klávesy jsou součástí samotného příkazového překrytí.

## Nabídka cílů

**Nabídka cílů** (hlavní klávesová zkratka následovaná klávesou `t`) zobrazuje všechny sledované cíle jako seřazené položky nabídky, takže si nemusíte pamatovat aktuální pořadí cíle v seznamu ani žádnou z ostatních kláves.

Každá položka přesně pojmenovává, čeho se týká, například *Okno: Claude, před 3 minutami, 3 tasks running*. Cíl, který právě neexistuje – zapamatovaný cíl, jehož okno není otevřené – uvádí *Nenalezeno* a v nabídce zůstává, protože ho pořád můžete přestat sledovat, změnit jeho nastavení nebo počkat, až se objeví. Pořadí, ve kterém jsou cíle zobrazeny, se řídí [nastavením **Řazení cílů v nabídce**](#řazení-cílů).

Každý cíl je podnabídkou. Když ji rozbalíte, můžete:

- Cíl *Přestat sledovat*,
- *Přesunout fokus* na něj (pokud ho už nemá),
- Změnit jeho [*Nastavení cíle*](#nastavení-cíle),
- Nebo procházet jeho [historii **nedávných změn**](#historie-nedávných-změn) (nezobrazí se, pokud se zatím v cíli nic nezměnilo nebo pokud je [velikost historie](#kolik-změn-uchovávat-pro-každý-cíl-editační-pole-ve-výchozím-nastavení-50) nastavena na 0).

Vše, co už sledujete, se v nabídce zobrazí jako první, takže se na daný cíl můžete rychle přesunout nebo ho přestat sledovat. Dále se zobrazí cíle, které můžete začít sledovat ze své aktuální pozice (okno, fokus, ukazatel myši nebo prohlížený objekt). Položka pro ukončení sledování všech aktuálních cílů je na konci nabídky.

### Nastavení cíle

Každá položka v podnabídce *Nastavení cíle* je zaškrtávací políčko a ukazuje to, co cíl skutečně dělá: Jeho vlastní hodnotu tam, kde jste ji nastavili, a všude jinde [globální nastavení](#globální-nastavení). Zaškrtnutím nebo odškrtnutím nastavíte cíli vlastní hodnotu právě pro toto jedno nastavení, a to okamžitě; všechna ostatní nastavení dál respektují globální hodnotu.

- *Při oznamování nové změny přerušit předchozí řeč* se zobrazuje u všech cílů, pokud je zapnuta [globální možnost *Oznámit*](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto).
- *Aktualizovat historii, když je otevřená* se zobrazuje u všech cílů, pokud [velikost historie](#kolik-změn-uchovávat-pro-každý-cíl-editační-pole-ve-výchozím-nastavení-50) není 0.
- *Při otevřené historii oznamovat nové změny* se zobrazuje u všech cílů, pokud [velikost historie](#kolik-změn-uchovávat-pro-každý-cíl-editační-pole-ve-výchozím-nastavení-50) není 0 a je zapnuta globální možnost [*Oznámit*](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto).
- Možnosti *Ignorovat indikátory průběhu*, *Ignorovat počítadla, krokovače a časovače*, *Považovat změnu názvu za zmizení cíle* a *Ignorovat známé generické prvky* se zobrazují jen u těch cílů, které jsou okna.
- *Sledovat tento cíl i v popředí* se zobrazuje u všech cílů.
- *Ignorovat prvek pod fokusem* se zobrazuje, pokud je cíl okno a zároveň je u něj [nastaveno, že se má sledovat i v popředí](#sledovat-i-cíle-v-popředí-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto).
- *Pamatovat si tento cíl* se zobrazuje u všech cílů.
- *Zapomenout tento cíl, když přestane existovat* se zobrazuje jen u cílů, které si doplněk pamatuje.

Změna [globálního nastavení](#globální-nastavení) se projeví i u existujících cílů, pokud jste stejné nastavení nezměnili zvlášť právě pro tento cíl. Panel nastavení zadává výhradně globální hodnoty: Nic, co v něm uděláte, cíli jeho vlastní hodnotu nevezme. Všechny vlastní hodnoty vymaže až to, že cíl přestanete sledovat a přidáte ho znovu, nebo že zapamatovaný cíl zapomenete.

### Historie nedávných změn

Tato podnabídka uvádí tolik nedávných změn, ke kterým v daném cíli došlo, kolik jste nastavili v možnosti [*Kolik změn uchovávat pro každý cíl*](#kolik-změn-uchovávat-pro-každý-cíl-editační-pole-ve-výchozím-nastavení-50), v pořadí určeném [*řazením historie změn*](#řazení-cílů) a s nastavenou [výřečností](#do-popisů-v-nabídce-zahrnout-skupina). Pokud je *Kolik změn uchovávat pro každý cíl* nastaveno na 0, podnabídka se vůbec nezobrazí. Starší změny nad tento počet se odstraňují. Toto nastavení je pouze globální. Výběrem kterékoli položky v této podnabídce zobrazíte celou historii v dialogovém okně pro pohodlnější čtení.

Historie zmizí, když cíl přestanete sledovat, když je cíl automaticky [zapomenut poté, co zmizí](#zapomínat-zapamatované-cíle-když-přestanou-existovat-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto), nebo na konci relace, a nikam se neukládá. Když je [sledování pozastaveno](#povolit-sledování-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto), historie se také neaktualizuje.

## Globální nastavení

Nastavení doplňku najdete v kategorii **Sledování obsahu na pozadí** v dialogu Nastavení NVDA (nabídka NVDA → Možnosti → Nastavení). Doplněk podporuje více konfiguračních profilů.

Související možnosti jsou uspořádány do skupin. Všechny dostupné možnosti jsou popsány níže v pořadí, v jakém se v dialogu zobrazují. Možnosti na nejvyšší úrovni a celé skupiny jsou nadpisy úrovně 3, jednotlivé možnosti uvnitř skupin jsou nadpisy úrovně 4.

### **Povolit sledování** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud není zaškrtnuto, doplněk vás přestane upozorňovat, ale zachová celý seznam cílů i všechna nastavení, takže ho můžete umlčet (třeba během schůzky) a později zase zapnout přesně v tom stavu, v jakém byl. Jde o stejný přepínač, který přepíná [klávesa pro pozastavení a obnovení](#klávesové-příkazy).

Toto nastavení se jako jediné nikdy neukládá: Při spuštění NVDA je sledování vždy povoleno.

### **Interval sledování** (editační pole, ve výchozím nastavení 1)

Lze zapsat pouze celá čísla. Nastavuje, jak často má doplněk kontrolovat změny ve všech existujících cílech, v sekundách. 0 znamená nikdy neoznamovat změny cílů automaticky, pouze je zobrazovat v [nabídce cílů](#nabídka-cílů).

### **Kolik změn oznámit najednou (jen cíle na pozadí)** (editační pole, ve výchozím nastavení 5)

Lze zapsat pouze celá čísla. Nastavuje, kolik po sobě jdoucích změn ve stejném cíli má doplněk oznámit v řadě, než budete muset cíl znovu fokusovat a poté se opět přepnout jinam, aby se zase začaly oznamovat následující změny. 0 znamená oznamovat každou změnu.

Cílů v popředí se tato možnost nikdy netýká. Pokud je [sledování zapnuto i pro cíle v popředí](#sledovat-i-cíle-v-popředí-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto), oznamují se u nich vždy všechny změny.

### **Čas do zavření překrytí** (editační pole, ve výchozím nastavení 10)

Lze zapsat pouze celá čísla. Určuje, kolik sekund bez stisku klávesy musí uplynout, než se překrytí samo zavře. Při hodnotě 0 se překrytí samo nezavře nikdy: Zůstane otevřené, dokud ho nezavřete klávesou escape nebo příkazem, který přesune fokus jinam, například otevřením [nabídky cílů](#nabídka-cílů).

### **Sledovat i cíle v popředí** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Ve výchozím stavu se změny v cíli čtou jen ve chvíli, kdy pracujete někde jinde: Jakmile jeho aplikace získá fokus, doplněk si jí přestane všímat. Pokud je tato možnost povolena, nový obsah v cíli se oznamuje i tehdy, když právě pracujete s tímto oknem nebo jednotlivým prvkem.

Pokud aplikace cíle komunikuje s odečítači obrazovky přímo (prostřednictvím živých regionů ARIA nebo jiných událostí přístupnosti), mohou se při práci v jejím okně stejná oznámení někdy ohlásit dvakrát – jednou samotnou aplikací a jednou doplňkem. Chcete-li v takovém případě slyšet jen vlastní oznámení aplikace, můžete v [nastavení daného cíle](#nastavení-cíle) odškrtnout *Sledovat tento cíl i v popředí*, dočasně pozastavit sledování, nebo cíl odebrat a později ho přidat znovu. Chcete-li slyšet jen oznámení doplňku, vypněte v NVDA hlášení dynamických změn obsahu (ve výchozím nastavení NVDA+5).

### **Historie nedávných změn** (skupina)

Možnosti v této skupině určují chování [historie nedávných změn](#historie-nedávných-změn) uchovávané zvlášť pro každý cíl.

#### **Kolik změn uchovávat pro každý cíl** (editační pole, ve výchozím nastavení 50)

Lze zapsat pouze celá čísla. Nastavuje, kolik nedávných změn se má uchovávat v [historii každého cíle](#historie-nedávných-změn). Starší změny se zahazují. 0 znamená žádnou historii a ostatní možnosti v této skupině jsou pak nedostupné.

U zapamatovaných cílů, které zmizely, se historie také uchovává a zůstává dostupná, dokud cíl neodeberete, nebo do konce relace.

#### **Aktualizovat historii, když je otevřená** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, do otevřeného dialogu s historií se budou průběžně přidávat nové změny. Pokud ne, dialog zůstane v takovém stavu, v jakém byl po otevření.

#### **Při otevřené historii oznamovat nové změny** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Tato možnost je dostupná, pouze pokud je zaškrtnuto políčko [**Oznámit**](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto). Pokud je zakázána, nové změny v cíli nebudou oznamovány, dokud je otevřený dialog historie.

### Řazení cílů

Tři sady přepínačů, jedna za druhou: *Řazení cílů ve slotech*, *Řazení cílů v nabídce* a *Řazení historie změn*. Všechny nabízejí stejné možnosti uvedené níže (až na několik výjimek) a lze je nastavit buď shodně, nebo nezávisle na sobě. Určují, v jakém pořadí se cíle umisťují do deseti dostupných číslovaných slotů (viz [Klávesové příkazy](#klávesové-příkazy)), zobrazují v [nabídce cílů](#nabídka-cílů), respektive řadí v [historii nedávných změn jednotlivých cílů](#historie-nedávných-změn).

- *Nejnovější cíl / změna první* (výchozí nastavení u všech typů řazení)
- *Nejstarší cíl / změna první*
- *Naposledy změněný cíl první* (u řazení historie není k dispozici)
- *Nejdéle nezměněný cíl první* (u řazení historie není k dispozici)
- *Abecedně, A až Z*
- *Abecedně, Z až A*

### **Pamatovat si cíle** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Pokud je zaškrtnuto, seznam cílů zůstane zachován i po restartu NVDA a doplněk se k cíli znovu připojí pokaždé, když se cíl znovu objeví. Sleduje tak například okno asistenta při každém jeho otevření, aniž byste to museli znovu nastavovat. Pokud zaškrtnuto není, začíná seznam cílů při každém spuštění prázdný a ukládají se pouze vaše nastavení.

### **Zapomínat zapamatované cíle, když přestanou existovat** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Tato možnost je dostupná, pouze pokud je zaškrtnuto [**Pamatovat si cíle**](#pamatovat-si-cíle-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto). Určuje, jestli se má zapamatovaný cíl zapomenout, jakmile přestane existovat – zavřeli jste jeho okno nebo zmizelo samo. Pokud je povolena, budete každý cíl muset začít sledovat znovu pokaždé, když zmizí.

Cíle, které přestanete sledovat ručně, budou zapomenuty vždy, ať je tato možnost nastavena jakkoli.

### **Chování při sledování oken** (skupina)

Možnosti v této skupině upřesňují, jak má doplněk oznamovat změny ve sledovaných oknech.

#### **Ignorovat indikátory průběhu** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuta, tato možnost potlačí oznamování měnících se indikátorů průběhu v okně. Samotné NVDA umí ohlašovat nativní indikátory průběhu slovně anebo pípáním, i na pozadí, takže nemusí být žádoucí, aby vás tento doplněk zahlcoval dvojím hlášením neustále se měnícího indikátoru průběhu v konkrétní aplikaci.

#### **Ignorovat počítadla, krokovače a časovače** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, doplněk sleduje, jestli se u některého prvku nemění nic jiného než čísla – časovač nebo odpočet tikající každou sekundu, počítadlo kroků či položek, procenta, jako třeba aplikace Claude počítající, jak dlouho modelu trvalo přemýšlení. Tyto prvky bývají často spíše na obtíž než k užitku, protože samy o sobě neposkytují žádnou užitečnou informaci a hlavně nevypovídají o žádné skutečné změně – jen naznačují, že úloha stále běží. Jakmile doplněk takový prvek přistihne, umlčí ho po celou dobu, kdy je cíl sledován.

#### **Považovat změnu názvu za zmizení cíle** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Pokud je zaškrtnuto a změní se název okna, které sledujete, doplněk ho začne považovat za jiné okno a tedy se zachová stejně, jako by původní cíl zmizel, přestože fyzické okno v systému je pořád stejné.

#### **Ignorovat známé generické prvky** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, potlačí oznamování generických prvků, jako například když se tlačítko „Minimalizovat“ v příslušném okně změní na „Maximalizovat“ a naopak. Patří sem:

- Panel nabídek aplikace (obvykle se na něj přechází klávesou alt)
- Tlačítka „Minimalizovat“, „Obnovit“, „Maximalizovat“ a „Zavřít“
- Tlačítka „OK“, „Storno“, „Přerušit“, „Opakovat“, „Pokračovat“, „Další“, „Předchozí“, „Zpět“, „Dokončit“ a „Nyní ne“
- A tlačítka „Ano“ a „Ne“.

#### **Při sledování okna v popředí ignorovat prvek pod fokusem** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Tato možnost je dostupná, pouze pokud je zaškrtnuto [Sledovat i cíle v popředí](#sledovat-i-cíle-v-popředí-zaškrtávací-políčko-ve-výchozím-nastavení-nezaškrtnuto), protože se projeví jen u okna, které se čte ve chvíli, kdy v něm právě pracujete. Oken na pozadí ani cílů, které sledují jednotlivé prvky, se tak či tak netýká.

Pokud je povolena, prvek, který má právě fokus, se nikdy neoznámí jako změna, takže se vám například znaky, které píšete do editačního pole, nebudou hlásit jako nový obsah.

### **Při změně cíle** (skupina)

Co se stane, když se ve sledovaném cíli objeví nový obsah.

#### **Pípnout** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Přehraje tón, když se cíl změní.

#### **Oznámit** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Oznámí, co se kde změnilo, například „Okno: Claude“ nebo „Seznam: Seznam zpráv“. Úroveň podrobnosti oznámení lze dále upravit níže.

#### **Při oznamování nové změny přerušit předchozí řeč** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Tato možnost je dostupná, pouze pokud je zaškrtnuto výše uvedené políčko [**Oznámit**](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto). Pokud je povolena, oznámení o změně přeruší stávající promluvu NVDA a přečte se ihned. Pokud je zakázána, oznámení o změně počká, až NVDA domluví.

#### **Při po sobě jdoucích změnách ve stejném cíli zopakovat jeho název** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Tato možnost je dostupná, pouze pokud je zapnuto [slovní oznamování jako takové](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto). Pokud je povolena, název cíle zazní v každém oznámení změny, i když v tomtéž cíli došlo k několika změnám po sobě. Pokud je zakázána, název cíle se oznámí jen u první změny ve stejném cíli.

### **Parametry pípnutí** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko [**Pípnout**](#pípnout-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto).

#### **Délka** (editační pole, ve výchozím nastavení 50)

Lze zapsat pouze celá čísla. Nastavuje, jak dlouho má pípnutí trvat, v milisekundách.

#### **Výška** (editační pole, ve výchozím nastavení 440)

Lze zapsat pouze celá čísla. Nastavuje, s jakou frekvencí se má pípnutí přehrávat, v hertzech.

#### **Otestovat** (tlačítko)

Přehraje testovací pípnutí s aktuálně nastavenými parametry, abyste si mohli ověřit, jestli zní tak, jak chcete.

### **Do oznámení o změně zahrnout** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko [**Oznámit**](#oznámit-zaškrtávací-políčko-ve-výchozím-nastavení-zaškrtnuto). Určují, z čeho přesně se oznámení o změně skládá.

#### **Typ cíle** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli oznamovat typ (roli) cíle (například **okno**, **seznam** nebo **editační pole**).

#### **Změněný obsah** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli oznamovat nový obsah v cíli po poslední změně.

### **Do popisů v nabídce zahrnout** (skupina)

Možnosti v této skupině určují, jak budou vypadat popisky položek v [nabídce cílů](#nabídka-cílů). Ovlivňují také, jak se zapisují položky do [historie změn](#historie-nedávných-změn) jednotlivých cílů.

#### **Typ cíle** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v textu příslušné položky daného cíle zobrazovat typ (roli) cíle (například **okno**, **seznam** nebo **editační pole**).

#### **Čas od poslední změny** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v textu příslušné položky daného cíle zobrazovat relativní čas od poslední změny (například před 3 minutami).

#### **Změněný obsah** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v textu příslušné položky daného cíle zobrazovat nový obsah po poslední změně.

## Známá omezení (potřebuje přepsat)

- **Panely prohlížečů na pozadí nelze sledovat.** Webové prohlížeče udržují čitelný pouze ten panel, na který se právě díváte. Pokud chcete některou stránku sledovat, zatímco pracujete jinde, otevřete si ji ve vlastním okně místo v panelu na pozadí. Vidící uživatelé panel na pozadí také nevidí.
- **Některé aplikace toho na pozadí zobrazují jen velmi málo.** Kolik toho aplikace prozradí odečítači obrazovky o obsahu, na kterém není fokus, řídí výhradně ona sama. Moderní aplikace postavené na technologii UIA – Terminál, Nastavení, Kalkulačka, Fotky a většina aplikací z Microsoft Storu – a aplikace vykreslované jako webová stránka – desktopové aplikace Claude a ChatGPT, nový Outlook, Visual Studio Code, Discord, Slack, Signal, WhatsApp pro Windows, Spotify i skutečné webové stránky – se v tomto ohledu značně liší. Pokud aplikace nový obsah nezpřístupňuje jako text, doplněk ho oznámit nedokáže.
- **Počítá se jen to, co se v okně právě zobrazuje.** Dlouhé seznamy – historie chatu, seznamy souborů, výsledky hledání – existují obvykle jen jako těch několik řádků, které jsou zrovna zobrazeny. Doplněk nevidí položky odrolované mimo obrazovku, stejně jako je nevidí vidící uživatelé, a minimalizované okno může přestat svůj obsah zobrazovat úplně, dokud ho neobnovíte – podle toho, jak je daná aplikace naprogramovaná.

Pokud často potřebujete vědět o aktualizacích z aplikace, kterou používáte na pozadí, bývá obvykle spolehlivější a jednodušší nastavit samotnou aplikaci tak, aby vám posílala oznámení, pokud to daná aplikace umožňuje. Také když aplikaci minimalizujete do systémové lišty, přestane zobrazovat viditelné okno, takže ji doplněk už nemůže sledovat. Pokud ale ikona na systémové liště zobrazuje užitečné informace ve formě textu, můžete sledovat přímo tuto ikonu.

## Spolupráce

Pokud byste chtěli přispět k vývoji doplňku – ať už překladem, hlášením chyb nebo vytvořením pull requestu – a víte, jak na to, můžete to udělat v jeho [repozitáři na GitHubu](https://github.com/4sensegaming/background-content-tracker). Veškerou pomoc vítám a vážím si jí.

## Historie změn

### Verze 1.0, 18. října 2026
* První verze