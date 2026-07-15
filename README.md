# Anime Factory Pipeline

Generates an anime episode end to end from a JSON config:

1. **Script** — an LLM (Anthropic or OpenAI) writes the episode as structured scenes
   (scene description, camera shot, lighting mood, dialogue, narrator lines,
   emotional tone), one scene per 30-45 seconds of runtime, plus a scroll-stopping
   "hook" line for the opening title card.
2. **Image prompts** — each scene is turned into a Midjourney-style prompt, reusing
   "same character" continuity wording after a character's first appearance, and
   written to a text file for reference.
3. **Images** — Midjourney has no official API, so scene images are generated via
   the Stability AI image API instead (the practical automated substitute).
4. **Voiceover** — every dialogue/narration line is sent to the ElevenLabs TTS API
   using voice settings tuned for anime delivery (stability 0.35, similarity 0.85,
   style exaggeration 0.40, speaker boost on).
5. **Video assembly** — ffmpeg opens with a 1.8s hook title card, turns each
   scene's image + voiceover into a slow zoom clip with burned-in captions timed
   to each line's real audio duration, concatenates everything into the finished
   vertical short (`episode.mp4`), and optionally mixes a quiet music bed under
   the voiceover. Pass `--no-captions` to turn the on-screen text off.

Extras in the episode config:
- `"style"` — art direction preset: `dark_fantasy` (default), `wholesome`,
  `cyberpunk`, or your own raw style text
- `"music"` — path to a music file to loop quietly under the voice (a
  `music.mp3` next to the project is picked up automatically)

The pipeline validates your config and API keys up front — a typo'd voice name,
a missing narrator, or a missing key fails immediately with a clear message
before any paid API call is made. The CLI loads `.env` automatically.

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

Add `--mock` to do a dry run with no API calls: placeholder script and images, and
real (silent) mp3s sized to estimated speech time — so the rendered `episode.mp4`
previews the true caption timing and layout. Other flags:
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

## Free script writing with OpenRouter

The script stage works with any OpenAI-compatible endpoint. To use OpenRouter's
free models (writes the episode for $0 — quality is below Claude/GPT-4o but fine
for testing), set in `.env`:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-or-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

Note this only covers the writing stage — images (Stability) and voice
(ElevenLabs) are separate services with their own keys.

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
