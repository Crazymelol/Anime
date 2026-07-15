# Anime Factory — project notes for Claude

This project generates anime short videos end-to-end: LLM script → scene
images → voiceover → ffmpeg vertical video with burned-in captions.

## About the owner

The owner is non-technical and prefers plain language (Greek or simple
English). When they ask for help, do the work for them rather than giving
instructions — run commands yourself, confirm results, and explain what
happened in one or two friendly sentences. Never paste raw tracebacks at them;
diagnose and fix.

## Setup on this machine

Run the whole setup with: `bash "Install (run me first).command"` — it is
idempotent (installs Homebrew/python/ffmpeg only if missing, then creates
.venv and installs requirements.txt). If the owner asks "install everything" /
"δεν μπορώ με τις εγκαταστάσεις", run that script and verify with:
`.venv/bin/python -m anime_factory.check_setup`

## Key commands

- Studio (web UI the owner uses): `.venv/bin/python -m anime_factory.webui` → http://127.0.0.1:8765
- Free test video: `.venv/bin/python -m anime_factory.cli --config examples/shadow_protocol_ep3.json --mock`
- Tests: `.venv/bin/python -m pytest tests/ -q` (needs ffmpeg for the video tests)
- Lint: `ruff check anime_factory tests`

## Configuration (.env)

- Providers: `IMAGE_PROVIDER=stability|drawthings`, `TTS_PROVIDER=elevenlabs|xtts`
- The owner runs Draw Things (port 7859, needs Protocol=HTTP, TLS off) with the
  Anything V3 model, and a local XTTS-v2 `tts-server` for voice; both free/local.
- `.env` holds secrets — NEVER commit it, never print key values.
- Episode configs support `"language": "el"` (Greek script + captions + voice).

## Conventions

- All media constants (canvas size, FPS) live in `anime_factory/config.py`.
- LLM script output must pass `validation.canonicalize_script` before use.
- Mock mode must stay fully offline and free (silent real mp3s, solid-color
  images) — don't add network calls to it.
- Keep user-facing text (launchers, Studio, errors) plain-language, no jargon.
