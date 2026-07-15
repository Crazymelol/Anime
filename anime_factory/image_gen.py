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
# SD1.5 models (Anything, Counterfeit...) were trained near 512px and grow
# extra limbs at larger sizes, so default to a 512-wide 9:16 frame; the video
# stage upscales. SDXL users can raise these via env.
LOCAL_WIDTH = int(os.environ.get("DRAWTHINGS_WIDTH", "512"))
LOCAL_HEIGHT = int(os.environ.get("DRAWTHINGS_HEIGHT", "912"))
# Danbooru-style quality tags that SD1.5 anime models expect up front.
LOCAL_PROMPT_PREFIX = os.environ.get("DRAWTHINGS_PROMPT_PREFIX", "masterpiece, best quality")
LOCAL_NEGATIVE_PROMPT = os.environ.get(
    "DRAWTHINGS_NEGATIVE_PROMPT",
    "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, "
    "fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, "
    "watermark, username, blurry, extra limbs, deformed",
)


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
            "prompt": f"{LOCAL_PROMPT_PREFIX}, {prompt}" if LOCAL_PROMPT_PREFIX else prompt,
            "negative_prompt": LOCAL_NEGATIVE_PROMPT,
            "width": LOCAL_WIDTH,
            "height": LOCAL_HEIGHT,
            "steps": int(os.environ.get("DRAWTHINGS_STEPS", "30")),
            "cfg_scale": float(os.environ.get("DRAWTHINGS_CFG", "7")),
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
            for i, (prompt, path) in enumerate(zip(prompts, paths)):  # sequential: one local GPU
                print(f"STAGE: Drawing scene {i + 1} of {len(prompts)} (local, can take a while)...", flush=True)
                generate_image_drawthings(prompt, path, session=session)
    else:
        with requests.Session() as session, ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            list(pool.map(
                lambda job: generate_image(job[0], api_key, job[1], session=session),
                zip(prompts, paths),
            ))

    return paths
