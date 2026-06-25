import pytest

from anime_factory.script_writer import build_character_briefs, build_user_prompt, parse_script_json

EPISODE_CONFIG = {
    "series_title": "Shadow Protocol",
    "total_episodes": 12,
    "episode_number": 3,
    "premise": "Kaito infiltrates a corporate server.",
    "tone": "dark",
    "pacing": "fast",
    "total_minutes": 12,
    "characters": [
        {"name": "Kaito", "role": "main character", "age": 17, "brief": "a hacker."},
        {"name": "Narrator", "role": "narrator"},
    ],
}


def test_build_user_prompt_includes_episode_details():
    prompt = build_user_prompt(EPISODE_CONFIG)
    assert "Shadow Protocol" in prompt
    assert "episode 3 of a 12 episode series" in prompt
    assert "Kaito" in prompt


def test_build_character_briefs_skips_narrator():
    briefs = build_character_briefs(EPISODE_CONFIG["characters"])
    assert "Kaito" in briefs
    assert "Narrator" not in briefs


def test_parse_script_json_plain():
    raw = '{"episode_title": "Test", "scenes": []}'
    assert parse_script_json(raw) == {"episode_title": "Test", "scenes": []}


def test_parse_script_json_fenced():
    raw = '```json\n{"episode_title": "Test", "scenes": []}\n```'
    assert parse_script_json(raw) == {"episode_title": "Test", "scenes": []}


def test_parse_script_json_invalid_raises():
    with pytest.raises(Exception):
        parse_script_json("not json")
