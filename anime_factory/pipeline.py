"""Orchestrates script -> image prompts -> voiceover for one episode config."""

import json
from pathlib import Path

from anime_factory.config import VOICE_PRESETS
from anime_factory.image_prompts import build_episode_prompts
from anime_factory.llm_client import LLMClient
from anime_factory.script_writer import generate_episode_script
from anime_factory.voiceover import generate_episode_audio


def resolve_voice_ids(characters: list[dict]) -> list[dict]:
    resolved = []
    for c in characters:
        c = dict(c)
        voice = c.get("voice", "")
        c["voice_id"] = VOICE_PRESETS.get(voice, voice)
        resolved.append(c)
    return resolved


def run_pipeline(episode_config: dict, output_dir: Path, mock: bool = False, skip_audio: bool = False) -> Path:
    series_slug = episode_config["series_title"].lower().replace(" ", "_")
    episode_dir = output_dir / series_slug / f"episode_{episode_config['episode_number']}"
    episode_dir.mkdir(parents=True, exist_ok=True)

    characters = resolve_voice_ids(episode_config["characters"])

    if mock:
        script = _mock_script(episode_config)
    else:
        script = generate_episode_script(episode_config, LLMClient())

    (episode_dir / "script.json").write_text(json.dumps(script, indent=2))

    prompts = build_episode_prompts(script["scenes"], characters)
    (episode_dir / "image_prompts.txt").write_text("\n\n".join(
        f"Scene {i + 1}: {p}" for i, p in enumerate(prompts)
    ))

    audio_files: list[Path] = []
    if not skip_audio:
        audio_files = generate_episode_audio(script["scenes"], characters, episode_dir, mock=mock)

    manifest = {
        "series_title": episode_config["series_title"],
        "episode_number": episode_config["episode_number"],
        "episode_title": script.get("episode_title"),
        "scene_count": len(script["scenes"]),
        "image_prompts_file": "image_prompts.txt",
        "audio_files": [str(p.relative_to(episode_dir)) for p in audio_files],
    }
    (episode_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    return episode_dir


def _mock_script(episode_config: dict) -> dict:
    main_character = next(c for c in episode_config["characters"] if c.get("role") != "narrator")
    return {
        "episode_title": f"{episode_config['series_title']} - Episode {episode_config['episode_number']} (mock)",
        "scenes": [
            {
                "scene_number": 1,
                "scene_description": f"{main_character['name']} discovers something is wrong.",
                "dialogue": [{"character": main_character["name"], "line": "This can't be right."}],
                "narrator_lines": [f"{main_character['name']} had no idea what came next."],
                "emotional_tone": "tense, uncertain",
                "duration_seconds": 35,
            },
            {
                "scene_number": 2,
                "scene_description": f"{main_character['name']} confronts the truth.",
                "dialogue": [{"character": main_character["name"], "line": "I won't let them win."}],
                "narrator_lines": ["The line had been crossed."],
                "emotional_tone": "defiant",
                "duration_seconds": 40,
            },
        ],
    }
