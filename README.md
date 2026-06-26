# Anime Factory Pipeline

Generates an anime episode end to end from a JSON config:

1. **Script** — an LLM (Anthropic or OpenAI) writes the episode as structured scenes
   (scene description, dialogue, narrator lines, emotional tone), one scene per
   30-45 seconds of runtime.
2. **Image prompts** — each scene is turned into a Midjourney-style prompt, reusing
   "same character" continuity wording after a character's first appearance, and
   written to a text file for reference.
3. **Images** — Midjourney has no official API, so scene images are generated via
   the Stability AI image API instead (the practical automated substitute).
4. **Voiceover** — every dialogue/narration line is sent to the ElevenLabs TTS API
   using voice settings tuned for anime delivery (stability 0.35, similarity 0.85,
   style exaggeration 0.40, speaker boost on).
5. **Video assembly** — ffmpeg turns each scene's image + voiceover into a slow
   zoom clip, then concatenates all scenes into the finished vertical short
   (`episode.mp4`).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in the API keys you have
```

Requires `ffmpeg`/`ffprobe` on PATH for the video assembly step (`apt-get install ffmpeg`
or equivalent).

## Usage

```bash
python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --output-dir output
```

Add `--mock` to do a dry run with no API calls (writes placeholder script/audio/images
and still renders a real `episode.mp4` so you can check timing and layout). Other flags:
- `--skip-audio` — skip ElevenLabs
- `--skip-images` — skip image generation (also skips video, since it has nothing to render)
- `--skip-video` — skip the final ffmpeg assembly, keep script/prompts/images/audio

Output is written to `output/<series_slug>/episode_<n>/`:
- `script.json` — parsed scenes
- `image_prompts.txt` — one Midjourney-style prompt per scene
- `images/*.png` — one image per scene
- `audio/*.mp3` — one file per dialogue/narration line, in scene order
- `episode.mp4` — the assembled short
- `manifest.json` — summary of what was generated

## Episode config format

See `examples/shadow_protocol_ep3.json`. Each character needs a `name`, `role`,
`visual_description` (used for image prompts; `null` for the narrator), and a
`voice` — either a preset (`adam`, `antoni`, `bella`) or a raw ElevenLabs voice ID.

## Scope

This covers all three of the script/image/voiceover/video stages described in the
source workflow for the "anime story short" content type. The "lofi anime channel"
and "AI OST channel" formats mentioned alongside it aren't built — the source
material gave no concrete spec for those (no prompt templates, settings, or
examples), unlike the story-short pipeline.
