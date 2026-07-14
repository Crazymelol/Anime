import pytest

from anime_factory.validation import (
    ConfigError,
    canonicalize_script,
    find_narrator,
    validate_episode_config,
)

GOOD_CONFIG = {
    "series_title": "Shadow Protocol",
    "episode_number": 3,
    "premise": "Kaito infiltrates a corporate server.",
    "characters": [
        {"name": "Kaito", "role": "main character", "voice": "adam"},
        {"name": "The Voice", "role": "narrator", "voice": "antoni"},
    ],
}


def test_good_config_passes():
    validate_episode_config(GOOD_CONFIG)


def test_narrator_found_by_role_not_name():
    assert find_narrator(GOOD_CONFIG["characters"])["name"] == "The Voice"


def test_missing_voice_rejected():
    config = dict(GOOD_CONFIG, characters=[{"name": "Kaito", "role": "main"},
                                           {"name": "N", "role": "narrator", "voice": "antoni"}])
    with pytest.raises(ConfigError, match="no 'voice'"):
        validate_episode_config(config)


def test_missing_narrator_rejected():
    config = dict(GOOD_CONFIG, characters=[{"name": "Kaito", "role": "main", "voice": "adam"}])
    with pytest.raises(ConfigError, match="narrator"):
        validate_episode_config(config)


def test_canonicalize_renumbers_duplicate_scene_numbers():
    script = {"scenes": [
        {"scene_number": 3, "scene_description": "a", "dialogue": [], "narrator_lines": []},
        {"scene_number": 3, "scene_description": "b", "dialogue": [], "narrator_lines": []},
    ]}
    result = canonicalize_script(script)
    assert [s["scene_number"] for s in result["scenes"]] == [1, 2]


def test_canonicalize_strips_blank_lines():
    script = {"scenes": [{
        "scene_number": 1, "scene_description": "a",
        "narrator_lines": ["", "  ", "real line"],
        "dialogue": [{"character": "Kaito", "line": "  hi  "}],
    }]}
    scene = canonicalize_script(script)["scenes"][0]
    assert scene["narrator_lines"] == ["real line"]
    assert scene["dialogue"] == [{"character": "Kaito", "line": "hi"}]


def test_canonicalize_rejects_malformed_dialogue():
    script = {"scenes": [{
        "scene_number": 1, "scene_description": "a",
        "dialogue": [{"speaker": "Kaito", "text": "wrong shape"}],
    }]}
    with pytest.raises(ConfigError, match="dialogue"):
        canonicalize_script(script)


def test_canonicalize_coerces_bad_duration():
    script = {"scenes": [{"scene_number": 1, "scene_description": "a",
                          "duration_seconds": "30s", "dialogue": [], "narrator_lines": []}]}
    assert canonicalize_script(script)["scenes"][0]["duration_seconds"] == 35.0


def test_canonicalize_rejects_empty_scenes():
    with pytest.raises(ConfigError, match="no scenes"):
        canonicalize_script({"scenes": []})
