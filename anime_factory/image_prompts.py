"""Builds Midjourney-ready prompts per scene.

Midjourney has no official API, so this stage produces a ready-to-paste prompt
list rather than calling out to an image service. The first scene featuring a
given character gets the full visual description baked in; later scenes reuse
"same character" for continuity, exactly as shown in the source workflow.
"""

import re

from anime_factory.config import DEFAULT_IMAGE_STYLE_SUFFIX


def _mentioned(name: str, text: str) -> bool:
    # Word-boundary match so "Kai" doesn't false-positive inside "Kaito".
    return re.search(rf"\b{re.escape(name)}\b", text) is not None


def build_scene_prompt(
    scene: dict,
    characters: list[dict],
    seen_characters: set[str],
    style_suffix: str = DEFAULT_IMAGE_STYLE_SUFFIX,
) -> str:
    char_lookup = {c["name"]: c for c in characters if c.get("visual_description")}
    present = [name for name in char_lookup if _mentioned(name, scene["scene_description"]) or any(
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
    # Per-scene direction from the script (shot type, lighting mood) makes each
    # frame read like a storyboard panel instead of the same flat composition.
    description_parts.append(scene.get("camera", ""))
    description_parts.append(scene.get("lighting", ""))
    description_parts.append(scene.get("emotional_tone", ""))
    description_parts.append(style_suffix)

    return ", ".join(p for p in description_parts if p)


def build_episode_prompts(
    scenes: list[dict],
    characters: list[dict],
    style_suffix: str = DEFAULT_IMAGE_STYLE_SUFFIX,
) -> list[str]:
    seen_characters: set[str] = set()
    return [build_scene_prompt(scene, characters, seen_characters, style_suffix) for scene in scenes]
