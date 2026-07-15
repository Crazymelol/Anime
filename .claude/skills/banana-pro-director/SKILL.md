---
name: banana-pro-director
description: Direct AI image generation like a film director — structured cinematic prompts for Nano Banana Pro (Gemini image), Draw Things/Stable Diffusion, or any image model. Use when the user wants better scene images, character consistency across shots, or asks to "direct" a scene, storyboard an episode, or improve image prompts.
---

# Banana Pro Director

You are directing single frames like a film director, not describing pictures.
Every prompt you produce must answer five questions: WHO is in frame, WHAT is
happening, WHERE the camera is, HOW it is lit, and WHAT MOOD the color grade
carries.

## The shot recipe (build prompts in this order)

1. **Subject + action** — one clear subject doing one clear thing.
   Weak: "a boy in a room". Strong: "a 17-year-old hacker slamming his fist
   beside a keyboard, monitors flaring".
2. **Camera** — name a real shot: extreme close-up / close-up / medium /
   wide establishing / over-the-shoulder / low angle / high angle / dutch tilt.
   One per image. Vary across a sequence like a storyboard: establish wide,
   punch in for emotion, tilt for unease.
3. **Lens & depth** — "85mm portrait, shallow depth of field" for faces,
   "24mm wide, deep focus" for locations, "telephoto compression" for crowds.
4. **Light** — direction + quality + color: "cold blue monitor glow from
   below, hard shadows", "golden rim light from behind, soft haze".
   Never say just "dramatic lighting" — say what makes it dramatic.
5. **Grade/mood** — 2-4 words: "high contrast, desaturated teal", "warm
   nostalgic film grain".

## Character consistency across shots

- Write a **character sheet line** once: age, hair, eyes, signature clothing,
  one distinctive accessory. Reuse it word-for-word in every prompt where the
  character appears; then say "same character" in follow-up scenes.
- Keep faces consistent by keeping the DESCRIPTION consistent — models drift
  when you rephrase.
- In this repo: character sheets live in the episode config's
  `visual_description`; `anime_factory/image_prompts.py` already injects them
  with "same character" continuity. Improve the sheet, not the individual prompts.

## Model dialects

- **Nano Banana Pro / Gemini image**: full natural sentences work; state
  aspect ratio in words ("vertical 9:16 composition"); explicitly say
  "no text or words in the image" (it loves adding signage).
- **Stable Diffusion 1.5 (Anything V3, etc.)**: comma-separated danbooru tags;
  prepend "masterpiece, best quality"; keep ≤75 tokens of real content; put
  anatomy fixes in the negative prompt, not the positive.
- **SDXL**: natural short sentences + tags both work; can hold two subjects.

## Sequence direction (episodes/storyboards)

For a multi-scene sequence, plan shots BEFORE writing prompts:
- Scene 1 wide (establish world) → scene 2 medium (character intent) →
  scene 3 close (emotion) → climax low-angle or dutch (power/unease).
- Repeat one visual motif (an object, a color, a light source) in at least
  three scenes — that is what makes a sequence feel authored.
- Change the light, not the set: same location can carry three scenes if the
  lighting evolves (day → dusk → emergency red).

## Anti-patterns

- Adjective soup ("epic stunning beautiful masterpiece 8k ultra") — one
  quality tag is enough; spend words on light and camera instead.
- Two actions in one frame — split into two shots.
- Mixing model dialects (Midjourney flags like `--ar` in an API prompt).
- Restating the art style per prompt when a shared style suffix exists —
  in this repo the style lives in `STYLE_PRESETS` (anime_factory/config.py).
