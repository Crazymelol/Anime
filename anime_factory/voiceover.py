"""Calls the ElevenLabs text-to-speech API for every dialogue/narration line in a script,
using the voice settings from the source workflow (stability 0.35, similarity 0.85,
style 0.40, speaker boost on).

Real lines are synthesized over a shared HTTP session with a small worker pool
(lines are independent; a 12-minute episode has dozens). In mock mode each line
becomes a REAL silent .mp3 (ffmpeg anullsrc) sized to an estimated speech
duration, so offline runs exercise the exact same downstream path — concat,
duration probing, caption sync — as paid runs.
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from anime_factory.config import API_TIMEOUT, DEFAULT_VOICE_SETTINGS
from anime_factory.validation import ConfigError, find_narrator

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
WORDS_PER_SECOND = 2.6  # rough narration pace, used only to size mock audio
MAX_WORKERS = 4


def synthesize_line(
    voice_id: str,
    text: str,
    api_key: str,
    settings: dict = DEFAULT_VOICE_SETTINGS,
    session: requests.Session | None = None,
) -> bytes:
    post = (session or requests).post
    response = post(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": settings,
        },
        timeout=API_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


def voice_id_for_character(name: str, characters: list[dict]) -> str:
    for c in characters:
        if c["name"] == name:
            return c["voice_id"]
    raise ConfigError(f"No voice configured for character: {name}")


def estimate_speech_seconds(text: str) -> float:
    return max(1.2, len(text.split()) / WORDS_PER_SECOND)


def _write_silent_mp3(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono:d={seconds:.2f}",
         "-q:a", "9", str(path)],
        check=True, capture_output=True,
    )


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

    narrator = find_narrator(characters)

    # Flatten to independent (text, voice_id, path) jobs, keeping per-scene order.
    jobs: list[tuple[str, str, Path]] = []
    audio_by_scene: dict[int, list[Path]] = {}
    for scene in scenes:
        scene_number = scene["scene_number"]
        scene_paths: list[Path] = []

        for line in scene.get("narrator_lines", []):
            if narrator is None:
                raise ConfigError("The script has narration but no character has role 'narrator'.")
            path = audio_dir / f"scene_{scene_number}_{len(scene_paths):02d}_narrator.mp3"
            jobs.append((line, narrator["voice_id"], path))
            scene_paths.append(path)

        for entry in scene.get("dialogue", []):
            voice_id = voice_id_for_character(entry["character"], characters)
            path = audio_dir / f"scene_{scene_number}_{len(scene_paths):02d}_{entry['character'].lower()}.mp3"
            jobs.append((entry["line"], voice_id, path))
            scene_paths.append(path)

        audio_by_scene[scene_number] = scene_paths

    if mock:
        for text, _voice_id, path in jobs:
            _write_silent_mp3(path, estimate_speech_seconds(text))
    else:
        with requests.Session() as session, ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            def synth(job: tuple[str, str, Path]) -> None:
                text, voice_id, path = job
                path.write_bytes(synthesize_line(voice_id, text, api_key, session=session))

            # list() drains the iterator so the first failure raises here.
            list(pool.map(synth, jobs))

    return audio_by_scene
