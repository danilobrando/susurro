"""Smoke tests — verify the package imports and basic wiring is intact.

Real STT + audio capture + cloud calls aren't exercised here. Run
`scripts/test_mic.py` locally for end-to-end with a mic + API key.
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

    HotkeyListener(on_press=lambda: None, on_release=lambda: None)


def test_recorder_constructs_without_starting() -> None:
    from susurro.audio import Recorder

    r = Recorder()
    assert not r.is_recording
    out = r.stop()
    assert isinstance(out, np.ndarray)
    assert out.size == 0
    assert r.peak_level() == 0.0


def test_indicator_constructs_without_creating_window() -> None:
    from susurro.audio import Recorder
    from susurro.indicator import WaveformIndicator

    ind = WaveformIndicator(Recorder())
    assert ind is not None


def test_backend_factory_known_and_unknown() -> None:
    from susurro.backends import make_polish_llm, make_transcriber

    # Construction must NOT do network or model load.
    assert make_transcriber("local") is not None
    assert make_transcriber("groq") is not None
    assert make_polish_llm("groq") is not None

    import pytest

    with pytest.raises(ValueError):
        make_transcriber("nonexistent")
    with pytest.raises(ValueError):
        make_polish_llm("nonexistent")
