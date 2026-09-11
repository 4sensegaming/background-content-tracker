# Background Content Tracker: configuration handling
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

from collections.abc import Callable, Mapping

import config
from configobj.validate import Validator
from logHandler import log

ConfigValue = bool | int | str
Settings = dict[str, ConfigValue]
ChangedKeys = set[str]

CONF_SECTION = "backgroundContentTracker"

SORT_ORDERS: tuple[str, ...] = (
	"newest",
	"oldest",
	"recentlyChanged",
	"leastRecentlyChanged",
	"alphabetical",
	"reverseAlphabetical",
)
_SORT_SPEC = f"option({', '.join(repr(order) for order in SORT_ORDERS)}, default='newest')"

confspec: dict[str, str] = {
	"enabled": "boolean(default=True)",
	"changeBeep": "boolean(default=True)",
	"changeAnnounce": "boolean(default=True)",
	"interruptSpeech": "boolean(default=False)",
	"trackingInterval": "integer(default=1,min=0,max=3600)",
	"changesAtOnce": "integer(default=5,min=0,max=100)",
	"ignoreProgressBars": "boolean(default=True)",
	"ignoreCounters": "boolean(default=True)",
	"titleChangeDisappears": "boolean(default=False)",
	"ignoreGenericControls": "boolean(default=True)",
	"ignoreFocusedControl": "boolean(default=True)",
	"beepDuration": "integer(default=50,min=1,max=30000)",
	"beepPitch": "integer(default=440,min=20,max=20000)",
	"announceTargetType": "boolean(default=True)",
	"announceChangedContent": "boolean(default=True)",
	"menuTargetType": "boolean(default=True)",
	"menuTimeSinceChange": "boolean(default=True)",
	"menuChangedContent": "boolean(default=True)",
	"overlayTimeout": "integer(default=10,min=0,max=120)",
	"slotSorting": _SORT_SPEC,
	"menuSorting": _SORT_SPEC,
	"trackForegroundTargets": "boolean(default=False)",
	"rememberTargets": "boolean(default=False)",
	"forgetOnDisappear": "boolean(default=True)",
	"savedTargets": "string(default='')",
}

_validator = Validator()
DEFAULTS: Settings = {key: _validator.get_default_value(spec) for key, spec in confspec.items()}

LOCAL_KEYS: tuple[str, ...] = (
	"interruptSpeech",
	"ignoreProgressBars",
	"ignoreCounters",
	"titleChangeDisappears",
	"ignoreGenericControls",
	"ignoreFocusedControl",
	"rememberTargets",
	"trackForegroundTargets",
	"forgetOnDisappear",
)


def sanitizeOverrides(raw: object) -> dict[str, bool]:
	if not isinstance(raw, dict):
		return {}
	return {key: bool(raw[key]) for key in LOCAL_KEYS if key in raw}


_changeHooks: list[Callable[[ChangedKeys], None]] = []

_snapshot: Settings = dict(DEFAULTS)


def initialize():
	config.conf.spec[CONF_SECTION] = confspec
	refresh()
	config.post_configProfileSwitch.register(_onProfileSwitch)


def terminate():
	config.post_configProfileSwitch.unregister(_onProfileSwitch)


def registerChangeHook(func: Callable[[ChangedKeys], None]):
	if func not in _changeHooks:
		_changeHooks.append(func)


def unregisterChangeHook(func: Callable[[ChangedKeys], None]):
	try:
		_changeHooks.remove(func)
	except ValueError:
		pass


def _onProfileSwitch(*args: object, **kwargs: object):
	notifyChanged(refresh())


def refresh() -> ChangedKeys:
	global _snapshot
	previous = _snapshot
	_snapshot = {key: get(key) for key in DEFAULTS}
	return {key for key in DEFAULTS if previous.get(key) != _snapshot[key]}


def notifyChanged(changed: ChangedKeys):
	if not changed:
		return
	for hook in tuple(_changeHooks):
		try:
			hook(changed)
		except Exception:  # noqa: BLE001
			log.debugWarning("Error in a configuration change hook", exc_info=True)


def snapshot() -> Settings:
	return _snapshot


def get(key: str) -> ConfigValue:
	try:
		return config.conf[CONF_SECTION][key]
	except (KeyError, TypeError):
		return DEFAULTS[key]


def set(key: str, value: ConfigValue):
	setMany({key: value})


def setMany(values: Mapping[str, ConfigValue], notify: bool = True):
	if CONF_SECTION not in config.conf:
		config.conf[CONF_SECTION] = {}
	section = config.conf[CONF_SECTION]
	for key, value in values.items():
		section[key] = value
	changed = refresh()
	if notify:
		notifyChanged(changed)
