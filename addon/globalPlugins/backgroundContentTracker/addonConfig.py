# Background Content Tracker: configuration handling
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2.
# See the file COPYING.txt for more details.

"""Configuration specification, defaults and small accessor helpers.

The specification is registered with NVDA so that values are typed, validated,
saved with NVDA's own configuration and honoured by configuration profiles.
Reads go through :func:`get`, which falls back to :data:`DEFAULTS` if a value
cannot be read for any reason, so the rest of the add-on never has to guard
against a missing configuration section.

Most settings are global. A handful of them, listed in :data:`LOCAL_KEYS`, can
also be set on a single target, which then uses its own value in place of the
global one. The overriding itself belongs to the target (see
:meth:`.TrackedTarget.setting`); all this module contributes is the list of
which settings may be overridden at all, and a sanitiser for a set of overrides
read back from the saved target list.

:func:`get` reads NVDA's live configuration and therefore belongs on NVDA's main
thread. The monitor thread calls :func:`snapshot` instead, which hands back a
plain dictionary that no other thread ever mutates in place.
"""

import config
from logHandler import log

#: The key of our section inside NVDA's configuration.
CONF_SECTION = "backgroundContentTracker"

#: Configuration specification (types and defaults).
confspec = {
	"enabled": "boolean(default=True)",
	"changeBeep": "boolean(default=True)",
	"changeAnnounce": "boolean(default=True)",
	"trackingInterval": "integer(default=1,min=0,max=3600)",
	"changesAtOnce": "integer(default=5,min=0,max=100)",
	"ignoreProgressBars": "boolean(default=True)",
	"ignoreRepeatedControls": "boolean(default=True)",
	"titleChangeDisappears": "boolean(default=False)",
	"beepDuration": "integer(default=50,min=1,max=30000)",
	"beepPitch": "integer(default=440,min=20,max=20000)",
	"announceTargetType": "boolean(default=True)",
	"announceChangedContent": "boolean(default=True)",
	"menuTargetType": "boolean(default=True)",
	"menuTimeSinceChange": "boolean(default=True)",
	"menuChangedContent": "boolean(default=True)",
	"overlayTimeout": "integer(default=10,min=1,max=120)",
	"targetSorting": "option('oldest', 'newest', default='oldest')",
	"trackForegroundTargets": "boolean(default=False)",
	"rememberTargets": "boolean(default=False)",
	"forgetOnDisappear": "boolean(default=True)",
	# Serialised (JSON) list of remembered target identities. Internal; not shown in the GUI.
	"savedTargets": "string(default='')",
}

#: Fallback defaults, mirroring ``confspec`` above, used if a live read fails.
DEFAULTS = {
	"enabled": True,
	"changeBeep": True,
	"changeAnnounce": True,
	"trackingInterval": 1,
	"changesAtOnce": 5,
	"ignoreProgressBars": True,
	"ignoreRepeatedControls": True,
	"titleChangeDisappears": False,
	"beepDuration": 50,
	"beepPitch": 440,
	"announceTargetType": True,
	"announceChangedContent": True,
	"menuTargetType": True,
	"menuTimeSinceChange": True,
	"menuChangedContent": True,
	"overlayTimeout": 10,
	"targetSorting": "oldest",
	"trackForegroundTargets": False,
	"rememberTargets": False,
	"forgetOnDisappear": True,
	"savedTargets": "",
}

#: The settings a single target may override; everything else is global only.
#: A target holds a value for those of these it actually overrides and inherits
#: the rest, so a global the user changes later still moves every target that
#: never had an opinion about it.
LOCAL_KEYS = (
	"ignoreProgressBars",
	"ignoreRepeatedControls",
	"titleChangeDisappears",
	"rememberTargets",
	"trackForegroundTargets",
	"forgetOnDisappear",
)


def sanitizeOverrides(raw):
	"""The recognised local settings in ``raw``, as booleans.

	Guards the loader of the saved target list against a blob written by another
	version of the add-on, or edited by hand: an unrecognised key would otherwise
	sit in a target's overrides for the rest of its life, shadowing nothing and
	confusing every later reader of them.
	"""
	if not isinstance(raw, dict):
		return {}
	return {key: bool(raw[key]) for key in LOCAL_KEYS if key in raw}


#: Callbacks run after a write that actually changes a setting, each with the
#: set of keys whose stored value moved. Registered by the global plugin, which
#: owns the target list and is the one that has to act on such a change.
_changeHooks = []


#: A plain copy of every setting, safe to read from any thread. Rebound wholesale
#: by :func:`refresh`, never mutated, so a reader always sees a consistent set of
#: values without needing a lock.
_snapshot = dict(DEFAULTS)


def initialize():
	"""Register the configuration specification with NVDA. Main thread only."""
	config.conf.spec[CONF_SECTION] = confspec
	# The first read is not a change: nothing has had a chance to register a hook
	# yet, and every setting having "moved" from its default is not news.
	refresh()
	action = getattr(config, "post_configProfileSwitch", None)
	if action is not None:
		action.register(_onProfileSwitch)


def terminate():
	"""Undo :func:`initialize`. Main thread only."""
	action = getattr(config, "post_configProfileSwitch", None)
	if action is not None:
		try:
			action.unregister(_onProfileSwitch)
		except Exception:
			pass


def registerChangeHook(func):
	"""Call ``func(changed)`` after a write that moves any setting.

	``changed`` is the set of keys whose stored value is not what it was. Keys
	written with the value they already held are not in it, so a hook can treat
	being called about a key as the setting having genuinely just been switched.
	"""
	if func not in _changeHooks:
		_changeHooks.append(func)


def unregisterChangeHook(func):
	"""Undo :func:`registerChangeHook`; harmless if ``func`` was never registered."""
	try:
		_changeHooks.remove(func)
	except ValueError:
		pass


def _onProfileSwitch(*args, **kwargs):
	# NVDA has notified this with differing keyword arguments over the years, so
	# accept anything and ignore it.
	#
	# A profile carries its own values for these settings, so switching to one is
	# every bit as much a change of the globals as saving the settings panel is,
	# and the hooks are told about it on the same terms.
	notifyChanged(refresh())


def refresh():
	"""Re-read every setting into the thread-safe snapshot. Main thread only.

	Returns the set of keys whose value moved, which is what tells a change from
	a re-read that found everything as it was. This is the one place the two
	snapshots are compared, so every route by which the configuration can change —
	a write here, a profile switch — reports a change on the same terms.
	"""
	global _snapshot
	previous = _snapshot
	_snapshot = {key: get(key) for key in DEFAULTS}
	return {key for key in DEFAULTS if previous.get(key) != _snapshot[key]}


def notifyChanged(changed):
	"""Hand ``changed`` to every registered change hook. Main thread only.

	A hook that raises is logged and stepped over: one of them failing must not
	cost the others their notification, nor take down the write that caused it.
	"""
	if not changed:
		return
	for hook in list(_changeHooks):
		try:
			hook(changed)
		except Exception:
			log.debugWarning("Error in a configuration change hook", exc_info=True)


def snapshot():
	"""Every setting as a plain dict. Safe to read from the monitor thread.

	Treat the result as read-only: it is shared with whichever thread called
	:func:`refresh` last.
	"""
	return _snapshot


def get(key):
	"""Return a configuration value, falling back to the default on any error.

	Reads NVDA's live configuration, so this belongs on the main thread.
	"""
	try:
		return config.conf[CONF_SECTION][key]
	except (KeyError, TypeError):
		return DEFAULTS[key]


def set(key, value):
	"""Store a configuration value, creating the section if necessary."""
	setMany({key: value})


def setMany(values, notify=True):
	"""Store several configuration values and refresh the snapshot once.

	:func:`refresh` re-reads every setting, so writing a whole settings panel one
	key at a time costs a full re-read per key. Main thread only.

	Some settings need something done to the existing targets the moment they
	move — the saved target list re-written, a window's tracked title re-taken —
	so the keys that actually changed are handed to the registered change hooks
	afterwards. What decides that is whether the value moved, not merely which
	keys were written: the settings panel writes every one of its settings on
	every save, and a hook must be able to tell a setting that was just switched
	from one that was only written down again.

	A hook's own configuration writes pass ``notify=False``, so they cannot set
	the hooks off again.
	"""
	if CONF_SECTION not in config.conf:
		config.conf[CONF_SECTION] = {}
	section = config.conf[CONF_SECTION]
	for key, value in values.items():
		section[key] = value
	changed = refresh()
	if notify:
		notifyChanged(changed)
