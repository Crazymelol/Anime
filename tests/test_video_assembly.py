import shutil

import pytest

from anime_factory.image_gen import generate_episode_images
from anime_factory.video_assembly import assemble_episode_video

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

SCENES = [
    {"scene_number": 1, "duration_seconds": 1},
    {"scene_number": 2, "duration_seconds": 1},
]


@requires_ffmpeg
def test_assemble_episode_video_mock_produces_playable_file(tmp_path):
    image_paths = generate_episode_images(["prompt one", "prompt two"], tmp_path, mock=True)
    output_path = tmp_path / "episode.mp4"

    result = assemble_episode_video(SCENES, image_paths, audio_by_scene={}, output_path=output_path, mock=True)

    assert result == output_path
    assert output_path.exists() and output_path.stat().st_size > 0
