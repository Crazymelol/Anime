"""Assembles per-scene image + voiceover into a finished vertical short via ffmpeg:
each scene becomes a slow zoom-in clip synced to its concatenated dialogue/narration
audio, then all scene clips are concatenated into the final episode video.

In mock mode (no real audio), each scene falls back to its planned
`duration_seconds` from the script and renders silently.
"""

import shutil
import subprocess
from pathlib import Path

VIDEO_SIZE = "1080x1920"
FPS = 25


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def concat_scene_audio(audio_paths: list[Path], output_path: Path) -> Path:
    list_file = output_path.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in audio_paths))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)])
    list_file.unlink()
    return output_path


def get_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def build_scene_clip(image_path: Path, audio_path: Path | None, duration_seconds: float, output_path: Path) -> Path:
    # Oversample before zoompan to avoid jitter, but only ~2x output size -- scaling to
    # 8000px (a common ffmpeg ken-burns recipe) made long scenes take minutes to encode.
    zoompan = f"scale=2400:-1,zoompan=z='min(zoom+0.0008,1.1)':d={int(duration_seconds * FPS)}:s={VIDEO_SIZE}:fps={FPS}"

    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(image_path)]
    if audio_path:
        cmd += ["-i", str(audio_path)]
    cmd += ["-vf", zoompan, "-t", str(duration_seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p"]
    cmd += ["-c:a", "aac", "-shortest"] if audio_path else ["-an"]
    cmd += [str(output_path)]

    _run(cmd)
    return output_path


def concat_clips(clip_paths: list[Path], output_path: Path) -> Path:
    list_file = output_path.with_suffix(".clips.txt")
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in clip_paths))
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output_path)])
    list_file.unlink()
    return output_path


def assemble_episode_video(
    scenes: list[dict],
    image_paths: list[Path],
    audio_by_scene: dict[int, list[Path]],
    output_path: Path,
    mock: bool = False,
) -> Path:
    work_dir = output_path.parent / "_video_tmp"
    work_dir.mkdir(parents=True, exist_ok=True)

    clip_paths = []
    for i, scene in enumerate(scenes):
        scene_number = scene["scene_number"]
        scene_audio_files = [p for p in audio_by_scene.get(scene_number, []) if p.suffix == ".mp3"]
        scene_audio_path = None
        duration = float(scene.get("duration_seconds", 35))

        if scene_audio_files and not mock:
            scene_audio_path = work_dir / f"scene_{scene_number}_audio.mp3"
            concat_scene_audio(scene_audio_files, scene_audio_path)
            duration = get_audio_duration(scene_audio_path)

        clip_path = work_dir / f"scene_{scene_number}.mp4"
        build_scene_clip(image_paths[i], scene_audio_path, duration, clip_path)
        clip_paths.append(clip_path)

    concat_clips(clip_paths, output_path)
    shutil.rmtree(work_dir)
    return output_path
