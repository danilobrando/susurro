# Susurro

> **Local-first voice dictation for macOS. Your audio never leaves your machine.**

Hold a hotkey, talk, release. The transcript is pasted at the cursor in any app — Slack, VS Code, Notes, your browser, anywhere. Whisper runs entirely on-device via Apple's MLX framework. No cloud, no telemetry, no API keys.

<p align="center">
  <em>[demo GIF goes here — record one with QuickTime + Gifski once you're happy with the UX]</em>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-13%2B-blue)]()
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-required-success)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()

## Why

| | Susurro | WisprFlow / SuperWhisper Cloud | macOS Dictation |
|---|---|---|---|
| Audio leaves your Mac? | **No** | Yes (cloud STT) | No (on most settings) |
| Works offline? | **Yes** | No | Yes |
| Subscription? | **Free, MIT** | Paid | Free |
| Model | Whisper large-v3 / turbo | Proprietary | Apple's |
| Latency on M3 Pro | ~0.3–1.2 s after release | ~1–3 s | instant but lower accuracy |
| Customizable hotkey | **Yes** | Yes | Limited |
| Privacy | **Auditable code, MIT** | Trust the vendor | Trust Apple |

If you want WisprFlow-tier dictation but cannot — or will not — send audio to a third party, this is for you.

## Requirements

- Apple Silicon Mac (M1 or later). MLX doesn't support Intel.
- macOS 13+ recommended. Tested on macOS 26.
- Python 3.10+.

## Install

```bash
pipx install susurro
susurro
```

Or from source:

```bash
git clone https://github.com/danilobrando/susurro
cd susurro
pip install -e .
python -m susurro
```

## First-run permissions

macOS will prompt for three permissions the first time you run Susurro. **You must grant all three** for dictation to work end-to-end.

1. **Microphone** — to capture your voice.
2. **Accessibility** — to paste the transcript into the focused app.
3. **Input Monitoring** — to listen for the global hotkey.

After granting any of these, **fully quit and relaunch your terminal** (or the Susurro process) for the new permission to take effect. The menu bar has shortcuts that jump straight to the right System Settings pane — use them; they save time.

## Usage

1. Click into any text field.
2. **Hold the right Option key (⌥)** and speak.
3. **Release.** After ~1 second, the transcript is pasted at the cursor via Cmd+V.

Menu bar icon reflects state:

| Icon | Meaning |
|---|---|
| 🎙 idle | Ready. Hold the hotkey to record. |
| 🔴 recording | Listening. Release the hotkey to transcribe. |
| ⏳ processing | Transcribing on-device. Don't move the cursor. |

While recording, a small dark **waveform pill** appears near the bottom-center of the active screen, with 16 white bars that ripple to your voice — same affordance as WisprFlow. It's click-through and floats above all other windows. Toggle it off via the *Show waveform indicator* menu item if you find it distracting.

## Configuration

Edit `susurro/config.py`:

- **`MODEL_REPO`** — default `whisper-large-v3-mlx` (~3 GB, best accuracy). Swap to `whisper-large-v3-turbo` (~1.6 GB, ~6× faster decode, near-identical accuracy) for WisprFlow-tier latency. Smaller alternatives: `whisper-medium-mlx`, `whisper-small-mlx`.
- **`HOTKEY`** — default `alt_r` (right Option). Any pynput `Key` name: `alt_l`, `ctrl_r`, `f19`, etc.
- **`LANGUAGE`** — `None` for auto-detect, or pin to `"es"` / `"en"` to save ~100 ms per request.
- **`INPUT_DEVICE`** — pick a specific mic. Run `python -m sounddevice` to list devices.
- **`PLAY_SOUNDS`** — subtle audio feedback on record start/stop.
- **`SHOW_INDICATOR`** — floating waveform pill near the bottom of the screen while recording.

## Performance

Latency from hotkey release to text pasted, measured on M3 Pro / 18 GB / macOS 26:

| Model | 5-second clip | 15-second clip |
|---|---|---|
| `whisper-large-v3-mlx` (default) | ~1.0 s | ~2.8 s |
| `whisper-large-v3-turbo` | ~0.3 s | ~0.6 s |
| `whisper-medium-mlx` | ~0.5 s | ~1.4 s |

Your numbers will vary with chip generation and concurrent system load.

## Troubleshooting

- **Menu bar icon invisible** — emoji-only menu bar items can be hidden on MacBooks with a notch. This release ships a real template PNG, which solves it for most users. If yours is still missing, you have too many menu bar items competing for space — tools like [Bartender](https://www.macbartender.com/) or [Hidden Bar](https://github.com/dwarvesf/hidden) fix this.
- **"This process is not trusted"** — Accessibility permission isn't granted. Use the *Open Accessibility Settings…* menu item, then fully restart the terminal.
- **Hotkey doesn't trigger** — Input Monitoring permission is missing.
- **Silent recordings / empty transcript** — Microphone permission is missing, or `INPUT_DEVICE` points at the wrong device.
- **First transcription is slow** — the model is still warming up. Wait until the menu shows *Status: idle* before the first real dictation.
- **Garbled text in some apps** — toggle *Insert via clipboard (Cmd+V)* off in the menu to switch to direct keystroke typing.

Logs land in `~/.susurro/susurro.log`.

## Architecture

```
audio (sounddevice → 16kHz mono float32)
    → mlx_whisper.transcribe (local, on-device)
    → clipboard write + Cmd+V into focused app
```

Six modules, ~600 lines total. Designed to fit in your head.

```
susurro/
  config.py          # all tunables in one place
  audio.py           # mic capture
  stt.py             # mlx-whisper wrapper
  typer.py           # clipboard / keystroke insertion
  hotkey.py          # pynput global hotkey
  permissions.py     # System Settings jumpers
  app.py             # rumps menu bar + main loop
  icons/             # template PNGs for menu bar
```

## Roadmap

Tracked in [GitHub Discussions → Roadmap](https://github.com/danilobrando/susurro/discussions). Tentative:

- **v0.2** — `.app` bundle via py2app; first-run setup wizard.
- **v0.3** — Homebrew tap.
- **v0.4** — Settings UI (no more editing `config.py`).
- **v0.5** — Multiple hotkeys for different languages / models.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The project is intentionally small — under ~800 lines of Python. PRs welcome; please keep it that way.

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately to the maintainer.

## Maintainer

Built and maintained by [Danny Bravo](https://github.com/danilobrando) (`dannybravo@gmail.com`). Product strategist, AI ecosystem builder, educator — based in Bogotá. Susurro is part of a broader effort to make local-first, privacy-respecting AI tools accessible to Spanish-speaking developers.

## License

[MIT](LICENSE) © 2026 Danny Bravo.

## Credits

- [ml-explore/mlx](https://github.com/ml-explore/mlx) and [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — Apple's MLX framework and the MLX Whisper port.
- [OpenAI Whisper](https://github.com/openai/whisper) — the model.
- [rumps](https://github.com/jaredks/rumps), [pynput](https://github.com/moses-palmer/pynput), [sounddevice](https://github.com/spatialaudio/python-sounddevice) — Python ↔ macOS glue.
- WisprFlow and SuperWhisper — the product UX this clones.
