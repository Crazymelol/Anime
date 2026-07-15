"""Generates an episode script from an episode config, mirroring the writer-prompt
structure from the source workflow (scene description / dialogue / narrator lines /
emotional tone per scene) but asking the LLM for JSON so it can be parsed reliably.
"""

import json
import re

from anime_factory.llm_client import LLMClient

SYSTEM_PROMPT = """You are a writer for a dark fantasy anime series. You output ONLY valid JSON, \
no commentary, no markdown code fences."""

USER_PROMPT_TEMPLATE = """Write episode {episode_number} of a {total_episodes} episode series called "{series_title}".

{character_briefs}

Episode {episode_number}: {premise}

Format the output as a JSON object with this exact shape:
{{
  "episode_title": "<short title for this episode>",
  "hook": "<one scroll-stopping line, max 8 words, shown on screen in the first 2 seconds>",
  "scenes": [
    {{
      "scene_number": 1,
      "scene_description": "<visual description suitable for image generation>",
      "camera": "<shot type and angle, e.g. 'extreme close-up, low angle'>",
      "lighting": "<lighting mood, e.g. 'cold blue monitor glow, hard shadows'>",
      "dialogue": [{{"character": "<name>", "line": "<spoken line>"}}],
      "narrator_lines": ["<narration line>"],
      "emotional_tone": "<short tone note>",
      "duration_seconds": 30
    }}
  ]
}}

Vary the camera between scenes (wide establishing, close-up, dutch angle, over-the-shoulder)
like a storyboard artist would.{language_instruction}

Each scene should be 30-45 seconds when read aloud. Total episode: {total_minutes} minutes.
Tone: {tone}. Pacing: {pacing}."""


def build_character_briefs(characters: list[dict]) -> str:
    lines = []
    for c in characters:
        if c.get("role") == "narrator":
            continue
        age_part = f", {c['age']}," if c.get("age") else ""
        lines.append(f"The {c.get('role', 'character')} is {c['name']}{age_part} {c['brief']}")
    return "\n".join(lines)


def build_user_prompt(episode_config: dict) -> str:
    language = episode_config.get("language", "en")
    language_instruction = ""
    if language != "en":
        language_instruction = (
            f"\n\nWrite the episode title, hook, all dialogue, and all narration in the "
            f"language with ISO code '{language}'. Keep scene_description, camera, and "
            f"lighting in English (they feed an image generator)."
        )
    return USER_PROMPT_TEMPLATE.format(
        episode_number=episode_config["episode_number"],
        total_episodes=episode_config["total_episodes"],
        series_title=episode_config["series_title"],
        character_briefs=build_character_briefs(episode_config["characters"]),
        premise=episode_config["premise"],
        total_minutes=episode_config["total_minutes"],
        tone=episode_config["tone"],
        pacing=episode_config["pacing"],
        language_instruction=language_instruction,
    )


def parse_script_json(raw_text: str) -> dict:
    """Extract the JSON object from an LLM response, tolerating ```json fences."""
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw_text, re.DOTALL)
    candidate = fenced.group(1) if fenced else raw_text.strip()
    return json.loads(candidate)


def generate_episode_script(episode_config: dict, llm_client: LLMClient | None = None) -> dict:
    llm_client = llm_client or LLMClient()
    user_prompt = build_user_prompt(episode_config)
    raw_text = llm_client.generate(SYSTEM_PROMPT, user_prompt)
    return parse_script_json(raw_text)
