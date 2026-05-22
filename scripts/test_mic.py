"""Quick sanity check: record 3 seconds, transcribe, optionally polish, print.

Run with:
    python scripts/test_mic.py            # uses config defaults (STT + polish)
    SUSURRO_STT_BACKEND=local python scripts/test_mic.py    # override

Useful for debugging without the menu bar / hotkey machinery.
"""

import os
import time

from susurro import config
from susurro.audio import Recorder
from susurro.backends import make_transcriber
from susurro.polish import Polisher

# Allow CLI overrides via env var so we don't need to edit config.py.
stt_backend = os.environ.get("SUSURRO_STT_BACKEND", config.STT_BACKEND)
polish_mode = os.environ.get("SUSURRO_POLISH_MODE", config.POLISH_MODE)


def main() -> None:
    print(f"Loading STT backend: {stt_backend}")
    stt = make_transcriber(stt_backend)
    stt.warmup()
    print("STT ready.")

    polisher = Polisher(mode=polish_mode)
    if polish_mode == "smart":
        print("Warming polish LLM…")
        polisher.warmup()

    print("Recording 3 seconds — speak now.")
    rec = Recorder()
    rec.start()
    time.sleep(3.0)
    audio = rec.stop()
    print(f"Captured {audio.size / 16_000:.2f}s of audio.")

    raw = stt.transcribe(audio)
    print(f"\n[raw] {raw!r}")

    polished, meta = polisher.polish(raw)
    print(f"[polished] {polished!r}")
    print(f"[meta] mode={meta['mode']} llm_invoked={meta['llm_invoked']} elapsed={meta['elapsed_s']:.2f}s")


if __name__ == "__main__":
    main()
