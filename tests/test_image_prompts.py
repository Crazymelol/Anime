from anime_factory.image_prompts import build_episode_prompts

CHARACTERS = [
    {"name": "Kaito", "visual_description": "anime teen boy, dark messy hair"},
    {"name": "Narrator", "visual_description": None},
]

SCENES = [
    {
        "scene_number": 1,
        "scene_description": "Kaito sits in a dark server room.",
        "dialogue": [{"character": "Kaito", "line": "This can't be right."}],
        "emotional_tone": "tense",
    },
    {
        "scene_number": 2,
        "scene_description": "Kaito runs through the corridor.",
        "dialogue": [{"character": "Kaito", "line": "I have to get out."}],
        "emotional_tone": "urgent",
    },
]


def test_first_scene_includes_full_visual_description():
    prompts = build_episode_prompts(SCENES, CHARACTERS)
    assert "anime teen boy, dark messy hair" in prompts[0]


def test_later_scene_reuses_same_character_continuity():
    prompts = build_episode_prompts(SCENES, CHARACTERS)
    assert "same character" in prompts[1]
    assert "anime teen boy, dark messy hair" not in prompts[1]


def test_narrator_with_no_visual_description_is_skipped():
    prompts = build_episode_prompts(SCENES, CHARACTERS)
    assert "Narrator" not in prompts[0]
