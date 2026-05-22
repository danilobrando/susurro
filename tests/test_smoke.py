"""Smoke tests — verify the package imports and the basic wiring is intact.

Real STT + audio capture aren't exercised here because CI runners don't have
mics or Apple Silicon. Run `scripts/test_mic.py` locally for end-to-end.
"""

from __future__ import annotations

import numpy as np


def test_version_string() -> None:
    import susurro

    assert isinstance(susurro.__version__, str)
    assert susurro.__version__.count(".") >= 1


def test_config_paths_exist() -> None:
    from susurro import config

    assert config.ICONS_DIR.is_dir()
    assert (config.ICONS_DIR / "idle.png").is_file()
    assert (config.ICONS_DIR / "recording.png").is_file()
    assert (config.ICONS_DIR / "processing.png").is_file()


def test_hotkey_resolves() -> None:
    from susurro.hotkey import HotkeyListener

    # Constructing the listener resolves the hotkey name to a pynput Key.
    HotkeyListener(on_press=lambda: None, on_release=lambda: None)


def test_recorder_constructs_without_starting() -> None:
    from susurro.audio import Recorder

    r = Recorder()
    assert not r.is_recording
    # Empty stop() returns zero-length array.
    out = r.stop()
    assert isinstance(out, np.ndarray)
    assert out.size == 0
