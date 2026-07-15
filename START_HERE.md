# Make Your First Anime Video (Mac) — Plain English

No coding needed. Follow the steps in order. You'll end up with a finished
vertical video (like a TikTok) made from a story idea.

> **The easy way, once Steps 1–2 are done:** double-click **`Open Studio.command`**.
> It opens a page in your browser where you write the story in a form, check
> that everything is connected, press one button, and watch the video get made.
> Everything below still works too — the Studio is just the friendliest door.

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

## Step 2 — One-time install (automatic!)

Just **double-click `Install (run me first).command`** in the project folder
and leave the window open for 10–20 minutes. It installs everything by itself.

Two things it may ask:
- Your **Mac password** — type it (nothing shows while typing, that's normal)
  and press Enter.
- If macOS blocks the file ("unidentified developer"): **right-click** the file
  → **Open** → **Open**. You only do this once.

When it says **ALL DONE / ΕΤΟΙΜΟ**, the techie part is over — forever.

<details>
<summary>Manual version (only if the automatic one fails)</summary>

1. Open **Terminal** (Cmd + Space, type `Terminal`, Enter) and paste, one at a time:
```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
```
brew install python ffmpeg
```
2. Type `cd ` (with a space), drag the project folder into the window, Enter. Then:
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```
</details>

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

## Not sure if everything is connected?

Double-click **`Check Setup.command`** any time. It tests everything on your
Mac — Draw Things connection, the voice server, your keys, the video tool —
and tells you exactly what's OK and what to fix. It changes nothing and costs
nothing.

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
