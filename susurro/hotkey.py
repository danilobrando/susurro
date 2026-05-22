"""Push-to-talk global hotkey listener via pynput."""

from __future__ import annotations

import logging
from collections.abc import Callable

from pynput import keyboard

from . import config

logger = logging.getLogger(__name__)


def _resolve_key(name: str):
    """Map a config string like 'alt_r' or 'f19' to the pynput Key constant."""
    try:
        return getattr(keyboard.Key, name)
    except AttributeError as e:
        raise ValueError(f"Unknown hotkey name: {name!r}") from e


class HotkeyListener:
    """Fires on_press when the configured key is pressed, on_release when released.

    Press repeats from holding the key are debounced — on_press only fires on the
    first transition from up→down.
    """

    def __init__(self, on_press: Callable[[], None], on_release: Callable[[], None]) -> None:
        self._target = _resolve_key(config.HOTKEY)
        self._on_press = on_press
        self._on_release = on_release
        self._is_down = False
        self._listener: keyboard.Listener | None = None

    def _press(self, key) -> None:
        if key == self._target and not self._is_down:
            self._is_down = True
            try:
                self._on_press()
            except Exception:
                logger.exception("on_press callback failed")

    def _release(self, key) -> None:
        if key == self._target and self._is_down:
            self._is_down = False
            try:
                self._on_release()
            except Exception:
                logger.exception("on_release callback failed")

    def start(self) -> None:
        self._listener = keyboard.Listener(on_press=self._press, on_release=self._release)
        self._listener.daemon = True
        self._listener.start()
        logger.info("hotkey listener active: %s", config.HOTKEY)

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
