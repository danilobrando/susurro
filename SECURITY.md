# Security policy

## Reporting a vulnerability

If you find a security issue in Susurro, please **do not** open a public GitHub issue.

Email the maintainer privately at `dannybravo@gmail.com` with:

- A description of the issue
- Steps to reproduce, if applicable
- The version of Susurro you're running (`pip show susurro`)
- Your macOS version and chip

You'll get an acknowledgement within 72 hours. Fixes for high-severity issues will be released within 14 days; lower-severity within 30.

## Threat model

Susurro runs **entirely on-device**:

- Audio capture, transcription, and text insertion all happen locally on your Mac.
- No telemetry, no analytics, no remote API calls during normal operation.
- The only network traffic is the one-time download of model weights from Hugging Face on first run (and only if the weights aren't already cached). After that, `mlx-whisper` runs offline.

The dependency surface is intentionally narrow — `mlx-whisper`, `sounddevice`, `pynput`, `rumps`, `numpy` — and is audited on each release.

## What's in scope

- Code execution via crafted audio or model files.
- Clipboard leakage beyond the documented paste flow (the previous clipboard contents are restored ~150ms after paste).
- Permission escalation via the global hotkey listener.

## What's out of scope

- macOS-level vulnerabilities in pynput, sounddevice, or rumps — please report those upstream.
- Whisper model accuracy or hallucinations.
- Permission prompts shown by macOS itself.
