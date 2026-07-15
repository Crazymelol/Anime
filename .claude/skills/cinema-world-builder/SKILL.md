---
name: cinema-world-builder
description: Build coherent cinematic worlds for episodic stories — locations, lighting bible, color language, factions, recurring motifs — so every episode looks and feels like the same universe. Use when the user starts a new series, asks for world building, lore, a series bible, or complains that episodes/scenes feel disconnected.
---

# Cinema World Builder

A series dies when every episode looks like a different show. This skill
builds a **series bible**: a small set of reusable decisions that every
script, image prompt, and episode inherits.

## The bible (produce these six blocks)

1. **Premise engine** — one sentence: WHO wants WHAT, WHAT stands in the way,
   WHY it escalates every episode. Every episode premise must be derivable
   from this sentence.
2. **World rules** — 3 hard rules of the universe (what powers exist, what
   they cost, what is forbidden). Rules create drama; exceptions destroy it.
3. **Locations (3-5, no more)** — for each: name, one-line visual identity,
   its lighting signature, and what story beats happen there.
   Example: "The Server Vault — endless black racks, cold blue LED grid,
   where secrets are found and alarms begin."
4. **Color & light language** — assign meaning: e.g. blue = surveillance/
   the system, purple = the protagonist's power, red = the enemy/alarm,
   warm amber = the life he's losing. Then USE it: a scene's palette should
   tell viewers who is winning before a word is spoken.
5. **Cast sheet** — protagonist, antagonist force, one ally; for each: a
   fixed visual description (reused verbatim in image prompts), a voice, a
   want, and a line they would never say.
6. **Motif set** — 3 recurring images (an object, a gesture, a sound cue)
   that appear across episodes. Cheap to render, huge for identity.

## How it plugs into this repo

- Store the bible as `series_bible.md` next to the episode configs.
- Locations' lighting signatures feed each scene's `lighting`; the color
  language belongs in the style suffix (`STYLE_PRESETS` in
  anime_factory/config.py) or per-scene prompts.
- Cast sheet visual descriptions go into the episode config's
  `visual_description` fields verbatim — consistency comes from repetition.
- When writing a new episode premise, check it against the premise engine
  and end on the next question, not an answer (cliffhanger discipline).

## Episode arc template (for 8-20 scene shorts)

1. **Hook** (scene 1): the promise — something is wrong in a specific way.
2. **Descent** (scenes 2-40%): the protagonist chooses to look closer.
3. **Turn** (midpoint): what they find changes what the goal means.
4. **Price** (60-80%): the world rule exacts its cost.
5. **Cliff** (final scene): a new, bigger question — stated visually, in the
   world's color language.

## Anti-patterns

- More than 5 locations or 4 named characters in a short-form series —
  viewers can't attach, and image consistency collapses.
- Palette drift: if every episode introduces new colors, none mean anything.
- Lore dumps in narration — reveal rules by showing their cost.
- Building the world in prose only: every bible entry must translate to
  something a camera can see (a light, a color, an object, a face).
