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
    import pytest

    from susurro.backends import (
        available_polish_llms,
        available_transcribers,
        make_polish_llm,
        make_transcriber,
    )

    # OSS only ships "local".
    assert make_transcriber("local") is not None
    assert make_polish_llm("local") is not None
    assert "local" in available_transcribers()
    assert "local" in available_polish_llms()

    with pytest.raises(ValueError):
        make_transcriber("nonexistent")
    with pytest.raises(ValueError):
        make_polish_llm("nonexistent")


def test_backend_registration_hook() -> None:
    from susurro.backends import available_transcribers, make_transcriber, register_transcriber

    class _FakeSTT:
        name = "fake"

        def warmup(self) -> None: ...
        def transcribe(self, audio):
            return ""

    register_transcriber("fake", lambda: _FakeSTT())
    assert "fake" in available_transcribers()
    assert make_transcriber("fake").name == "fake"
