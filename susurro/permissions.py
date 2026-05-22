"""Shortcuts that open System Settings directly at the relevant privacy pane.

These URLs are documented Apple URI schemes — they jump past the hierarchy
the user would otherwise have to navigate manually.
"""

from __future__ import annotations

import subprocess

_MICROPHONE = "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
_ACCESSIBILITY = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
_INPUT_MONITORING = "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"


def _open(url: str) -> None:
    subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_microphone() -> None:
    _open(_MICROPHONE)


def open_accessibility() -> None:
    _open(_ACCESSIBILITY)


def open_input_monitoring() -> None:
    _open(_INPUT_MONITORING)
