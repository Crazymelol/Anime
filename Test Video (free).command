#!/bin/bash
# Double-click this to make a FREE test video (no keys, no money needed).
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "It looks like setup hasn't run yet."
  echo "Please follow Step 2 in START_HERE.md first."
  echo ""
  echo "Press Enter to close."
  read
  exit 1
fi

# Your own story (my_episode.json) wins; otherwise the built-in example runs.
CONFIG="examples/shadow_protocol_ep3.json"
if [ -f my_episode.json ]; then
  CONFIG="my_episode.json"
  echo "Using your story file: my_episode.json"
else
  echo "Using the built-in example story. (To use your own, save it as my_episode.json"
  echo "in this folder — see START_HERE.md.)"
fi

echo "Making a free test video... this takes a minute or two."
RUN_LOG=$(mktemp)
.venv/bin/python -m anime_factory.cli --config "$CONFIG" --mock 2>&1 | tee "$RUN_LOG"
STATUS=${PIPESTATUS[0]}
EPISODE_DIR=$(sed -n 's/^Episode written to //p' "$RUN_LOG" | tail -1)
rm -f "$RUN_LOG"

if [ "$STATUS" -eq 0 ] && [ -n "$EPISODE_DIR" ]; then
  echo ""
  echo "Done! Opening the folder with your video (episode.mp4)."
  open "$EPISODE_DIR" 2>/dev/null
else
  echo ""
  echo "*** Something went wrong — no video was made. ***"
  echo "The messages above say why. Common causes: setup step missed, or a typo"
  echo "in my_episode.json. Copy the text above if you need help."
fi
echo ""
echo "Press Enter to close."
read
