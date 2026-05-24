"""Inject transcribed text into whatever app is focused.

Default path uses macOS clipboard + Cmd+V — much faster than typing character-by-character,
preserves Unicode, and avoids per-keystroke timing weirdness in some apps (Slack, Notion).
Falls back to pynput's direct typing if the user disables clipboard mode.
"""

from __future__ import annotations

import subprocess
import time

from pynput.keyboard import Controller, Key

from . import config

_kb = Controller()


def _set_clipboard(text: str) -> None:
    """Write text to the macOS clipboard via pbcopy."""
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(text.encode("utf-8"))


def _read_clipboard() -> str:
    try:
        return subprocess.check_output(["pbpaste"]).decode("utf-8")
    except Exception:
        return ""


def paste_text(text: str) -> None:
    """Put text on the clipboard and issue Cmd+V into the focused app.

    If macOS Accessibility is not granted to this process, the Cmd+V synthesis
    silently fails — pynput can't raise on that. To make degraded mode survivable,
    we leave the transcribed text on the clipboard so the user can press Cmd+V
    manually. The previous clipboard contents are NOT restored — losing them is
    the lesser evil compared to losing the dictated text.
    """
    if not text:
        return
    _set_clipboard(text)
    # Tiny delay so the system clipboard server swaps before the paste fires.
    time.sleep(0.03)
    with _kb.pressed(Key.cmd):
        _kb.press("v")
        _kb.release("v")


def type_text(text: str) -> None:
    """Direct keystroke typing. Slower but doesn't touch the clipboard."""
    if not text:
        return
    for ch in text:
        _kb.type(ch)
        if config.TYPE_DELAY > 0:
            time.sleep(config.TYPE_DELAY)


def insert(text: str, *, use_clipboard: bool = True) -> None:
    if use_clipboard:
        paste_text(text)
    else:
        type_text(text)
