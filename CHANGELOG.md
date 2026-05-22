# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Floating waveform indicator.** A small dark pill (140×40) appears near the bottom-center of the active screen while recording, with 16 white bars rippling to live mic input — same affordance as WisprFlow. Click-through, floats above all windows, follows the cursor to the active display in multi-monitor setups. Toggle in the menu or via `SHOW_INDICATOR` in `config.py`.
- `Recorder.peak_level()` exposes the current mic RMS (0..1) for UI consumption.

## [0.1.0] — 2026-05-21

### Added

- Push-to-talk dictation triggered by the right Option key.
- Local transcription via [`mlx-whisper`](https://github.com/ml-explore/mlx-examples/tree/main/whisper) (Apple Silicon only). Default model is `whisper-large-v3-mlx`; swap to `whisper-large-v3-turbo` in `susurro/config.py` for ~6× faster decode.
- Menu bar app (rumps) with template PNG icons that adapt to light/dark mode.
- Clipboard paste mode (Cmd+V) with prior-clipboard restoration, and a direct-typing fallback.
- Status updates and last-transcript shortcut in the menu dropdown.
- Quick-access menu items that open the correct System Settings pane for Microphone, Accessibility, and Input Monitoring.
- File logging at `~/.susurro/susurro.log`.
- Smoke test script: `scripts/test_mic.py`.

### Known limitations

- Apple Silicon only — Intel Macs aren't supported by MLX.
- First launch requires three System Settings permission grants (Microphone, Accessibility, Input Monitoring) and a terminal restart.
- No `.app` bundle yet; install via `pipx` or `pip` and launch from terminal.
