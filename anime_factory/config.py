"""Shared constants and small helpers used across the pipeline.

Voice IDs below are ElevenLabs' public premade voices (Adam/Antoni/Bella),
matching the voices called out in the source workflow. Override with a raw
voice_id in an episode config if your account uses different/cloned voices.
"""

import os
from pathlib import Path

VOICE_PRESETS = {
    "adam": "pNInz6obpgDQGcFmaJgB",
    "antoni": "ErXwobaYiN019PkySvjV",
    "bella": "EXAVITQu4vr4xnSDxMaL",
}

# Stability 0.35 / similarity 0.85 / style 0.40 / speaker boost on
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.35,
    "similarity_boost": 0.85,
    "style": 0.40,
    "use_speaker_boost": True,
}

# Single source of truth for the output canvas; captions/image/video all derive
# from these so a format change can't leave the modules out of sync.
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_SIZE = f"{VIDEO_WIDTH}x{VIDEO_HEIGHT}"
FPS = 25

# Pure descriptive text — no Midjourney CLI flags. The prompts go verbatim to
# the Stability API (which takes aspect_ratio as a separate parameter), and the
# wording matches the vertical 9:16 short the pipeline renders.
DEFAULT_IMAGE_STYLE_SUFFIX = (
    "cinematic anime style, ultra detailed, dramatic lighting, "
    "vertical composition, 4k"
)

API_TIMEOUT = 60


def load_env_file(path: Path | str = ".env") -> None:
    """Load KEY=VALUE lines from a .env file into os.environ (existing vars win).

    Minimal stdlib parser so the documented `python -m anime_factory.cli` path
    sees the same keys as the launcher scripts, without a dotenv dependency.
    """
    path = Path(path)
    if not path.is_file():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value
