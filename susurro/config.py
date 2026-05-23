"""Centralized config — tweak these to match your machine and preferences.

Susurro runs fully offline. All inference (Whisper STT + Llama polish) happens
on-device via Apple's MLX framework. No API keys, no accounts, no network.

For cloud-extended dictation (lower latency, zero local RAM), see Susurro Pro
at https://susurro.live — it's a separate package that extends this one.
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ICONS_DIR = PACKAGE_DIR / "icons"

# --- STT backend ---
# OSS ships only "local". Extensions register additional backends at import
# time via susurro.backends.register_transcriber().
STT_BACKEND: str = "local"

# Model used by the LOCAL MLX backend. Larger = more accurate, slower.
#   mlx-community/whisper-large-v3-turbo  — recommended (~1.5 GB, ~6x faster decode)
#   mlx-community/whisper-large-v3-mlx    — best accuracy (~3 GB)
#   mlx-community/whisper-medium-mlx      — balanced (~1.5 GB)
LOCAL_STT_MODEL = "mlx-community/whisper-large-v3-turbo"

# Force a language ("es", "en", ...) or None for auto-detect.
LANGUAGE: str | None = None

# --- Polish (post-STT structuring) ---
#   off    — pass through raw STT
#   rules  — regex cleanup only (~5 ms, no network)
#   smart  — rules + LLM polish when ordinals/long-form patterns trigger
POLISH_MODE: str = "smart"

# Polish LLM backend. OSS ships only "local". Extensions can register others.
POLISH_BACKEND: str = "local"

# Model used by the LOCAL polish backend (mlx-lm).
#   mlx-community/Llama-3.2-3B-Instruct-4bit  — ~1.8 GB, ~50 tok/s on M3 Pro
#   mlx-community/Qwen2.5-3B-Instruct-4bit    — alternative multilingual
LOCAL_POLISH_MODEL = "mlx-community/Llama-3.2-3B-Instruct-4bit"

# --- Audio ---
SAMPLE_RATE = 16_000  # Whisper expects 16kHz mono.
CHANNELS = 1
INPUT_DEVICE: int | str | None = (
    None  # None = system default. Use index or name from `python -m sounddevice`.
)
MIN_RECORD_SECONDS = 0.3  # Anything shorter is treated as a misfire and ignored.
MAX_RECORD_SECONDS = 120  # Hard cap to prevent runaway recordings.

# --- Hotkey ---
# pynput Key name to use as push-to-talk. Hold to record, release to transcribe.
# Common choices: "alt_r" (right Option), "alt_l" (left Option), "ctrl_r", "f19".
HOTKEY = "alt_r"

# --- Behavior ---
TYPE_DELAY = 0.005  # Seconds between keystrokes; lower = faster typing.
PLAY_SOUNDS = True  # Subtle audio feedback on start/stop.
SHOW_NOTIFICATIONS = True
SHOW_INDICATOR = True  # Floating waveform pill near the bottom of the screen.

# --- Paths ---
HOME_DIR = Path.home() / ".susurro"
HOME_DIR.mkdir(exist_ok=True)
LOG_FILE = HOME_DIR / "susurro.log"
POLISH_LOG_FILE = HOME_DIR / "polish.jsonl"
