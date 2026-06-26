# Make Your First Anime Video — Plain English Guide

No coding knowledge needed. Just follow the steps in order.

You will end up with a finished vertical video (like a TikTok) made from a story idea.

---

## What you need first

- A **computer** (Mac or Windows). This does not run on a phone.
- About **30 minutes** for the one-time setup.
- A little money for the 3 services below (under $1 per video once running). Sign-up is free.

---

## Step 1 — Sign up for the 3 helpers

Each one gives you a **key** (a long secret code). Copy each key somewhere safe
(like a notes app). You'll paste all 3 in during Step 3.

| Helper | What it does | Where to sign up |
|--------|--------------|------------------|
| **Claude** (Anthropic) | Writes the story | console.anthropic.com |
| **Stability AI** | Draws the scenes | platform.stability.ai |
| **ElevenLabs** | Does the voice | elevenlabs.io |

> On each site, look for a page called **"API Keys"** and click **"Create key"**.
> Copy the key it shows you.

---

## Step 2 — Get the tool onto your computer

Ask whoever set this up (or a tech-savvy friend) to do this one-time install:

1. Install **Python** (python.org) and **ffmpeg** (the video tool).
2. Download this project folder.
3. Open the folder in the "Terminal" and run: `pip install -r requirements.txt`

That's the only "techie" part. After this, you never touch it again.

---

## Step 3 — Paste in your 3 keys

1. In the project folder, find the file named `.env.example`.
2. Make a copy of it and rename the copy to just `.env`
3. Open `.env` and paste your keys after the `=` signs, like this:

```
ANTHROPIC_API_KEY=paste-your-claude-key-here
ELEVENLABS_API_KEY=paste-your-elevenlabs-key-here
STABILITY_API_KEY=paste-your-stability-key-here
```

Save the file. Done — you only do this once.

---

## Step 4 — Write your story idea

Open the file `examples/shadow_protocol_ep3.json`. It's already filled in with an
example. To make your own, just change the wording:

- **series_title** — the name of your show
- **premise** — what happens in this episode (one or two sentences)
- **characters** — who's in it and what they look like

Keep the same shape (the quote marks and commas matter), just swap the words.

---

## Step 5 — Make the video

In the Terminal, from the project folder, type this one line and press Enter:

```
python -m anime_factory.cli --config examples/shadow_protocol_ep3.json
```

Wait a minute or two. When it finishes, your video is at:

```
output/your_show_name/episode_3/episode.mp4
```

Double-click it to watch. Then upload it wherever you want.

---

## Want to test it for free first?

Add the word `--mock` to the end of the command:

```
python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --mock
```

This makes a **gray placeholder video** with no real art or voice, using **no money
and no keys**. It's just to prove everything is wired up before you spend anything.

---

## Honest expectations

- Cost: roughly **under $1 per short video** once set up.
- The TikTok's "$8k/month" is marketing. This tool does the *making*. Growing a
  channel (posting often, getting views) is still up to you.
- First videos won't be perfect. Tweak the **premise** and character
  **descriptions** to improve the look and story.
