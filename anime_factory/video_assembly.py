"""Assembles per-scene image + voiceover into a finished vertical short via ffmpeg:
each scene becomes a slow zoom-in clip synced to its concatenated dialogue/narration
audio (with captions timed to each line's real duration), then all scene clips are
concatenated into the final episode video.

Mock runs produce silent per-line mp3s upstream, so this module has no mock
branch — scenes without audio simply fall back to the script's planned
`duration_seconds` and render silently.
"""

import shutil
import subprocess
from pathlib import Path

from anime_factory.captions import build_scene_caption_file, scene_caption_lines
from anime_factory.config import FPS, VIDEO_SIZE


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        # Surface ffmpeg's own diagnostics instead of a bare exit code.
        raise RuntimeError(f"ffmpeg failed ({' '.join(cmd[:2])}...):\n{e.stderr[-2000:]}") from e


def _concat_list_entry(path: Path) -> str:
    # concat demuxer quoting: embedded single quotes close the string, insert an
    # escaped quote, and reopen — same trick as POSIX shell quoting.
    return "file '" + str(path.resolve()).replace("'", "'\\''") + "'"


def _escape_filter_path(path: Path) -> str:
    """Quote a path for use as a filtergraph option value (handles ' : \\)."""
    escaped = str(path).replace("\\", "\\\\").replace("'", "'\\''")
    return f"'{escaped}'"


def concat_media(paths: list[Path], output_path: Path) -> Path:
    """Losslessly concatenate same-codec media files via the concat demuxer."""
    list_file = output_path.with_suffix(output_path.suffix + ".list")
    list_file.write_text("\n".join(_concat_list_entry(p) for p in paths))
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
              "-c", "copy", str(output_path)])
    finally:
        list_file.unlink(missing_ok=True)
    return output_path


def get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def build_scene_clip(
    image_path: Path,
    audio_path: Path | None,
    duration_seconds: float,
    output_path: Path,
    caption_file: Path | None = None,
) -> Path:
    # Oversample before zoompan to avoid jitter, but only ~2x output size -- scaling to
    # 8000px (a common ffmpeg ken-burns recipe) made long scenes take minutes to encode.
    # zoompan's d= is the single frame-count bound: the image is read once (no -loop),
    # so the zoom can never restart mid-scene.
    frames = max(1, round(duration_seconds * FPS))
    filters = f"scale=2400:-1,zoompan=z='min(zoom+0.0008,1.1)':d={frames}:s={VIDEO_SIZE}:fps={FPS}"
    if caption_file:
        filters += f",subtitles=filename={_escape_filter_path(caption_file)}"

    cmd = ["ffmpeg", "-y", "-i", str(image_path)]
    if audio_path:
        cmd += ["-i", str(audio_path)]
    cmd += ["-vf", filters, "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac", "-shortest"] if audio_path else ["-an"]
    cmd += [str(output_path)]

    _run(cmd)
    return output_path


def assemble_episode_video(
    scenes: list[dict],
    image_paths: list[Path],
    audio_by_scene: dict[int, list[Path]],
    output_path: Path,
    captions: bool = True,
) -> Path:
    if len(image_paths) != len(scenes):
        raise ValueError(f"Got {len(image_paths)} images for {len(scenes)} scenes.")

    work_dir = output_path.parent / "_video_tmp"
    work_dir.mkdir(parents=True, exist_ok=True)

    try:
        clip_paths = []
        for i, scene in enumerate(scenes):
            scene_number = scene["scene_number"]
            scene_audio_files = audio_by_scene.get(scene_number, [])
            scene_audio_path = None
            line_durations: list[float] | None = None
            duration = float(scene.get("duration_seconds", 35))

            if scene_audio_files:
                line_durations = [get_audio_duration(p) for p in scene_audio_files]
                scene_audio_path = concat_media(scene_audio_files, work_dir / f"scene_{scene_number}_audio.mp3")
                duration = sum(line_durations)

            caption_file = None
            if captions:
                caption_file = build_scene_caption_file(
                    scene_caption_lines(scene), duration,
                    work_dir / f"scene_{scene_number}.ass",
                    line_durations=line_durations,
                )

            clip_paths.append(build_scene_clip(
                image_paths[i], scene_audio_path, duration,
                work_dir / f"scene_{scene_number}.mp4", caption_file=caption_file,
            ))

        concat_media(clip_paths, output_path)
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    return output_path
