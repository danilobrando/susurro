# Susurro

> **Local voice dictation for macOS. Fully offline. MIT licensed.**

Hold a hotkey, talk, release. The transcript is polished into structured text — ordinals become numbered lists, fillers get stripped, self-corrections get applied — and pasted at the cursor in any app. Everything runs on your Mac through Apple's MLX framework. No accounts, no API keys, no network.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-13%2B-blue)]()
[![Apple Silicon](https://img.shields.io/badge/Apple%20Silicon-required-success)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Version](https://img.shields.io/badge/version-0.4.0-success)](https://github.com/danilobrando/susurro/releases/latest)
[![PyPI](https://img.shields.io/pypi/v/susurro.svg)](https://pypi.org/project/susurro/)
[![Landing](https://img.shields.io/badge/site-susurro.live-white)](https://susurro.live)

## Install (one line)

```bash
curl -fsSL https://raw.githubusercontent.com/danilobrando/susurro/main/install.sh | bash
```

Or with `pipx`:

```bash
pipx install susurro
susurro
```

After install, hold the **right Option key (⌥)** to dictate. The first launch downloads Whisper + Llama weights (~5 GB total, one-time) and triggers three macOS permission prompts (Microphone, Accessibility, Input Monitoring).

## Why Susurro

- **Fully offline.** Audio never leaves your machine. No telemetry, no analytics, no cloud calls during normal use.
- **WisprFlow-grade smart formatting.** An LLM polishes the raw transcript: ordinals become numbered lists, fillers like "um/eh/o sea" get removed, self-corrections ("Pedro, eh, Pablo digo") collapse to the final intent.
- **Auditable.** Every (raw → polished) edit is logged locally to `~/.susurro/polish.jsonl`. Nothing is hidden.
- **MIT licensed.** Read the code, fork it, redistribute it.

If you want zero local RAM + lower latency at the cost of cloud transcription, [Susurro Pro](https://susurro.live) is a paid hosted variant that extends this package.

## Requirements

- Apple Silicon Mac (M1 or later). MLX doesn't support Intel.
- macOS 13+ recommended (tested on 26).
- Python 3.10+.
- ~5 GB free disk (one-time model download).
- ~3 GB free RAM while running.

## Usage

1. Click into any text field.
2. **Hold the right Option key (⌥)** and speak.
3. **Release.** After ~1.5 s, the polished transcript pastes at the cursor via Cmd+V.

While recording, a small dark **waveform pill** appears near the bottom of the active screen, with 16 white bars rippling to your voice. Toggle off via the *Show waveform indicator* menu item.

Menu bar icon reflects state:

| Icon | Meaning |
|---|---|
| 🎙 idle | Ready. Hold the hotkey to record. |
| 🔴 recording | Listening. Release to transcribe. |
| ⏳ processing | Transcribing + polishing on-device. |

## Smart formatting

The polish step turns raw dictation into structured text. Three modes (switchable from the menu):

- **Off** — paste raw STT output unchanged.
- **Rules only** — regex cleanup: filler removal (`eh`, `mmm`, `o sea sí`, `um`, `uh`), whitespace normalization. <5 ms.
- **Smart (LLM)** — rules + local Llama 3.2 3B polish, but only when triggers fire (ordinal markers, backtrack phrases, long-form input). Otherwise stays rules-only to keep latency low.

Example (`smart` mode):

```
Raw:   "Vamos a seguir tres pasos. Primero, reinicia. Segundo, vuelve a registrarte. Tercero, envía un correo."

Polished:
Vamos a seguir tres pasos.

1. Reinicia
2. Vuelve a registrarte
3. Envía un correo
```

## Configuration

Edit `susurro/config.py`:

- **`STT_BACKEND`** — `local` (default). Extension packages can register more.
- **`POLISH_MODE`** — `smart` (default), `rules`, or `off`.
- **`LOCAL_STT_MODEL`** — `whisper-large-v3-turbo` (default), or `whisper-large-v3-mlx` for max accuracy.
- **`LOCAL_POLISH_MODEL`** — `Llama-3.2-3B-Instruct-4bit` (default), or any mlx-community 3B-class model.
- **`HOTKEY`** — `alt_r` (default). Any pynput `Key` name: `alt_l`, `ctrl_r`, `f19`, etc.
- **`LANGUAGE`** — `None` for auto-detect, or pin to `"es"` / `"en"` to save ~100 ms per request.
- **`INPUT_DEVICE`** — pick a specific mic. Run `python -m sounddevice` to list devices.

## Permissions

macOS will prompt for three permissions the first time you run Susurro:

1. **Microphone** — to capture your voice.
2. **Accessibility** — to paste the transcript into the focused app.
3. **Input Monitoring** — to listen for the global hotkey.

After granting any of these, **fully quit and relaunch your terminal** for the new permission to take effect. The menu bar has direct links to each pane.

## Architecture

```
audio (sounddevice → 16kHz mono float32)
    → MLX Whisper (whisper-large-v3-turbo, on-device)
    → raw text
    → Polisher
        ├ Tier 1: regex rules (filler removal, whitespace)
        ├ Tier 2: trigger check (ordinals / backtrack / long-form)
        └ Tier 3: MLX-LM polish (Llama 3.2 3B Instruct, on-device)
    → polished text
    → clipboard write + Cmd+V into focused app
```

Source layout — under ~1500 lines of Python total:

```
susurro/
  config.py            # all tunables
  audio.py             # mic capture + peak_level for indicator
  hotkey.py            # pynput global hotkey
  typer.py             # clipboard / keystroke insertion
  indicator.py         # floating waveform pill (PyObjC)
  permissions.py       # System Settings deep links
  app.py               # rumps menu bar + main loop (subclassable)
  backends/
    base.py            # protocols (Transcriber, PolishLLM)
    local_mlx.py       # local Whisper via MLX
    local_mlx_lm.py    # local polish LLM via mlx-lm
    __init__.py        # factories + extension registration
  polish/
    __init__.py        # Polisher orchestrator
    rules.py           # regex cleanup
    triggers.py        # decides if LLM should fire
    prompt.py          # system prompt + few-shot examples
  icons/               # template PNGs for menu bar
```

## Extending Susurro

External packages can register additional backends without modifying this code:

```python
# in your_extension/__init__.py
from susurro.backends import register_transcriber, register_polish_llm

class MyCloudSTT:
    name = "mycloud"
    def warmup(self): ...
    def transcribe(self, audio): ...

register_transcriber("mycloud", lambda: MyCloudSTT())
```

Then set `STT_BACKEND = "mycloud"` in `susurro/config.py` or via environment.

## Troubleshooting

- **Menu bar icon invisible** — emoji-only menu bar items can be hidden on MacBooks with a notch. This release ships a real template PNG, which fixes it for most users.
- **"This process is not trusted"** — Accessibility permission isn't granted. Use the *Open Accessibility Settings…* menu item, then fully restart the terminal.
- **Hotkey doesn't trigger** — Input Monitoring permission is missing.
- **Silent recordings / empty transcript** — Microphone permission is missing, or `INPUT_DEVICE` is pointing at the wrong device.
- **First transcription is slow** — the model is still warming up. Wait until the menu shows *Status: idle* before the first real dictation.

Logs land in `~/.susurro/susurro.log`; polish events in `~/.susurro/polish.jsonl`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs welcome; please keep the package under ~1500 lines.

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately to the maintainer.

## Maintainer

Built and maintained by [Danny Bravo](https://github.com/danilobrando) (`dannybravo@gmail.com`). Product strategist, AI ecosystem builder, educator — based in Bogotá.

## License

[MIT](LICENSE) © 2026 Danny Bravo.

## Credits

- [ml-explore/mlx](https://github.com/ml-explore/mlx) and [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — Apple's MLX framework and the MLX Whisper port.
- [OpenAI Whisper](https://github.com/openai/whisper) — the model.
- [Meta Llama 3.2](https://www.llama.com/) — the polish LLM.
- [rumps](https://github.com/jaredks/rumps), [pynput](https://github.com/moses-palmer/pynput), [sounddevice](https://github.com/spatialaudio/python-sounddevice) — Python ↔ macOS glue.
- WisprFlow and SuperWhisper — the product UX this clones.
