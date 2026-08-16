# Background Content Tracker

* Author: Lukáš Hosnedl
* Last tested NVDA version: 2026.3

## Description

**Created by AI, designed and thoroughly tested by humans.**

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

When you press the prefix, the add-on opens a short-lived **virtual overlay** and announces "Background Content Tracker, H for help". While the overlay is open, the next key you press is treated as one of the commands below.

The overlay closes on its own if you press nothing for ten seconds (you can change this delay in the add-on's [settings](#settings)), and pressing any key that is *not* one of the commands closes it immediately. Opening and closing the overlay never moves your focus — it stays exactly where it was, so the add-on commands never disturb what you are doing. When the overlay closes automatically or because you pressed an invalid key, the add-on announces "Overlay closed".

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

The window, focus, mouse and navigator commands are toggles: press one once to add that target to the list, and press it again to remove it. You can track any number of targets at the same time.

The number keys refer to **slots** in your target list, not to fixed targets. By default, `1` is the target you started tracking first and `0` (the tenth slot) is the most recently added target; you can reverse this order under [Settings](#settings). If a target is removed — because you stopped tracking it or it no longer exists — the targets after it move up to fill the gap, so `2` always speaks whatever is currently second in the list. If there is currently no valid target in the slot you pressed, the add-on says for example "No target in slot 2".

When a target is present, by default the add-on speaks its role and name, and the changed content of the target, for example *Window: Claude, Editing readme.md* or *Listbox: Message list, You said: Okay.*. The level of detail of these announcements can be configured in the add-on's [settings](#settings).

You can change the prefix from NVDA's Input Gestures dialog (NVDA menu → Preferences → Input Gestures), where the add-on's command appears under the **Background Content Tracker** category. The follow-up keys are part of the layered command itself.

## The target menu

The **target menu** (the prefix followed by `t`) lists all current targets as ordered menu items, so you do not have to remember the target's current position in the list or any of the other keys.

Each item names exactly what it acts on, for example *Window: Claude, 3 minutes ago, 3 tasks running*. Each existing target is a submenu. When you expand it, the available options are *Stop tracking* and *Set focus*. The order in which the targets are listed respects the [**Target sorting** setting](#settings).

Anything you are already tracking appears first in the menu, so you can move to the target of your interest or stop tracking it quickly. Below that are the targets you can start tracking from your current location (window, focus, mouse pointer, or navigator object). The item to stop tracking all current targets is at the end of the menu.

## Add-on announcements

The add-on announces a few fixed messages during its operation:

- **Tracking a new target** — for example "Tracking window: Claude". You also hear this whenever a remembered target reappears, or is still present when NVDA restarts.
- **No longer tracking a target** — for example "Stopped tracking listbox: Message list". You also hear this whenever a target no longer exists.
- **Clearing the whole target list** — "All targets cleared".
- **Pausing** (the `p` key) — "Background content tracking disabled".
- **Resuming** — "Background content tracking enabled". When tracking resumes, and each time NVDA starts, the add-on also announces "No targets to track" if there are no valid targets left.

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

#### **Ignore repeatedly changing controls** (checkbox)

When enabled, the add-on will not announce consecutive changes to the same control (part of the window) that has already been announced once, such as timers or countdowns changing every second, like the Claude app counting how long it took the model to think. These controls can often be more annoying than helpful, as they do not provide any real, useful information by themselves. Therefore, you can suppress them being announced as changes by this add-on if you are really interested in the actual output. The default value is enabled.

#### **Consider changed title a disappeared target** (checkbox)

When enabled, if the title of a window being tracked changes, the add-on will consider it a different window and thus act as if the original target has disappeared, even though the physical window is still the same one in the system. The default value is disabled.

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

This option is always available. Only accepts whole numbers. This determines how many seconds without a key press must pass before the overlay closes on its own. The default value is 10.

### **Target sorting** (group)

The two radio buttons in this group are always available. They determine in which order new targets are placed into the ten available numbered slots (see [Keystrokes](#keystrokes)), as well as displayed in the [target menu](#the-target-menu).

#### **Oldest first** (radio button, default setting)

#### **Newest first** (radio button)

### **Remember targets** (checkbox)

This option is always available. When enabled, your target list is kept between NVDA restarts, and the add-on re-attaches to a target whenever it reappears (for example, it tracks the assistant's window every time that window opens, without you setting it up again). When disabled, the target list starts empty in each session, and only your settings are stored. The default value is disabled.

### **Forget targets when they disappear** (checkbox)

This option is always available. When enabled, a target is removed from the list automatically once it no longer exists, so old entries do not accumulate. The default value is enabled.

## Known limitations

- **Background browser tabs are never tracked.** A web browser only keeps the tab you are looking at readable. To keep an eye on a page while you work elsewhere, open it in a window of its own rather than leaving it on a background tab. This behaves the same for sighted users.

- **Some apps reveal very little while not in the foreground.** How much a program tells a screen reader about content you are not focused on is up to that program. Modern applications built on the UIA technology — Terminal, Settings, Calculator, Mail, Photos and most apps from the Microsoft Store — and applications that display web views (Electron apps) — the Claude desktop app, Visual Studio Code, Discord, Slack, Signal, WhatsApp for Windows, Spotify, as well as the browsers themselves (Chrome, Edge, Firefox) — differ considerably in this respect. Where a program does not expose its new content as text, the add-on cannot report it.

- **Only what a window currently reveals counts.** Long lists — chat history, file lists, search results — usually exist only as the handful of rows that happen to be displayed. The add-on cannot see entries that are scrolled out of view, just like sighted users can't, and a minimised window often stops revealing its contents altogether until you restore it.

If you need to know about frequent updates from an app that you use in the background, it's usually more reliable and straightforward to configure the app itself to send you notifications, if the app can do that. Likewise, if you minimize the app to the system tray, it no longer displays a window, so the add-on can't really track it anymore. However, if the tray icon does expose useful information as text updates that are accessible, you can in deed track the icon itself.

## Contributing

If you would like to contribute to the add-on's development by providing translations, reporting issues or opening a pull request, you can [do so in its GitHub repository](https://github.com/4sensegaming/background-content-tracker). All contributions are welcome and appreciated.
