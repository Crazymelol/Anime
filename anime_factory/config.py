"""Shared constants: voice presets and default ElevenLabs voice settings.

Voice IDs below are ElevenLabs' public premade voices (Adam/Antoni/Bella),
matching the voices called out in the source workflow. Override with a raw
voice_id in an episode config if your account uses different/cloned voices.
"""

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

DEFAULT_IMAGE_STYLE_SUFFIX = "cinematic anime style, ultra detailed, dramatic lighting, 4k --ar 16:9 --v 6"
