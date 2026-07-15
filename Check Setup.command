#!/bin/bash
# Double-click this to check that everything is connected (Draw Things, voice,
# keys, ffmpeg). It changes nothing and costs nothing.
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "It looks like setup hasn't run yet."
  echo "Please follow Step 2 in START_HERE.md first."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

.venv/bin/python -m anime_factory.check_setup
echo "Press Enter to close."
read
