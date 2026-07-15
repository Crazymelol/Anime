import json
import shutil
import time

import pytest

from anime_factory import webui

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

CONFIG = {
    "series_title": "Studio Test",
    "total_episodes": 12,
    "episode_number": 1,
    "premise": "A tiny test.",
    "tone": "dark",
    "pacing": "fast",
    "total_minutes": 1,
    "style": "dark_fantasy",
    "language": "en",
    "characters": [
        {"name": "Kaito", "role": "main character", "visual_description": "anime boy", "voice": "adam"},
        {"name": "Narrator", "role": "narrator", "visual_description": None, "voice": "antoni"},
    ],
}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(webui, "OUTPUT_DIR", tmp_path / "output")
    webui._state.update(running=False, log=[], done=False, ok=False, video=None)
    return webui.app.test_client()


def test_index_serves_studio_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Anime Factory Studio" in response.data


def test_status_returns_structured_checks(client):
    checks = client.get("/api/status").get_json()
    assert isinstance(checks, list) and len(checks) >= 4
    assert all({"ok", "title", "fixes"} <= set(c) for c in checks)


@requires_ffmpeg
def test_generate_mock_runs_to_completion(client):
    response = client.post("/api/generate", data=json.dumps({"config": CONFIG, "mock": True}),
                           content_type="application/json")
    assert response.status_code == 200

    for _ in range(120):  # mock render takes a few seconds
        state = client.get("/api/progress").get_json()
        if state["done"]:
            break
        time.sleep(0.5)
    assert state["done"] and state["ok"], state["log"]
    assert state["video"].endswith("episode.mp4")

    # the video must actually be downloadable through the server
    video = client.get(state["video"])
    assert video.status_code == 200 and len(video.data) > 10000


def test_generate_rejects_concurrent_runs(client):
    webui._state["running"] = True
    response = client.post("/api/generate", data=json.dumps({"config": CONFIG, "mock": True}),
                           content_type="application/json")
    assert response.status_code == 409
