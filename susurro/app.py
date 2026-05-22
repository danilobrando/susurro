"""Susurro main daemon — menu bar app that glues recorder + STT + polish + typer."""

from __future__ import annotations

import logging
import queue
import subprocess
import threading
import time

import rumps

from . import config, permissions
from .audio import MicrophoneUnavailable, Recorder
from .backends import BackendError, BackendUnavailable, make_transcriber
from .hotkey import HotkeyListener
from .indicator import WaveformIndicator
from .logging_config import setup as setup_logging
from .polish import Polisher, append_to_log
from .typer import insert

logger = logging.getLogger(__name__)

TITLE_IDLE = ""
TITLE_RECORDING = " ● REC"
TITLE_PROCESSING = " …"

ICON_IDLE = str(config.ICONS_DIR / "idle.png")
ICON_RECORDING = str(config.ICONS_DIR / "recording.png")
ICON_PROCESSING = str(config.ICONS_DIR / "processing.png")

START_SOUND = "/System/Library/Sounds/Tink.aiff"
STOP_SOUND = "/System/Library/Sounds/Pop.aiff"


def _play(path: str) -> None:
    if not config.PLAY_SOUNDS:
        return
    try:
        subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        logger.debug("afplay failed", exc_info=True)


class SusurroApp(rumps.App):
    def __init__(self) -> None:
        super().__init__(
            name="Susurro",
            title=TITLE_IDLE,
            icon=ICON_IDLE,
            template=True,
            quit_button=None,
        )
        self.recorder = Recorder()
        self.transcriber = make_transcriber(config.STT_BACKEND)
        self.polisher = Polisher()
        self.hotkey: HotkeyListener | None = None
        self.indicator = WaveformIndicator(self.recorder)

        # Single-worker queue so transcriptions run one at a time, in order.
        self._jobs: queue.Queue = queue.Queue()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        self._record_started_at: float | None = None
        self._max_record_timer: threading.Timer | None = None
        self._last_text: str = ""
        self._use_clipboard: bool = True
        self._last_polish_summary: str = "no polish yet"

        self.menu = [
            rumps.MenuItem("Status: starting…", callback=None),
            None,
            rumps.MenuItem(f"Hotkey: {config.HOTKEY} (hold to talk)", callback=None),
            rumps.MenuItem(f"STT: {config.STT_BACKEND}", callback=None),
            rumps.MenuItem(f"Polish: {config.POLISH_MODE} ({config.POLISH_BACKEND})", callback=None),
            rumps.MenuItem("Last polish: —", callback=None),
            None,
            rumps.MenuItem("Insert via clipboard (Cmd+V)", callback=self._toggle_clipboard),
            rumps.MenuItem("Play feedback sounds", callback=self._toggle_sounds),
            rumps.MenuItem("Show waveform indicator", callback=self._toggle_indicator),
            None,
            (
                "Smart formatting",
                [
                    rumps.MenuItem("Off (raw STT)", callback=self._set_polish_off),
                    rumps.MenuItem("Rules only", callback=self._set_polish_rules),
                    rumps.MenuItem("Smart (LLM)", callback=self._set_polish_smart),
                ],
            ),
            None,
            rumps.MenuItem("Copy last transcript", callback=self._copy_last),
            None,
            (
                "Permissions",
                [
                    rumps.MenuItem("Open Microphone Settings…", callback=self._open_mic_settings),
                    rumps.MenuItem(
                        "Open Accessibility Settings…", callback=self._open_accessibility_settings
                    ),
                    rumps.MenuItem("Open Input Monitoring Settings…", callback=self._open_input_settings),
                ],
            ),
            rumps.MenuItem("Open log…", callback=self._open_log),
            rumps.MenuItem("Open polish log…", callback=self._open_polish_log),
            None,
            rumps.MenuItem(f"Susurro v{__import__('susurro').__version__}", callback=None),
            rumps.MenuItem("Quit", callback=self._quit),
        ]
        self.menu["Insert via clipboard (Cmd+V)"].state = 1
        self.menu["Play feedback sounds"].state = 1 if config.PLAY_SOUNDS else 0
        self.menu["Show waveform indicator"].state = 1 if config.SHOW_INDICATOR else 0
        self._refresh_polish_menu_state()

        if config.SHOW_INDICATOR:
            self.indicator.start()

        threading.Thread(target=self._warmup, daemon=True).start()

    # --- background warmup ---
    def _warmup(self) -> None:
        self._set_status(f"Status: warming {config.STT_BACKEND} STT…")
        try:
            self.transcriber.warmup()
        except (BackendUnavailable, BackendError) as e:
            logger.warning("STT backend %s unavailable (%s); falling back to local", config.STT_BACKEND, e)
            self._set_status(f"Status: {config.STT_BACKEND} unavailable, falling back to local")
            self.transcriber = make_transcriber("local")
            try:
                self.transcriber.warmup()
            except Exception as e2:
                logger.exception("local STT warmup also failed")
                self._set_status(f"Status: STT load failed — {e2}")
                return
        self._set_status(f"Status: warming {config.POLISH_BACKEND} polish…")
        try:
            self.polisher.warmup()
        except Exception:
            logger.exception("polish warmup failed; polish disabled")
        self._set_status("Status: idle")

    # --- hotkey handlers ---
    def on_hotkey_press(self) -> None:
        if self.recorder.is_recording:
            return
        try:
            self.recorder.start()
        except MicrophoneUnavailable as e:
            self._set_status("Status: mic unavailable — open Microphone Settings")
            logger.error("mic unavailable: %s", e)
            return
        self._set_status("Status: recording…")
        self.title = TITLE_RECORDING
        self.icon = ICON_RECORDING
        _play(START_SOUND)
        self._record_started_at = time.perf_counter()
        self._max_record_timer = threading.Timer(config.MAX_RECORD_SECONDS, self._auto_stop)
        self._max_record_timer.daemon = True
        self._max_record_timer.start()

    def on_hotkey_release(self) -> None:
        if not self.recorder.is_recording:
            return
        if self._max_record_timer is not None:
            self._max_record_timer.cancel()
            self._max_record_timer = None
        audio = self.recorder.stop()
        elapsed = time.perf_counter() - (self._record_started_at or 0)
        self._record_started_at = None
        _play(STOP_SOUND)
        if elapsed < config.MIN_RECORD_SECONDS or audio.size == 0:
            self._set_status("Status: too short, ignored")
            self._reset_idle()
            return
        self.title = TITLE_PROCESSING
        self.icon = ICON_PROCESSING
        self._set_status(f"Status: transcribing {elapsed:.1f}s…")
        self._jobs.put(audio)

    def _auto_stop(self) -> None:
        if self.recorder.is_recording:
            logger.info("hit MAX_RECORD_SECONDS=%s, stopping", config.MAX_RECORD_SECONDS)
            self.on_hotkey_release()

    # --- worker: audio → STT → polish → paste ---
    def _transcribe_with_fallback(self, audio):
        """Try the configured STT backend; on runtime failure, switch to local once."""
        try:
            return self.transcriber.transcribe(audio)
        except BackendError as e:
            if self.transcriber.name == "local":
                raise
            logger.warning(
                "STT backend %s failed at runtime (%s); switching to local for this and future requests",
                self.transcriber.name,
                e,
            )
            self._set_status(f"Status: {self.transcriber.name} failed → switching to local")
            if config.SHOW_NOTIFICATIONS:
                try:
                    rumps.notification(
                        "Susurro",
                        f"{self.transcriber.name} STT failed",
                        "Switched to local Whisper. Check your API key.",
                    )
                except Exception:
                    logger.debug("notification failed", exc_info=True)
            self.transcriber = make_transcriber("local")
            self.transcriber.warmup()
            return self.transcriber.transcribe(audio)

    def _worker_loop(self) -> None:
        while True:
            audio = self._jobs.get()
            try:
                raw = self._transcribe_with_fallback(audio)
                if not raw:
                    self._set_status("Status: idle (empty result)")
                    continue
                self._set_status(f"Status: polishing ({len(raw)} chars)…")
                try:
                    polished, meta = self.polisher.polish(raw)
                except Exception:
                    logger.exception("polish raised; falling back to raw STT")
                    polished, meta = raw, {"mode": "off", "llm_invoked": False, "elapsed_s": 0.0}
                self._last_text = polished
                self._last_polish_summary = self._format_polish_summary(raw, polished, meta)
                self._refresh_polish_menu_state()
                append_to_log(raw, polished, meta)
                try:
                    insert(polished, use_clipboard=self._use_clipboard)
                except Exception:
                    logger.exception("text insertion failed — accessibility permission missing?")
                    self._set_status("Status: paste failed — check Accessibility")
                    continue
                self._set_status(f"Status: inserted ({len(polished)} chars)")
                if config.SHOW_NOTIFICATIONS:
                    try:
                        rumps.notification("Susurro", "Transcribed", polished[:120])
                    except Exception:
                        logger.debug("notification failed", exc_info=True)
            except Exception as e:
                logger.exception("pipeline failed")
                self._set_status(f"Status: error — {e}")
            finally:
                self._reset_idle()
                self._jobs.task_done()

    def _reset_idle(self) -> None:
        self.title = TITLE_IDLE
        self.icon = ICON_IDLE

    @staticmethod
    def _format_polish_summary(raw: str, polished: str, meta: dict) -> str:
        mode = meta.get("mode", "?")
        if meta.get("llm_invoked"):
            tag = f"smart in {meta.get('elapsed_s', 0):.2f}s"
        elif mode == "off":
            tag = "off (raw)"
        else:
            tag = "rules only"
        delta = len(polished) - len(raw)
        sign = "+" if delta >= 0 else ""
        return f"Last polish: {tag}, {sign}{delta} chars"

    # --- menu callbacks ---
    def _toggle_clipboard(self, sender) -> None:
        self._use_clipboard = not self._use_clipboard
        sender.state = 1 if self._use_clipboard else 0

    def _toggle_sounds(self, sender) -> None:
        config.PLAY_SOUNDS = not config.PLAY_SOUNDS
        sender.state = 1 if config.PLAY_SOUNDS else 0

    def _toggle_indicator(self, sender) -> None:
        config.SHOW_INDICATOR = not config.SHOW_INDICATOR
        sender.state = 1 if config.SHOW_INDICATOR else 0
        if config.SHOW_INDICATOR:
            self.indicator.start()
        else:
            self.indicator.stop()

    def _set_polish_off(self, _sender) -> None:
        self._set_polish_mode("off")

    def _set_polish_rules(self, _sender) -> None:
        self._set_polish_mode("rules")

    def _set_polish_smart(self, _sender) -> None:
        self._set_polish_mode("smart")

    def _set_polish_mode(self, mode: str) -> None:
        config.POLISH_MODE = mode
        self.polisher = Polisher(mode=mode)
        if mode == "smart":
            threading.Thread(target=self.polisher.warmup, daemon=True).start()
        self._refresh_polish_menu_state()

    def _refresh_polish_menu_state(self) -> None:
        try:
            sub = self.menu["Smart formatting"]
            sub["Off (raw STT)"].state = 1 if config.POLISH_MODE == "off" else 0
            sub["Rules only"].state = 1 if config.POLISH_MODE == "rules" else 0
            sub["Smart (LLM)"].state = 1 if config.POLISH_MODE == "smart" else 0
        except Exception:
            logger.debug("polish menu state refresh failed", exc_info=True)
        # Update the static info lines.
        for item in self.menu.values():
            if not isinstance(item, rumps.MenuItem):
                continue
            if item.title.startswith("Polish: "):
                item.title = f"Polish: {config.POLISH_MODE} ({config.POLISH_BACKEND})"
            elif item.title.startswith("Last polish:"):
                item.title = self._last_polish_summary

    def _copy_last(self, _sender) -> None:
        if not self._last_text:
            return
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(self._last_text.encode("utf-8"))

    def _open_log(self, _sender) -> None:
        subprocess.Popen(["open", str(config.LOG_FILE)])

    def _open_polish_log(self, _sender) -> None:
        config.POLISH_LOG_FILE.touch(exist_ok=True)
        subprocess.Popen(["open", str(config.POLISH_LOG_FILE)])

    def _open_mic_settings(self, _sender) -> None:
        permissions.open_microphone()

    def _open_accessibility_settings(self, _sender) -> None:
        permissions.open_accessibility()

    def _open_input_settings(self, _sender) -> None:
        permissions.open_input_monitoring()

    def _quit(self, _sender) -> None:
        if self.hotkey is not None:
            self.hotkey.stop()
        self.indicator.stop()
        rumps.quit_application()

    # --- helpers ---
    def _set_status(self, status: str) -> None:
        for item in self.menu.values():
            if isinstance(item, rumps.MenuItem) and item.title.startswith("Status:"):
                item.title = status
                break


def main() -> None:
    setup_logging()
    logger.info(
        "starting Susurro (STT=%s, polish=%s/%s)",
        config.STT_BACKEND,
        config.POLISH_MODE,
        config.POLISH_BACKEND,
    )
    config.LOG_FILE.touch(exist_ok=True)
    app = SusurroApp()
    app.hotkey = HotkeyListener(on_press=app.on_hotkey_press, on_release=app.on_hotkey_release)
    app.hotkey.start()
    app.run()


if __name__ == "__main__":
    main()
