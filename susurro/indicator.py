"""Floating waveform indicator near the bottom of the active screen.

A small, dark, rounded pill containing 16 white bars that scroll right-to-left
as the user speaks. Mirrors WisprFlow's "I'm listening" affordance. The bars
reflect the current microphone RMS, smoothed lightly so they don't jitter on
quiet noise.

The window is borderless, click-through, and floats above all other windows
via `NSStatusWindowLevel`. It does not activate the app or steal focus.

A single timer running at 30 Hz on the main thread polls the recorder for
state — when `is_recording` becomes True, the window is shown; when False,
it's hidden. The hotkey listener never touches AppKit directly, which keeps
us safe from AppKit's main-thread requirement.
"""

from __future__ import annotations

import logging
import math
from enum import Enum

import objc
import rumps
from AppKit import (
    NSBackingStoreBuffered,
    NSBezierPath,
    NSColor,
    NSEvent,
    NSScreen,
    NSStatusWindowLevel,
    NSView,
    NSWindow,
)
from Foundation import NSPointInRect

logger = logging.getLogger(__name__)

NUM_BARS = 16
BAR_WIDTH = 3
BAR_GAP = 3
BAR_MIN_HEIGHT = 3
BAR_MAX_HEIGHT = 22
WINDOW_WIDTH = 140
WINDOW_HEIGHT = 40
BOTTOM_OFFSET = 80  # pixels above the bottom edge of the active screen
TICK_HZ = 30.0
BAR_SMOOTHING = 0.6  # EMA weight on new sample (0..1, higher = more responsive)

# Processing animation tuning — sinusoidal wave traveling left-to-right.
PROCESSING_PHASE_STEP = 0.30  # radians per tick (~9 rad/sec at 30 Hz)
PROCESSING_BAR_SPACING = 0.55  # radians between adjacent bars in the wave
PROCESSING_BASELINE = 0.30  # bar height when sin == 0
PROCESSING_AMPLITUDE = 0.35  # peak-to-peak / 2


class IndicatorState(str, Enum):
    """High-level state the indicator should display.

    Set from any thread via `WaveformIndicator.set_state`. The main-thread
    timer picks up the change on its next tick.
    """

    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class _WaveformView(NSView):
    """NSView subclass that paints the dark pill + animated bars."""

    def initWithFrame_(self, frame):
        self = objc.super(_WaveformView, self).initWithFrame_(frame)
        if self is None:
            return None
        self._bars = [0.0] * NUM_BARS
        return self

    @objc.python_method
    def set_bars(self, bars):
        self._bars = list(bars)
        self.setNeedsDisplay_(True)

    def drawRect_(self, _dirty_rect):
        bounds = self.bounds()
        # Background pill.
        radius = bounds.size.height / 2
        bg = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, radius, radius)
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.72).setFill()
        bg.fill()
        # Subtle outer border so it reads as a defined shape on light wallpapers.
        NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).setStroke()
        bg.setLineWidth_(1.0)
        bg.stroke()
        # Centered group of bars.
        total_w = NUM_BARS * BAR_WIDTH + (NUM_BARS - 1) * BAR_GAP
        cx = bounds.size.width / 2
        cy = bounds.size.height / 2
        start_x = cx - total_w / 2
        NSColor.whiteColor().setFill()
        for i, lvl in enumerate(self._bars):
            h = max(BAR_MIN_HEIGHT, min(BAR_MAX_HEIGHT, lvl * BAR_MAX_HEIGHT))
            x = start_x + i * (BAR_WIDTH + BAR_GAP)
            y = cy - h / 2
            bar = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(((x, y), (BAR_WIDTH, h)), 1.5, 1.5)
            bar.fill()


def _active_screen():
    """Pick the screen the user is most likely looking at (mouse cursor location)."""
    try:
        mouse = NSEvent.mouseLocation()
        for s in NSScreen.screens():
            if NSPointInRect(mouse, s.frame()):
                return s
    except Exception:
        logger.debug("active screen detection failed", exc_info=True)
    return NSScreen.mainScreen()


class WaveformIndicator:
    """Owns the floating window and a polling timer.

    `start()` and `stop()` must be called from the main thread (rumps' loop).
    The app sets the high-level state via `set_state(IndicatorState.X)` from
    any thread; the main-thread timer reacts on its next tick. This keeps the
    hotkey listener and worker thread decoupled from AppKit.
    """

    def __init__(self, recorder) -> None:
        self._recorder = recorder
        self._window: NSWindow | None = None
        self._view: _WaveformView | None = None
        self._timer: rumps.Timer | None = None
        self._history = [0.0] * NUM_BARS
        self._smoothed = 0.0
        self._is_shown = False
        self._state: IndicatorState = IndicatorState.IDLE
        self._processing_phase = 0.0

    def set_state(self, state: IndicatorState) -> None:
        """Switch the visual state. Safe to call from any thread."""
        if state == self._state:
            return
        # Reset processing phase on each entry so the wave always starts the
        # same way — visually consistent across short and long processing runs.
        if state == IndicatorState.PROCESSING:
            self._processing_phase = 0.0
        self._state = state

    # --- lifecycle ---
    def start(self) -> None:
        if self._timer is None:
            try:
                self._create_window()
            except Exception:
                logger.exception("indicator window creation failed; indicator disabled")
                return
            self._timer = rumps.Timer(self._tick, 1.0 / TICK_HZ)
        self._timer.start()
        logger.info("waveform indicator armed")

    def stop(self) -> None:
        if self._timer is not None:
            self._timer.stop()
        self._do_hide()

    # --- window construction ---
    def _create_window(self) -> None:
        if self._window is not None:
            return
        screen = _active_screen()
        frame = self._frame_for(screen)
        # styleMask=0 → borderless. defer=False so the window/backing exists immediately.
        win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, 0, NSBackingStoreBuffered, False
        )
        win.setBackgroundColor_(NSColor.clearColor())
        win.setOpaque_(False)
        win.setLevel_(NSStatusWindowLevel)
        win.setIgnoresMouseEvents_(True)
        win.setHasShadow_(False)
        win.setHidesOnDeactivate_(False)
        # No window-list / Mission Control entry.
        try:
            win.setCollectionBehavior_(
                # NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary
                # | NSWindowCollectionBehaviorIgnoresCycle
                1 | 16 | 64
            )
        except Exception:
            logger.debug("collection behavior set failed", exc_info=True)

        view = _WaveformView.alloc().initWithFrame_(((0, 0), (frame[1][0], frame[1][1])))
        win.setContentView_(view)
        self._window = win
        self._view = view

    @staticmethod
    def _frame_for(screen) -> tuple[tuple[float, float], tuple[float, float]]:
        sr = screen.frame()
        w, h = WINDOW_WIDTH, WINDOW_HEIGHT
        x = sr.origin.x + (sr.size.width - w) / 2
        y = sr.origin.y + BOTTOM_OFFSET
        return ((x, y), (w, h))

    # --- show / hide ---
    def _do_show(self) -> None:
        if self._window is None:
            return
        # Re-position in case the active screen changed since last show.
        self._window.setFrame_display_(self._frame_for(_active_screen()), True)
        self._history = [0.0] * NUM_BARS
        self._smoothed = 0.0
        if self._view is not None:
            self._view.set_bars(self._history)
        self._window.orderFrontRegardless()
        self._is_shown = True

    def _do_hide(self) -> None:
        if self._window is not None and self._is_shown:
            self._window.orderOut_(None)
        self._is_shown = False

    # --- 30 Hz tick on main thread ---
    def _tick(self, _sender) -> None:
        state = self._state
        wants_visible = state in (IndicatorState.RECORDING, IndicatorState.PROCESSING)
        if wants_visible and not self._is_shown:
            self._do_show()
        elif not wants_visible and self._is_shown:
            self._do_hide()
            return
        if not self._is_shown or self._view is None:
            return

        if state == IndicatorState.RECORDING:
            raw = self._recorder.peak_level()
            self._smoothed = BAR_SMOOTHING * raw + (1 - BAR_SMOOTHING) * self._smoothed
            self._history = [*self._history[1:], self._smoothed]
        else:  # PROCESSING
            self._processing_phase += PROCESSING_PHASE_STEP
            self._history = [
                PROCESSING_BASELINE
                + PROCESSING_AMPLITUDE * math.sin(self._processing_phase + i * PROCESSING_BAR_SPACING)
                for i in range(NUM_BARS)
            ]

        self._view.set_bars(self._history)
