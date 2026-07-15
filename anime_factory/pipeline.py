"""Orchestrates script -> image prompts -> images -> voiceover -> video for one episode config."""

import json
import os
import re
from pathlib import Path

from anime_factory.config import DEFAULT_IMAGE_STYLE_SUFFIX, STYLE_PRESETS, VOICE_PRESETS
from anime_factory.image_gen import generate_episode_images
from anime_factory.image_prompts import build_episode_prompts
from anime_factory.llm_client import LLMClient
from anime_factory.script_writer import generate_episode_script
from anime_factory.validation import (
    canonicalize_script,
    validate_api_keys,
    validate_episode_config,
    validate_script_voices,
)
from anime_factory.video_assembly import assemble_episode_video
from anime_factory.voiceover import generate_episode_audio


def series_slug(series_title: str) -> str:
    """Filesystem-safe slug: apostrophes and other punctuation would otherwise
    flow into ffmpeg concat lists and filtergraph paths."""
    slug = re.sub(r"[^a-z0-9]+", "_", series_title.lower()).strip("_")
    return slug or "series"


def resolve_voice_ids(characters: list[dict]) -> list[dict]:
    # The adam/antoni/bella presets are ElevenLabs voice IDs; for local XTTS the
    # "voice" value is a speaker name or .wav sample path and passes through as-is.
    use_presets = os.environ.get("TTS_PROVIDER", "elevenlabs") == "elevenlabs"
    resolved = []
    for c in characters:
        c = dict(c)
        voice = c.get("voice", "")
        c["voice_id"] = VOICE_PRESETS.get(voice, voice) if use_presets else voice
        resolved.append(c)
    return resolved


def run_pipeline(
    episode_config: dict,
    output_dir: Path,
    mock: bool = False,
    skip_audio: bool = False,
    skip_images: bool = False,
    skip_video: bool = False,
    captions: bool = True,
) -> Path:
    # Fail on config/key problems BEFORE any paid API call.
    validate_episode_config(episode_config)
    if not mock:
        validate_api_keys(skip_images=skip_images, skip_audio=skip_audio)

    episode_dir = (
        output_dir / series_slug(episode_config["series_title"])
        / f"episode_{episode_config['episode_number']}"
    )
    episode_dir.mkdir(parents=True, exist_ok=True)

    characters = resolve_voice_ids(episode_config["characters"])

    if mock:
        script = _mock_script(episode_config)
    else:
        script = generate_episode_script(episode_config, LLMClient())
    script = canonicalize_script(script)
    validate_script_voices(script, characters)

    (episode_dir / "script.json").write_text(json.dumps(script, indent=2))

    # "style" may name a preset or be raw suffix text of its own.
    style = episode_config.get("style", "")
    style_suffix = STYLE_PRESETS.get(style, style) or DEFAULT_IMAGE_STYLE_SUFFIX

    prompts = build_episode_prompts(script["scenes"], characters, style_suffix)
    (episode_dir / "image_prompts.txt").write_text("\n\n".join(
        f"Scene {i + 1}: {p}" for i, p in enumerate(prompts)
    ))

    image_paths: list[Path] = []
    if not skip_images:
        image_paths = generate_episode_images(prompts, episode_dir, mock=mock)

    audio_by_scene: dict[int, list[Path]] = {}
    if not skip_audio:
        audio_by_scene = generate_episode_audio(
            script["scenes"], characters, episode_dir, mock=mock,
            language=episode_config.get("language", "en"),
        )

    # Optional music bed: explicit "music" path in the config, else music.mp3
    # next to the project if present.
    music_path = None
    music_setting = episode_config.get("music")
    for candidate in ([Path(music_setting)] if music_setting else []) + [Path("music.mp3")]:
        if candidate.is_file():
            music_path = candidate
            break

    video_path = None
    if not skip_video and image_paths:
        video_path = assemble_episode_video(
            script["scenes"], image_paths, audio_by_scene, episode_dir / "episode.mp4",
            captions=captions,
            hook_text=str(script.get("hook", "")),
            music_path=music_path,
        )

    manifest = {
        "series_title": episode_config["series_title"],
        "episode_number": episode_config["episode_number"],
        "episode_title": script.get("episode_title"),
        "scene_count": len(script["scenes"]),
        "image_prompts_file": "image_prompts.txt",
        "image_files": [str(p.relative_to(episode_dir)) for p in image_paths],
        "audio_files": [str(p.relative_to(episode_dir)) for paths in audio_by_scene.values() for p in paths],
        "video_file": str(video_path.relative_to(episode_dir)) if video_path else None,
    }
    (episode_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    return episode_dir


def _mock_script(episode_config: dict) -> dict:
    main_character = next(c for c in episode_config["characters"] if c.get("role") != "narrator")
    return {
        "episode_title": f"{episode_config['series_title']} - Episode {episode_config['episode_number']} (mock)",
        "hook": "They were never meant to find it.",
        "scenes": [
            {
                "scene_number": 1,
                "scene_description": f"{main_character['name']} discovers something is wrong.",
                "camera": "extreme close-up, low angle",
                "lighting": "cold blue monitor glow, hard shadows",
                "dialogue": [{"character": main_character["name"], "line": "This can't be right."}],
                "narrator_lines": [f"{main_character['name']} had no idea what came next."],
                "emotional_tone": "tense, uncertain",
                "duration_seconds": 8,
            },
            {
                "scene_number": 2,
                "scene_description": f"{main_character['name']} confronts the truth.",
                "camera": "wide shot, dutch angle",
                "lighting": "purple rim light against darkness",
                "dialogue": [{"character": main_character["name"], "line": "I won't let them win."}],
                "narrator_lines": ["The line had been crossed."],
                "emotional_tone": "defiant",
                "duration_seconds": 8,
            },
        ],
    }
