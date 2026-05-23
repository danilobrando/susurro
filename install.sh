#!/usr/bin/env bash
# Susurro installer — one-line install for macOS.
#
#   curl -fsSL https://raw.githubusercontent.com/danilobrando/susurro/main/install.sh | bash
#
# This script:
#   1. Checks macOS + Apple Silicon + Python 3.10+
#   2. Installs pipx via Homebrew if missing
#   3. Installs Susurro via pipx (from GitHub)
#   4. Prints the next-step instructions for API key + permissions

set -euo pipefail

GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
RED=$'\033[0;31m'
BLUE=$'\033[0;34m'
BOLD=$'\033[1m'
NC=$'\033[0m'

info()  { echo "${BLUE}==>${NC} $1"; }
ok()    { echo "${GREEN}✓${NC} $1"; }
warn()  { echo "${YELLOW}!${NC} $1"; }
err()   { echo "${RED}✗${NC} $1" >&2; }
title() { echo; echo "${BOLD}$1${NC}"; }

# --- 1. macOS ---
if [ "$(uname)" != "Darwin" ]; then
    err "Susurro is macOS-only. Detected: $(uname)"
    exit 1
fi
ok "macOS detected"

# --- 2. Apple Silicon ---
if [ "$(uname -m)" != "arm64" ]; then
    err "Susurro requires Apple Silicon (M1 or later). Intel Macs aren't supported in this release."
    err "Reason: the local Whisper backend depends on Apple's MLX framework."
    exit 1
fi
ok "Apple Silicon detected"

# --- 3. Pick a Python (3.10-3.13). Skip 3.14: Homebrew's build has a known
#       libexpat ABI mismatch that crashes pipx mid-install on macOS arm64.
PYTHON=""
for v in 3.13 3.12 3.11 3.10; do
    if command -v "python$v" >/dev/null 2>&1; then
        PYTHON="$(command -v "python$v")"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    # Fall back to the default python3 only if its minor is 10..13.
    if command -v python3 >/dev/null 2>&1; then
        DEFAULT_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
        if [ "$DEFAULT_MINOR" -ge 10 ] && [ "$DEFAULT_MINOR" -le 13 ]; then
            PYTHON="$(command -v python3)"
        fi
    fi
fi
if [ -z "$PYTHON" ]; then
    err "Need Python 3.10, 3.11, 3.12, or 3.13. Install one: brew install python@3.12"
    exit 1
fi
PY_VERSION=$("$PYTHON" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
ok "Python $PY_VERSION detected at $PYTHON"

# --- 4. pipx ---
if ! command -v pipx >/dev/null 2>&1; then
    info "pipx not found — installing via Homebrew…"
    if ! command -v brew >/dev/null 2>&1; then
        err "Homebrew not found. Install it from https://brew.sh, then re-run this script."
        exit 1
    fi
    brew install pipx
    pipx ensurepath
fi
ok "pipx ready"

# --- 5. Install Susurro from PyPI ---
info "Installing Susurro from PyPI… (~1 min the first time, pulls MLX wheels)"
if ! pipx install --force --python "$PYTHON" susurro 2>&1; then
    err "PyPI install failed. Falling back to GitHub main…"
    pipx install --force --python "$PYTHON" git+https://github.com/danilobrando/susurro.git@main
fi
ok "Susurro installed"

# --- 6. Verify CLI ---
if command -v susurro >/dev/null 2>&1; then
    INSTALLED_VERSION=$(susurro --version 2>/dev/null || echo "unknown")
    ok "$INSTALLED_VERSION on PATH"
else
    warn "susurro command not on PATH. Run: pipx ensurepath && exec \$SHELL -l"
fi

# --- 7. Next steps ---
title "Next steps"
cat <<EOF

${YELLOW}1.${NC} Launch the daemon:

     ${GREEN}susurro${NC}

   The first run downloads ~5 GB of model weights (Whisper + Llama 3.2 3B),
   one time only. After that, everything runs offline on your Mac.

${YELLOW}2.${NC} The first time you use the hotkey, macOS will prompt for ${BOLD}3 permissions${NC}:
     • Microphone (capture audio)
     • Accessibility (paste at cursor)
     • Input Monitoring (global hotkey)
   The menu bar dropdown has direct links to each pane. After granting them,
   ${BOLD}fully quit and relaunch the terminal${NC} before opening Susurro again.

${YELLOW}3.${NC} Hold the ${BOLD}right Option (⌥)${NC} key, talk, release. Polished text pastes
   at the cursor. A floating waveform pill at the bottom of the screen shows
   it's listening, then animates while it transcribes.

${YELLOW}4.${NC} (Optional) For zero local RAM + faster latency, upgrade to Susurro Pro:
   ${BLUE}https://susurro.live${NC}  · same hotkey, cloud Whisper + Llama 70B.

Docs:   ${BLUE}https://github.com/danilobrando/susurro${NC}
Issues: ${BLUE}https://github.com/danilobrando/susurro/issues${NC}

EOF
