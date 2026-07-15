"""Friendly setup doctor: checks every piece the pipeline needs and says what
to fix, in plain words. Run directly, via the "Check Setup.command" button, or
through the web UI (which renders the same structured results).
"""

import os
import shutil
import sys
from pathlib import Path

import requests

from anime_factory.config import load_env_file


def _result(ok: bool, title: str, fixes: list[str] | None = None) -> dict:
    return {"ok": ok, "title": title, "fixes": fixes or []}


def check_ffmpeg() -> dict:
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return _result(True, "ffmpeg is installed (video assembly will work)")
    return _result(False, "ffmpeg is MISSING", ["In Terminal run:  brew install ffmpeg"])


def check_env_file() -> dict:
    if Path(".env").is_file():
        return _result(True, ".env file found")
    return _result(False, "No .env file yet", [
        "Copy .env.example to .env and fill it in",
        "(only needed for REAL videos; the free test works without it)",
    ])


def check_drawthings() -> dict:
    if os.environ.get("IMAGE_PROVIDER", "stability") != "drawthings":
        if os.environ.get("STABILITY_API_KEY"):
            return _result(True, "Images: Stability AI (hosted), key found")
        return _result(False, "Images: STABILITY_API_KEY missing in .env", [
            "Add the key, or set IMAGE_PROVIDER=drawthings to use Draw Things for free",
        ])

    url = os.environ.get("DRAWTHINGS_URL", "http://127.0.0.1:7860").rstrip("/")
    try:
        response = requests.get(f"{url}/sdapi/v1/options", timeout=10)
        response.raise_for_status()
        response.json()
    except requests.exceptions.ConnectionError:
        return _result(False, f"Draw Things NOT reachable at {url}", [
            "Is the Draw Things app open, with Settings -> API Server -> Server Online ON?",
            "Does the port in DRAWTHINGS_URL match the port shown in the app?",
        ])
    except Exception:
        return _result(False, f"Something answered at {url} but not in the expected way", [
            "In Draw Things, set Protocol to HTTP (not gRPC) and turn Transport Layer Security OFF",
        ])
    return _result(True, f"Draw Things is connected at {url} (images will be free + local)")


def check_xtts() -> dict:
    if os.environ.get("TTS_PROVIDER", "elevenlabs") != "xtts":
        if os.environ.get("ELEVENLABS_API_KEY"):
            return _result(True, "Voice: ElevenLabs (hosted), key found")
        return _result(False, "Voice: ELEVENLABS_API_KEY missing in .env", [
            "Add the key, or set TTS_PROVIDER=xtts to use local voice for free",
        ])

    url = os.environ.get("XTTS_URL", "http://127.0.0.1:5002").rstrip("/")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception:
        return _result(False, f"Voice server (XTTS) NOT reachable at {url}", [
            "In a Terminal window, run and keep open:",
            "tts-server --model_name tts_models/multilingual/multi-dataset/xtts_v2",
        ])
    return _result(True, f"XTTS voice server is connected at {url} (voice will be free + local)")


def check_llm() -> dict:
    provider = os.environ.get("LLM_PROVIDER", "anthropic")
    key_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
    if os.environ.get(key_name):
        base = os.environ.get("OPENAI_BASE_URL", "")
        extra = f" via {base}" if provider == "openai" and base else ""
        return _result(True, f"Story writer: {provider}{extra} (key found)")
    return _result(False, f"Story writer key missing: set {key_name} in .env", [
        "Free options: OpenRouter or NVIDIA — see README",
    ])


def run_all_checks() -> list[dict]:
    load_env_file(Path(".env"))
    return [check_ffmpeg(), check_env_file(), check_llm(), check_drawthings(), check_xtts()]


def main() -> None:
    print("\nChecking your anime-factory setup...\n")
    results = run_all_checks()
    for r in results:
        print(("  [OK]  " if r["ok"] else "  [!!]  ") + r["title"])
        for fix in r["fixes"]:
            print("        -> " + fix)
    print("")
    if all(r["ok"] for r in results):
        print("Everything is ready! Double-click 'Make Video.command' to create a real video.")
    else:
        print("Fix the [!!] lines above, then run this check again.")
        print("(The FREE test video works regardless: 'Test Video (free).command')")
    print("")
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
