"""Upfront validation so problems surface as clear errors BEFORE any paid API call,
and LLM output is normalized before the media stages trust it.
"""

import os

from anime_factory.config import VOICE_PRESETS


class ConfigError(ValueError):
    """Raised for problems a user can fix in their episode config or .env."""


def find_narrator(characters: list[dict]) -> dict | None:
    """The narrator is identified by role, never by a magic name."""
    for c in characters:
        if str(c.get("role", "")).strip().lower() == "narrator":
            return c
    return None


def validate_episode_config(episode_config: dict) -> None:
    for key in ("series_title", "episode_number", "premise", "characters"):
        if not episode_config.get(key):
            raise ConfigError(f"Episode config is missing required field: {key!r}")

    characters = episode_config["characters"]
    for c in characters:
        name = c.get("name")
        if not name:
            raise ConfigError("Every character needs a 'name'.")
        voice = c.get("voice", "")
        if not voice:
            raise ConfigError(
                f"Character {name!r} has no 'voice'. Use a preset "
                f"({', '.join(VOICE_PRESETS)}) or a raw ElevenLabs voice ID."
            )

    if find_narrator(characters) is None:
        raise ConfigError(
            "No narrator found: one character needs \"role\": \"narrator\" "
            "(any name is fine)."
        )


def validate_api_keys(skip_images: bool, skip_audio: bool) -> None:
    """Check every key the enabled stages will need, before spending on any of them.

    Local providers (IMAGE_PROVIDER=drawthings, TTS_PROVIDER=xtts) need no keys.
    """
    missing = []
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    llm_key = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if not os.environ.get(llm_key):
        missing.append(llm_key)
    image_provider = os.environ.get("IMAGE_PROVIDER", "stability")
    if not skip_images and image_provider == "stability" and not os.environ.get("STABILITY_API_KEY"):
        missing.append("STABILITY_API_KEY")
    tts_provider = os.environ.get("TTS_PROVIDER", "elevenlabs")
    if not skip_audio and tts_provider == "elevenlabs" and not os.environ.get("ELEVENLABS_API_KEY"):
        missing.append("ELEVENLABS_API_KEY")
    if missing:
        raise ConfigError(
            f"Missing API key(s) in your environment/.env: {', '.join(missing)}. "
            "Nothing was generated (no money spent)."
        )


def canonicalize_script(script: dict) -> dict:
    """Normalize LLM output so later stages can trust its shape.

    - scenes must be a non-empty list; scene_number is REASSIGNED positionally
      (1-based), eliminating duplicate/gapped LLM numbering as a corruption vector
    - dialogue entries must have 'character' and 'line'
    - blank narration/dialogue lines are dropped (they'd desync captions and
      get rejected by the TTS API)
    - duration_seconds is coerced to float, defaulting to 35
    """
    scenes = script.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ConfigError("The script has no scenes — the LLM output was not usable.")

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ConfigError(f"Scene {i + 1} is not an object in the script JSON.")
        scene["scene_number"] = i + 1

        if not str(scene.get("scene_description", "")).strip():
            raise ConfigError(f"Scene {i + 1} is missing a scene_description.")

        scene["narrator_lines"] = [
            str(line).strip() for line in scene.get("narrator_lines", []) if str(line).strip()
        ]

        dialogue = []
        for entry in scene.get("dialogue", []):
            if not isinstance(entry, dict) or not entry.get("character") or not str(entry.get("line", "")).strip():
                raise ConfigError(
                    f"Scene {i + 1} has a malformed dialogue entry "
                    f"(needs 'character' and 'line'): {entry!r}"
                )
            dialogue.append({"character": entry["character"], "line": str(entry["line"]).strip()})
        scene["dialogue"] = dialogue

        try:
            scene["duration_seconds"] = float(scene.get("duration_seconds", 35))
        except (TypeError, ValueError):
            scene["duration_seconds"] = 35.0

    return script


def validate_script_voices(script: dict, characters: list[dict]) -> None:
    """Every speaking character in the script must have a configured voice."""
    configured = {c["name"] for c in characters}
    for scene in script["scenes"]:
        for entry in scene["dialogue"]:
            if entry["character"] not in configured:
                raise ConfigError(
                    f"Scene {scene['scene_number']}: the script has {entry['character']!r} "
                    "speaking, but no such character exists in your episode config."
                )
