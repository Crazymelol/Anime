# Anime Factory Pipeline

Generates an anime episode end to end from a JSON config:

1. **Script** — an LLM (Anthropic or OpenAI) writes the episode as structured scenes
   (scene description, dialogue, narrator lines, emotional tone), one scene per
   30-45 seconds of runtime.
2. **Image prompts** — each scene is turned into a Midjourney-ready prompt, reusing
   "same character" continuity wording after a character's first appearance.
   Midjourney has no official API, so these prompts are written to a text file for
   you to paste in yourself rather than auto-submitted.
3. **Voiceover** — every dialogue/narration line is sent to the ElevenLabs TTS API
   using voice settings tuned for anime delivery (stability 0.35, similarity 0.85,
   style exaggeration 0.40, speaker boost on).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the API keys you have
```

## Usage

```bash
python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --output-dir output
```

Add `--mock` to do a dry run with no API calls (writes placeholder script/audio so you
can check the pipeline and output layout). Add `--skip-audio` to skip ElevenLabs and
only produce the script + image prompts.

Output is written to `output/<series_slug>/episode_<n>/`:
- `script.json` — parsed scenes
- `image_prompts.txt` — one Midjourney prompt per scene
- `audio/*.mp3` — one file per dialogue/narration line
- `manifest.json` — summary of what was generated

## Episode config format

See `examples/shadow_protocol_ep3.json`. Each character needs a `name`, `role`,
`visual_description` (used for image prompts; `null` for the narrator), and a
`voice` — either a preset (`adam`, `antoni`, `bella`) or a raw ElevenLabs voice ID.

## Scope

This covers the script/prompts/voiceover stages described in the source workflow.
It does not assemble a finished video (image generation, ffmpeg compositing,
captions) — that's a natural next step once you've validated the script and voice
quality.
