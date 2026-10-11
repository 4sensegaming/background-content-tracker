# Background Content Tracker

* Author: Lukáš Hosnedl
* Minimum NVDA version: 2026.1
* Last tested NVDA version: 2026.2

**Created by AI, designed and thoroughly tested by humans.**

## Description

Background Content Tracker tracks a window or a single control and lets you know as soon as new content appears in it. You can carry on working in one window while the add-on keeps an eye on another.

While sighted people work in one window, they notice out of the corner of their eye when a pop-up appears or something changes in a window beside it, and can judge whether it needs attention now or later. NVDA can announce alerts and live regions, but usually only while the relevant window is in the foreground, so changes that happen while you are working elsewhere are easy to miss.

Background Content Tracker gives you this awareness: you choose what to track and how you want to be told, and NVDA notifies you when the content changes, without you having to move away from what you were doing.

This add-on is a very powerful and customizable tool that can essentially turn inaccessible windows or controls into talking live regions that work everywhere. For example, it works surprisingly well with:

- Brief, quickly changing dynamic messages in a single list, text area or NVDA object,
- As well as Electron apps like the new ChatGPT for Windows that leave a lot to be desired in terms of accessibility, which can stay silent for long periods of time and then start dumping large chunks of text that could be hard to locate otherwise.

However, the add-on will most likely be appreciated only by power users who feel the need to increase their speed and efficiency at work, such as:

- Team developers,
- Those who routinely use paid AI services or local models to create something substantial,
- Or those working in partially or fully automated corporate workflows involving several tasks at once.

If you need it, you probably know it by now. Others might find it overwhelming or confusing.

## Usage

You build a list of targets to track — whole windows, or individual controls such as a textbox or a chat's message list — and the add-on notifies you whenever new content appears in any of them. You can track several targets at once, and start or stop tracking each one independently.

### Example scenarios

- **Waiting for a long-running task in another app.** You set an AI assistant such as Claude working on a task and, rather than waiting on that window, you switch elsewhere to get on with something else. The add-on tracks the assistant's window and tells you as soon as new output appears, so you know it has replied without having to switch back to check again and again.
- **Keeping an eye on a web page while you type elsewhere.** You are typing in a chat such as WhatsApp while a web page sits open beside it. When that background page updates, the add-on lets you know — so you catch it just as a sighted person would.

### A typical workflow

1. Go to the window or control you want to track: focus it, point the mouse at it, or move the navigator object or review cursor to it.
2. Start tracking it, either with the matching [keystroke](#keystrokes) or by choosing it from the [target menu](#the-target-menu).
3. Switch to whatever you want to work on. When new content appears in the tracked target, NVDA notifies you in the way you have [configured](#global-settings).
4. Stop tracking a target when you no longer need it, or clear the whole list of targets at once.

## Keystrokes

The add-on is operated through a single **layered command**: you press a prefix keystroke, release it, and then press one more key to choose what to do. Nothing happens on the prefix by itself, so the add-on commands never get in the way of NVDA or other apps.

The default prefix is NVDA+; (the semicolon key, to the right of L on the home row).

When you press the prefix, the add-on opens a **virtual overlay**. While the overlay is open, every key you press is treated as one of the commands below. Opening and closing the overlay never moves focus — it stays exactly where it was, so the add-on commands never disturb what you are doing.

After pressing the prefix, press one of the following keys:

- `h` — **help**: briefly explains what every key available in the overlay does. Press twice to view the help text in a browseable message dialog.
- `f1` — **open this documentation** in the default web browser. This command is contextual: it jumps to this chapter in the overlay, to the [target menu](#the-target-menu) chapter when you are in the menu, to the [global settings](#global-settings) chapter when the settings dialog is open, and so on.
- `w` — start or stop tracking the current **window**.
- `f` — start or stop tracking the control that currently has keyboard **focus**.
- `m` — start or stop tracking the control under the **mouse pointer**.
- `n` — start or stop tracking the current **navigator object** (where the review cursor is).
- `t` — open the **[target menu](#the-target-menu)**.
- `1` to `0` — **speak information about a target** by its position in the list (see below). Press the same number a second time to set focus to that target.
- `space` or `enter` — the same as the number keys, but always for the **most recently added** target: press once to hear about it, twice to set focus to it.
- `control`+a number (`1` to `0`) — **stop tracking** the target in that slot.
- `alt`+a number (`1` to `0`) — **open the [target menu](#the-target-menu)** for the target in that slot directly.
- `backspace` — **stop tracking the most recently added** target.
- `delete` — **stop tracking all targets** (clear the whole list at once).
- `p` — **pause or resume** all tracking (this toggles the [*Enable tracking*](#enable-tracking-checkbox-enabled-by-default) switch).
- `s` — open the add-on's **[settings](#global-settings)** (the same panel as NVDA menu → Preferences → Settings → Background Content Tracker).
- `i` — open NVDA's **Input Gestures** dialog directly to the Background Content Tracker category, so you can rebind the prefix without hunting for it in the menus.
- `escape` — **close the overlay** without doing anything else.

The window, focus, mouse and navigator commands are toggles: press one once to add that target to the list, and press it again to remove it as long as it's still the current window, has focus, etc. You can track any number of targets at the same time.

Those four commands also take `shift` and `control`, which say how the target you are adding is to be tracked: `shift` remembers that one target, `control` reads it even while its own app is in the foreground, and holding both does both. These are [per-target settings](#target-settings), set on that specific target as it is added instead of being inherited from the [global settings](#global-settings) or configured in the [target menu](#the-target-menu) later, and they don't change the global setting. A press that *stops* tracking the target rather than adding it simply ignores the modifiers. The modifiers are only useful if you have the [**remember targets**](#remember-targets-checkbox-disabled-by-default) or [**track even foreground targets**](#track-even-foreground-targets-checkbox-disabled-by-default) options disabled globally but you need this behavior for this one target specifically.

The number keys refer to **slots** in your target list, not to fixed targets. By default, `1` is the most recently added target, `2` the one added before it, and so on up to `0` — the tenth slot. The [**Target slot sorting** setting](#target-sorting) can put the slots in a different order, such as oldest target first, most recently changed target first, or alphabetically. If a target is removed — because you stopped tracking it or it no longer exists — the targets after it move up to fill the gap, so `2` always speaks whatever is currently second in the list.

When a target is present, by default the add-on speaks its role and name, and the changed content of the target, for example *Window: Claude, Editing readme.md* or *List: Message list, You said: Okay*. The level of detail of these announcements can be [configured in the add-on's settings](#include-in-change-announcement-group).

You can change the prefix from NVDA's Input Gestures dialog (NVDA menu → Preferences → Input Gestures), where the add-on's command appears under the **Background Content Tracker** category. The follow-up keys are part of the layered command itself.

## The target menu

The **target menu** (the prefix followed by `t`) lists all current targets as ordered menu items, so you don't have to remember the target's current position in the list or any of the other keys.

Each item names exactly what it acts on, for example *Window: Claude, 3 minutes ago, 3 tasks running*. A target that does not exist at the moment — a remembered one whose window has not been reopened yet — reads *not found* in place of the time and the content, and stays in the menu, because you can still stop it, change its settings, or leave it there and wait for it to come back. The order in which the targets are listed respects the [**Target menu sorting** setting](#target-sorting).

Every target is a submenu. When you expand it, you can:

- *Stop tracking* it,
- *Set focus* to it (unless it's already focused),
- Change its [*Target settings*](#target-settings) in a submenu that holds that one target's own copy of the settings that can be set per target,
- Or browse that target's [history of **recent changes**](#history-of-recent-changes).

Anything you are already tracking appears first in the menu, so you can quickly move to the target you want, or stop tracking it. Below that are the targets you can start tracking from your current location (window, focus, mouse pointer, or navigator object). The item to stop tracking all current targets is at the end of the menu.

### Target settings

Each item in *Target settings* is a checkbox, and what it shows is what the target actually does: its own value where you have given it one, and the [global setting](#global-settings) everywhere else. Ticking or unticking one gives that target its own value for that one setting, effective immediately; every other setting still follows the global.

- *Interrupt previous speech when announcing a new change* is displayed for all targets, as long as the [global *Announce* option](#announce-checkbox-enabled-by-default) is enabled.
- The *Ignore progress bars*, *Ignore counters, steppers and timers*, *Consider changed title a disappeared target* and *Ignore known generic controls* options are displayed only for window targets.
- *Track this target even in the foreground* is displayed for all targets.
- *Ignore the focused control* is displayed as long as the target is a window and it's also [set to be tracked even in the foreground](#track-even-foreground-targets-checkbox-disabled-by-default).
- *Remember this target* is displayed for all targets.
- *Forget this target when it disappears* is displayed just for a target that is being remembered.

Changing a [global setting](#global-settings) affects even existing targets unless that setting has been overridden locally. The settings panel sets globals only: nothing you do there takes a target's own value away from it. Stopping the target and adding it again, or forgetting a remembered target, is what clears all local values.

### History of recent changes

This submenu lists as many recent changes that occurred in the given target as you have set for the [*Keep history of recent changes per target*](#keep-history-of-recent-changes-per-target-edit-50-by-default) setting, in the order governed by [*change history sorting*](#target-sorting), with exactly the configured [level of detail](#include-in-menu-descriptions-group). If *Keep history of recent changes per target* is set to 0, the submenu is not displayed at all. Older changes beyond that number are removed. Note that this setting is global only. Choosing any item in this submenu opens that change in a browseable message dialog.

The history disappears when you stop tracking a target, when a target is automatically [forgotten after it disappears](#forget-remembered-targets-when-they-disappear-checkbox-disabled-by-default), or at the end of the session, and is not saved anywhere. When [tracking is paused](#enable-tracking-checkbox-enabled-by-default), the history is not updated either.

## Global settings

The add-on's options live in the **Background Content Tracker** category in NVDA's Settings dialog (NVDA menu → Preferences → Settings). The add-on supports multiple configuration profiles.

Related options are grouped. All available options are described below, in the order they appear on the panel. Top-level options and whole groups are level 3 headings; individual options within groups are level 4 headings.

### **Enable tracking** (checkbox, enabled by default)

When disabled, the add-on stops notifying you but keeps your entire target list and all of your settings, so you can silence it (for instance during a meeting) and later switch it back on exactly as it was. This is the same switch toggled by the [pause/resume keystroke](#keystrokes). This switch is not saved: tracking is always enabled when NVDA starts.

### **Tracking interval** (edit, 1 by default)

Only accepts whole numbers. Sets how often the add-on should query all existing targets for changes, in seconds. 0 means never announce changes to targets automatically, only display them in the [target menu](#the-target-menu).

### **Changes to announce at once (background targets only)** (edit, 5 by default)

Only accepts whole numbers. Sets how many consecutive changes to the same target the add-on should announce in a row before you have to refocus the target and then switch elsewhere again for further changes to be announced. 0 means announce every change.

This option never affects foreground targets. If [tracking is enabled even for foreground targets](#track-even-foreground-targets-checkbox-disabled-by-default), then all changes are always announced for those.

### **Keep history of recent changes per target** (edit, 50 by default)

Only accepts whole numbers. Sets how many recent changes should be kept in the [history per target](#history-of-recent-changes). Older changes are dropped. 0 means no history.

For remembered targets that have disappeared, the history is also remembered and remains available until the target is removed or until the end of the session.

### **Track even foreground targets** (checkbox, disabled by default)

Normally, a target is only read while you are working somewhere else, so once its own app comes to the foreground, the add-on leaves it alone. When enabled, new content for a target is announced even when you are currently working with that window or single control.

Note that if the target app talks to screen readers directly (via ARIA live regions or other accessibility events), the same announcements may sometimes be reported twice while working in its window — once from the app itself and once from the add-on. In that case, to hear only the app's own announcements, you can untick *Track this target even in the foreground* in that target's [Target settings](#target-settings), pause tracking temporarily, or remove the target and add it back later. To hear only the add-on's announcements, disable reporting of dynamically changed content in NVDA (NVDA+5 by default).

### **Overlay timeout** (edit, 10 by default)

Only accepts whole numbers. Sets how many seconds without a key press must pass before the overlay closes on its own. 0 means that the overlay never closes by itself: it stays open until you close it with escape or a command that takes focus somewhere else, such as opening [the target menu](#the-target-menu).

### Target sorting

There are three sets of radio buttons, one after the other: *Target slot sorting*, *Target menu sorting* and *Change history sorting*. All of them offer the same options (with a few exceptions) listed below, and can be set either in sync or independently of one another. They determine in which order targets are placed into the ten available numbered slots (see [Keystrokes](#keystrokes)), displayed in the [target menu](#the-target-menu) or ordered in the [per-target history of recent changes](#history-of-recent-changes) respectively.

- *Newest target / change first* (set by default for all sorting types)
- *Oldest target / change first*
- *Most recently changed target first* (not offered for history sorting)
- *Least recently changed target first* (not offered for history sorting)
- *Alphabetically, A to Z*
- *Alphabetically, Z to A*

### **Remember targets** (checkbox, disabled by default)

When enabled, your target list is kept between NVDA restarts, and the add-on re-attaches to a target whenever it reappears. For example, it tracks the assistant's window every time that window opens, without you setting it up again. When disabled, the target list starts empty in each session, and only your settings are stored.

### **Forget remembered targets when they disappear** (checkbox, disabled by default)

Determines whether a remembered target should be forgotten when it no longer exists — you closed the target's window or it disappeared by itself. When enabled, you will have to start tracking the same target manually again every time it disappears. Any targets that you stop tracking manually are always forgotten, regardless of how this option is set.

### **Window tracking behavior** (group)

The options in this group refine how the add-on should announce changes in targets that are whole windows.

#### **Ignore progress bars** (checkbox, enabled by default)

When enabled, this option suppresses announcements of changing progress bar controls in the window. NVDA itself can speak and/or beep native progress bars, even in the background, so you may not want this add-on to spam you with double-reporting a constantly changing progress bar in a specific app.

#### **Ignore counters, steppers and timers** (checkbox, enabled by default)

When enabled, the add-on watches for a control that changes in nothing but numeric values — a timer or countdown ticking every second, a step or item counter, a percentage, like the Claude app counting how long it took the model to think. These controls can often be more annoying than helpful, as they do not provide any useful information by themselves and, more importantly, don't convey any real changes — they just indicate that the task is still in progress. The moment such a control is caught, it falls silent and stays silent for as long as the target is tracked.

#### **Consider changed title a disappeared target** (checkbox, disabled by default)

When enabled, if the title of a window being tracked changes, the add-on will consider it a different window and thus act as if the original target has disappeared, even though the physical window is still the same one in the system.

#### **Ignore known generic controls** (checkbox, enabled by default)

When enabled, this option suppresses announcements of generic controls, like a window's "Minimize" button changing to "Maximize" and vice versa. This includes:

- The application's menu bar (usually reached with the alt key)
- The "Minimize", "Restore", "Maximize" and "Close" buttons
- "OK", "Cancel", "Close", "Abort", "Retry", "Continue", "Next", "Previous", "Back", "Finish" and "Not now" buttons
- And "Yes" and "No" buttons.

#### **Ignore the focused control when tracking the foreground window** (checkbox, enabled by default)

This option is only available when [Track even foreground targets](#track-even-foreground-targets-checkbox-disabled-by-default) is enabled, since it only makes a difference for the window that is being read while you are currently working in it. Background windows or single-control targets are not affected either way. When enabled, the control that currently has focus is never announced as a change, so for example the characters you type into an edit field are not read as new content.

### **When target changes** (group)

What happens when new content appears in a target.

#### **Beep** (checkbox, enabled by default)

Plays a tone when the target has changed.

#### **Announce** (checkbox, enabled by default)

Announces what changed where, for example "Window: Claude" or "List: Message list". The level of detail of the announcement can be further customized below.

#### **Interrupt previous speech when announcing a new change** (checkbox, disabled by default)

This option is only available when the [**Announce**](#announce-checkbox-enabled-by-default) checkbox above is enabled. When enabled, a change announcement cuts off whatever NVDA is saying at the moment and is spoken right away. When disabled, it waits until NVDA has finished speaking.

#### **Repeat target name for consecutive changes in the same target** (checkbox, enabled by default)

This option is only available when [verbal announcements as such](#announce-checkbox-enabled-by-default) are enabled. When enabled, it includes the target's name in every single change announcement, even if multiple consecutive changes in a row occurred in the same target. When disabled, the target's name is announced only for the first consecutive change, as well as when the last announced change occurred in a different target.

### **Beep parameters** (group)

The options in this group are only available when the [**Beep**](#beep-checkbox-enabled-by-default) checkbox above is enabled.

#### **Duration** (edit, 50 by default)

Only accepts whole numbers. Sets how long the beep should be, in milliseconds.

#### **Pitch** (edit, 440 by default)

Only accepts whole numbers. Sets at what frequency the beep should play, in hertz.

#### **Test** (button)

Plays a test beep with the currently set parameters, so you can verify whether it sounds the way you want it to.

### **Include in change announcement** (group)

The options in this group are only available when the [**Announce**](#announce-checkbox-enabled-by-default) checkbox above is enabled. They determine exactly what the change announcement consists of.

#### **Target type** (checkbox, enabled by default)

Whether the type of the target (for example **window**, **list** or **textbox**) is announced.

#### **Changed content** (checkbox, enabled by default)

Whether the new content in the target after the most recent change is announced.

### **Include in menu descriptions** (group)

The options in this group specify the level of detail you want to hear when browsing the [target menu](#the-target-menu). They also affect how entries in the [history of changes](#history-of-recent-changes) for individual targets are written.

#### **Target type** (checkbox, enabled by default)

Whether the type of the target (for example **window**, **list** or **textbox**) is displayed in the description of the target's respective menu item.

#### **Time since last change** (checkbox, enabled by default)

Whether the relative time since the last change occurred in the target (for example 3 minutes ago) is displayed in the description of the target's respective menu item.

#### **Changed content** (checkbox, enabled by default)

Whether the new content in the target after the most recent change is displayed in the description of the target's respective menu item.

## Known limitations

- **Background browser tabs are never tracked.** A web browser only keeps the tab you are looking at readable. To keep an eye on a page while you work elsewhere, open it in a separate window rather than leaving it on a background tab. Sighted users can't see a background tab either.
- **Some apps reveal very little while not in the foreground.** How much an app tells a screen reader about non-focused content is exclusively controlled by the app itself. Modern UIA apps — Terminal, Settings, Calculator, Photos and most apps from the Microsoft Store — and apps that are rendered as web views — the Claude and ChatGPT desktop apps, the new Outlook, Visual Studio Code, Discord, Slack, Signal, WhatsApp for Windows, Spotify, as well as actual websites — differ considerably in this respect. Where an app does not expose its new content as accessible text, the add-on cannot report it.
- **Only what a window currently reveals counts.** Long lists — chat history, file lists, search results — usually exist only as the handful of rows that happen to be displayed. The add-on cannot see entries that are scrolled out of view, just like sighted users can't, and a minimized window may stop revealing its contents altogether until you restore it, depending on how the app in question is programmed.

If you need to know about frequent updates from an app that you use in the background, it's usually more reliable and straightforward to configure the app itself to send you notifications, if the app can do that. Also, if you minimize the app to the system tray, it no longer displays a visible window, so the add-on can't track it anymore. However, if the tray icon does expose useful information as text updates that are accessible, you can indeed track the icon itself.

## Contributing

If you would like to contribute to the add-on's development by providing translations, reporting issues or opening a pull request, and you know how to, you can [do so in its GitHub repository](https://github.com/4sensegaming/background-content-tracker). All contributions are welcome and appreciated.

## Changelog

### Version 1.0, 2026/10/12
* Initial release