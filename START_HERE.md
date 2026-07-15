# Make Your First Anime Video (Mac) — Plain English

No coding needed. Follow the steps in order. You'll end up with a finished
vertical video (like a TikTok) made from a story idea.

There's a **free test mode** that needs no sign-ups and no money — do that first
to prove it works, then add the paid helpers when you're ready.

---

## Step 1 — Get the project folder onto your Mac

1. Go to **github.com** and open your repo named **anime**.
2. Near the top-left there's a button that shows a branch name. Click it and choose
   **`claude/new-session-yh5vpm`** (that's where the tool lives).
3. Click the green **`< > Code`** button → **Download ZIP**.
4. Open your **Downloads** folder and **double-click the ZIP** to unzip it.
   You'll get a folder like `anime-claude-new-session-yh5vpm`.
5. Drag that folder onto your **Desktop** so it's easy to find.

---

## Step 2 — One-time install (about 15 min)

1. Open **Terminal**: press **Cmd + Space**, type `Terminal`, press **Enter**.
   A plain window opens — that's normal.
2. Copy each block below, paste into Terminal, press **Enter**. Let each finish
   before doing the next.

**a) Install Homebrew** (the thing that installs everything else):
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
> It may ask for your Mac password. Type it (the dots won't show — that's normal),
> press Enter. This one takes the longest.

**b) Install Python and the video tool:**
```
brew install python ffmpeg
```

**c) Set up the project.** Type `cd ` (the word cd then a space), then **drag your
project folder from the Desktop into the Terminal window** and press **Enter**.
Then paste:
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

That's the whole techie part. You never do it again.

---

## Step 3 — Free test (no money, no sign-ups)

Still in Terminal, paste:
```
.venv/bin/python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --mock
```

Wait a minute. It makes a **gray placeholder video** just to prove everything works.
Find it here and double-click to watch:
```
output/shadow_protocol/episode_3/episode.mp4
```

If you see a gray video play — congratulations, the machine works. Now make it real.

---

## Step 4 — Sign up for the 3 real helpers

Each gives you a **key** (a long secret code). Copy each into a notes app.

| Helper | What it does | Sign up at |
|--------|--------------|------------|
| **Claude** | Writes the story | console.anthropic.com |
| **Stability AI** | Draws the scenes | platform.stability.ai |
| **ElevenLabs** | Does the voice | elevenlabs.io |

On each site, find **"API Keys"**, click **"Create key"**, copy what it shows you.

---

## Step 5 — Paste your keys in (once)

1. In the project folder, find the file `.env.example`.
2. Make a copy, rename the copy to exactly **`.env`** (yes, starting with a dot).
3. Open it and paste your 3 keys after the `=` signs:
```
ANTHROPIC_API_KEY=your-claude-key
ELEVENLABS_API_KEY=your-elevenlabs-key
STABILITY_API_KEY=your-stability-key
```
4. Save.

---

## Step 6 — Make a REAL video

Start with the **tiny test story** — it's 2 scenes, about 1 minute, and costs
only a few cents, so you can confirm your keys work before making anything big:
```
.venv/bin/python -m anime_factory.cli --config examples/first_real_test.json
```
Once that works, make the full example (or your own story):
```
.venv/bin/python -m anime_factory.cli --config examples/shadow_protocol_ep3.json
```

Your finished video appears at `output/shadow_protocol/episode_3/episode.mp4`.
Upload it anywhere.

---

## Changing the story

1. Make a **copy** of `examples/shadow_protocol_ep3.json`.
2. Rename the copy to exactly **`my_episode.json`** and put it in the main
   project folder (next to the .command buttons).
3. Open it and change the words for **series_title**, **premise**, and the
   **characters** (names + what they look like). Keep the quote marks and
   commas where they are — just swap the words.
4. Double-click **Make Video** (or run Step 6 again). The buttons automatically
   use `my_episode.json` when it exists — they'll say so at the top.

---

## Optional: FREE images and voice (no sign-ups at all)

If you have the **Draw Things** app and **TTS v2 (XTTS)** on your Mac, you can
skip paying for Stability and ElevenLabs completely:

1. **Draw Things**: open its Settings and turn on **API Server**. Load an
   anime-style model. Leave the app running.
2. **Voice**: in Terminal run
   `tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2`
   and leave that window open.
3. In your `.env` file add these two lines:
```
IMAGE_PROVIDER=drawthings
TTS_PROVIDER=xtts
```
4. In `my_episode.json`, set each character's `"voice"` to an XTTS voice name
   like `"Damien Black"` (male) or `"Claribel Dervla"` (female) — or a path to
   a short `.wav` recording of any voice to imitate it.
5. **Greek episodes**: add `"language": "el"` to `my_episode.json` — the story,
   captions, and voice will all be in Greek.

It runs slower than the paid services (your Mac does the drawing and speaking),
but every video is 100% free.

## Optional: background music

Drop any music file named **`music.mp3`** into the main project folder and it
will automatically play quietly under the voice in every video. (Use music you
have the rights to — royalty-free tracks are easy to find.)

## Honest expectations

- Cost: roughly **under $1 per short video** once set up. Sign-up is free.
- The TikTok's "$8k/month" is marketing. This does the *making* for you. Growing a
  channel (posting often, getting views) is still your job.
- First videos won't be perfect — tweak the premise and character looks to improve.
- Stuck on any step? Tell me which step number and what you saw, and I'll help.
