"""Builds ASS subtitle files that get burned into the video.

Short-form vertical videos (TikTok/Reels) are almost always watched on mute, so
on-screen captions are essential. Each spoken line is timed to its own audio
clip's real duration when available (falling back to an even split), rendered
large and centered in the lower third with a heavy outline for readability.
"""

import textwrap
from pathlib import Path

from anime_factory.config import VIDEO_HEIGHT, VIDEO_WIDTH

WRAP_WIDTH = 24  # characters per caption line before wrapping

ASS_HEADER = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,66,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,4,2,2,80,80,260,1
Style: Hook,Arial,110,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,3,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def scene_caption_lines(scene: dict) -> list[str]:
    """Ordered spoken lines for a scene: narration first, then dialogue (matches audio order)."""
    lines = list(scene.get("narrator_lines", []))
    lines += [entry["line"] for entry in scene.get("dialogue", [])]
    return [line for line in lines if line.strip()]


def _format_time(seconds: float) -> str:
    # Integer centisecond arithmetic with carry, so 59.997s becomes 0:01:00.00
    # rather than the invalid 0:00:60.00 that naive float formatting produces.
    centis = max(0, round(seconds * 100))
    hours, rem = divmod(centis, 360000)
    minutes, rem = divmod(rem, 6000)
    secs, centis = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _escape_text(text: str) -> str:
    # Braces start ASS override blocks; newlines become the ASS line break \N.
    text = text.replace("{", "(").replace("}", ")")
    wrapped = textwrap.fill(text.strip(), width=WRAP_WIDTH)
    return wrapped.replace("\n", "\\N")


def build_scene_caption_file(
    lines: list[str],
    duration_seconds: float,
    output_path: Path,
    line_durations: list[float] | None = None,
) -> Path | None:
    """Write an ASS file timing each line to its real audio duration when known.

    `line_durations` (seconds per line, same order as `lines`) comes from probing
    the per-line audio files; when absent or mismatched, lines get an equal slice
    of the scene. Returns None (writes nothing) if there are no lines to show.
    """
    if not lines:
        return None

    if line_durations and len(line_durations) == len(lines):
        durations = line_durations
    else:
        durations = [duration_seconds / len(lines)] * len(lines)

    events = []
    cursor = 0.0
    for line, duration in zip(lines, durations):
        start, cursor = cursor, cursor + duration
        events.append(
            f"Dialogue: 0,{_format_time(start)},{_format_time(cursor)},Default,,0,0,0,,{_escape_text(line)}"
        )

    output_path.write_text(ASS_HEADER + "\n".join(events) + "\n")
    return output_path


def build_hook_caption_file(hook_text: str, duration_seconds: float, output_path: Path) -> Path | None:
    """Big centered scroll-stopper text for the title card, with a quick fade."""
    if not hook_text.strip():
        return None
    event = (
        f"Dialogue: 0,{_format_time(0)},{_format_time(duration_seconds)},Hook,,0,0,0,,"
        f"{{\\fad(200,200)}}{_escape_text(hook_text)}"
    )
    output_path.write_text(ASS_HEADER + event + "\n")
    return output_path
