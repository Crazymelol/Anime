import shutil
import subprocess

import pytest

from anime_factory.image_gen import generate_episode_images
from anime_factory.video_assembly import (
    _concat_list_entry,
    _escape_filter_path,
    assemble_episode_video,
    concat_media,
    get_audio_duration,
)
from anime_factory.voiceover import _write_silent_mp3

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

SCENES = [
    {"scene_number": 1, "duration_seconds": 1},
    {"scene_number": 2, "duration_seconds": 1},
]


def test_concat_list_entry_escapes_apostrophes(tmp_path):
    entry = _concat_list_entry(tmp_path / "kai's_blade.mp3")
    assert "kai'\\''s_blade" in entry


def test_escape_filter_path_quotes_apostrophes(tmp_path):
    escaped = _escape_filter_path(tmp_path / "kai's.ass")
    assert escaped.startswith("'") and escaped.endswith("'")
    assert "kai'\\''s.ass" in escaped


@requires_ffmpeg
def test_assemble_episode_video_produces_playable_file(tmp_path):
    image_paths = generate_episode_images(["prompt one", "prompt two"], tmp_path, mock=True)
    output_path = tmp_path / "episode.mp4"

    result = assemble_episode_video(SCENES, image_paths, audio_by_scene={}, output_path=output_path)

    assert result == output_path
    assert output_path.exists() and output_path.stat().st_size > 0
    assert not (tmp_path / "_video_tmp").exists()


@requires_ffmpeg
def test_assemble_video_length_mismatch_raises(tmp_path):
    image_paths = generate_episode_images(["only one"], tmp_path, mock=True)
    with pytest.raises(ValueError, match="1 images for 2 scenes"):
        assemble_episode_video(SCENES, image_paths, audio_by_scene={}, output_path=tmp_path / "e.mp4")


@requires_ffmpeg
def test_concat_media_survives_apostrophe_paths(tmp_path):
    apostrophe_dir = tmp_path / "kai's_blade"
    apostrophe_dir.mkdir()
    a = apostrophe_dir / "a.mp3"
    b = apostrophe_dir / "b.mp3"
    _write_silent_mp3(a, 0.5)
    _write_silent_mp3(b, 0.5)

    out = concat_media([a, b], tmp_path / "joined.mp3")

    assert out.exists()
    assert get_audio_duration(out) == pytest.approx(1.0, abs=0.3)


@requires_ffmpeg
def test_odd_aspect_source_image_fills_frame_undistorted(tmp_path):
    # local SD models produce e.g. 512x912 — the clip must still be exactly
    # 1080x1920 (cover + center-crop), never squished
    odd = tmp_path / "odd.png"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x336699:s=512x768",
         "-frames:v", "1", str(odd)],
        check=True, capture_output=True,
    )
    from anime_factory.video_assembly import build_scene_clip
    clip = build_scene_clip(odd, None, 1.0, tmp_path / "clip.mp4")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(clip)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert probe == "1080,1920"


@requires_ffmpeg
def test_scene_duration_follows_audio(tmp_path):
    image_paths = generate_episode_images(["p1"], tmp_path, mock=True)
    audio = tmp_path / "line.mp3"
    _write_silent_mp3(audio, 2.0)

    scenes = [{"scene_number": 1, "duration_seconds": 30,
               "narrator_lines": ["hello there"], "dialogue": []}]
    out = assemble_episode_video(scenes, image_paths, audio_by_scene={1: [audio]},
                                 output_path=tmp_path / "e.mp4")

    # video length must track the real 2s audio, not the script's 30s guess
    assert get_audio_duration(out) == pytest.approx(2.0, abs=0.5)
