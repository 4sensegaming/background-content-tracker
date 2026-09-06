# Sledování obsahu na pozadí

* Autor: Lukáš Hosnedl
* Minimální verze NVDA: 2026.1
* Poslední testovaná verze NVDA: 2027.1

**Vytvořeno umělou inteligencí, navrženo a důkladně otestováno lidmi.**

## Popis

Doplněk Sledování obsahu na pozadí sleduje okno nebo jednotlivý prvek, na kterém právě **nemáte** fokus, a dá vám vědět, jakmile se v něm objeví nový obsah. Můžete tak dál pracovat v jednom okně, zatímco doplněk hlídá jiné a upozorní vás ve chvíli, kdy se tam něco změní.

Když vidící lidé pracují v jednom okně, okamžitě zachytí koutkem oka, že ve vedlejším okně něco vyskočilo nebo se změnilo, a dokážou odhadnout, jestli to vyžaduje pozornost hned, nebo až za chvíli. NVDA umí oznamovat upozornění a živé regiony, ale jen ve chvíli, kdy je dané okno v popředí, takže změny, ke kterým došlo, zatímco jste pracovali jinde, vám mohou snadno uniknout.

Sledování obsahu na pozadí vám dává přesně tento přehled: vyberete si, co se má sledovat a jak chcete být upozorněni, a NVDA vás na změnu obsahu upozorní, aniž byste museli přesouvat fokus od toho, co právě děláte.

## Použití

Vytvoříte si seznam cílů ke sledování – celá okna, nebo jednotlivé prvky, jako je editační pole či seznam zpráv v chatu – a doplněk vás upozorní pokaždé, když se v některém z nich objeví nový obsah. Můžete sledovat více cílů najednou a každý z nich zapínat a vypínat samostatně.

### Příklady použití:

- **Čekání na dlouhou úlohu v jiné aplikaci.** Zadáte úkol AI asistentovi, například Claude, a místo abyste čekali v jeho okně, přepnete se jinam a věnujete se něčemu jinému. Doplněk sleduje okno asistenta a dá vám vědět, jakmile se objeví nový výstup, takže poznáte, že odpověděl, aniž byste se museli znovu a znovu vracet a kontrolovat to.
- **Sledování webové stránky, zatímco píšete jinde.** Píšete v chatu, například ve WhatsAppu, zatímco vedle máte otevřenou webovou stránku. Když se tato stránka na pozadí aktualizuje, doplněk vám to oznámí – takže si toho všimnete stejně, jako by se vidící člověk podíval vedle.

### Typický postup:

1. Přejděte na okno nebo prvek, který chcete sledovat: přesuňte na něj **fokus**, najeďte na něj **myší**, nebo na něj přesuňte **objektovou navigaci** či prohlížecí kurzor.
2. Začněte ho sledovat – buď příslušnou [klávesovou zkratkou](#klávesové-příkazy), nebo výběrem z [nabídky cílů](#nabídka-cílů).
3. Přepněte se na to, čemu se chcete věnovat. Když se ve sledovaném cíli objeví nový obsah, NVDA vás upozorní tak, jak jste si nastavili – pípnutím, názvem cíle nebo změněným obsahem.
4. Až daný cíl nebudete potřebovat, přestaňte ho sledovat, nebo vymažte celý seznam cílů najednou.

## Klávesové příkazy

Doplněk se ovládá jediným **vrstveným příkazem**: stisknete klávesovou zkratku, uvolníte ji a poté stisknete ještě jednu klávesu, kterou zvolíte požadovanou akci. Po stisku samotné hlavní klávesové zkratky se nic nestane, takže příkazy doplňku nikdy nekolidují s NVDA ani jinými aplikacemi.

Výchozí klávesová zkratka je NVDA+; (středník – na české klávesnici klávesa nalevo od číslice 1).

Po stisku hlavní klávesové zkratky doplněk otevře dočasné **virtuální překrytí** a oznámí „Sledování obsahu na pozadí, H pro nápovědu“. Dokud je překrytí otevřené, následující stisk klávesy se považuje za jeden z níže uvedených příkazů.

Překrytí se samo zavře, když deset sekund nic nestisknete (tuto prodlevu lze změnit v [nastavení doplňku](#nastavení)), a stisknutím libovolné klávesy, která *není* jedním z příkazů, ho zavřete okamžitě. Otevření ani zavření překrytí nikdy nepřesouvá fokus – ten vždy zůstává přesně tam, kde byl, takže příkazy doplňku nikdy nenaruší to, co právě děláte. Když se překrytí zavře automaticky nebo proto, že jste stiskli neplatnou klávesu, doplněk oznámí „Překrytí zavřeno“.

Po stisku hlavní klávesové zkratky stiskněte jednu z následujících kláves:

- `h` – **nápověda**: přečte každou klávesu dostupnou v překrytí a stručně vysvětlí, k čemu slouží. Dvojím stiskem této klávesy zobrazíte zprávu s nápovědou v dialogovém okně pro pohodlnější čtení.
- `w` – začne nebo přestane sledovat aktuální **okno** (jakoukoli změnu v celém okně v popředí).
- `f` – začne nebo přestane sledovat prvek, který má právě **fokus** klávesnice.
- `m` – začne nebo přestane sledovat prvek pod ukazatelem **myši**.
- `n` – začne nebo přestane sledovat aktuální objekt, který prohlížíte objektovou **navigací** (tam, kde je prohlížecí kurzor).
- `t` – otevře **[nabídku cílů](#nabídka-cílů)**.
- `1` až `0` – **oznámí informace o cíli** podle jeho pořadí v seznamu (viz níže). Stisknete-li totéž číslo podruhé do deseti sekund a mezitím nestisknete jinou klávesu, přesune se na daný cíl fokus.
- `mezerník` nebo `enter` – totéž jako číselné zkratky, ale vždy pro **naposledy přidaný** cíl: prvním stisknutím si o něm necháte oznámit informace, dalším stiskem do deseti sekund se na něj přesune fokus.
- `control`+číslo (`1` až `0`) – **přestane sledovat** cíl v daném slotu.
- `backspace` – **přestane sledovat poslední přidaný** cíl.
- `delete` – **přestane sledovat všechny cíle** (vymaže celý seznam najednou).
- `p` – **pozastaví nebo obnoví** veškeré sledování (přepíná přepínač *Povolit sledování obsahu na pozadí*, popsaný v části [Nastavení](#nastavení)).

Příkazy pro okno, fokus, myš a prohlížený objekt fungují jako přepínače: prvním stisknutím daný cíl přidáte do seznamu, dalším stisknutím ho odeberete. Sledovat můžete libovolný počet cílů současně.

Číselné zkratky odkazují na **pořadí** v seznamu cílů, nikoli na pevně dané cíle. Ve výchozím nastavení je `1` cíl, který jste začali sledovat jako první, a `0` (desátý slot) je cíl, který jste začali sledovat naposledy; toto pořadí lze obrátit v [nastavení](#nastavení). Když některý cíl zmizí – protože jste ho přestali sledovat, nebo přestal existovat – cíle za ním se posunou a mezeru zaplní, takže číslo `2` vždy oznámí ten cíl, který je právě teď v seznamu jako druhý. Pokud ve slotu, jehož číslo jste stiskli, není žádný platný cíl, doplněk řekne například „Žádný cíl ve slotu 2“.

Pokud cíl existuje, doplněk ve výchozím nastavení oznámí jeho roli a název a změněný obsah cíle, například *Okno: Claude, Editing readme.md* nebo *Seznam: Seznam zpráv, Řekli jste: Tak jo.*. Úroveň podrobnosti těchto oznámení lze upravit v [nastavení](#nastavení) doplňku.

Hlavní klávesovou zkratku můžete změnit v dialogu Klávesové příkazy (nabídka NVDA → Možnosti → Klávesové příkazy), kde se příkaz doplňku nachází v kategorii **Sledování obsahu na pozadí**. Následné klávesy jsou součástí samotného vrstveného příkazu.

## Nabídka cílů

**Nabídka cílů** (hlavní klávesová zkratka následovaná klávesou `t`) zobrazuje všechny aktuální cíle jako seřazené položky nabídky, takže si nemusíte pamatovat aktuální pořadí cíle v seznamu ani žádnou z ostatních kláves.

Každá položka přesně pojmenovává, čeho se týká, například *Okno: Claude, před 3 minutami, 3 tasks running*. Každý existující cíl je podnabídkou. Když ji rozbalíte, jsou k dispozici volby *Přestat sledovat* a *Přesunout fokus*. Pořadí, ve kterém jsou cíle vypsány, respektuje [nastavení **Řazení cílů**](#nastavení).

Vše, co už sledujete, se v nabídce zobrazí jako první, takže se na daný cíl můžete rychle přesunout nebo ho přestat sledovat. Dále se zobrazí cíle, které můžete začít sledovat ze své aktuální pozice (okno, fokus, ukazatel myši nebo prohlížený objekt). Položka pro ukončení sledování všech aktuálních cílů je na konci nabídky.

## Oznámení doplňku

Doplněk za chodu oznamuje několik neměnných zpráv:

- **Zahájení sledování nového cíle** – například „Sleduji okno: Claude“. Totéž uslyšíte pokaždé, když se zapamatovaný cíl znovu objeví.
- **Obnovení zapamatovaných cílů** – při spuštění NVDA doplněk zapamatované cíle několik sekund hledá a pak je oznámí najednou, například „Sleduji 3 zapamatované cíle“, nebo „Sleduji 3 z 10 zapamatovaných cílů“, pokud se zbývající zatím neobjevily. Ty, které se objeví později, se ohlásí jednotlivě.
- **Ukončení sledování cíle** – například „Přestávám sledovat seznam: Seznam zpráv“. Totéž uslyšíte pokaždé, když cíl přestane existovat.
- **Vymazání celého seznamu cílů** – „Všechny cíle vymazány“.
- **Pozastavení sledování** (klávesa `p`) – „Sledování obsahu na pozadí vypnuto“.
- **Obnovení** – „Sledování obsahu na pozadí zapnuto“. Při obnovení sledování a na konci hledání po spuštění NVDA doplněk místo toho oznámí „Žádné cíle ke sledování“, pokud nezbývá co sledovat.

## Nastavení

Nastavení doplňku najdete v kategorii **Sledování obsahu na pozadí** v dialogu Nastavení NVDA (nabídka NVDA → Možnosti → Nastavení).

Vaše nastavení se ukládají do konfigurace NVDA, takže fungují s konfiguračními profily a ukládají se běžným způsobem – při ukončení NVDA, nebo když zvolíte Uložit nastavení.

Související možnosti jsou uspořádány do skupin. Všechny dostupné možnosti jsou popsány níže v pořadí, v jakém se v dialogu zobrazují. Možnosti na nejvyšší úrovni a celé skupiny jsou nadpisy úrovně 3, jednotlivé možnosti uvnitř skupin jsou nadpisy úrovně 4.

### **Povolit sledování obsahu na pozadí** (zaškrtávací políčko)

Pokud není zaškrtnuto, doplněk vás přestane upozorňovat, ale zachová celý seznam cílů i všechna nastavení, takže ho můžete umlčet (třeba během schůzky) a později zase zapnout přesně v tom stavu, v jakém byl. Jde o stejný přepínač, který přepíná klávesa pro pozastavení a obnovení. Výchozí hodnota je zaškrtnuto.

### **Při změně cíle** (skupina)

Co se stane, když se ve sledovaném cíli objeví nový obsah. Možnosti v této skupině jsou dostupné vždy.

#### **Pípnout** (zaškrtávací políčko)

Přehraje tón, když se cíl změní. Výchozí hodnota je zaškrtnuto.

#### **Oznámit** (zaškrtávací políčko)

Oznámí, co se kde změnilo, například „Okno: Claude“ nebo „Seznam: Seznam zpráv“. Úroveň podrobnosti oznámení lze dále upravit níže. Výchozí hodnota je zaškrtnuto.

#### **Interval sledování** (editační pole)

Lze zapsat pouze celá čísla. Nastavuje, jak často má doplněk kontrolovat změny ve všech existujících cílech, v sekundách. 0 znamená nikdy neoznamovat změny cílů automaticky, pouze je zobrazovat v [nabídce cílů](#nabídka-cílů). Výchozí hodnota je 1.

#### **Kolik změn oznámit najednou** (editační pole)

Lze zapsat pouze celá čísla. Nastavuje, kolik po sobě jdoucích změn stejného cíle má doplněk oznámit v řadě, než budete muset cíl alespoň jednou znovu fokusovat a poté se opět přepnout jinam, aby se zase začaly oznamovat následující změny. 0 znamená oznámit každou jednotlivou změnu pokaždé, když je cíl na pozadí, bez ohledu na cokoli. Výchozí hodnota je 5.

### **Chování při sledování oken** (skupina)

Možnosti v této skupině jsou dostupné vždy. Upřesňují, jak má doplněk oznamovat změny v cílech, které jsou celými okny.

#### **Ignorovat indikátory průběhu** (zaškrtávací políčko)

Samotné NVDA umí ohlašovat nativní indikátory průběhu slovně anebo pípáním, i na pozadí, takže nemusí být vždy žádoucí, aby vás tento doplněk zahlcoval hlášením neustále se měnícího indikátoru průběhu v konkrétní aplikaci, když vás ve skutečnosti zajímá její skutečný textový výstup. Pokud je tato volba zaškrtnuta, potlačí oznamování indikátorů průběhu. Výchozí hodnota je zaškrtnuto.

#### **Ignorovat opakovaně se měnící prvky** (zaškrtávací políčko)

Pokud je zaškrtnuto, doplněk nebude oznamovat po sobě jdoucí změny stejného prvku (části okna), který už byl jednou oznámen, například časovače nebo odpočtu měnícího se každou sekundu, jako třeba aplikace Claude počítající, jak dlouho modelu trvalo přemýšlení. Tyto prvky bývají často spíše na obtíž než k užitku, protože samy o sobě neposkytují žádnou skutečnou, užitečnou informaci. Proto si můžete nastavit, aby je doplněk neoznamoval jako změny, pokud vás ve skutečnosti zajímá samotný výstup. Výchozí hodnota je zaškrtnuto.

#### **Považovat změnu názvu za zmizení cíle** (zaškrtávací políčko)

Pokud je zaškrtnuto a změní se název okna, které sledujete, doplněk ho začne považovat za jiné okno a tedy se zachová stejně, jako by původní cíl zmizel, přestože fyzické okno v systému je pořád stejné. Výchozí hodnota je nezaškrtnuto.

#### **Ignorovat prvek pod fokusem** (zaškrtávací políčko)

Tato volba se projeví pouze u okna, které se čte i ve chvíli, kdy v něm pracujete, což umožňuje nastavení sledování cílů i na popředí. Pokud je zaškrtnuta, prvek, na kterém máte fokus, ani nic uvnitř něj se nikdy neoznámí jako změna, takže se vám znaky, které píšete do editačního pole, nečtou zpátky jako nový obsah. Napsaný text se neoznámí ani ve chvíli, kdy prvek opustíte, oznámí se jen to, co mezitím přibylo jinde v okně. Výchozí hodnota je zaškrtnuto.

### **Parametry pípnutí** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko **Pípnout**.

#### **Délka** (editační pole)

Lze zapsat pouze celá čísla. Nastavuje, jak dlouho má pípnutí trvat, v milisekundách. Výchozí hodnota je 50.

#### **Výška** (editační pole)

Lze zapsat pouze celá čísla. Nastavuje, s jakou frekvencí se má pípnutí přehrávat, v hertzech. Výchozí hodnota je 440.

#### **Otestovat** (tlačítko)

Přehraje testovací pípnutí s aktuálně nastavenými parametry, abyste si mohli ověřit, jestli zní tak, jak chcete.

### **Do oznámení o změně zahrnout** (skupina)

Možnosti v této skupině jsou dostupné, pouze pokud je zaškrtnuto výše uvedené políčko **Oznámit**. Určují, z čeho přesně se oznámení o změně cíle skládá. Dokud je zapnuto slovní oznamování jako takové, název cíle (například Claude nebo Seznam zpráv) je zahrnut vždy.

#### **Typ cíle** (zaškrtávací políčko)

Jestli oznamovat typ cíle (například **okno**, **seznam** nebo **editační pole**). Výchozí hodnota je zaškrtnuto.

#### **Změněný obsah** (zaškrtávací políčko)

Jestli oznamovat nový obsah v cíli po poslední změně. Výchozí hodnota je zaškrtnuto.

### **Do popisů v nabídce zahrnout** (skupina)

Možnosti v této skupině jsou dostupné vždy. Určují úroveň podrobnosti, kterou chcete slyšet při procházení [nabídky cílů](#nabídka-cílů).

#### **Typ cíle** (zaškrtávací políčko)

Jestli v popisu příslušné položky pro daný cíl zobrazovat typ cíle (například **okno**, **seznam** nebo **editační pole**). Výchozí hodnota je zaškrtnuto.

#### **Čas od poslední změny** (zaškrtávací políčko)

Jestli v popisu příslušné položky pro daný cíl zobrazovat relativní čas od poslední změny(například před 3 minutami). Výchozí hodnota je zaškrtnuto.

#### **Změněný obsah** (zaškrtávací políčko)

Jestli v popisu příslušné položky pro daný cíl zobrazovat nový obsah po poslední změně. Výchozí hodnota je zaškrtnuto.

### **Čas do zavření překrytí** (editační pole)

Toto nastavení je dostupné vždy. Lze zapsat pouze celá čísla. Určuje, kolik sekund bez stisku klávesy musí uplynout, než se překrytí samo zavře. Výchozí hodnota je 10.

### **Řazení cílů** (skupina)

Dva přepínače v této skupině jsou dostupné vždy. Určují, v jakém pořadí se nové cíle umisťují do deseti dostupných číslovaných slotů (viz [Klávesové příkazy](#klávesové-příkazy)) i zobrazují v [nabídce cílů](#nabídka-cílů).

#### **Nejstarší první** (přepínač, výchozí nastavení)

#### **Nejnovější první** (přepínač)

### **Pamatovat si cíle** (zaškrtávací políčko)

Toto nastavení je dostupné vždy. Pokud je zaškrtnuto, seznam cílů zůstane zachován i po restartu NVDA a doplněk se k cíli znovu připojí pokaždé, když se cíl znovu objeví (například sleduje okno asistenta při každém jeho otevření, aniž byste to museli znovu nastavovat). Pokud zaškrtnuto není, začíná seznam cílů při každém spuštění prázdný a ukládají se pouze vaše nastavení. Výchozí hodnota je nezaškrtnuto.

### **Zapomenout cíl, když přestane existovat** (zaškrtávací políčko)

Toto nastavení je dostupné vždy. Pokud je zaškrtnuto, cíl se ze seznamu automaticky odebere, jakmile přestane existovat, aby se nehromadily zastaralé položky. Výchozí hodnota je zaškrtnuto.

## Známá omezení

- **Panely prohlížečů na pozadí nelze sledovat.** Webové prohlížeče udržují čitelný pouze ten panel, na který se právě díváte. Pokud chcete některou stránku sledovat, zatímco pracujete jinde, otevřete si ji ve vlastním okně místo v panelu na pozadí. Toto je stejné i pro vidící uživatele.

- **Některé aplikace toho na pozadí zobrazují jen velmi málo.** Kolik ten který program prozradí odečítači obrazovky o obsahu, na kterém není fokus, záleží na daném programu. Moderní aplikace postavené na technologii UIA – Terminál, Nastavení, Kalkulačka, Pošta, Fotky a většina programů z Microsoft Storu – aplikace, které zobrazují webovou stránku (aplikace postavené na Electronu) – desktopová aplikace Claude, Visual Studio Code, Discord, Slack, Signal, WhatsApp pro Windows, Spotify i samotné prohlížeče (Chrome, Edge, Firefox) – se v tomto ohledu značně liší. Pokud program nový obsah nezobrazuje jako text, doplněk ho oznámit nedokáže.

- **Počítá se jen to, co se v okně právě zobrazuje.** Dlouhé seznamy – historie chatu, seznamy souborů, výsledky hledání – existují obvykle jen jako těch několik řádků, které jsou zrovna zobrazeny. Doplněk nevidí položky odrolované mimo obrazovku, stejně jako je nevidí vidící uživatelé, a minimalizované okno často přestane svůj obsah zobrazovat úplně, dokud ho neobnovíte.

Pokud často potřebujete vědět o aktualizacích z aplikace, kterou používáte na pozadí, bývá obvykle spolehlivější a jednodušší nastavit samotnou aplikaci tak, aby vám posílala oznámení, pokud to daná aplikace umožňuje. Stejně tak když aplikaci minimalizujete do systémové lišty, přestane zobrazovat okno, takže ji doplněk už nadále nemůže sledovat. Pokud ale ikona na systémové liště prezentuje užitečné informace jako přístupné textové aktualizace, můžete sledovat přímo tuto ikonu.

## Spolupráce

Pokud byste chtěli přispět k vývoji doplňku – ať už překladem, hlášením chyb nebo vytvořením pull requestu – můžete tak učinit v jeho [repozitáři na GitHubu](https://github.com/4sensegaming/background-content-tracker). Veškerou pomoc vítám a vážím si jí.

## Historie změn

### Verze 1.0, 6. září 2026
* První verze