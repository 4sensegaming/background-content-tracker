# Sledování obsahu na pozadí

* Autor: Lukáš Hosnedl
* Minimální verze NVDA: 2026.1
* Poslední testovaná verze NVDA: 2026.2

**Vytvořeno umělou inteligencí, navrženo a důkladně otestováno lidmi.**

## Popis

Doplněk Sledování obsahu na pozadí sleduje okno nebo jednotlivý prvek, který právě **není** pod fokusem ani v popředí, a dá vám vědět, jakmile se v něm objeví nový obsah. Můžete tak dál pracovat v jednom okně, zatímco doplněk hlídá jiné a upozorní vás ve chvíli, kdy se tam něco změní.

Když vidící lidé pracují v jednom okně, okamžitě zachytí koutkem oka, že ve vedlejším okně něco vyskočilo nebo se změnilo, a dokážou odhadnout, jestli to vyžaduje pozornost hned, nebo až za chvíli. NVDA umí oznamovat upozornění a živé regiony, ale obvykle jen ve chvíli, kdy je dané okno v popředí, takže změny, ke kterým došlo, zatímco jste pracovali jinde, vám mohou snadno uniknout.

Sledování obsahu na pozadí vám dává přesně tento přehled: Vyberete si, co se má sledovat a jak chcete být upozorněni, a NVDA vás na změnu obsahu upozorní, aniž byste museli opustit to, co právě děláte.

Tento doplněk je velmi mocný a přizpůsobitelný nástroj, který dokáže z nepřístupné aplikace podle potřeby udělat mluvící živý region. Překvapivě dobře si rozumí s:

- Terminály,
- Krátkými, rychle se měnícími dynamickými zprávami v jediném seznamu, textové oblasti nebo objektu NVDA,
- A také s velkými okny aplikací postavených na Electronu, jako je Claude, které toho po stránce přístupnosti hodně dluží: Dokážou dlouho mlčet a pak najednou začnou rychle za sebou chrlit spoustu velkých kusů nového textu, které by se jinak hledaly jen těžko.

Doplněk ale nejspíš ocení jen pokročilí uživatelé, kteří potřebují zrychlit a zefektivnit svou práci, například:

- Vývojáři pracující v týmu,
- Ti, kdo běžně používají placené služby AI nebo lokální modely k tvorbě něčeho rozsáhlejšího,
- Nebo ti, kdo pracují v částečně či plně automatizovaných firemních procesech, v nichž běží několik úloh naráz.

Pokud ho potřebujete, poznáte to nejspíš hned po přečtení předchozího popisu. Ostatní se při jeho používání možná budou cítit spíš zahlceni nebo zmateni.

## Použití

Vytvoříte si seznam cílů ke sledování – celá okna, nebo jednotlivé prvky, jako je editační pole či seznam zpráv v chatu – a doplněk vás upozorní pokaždé, když se v některém z nich objeví nový obsah. Můžete sledovat více cílů najednou a každý z nich zapínat a vypínat samostatně.

### Příklady použití:

- **Čekání na dlouhou úlohu v jiné aplikaci.** Zadáte úkol AI asistentovi, například Claude, a místo abyste čekali v jeho okně, přepnete se jinam a věnujete se něčemu jinému. Doplněk sleduje okno asistenta a dá vám vědět, jakmile se objeví nový výstup, takže poznáte, že odpověděl, aniž byste se museli znovu a znovu vracet a kontrolovat to.
- **Sledování webové stránky, zatímco píšete jinde.** Píšete v chatu, například ve WhatsAppu, zatímco vedle máte otevřenou webovou stránku. Když se tato stránka na pozadí aktualizuje, doplněk vám to oznámí – takže si toho všimnete stejně, jako by se vidící člověk podíval vedle.

### Typický postup:

1. Přejděte na okno nebo prvek, který chcete sledovat: Přesuňte na něj **fokus**, najeďte na něj **myší**, nebo na něj přesuňte **objektovou navigaci** či prohlížecí kurzor.
2. Začněte ho sledovat – buď příslušnou [klávesovou zkratkou](#klávesové-příkazy), nebo výběrem z [nabídky cílů](#nabídka-cílů).
3. Přepněte se na to, čemu se chcete věnovat. Když se ve sledovaném cíli objeví nový obsah, NVDA vás upozorní tak, jak jste si [nastavili](#nastavení) – pípnutím, názvem cíle nebo změněným obsahem.
4. Až daný cíl nebudete potřebovat, přestaňte ho sledovat, nebo vymažte celý seznam cílů najednou.

## Klávesové příkazy

Doplněk se ovládá jediným **vrstveným příkazem**: Stisknete klávesovou zkratku, uvolníte ji a poté stisknete ještě jednu klávesu, kterou zvolíte požadovanou akci. Po stisku samotné hlavní klávesové zkratky se nic nestane, takže příkazy doplňku nikdy nekolidují s NVDA ani jinými aplikacemi.

Výchozí klávesová zkratka je NVDA+; (středník – na české klávesnici klávesa nalevo od číslice 1).

Po stisku hlavní klávesové zkratky doplněk otevře **virtuální překrytí** a oznámí „Překrytí otevřeno“, a pokud je sledování právě pozastaveno, pak i „Sledování pozastaveno“. Dokud je překrytí otevřené, považuje se každý stisk klávesy za jeden z níže uvedených příkazů. Otevření ani zavření překrytí nepřesouvá fokus – ten zůstává přesně tam, kde byl, takže příkazy doplňku nikdy nenaruší to, co právě děláte. Kdykoli se překrytí zavře, doplněk oznámí „Překrytí zavřeno“.

Po stisku hlavní klávesové zkratky stiskněte jednu z následujících kláves:

- `H` – **nápověda**: Přečte každou klávesu dostupnou v překrytí a stručně vysvětlí, k čemu slouží. Dvojím stiskem této klávesy zobrazíte zprávu s nápovědou v dialogovém okně pro pohodlnější čtení.
- `W` – začne nebo přestane sledovat aktuální **okno** (jakoukoli změnu v celém okně v popředí).
- `F` – začne nebo přestane sledovat prvek, který má právě **fokus** klávesnice.
- `M` – začne nebo přestane sledovat prvek pod ukazatelem **myši**.
- `N` – začne nebo přestane sledovat aktuální **prohlížený objekt** (tam, kde je prohlížecí kurzor).
- `T` – otevře **[nabídku cílů](#nabídka-cílů)**.
- `1` až `0` – **oznámí informace o cíli** podle jeho pořadí v seznamu (viz níže). Dalším stiskem téhož čísla se na daný cíl přesune fokus.
- `Mezerník` nebo `enter` – totéž jako číselné zkratky, ale vždy pro **naposledy přidaný** cíl: Prvním stiskem si o něm necháte oznámit informace, druhým se na něj přesune fokus.
- `Control`+číslo (`1` až `0`) – **přestane sledovat** cíl v daném slotu.
- `Backspace` – **přestane sledovat poslední přidaný** cíl.
- `Delete` – **přestane sledovat všechny cíle** (vymaže celý seznam najednou).
- `P` – **pozastaví nebo obnoví** veškeré sledování (přepíná přepínač *Povolit sledování*, popsaný v části [Nastavení](#nastavení)).
- `S` – otevře **[nastavení](#nastavení)** doplňku (týž panel jako nabídka NVDA → Možnosti → Nastavení → Sledování obsahu na pozadí).
- `I` – otevře dialog **Klávesové příkazy** NVDA, kde můžete hlavní klávesovou zkratku přenastavit, aniž byste ji museli hledat v nabídkách.
- `Escape` – **zavře překrytí**, aniž by udělal cokoli jiného.

Příkazy pro okno, fokus, myš a prohlížený objekt fungují jako přepínače: Prvním stisknutím daný cíl přidáte do seznamu, dalším stisknutím ho odeberete. Sledovat můžete libovolný počet cílů současně.

Tyto čtyři příkazy přijímají i klávesy `shift` a `control`, které určují, jak se má přidávaný cíl sledovat: `shift` si tento jeden cíl zapamatuje, `control` ho nechá číst i ve chvíli, kdy je jeho aplikace v popředí, a s oběma klávesami najednou platí obojí. Jde o [nastavení pro jednotlivý cíl](#globální-nastavení-a-nastavení-pro-jednotlivý-cíl), zadaná přímo tomuto cíli při jeho přidání místo toho, aby se převzala z globálního [nastavení](#nastavení) nebo se zadala dodatečně v [nabídce cílů](#nabídka-cílů); globálním nastavením nepohnou. Stisk, který sledování *ukončuje*, tyto klávesy prostě ignoruje.

Číselné zkratky odkazují na **sloty** v seznamu cílů, nikoli na pevně dané cíle. Ve výchozím nastavení je `1` naposledy přidaný cíl, `2` ten přidaný před ním a tak dál až po `0` – desátý slot. [Nastavení **Řazení cílů**](#nastavení) může sloty seřadit jinak, třeba od nejstaršího cíle, od naposledy změněného cíle nebo abecedně. Když některý cíl zmizí – protože jste ho přestali sledovat, nebo přestal existovat – cíle za ním se posunou a mezeru zaplní, takže číslo `2` vždy oznámí ten cíl, který je právě teď v seznamu jako druhý. Pokud ve slotu, jehož číslo jste stiskli, není žádný platný cíl, doplněk řekne například „Žádný cíl ve slotu 2“ (nebo „název cíle nenalezeno“ u dříve zapamatovaného cíle).

Pokud cíl existuje, doplněk ve výchozím nastavení oznámí jeho roli a název a změněný obsah cíle, například *Okno: Claude, Editing readme.md* nebo *Seznam: Seznam zpráv, Řekli jste: Tak jo.*. Úroveň podrobnosti těchto oznámení lze upravit v [nastavení](#nastavení) doplňku.

Hlavní klávesovou zkratku můžete změnit v dialogu Klávesové příkazy (nabídka NVDA → Možnosti → Klávesové příkazy), kde se příkaz doplňku nachází v kategorii **Sledování obsahu na pozadí**. Následné klávesy jsou součástí samotného vrstveného příkazu.

## Nabídka cílů

**Nabídka cílů** (hlavní klávesová zkratka následovaná klávesou `t`) zobrazuje všechny aktuální cíle jako seřazené položky nabídky, takže si nemusíte pamatovat aktuální pořadí cíle v seznamu ani žádnou z ostatních kláves.

Každá položka přesně pojmenovává, čeho se týká, například *Okno: Claude, před 3 minutami, 3 tasks running*. Cíl, který právě neexistuje – třeba zapamatovaný cíl, jehož okno ještě není znovu otevřené –, místo času a obsahu uvádí *nenalezeno* a v nabídce zůstává, protože ho pořád můžete přestat sledovat, změnit jeho nastavení, nebo ho nechat být a počkat, až se zase objeví. Pořadí, ve kterém jsou cíle vypsány, respektuje [nastavení **Řazení cílů**](#nastavení).

Každý cíl je podnabídkou. Když ji rozbalíte, můžete cíl *Přestat sledovat*, *Přesunout fokus* na něj, nebo změnit jeho *Nastavení cíle* v podnabídce, která obsahuje vlastní kopii těch nastavení, jež lze [zadat pro jednotlivý cíl](#globální-nastavení-a-nastavení-pro-jednotlivý-cíl).

Každá položka v *Nastavení cíle* je zaškrtávací políčko a ukazuje to, co cíl skutečně dělá: Jeho vlastní hodnotu tam, kde jste mu ji zadali, a jinde globální nastavení. Zaškrtnutím nebo odškrtnutím dáte cíli vlastní hodnotu právě pro toto jedno nastavení, a to okamžitě; všechna ostatní nastavení dál sledují globální hodnotu.

- *Při oznamování nové změny přerušit předchozí řeč* se zobrazuje na začátku *Nastavení cíle* u všech cílů, pokud je zapnuta globální možnost *Oznámit*.
- Dále následují u cílů, které jsou oknem, možnosti *Ignorovat indikátory průběhu*, *Ignorovat počítadla, krokovače a časovače*, *Považovat změnu názvu za zmizení cíle* a *Ignorovat známé generické prvky*.
- Pak následuje *Sledovat tento cíl i v popředí*, zobrazené u všech cílů.
- Za ním je *Ignorovat prvek pod fokusem*, pokud je cíl oknem a zároveň je u něj nastaveno, že se má sledovat i v popředí.
- *Pamatovat si tento cíl* se zobrazuje u všech cílů.
- *Zapomenout tento cíl, když přestane existovat* se zobrazuje jen u cíle, který si doplněk pamatuje.

Vše, co už sledujete, se v nabídce zobrazí jako první, takže se na daný cíl můžete rychle přesunout nebo ho přestat sledovat. Dále se zobrazí cíle, které můžete začít sledovat ze své aktuální pozice (okno, fokus, ukazatel myši nebo prohlížený objekt). Položka pro ukončení sledování všech aktuálních cílů je na konci nabídky.

## Důležité zprávy doplňku

- **Zahájení sledování nového cíle** – například „Sleduji okno: Claude“. Totéž uslyšíte pokaždé, když se zapamatovaný cíl znovu objeví později, po spuštění.
- **Ukončení sledování cíle** – například „Přestávám sledovat seznam: Seznam zpráv“. Uslyšíte to, když cíl přestanete sledovat sami, a také když cíl přestane existovat a doplněk ho proto přestane sledovat: Vždy u cíle, který si nepamatuje, a u zapamatovaného tehdy, když je u něj nastaveno, že se má při zmizení zapomenout.
- **Zmizení cíle** – například „Cíl zmizel: Claude“. Uslyšíte to, když zapamatovaný cíl zmizí, ale zůstane v seznamu, takže se začne sledovat znovu, jakmile se zase objeví.

Ani jedna z těchto zpráv se neoznámí u cíle, který zmizí, zatímco je v popředí, například když jeho okno sami zavřete. Jedinou výjimkou je zapamatovaný cíl, u kterého je nastaveno, že se má při zmizení zapomenout: V tom případě „Přestávám sledovat název cíle“ uslyšíte, protože jeho zavřením se zároveň přestane sledovat i napříště, což jste možná nezamýšleli.

Při spuštění NVDA a pokaždé, když obnovíte dříve pozastavené sledování, doplněk zapamatované cíle vyhledá a oznámí najednou, jako „Nalezeno 7 zapamatovaných cílů“, nebo „Nalezeno 6 z 9 zapamatovaných cílů“, pokud se zbývající zatím neobjevily. Když jich je nalezeno méně než pět, následují jejich názvy, například „Nalezeny 3 zapamatované cíle: Claude, ChatGPT Classic, Gemini“ nebo „Nalezeno 1 z 3 zapamatovaných cílů: Claude“. Ty, které se objeví později, se ohlásí jednotlivě. Pokud tam právě žádný ze zapamatovaných cílů není, doplněk místo toho oznámí „Žádné zapamatované cíle nenalezeny“.

## Globální nastavení a nastavení pro jednotlivý cíl

Většina možností doplňku je **globálních**: Zadáte je v [nastavení](#nastavení) a řídí se jimi každý cíl. Devět z nich lze navíc zadat pro **jednotlivý cíl** v [nabídce cílů](#nabídka-cílů); takový cíl se pak v tomto jednom nastavení řídí vlastní hodnotou a ve všech ostatních dál sleduje globální:

- *Při oznamování nové změny přerušit předchozí řeč*
- *Ignorovat indikátory průběhu*
- *Ignorovat počítadla, krokovače a časovače*
- *Považovat změnu názvu za zmizení cíle*
- *Ignorovat známé generické prvky*
- *Sledovat tento cíl i v popředí*
- *Ignorovat prvek pod fokusem*
- *Pamatovat si tento cíl*
- *Zapomenout tento cíl, když přestane existovat*

Vlastní hodnotu lze jednomu cíli zadat dvěma způsoby. Buď v [nabídce cílů](#nabídka-cílů) rozbalíte u daného cíle podnabídku *Nastavení cíle* a zaškrtnete či odškrtnete, co potřebujete. Nebo při přidání cíle [klávesami `w`, `f`, `m` či `n`](#klávesové-příkazy) podržíte `shift`, `control` nebo obojí, čímž přidávanému cíli zadáte vlastní *Pamatovat si tento cíl*, respektive *Sledovat tento cíl i v popředí*.

Změna nastavení se projeví i u existujících cílů, pokud toto nastavení nebylo u cíle zadáno zvlášť. Panel nastavení zadává výhradně globální hodnoty: Nic, co v něm uděláte, cíli jeho vlastní hodnotu nevezme. Všechny vlastní hodnoty vymaže až to, že cíl přestanete sledovat a přidáte ho znovu, nebo že zapamatovaný cíl zapomenete.

## Nastavení

Nastavení doplňku najdete v kategorii **Sledování obsahu na pozadí** v dialogu Nastavení NVDA (nabídka NVDA → Možnosti → Nastavení). Doplněk podporuje více konfiguračních profilů.

Související možnosti jsou uspořádány do skupin. Všechny dostupné možnosti jsou popsány níže v pořadí, v jakém se v dialogu zobrazují. Možnosti na nejvyšší úrovni a celé skupiny jsou nadpisy úrovně 3, jednotlivé možnosti uvnitř skupin jsou nadpisy úrovně 4.

### **Povolit sledování** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud není zaškrtnuto, doplněk vás přestane upozorňovat, ale zachová celý seznam cílů i všechna nastavení, takže ho můžete umlčet (třeba během schůzky) a později zase zapnout přesně v tom stavu, v jakém byl. Jde o stejný přepínač, který přepíná [klávesa pro pozastavení a obnovení](#klávesové-příkazy).

### **Při změně cíle** (skupina)

Co se stane, když se ve sledovaném cíli objeví nový obsah.

#### **Pípnout** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Přehraje tón, když se cíl změní.

#### **Oznámit** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Oznámí, co se kde změnilo, například „Okno: Claude“ nebo „Seznam: Seznam zpráv“. Úroveň podrobnosti oznámení lze dále upravit níže.

#### **Při oznamování nové změny přerušit předchozí řeč** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Tato možnost je dostupná, pouze pokud je zaškrtnuto výše uvedené políčko **Oznámit**. Pokud je zaškrtnuta, oznámení o změně přeruší to, co NVDA právě říká, a přečte se ihned. Pokud zaškrtnuta není, počká, až NVDA domluví.

#### **Interval sledování** (editační pole, ve výchozím nastavení 1)

Lze zapsat pouze celá čísla. Nastavuje, jak často má doplněk kontrolovat změny ve všech existujících cílech, v sekundách. 0 znamená nikdy neoznamovat změny cílů automaticky, pouze je zobrazovat v [nabídce cílů](#nabídka-cílů).

#### **Kolik změn oznámit najednou (jen cíle na pozadí)** (editační pole, ve výchozím nastavení 5)

Lze zapsat pouze celá čísla. Nastavuje, kolik po sobě jdoucích změn stejného cíle má doplněk oznámit v řadě, než budete muset cíl znovu fokusovat a poté se opět přepnout jinam, aby se zase začaly oznamovat následující změny. 0 znamená oznámit každou jednotlivou změnu pokaždé. Cílů v popředí se tato možnost nikdy netýká. Pokud je zapnuto sledování i pro cíle v popředí, oznamují se u nich vždy všechny změny.

#### **Sledovat i cíle v popředí** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Běžně se cíl čte jen ve chvíli, kdy pracujete někde jinde: Jakmile se jeho aplikace dostane do popředí, doplněk ji nechává být. Pokud je zaškrtnuto, nový obsah cíle se oznamuje i tehdy, když právě pracujete s tímto oknem nebo jednotlivým prvkem, bez ohledu na hodnotu výše uvedené možnosti.

### **Chování při sledování oken** (skupina)

Možnosti v této skupině upřesňují, jak má doplněk oznamovat změny v cílech, které jsou celými okny.

#### **Ignorovat indikátory průběhu** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, tato možnost potlačí oznamování měnících se indikátorů průběhu v okně. Samotné NVDA umí ohlašovat nativní indikátory průběhu slovně anebo pípáním, i na pozadí, takže nemusí být vždy žádoucí, aby vás tento doplněk zahlcoval dvojím hlášením neustále se měnícího indikátoru průběhu v konkrétní aplikaci.

#### **Ignorovat počítadla, krokovače a časovače** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, doplněk sleduje, jestli se u některého prvku nemění nic jiného než čísla – časovač nebo odpočet tikající každou sekundu, počítadlo kroků či položek, procenta, jako třeba aplikace Claude počítající, jak dlouho modelu trvalo přemýšlení. Tyto prvky bývají často spíše na obtíž než k užitku, protože samy o sobě neposkytují žádnou užitečnou informaci a hlavně nevypovídají o žádné skutečné změně – jen naznačují, že úloha stále běží. Jakmile doplněk takový prvek přistihne, umlčí ho a mlčí o něm po celou dobu, kdy je cíl sledován.

#### **Považovat změnu názvu za zmizení cíle** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Pokud je zaškrtnuto a změní se název okna, které sledujete, doplněk ho začne považovat za jiné okno a tedy se zachová stejně, jako by původní cíl zmizel, přestože fyzické okno v systému je pořád stejné.

#### **Ignorovat známé generické prvky** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Pokud je zaškrtnuto, tato možnost potlačí oznamování generických prvků, jako když se tlačítko „Minimalizovat“ změní na „Maximalizovat“ a naopak. Patří sem:

- Nabídka aplikace (obvykle se otevírá klávesou alt)
- Tlačítka „Minimalizovat“, „Obnovit“, „Maximalizovat“ a „Zavřít“
- Tlačítka „OK“, „Storno“, „Zavřít“, „Přerušit“, „Opakovat“, „Pokračovat“, „Další“, „Předchozí“, „Zpět“, „Dokončit“ a „Teď ne“
- A tlačítka „Ano“ a „Ne“.

#### **Při sledování okna v popředí ignorovat prvek pod fokusem** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Tato volba se projeví pouze u okna, které se čte i ve chvíli, kdy v něm pracujete, což umožňuje nastavení sledování cílů i v popředí. Jinými slovy se tato možnost týká jen celého okna, u kterého je zároveň nastaveno, že se má číst i v popředí. Oken na pozadí ani cílů, které jsou jednotlivým prvkem, se tak či tak netýká. Pokud je zaškrtnuta, prvek, na kterém máte fokus, se nikdy neoznámí jako změna, takže se vám například znaky, které píšete do editačního pole, nečtou zpátky jako nový obsah.

### **Parametry pípnutí** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko **Pípnout**.

#### **Délka** (editační pole, ve výchozím nastavení 50)

Lze zapsat pouze celá čísla. Nastavuje, jak dlouho má pípnutí trvat, v milisekundách.

#### **Výška** (editační pole, ve výchozím nastavení 440)

Lze zapsat pouze celá čísla. Nastavuje, s jakou frekvencí se má pípnutí přehrávat, v hertzech.

#### **Otestovat** (tlačítko)

Přehraje testovací pípnutí s aktuálně nastavenými parametry, abyste si mohli ověřit, jestli zní tak, jak chcete.

### **Do oznámení o změně zahrnout** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko **Oznámit**. Určují, z čeho přesně se oznámení o změně cíle skládá.

Dokud je zapnuto slovní oznamování jako takové, název cíle (například Claude nebo Seznam zpráv) je zahrnut vždy – kromě případů, kdy se týž cíl mění velmi rychle a mezitím se nezmění žádný jiný cíl, jako u postupně rostoucí odpovědi chatbota. Tehdy se název cíle vynechá, abyste odpověď vnímali přirozeně, zdánlivě jako jedinou souvislou promluvu, a ne rozsekanou na kusy neustále se opakujícím názvem aplikace.

#### **Typ cíle** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli oznamovat typ cíle (například **okno**, **seznam** nebo **editační pole**).

#### **Změněný obsah** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli oznamovat nový obsah v cíli po poslední změně.

### **Do popisů v nabídce zahrnout** (skupina)

Možnosti v této skupině určují úroveň podrobnosti, kterou chcete slyšet při procházení [nabídky cílů](#nabídka-cílů).

#### **Typ cíle** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v popisu příslušné položky pro daný cíl zobrazovat typ cíle (například **okno**, **seznam** nebo **editační pole**).

#### **Čas od poslední změny** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v popisu příslušné položky pro daný cíl zobrazovat relativní čas od poslední změny (například před 3 minutami).

#### **Změněný obsah** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Jestli v popisu příslušné položky pro daný cíl zobrazovat nový obsah po poslední změně.

### **Čas do zavření překrytí** (editační pole, ve výchozím nastavení 10)

Lze zapsat pouze celá čísla. Určuje, kolik sekund bez stisku klávesy musí uplynout, než se překrytí samo zavře. Při hodnotě 0 se překrytí samo nezavře nikdy: Zůstane otevřené, dokud ho nezavřete klávesou escape nebo příkazem, který přesune fokus jinam.

### Řazení cílů

Jsou tu dvě sady přepínačů, jedna za druhou: *Řazení cílů ve slotech* a *Řazení cílů v nabídce*. Obě nabízejí stejné možnosti uvedené níže a u obou lze mít zvolenou vždy právě jednu z nich, buď shodně, nebo nezávisle na sobě. Určují, v jakém pořadí se nové cíle umisťují do deseti dostupných číslovaných slotů (viz [Klávesové příkazy](#klávesové-příkazy)), respektive zobrazují v [nabídce cílů](#nabídka-cílů).

- *Nejnovější cíl první* (výchozí nastavení u obou řazení)
- *Nejstarší cíl první*
- *Naposledy změněný cíl první*
- *Nejdéle nezměněný cíl první*
- *Abecedně, A až Z*
- *Abecedně, Z až A*

### **Pamatovat si cíle** (zaškrtávací políčko, ve výchozím nastavení nezaškrtnuto)

Pokud je zaškrtnuto, seznam cílů zůstane zachován i po restartu NVDA a doplněk se k cíli znovu připojí pokaždé, když se cíl znovu objeví. Sleduje tak například okno asistenta při každém jeho otevření, aniž byste to museli znovu nastavovat. Pokud zaškrtnuto není, začíná seznam cílů při každém spuštění prázdný a ukládají se pouze vaše nastavení.

### **Zapomínat zapamatované cíle, když přestanou existovat** (zaškrtávací políčko, ve výchozím nastavení zaškrtnuto)

Určuje, jestli se má zapamatovaný cíl zapomenout, jakmile přestane existovat (zavřete okno nebo konkrétní prvek z okna zmizí). Pokud je zaškrtnuto, budete muset začít týž cíl sledovat znovu ručně pokaždé, když zmizí, zatímco ho doplněk sleduje. Cíle, které přestanete sledovat ručně, se zapomínají vždy, ať je tato možnost nastavena jakkoli.

## Známá omezení

- **Panely prohlížečů na pozadí nelze sledovat.** Webové prohlížeče udržují čitelný pouze ten panel, na který se právě díváte. Pokud chcete některou stránku sledovat, zatímco pracujete jinde, otevřete si ji ve vlastním okně místo v panelu na pozadí. Toto je stejné i pro vidící uživatele.
- **Některé aplikace toho na pozadí zobrazují jen velmi málo.** Kolik toho aplikace prozradí odečítači obrazovky o obsahu, na kterém není fokus, řídí výhradně ona sama. Moderní aplikace postavené na technologii UIA – Terminál, Nastavení, Kalkulačka, Pošta, Fotky a většina programů z Microsoft Storu – a aplikace vykreslované jako webová stránka – desktopová aplikace Claude, Visual Studio Code, Discord, Slack, Signal, WhatsApp pro Windows, Spotify i samotné webové prohlížeče – se v tomto ohledu značně liší. Pokud aplikace nový obsah nezobrazuje jako viditelný text, doplněk ho oznámit nedokáže.
- **Počítá se jen to, co se v okně právě zobrazuje.** Dlouhé seznamy – historie chatu, seznamy souborů, výsledky hledání – existují obvykle jen jako těch několik řádků, které jsou zrovna zobrazeny. Doplněk nevidí položky odrolované mimo obrazovku, stejně jako je nevidí vidící uživatelé, a minimalizované okno může přestat svůj obsah zobrazovat úplně, dokud ho neobnovíte – podle toho, jak je daná aplikace naprogramovaná.

Pokud často potřebujete vědět o aktualizacích z aplikace, kterou používáte na pozadí, bývá obvykle spolehlivější a jednodušší nastavit samotnou aplikaci tak, aby vám posílala oznámení, pokud to daná aplikace umožňuje. Stejně tak když aplikaci minimalizujete do systémové lišty, přestane zobrazovat viditelné okno, takže ji doplněk už nemůže sledovat. Pokud ale ikona na systémové liště prezentuje užitečné informace jako přístupné textové aktualizace, můžete sledovat přímo tuto ikonu.

## Spolupráce

Pokud byste chtěli přispět k vývoji doplňku – ať už překladem, hlášením chyb nebo vytvořením pull requestu – a víte, jak na to, můžete tak učinit v jeho [repozitáři na GitHubu](https://github.com/4sensegaming/background-content-tracker). Veškerou pomoc vítám a vážím si jí.

## Historie změn

### Verze 1.0, 12. září 2026
* První verze