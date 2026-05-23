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

# --- 3. Python 3.10+ ---
if ! command -v python3 >/dev/null 2>&1; then
    err "Python 3 not found."
    echo "  Install via Homebrew: brew install python@3.12"
    exit 1
fi
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    err "Python 3.10+ required. Found: $PY_VERSION"
    echo "  Install a newer Python: brew install python@3.12"
    exit 1
fi
ok "Python $PY_VERSION detected"

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

# --- 5. Install Susurro ---
# Prefer PyPI (faster, signed wheels). Fall back to GitHub for unreleased builds.
info "Installing Susurro from PyPI… (this can take a minute — pulls MLX wheels)"
if pipx install --force susurro 2>&1 | grep -qi "no matching distribution\|could not find"; then
    info "PyPI install failed (package may not be published yet); falling back to GitHub"
    pipx install --force git+https://github.com/danilobrando/susurro.git@main
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

${YELLOW}1.${NC} Get a free Groq API key (covers normal personal use):
   ${BLUE}https://console.groq.com/keys${NC}

${YELLOW}2.${NC} Add the key to your shell so Susurro can find it. Open your shell rc file
   in an editor — usually ${BOLD}~/.zshrc${NC} — and add this line:

     ${GREEN}export SUSURRO_GROQ_API_KEY="gsk_..."${NC}

   Then reload it:

     ${GREEN}source ~/.zshrc${NC}

   Verify (should print ${BOLD}gsk_${NC}):
     ${GREEN}echo "\${SUSURRO_GROQ_API_KEY:0:4}"${NC}

${YELLOW}3.${NC} Launch the daemon:

     ${GREEN}susurro${NC}

${YELLOW}4.${NC} The first time you use the hotkey, macOS will prompt for ${BOLD}3 permissions${NC}:
     • Microphone (capture audio)
     • Accessibility (paste at cursor)
     • Input Monitoring (global hotkey)
   The menu bar dropdown has direct links to each pane. After granting them,
   ${BOLD}fully quit and relaunch the terminal${NC} before opening Susurro again.

${YELLOW}5.${NC} Hold the ${BOLD}right Option (⌥)${NC} key, talk, release. The transcript pastes
   at your cursor. You'll see a floating waveform pill at the bottom-center
   of the screen while recording + processing.

Docs:   ${BLUE}https://github.com/danilobrando/susurro${NC}
Issues: ${BLUE}https://github.com/danilobrando/susurro/issues${NC}

EOF
