# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] — 2026-05-23

### Changed

- **Split into two products.** This package (`susurro` on PyPI) is now the OSS local-only Mac client. The cloud-extended product (`susurro-pro`) lives in a separate private repo, depends on this package, and adds hosted transcription via api.susurro.live. Same hotkey, same UX — different backend.
- Default `STT_BACKEND` = `local` (was `groq`).
- Default `POLISH_BACKEND` = `local` (was `groq`).
- Removed `openai` and `httpx` dependencies (no more cloud calls from OSS).
- Default `LOCAL_STT_MODEL` switched from `whisper-large-v3-mlx` to `whisper-large-v3-turbo` for ~6x faster decode.

### Removed

- `susurro/backends/susurro_pro.py` — moved to the susurro-pro package.
- `susurro/backends/groq.py` — moved to the susurro-pro package.
- `susurro/backends/audio_io.py` and `credentials.py` — used only by cloud backends, moved with them.
- `api/` directory — FastAPI backend moved to the susurro-pro repo.
- `docs/` directory — landing page moved to susurro-pro/landing/.
- Root-level `Dockerfile`, `Caddyfile`, `railway.json` — Pro-only.
- "Sign in to Susurro Pro" menu items — Pro adds these via `_extra_menu_items()` override.

### Added

- `susurro.backends.register_transcriber()` and `register_polish_llm()` — public extension points so external packages can add backends without forking.
- `SusurroApp._build_menu()` and `_extra_menu_items()` — hook points so subclasses can extend the menu cleanly.
- `available_transcribers()` / `available_polish_llms()` helpers.
- Published to PyPI as `susurro`.

## [0.2.0] — 2026-05-22

### Added

- **Hot-swappable backends.** STT and polish providers are now pluggable. Ships with `local` (MLX Whisper) and `groq` (hosted Whisper + Llama 3.3 70B). Future drops: OpenAI, Anthropic, Gemini, Deepgram.
- **Cloud-first defaults.** `STT_BACKEND="groq"` and `POLISH_BACKEND="groq"` drop local RAM usage from ~3 GB to 0 GB. Latency improves from ~1.8 s to ~0.7 s end-to-end on a 5 s clip.
- **Smart formatting (LLM polish).** Three modes (`off`/`rules`/`smart`). The LLM runs **only** when triggers fire (ordinal markers, backtrack phrases, long-form input) to keep latency low for the common case.
- **Polish rules layer.** Regex-based filler removal (`eh`, `mmm`, `o sea sí`, `um`, `uh`, `este pues`) + whitespace normalization. Runs in <5 ms, no network.
- **Polish trigger detection.** Detects Spanish/English ordinals (`primero/segundo/tercero`, `first/second/third`, `en primer lugar`) and self-correction phrases (`en realidad`, `actually`, `digo`).
- **Polish system prompt.** Idempotent prompt with 5 few-shot examples covering numbered lists, filler removal, and backtrack. Refuses to paraphrase or translate.
- **Polish event log.** Every (raw, polished, metadata) tuple appended to `~/.susurro/polish.jsonl` for local audit and future tuning. Never sent anywhere.
- **Menu submenu: Smart formatting ▸ Off / Rules only / Smart (LLM).** Hot-toggle without restart.
- **Fallback chain.** If a cloud backend fails (missing key, network error), automatically falls back to local MLX.
- **Floating waveform indicator** (carried over from v0.1.x development). 16-bar pill, click-through, follows the active screen.
- API key resolution accepts both `SUSURRO_<PROVIDER>_API_KEY` and the provider's standard env var.

### Changed

- **Tagline: dropped "local-first" as the default identity.** Susurro now positions as "your choice of where inference runs" — local for full privacy, cloud for low memory + low latency. Per-stage configuration.
- Default `LOCAL_STT_MODEL` switched from `whisper-large-v3-mlx` to `whisper-large-v3-turbo` for ~6× faster local decode.
- Package version bumped to 0.2.0.
- `susurro/stt.py` removed; replaced by `susurro/backends/local_mlx.py` (`MLXTranscriber`).

### Dependencies

- Added `openai>=1.40` (used for both OpenAI and Groq via OpenAI-compatible API).
- Added optional extras: `anthropic`, `gemini`, `deepgram`.

## [0.1.0] — 2026-05-21

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
