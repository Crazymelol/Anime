#!/bin/bash
# Double-click this to open the Anime Factory Studio in your browser.
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "It looks like setup hasn't run yet."
  echo "Please follow Step 2 in START_HERE.md first."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

echo "Starting the Studio... your browser will open in a moment."
echo "Keep this window open while you use it. (Close it to stop the Studio.)"
( sleep 2; open "http://127.0.0.1:8765" ) &
.venv/bin/python -m anime_factory.webui
