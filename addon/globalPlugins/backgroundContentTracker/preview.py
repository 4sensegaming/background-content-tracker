# Background Content Tracker: keeping covered Chromium windows drawn
# Copyright (C) 2026 Lukáš Hosnedl
# This file is covered by the GNU General Public License, version 2 or later.
# See the file COPYING.txt for more details.

import ctypes
from ctypes import wintypes

# Chromium stops drawing, and updating the accessible content of, a window that is completely covered,
# but treats every window that is not minimized as visible while a taskbar thumbnail preview is shown,
# which it recognises by this window class alone.
_CLASS_NAME = "TaskListThumbnailWnd"

_WS_POPUP = 0x80000000
_WS_EX_TRANSPARENT = 0x20
_WS_EX_TOOLWINDOW = 0x80
_WS_EX_LAYERED = 0x80000
_WS_EX_NOACTIVATE = 0x08000000
_LWA_ALPHA = 0x2
_SW_HIDE = 0
_SW_SHOWNOACTIVATE = 4


class _WNDCLASSW(ctypes.Structure):
	_fields_ = (
		("style", wintypes.UINT),
		("lpfnWndProc", ctypes.c_void_p),
		("cbClsExtra", ctypes.c_int),
		("cbWndExtra", ctypes.c_int),
		("hInstance", wintypes.HINSTANCE),
		("hIcon", wintypes.HICON),
		("hCursor", wintypes.HANDLE),
		("hbrBackground", wintypes.HBRUSH),
		("lpszMenuName", wintypes.LPCWSTR),
		("lpszClassName", wintypes.LPCWSTR),
	)


_user32 = ctypes.windll.user32
_getModuleHandle = ctypes.WINFUNCTYPE(wintypes.HMODULE, wintypes.LPCWSTR)(
	("GetModuleHandleW", ctypes.windll.kernel32)
)
_registerClass = ctypes.WINFUNCTYPE(wintypes.ATOM, ctypes.POINTER(_WNDCLASSW))(("RegisterClassW", _user32))
_unregisterClass = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.LPCWSTR, wintypes.HINSTANCE)(
	("UnregisterClassW", _user32)
)
_createWindowEx = ctypes.WINFUNCTYPE(
	wintypes.HWND,
	wintypes.DWORD,
	wintypes.LPCWSTR,
	wintypes.LPCWSTR,
	wintypes.DWORD,
	ctypes.c_int,
	ctypes.c_int,
	ctypes.c_int,
	ctypes.c_int,
	wintypes.HWND,
	wintypes.HMENU,
	wintypes.HINSTANCE,
	wintypes.LPVOID,
)(("CreateWindowExW", _user32))
_setLayeredWindowAttributes = ctypes.WINFUNCTYPE(
	wintypes.BOOL, wintypes.HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD
)(("SetLayeredWindowAttributes", _user32))
_showWindow = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_int)(("ShowWindow", _user32))
_showWindowAsync = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, ctypes.c_int)(
	("ShowWindowAsync", _user32)
)
_destroyWindow = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND)(("DestroyWindow", _user32))


class PreviewWindow:
	def __init__(self):
		"""Make the window, hidden, on the thread whose message loop is to serve it."""
		self._instance = _getModuleHandle(None)
		windowClass = _WNDCLASSW(
			lpfnWndProc=ctypes.cast(_user32.DefWindowProcW, ctypes.c_void_p).value,
			hInstance=self._instance,
			lpszClassName=_CLASS_NAME,
		)
		_registerClass(ctypes.byref(windowClass))
		self._hwnd = _createWindowEx(
			_WS_EX_TOOLWINDOW | _WS_EX_NOACTIVATE | _WS_EX_LAYERED | _WS_EX_TRANSPARENT,
			_CLASS_NAME,
			"",
			_WS_POPUP,
			0,
			0,
			1,
			1,
			None,
			None,
			self._instance,
			None,
		)
		_setLayeredWindowAttributes(self._hwnd, 0, 0, _LWA_ALPHA)

	def show(self):
		_showWindowAsync(self._hwnd, _SW_SHOWNOACTIVATE)

	def hide(self):
		_showWindowAsync(self._hwnd, _SW_HIDE)

	def destroy(self):
		_showWindow(self._hwnd, _SW_HIDE)
		_destroyWindow(self._hwnd)
		_unregisterClass(_CLASS_NAME, self._instance)
