# Background Content Tracker

* Author: Lukáš Hosnedl
* Minimum NVDA version: 2026.1
* Last tested NVDA version: 2026.2

**Created by AI, designed and thoroughly tested by humans.**

## Description

Background Content Tracker tracks a window or a single control that you are **not** currently focused on, and lets you know as soon as new content appears in it. You can carry on working in one window while the add-on keeps an eye on another, and tells you the moment something there changes.

While sighted people work in one window, they notice out of the corner of their eye when a pop-up appears or something changes in a window beside it, and can judge whether it needs attention now or later. NVDA can announce alerts and live regions, but only while the relevant window is in the foreground, so changes that happen while you are working elsewhere are easy to miss.

Background Content Tracker gives you this awareness: you choose what to track and how you want to be told, and NVDA notifies you when the content changes — without moving your focus away from what you are doing.

## Usage

You build a list of targets to track — whole windows, or individual controls such as a textbox or a chat's message list — and the add-on notifies you whenever new content appears in any of them. You can track several targets at once, and switch each one on or off independently.

### Example scenarios:

- **Waiting for a long-running task in another application.** You set an AI assistant such as Claude working on a task and, rather than waiting on that window, you switch elsewhere to get on with something else. The add-on tracks the assistant's window and tells you as soon as new output appears, so you know it has replied without having to switch back to check again and again.
- **Keeping an eye on a web page while you type elsewhere.** You are typing in a chat such as WhatsApp while a web page sits open beside it. When that background page updates, the add-on lets you know — so you catch it just as a sighted person would glance across.

### A typical workflow:

1. Go to the window or control you want to track: focus it, point the mouse at it, or move the navigator object or review cursor to it.
2. Start tracking it, either with the matching [keystroke](#keystrokes) or by choosing it from the [target menu](#the-target-menu).
3. Switch to whatever you want to work on. When new content appears in the tracked target, NVDA notifies you in the way you have configured — a beep, the target name, or the changed content.
4. Stop tracking a target when you no longer need it, or clear the whole list of targets at once.

## Keystrokes

The add-on is operated through a single **layered command**: you press a prefix keystroke, release it, and then press one more key to choose what to do. Nothing happens on the prefix by itself, so the add-on commands never get in the way of NVDA or other applications.

The default prefix is NVDA+; (the semicolon key, to the right of L on the letters row).

When you press the prefix, the add-on opens a **virtual overlay** and announces "Overlay opened". The overlay is a mode rather than a one-off prompt: while it is open, every key you press is treated as one of the commands below, one command after another, until something closes it.

Exactly three things close it. Pressing `escape`; the timeout running out, which is ten seconds without a key press (you can change this delay in the add-on's [settings](#settings), or set it to 0 so that the overlay never closes on its own); and any command that takes your focus somewhere else — a dialog, the target menu, or a tracked target — which closes the overlay so that what you type there is not swallowed by it. Anything else leaves the overlay open, a mistyped key included: the add-on says "Unknown command. Press H once for help, twice to display the help as a browseable message." and waits for the next key, rather than costing you the command you actually meant to give. Opening and closing the overlay never moves your focus by itself — it stays exactly where it was, so the add-on commands never disturb what you are doing. Whenever the overlay closes, the add-on announces "Overlay closed".

After pressing the prefix, press one of the following keys:

- `h` — **help**: reads out every key available in the overlay and briefly explains what each one does. Press the key twice to view the help text in a browseable message dialog.
- `w` — start or stop tracking the current **window** (any change in the whole foreground window).
- `f` — start or stop tracking the control that currently has keyboard **focus**.
- `m` — start or stop tracking the control under the **mouse pointer**.
- `n` — start or stop tracking the current **navigator object** (where the review cursor is).
- `t` — open the **[target menu](#the-target-menu)**.
- `1` to `0` — **speak information about a target** by its position in the list (see below). Press the same number a second time within ten seconds, with no other key in between, to move your focus to that target.
- `space` or `enter` — the same as the number keys, but always for the **most recently added** target: press once to hear about it, again within ten seconds to move your focus to it.
- `control`+a number (`1` to `0`) — **stop tracking** the target in that slot.
- `backspace` — **stop tracking the most recently added** target.
- `delete` — **stop tracking all targets** (clear the whole list at once).
- `p` — **pause or resume** all tracking (this flips the *Enable background content tracking* switch described under [Settings](#settings)).
- `s` — open the add-on's **[settings](#settings)** (the same panel as NVDA menu → Preferences → Settings → Background Content Tracker).
- `i` — open NVDA's **Input Gestures** dialog, so you can rebind the prefix without hunting for it in the menus.
- `escape` — **close the overlay** without doing anything else.

The window, focus, mouse and navigator commands are toggles: press one once to add that target to the list, and press it again to remove it. You can track any number of targets at the same time.

Those four commands also take `shift` and `control`, which say how the target you are adding is to be tracked: `shift` remembers that one target, `control` reads it even while its own application is in the foreground, and holding both does both. These are the [per-target settings](#global-and-per-target-settings) of the same name, set on the target as it is added instead of afterwards in the target menu, and they never change the global setting. A press that *stops* tracking has no target to give them to, so the modifiers are simply ignored there.

The number keys refer to **slots** in your target list, not to fixed targets. By default, `1` is the target you started tracking first and `0` (the tenth slot) is the most recently added target; you can reverse this order under [Settings](#settings). If a target is removed — because you stopped tracking it or it no longer exists — the targets after it move up to fill the gap, so `2` always speaks whatever is currently second in the list. If there is currently no valid target in the slot you pressed, the add-on says for example "No target in slot 2".

When a target is present, by default the add-on speaks its role and name, and the changed content of the target, for example *Window: Claude, Editing readme.md* or *Listbox: Message list, You said: Okay.*. The level of detail of these announcements can be configured in the add-on's [settings](#settings). If the target is there but nothing new has arrived, you hear *no changes yet* in place of the content, and if it does not exist at the moment — a remembered target whose window has not been reopened yet, say — you hear *not found*.

You can change the prefix from NVDA's Input Gestures dialog (NVDA menu → Preferences → Input Gestures), where the add-on's command appears under the **Background Content Tracker** category. The follow-up keys are part of the layered command itself.

## The target menu

The **target menu** (the prefix followed by `t`) lists all current targets as ordered menu items, so you do not have to remember the target's current position in the list or any of the other keys.

Each item names exactly what it acts on, for example *Window: Claude, 3 minutes ago, 3 tasks running*. A target that does not exist at the moment — a remembered one whose window has not been reopened yet, say — reads *not found* in place of the time and the content, and stays in the menu, because you can still stop it, change its settings, or simply leave it there and wait for it to come back. The order in which the targets are listed respects the [**Target sorting** setting](#settings).

Every target is a submenu. When you expand it, you get *Stop tracking*, *Set focus*, and a *Target settings* submenu holding that one target's own copy of the settings that can be [set per target](#global-and-per-target-settings).

Each item in *Target settings* is a check box, and what it shows is what the target actually does: its own value where you have given it one, and the global setting everywhere else. Ticking or unticking one gives that target its own value for that one setting, effective immediately; every other setting goes on following the global. The settings that apply to whole windows only are offered for a whole-window target only, and two more are offered only while the setting they qualify is ticked — *Ignore the focused control* while *Read this target even when in foreground* is, and *Forget this target when it disappears* while *Remember this target* is — because that is the only time they decide anything.

Anything you are already tracking appears first in the menu, so you can move to the target of your interest or stop tracking it quickly. Below that are the targets you can start tracking from your current location (window, focus, mouse pointer, or navigator object). The item to stop tracking all current targets is at the end of the menu.

## Add-on announcements

The add-on announces a few fixed messages during its operation:

- **Tracking a new target** — for example "Tracking window: Claude". You also hear this whenever a remembered target reappears.
- **Restoring remembered targets** — when NVDA starts, the remembered targets are looked for and reported together, as "Found 3 remembered targets", or as "Found 3 of 10 remembered targets" when the rest have not appeared yet. Any that turn up later announce themselves individually.
- **No longer tracking a target** — for example "Stopped tracking listbox: Message list". You also hear this whenever a target no longer exists.
- **Clearing the whole target list** — "All targets cleared".
- **Set focus not getting through** — "Could not move focus to the target", when *Set focus* in the target menu cannot reach the target, because its window is gone, for instance.
- **Pausing** (the `p` key) — "Tracking paused".
- **Resuming** — "Tracking resumed". When tracking resumes, and each time NVDA starts, the add-on announces "No remembered targets found" instead if there is nothing left to track.

## Global and per-target settings

Most of the add-on's options are **global**: you set them in the [settings](#settings) panel, and every target follows them. Seven of them can also be set on a **single target**, which then follows its own value for that one setting and goes on following the global for all the rest:

- *Ignore progress bars*
- *Ignore counters, steppers and timers*
- *Consider changed title a disappeared target*
- *Ignore the focused control when tracking the foreground window*
- *Track even foreground targets*
- *Remember targets*
- *Forget remembered targets when they disappear*

The first four of those decide nothing for a target that is a single control, so they are only offered for a target that is a whole window.

There are two ways to give one target its own value. In the [target menu](#the-target-menu), open that target's *Target settings* submenu and tick or untick what you want. Or hold `shift`, `control` or both while adding a target with `w`, `f`, `m` or `n`, which gives the target being added its own *Remember targets* and *Track even foreground targets* respectively.

The menu words these settings for the one target they act on, so *Remember targets* reads *Remember this target* there, and *Track even foreground targets* reads *Read this target even when in foreground*. They are the same settings, differently worded.

A target has an opinion of its own about a setting only once you have given it one, so changing a global still moves every target that has never been told otherwise, and never disturbs one that has. The settings panel sets globals only: nothing you do there takes a target's own value away from it. Stopping the target and starting it again is what clears them, since a target added afresh has no values of its own beyond any that `shift` or `control` gave it.

## Settings

The add-on's options live in the **Background Content Tracker** category in NVDA's Settings dialog (NVDA menu → Preferences → Settings).

Your settings are stored in NVDA's configuration, so they work with configuration profiles and are saved in the usual way — when NVDA exits, or when you choose Save configuration.

Related options are grouped. All available options are described below, in the order they appear on the panel. Top-level options and whole groups are level 3 headings, individual options within groups are level 4 headings.

### **Enable background content tracking** (checkbox)

When disabled, the add-on stops notifying you but keeps your entire target list and all of your settings, so you can silence it (during a meeting, say) and later switch it back on exactly as it was. This is the same switch toggled by the pause/resume keystroke. The default value is enabled.

### **When target changes** (group)

What happens when new content appears in a target. The options in this group are always available.

#### **Beep** (checkbox)

Plays a tone when the target has changed. The default value is enabled.

#### **Announce** (checkbox)

Announces what changed where, for example "Window: Claude" or "Listbox: Message list". The level of detail of the announcement can be further customized below. The default value is enabled.

#### **Tracking interval** (edit)

Only accepts whole numbers. Sets how often the add-on should query all existing targets for changes, in seconds. 0 means never announce changes to targets automatically, only display them in the [target menu](#the-target-menu). The default value is 1.

#### **Changes to announce at once** (edit)

Only accepts whole numbers. Sets how many consecutive changes to the same target the add-on should announce in a row before you have to refocus the target at least once and then switch elsewhere again for further changes to be announced. 0 means announce any single change every time the target is in the background, no matter what. The default value is 5.

### **Window tracking behavior** (group)

The options in this group are always available. They refine how the add-on should announce changes in targets that are whole windows.

#### **Ignore progress bars** (checkbox)

NVDA itself can speak and/or beep native progress bar controls, even in the background, so you may not always want this add-on to spam you with reporting a constantly changing progress bar from an app when you are actually interested in its real text output. This option suppresses announcements of progress bar controls when enabled. The default value is enabled.

#### **Ignore counters, steppers and timers** (checkbox)

When enabled, the add-on watches for a control (part of the window) that changes in nothing but its numbers — a timer or countdown ticking every second, a step or item counter, a percentage, like the Claude app counting how long it took the model to think. These controls can often be more annoying than helpful, as they do not provide any real, useful information by themselves.

The moment such a control is caught doing that, it falls silent — including the change that gave it away — and stays silent for as long as the target is tracked. You still hear it when it first appears, which is the part that tells you anything.

A control has to contain a number to qualify at all, and its wording has to stay exactly the same while the number moves. Anything whose text changes in some other way is left alone, so ordinary content that happens to contain numbers is never affected. Switching the option off, or off and on again, for the target or globally, makes the add-on forget what it has learned and start watching afresh. The default value is enabled.

#### **Consider changed title a disappeared target** (checkbox)

When enabled, if the title of a window being tracked changes, the add-on will consider it a different window and thus act as if the original target has disappeared, even though the physical window is still the same one in the system. The default value is disabled.

#### **Ignore the focused control when tracking the foreground window** (checkbox)

This only makes a difference for a window that is read while you are working in it, which is what the option to track even foreground targets allows. When enabled, the control you are focused on, and anything inside it, is never announced as a change, so the characters you type into an edit field are not read back at you as new content. What you typed is not announced when you leave the control either, only what arrived elsewhere in the window while you were writing. The default value is enabled.

### **Beep parameters** (group)

The options in this group are only available when the **Beep** checkbox above is enabled.

#### **Duration** (edit)

Only accepts whole numbers. Sets how long the beep should be, in milliseconds. The default value is 50.

#### **Pitch** (edit)

Only accepts whole numbers. Sets at what frequency the beep should play, in hertz. The default value is 440.

#### **Test** (button)

Plays a test beep with the currently set parameters, so you can verify whether it sounds the way you want it to.

### **Include in change announcement** (group)

The options in this group are only available when the **Announce** checkbox above is enabled. They determine exactly what the target changed announcement consists of. As long as the verbal announcement itself is enabled, the name of the target (for example Claude or Message list) is always included.

#### **Target type** (checkbox)

Whether the type of the target (for example **window**, **listbox** or **textbox**) is announced. The default value is enabled.

#### **Changed content** (checkbox)

Whether the new content in the target after the most recent change is announced. The default value is enabled.

### **Include in menu descriptions** (group)

The options in this group are always available. They specify the level of detail you want to hear when browsing the [target menu](#the-target-menu).

#### **Target type** (checkbox)

Whether the type of the target (for example **window**, **listbox** or **textbox**) is displayed in the description of the target's respective menu item. The default value is enabled.

#### **Time since last change** (checkbox)

Whether the relative time since the last change occurred in the target (for example 3 minutes ago) is displayed in the description of the respective target's menu item. The default value is enabled.

#### **Changed content** (checkbox)

Whether the new content in the target after the most recent change is displayed in the description of the target's respective menu item. The default value is enabled.

### **Overlay timeout** (edit)

This option is always available. Only accepts whole numbers. This determines how many seconds without a key press must pass before the overlay closes on its own. Set it to 0 and the overlay never closes by itself: it stays open until you close it, either with escape or with a command that takes your focus somewhere else. The default value is 10.

### **Target sorting** (group)

The two radio buttons in this group are always available. They determine in which order new targets are placed into the ten available numbered slots (see [Keystrokes](#keystrokes)), as well as displayed in the [target menu](#the-target-menu).

#### **Oldest first** (radio button, default setting)

#### **Newest first** (radio button)

### **Track even foreground targets** (checkbox)

This option is always available. Normally a target is only read while you are working somewhere else: once its own application comes to the foreground you are looking at it yourself, so the add-on leaves it alone. When enabled, the target is read even then, so new content is announced in the very window you are working in — a chat window you are typing into, say. Whether what *you* type there is read back at you is decided by **Ignore the focused control when tracking the foreground window** above, which only makes a difference while this option is on. The default value is disabled.

### **Remember targets** (checkbox)

This option is always available. When enabled, your target list is kept between NVDA restarts, and the add-on re-attaches to a target whenever it reappears (for example, it tracks the assistant's window every time that window opens, without you setting it up again). When disabled, the target list starts empty in each session, and only your settings are stored. Whether a remembered target survives the closing of its window *within* a session is decided by **Forget remembered targets when they disappear** below. The default value is disabled.

### **Forget remembered targets when they disappear** (checkbox)

This option is always available, but it only decides anything for a target that is being remembered. A target that is not remembered is always dropped from the list the moment it no longer exists, whatever this option says: nothing would ever look for it again, so it would only sit there reading *not found* for the rest of the session.

For a remembered target, enabled means the same thing — the entry goes as soon as the target does, so old entries do not accumulate — while disabled keeps the entry in the list, reading *not found*, and the add-on goes on looking for that target and takes it up again when it comes back. Either way, you are told that the target is gone at the moment it goes. The default value is enabled.

## Known limitations

- **Background browser tabs are never tracked.** A web browser only keeps the tab you are looking at readable. To keep an eye on a page while you work elsewhere, open it in a window of its own rather than leaving it on a background tab. This behaves the same for sighted users.

- **Some apps reveal very little while not in the foreground.** How much a program tells a screen reader about content you are not focused on is up to that program. Modern applications built on the UIA technology — Terminal, Settings, Calculator, Mail, Photos and most apps from the Microsoft Store — and applications that display web views (Electron apps) — the Claude desktop app, Visual Studio Code, Discord, Slack, Signal, WhatsApp for Windows, Spotify, as well as the browsers themselves (Chrome, Edge, Firefox) — differ considerably in this respect. Where a program does not expose its new content as text, the add-on cannot report it.

- **Only what a window currently reveals counts.** Long lists — chat history, file lists, search results — usually exist only as the handful of rows that happen to be displayed. The add-on cannot see entries that are scrolled out of view, just like sighted users can't, and a minimised window often stops revealing its contents altogether until you restore it. Content that is hidden, collapsed or scrolled out of sight is never announced either, so expanding a panel or scrolling back to something that was already there does not reach you as new content.

If you need to know about frequent updates from an app that you use in the background, it's usually more reliable and straightforward to configure the app itself to send you notifications, if the app can do that. Likewise, if you minimize the app to the system tray, it no longer displays a window, so the add-on can't really track it anymore. However, if the tray icon does expose useful information as text updates that are accessible, you can in deed track the icon itself.

## Contributing

If you would like to contribute to the add-on's development by providing translations, reporting issues or opening a pull request, you can [do so in its GitHub repository](https://github.com/4sensegaming/background-content-tracker). All contributions are welcome and appreciated.

## Changelog

### Version 1.0, 2026/09/07
* Initial release