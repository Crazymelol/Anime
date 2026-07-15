"""Friendly setup doctor: checks every piece the pipeline needs and says what
to fix, in plain words. Run directly or via the "Check Setup.command" button.
"""

import os
import shutil
import sys
from pathlib import Path

import requests

from anime_factory.config import load_env_file

OK = "  [OK]  "
BAD = "  [!!]  "


def check_ffmpeg() -> bool:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        print(f"{OK}ffmpeg is installed (video assembly will work)")
        return True
    print(f"{BAD}ffmpeg is MISSING. In Terminal run:  brew install ffmpeg")
    return False


def check_env_file() -> bool:
    if Path(".env").is_file():
        print(f"{OK}.env file found")
        return True
    print(f"{BAD}No .env file yet. Copy .env.example to .env and fill it in")
    print("        (only needed for REAL videos; the free test works without it).")
    return False


def check_drawthings() -> bool:
    if os.environ.get("IMAGE_PROVIDER", "stability") != "drawthings":
        key = bool(os.environ.get("STABILITY_API_KEY"))
        print(f"{OK if key else BAD}Images: using Stability AI (hosted). "
              + ("Key found." if key else "STABILITY_API_KEY missing in .env — "
                 "or set IMAGE_PROVIDER=drawthings to use Draw Things for free."))
        return key

    url = os.environ.get("DRAWTHINGS_URL", "http://127.0.0.1:7860").rstrip("/")
    try:
        response = requests.get(f"{url}/sdapi/v1/options", timeout=10)
        response.raise_for_status()
        response.json()
    except requests.exceptions.ConnectionError:
        print(f"{BAD}Draw Things NOT reachable at {url}")
        print("        -> Is the Draw Things app open, with Settings -> API Server -> Server Online ON?")
        print("        -> Does the port in DRAWTHINGS_URL match the port shown in the app?")
        return False
    except Exception:
        print(f"{BAD}Something answered at {url} but not in the expected way.")
        print("        -> In Draw Things, set Protocol to HTTP (not gRPC) and turn Transport Layer Security OFF.")
        return False
    print(f"{OK}Draw Things is connected at {url} (images will be free + local)")
    return True


def check_xtts() -> bool:
    if os.environ.get("TTS_PROVIDER", "elevenlabs") != "xtts":
        key = bool(os.environ.get("ELEVENLABS_API_KEY"))
        print(f"{OK if key else BAD}Voice: using ElevenLabs (hosted). "
              + ("Key found." if key else "ELEVENLABS_API_KEY missing in .env — "
                 "or set TTS_PROVIDER=xtts to use local TTS for free."))
        return key

    url = os.environ.get("XTTS_URL", "http://127.0.0.1:5002").rstrip("/")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception:
        print(f"{BAD}Voice server (XTTS) NOT reachable at {url}")
        print("        -> In a Terminal window, run and keep open:")
        print("           tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2")
        return False
    print(f"{OK}XTTS voice server is connected at {url} (voice will be free + local)")
    return True


def check_llm() -> bool:
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if os.environ.get(key_name):
        base = os.environ.get("OPENAI_BASE_URL", "")
        extra = f" via {base}" if provider == "openai" and base else ""
        print(f"{OK}Story writer: {provider}{extra} (key found)")
        return True
    print(f"{BAD}Story writer key missing: set {key_name} in .env")
    print("        (free options: OpenRouter or NVIDIA — see README)")
    return False


def main() -> None:
    load_env_file(Path(".env"))
    print("")
    print("Checking your anime-factory setup...")
    print("")
    results = [check_ffmpeg(), check_env_file(), check_llm(), check_drawthings(), check_xtts()]
    print("")
    if all(results):
        print("Everything is ready! Double-click 'Make Video.command' to create a real video.")
    else:
        print("Fix the [!!] lines above, then run this check again.")
        print("(The FREE test video works regardless: 'Test Video (free).command')")
    print("")
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
