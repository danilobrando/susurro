"""Centralized config — tweak these to match your machine and preferences."""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ICONS_DIR = PACKAGE_DIR / "icons"

# --- STT model ---
# Default is large-v3 (best accuracy, ~3GB). Already cached on this machine.
# For WisprFlow-tier latency switch to turbo — ~6x faster decode with near-identical
# accuracy on Apple Silicon, but adds a one-time ~1.6GB download:
#     MODEL_REPO = "mlx-community/whisper-large-v3-turbo"
# Smaller options: "mlx-community/whisper-medium-mlx", "...whisper-small-mlx".
MODEL_REPO = "mlx-community/whisper-large-v3-mlx"

# Force a language ("es", "en", ...) or leave None for auto-detect.
LANGUAGE: str | None = None

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

# --- Paths ---
HOME_DIR = Path.home() / ".susurro"
HOME_DIR.mkdir(exist_ok=True)
LOG_FILE = HOME_DIR / "susurro.log"
