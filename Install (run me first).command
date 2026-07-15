#!/bin/bash
# Double-click this ONCE. It installs everything the project needs, automatically.
# Κάνε διπλό κλικ ΜΙΑ φορά. Εγκαθιστά αυτόματα ό,τι χρειάζεται.
cd "$(dirname "$0")"

echo "==============================================="
echo "  Anime Factory — automatic setup / αυτόματη εγκατάσταση"
echo "==============================================="
echo ""
echo "This can take 10-20 minutes. Leave the window open."
echo "If it asks for a password, type your Mac password"
echo "(nothing appears while typing — that's normal) and press Enter."
echo ""

fail() {
  echo ""
  echo "*** Something went wrong at step: $1 ***"
  echo "Take a screenshot of this window and send it to Claude — easy fix."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
}

# Load Homebrew into this shell if it's installed (Apple Silicon or Intel path).
load_brew() {
  [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
  [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
}
load_brew

NEED_PY=false; command -v python3 >/dev/null 2>&1 || NEED_PY=true
NEED_FF=false; command -v ffmpeg  >/dev/null 2>&1 || NEED_FF=true

if { $NEED_PY || $NEED_FF; } && ! command -v brew >/dev/null 2>&1; then
  echo "--- Step 1/4: Installing Homebrew (the installer's installer)..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || fail "Homebrew"
  load_brew
  command -v brew >/dev/null 2>&1 || fail "Homebrew (not found after install)"
else
  echo "--- Step 1/4: Homebrew — OK (or not needed)"
fi

if $NEED_PY; then
  echo "--- Step 2/4: Installing Python..."
  brew install python || fail "Python"
else
  echo "--- Step 2/4: Python — already installed"
fi

if $NEED_FF; then
  echo "--- Step 3/4: Installing ffmpeg (the video tool)..."
  brew install ffmpeg || fail "ffmpeg"
else
  echo "--- Step 3/4: ffmpeg — already installed"
fi

echo "--- Step 4/4: Setting up the project..."
if [ ! -d .venv ]; then
  python3 -m venv .venv || fail "project environment"
fi
.venv/bin/pip install --quiet --upgrade pip || true
.venv/bin/pip install --quiet -r requirements.txt || fail "project packages"

echo ""
echo "==============================================="
echo "  ALL DONE! / ΕΤΟΙΜΟ!"
echo "==============================================="
echo ""
echo "Next: double-click 'Open Studio.command' and make your first video."
echo "Επόμενο βήμα: διπλό κλικ στο 'Open Studio.command'."
echo ""
echo "Press Enter to close."
read
