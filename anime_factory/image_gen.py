"""Generates scene images from the Midjourney-style prompts.

Midjourney has no public API, so this uses Stability AI's image API as the
practical automated substitute. In mock mode it renders a solid-color frame
with ffmpeg instead, so the rest of the pipeline (and tests) can run offline.
"""

import os
import subprocess
from pathlib import Path

import requests

STABILITY_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"
VIDEO_SIZE = "1080x1920"  # vertical short format
MOCK_PALETTE = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483"]


def generate_image(prompt: str, api_key: str, output_path: Path) -> Path:
    response = requests.post(
        STABILITY_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
        files={"none": ("", "")},
        data={"prompt": prompt, "output_format": "png", "aspect_ratio": "9:16"},
        timeout=60,
    )
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def generate_mock_image(output_path: Path, color: str) -> Path:
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={VIDEO_SIZE}",
            "-frames:v", "1", str(output_path),
        ],
        check=True, capture_output=True,
    )
    return output_path


def generate_episode_images(
    prompts: list[str],
    output_dir: Path,
    mock: bool = False,
    api_key: str | None = None,
) -> list[Path]:
    api_key = api_key or os.environ.get("STABILITY_API_KEY")
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for i, prompt in enumerate(prompts):
        path = images_dir / f"scene_{i + 1}.png"
        if mock:
            generate_mock_image(path, MOCK_PALETTE[i % len(MOCK_PALETTE)])
        else:
            generate_image(prompt, api_key, path)
        paths.append(path)
    return paths
