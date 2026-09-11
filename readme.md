# Background Content Tracker

* Author: Lukáš Hosnedl
* Minimum NVDA version: 2026.1
* Last tested NVDA version: 2026.2

**Created by AI, designed and thoroughly tested by humans.**

## Description

Background Content Tracker tracks a window or a single control that is **not** currently focused or in the foreground, and lets you know as soon as new content appears in it. You can carry on working in one window while the add-on keeps an eye on another, and tells you the moment something there changes.

While sighted people work in one window, they notice out of the corner of their eye when a pop-up appears or something changes in a window beside it, and can judge whether it needs attention now or later. NVDA can announce alerts and live regions, but usually only while the relevant window is in the foreground, so changes that happen while you are working elsewhere are easy to miss.

Background Content Tracker gives you this awareness: you choose what to track and how you want to be told, and NVDA notifies you when the content changes, without you having to move away from what you were doing.

This add-on will most likely be appreciated only by power users who feel the need to increase their speed and efficiency at work, such as team developers, those who routinely use paid AI services or local models to create something substantial, or those working in partially or fully automated corporate workflows involving several tasks at once. If you need it, you probably know it right away after reading the above description. It's possible that others might feel overwhelmed or confused when using it instead.

## Usage

You build a list of targets to track — whole windows, or individual controls such as a textbox or a chat's message list — and the add-on notifies you whenever new content appears in any of them. You can track several targets at once, and switch each one on or off independently.

### Example scenarios:

- **Waiting for a long-running task in another app.** You set an AI assistant such as Claude working on a task and, rather than waiting on that window, you switch elsewhere to get on with something else. The add-on tracks the assistant's window and tells you as soon as new output appears, so you know it has replied without having to switch back to check again and again.
- **Keeping an eye on a web page while you type elsewhere.** You are typing in a chat such as WhatsApp while a web page sits open beside it. When that background page updates, the add-on lets you know — so you catch it just as a sighted person would glance across.

### A typical workflow:

1. Go to the window or control you want to track: focus it, point the mouse at it, or move the navigator object or review cursor to it.
2. Start tracking it, either with the matching [keystroke](#keystrokes) or by choosing it from the [target menu](#the-target-menu).
3. Switch to whatever you want to work on. When new content appears in the tracked target, NVDA notifies you in the way you have [configured](#settings) — a beep, the target name, or the changed content.
4. Stop tracking a target when you no longer need it, or clear the whole list of targets at once.

## Keystrokes

The add-on is operated through a single **layered command**: you press a prefix keystroke, release it, and then press one more key to choose what to do. Nothing happens on the prefix by itself, so the add-on commands never get in the way of NVDA or other apps.

The default prefix is NVDA+; (the semicolon key, to the right of L on the letters row).

When you press the prefix, the add-on opens a **virtual overlay** and announces "Overlay opened", followed by "Tracking paused" if tracking is currently paused. While the overlay is open, every key you press is treated as one of the commands below. Opening and closing the overlay never moves focus — it stays exactly where it was, so the add-on commands never disturb what you are doing. Whenever the overlay closes, the add-on announces "Overlay closed".

After pressing the prefix, press one of the following keys:

- `h` — **help**: reads out every key available in the overlay and briefly explains what each one does. Press the key twice to view the help text in a browseable message dialog.
- `w` — start or stop tracking the current **window** (any change in the whole foreground window).
- `f` — start or stop tracking the control that currently has keyboard **focus**.
- `m` — start or stop tracking the control under the **mouse pointer**.
- `n` — start or stop tracking the current **navigator object** (where the review cursor is).
- `t` — open the **[target menu](#the-target-menu)**.
- `1` to `0` — **speak information about a target** by its position in the list (see below). Press the same number a second time to set focus to that target.
- `space` or `enter` — the same as the number keys, but always for the **most recently added** target: press once to hear about it, twice to set focus to it.
- `control`+a number (`1` to `0`) — **stop tracking** the target in that slot.
- `backspace` — **stop tracking the most recently added** target.
- `delete` — **stop tracking all targets** (clear the whole list at once).
- `p` — **pause or resume** all tracking (this flips the *Enable background content tracking* switch described under [Settings](#settings)).
- `s` — open the add-on's **[settings](#settings)** (the same panel as NVDA menu → Preferences → Settings → Background Content Tracker).
- `i` — open NVDA's **Input Gestures** dialog, so you can rebind the prefix without hunting for it in the menus.
- `escape` — **close the overlay** without doing anything else.

The window, focus, mouse and navigator commands are toggles: press one once to add that target to the list, and press it again to remove it. You can track any number of targets at the same time.

Those four commands also take `shift` and `control`, which say how the target you are adding is to be tracked: `shift` remembers that one target, `control` reads it even while its own app is in the foreground, and holding both does both. These are [per-target settings](#global-and-per-target-settings), set on that specific target as it is added instead of via inheriting the global [settings](#settings) or via [the target menu](#the-target-menu) later, and they don't change the global setting. A press that *stops* tracking simply ignores the modifiers.

The number keys refer to **slots** in your target list, not to fixed targets. By default, `1` is the most recently added target, `2` the one added before it, and so on up to `0`, the tenth slot. The [**Target sorting** setting](#settings) can put the slots in a different order, such as oldest target first, most recently changed target first, or alphabetically. If a target is removed — because you stopped tracking it or it no longer exists — the targets after it move up to fill the gap, so `2` always speaks whatever is currently second in the list. If there is currently no valid target in the slot you pressed, the add-on says for example "No target in slot 2".

When a target is present, by default the add-on speaks its name and role, and the changed content of the target, for example *Window: Claude, Editing readme.md* or *Listbox: Message list, You said: Okay.*. The level of detail of these announcements can be configured in the add-on's [settings](#settings).

You can change the prefix from NVDA's Input Gestures dialog (NVDA menu → Preferences → Input Gestures), where the add-on's command appears under the **Background Content Tracker** category. The follow-up keys are part of the layered command itself.

## The target menu

The **target menu** (the prefix followed by `t`) lists all current targets as ordered menu items, so you don't have to remember the target's current position in the list or any of the other keys.

Each item names exactly what it acts on, for example *Window: Claude, 3 minutes ago, 3 tasks running*. A target that does not exist at the moment — a remembered one whose window has not been reopened yet — reads *not found* in place of the time and the content, and stays in the menu, because you can still stop it, change its settings, or leave it there and wait for it to come back. The order in which the targets are listed respects the [**Target sorting** setting](#settings).

Every target is a submenu. When you expand it, you can *Stop tracking* it, *Set focus* to it, or change its *Target settings* in a submenu which holds that one target's own copy of the settings that can be [set per target](#global-and-per-target-settings).

Each item in *Target settings* is a check box, and what it shows is what the target actually does: its own value where you have given it one, and the global setting everywhere else. Ticking or unticking one gives that target its own value for that one setting, effective immediately; every other setting still follows the global.

- *Interrupt previous speech when announcing a change* is displayed at the top of *Target settings* for all targets, as long as the global *Announce* option is enabled.
- The *Ignore progress bars*, *Ignore counters, steppers and timers*, *Consider changed title a disappeared target* and *Ignore known generic controls* options come next for window targets.
- *Track this target even in the foreground* comes next, displayed for all targets.
- *Ignore the focused control* is after that as long as the target is a window and it's also set to be tracked even in the foreground.
- *Remember this target* is displayed for all targets.
- *Forget this target when it disappears* is displayed just for a target that is being remembered.

Anything you are already tracking appears first in the menu, so you can move to the target of your interest or stop tracking it quickly. Below that are the targets you can start tracking from your current location (window, focus, mouse pointer, or navigator object). The item to stop tracking all current targets is at the end of the menu.

## Important add-on messages

- **Tracking a new target** — for example "Tracking window: Claude". You also hear this whenever a remembered target reappears later, after launch.
- **No longer tracking a target** — for example "Stopped tracking listbox: Message list". You hear this when you stop tracking a target yourself, and when a target disappears and the add-on stops tracking it as a result: always for a target that is not remembered, and for a remembered one when it is set to be forgotten when it disappears.
- **A target disappearing** — for example "Target disappeared: Claude". You hear this when a remembered target disappears but is kept in the list, so it's tracked again as soon as it reappears.

Neither of these is announced for a target that disappears while it's in the foreground — for example, when you close its window yourself — because you already know about it. The one exception is a remembered target that is forgotten because it disappeared: you still hear "Stopped tracking", since closing it also means it won't be tracked again, which you may not have intended.

When NVDA starts and every time you resume previously paused tracking, the remembered targets are looked for and reported together, as "Found 7 remembered targets", or as "Found 6 of 9 remembered targets" when the rest have not appeared yet. When fewer than five are found, their names follow, for example "Found 3 remembered targets: Claude, ChatGPT Classic, Gemini" or "Found 1 of 3 remembered targets: Claude". Any that turn up later announce themselves individually. The add-on announces "No remembered targets found" instead if none of the remembered targets are there at the moment.

## Global and per-target settings

Most of the add-on's options are **global**: you set them in the [settings](#settings) panel, and every target follows them. Nine of them can also be set on a **single target**, which then follows its own value for that one setting and keeps following the global for all the rest:

- *Interrupt previous speech when announcing a change*
- *Ignore progress bars*
- *Ignore counters, steppers and timers*
- *Consider changed title a disappeared target*
- *Ignore known generic controls*
- *Track even foreground targets*
- *Ignore the focused control when tracking the foreground window*
- *Remember targets*
- *Forget remembered targets when they disappear*

There are two ways to give one target its own value. In the [target menu](#the-target-menu), open that target's *Target settings* submenu and tick or untick what you want. Or hold `shift`, `control` or both while adding a target with the [`w`, `f`, `m` or `n` keystrokes](#keystrokes), which gives the target being added its own *Remember targets* and *Track even foreground targets* respectively.

Changing a setting affects even existing targets unless that setting has been overridden locally. The settings panel sets globals only: nothing you do there takes a target's own value away from it. Stopping the target and adding it again or forgetting a remembered target is what clears all local values.

## Settings

The add-on's options live in the **Background Content Tracker** category in NVDA's Settings dialog (NVDA menu → Preferences → Settings). The add-on supports multiple configuration profiles.

Related options are grouped. All available options are described below, in the order they appear on the panel. Top-level options and whole groups are level 3 headings, individual options within groups are level 4 headings.

### **Enable tracking** (checkbox, enabled by default)

When disabled, the add-on stops notifying you but keeps your entire target list and all of your settings, so you can silence it (for instance during a meeting) and later switch it back on exactly as it was. This is the same switch toggled by the [pause/resume keystroke](#keystrokes).

### **When target changes** (group)

What happens when new content appears in a target.

#### **Beep** (checkbox, enabled by default)

Plays a tone when the target has changed.

#### **Announce** (checkbox, enabled by default)

Announces what changed where, for example "Window: Claude" or "Listbox: Message list". The level of detail of the announcement can be further customized below.

#### **Interrupt previous speech when announcing a change** (checkbox, disabled by default)

This option is only available when the **Announce** checkbox above is enabled. When enabled, a change announcement cuts off whatever NVDA is saying at the moment and is spoken right away. When disabled, it waits until NVDA has finished speaking.

#### **Tracking interval** (edit, 1 by default)

Only accepts whole numbers. Sets how often the add-on should query all existing targets for changes, in seconds. 0 means never announce changes to targets automatically, only display them in the [target menu](#the-target-menu).

#### **Changes to announce at once (background targets only)** (edit, 5 by default)

Only accepts whole numbers. Sets how many consecutive changes to the same target the add-on should announce in a row before you have to refocus the target and then switch elsewhere again for further changes to be announced. 0 means announce any single change every time. This option never affects foreground targets. If tracking is enabled even for foreground targets, then all changes are always announced for those.

#### **Track even foreground targets** (checkbox, disabled by default)

Normally, a target is only read while you are working somewhere else, so once its own app comes to the foreground, the add-on leaves it alone. When enabled, new content for a target is announced even when you are currently working with that window or single control, regardless of the value of the option above.

### **Window tracking behavior** (group)

The options in this group refine how the add-on should announce changes in targets that are whole windows.

#### **Ignore progress bars** (checkbox, enabled by default)

When enabled, this option suppresses announcements of changing progress bar controls in the window. NVDA itself can speak and/or beep native progress bars, even in the background, so you may not always want this add-on to spam you with double-reporting a constantly changing progress bar from a specific app.

#### **Ignore counters, steppers and timers** (checkbox, enabled by default)

When enabled, the add-on watches for a control that changes in nothing but numeric values — a timer or countdown ticking every second, a step or item counter, a percentage, like the Claude app counting how long it took the model to think. These controls can often be more annoying than helpful, as they do not provide any useful information by themselves and, more importantly, don't convey any real changes — they just indicate that the task is still in progress. The moment such a control is caught doing that, it falls silent and stays silent for as long as the target is tracked.

#### **Consider changed title a disappeared target** (checkbox, disabled by default)

When enabled, if the title of a window being tracked changes, the add-on will consider it a different window and thus act as if the original target has disappeared, even though the physical window is still the same one in the system.

#### **Ignore known generic controls** (checkbox, enabled by default)

When enabled, this option suppresses announcements of generic controls, like a "Minimize" button of a window changing to "Maximize" and vice versa. This includes the applications menu (usually opened with the alt key), the "Minimize", "Restore" and "Maximize" buttons, "OK", "Cancel", "Close", "Abort", "Retry", "Continue", "Next" and "Not now" buttons, and "Yes" and "No" buttons.

#### **Ignore the focused control when tracking the foreground window** (checkbox, enabled by default)

This only makes a difference for a window that is read while you are working in it, which is what the option to track even foreground targets allows. In other words, this option affects only a whole window that is also set to be read in the foreground. Background windows or single control targets are not affected either way. When enabled, the control you are focused on is never announced as a change, so for example the characters you type into an edit field are not being read as new content.

### **Beep parameters** (group)

The options in this group are only available when the **Beep** checkbox above is enabled.

#### **Duration** (edit, 50 by default)

Only accepts whole numbers. Sets how long the beep should be, in milliseconds.

#### **Pitch** (edit, 440 by default)

Only accepts whole numbers. Sets at what frequency the beep should play, in hertz.

#### **Test** (button)

Plays a test beep with the currently set parameters, so you can verify whether it sounds the way you want it to.

### **Include in change announcement** (group)

The options in this group are only available when the **Announce** checkbox above is enabled. They determine exactly what the target changed announcement consists of. As long as the verbal announcement itself is enabled, the name of the target (for example Claude or Message list) is always included.

#### **Target type** (checkbox, enabled by default)

Whether the type of the target (for example **window**, **listbox** or **textbox**) is announced.

#### **Changed content** (checkbox, enabled by default)

Whether the new content in the target after the most recent change is announced.

### **Include in menu descriptions** (group)

The options in this group specify the level of detail you want to hear when browsing the [target menu](#the-target-menu).

#### **Target type** (checkbox, enabled by default)

Whether the type of the target (for example **window**, **listbox** or **textbox**) is displayed in the description of the target's respective menu item.

#### **Time since last change** (checkbox, enabled by default)

Whether the relative time since the last change occurred in the target (for example 3 minutes ago) is displayed in the description of the respective target's menu item.

#### **Changed content** (checkbox, enabled by default)

Whether the new content in the target after the most recent change is displayed in the description of the target's respective menu item.

### **Overlay timeout** (edit, 10 by default)

Only accepts whole numbers. This determines how many seconds without a key press must pass before the overlay closes on its own. Setting this to 0 means that the overlay never closes by itself: it stays open until you close it with escape or a command that takes focus somewhere else.

### **Target sorting** (group)

There are two groups of radio buttons, one after the other: *Target slot sorting* and *Target menu sorting*. Both offer the same options listed below, and both can be set to exactly one of the available options at a time, either in sync or independently from one another. They determine in which order new targets are placed into the ten available numbered slots (see [Keystrokes](#keystrokes)) and displayed in the [target menu](#the-target-menu) respectively.

- *Newest target first* (set by default for both sorting types)
- *Oldest target first*
- *Most recently changed target first*
- *Least recently changed target first*
- *Alphabetically, A to Z*
- *Alphabetically, Z to A*

### **Remember targets** (checkbox, disabled by default)

When enabled, your target list is kept between NVDA restarts, and the add-on re-attaches to a target whenever it reappears. For example, it tracks the assistant's window every time that window opens, without you setting it up again. When disabled, the target list starts empty in each session, and only your settings are stored.

### **Forget remembered targets when they disappear** (checkbox, enabled by default)

Determines whether a remembered target should be forgotten when it no longer exists (you close the window or the specific control disappears from the window). When enabled, you will have to start tracking the same target manually every time if it ever disappeared while the add-on was tracking it. Any targets that you stop tracking manually are always forgotten, regardless of how this option is set.

## Known limitations

- **Background browser tabs are never tracked.** A web browser only keeps the tab you are looking at readable. To keep an eye on a page while you work elsewhere, open it in a separate window rather than leaving it on a background tab. This behaves the same for sighted users.
- **Some apps reveal very little while not in the foreground.** How much an app tells a screen reader about non-focused content is exclusively controlled by the app itself. Modern UIA apps — Terminal, Settings, Calculator, Mail, Photos and most apps from the Microsoft Store — and apps that are rendered as web views — the Claude desktop app, Visual Studio Code, Discord, Slack, Signal, WhatsApp for Windows, Spotify, as well as web browsers themselves — differ considerably in this respect. Where an app does not expose its new content as visible text, the add-on cannot report it.
- **Only what a window currently reveals counts.** Long lists — chat history, file lists, search results — usually exist only as the handful of rows that happen to be displayed. The add-on cannot see entries that are scrolled out of view, just like sighted users can't, and a minimized window often stops revealing its contents altogether until you restore it.

If you need to know about frequent updates from an app that you use in the background, it's usually more reliable and straightforward to configure the app itself to send you notifications, if the app can do that. Likewise, if you minimize the app to the system tray, it no longer displays a visible window, so the add-on can't track it anymore. However, if the tray icon does expose useful information as text updates that are accessible, you can in deed track the icon itself.

## Contributing

If you would like to contribute to the add-on's development by providing translations, reporting issues or opening a pull request, and you know how to, you can [do so in its GitHub repository](https://github.com/4sensegaming/background-content-tracker). All contributions are welcome and appreciated.

## Changelog

### Version 1.0, 2026/09/09
* Initial release