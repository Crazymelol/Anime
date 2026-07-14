"""End-to-end pipeline tests (mock mode, no network): the whole factory from
episode config to finished episode.mp4, including the paths a real LLM's
quirky-but-valid output takes.
"""

import json
import shutil
import subprocess

import pytest

from anime_factory.pipeline import run_pipeline
from anime_factory.script_writer import parse_script_json
from anime_factory.validation import canonicalize_script
from anime_factory.video_assembly import get_audio_duration

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

CONFIG = {
    "series_title": "Shadow Protocol",
    "total_episodes": 12,
    "episode_number": 3,
    "premise": "Kaito infiltrates a corporate server.",
    "tone": "dark",
    "pacing": "fast",
    "total_minutes": 1,
    "characters": [
        {"name": "Kaito", "role": "main character", "age": 17, "brief": "a hacker.",
         "visual_description": "anime teen boy, dark messy hair", "voice": "adam"},
        {"name": "Narrator", "role": "narrator", "visual_description": None, "voice": "antoni"},
    ],
}


@requires_ffmpeg
def test_full_mock_pipeline_produces_complete_episode(tmp_path):
    episode_dir = run_pipeline(CONFIG, tmp_path, mock=True)

    manifest = json.loads((episode_dir / "manifest.json").read_text())
    assert manifest["video_file"] == "episode.mp4"
    assert manifest["scene_count"] == 2
    assert all(f.endswith(".mp3") for f in manifest["audio_files"])

    video = episode_dir / "episode.mp4"
    assert video.exists()
    # hook card (1.8s) + two audio-driven scenes -> comfortably > 2s, < 60s
    assert 2 < get_audio_duration(video) < 60

    # the finished video must carry both streams
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", str(video)],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    assert sorted(probe) == ["audio", "video"]


@requires_ffmpeg
def test_pipeline_handles_greek_text(tmp_path):
    config = dict(CONFIG, series_title="Σκιά Πρωτόκολλο")
    config["characters"] = [
        {"name": "Νίκος", "role": "main character", "brief": "χάκερ.",
         "visual_description": "anime αγόρι", "voice": "adam"},
        {"name": "Αφηγητής", "role": "narrator", "visual_description": None, "voice": "antoni"},
    ]
    episode_dir = run_pipeline(config, tmp_path, mock=True)
    assert (episode_dir / "episode.mp4").exists()
    # slug must stay filesystem/ffmpeg-safe even for non-latin titles
    assert episode_dir.parent.name == "series"


@requires_ffmpeg
def test_pipeline_with_music_bed(tmp_path):
    music = tmp_path / "bed.mp3"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
         "-q:a", "9", str(music)],
        check=True, capture_output=True,
    )
    config = dict(CONFIG, music=str(music))
    episode_dir = run_pipeline(config, tmp_path, mock=True)
    assert (episode_dir / "episode.mp4").exists()


def test_realistic_llm_output_survives_parse_and_canonicalize():
    # fenced JSON, 0-based duplicate scene numbers, blank narration, string duration
    raw = """Here is the episode:
```json
{
  "episode_title": "The Breach",
  "hook": "He saw the files.",
  "scenes": [
    {"scene_number": 0, "scene_description": "Kaito at his desk.",
     "camera": "close-up", "lighting": "monitor glow",
     "dialogue": [{"character": "Kaito", "line": "What is this?"}],
     "narrator_lines": ["", "It began at midnight."], "duration_seconds": "30"},
    {"scene_number": 0, "scene_description": "Alarms flare.",
     "dialogue": [], "narrator_lines": ["Everything changed."],
     "duration_seconds": 40}
  ]
}
```"""
    script = canonicalize_script(parse_script_json(raw))
    assert [s["scene_number"] for s in script["scenes"]] == [1, 2]
    assert script["scenes"][0]["narrator_lines"] == ["It began at midnight."]
    assert script["scenes"][0]["duration_seconds"] == 30.0
    assert script["hook"] == "He saw the files."
