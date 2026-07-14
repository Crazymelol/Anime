from anime_factory.captions import _format_time, build_scene_caption_file, scene_caption_lines

SCENE = {
    "scene_number": 1,
    "narrator_lines": ["Kaito had no idea what came next."],
    "dialogue": [{"character": "Kaito", "line": "This can't be right."}],
}


def test_scene_caption_lines_orders_narration_then_dialogue():
    lines = scene_caption_lines(SCENE)
    assert lines == ["Kaito had no idea what came next.", "This can't be right."]


def test_scene_caption_lines_skips_blank():
    lines = scene_caption_lines({"narrator_lines": ["", "  "], "dialogue": []})
    assert lines == []


def test_format_time_carries_at_minute_boundary():
    # 59.997s must round to 0:01:00.00, never the invalid 0:00:60.00
    assert _format_time(59.997) == "0:01:00.00"
    assert _format_time(3599.996) == "1:00:00.00"
    assert _format_time(0) == "0:00:00.00"


def test_build_caption_file_even_split_fallback(tmp_path):
    path = build_scene_caption_file(["line one", "line two"], duration_seconds=10, output_path=tmp_path / "s.ass")
    content = path.read_text()
    assert content.count("Dialogue:") == 2
    assert "0:00:00.00,0:00:05.00" in content
    assert "0:00:05.00,0:00:10.00" in content


def test_build_caption_file_uses_real_line_durations(tmp_path):
    path = build_scene_caption_file(
        ["long narration", "short reply"], duration_seconds=10,
        output_path=tmp_path / "s.ass", line_durations=[7.5, 2.5],
    )
    content = path.read_text()
    assert "0:00:00.00,0:00:07.50" in content
    assert "0:00:07.50,0:00:10.00" in content


def test_build_caption_file_returns_none_when_no_lines(tmp_path):
    assert build_scene_caption_file([], duration_seconds=10, output_path=tmp_path / "s.ass") is None


def test_build_caption_file_escapes_braces(tmp_path):
    path = build_scene_caption_file(["hello {world}"], duration_seconds=5, output_path=tmp_path / "s.ass")
    content = path.read_text()
    assert "{world}" not in content
    assert "(world)" in content
