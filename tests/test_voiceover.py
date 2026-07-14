import shutil

import pytest

from anime_factory.validation import ConfigError
from anime_factory.voiceover import generate_episode_audio

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

SCENES = [{
    "scene_number": 1,
    "narrator_lines": ["Kaito had no idea what came next."],
    "dialogue": [{"character": "Kaito", "line": "This can't be right."}],
}]


@requires_ffmpeg
def test_mock_audio_is_real_mp3_keyed_by_scene(tmp_path):
    characters = [
        {"name": "Kaito", "role": "main", "voice_id": "k"},
        {"name": "The Voice", "role": "narrator", "voice_id": "n"},
    ]
    audio = generate_episode_audio(SCENES, characters, tmp_path, mock=True)

    assert list(audio.keys()) == [1]
    assert len(audio[1]) == 2  # narration + dialogue, in order
    assert all(p.suffix == ".mp3" and p.exists() and p.stat().st_size > 0 for p in audio[1])
    assert "narrator" in audio[1][0].name and "kaito" in audio[1][1].name


@requires_ffmpeg
def test_narrator_resolved_by_role_any_name(tmp_path):
    # narrator named something other than "Narrator" must work
    characters = [
        {"name": "Kaito", "role": "main", "voice_id": "k"},
        {"name": "Whisper", "role": "narrator", "voice_id": "n"},
    ]
    audio = generate_episode_audio(SCENES, characters, tmp_path, mock=True)
    assert len(audio[1]) == 2


def test_narration_without_narrator_is_clear_error(tmp_path):
    with pytest.raises(ConfigError, match="narrator"):
        generate_episode_audio(SCENES, [{"name": "Kaito", "role": "main", "voice_id": "k"}],
                               tmp_path, mock=True)
