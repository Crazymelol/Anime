#!/bin/bash
# Double-click this to make a FREE gray test video (no keys, no money needed).
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "It looks like setup hasn't run yet."
  echo "Please follow Step 2 in START_HERE.md first."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

echo "Making a free test video... this takes a minute or two."
.venv/bin/python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --mock

echo ""
echo "Done! Opening the folder with your video (episode.mp4)."
open output/shadow_protocol/episode_3 2>/dev/null
echo "You can close this window."
