# Hintergrund-Inhaltsverfolgung

* Autor: Lukáš Hosnedl
* Mindestens erforderliche NVDA-Version: 2026.3
* Zuletzt getestete NVDA-Version: 2027.1

**Von KI erstellt, von Menschen entworfen und gründlich getestet.**

## Beschreibung

Die Hintergrund-Inhaltsverfolgung verfolgt ein Fenster oder ein einzelnes Steuerelement und gibt Ihnen Bescheid, sobald darin neuer Inhalt erscheint. Sie können in einem Fenster weiterarbeiten, während das Add-on ein anderes im Auge behält.

Wenn sehende Menschen in einem Fenster arbeiten, bemerken sie sofort, wenn ein Pop-up erscheint oder sich in einem Fenster daneben etwas ändert, und können einschätzen, ob das jetzt oder erst später Aufmerksamkeit braucht. NVDA kann Warnungen und Live-Regionen ansagen, aber meist nur, solange sich das betreffende Fenster im Vordergrund befindet. Änderungen, die passieren, während Sie woanders arbeiten, entgehen Ihnen daher leicht.

Die Hintergrund-Inhaltsverfolgung gibt Ihnen genau diesen Überblick: Sie wählen aus, was verfolgt werden soll und wie Sie benachrichtigt werden möchten, und NVDA benachrichtigt Sie, wenn sich der Inhalt ändert, ohne dass Sie das verlassen müssen, woran Sie gerade arbeiten.

Dieses Add-on ist ein sehr mächtiges und anpassbares Werkzeug, das unzugängliche Fenster oder Steuerelemente im Grunde in sprechende Live-Regionen verwandeln kann, die überall funktionieren. Überraschend gut funktioniert es zum Beispiel mit:

- Terminals, die im Hintergrund laufen,
- Kurzen, sich schnell ändernden dynamischen Meldungen in einer einzelnen Liste, einem Textbereich oder einem NVDA-Objekt,
- Unzugänglichen Webseiten mit dynamischen Änderungen,
- Messaging-Apps, die neu eingehende Nachrichten nicht automatisch vorlesen,
- Sowie Electron-Apps wie dem neuen ChatGPT, die in puncto Barrierefreiheit viel zu wünschen übrig lassen: Sie können lange stumm bleiben und dann große Textblöcke an einer sich verschiebenden Stelle ausgeben, die womöglich schwer zu finden ist.

Allerdings werden das Add-on wohl nur Power-User zu schätzen wissen, die ihre Arbeit schneller und effizienter erledigen möchten, zum Beispiel:

- Diejenigen, die routinemäßig KI einsetzen, um etwas Umfangreiches zu erstellen,
- Diejenigen, die oft langwierige automatisierte Aufgaben ausführen und deren Ausgabe in Echtzeit verfolgen müssen,
- Diejenigen, die häufig zwischen mehreren Fenstern mit dynamischer Ausgabe wechseln müssen,
- Oder diejenigen, die an teilweise oder vollständig automatisierten Arbeitsabläufen beteiligt sind, in denen mehrere Aufgaben gleichzeitig laufen.

Wenn Sie es brauchen, wissen Sie das wahrscheinlich schon. Anderen mag es überwältigend, überladen oder verwirrend vorkommen.

## Verwendung

Sie erstellen eine Liste von Zielen, die verfolgt werden sollen – ganze Fenster oder einzelne Steuerelemente wie ein Eingabefeld oder die Nachrichtenliste eines Chats –, und das Add-on benachrichtigt Sie, sobald in einem davon neuer Inhalt erscheint. Sie können mehrere Ziele gleichzeitig verfolgen und die Verfolgung jedes einzelnen unabhängig starten oder stoppen.

### Beispielszenarien

- **Warten auf eine lang laufende Aufgabe in einer anderen App.** Sie geben einem KI-Assistenten wie Claude eine Aufgabe und wechseln, statt in diesem Fenster zu warten, woandershin, um etwas anderes zu erledigen. Das Add-on verfolgt das Fenster des Assistenten und gibt Ihnen Bescheid, sobald neue Ausgabe erscheint. So wissen Sie, dass er geantwortet hat, ohne immer wieder zurückwechseln und nachsehen zu müssen.
- **Eine Webseite im Auge behalten, während Sie woanders tippen.** Sie schreiben in einem Chat wie WhatsApp, während daneben eine Webseite geöffnet ist. Wenn sich diese Seite im Hintergrund aktualisiert, gibt Ihnen das Add-on Bescheid – so bemerken Sie es genau wie eine sehende Person.

### Ein typischer Ablauf

1. Gehen Sie zu dem Fenster oder Steuerelement, das Sie verfolgen möchten: Setzen Sie den Fokus darauf, zeigen Sie mit der Maus darauf oder bewegen Sie das Navigator-Objekt oder den NVDA-Cursor dorthin.
2. Starten Sie die Verfolgung, entweder mit dem passenden [Tastenkombination](#tastenkombinationen) oder über das [Zielmenü](#das-zielmenü).
3. Wechseln Sie zu dem, woran Sie arbeiten möchten. Wenn im verfolgten Ziel neuer Inhalt erscheint, benachrichtigt NVDA Sie so, wie Sie es [eingestellt](#globale-einstellungen) haben.
4. Stoppen Sie die Verfolgung eines Ziels, wenn Sie es nicht mehr brauchen, oder löschen Sie die ganze Zielliste auf einmal.

## Tastenkombinationen

Das Add-on wird über einen einzigen **mehrstufigen Befehl** bedient: Sie drücken eine Präfix-Tastenkombination, lassen sie los und drücken dann noch eine Taste, um auszuwählen, was geschehen soll. Das Präfix allein bewirkt nichts, sodass die Befehle des Add-ons NVDA oder anderen Apps nie in die Quere kommen.

Das Standardpräfix ist NVDA+; (Semikolon). Auf einer deutschen Tastatur wird das Semikolon mit Umschalt+Komma eingegeben, das Präfix ist dort also NVDA+Umschalt+Komma.

Wenn Sie das Präfix drücken, öffnet das Add-on eine **virtuelle Überlagerung**. Solange die Überlagerung geöffnet ist, wird jede Taste, die Sie drücken, als einer der folgenden Befehle behandelt. Das Öffnen und Schließen der Überlagerung verschiebt nie den Fokus – er bleibt genau dort, wo er war, sodass die Befehle des Add-ons Sie nie bei dem stören, was Sie gerade tun.

Drücken Sie nach dem Präfix eine der folgenden Tasten:

- `h` – **Hilfe**: erklärt kurz, was jede in der Überlagerung verfügbare Taste bewirkt. Zweimal drücken, um den Hilfetext als Meldung im Lesemodus anzuzeigen.
- `f1` – **öffnet diese Dokumentation** im Standard-Webbrowser. Dieser Befehl ist kontextabhängig: In der Überlagerung springt er zu diesem Kapitel, im Menü zum Kapitel [Das Zielmenü](#das-zielmenü), bei geöffnetem Einstellungsdialog zum Kapitel [Globale Einstellungen](#globale-einstellungen) und so weiter.
- `w` – startet oder stoppt die Verfolgung des aktuellen **Fensters**.
- `f` – startet oder stoppt die Verfolgung des Steuerelements, das gerade den Tastatur**fokus** hat.
- `m` – startet oder stoppt die Verfolgung des Steuerelements unter dem **Maus**zeiger.
- `n` – startet oder stoppt die Verfolgung des aktuellen **Navigator-Objekts** (dort, wo sich der NVDA-Cursor befindet).
- `t` – öffnet das **[Zielmenü](#das-zielmenü)**.
- `1` bis `0` – **sagt Informationen über ein Ziel an**, je nach seiner Position in der Liste (siehe unten). Drücken Sie dieselbe Zahl ein zweites Mal, um den Fokus auf dieses Ziel zu setzen, oder direkt danach ein drittes Mal, um stattdessen seinen [Verlauf der letzten Änderungen](#verlauf-der-letzten-änderungen) zu öffnen.
- `Leertaste` oder `Eingabetaste` – wie die Zahlentasten, aber immer für das **zuletzt hinzugefügte** Ziel: einmal drücken, um Informationen darüber zu hören, zweimal, um den Fokus darauf zu setzen, dreimal, um seinen Verlauf zu öffnen.
- `Strg`+eine Zahl (`1` bis `0`) – **stoppt die Verfolgung** des Ziels in diesem Fach.
- `Alt`+eine Zahl (`1` bis `0`) – **öffnet das [Zielmenü](#das-zielmenü)** direkt für das Ziel in diesem Fach.
- `Rücktaste` – **stoppt die Verfolgung des zuletzt hinzugefügten** Ziels.
- `Entf` – **stoppt die Verfolgung aller Ziele** (löscht die ganze Liste auf einmal).
- `p` – **pausiert** die gesamte Verfolgung **oder setzt sie fort** (schaltet [*Verfolgung aktivieren*](#verfolgung-aktivieren-kontrollfeld-standardmäßig-aktiviert) um).
- `s` – öffnet die **[Einstellungen](#globale-einstellungen)** des Add-ons (dieselbe Kategorie wie NVDA-Menü → Optionen → Einstellungen → Hintergrund-Inhaltsverfolgung).
- `i` – öffnet den NVDA-Dialog **Tastenzuordnungen** direkt bei der Kategorie Hintergrund-Inhaltsverfolgung, sodass Sie das Präfix neu zuweisen können, ohne danach suchen zu müssen.
- `Escape` – **schließt die Überlagerung**, ohne sonst etwas zu tun.

Die Befehle für Fenster, Fokus, Maus und Navigator-Objekt sind Umschalter: Drücken Sie einen davon einmal, um dieses Ziel zur Liste hinzuzufügen, und erneut, um es wieder zu entfernen, solange es noch das aktuelle Fenster ist, den Fokus hat usw. Sie können beliebig viele Ziele gleichzeitig verfolgen.

Diese vier Befehle berücksichtigen außerdem `Umschalt` und `Strg`, die festlegen, wie das Ziel, das Sie hinzufügen, verfolgt werden soll: `Umschalt` merkt sich genau dieses eine Ziel, `Strg` liest es auch dann, wenn seine eigene App im Vordergrund ist, und beide zusammen tun beides. Das sind [zielbezogene Einstellungen](#zieleinstellungen), die beim Hinzufügen direkt für dieses Ziel gesetzt werden, anstatt von den [globalen Einstellungen](#globale-einstellungen) übernommen oder später im [Zielmenü](#das-zielmenü) manuell eingestellt zu werden, und sie ändern die globale Einstellung nicht. Ein Tastendruck, der die Verfolgung des Ziels *stoppt*, statt es hinzuzufügen, ignoriert die Zusatztasten einfach. Die Zusatztasten sind nur nützlich, wenn Sie die Optionen [**Ziele merken**](#ziele-merken-kontrollfeld-standardmäßig-deaktiviert) oder [**Ziele auch im Vordergrund verfolgen**](#ziele-auch-im-vordergrund-verfolgen-kontrollfeld-standardmäßig-deaktiviert) global deaktiviert haben, dieses Verhalten aber genau für dieses eine Ziel brauchen.

Die Zahlentasten beziehen sich auf **Fächer** in Ihrer Zielliste, nicht auf feste Ziele. Standardmäßig ist `1` das zuletzt hinzugefügte Ziel, `2` das davor hinzugefügte und so weiter bis `0` – das zehnte Fach. Die Einstellung [**Sortierung der Zielfächer**](#sortierung-der-ziele) kann die Fächer anders anordnen, etwa ältestes Ziel zuerst, zuletzt geändertes Ziel zuerst oder alphabetisch. Wird ein Ziel entfernt – weil Sie seine Verfolgung gestoppt haben oder es nicht mehr existiert –, rücken die nachfolgenden Ziele auf und füllen die Lücke, sodass `2` immer das Ziel ansagt, das gerade an zweiter Stelle der Liste steht.

Wenn ein Ziel vorhanden ist, sagt das Add-on standardmäßig seinen Typ (seine Rolle), seinen Namen und den geänderten Inhalt des Ziels an, zum Beispiel *Fenster: Claude, Editing readme.md* oder *Liste: Nachrichtenliste, Sie haben gesagt: Okay*. Der Detailgrad dieser Ansagen lässt sich [in den Einstellungen des Add-ons anpassen](#in-änderungsansage-einbeziehen-gruppierung).

Sie können das Präfix im NVDA-Dialog Tastenzuordnungen (NVDA-Menü → Optionen → Tastenbefehle) ändern, wo der Befehl des Add-ons unter der Kategorie **Hintergrund-Inhaltsverfolgung** erscheint. Die nachfolgenden Tasten sind Teil des mehrstufigen Befehls selbst.

## Das Zielmenü

Das **Zielmenü** (das Präfix gefolgt von `t`) listet alle verfolgten Ziele als geordnete Menüeinträge auf, sodass Sie sich weder die aktuelle Position des Ziels in der Liste noch eine der anderen Tasten merken müssen.

Jeder Eintrag benennt genau, worauf er sich bezieht, zum Beispiel *Fenster: Claude, vor 3 Minuten, 3 tasks running*. Ein Ziel, das gerade nicht existiert – ein gemerktes Ziel, dessen Fenster noch nicht wieder geöffnet wurde –, zeigt statt der Zeit und des Inhalts *nicht gefunden* an und bleibt im Menü, denn Sie können seine Verfolgung weiterhin stoppen, seine Einstellungen ändern oder es dort lassen und warten, bis es zurückkommt. Die Reihenfolge, in der die Ziele angezeigt werden, richtet sich nach der Einstellung [**Sortierung der Ziele im Menü**](#sortierung-der-ziele).

Jedes Ziel ist ein Untermenü. Wenn Sie es aufklappen, können Sie:

- Mit *Verfolgung stoppen* seine Verfolgung stoppen,
- Mit *Fokus setzen* den Fokus darauf setzen (sofern es ihn nicht bereits hat),
- Seine [*Zieleinstellungen*](#zieleinstellungen) ändern,
- Oder den [**Verlauf der letzten Änderungen**](#verlauf-der-letzten-änderungen) dieses Ziels durchsehen (wird gar nicht angezeigt, solange sich noch nichts geändert hat oder die Verlaufsgröße 0 ist).

Alles, was Sie bereits verfolgen, steht im Menü ganz oben, sodass Sie schnell zum gewünschten Ziel wechseln oder seine Verfolgung stoppen können. Darunter folgen die Ziele, deren Verfolgung Sie von Ihrer aktuellen Position aus starten können (Fenster, Fokus, Mauszeiger oder Navigator-Objekt). Der Eintrag, mit dem Sie die Verfolgung aller aktuellen Ziele stoppen, steht am Ende des Menüs.

### Zieleinstellungen

Jeder Eintrag unter *Zieleinstellungen* ist ein Kontrollfeld, und es zeigt das, was das Ziel tatsächlich tut: seinen eigenen Wert, wo Sie ihm einen gegeben haben, und überall sonst die [globale Einstellung](#globale-einstellungen). Wenn Sie eines aktivieren oder deaktivieren, erhält das Ziel einen eigenen Wert für genau diese eine Einstellung, und zwar sofort; alle anderen Einstellungen folgen weiterhin der globalen.

- *Beim Ansagen einer neuen Änderung vorherige Sprachausgabe unterbrechen* wird für alle Ziele angezeigt, solange die [globale Option *Ansagen*](#ansagen-kontrollfeld-standardmäßig-aktiviert) aktiviert ist.
- *Änderungsverlauf beim Ansehen aktualisieren* wird für alle Ziele angezeigt, solange die [Verlaufsgröße](#verlauf-der-letzten-änderungen-pro-ziel-aufbewahren-eingabefeld-standardmäßig-50) nicht 0 ist.
- *Neue Änderungen bei geöffnetem Verlauf ansagen* wird für alle Ziele angezeigt, solange die Verlaufsgröße nicht 0 ist und die globale Option *Ansagen* aktiviert ist.
- Die Optionen *Fortschrittsbalken ignorieren*, *Zähler, Schrittanzeigen und Timer ignorieren*, *Geänderten Titel als verschwundenes Ziel betrachten* und *Bekannte allgemeine Steuerelemente ignorieren* werden nur für Fensterziele angezeigt.
- *Dieses Ziel auch im Vordergrund verfolgen* wird für alle Ziele angezeigt.
- *Fokussiertes Steuerelement ignorieren* wird angezeigt, solange das Ziel ein Fenster ist und außerdem [auch im Vordergrund verfolgt werden soll](#ziele-auch-im-vordergrund-verfolgen-kontrollfeld-standardmäßig-deaktiviert).
- *Dieses Ziel merken* wird für alle Ziele angezeigt.
- *Dieses Ziel vergessen, wenn es verschwindet* wird nur für gemerkte Ziele angezeigt.

Wenn Sie eine [globale Einstellung](#globale-einstellungen) ändern, wirkt sich das auch auf bestehende Ziele aus, sofern diese Einstellung nicht lokal überschrieben wurde. Der Einstellungsbereich legt nur globale Werte fest: Nichts, was Sie dort tun, nimmt einem Ziel seinen eigenen Wert weg. Alle lokalen Werte werden erst gelöscht, wenn Sie die Verfolgung des Ziels stoppen und es erneut hinzufügen oder ein gemerktes Ziel vergessen.

### Verlauf der letzten Änderungen

Dieses Untermenü listet so viele der letzten Änderungen im jeweiligen Ziel auf, wie Sie in der Einstellung [*Verlauf der letzten Änderungen pro Ziel aufbewahren*](#verlauf-der-letzten-änderungen-pro-ziel-aufbewahren-eingabefeld-standardmäßig-50) festgelegt haben, in der durch die [*Sortierung des Änderungsverlaufs*](#sortierung-der-ziele) bestimmten Reihenfolge und mit dem eingestellten [Detailgrad](#in-menübeschreibungen-einbeziehen-gruppierung). Ist *Verlauf der letzten Änderungen pro Ziel aufbewahren* auf 0 gesetzt, wird das Untermenü gar nicht angezeigt. Ältere Änderungen über diese Anzahl hinaus werden entfernt. Beachten Sie, dass diese Einstellung nur global gilt. Wenn Sie einen Eintrag in diesem Untermenü auswählen, wird diese Änderung als Meldung im Lesemodus geöffnet.

Der Verlauf verschwindet, wenn Sie die Verfolgung eines Ziels stoppen, wenn ein Ziel [nach seinem Verschwinden](#gemerkte-ziele-vergessen-wenn-sie-verschwinden-kontrollfeld-standardmäßig-deaktiviert) automatisch vergessen wird oder am Ende der Sitzung, und er wird nirgends gespeichert. Wenn die [Verfolgung pausiert ist](#verfolgung-aktivieren-kontrollfeld-standardmäßig-aktiviert), wird auch der Verlauf nicht aktualisiert.

## Globale Einstellungen

Die Optionen des Add-ons befinden sich in der Kategorie **Hintergrund-Inhaltsverfolgung** im Einstellungsdialog von NVDA (NVDA-Menü → Optionen → Einstellungen). Das Add-on unterstützt mehrere Konfigurationsprofile.

Zusammengehörige Optionen sind gruppiert. Alle verfügbaren Optionen werden unten in der Reihenfolge beschrieben, in der sie im Einstellungsbereich erscheinen. Optionen der obersten Ebene und ganze Gruppierungen sind Überschriften der Ebene 3, einzelne Optionen innerhalb von Gruppen sind Überschriften der Ebene 4.

### **Verfolgung aktivieren** (Kontrollfeld, standardmäßig aktiviert)

Wenn deaktiviert, benachrichtigt Sie das Add-on nicht mehr, behält aber Ihre gesamte Zielliste und alle Ihre Einstellungen, sodass Sie es stummschalten können (etwa während einer Besprechung) und später genau so wieder einschalten, wie es war. Das ist derselbe Schalter, den der [Tastenkombination zum Pausieren und Fortsetzen](#tastenkombinationen) umschaltet.

Dies ist die einzige Option, die nie gespeichert wird: Beim Start von NVDA ist die Verfolgung immer aktiviert.

### **Verfolgungsintervall** (Eingabefeld, standardmäßig 1)

Akzeptiert nur ganze Zahlen. Legt in Sekunden fest, wie oft das Add-on alle vorhandenen Ziele auf Änderungen prüfen soll. 0 bedeutet, Änderungen an Zielen nie automatisch anzusagen, sondern sie nur im [Zielmenü](#das-zielmenü) anzuzeigen.

### **Auf einmal anzusagende Änderungen (nur Ziele im Hintergrund)** (Eingabefeld, standardmäßig 5)

Akzeptiert nur ganze Zahlen. Legt fest, wie viele aufeinanderfolgende Änderungen desselben Ziels das Add-on hintereinander ansagen soll, bevor Sie das Ziel erneut fokussieren und dann wieder woandershin wechseln müssen, damit weitere Änderungen angesagt werden. 0 bedeutet, jede Änderung anzusagen.

Diese Option wirkt sich nie auf Ziele im Vordergrund aus. Wenn die [Verfolgung auch für Ziele im Vordergrund aktiviert ist](#ziele-auch-im-vordergrund-verfolgen-kontrollfeld-standardmäßig-deaktiviert), werden für diese immer alle Änderungen angesagt.

### **Überlagerungs-Timeout** (Eingabefeld, standardmäßig 10)

Akzeptiert nur ganze Zahlen. Legt fest, wie viele Sekunden ohne Tastendruck vergehen müssen, bevor sich die Überlagerung von selbst schließt. 0 bedeutet, dass sich die Überlagerung nie von selbst schließt: Sie bleibt geöffnet, bis Sie sie mit Escape oder einem Befehl schließen, der den Fokus woandershin verschiebt, etwa dem Öffnen des [Zielmenüs](#das-zielmenü).

### **Ziele auch im Vordergrund verfolgen** (Kontrollfeld, standardmäßig deaktiviert)

Normalerweise wird ein Ziel nur gelesen, während Sie woanders arbeiten; sobald seine eigene App in den Vordergrund kommt, lässt das Add-on es in Ruhe. Wenn aktiviert, wird neuer Inhalt eines Ziels auch dann angesagt, wenn Sie gerade mit diesem Fenster oder einzelnen Steuerelement arbeiten.

Beachten Sie: Wenn die App des Ziels direkt mit Screenreadern kommuniziert (über ARIA-Live-Regionen oder andere Barrierefreiheitsereignisse), können dieselben Ansagen beim Arbeiten in ihrem Fenster manchmal doppelt gemeldet werden – einmal von der App selbst und einmal vom Add-on. Um in diesem Fall nur die eigenen Ansagen der App zu hören, können Sie *Dieses Ziel auch im Vordergrund verfolgen* in den [Zieleinstellungen](#zieleinstellungen) dieses Ziels deaktivieren, die Verfolgung vorübergehend pausieren oder das Ziel entfernen und später wieder hinzufügen. Um nur die Ansagen des Add-ons zu hören, deaktivieren Sie in NVDA die Option „Änderungen dynamischer Inhalte vorlesen“ (standardmäßig NVDA+5).

### **Änderungsverlauf** (Gruppierung)

Die Optionen in dieser Gruppierung steuern den [Verlauf der letzten Änderungen](#verlauf-der-letzten-änderungen), der für jedes Ziel aufbewahrt wird.

#### **Verlauf der letzten Änderungen pro Ziel aufbewahren** (Eingabefeld, standardmäßig 50)

Akzeptiert nur ganze Zahlen. Legt fest, wie viele der letzten Änderungen im [Verlauf pro Ziel](#verlauf-der-letzten-änderungen) aufbewahrt werden sollen. Ältere Änderungen werden verworfen. 0 bedeutet kein Verlauf, und die anderen Optionen dieser Gruppierung sind dann nicht verfügbar.

Bei gemerkten Zielen, die verschwunden sind, wird auch der Verlauf gemerkt und bleibt verfügbar, bis das Ziel entfernt wird oder bis zum Ende der Sitzung.

#### **Änderungsverlauf beim Ansehen aktualisieren** (Kontrollfeld, standardmäßig aktiviert)

Wenn aktiviert, fügt ein geöffneter Verlaufsdialog neue Änderungen laufend hinzu, und die Zeit jeder Änderung zählt weiter hoch. Wenn deaktiviert, bleibt der Dialog so, wie er beim Öffnen war.

#### **Neue Änderungen bei geöffnetem Verlauf ansagen** (Kontrollfeld, standardmäßig aktiviert)

Diese Option ist nur verfügbar, wenn das Kontrollfeld [**Ansagen**](#ansagen-kontrollfeld-standardmäßig-aktiviert) aktiviert ist. Wenn deaktiviert, werden neue Änderungen in einem Ziel nicht gesprochen, solange sein Verlaufsdialog geöffnet ist. Der [Signalton](#signalton-kontrollfeld-standardmäßig-aktiviert) ertönt trotzdem.

### Sortierung der Ziele

Es gibt drei Sätze von Auswahlschaltern, eine nach der anderen: *Sortierung der Zielfächer*, *Sortierung der Ziele im Menü* und *Sortierung des Änderungsverlaufs*. Alle bieten (mit wenigen Ausnahmen) dieselben unten aufgeführten Optionen und können entweder gleich oder unabhängig voneinander eingestellt werden. Sie bestimmen, in welcher Reihenfolge Ziele auf die zehn verfügbaren nummerierten Fächer verteilt (siehe [Tastenkombinationen](#tastenkombinationen)), im [Zielmenü](#das-zielmenü) angezeigt beziehungsweise im [Verlauf der letzten Änderungen pro Ziel](#verlauf-der-letzten-änderungen) angeordnet werden.

- *Neuestes Ziel / neueste Änderung zuerst* (Standard für alle Sortierungsarten)
- *Ältestes Ziel / älteste Änderung zuerst*
- *Zuletzt geändertes Ziel zuerst* (nicht für die Sortierung des Verlaufs verfügbar)
- *Am längsten unverändertes Ziel zuerst* (nicht für die Sortierung des Verlaufs verfügbar)
- *Alphabetisch, A bis Z*
- *Alphabetisch, Z bis A*

### **Ziele merken** (Kontrollfeld, standardmäßig deaktiviert)

Wenn aktiviert, bleibt Ihre Zielliste über NVDA-Neustarts hinweg erhalten, und das Add-on verbindet sich erneut mit einem Ziel, sobald es wieder erscheint. So verfolgt es zum Beispiel das Fenster des Assistenten jedes Mal, wenn dieses Fenster geöffnet wird, ohne dass Sie es neu einrichten müssen. Wenn deaktiviert, beginnt die Zielliste in jeder Sitzung leer, und nur Ihre Einstellungen werden gespeichert.

### **Gemerkte Ziele vergessen, wenn sie verschwinden** (Kontrollfeld, standardmäßig deaktiviert)

Legt fest, ob ein gemerktes Ziel vergessen werden soll, wenn es nicht mehr existiert – weil Sie das Fenster des Ziels geschlossen haben oder es von selbst verschwunden ist. Wenn aktiviert, müssen Sie die Verfolgung desselben Ziels jedes Mal, wenn es verschwindet, erneut manuell starten. Ziele, deren Verfolgung Sie manuell stoppen, werden immer vergessen, unabhängig davon, wie diese Option eingestellt ist.

### **Verhalten bei Fensterverfolgung** (Gruppierung)

Die Optionen in dieser Gruppierung legen genauer fest, wie das Add-on Änderungen in Zielen ansagen soll, die ganze Fenster sind.

#### **Fortschrittsbalken ignorieren** (Kontrollfeld, standardmäßig aktiviert)

Wenn aktiviert, unterdrückt diese Option Ansagen sich ändernder Fortschrittsbalken im Fenster. NVDA selbst kann native Fortschrittsbalken ansagen und/oder mit Signaltönen ausgeben, sogar im Hintergrund. Daher möchten Sie vielleicht nicht, dass dieses Add-on Sie in einer bestimmten App zusätzlich mit doppelten Meldungen eines sich ständig ändernden Fortschrittsbalkens überhäuft.

#### **Zähler, Schrittanzeigen und Timer ignorieren** (Kontrollfeld, standardmäßig aktiviert)

Wenn aktiviert, achtet das Add-on auf Steuerelemente, die sich in nichts als Zahlenwerten ändern – ein Timer oder Countdown, der jede Sekunde weiterläuft, ein Schritt- oder Elementzähler, eine Prozentangabe, etwa wenn die Claude-App mitzählt, wie lange das Modell nachgedacht hat. Solche Steuerelemente sind oft eher störend als hilfreich, da sie für sich genommen keine nützlichen Informationen liefern und vor allem keine echten Änderungen vermitteln – sie zeigen nur an, dass die Aufgabe noch läuft. Sobald ein solches Steuerelement erkannt wird, verstummt es und bleibt stumm, solange das Ziel verfolgt wird.

#### **Geänderten Titel als verschwundenes Ziel betrachten** (Kontrollfeld, standardmäßig deaktiviert)

Wenn aktiviert und sich der Titel eines verfolgten Fensters ändert, betrachtet das Add-on es als ein anderes Fenster und verhält sich daher so, als wäre das ursprüngliche Ziel verschwunden, obwohl es im System physisch noch dasselbe Fenster ist.

#### **Bekannte allgemeine Steuerelemente ignorieren** (Kontrollfeld, standardmäßig aktiviert)

Wenn aktiviert, unterdrückt diese Option Ansagen allgemeiner Steuerelemente, etwa wenn der Schalter „Minimieren“ eines Fensters zu „Maximieren“ wird und umgekehrt. Dazu gehören:

- Die Menüleiste der Anwendung (meist mit der Alt-Taste erreichbar)
- Die Schalter „Minimieren“, „Wiederherstellen“, „Maximieren“ und „Schließen“
- Die Schalter „OK“, „Abbrechen“, „Wiederholen“, „Fortfahren“, „Weiter“, „Vorheriges“, „Zurück“, „Fertigstellen“ und „Nicht jetzt“
- Sowie die Schalter „Ja“ und „Nein“.

#### **Fokussiertes Steuerelement beim Verfolgen des Vordergrundfensters ignorieren** (Kontrollfeld, standardmäßig aktiviert)

Diese Option ist nur verfügbar, wenn [Ziele auch im Vordergrund verfolgen](#ziele-auch-im-vordergrund-verfolgen-kontrollfeld-standardmäßig-deaktiviert) aktiviert ist, da sie nur für das Fenster einen Unterschied macht, das gelesen wird, während Sie gerade darin arbeiten. Fenster im Hintergrund und Ziele, die einzelne Steuerelemente sind, sind in keinem Fall betroffen.

Wenn aktiviert, wird das Steuerelement, das gerade den Fokus hat, nie als Änderung angesagt, sodass zum Beispiel die Zeichen, die Sie in ein Eingabefeld tippen, nicht als neuer Inhalt vorgelesen werden.

### **Wenn sich ein Ziel ändert** (Gruppierung)

Was passiert, wenn in einem Ziel neuer Inhalt erscheint.

#### **Signalton** (Kontrollfeld, standardmäßig aktiviert)

Spielt einen Ton ab, wenn sich das Ziel geändert hat.

#### **Ansagen** (Kontrollfeld, standardmäßig aktiviert)

Sagt an, was sich wo geändert hat, zum Beispiel „Fenster: Claude“ oder „Liste: Nachrichtenliste“. Der Detailgrad der Ansage lässt sich weiter unten genauer anpassen.

#### **Beim Ansagen einer neuen Änderung vorherige Sprachausgabe unterbrechen** (Kontrollfeld, standardmäßig deaktiviert)

Diese Option ist nur verfügbar, wenn das Kontrollfeld [**Ansagen**](#ansagen-kontrollfeld-standardmäßig-aktiviert) oben aktiviert ist. Wenn aktiviert, unterbricht eine Änderungsansage alles, was NVDA gerade sagt, und wird sofort gesprochen. Wenn deaktiviert, wartet sie, bis NVDA zu Ende gesprochen hat.

#### **Zielnamen bei aufeinanderfolgenden Änderungen im selben Ziel wiederholen** (Kontrollfeld, standardmäßig aktiviert)

Diese Option ist nur verfügbar, wenn [gesprochene Ansagen an sich](#ansagen-kontrollfeld-standardmäßig-aktiviert) aktiviert sind. Wenn aktiviert, enthält jede einzelne Änderungsansage den Namen des Ziels, auch wenn mehrere Änderungen hintereinander im selben Ziel aufgetreten sind. Wenn deaktiviert, wird der Name des Ziels nur bei der ersten von mehreren aufeinanderfolgenden Änderungen im selben Ziel angesagt.

### **Signalton-Parameter** (Gruppierung)

Die Optionen in dieser Gruppierung sind nur verfügbar, wenn das Kontrollfeld [**Signalton**](#signalton-kontrollfeld-standardmäßig-aktiviert) oben aktiviert ist.

#### **Dauer** (Eingabefeld, standardmäßig 50)

Akzeptiert nur ganze Zahlen. Legt in Millisekunden fest, wie lange der Signalton dauern soll.

#### **Tonhöhe** (Eingabefeld, standardmäßig 440)

Akzeptiert nur ganze Zahlen. Legt in Hertz fest, mit welcher Frequenz der Signalton abgespielt werden soll.

#### **Testen** (Schalter)

Spielt einen Testton mit den aktuell eingestellten Parametern ab, damit Sie prüfen können, ob er so klingt, wie Sie es möchten.

### **In Änderungsansage einbeziehen** (Gruppierung)

Die Optionen in dieser Gruppierung sind nur verfügbar, wenn das Kontrollfeld [**Ansagen**](#ansagen-kontrollfeld-standardmäßig-aktiviert) oben aktiviert ist. Sie bestimmen, woraus die Änderungsansage genau besteht.

#### **Zieltyp** (Kontrollfeld, standardmäßig aktiviert)

Ob der Typ (die Rolle) des Ziels (zum Beispiel **Fenster**, **Liste** oder **Eingabefeld**) angesagt wird.

#### **Geänderter Inhalt** (Kontrollfeld, standardmäßig aktiviert)

Ob der neue Inhalt des Ziels nach der letzten Änderung angesagt wird.

### **In Menübeschreibungen einbeziehen** (Gruppierung)

Die Optionen in dieser Gruppierung legen fest, wie die Einträge im [Zielmenü](#das-zielmenü) beschriftet werden. Sie wirken sich auch darauf aus, wie die Einträge im [Änderungsverlauf](#verlauf-der-letzten-änderungen) der einzelnen Ziele geschrieben werden.

#### **Zieltyp** (Kontrollfeld, standardmäßig aktiviert)

Ob der Typ (die Rolle) des Ziels (zum Beispiel **Fenster**, **Liste** oder **Eingabefeld**) in der Beschreibung des Menüeintrags dieses Ziels angezeigt wird.

#### **Zeit seit letzter Änderung** (Kontrollfeld, standardmäßig aktiviert)

Ob die relative Zeit seit der letzten Änderung im Ziel (zum Beispiel vor 3 Minuten) in der Beschreibung des Menüeintrags dieses Ziels angezeigt wird.

#### **Geänderter Inhalt** (Kontrollfeld, standardmäßig aktiviert)

Ob der neue Inhalt des Ziels nach der letzten Änderung in der Beschreibung des Menüeintrags dieses Ziels angezeigt wird.

## Bekannte Einschränkungen

- **Browser-Tabs im Hintergrund werden nie verfolgt.** Ein Webbrowser hält nur den Tab lesbar, den Sie gerade ansehen. Um eine Seite im Auge zu behalten, während Sie woanders arbeiten, öffnen Sie sie in einem eigenen Fenster, statt sie in einem Hintergrund-Tab zu lassen. Sehende Nutzer können einen Hintergrund-Tab auch nicht sehen.
- **Manche Apps geben sehr wenig preis, wenn sie nicht im Vordergrund sind.** Wie viel eine App einem Screenreader über Inhalte ohne Fokus mitteilt, bestimmt ausschließlich die App selbst. Moderne UIA-Apps – Terminal, Einstellungen, Rechner, Fotos und die meisten Apps aus dem Microsoft Store – und Apps, die als Webansicht dargestellt werden – die Desktop-Apps von Claude und ChatGPT, das neue Outlook, Visual Studio Code, Discord, Slack, Signal, WhatsApp für Windows, Spotify sowie echte Webseiten – unterscheiden sich in dieser Hinsicht erheblich. Wo eine App ihren neuen Inhalt nicht als zugänglichen Text bereitstellt, kann das Add-on ihn nicht melden.
- **Es zählt nur, was ein Fenster gerade preisgibt.** Lange Listen – Chatverläufe, Dateilisten, Suchergebnisse – existieren meist nur als die Handvoll Zeilen, die gerade angezeigt werden. Das Add-on kann Einträge, die aus dem sichtbaren Bereich gescrollt sind, nicht sehen, genauso wenig wie sehende Nutzer, und ein minimiertes Fenster gibt seinen Inhalt je nachdem, wie die betreffende App programmiert ist, womöglich gar nicht mehr preis, bis Sie es wiederherstellen.

Wenn Sie über häufige Aktualisierungen einer App informiert werden müssen, die Sie im Hintergrund verwenden, ist es meist zuverlässiger und einfacher, die App selbst so einzurichten, dass sie Ihnen Benachrichtigungen sendet, sofern sie das kann. Außerdem zeigt eine App, die Sie in den Infobereich der Taskleiste minimieren, kein sichtbares Fenster mehr an, sodass das Add-on sie nicht mehr verfolgen kann. Wenn das Symbol im Infobereich jedoch nützliche Informationen als Text bereitstellt, können Sie das Symbol selbst verfolgen.

## Mitwirken

Wenn Sie zur Entwicklung des Add-ons beitragen möchten, indem Sie Übersetzungen bereitstellen, Fehler melden oder einen Pull Request öffnen, und wissen, wie das geht, können Sie [das im GitHub-Repository des Add-ons tun](https://github.com/4sensegaming/background-content-tracker). Alle Beiträge sind willkommen und werden geschätzt.

## Änderungsprotokoll

### Version 1.0, 12.10.2026
* Erste Veröffentlichung
