"""Generates scene images from the Midjourney-style prompts.

Midjourney has no public API, so this uses Stability AI's image API as the
practical automated substitute. Prompts are independent, so real generation
runs a few requests in parallel over a shared session. In mock mode it renders
a solid-color frame with ffmpeg instead, so the rest of the pipeline (and
tests) can run offline.
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from anime_factory.config import API_TIMEOUT, VIDEO_SIZE

STABILITY_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"
MOCK_PALETTE = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483"]
MAX_WORKERS = 4


def generate_image(prompt: str, api_key: str, output_path: Path, session: requests.Session | None = None) -> Path:
    post = (session or requests).post
    response = post(
        STABILITY_API_URL,
        headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
        files={"none": ("", "")},
        data={"prompt": prompt, "output_format": "png", "aspect_ratio": "9:16"},
        timeout=API_TIMEOUT,
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

    paths = [images_dir / f"scene_{i + 1}.png" for i in range(len(prompts))]

    if mock:
        for i, path in enumerate(paths):
            generate_mock_image(path, MOCK_PALETTE[i % len(MOCK_PALETTE)])
    else:
        with requests.Session() as session, ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            list(pool.map(
                lambda job: generate_image(job[0], api_key, job[1], session=session),
                zip(prompts, paths),
            ))

    return paths
