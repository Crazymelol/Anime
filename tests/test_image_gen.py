import shutil

import pytest

from anime_factory.image_gen import generate_episode_images

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")


@requires_ffmpeg
def test_mock_images_are_created_per_prompt(tmp_path):
    paths = generate_episode_images(["a prompt", "another prompt"], tmp_path, mock=True)

    assert len(paths) == 2
    assert all(p.exists() and p.stat().st_size > 0 for p in paths)
