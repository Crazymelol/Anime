from anime_factory.captions import build_scene_caption_file, scene_caption_lines

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


def test_build_caption_file_creates_timed_events(tmp_path):
    path = build_scene_caption_file(["line one", "line two"], duration_seconds=10, output_path=tmp_path / "s.ass")
    assert path is not None
    content = path.read_text()
    # Two events, split evenly across the 10s scene.
    assert content.count("Dialogue:") == 2
    assert "0:00:00.00,0:00:05.00" in content
    assert "0:00:05.00,0:00:10.00" in content
    assert "line one" in content and "line two" in content


def test_build_caption_file_returns_none_when_no_lines(tmp_path):
    assert build_scene_caption_file([], duration_seconds=10, output_path=tmp_path / "s.ass") is None


def test_build_caption_file_escapes_braces(tmp_path):
    path = build_scene_caption_file(["hello {world}"], duration_seconds=5, output_path=tmp_path / "s.ass")
    content = path.read_text()
    assert "{world}" not in content
    assert "(world)" in content
