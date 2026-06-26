"""Calls the ElevenLabs text-to-speech API for every dialogue/narration line in a script,
using the voice settings from the source workflow (stability 0.35, similarity 0.85,
style 0.40, speaker boost on).
"""

import os
from pathlib import Path

import requests

from anime_factory.config import DEFAULT_VOICE_SETTINGS

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


def synthesize_line(voice_id: str, text: str, api_key: str, settings: dict = DEFAULT_VOICE_SETTINGS) -> bytes:
    response = requests.post(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": settings,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.content


def voice_id_for_character(name: str, characters: list[dict]) -> str:
    for c in characters:
        if c["name"] == name:
            return c["voice_id"]
    raise ValueError(f"No voice configured for character: {name}")


def generate_episode_audio(
    scenes: list[dict],
    characters: list[dict],
    output_dir: Path,
    mock: bool = False,
    api_key: str | None = None,
) -> dict[int, list[Path]]:
    """Returns {scene_number: [audio_path, ...]} in narration-then-dialogue order,
    so callers (e.g. video assembly) don't have to reconstruct ordering from filenames.
    """
    api_key = api_key or os.environ.get("ELEVENLABS_API_KEY")
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    audio_by_scene: dict[int, list[Path]] = {}
    for scene in scenes:
        scene_number = scene["scene_number"]
        scene_paths: list[Path] = []
        seq = 0

        for line in scene.get("narrator_lines", []):
            path = audio_dir / f"scene_{scene_number}_{seq:02d}_narrator.mp3"
            scene_paths.append(_synthesize_to_file(line, voice_id_for_character("Narrator", characters),
                                                    path, api_key, mock))
            seq += 1

        for entry in scene.get("dialogue", []):
            voice_id = voice_id_for_character(entry["character"], characters)
            path = audio_dir / f"scene_{scene_number}_{seq:02d}_{entry['character'].lower()}.mp3"
            scene_paths.append(_synthesize_to_file(entry["line"], voice_id, path, api_key, mock))
            seq += 1

        audio_by_scene[scene_number] = scene_paths

    return audio_by_scene


def _synthesize_to_file(text: str, voice_id: str, path: Path, api_key: str | None, mock: bool) -> Path:
    if mock:
        path.with_suffix(".txt").write_text(text)
        return path.with_suffix(".txt")
    audio_bytes = synthesize_line(voice_id, text, api_key)
    path.write_bytes(audio_bytes)
    return path
