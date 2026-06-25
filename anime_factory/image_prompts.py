"""Builds Midjourney-ready prompts per scene.

Midjourney has no official API, so this stage produces a ready-to-paste prompt
list rather than calling out to an image service. The first scene featuring a
given character gets the full visual description baked in; later scenes reuse
"same character" for continuity, exactly as shown in the source workflow.
"""

from anime_factory.config import DEFAULT_IMAGE_STYLE_SUFFIX


def build_scene_prompt(
    scene: dict,
    characters: list[dict],
    seen_characters: set[str],
    style_suffix: str = DEFAULT_IMAGE_STYLE_SUFFIX,
) -> str:
    char_lookup = {c["name"]: c for c in characters if c.get("visual_description")}
    present = [name for name in char_lookup if name in scene["scene_description"] or any(
        d["character"] == name for d in scene.get("dialogue", [])
    )]

    description_parts = []
    for name in present:
        if name not in seen_characters:
            description_parts.append(char_lookup[name]["visual_description"])
            seen_characters.add(name)
        else:
            description_parts.append("same character")

    description_parts.append(scene["scene_description"])
    description_parts.append(scene.get("emotional_tone", ""))
    description_parts.append(style_suffix)

    return ", ".join(p for p in description_parts if p)


def build_episode_prompts(scenes: list[dict], characters: list[dict]) -> list[str]:
    seen_characters: set[str] = set()
    return [build_scene_prompt(scene, characters, seen_characters) for scene in scenes]
