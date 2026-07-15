"""Turns every dialogue/narration line in a script into speech.

Two real providers, chosen with TTS_PROVIDER:
- "elevenlabs" (default): hosted API with the voice settings from the source
  workflow (stability 0.35, similarity 0.85, style 0.40, speaker boost on)
- "xtts": a LOCAL Coqui TTS v2 (XTTS-v2) server — free, on-device, speaks 16+
  languages including Greek. Start it with:
      tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2
  (default http://127.0.0.1:5002). Character "voice" is then an XTTS speaker
  name (e.g. "Damien Black") or a path to a short .wav sample to clone.

Hosted lines run over a shared session with a small worker pool; local lines
run sequentially (one laptop). In mock mode each line becomes a REAL silent
.mp3 (ffmpeg anullsrc) sized to an estimated speech duration, so offline runs
exercise the exact same downstream path — concat, duration probing, caption
sync — as paid runs.
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
LOCAL_TIMEOUT = 300  # local TTS on a laptop can take a while per line


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


def synthesize_line_xtts(
    voice: str,
    text: str,
    language: str = "en",
    session: requests.Session | None = None,
    base_url: str | None = None,
) -> bytes:
    """GET /api/tts on a local Coqui tts-server; returns WAV bytes.

    `voice` is a built-in XTTS speaker name, or a path to a .wav sample for
    voice cloning (sent as speaker_wav/style_wav).
    """
    base_url = (base_url or os.environ.get("XTTS_URL", "http://127.0.0.1:5002")).rstrip("/")
    params = {"text": text, "language_id": language}
    if voice.endswith(".wav"):
        params["speaker_wav"] = voice
        params["style_wav"] = voice
    else:
        params["speaker_id"] = voice
    get = (session or requests).get
    response = get(f"{base_url}/api/tts", params=params, timeout=LOCAL_TIMEOUT)
    response.raise_for_status()
    return response.content


def _wav_bytes_to_mp3(wav_bytes: bytes, output_path: Path) -> None:
    # Keep every provider's output as mp3 so concat/probing sees uniform files.
    subprocess.run(
        ["ffmpeg", "-y", "-i", "pipe:0", "-codec:a", "libmp3lame", "-q:a", "4", str(output_path)],
        input=wav_bytes, check=True, capture_output=True,
    )


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
    language: str = "en",
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

    provider = os.environ.get("TTS_PROVIDER", "elevenlabs")
    if mock:
        for text, _voice_id, path in jobs:
            _write_silent_mp3(path, estimate_speech_seconds(text))
    elif provider == "xtts":
        with requests.Session() as session:
            for i, (text, voice, path) in enumerate(jobs):  # sequential: one local machine
                print(f"STAGE: Speaking line {i + 1} of {len(jobs)}...", flush=True)
                _wav_bytes_to_mp3(synthesize_line_xtts(voice, text, language, session=session), path)
    else:
        with requests.Session() as session, ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            def synth(job: tuple[str, str, Path]) -> None:
                text, voice_id, path = job
                path.write_bytes(synthesize_line(voice_id, text, api_key, session=session))

            # list() drains the iterator so the first failure raises here.
            list(pool.map(synth, jobs))

    return audio_by_scene
