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


#: Callbacks run after a write that changes which targets are to be persisted.
#: Registered by the global plugin, which is the one that owns the target list.
_saveHooks = []


#: A plain copy of every setting, safe to read from any thread. Rebound wholesale
#: by :func:`refresh`, never mutated, so a reader always sees a consistent set of
#: values without needing a lock.
_snapshot = dict(DEFAULTS)


def initialize():
	"""Register the configuration specification with NVDA. Main thread only."""
	config.conf.spec[CONF_SECTION] = confspec
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


def registerSaveHook(func):
	"""Call ``func`` after a write that changes which targets are persisted."""
	if func not in _saveHooks:
		_saveHooks.append(func)


def unregisterSaveHook(func):
	"""Undo :func:`registerSaveHook`; harmless if ``func`` was never registered."""
	try:
		_saveHooks.remove(func)
	except ValueError:
		pass


def _onProfileSwitch(*args, **kwargs):
	# NVDA has notified this with differing keyword arguments over the years, so
	# accept anything and ignore it.
	refresh()


def refresh():
	"""Re-read every setting into the thread-safe snapshot. Main thread only."""
	global _snapshot
	_snapshot = {key: get(key) for key in DEFAULTS}


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

	Writing ``rememberTargets`` changes which targets are to be persisted, so the
	saved target list is re-written afterwards through the registered save hooks:
	ticking the box in the settings panel stores the targets the user already has
	instead of waiting for the list to next change. That re-write is itself a
	configuration write and passes ``notify=False``, so it cannot call itself
	back.
	"""
	if CONF_SECTION not in config.conf:
		config.conf[CONF_SECTION] = {}
	section = config.conf[CONF_SECTION]
	for key, value in values.items():
		section[key] = value
	refresh()
	if notify and "rememberTargets" in values:
		for hook in list(_saveHooks):
			try:
				hook()
			except Exception:
				log.debugWarning("Error in a configuration save hook", exc_info=True)
