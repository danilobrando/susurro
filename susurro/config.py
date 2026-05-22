"""Centralized config — tweak these to match your machine and preferences.

API keys are NEVER read from this file. They come from environment variables:

    export SUSURRO_GROQ_API_KEY="gsk_..."        # or GROQ_API_KEY
    export SUSURRO_ANTHROPIC_API_KEY="sk-ant-..." # or ANTHROPIC_API_KEY
    export SUSURRO_OPENAI_API_KEY="sk-..."        # or OPENAI_API_KEY
    export SUSURRO_GEMINI_API_KEY="..."           # or GEMINI_API_KEY
"""

from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ICONS_DIR = PACKAGE_DIR / "icons"

# --- STT backend ---
# "local"        runs Whisper on-device via MLX (~3 GB RAM, no network).
# "groq"         uses Groq's hosted Whisper with the user's own API key.
# "susurro_pro"  uses Susurro Pro's hosted service (one-call STT + polish,
#                billed monthly, sign in via the menu).
STT_BACKEND: str = "local"

# Model used by the LOCAL MLX backend. Larger = more accurate, slower.
#   mlx-community/whisper-large-v3-mlx       (~3 GB, best)
#   mlx-community/whisper-large-v3-turbo     (~1.6 GB, ~6x faster)
#   mlx-community/whisper-medium-mlx         (~1.5 GB, balanced)
LOCAL_STT_MODEL = "mlx-community/whisper-large-v3-turbo"

# Model used by the GROQ STT backend.
#   whisper-large-v3-turbo  — fastest, recommended
#   whisper-large-v3        — slightly higher accuracy
GROQ_STT_MODEL = "whisper-large-v3-turbo"

# Force a language ("es", "en", ...) or None for auto-detect.
LANGUAGE: str | None = None

# --- Polish (post-STT structuring) ---
# Three modes:
#   off    — pass through raw STT
#   rules  — regex cleanup only (~5 ms, no network)
#   smart  — rules + LLM polish when ordinals/long-form patterns trigger
POLISH_MODE: str = "smart"

# Polish LLM backend.
#   "local"  — mlx-lm with a small local model (default for Susurro Local).
#   "groq"   — Groq's hosted Llama 3.3 70B (requires user's own API key).
POLISH_BACKEND: str = "local"

# Model used by the GROQ polish backend.
#   llama-3.3-70b-versatile  — best Spanish quality
#   llama-3.1-8b-instant     — faster, lower quality
GROQ_POLISH_MODEL = "llama-3.3-70b-versatile"

# Model used by the LOCAL polish backend (mlx-lm).
#   mlx-community/Llama-3.2-3B-Instruct-4bit  — ~1.8 GB, ~50 tok/s on M3 Pro
#   mlx-community/Qwen2.5-3B-Instruct-4bit    — alternative multilingual
LOCAL_POLISH_MODEL = "mlx-community/Llama-3.2-3B-Instruct-4bit"

# --- Susurro Pro (hosted SaaS) ---
SUSURRO_PRO_API_URL = "https://api.susurro.live"
SUSURRO_PRO_WEB_URL = "https://susurro.live"

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
