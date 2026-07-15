"""Generates scene images from the Midjourney-style prompts.

Two real providers, chosen with IMAGE_PROVIDER:
- "stability" (default): Stability AI's hosted API (paid, needs STABILITY_API_KEY)
- "drawthings": a LOCAL Stable Diffusion server with an Automatic1111-compatible
  API — e.g. the Draw Things Mac app with its API Server switched on
  (Settings -> API Server, default http://127.0.0.1:7860). Free, runs on-device.

Prompts are independent, so hosted generation runs a few requests in parallel;
local generation runs sequentially (one laptop GPU). In mock mode a solid-color
frame is rendered with ffmpeg so the rest of the pipeline runs offline.
"""

import base64
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from anime_factory.config import API_TIMEOUT, VIDEO_SIZE

STABILITY_API_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"
MOCK_PALETTE = ["0x1a1a2e", "0x16213e", "0x0f3460", "0x533483"]
MAX_WORKERS = 4
LOCAL_TIMEOUT = 600  # local SD on a laptop can take minutes per image
# SD-friendly 9:16; the video stage upscales, so 720x1280 is plenty
LOCAL_WIDTH, LOCAL_HEIGHT = 720, 1280


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


def generate_image_drawthings(
    prompt: str,
    output_path: Path,
    session: requests.Session | None = None,
    base_url: str | None = None,
) -> Path:
    """txt2img against an A1111-compatible local server (Draw Things, A1111, Forge...)."""
    base_url = (base_url or os.environ.get("DRAWTHINGS_URL", "http://127.0.0.1:7860")).rstrip("/")
    post = (session or requests).post
    response = post(
        f"{base_url}/sdapi/v1/txt2img",
        json={
            "prompt": prompt,
            "negative_prompt": "text, watermark, logo, low quality, deformed hands",
            "width": LOCAL_WIDTH,
            "height": LOCAL_HEIGHT,
            "steps": int(os.environ.get("DRAWTHINGS_STEPS", "30")),
        },
        timeout=LOCAL_TIMEOUT,
    )
    response.raise_for_status()
    images = response.json().get("images") or []
    if not images:
        raise RuntimeError("The local image server returned no image (check the model is loaded).")
    output_path.write_bytes(base64.b64decode(images[0]))
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
    provider = os.environ.get("IMAGE_PROVIDER", "stability")
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    paths = [images_dir / f"scene_{i + 1}.png" for i in range(len(prompts))]

    if mock:
        for i, path in enumerate(paths):
            generate_mock_image(path, MOCK_PALETTE[i % len(MOCK_PALETTE)])
    elif provider == "drawthings":
        with requests.Session() as session:
            for prompt, path in zip(prompts, paths):  # sequential: one local GPU
                generate_image_drawthings(prompt, path, session=session)
    else:
        with requests.Session() as session, ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            list(pool.map(
                lambda job: generate_image(job[0], api_key, job[1], session=session),
                zip(prompts, paths),
            ))

    return paths
