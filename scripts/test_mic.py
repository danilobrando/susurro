"""Quick sanity check: record 3 seconds, transcribe, print.

Run with:
    python scripts/test_mic.py

Useful for debugging without the menu bar / hotkey machinery.
"""

import time

from susurro.audio import Recorder
from susurro.stt import Transcriber


def main() -> None:
    print("Loading model… (first run downloads weights, may take a minute)")
    stt = Transcriber()
    stt.warmup()
    print("Model ready.")

    print("Recording 3 seconds — speak now.")
    rec = Recorder()
    rec.start()
    time.sleep(3.0)
    audio = rec.stop()
    print(f"Captured {audio.size / 16_000:.2f}s of audio.")

    text = stt.transcribe(audio)
    print(f"\n>>> {text!r}\n")


if __name__ == "__main__":
    main()
