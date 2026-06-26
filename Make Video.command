#!/bin/bash
# Double-click this to make a REAL video (needs your 3 keys set up in .env first).
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "It looks like setup hasn't run yet."
  echo "Please follow Step 2 in START_HERE.md first."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

if [ ! -f .env ]; then
  echo "Your keys aren't set up yet, so a real video can't be made."
  echo "Follow Steps 4 and 5 in START_HERE.md (sign up + paste keys),"
  echo "or double-click 'Test Video (free).command' to make a free gray test instead."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

echo "Making your video... this takes a few minutes."
set -a; . ./.env; set +a
.venv/bin/python -m anime_factory.cli --config examples/shadow_protocol_ep3.json

echo ""
echo "Done! Opening the folder with your video (episode.mp4)."
open output/shadow_protocol/episode_3 2>/dev/null
echo "You can close this window."
