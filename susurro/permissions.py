"""Shortcuts that open System Settings directly at the relevant privacy pane,
plus programmatic permission prompts for Accessibility.

For a packaged .app, macOS won't add the bundle to the Accessibility list
until the app explicitly requests it. We do that on first launch via
PyObjC's AXIsProcessTrustedWithOptions so the user sees the native dialog
instead of having to drag-and-drop the .app into System Settings manually.
"""

from __future__ import annotations

import logging
import subprocess

logger = logging.getLogger(__name__)

_MICROPHONE = "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
_ACCESSIBILITY = "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
_INPUT_MONITORING = "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent"


def _open(url: str) -> None:
    subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_microphone() -> None:
    _open(_MICROPHONE)


def open_accessibility() -> None:
    _open(_ACCESSIBILITY)


def open_input_monitoring() -> None:
    _open(_INPUT_MONITORING)


def request_accessibility(prompt: bool = True) -> bool:
    """Ask macOS whether this process has Accessibility access; trigger the
    user-facing dialog if `prompt` is True. Returns True if already granted.

    The dialog is the standard one — once the user clicks "Open System Settings"
    the bundle is added to the Accessibility list and they only need to toggle
    the switch. No drag-and-drop required.
    """
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions
    except ImportError:
        logger.debug("ApplicationServices not available; skipping Accessibility request")
        return False
    options = {"AXTrustedCheckOptionPrompt": bool(prompt)}
    trusted = bool(AXIsProcessTrustedWithOptions(options))
    logger.info("Accessibility trust check: %s (prompted=%s)", trusted, prompt)
    return trusted


def request_microphone() -> None:
    """Trigger the native macOS microphone permission dialog.

    macOS Microphone settings has no '+' button — apps only appear in the list
    after they've requested access via AVCaptureDevice. Calling this synthesizes
    that request so the OS shows the standard 'X wants to access the microphone'
    popup. After the user clicks Allow, the bundle appears in System Settings
    with the toggle ON.
    """
    try:
        from AVFoundation import AVCaptureDevice
    except ImportError:
        logger.debug("AVFoundation not available; skipping microphone request")
        return
    # "soun" = AVMediaTypeAudio 4-char code. The completion handler is required
    # by the API but we don't need to react to the result — the wizard polls
    # status separately.
    AVCaptureDevice.requestAccessForMediaType_completionHandler_(
        "soun", lambda granted: logger.info("microphone access result: %s", granted)
    )
