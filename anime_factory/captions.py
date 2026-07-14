"""Builds ASS subtitle files that get burned into the video.

Short-form vertical videos (TikTok/Reels) are almost always watched on mute, so
on-screen captions are essential. Each scene's spoken lines (narration + dialogue)
are split evenly across the scene's duration and rendered large, centered in the
lower third with a heavy outline for readability over any background.
"""

import textwrap
from pathlib import Path

# Vertical canvas; must match video_assembly.VIDEO_SIZE.
PLAY_RES_X = 1080
PLAY_RES_Y = 1920
WRAP_WIDTH = 24  # characters per caption line before wrapping

ASS_HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {PLAY_RES_X}
PlayResY: {PLAY_RES_Y}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,66,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def scene_caption_lines(scene: dict) -> list[str]:
    """Ordered spoken lines for a scene: narration first, then dialogue (matches audio order)."""
    lines = list(scene.get("narrator_lines", []))
    lines += [entry["line"] for entry in scene.get("dialogue", [])]
    return [line for line in lines if line.strip()]


def _format_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours}:{minutes:02d}:{secs:05.2f}"


def _escape_text(text: str) -> str:
    # Braces start ASS override blocks; newlines become the ASS line break \N.
    text = text.replace("{", "(").replace("}", ")")
    wrapped = textwrap.fill(text.strip(), width=WRAP_WIDTH)
    return wrapped.replace("\n", "\\N")


def build_scene_caption_file(lines: list[str], duration_seconds: float, output_path: Path) -> Path | None:
    """Write an ASS file with each line shown for an equal slice of the scene.

    Returns None (writes nothing) if there are no lines to show.
    """
    if not lines:
        return None

    segment = duration_seconds / len(lines)
    events = []
    for i, line in enumerate(lines):
        start = _format_time(i * segment)
        end = _format_time((i + 1) * segment)
        events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{_escape_text(line)}")

    output_path.write_text(ASS_HEADER + "\n".join(events) + "\n")
    return output_path
