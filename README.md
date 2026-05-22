# Susurro

> **Voice dictation for macOS with WisprFlow-grade smart formatting. Hot-swap between local Whisper (MLX) and hosted backends (Groq, OpenAI, Anthropic, Gemini, Deepgram) — choose between zero memory footprint, full privacy, or anywhere in between.**

Hold a hotkey, talk, release. The transcript is polished into structured text — ordinals become numbered lists, fillers get stripped, self-corrections get applied — and pasted at the cursor in any app.

<p align="center">
  <em>[demo GIF goes here — record one with QuickTime + Gifski once you're happy with the UX]</em>
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![macOS](https://img.shields.io/badge/macOS-13%2B-blue)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Version](https://img.shields.io/badge/version-0.2.0-success)](https://github.com/danilobrando/susurro/releases/latest)
[![Landing](https://img.shields.io/badge/site-danilobrando.github.io%2Fsusurro-white)](https://danilobrando.github.io/susurro/)

## Install (one line)

```bash
curl -fsSL https://raw.githubusercontent.com/danilobrando/susurro/main/install.sh | bash
```

The script checks for Apple Silicon, Python 3.10+, installs `pipx` via Homebrew if needed, then installs Susurro from this repo. After install, you'll get instructions for setting your Groq API key and granting macOS permissions. Full landing + docs at **[danilobrando.github.io/susurro](https://danilobrando.github.io/susurro/)**.

## Why

| | Susurro | WisprFlow | macOS Dictation |
|---|---|---|---|
| Smart formatting (lists, fillers, backtrack) | **Yes** | Yes | Limited |
| Choice of local vs cloud STT | **Yes** | No (cloud) | Local |
| Choice of polish provider | **Yes** | No | N/A |
| Subscription? | **Free, MIT** | $15/mo | Free |
| Latency on M3 Pro (5 s clip) | ~0.7 s (Groq) / ~1.8 s (local) | ~1–3 s | instant but lower accuracy |
| Customizable hotkey | **Yes** | Yes | Limited |
| Auditable code | **Yes, MIT** | Closed | Closed |

## Backend matrix

The pipeline is `audio → STT → polish → paste`. Each stage has hot-swappable backends.

| Stage | Backend | Memory | Latency (5 s clip) | Cost / 1000 dictations | Notes |
|---|---|---|---|---|---|
| **STT** | `local` (MLX Whisper) | ~3 GB | ~1.0 s | $0 | No network |
| **STT** | `groq` *(default)* | 0 GB | ~0.15 s | $0.06 | OpenAI-compatible API |
| **STT** | `openai` *(planned)* | 0 GB | ~0.6 s | $0.50 | gpt-4o-transcribe |
| **STT** | `deepgram` *(planned)* | 0 GB | ~0.2 s | $0.36 | Streaming-native |
| **Polish** | `off` | 0 | 0 | $0 | Raw STT output |
| **Polish** | `rules` | 0 | ~5 ms | $0 | Regex cleanup only |
| **Polish** | `smart` (Groq Llama 3.3 70B) *(default)* | 0 GB | ~300 ms | $0.06 | Triggered by ordinals / long-form |
| **Polish** | `anthropic` *(planned)* | 0 GB | ~500 ms | $0.40 | Claude Haiku 4.5 |
| **Polish** | `gemini` *(planned)* | 0 GB | ~400 ms | $0.01 | Gemini Flash |

## Requirements

- Apple Silicon Mac (M1 or later). Required only for the `local` STT backend.
- macOS 13+ recommended. Tested on macOS 26.
- Python 3.10+.
- An API key for whichever cloud backend you pick (see below).

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

## API keys (cloud backends)

Set keys via environment variables — Susurro accepts both the namespaced form and the provider's standard env var:

```bash
export SUSURRO_GROQ_API_KEY="gsk_..."        # or GROQ_API_KEY
export SUSURRO_ANTHROPIC_API_KEY="sk-ant-..." # or ANTHROPIC_API_KEY
export SUSURRO_OPENAI_API_KEY="sk-..."        # or OPENAI_API_KEY
export SUSURRO_GEMINI_API_KEY="..."           # or GEMINI_API_KEY
```

Get a free Groq key at [console.groq.com](https://console.groq.com). The free tier comfortably covers personal use.

If a cloud backend is selected but its key is missing or the network fails, Susurro automatically falls back to the `local` MLX backend (if available).

## First-run permissions

macOS will prompt for three permissions the first time you run Susurro:

1. **Microphone** — to capture your voice.
2. **Accessibility** — to paste the transcript into the focused app.
3. **Input Monitoring** — to listen for the global hotkey.

After granting any of these, **fully quit and relaunch your terminal** for the new permission to take effect. The menu bar has shortcuts that jump straight to the right System Settings pane.

## Usage

1. Click into any text field.
2. **Hold the right Option key (⌥)** and speak.
3. **Release.** After ~1 second, the polished transcript is pasted at the cursor via Cmd+V.

While recording, a small dark **waveform pill** appears near the bottom-center of the active screen, with 16 white bars that ripple to your voice — same affordance as WisprFlow. Toggle it off via the *Show waveform indicator* menu item.

## Smart formatting (what the LLM polish does)

The polish step turns raw dictation into structured text. Three modes (switchable from the menu):

- **Off** — paste raw STT output unchanged.
- **Rules only** — regex cleanup: removes obvious fillers (`eh`, `mmm`, `o sea sí`, `um`, `uh`), collapses extra whitespace.
- **Smart (LLM)** — rules first, then sends to the polish LLM **only when triggered** by ordinals (`primero/segundo`, `first/second`), backtrack phrases (`actually`, `digo`, `en realidad`), or long-form input (>40 words). Otherwise stays rules-only to keep latency low.

Example (`smart` mode):

```
Raw:   "Vamos a seguir tres pasos. Primero, reinicia. Segundo, vuelve a registrarte. Tercero, envía un correo."

Polished:
Vamos a seguir tres pasos.

1. Reinicia
2. Vuelve a registrarte
3. Envía un correo
```

Every polish event is logged to `~/.susurro/polish.jsonl` (locally only — never sent anywhere) so you can audit what was changed.

## Configuration

Edit `susurro/config.py`:

- **`STT_BACKEND`** — `groq` (default) or `local`. Planned: `openai`, `deepgram`, `gemini`, `anthropic`.
- **`POLISH_MODE`** — `smart` (default), `rules`, or `off`.
- **`POLISH_BACKEND`** — `groq` (default). Planned: `anthropic`, `openai`, `gemini`.
- **`GROQ_STT_MODEL`** — `whisper-large-v3-turbo` (default) or `whisper-large-v3`.
- **`GROQ_POLISH_MODEL`** — `llama-3.3-70b-versatile` (default) or `llama-3.1-8b-instant`.
- **`LOCAL_STT_MODEL`** — `whisper-large-v3-turbo` (default) or `whisper-large-v3-mlx`.
- **`HOTKEY`** — `alt_r` (default). Any pynput `Key` name: `alt_l`, `ctrl_r`, `f19`, etc.
- **`LANGUAGE`** — `None` for auto-detect, or pin to `"es"` / `"en"` to save ~100 ms per request.
- **`INPUT_DEVICE`** — pick a specific mic. Run `python -m sounddevice` to list devices.
- **`PLAY_SOUNDS`** — subtle audio feedback on record start/stop.
- **`SHOW_INDICATOR`** — floating waveform pill near the bottom of the screen.

## Privacy

Your privacy posture depends on which backends you pick:

| STT | Polish | Audio leaves Mac? | Transcript leaves Mac? |
|---|---|---|---|
| `local` | `off` or `rules` | No | No |
| `local` | `smart` (cloud LLM) | No | Yes (text only) |
| `groq` (or other cloud) | any | Yes | Yes |

Groq, Anthropic, OpenAI, and Google all state they do not train on API data with appropriate settings. Susurro itself ships zero telemetry and makes no network calls beyond the configured backends.

## Performance

Latency from hotkey release to text pasted, measured on M3 Pro / 18 GB / macOS 26:

| STT | Polish trigger | Total |
|---|---|---|
| `groq` | none | ~0.4 s |
| `groq` | LLM fired | ~0.7 s |
| `local` (turbo) | none | ~0.5 s |
| `local` (turbo) | LLM fired (Groq) | ~0.9 s |
| `local` (large-v3) | LLM fired (Groq) | ~1.5 s |

Your numbers will vary with chip generation, concurrent load, and network conditions.

## Troubleshooting

- **Menu bar icon invisible** — emoji-only menu bar items can be hidden on MacBooks with a notch. This release ships a real template PNG, which fixes it for most users. If yours is still missing, try [Bartender](https://www.macbartender.com/) or [Hidden Bar](https://github.com/dwarvesf/hidden).
- **"Status: groq unavailable, falling back to local"** — your `SUSURRO_GROQ_API_KEY` is missing or invalid. Set it and restart.
- **"This process is not trusted"** — Accessibility permission isn't granted. Use the *Open Accessibility Settings…* menu item and fully restart the terminal.
- **Hotkey doesn't trigger** — Input Monitoring permission is missing.
- **Silent recordings / empty transcript** — Microphone permission is missing, or `INPUT_DEVICE` is pointing at the wrong device.
- **Polish output is too aggressive / wrong** — switch *Smart formatting* to *Rules only* or *Off* in the menu. Inspect `~/.susurro/polish.jsonl` to see what was changed.

Logs land in `~/.susurro/susurro.log`; polish events in `~/.susurro/polish.jsonl`.

## Architecture

```
audio (sounddevice → 16kHz mono float32)
    → Transcriber backend       [local MLX | Groq | …]
    → raw text
    → Polisher                  [off | rules | smart]
        ├ Tier 1: regex rules (filler removal, whitespace)
        ├ Tier 2: trigger check (ordinals / backtrack / long-form)
        └ Tier 3: LLM polish backend [Groq Llama | …]
    → polished text
    → clipboard write + Cmd+V into focused app
```

Source layout (under ~1200 lines of Python total):

```
susurro/
  config.py            # all tunables
  audio.py             # mic capture + peak_level for indicator
  hotkey.py            # pynput global hotkey
  typer.py             # clipboard / keystroke insertion
  indicator.py         # floating waveform pill (PyObjC)
  permissions.py       # System Settings deep links
  app.py               # rumps menu bar + main loop
  backends/
    base.py            # protocols (Transcriber, PolishLLM)
    audio_io.py        # float32 → WAV bytes
    credentials.py     # env-var key resolution
    local_mlx.py       # local Whisper via MLX
    groq.py            # Groq Whisper + Groq Llama
  polish/
    __init__.py        # Polisher orchestrator + log writer
    rules.py           # regex cleanup (Tier 1)
    triggers.py        # decides if LLM should fire (Tier 2)
    prompt.py          # system prompt + few-shot examples
  icons/               # template PNGs for menu bar
```

## Roadmap

- **v0.3** — Per-app polish override (Cursor/Terminal → rules-only). Dictionary (vocab biasing + replace rules). Snippets (voice-triggered text expansion).
- **v0.4** — Voice commands: "punto", "coma", "nueva línea", "nuevo párrafo". Anthropic + OpenAI + Gemini backends.
- **v0.5** — Command Mode: second hotkey + text selection + spoken edit ("hazlo más formal", "traduce a inglés").
- **v0.6** — `.app` bundle via py2app + first-run setup wizard.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The project is intentionally small — under ~1200 lines of Python. PRs welcome; please keep it that way.

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately to the maintainer.

## Maintainer

Built and maintained by [Danny Bravo](https://github.com/danilobrando) (`dannybravo@gmail.com`). Product strategist, AI ecosystem builder, educator — based in Bogotá. Susurro is part of a broader effort to make voice-first AI tools available outside the WisprFlow paywall, with full user control over the privacy / cost / quality tradeoff.

## License

[MIT](LICENSE) © 2026 Danny Bravo.

## Credits

- [Groq](https://groq.com) — hosted Whisper + Llama at remarkable latency.
- [ml-explore/mlx](https://github.com/ml-explore/mlx) and [mlx-examples/whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — Apple's MLX framework and the MLX Whisper port.
- [OpenAI Whisper](https://github.com/openai/whisper) — the model.
- [rumps](https://github.com/jaredks/rumps), [pynput](https://github.com/moses-palmer/pynput), [sounddevice](https://github.com/spatialaudio/python-sounddevice) — Python ↔ macOS glue.
- WisprFlow and SuperWhisper — the product UX this clones.
