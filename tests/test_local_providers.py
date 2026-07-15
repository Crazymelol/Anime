"""Verify the local-provider clients speak the right protocols, using stub HTTP
servers standing in for the Draw Things API and a Coqui XTTS tts-server.
"""

import base64
import json
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from anime_factory.image_gen import generate_image_drawthings
from anime_factory.voiceover import _wav_bytes_to_mp3, synthesize_line_xtts

requires_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")

FAKE_PNG = base64.b64encode(b"\x89PNG\r\n\x1a\nfakepng").decode()


class _StubHandler(BaseHTTPRequestHandler):
    seen: dict = {}

    def log_message(self, *args):  # silence test output
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        _StubHandler.seen = {"path": self.path, "body": body}
        payload = json.dumps({"images": [FAKE_PNG]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlparse(self.path)
        _StubHandler.seen = {"path": parsed.path, "params": parse_qs(parsed.query)}
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.end_headers()
        self.wfile.write(b"RIFFfakewav")


@pytest.fixture
def stub_server():
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_drawthings_speaks_a1111_protocol(stub_server, tmp_path):
    out = generate_image_drawthings("kaito in server room", tmp_path / "s.png", base_url=stub_server)

    assert _StubHandler.seen["path"] == "/sdapi/v1/txt2img"
    body = _StubHandler.seen["body"]
    # SD1.5 anime models want quality tags up front and a 512-wide vertical frame
    assert body["prompt"] == "masterpiece, best quality, kaito in server room"
    assert (body["width"], body["height"]) == (512, 912)
    assert "bad anatomy" in body["negative_prompt"]
    assert body["cfg_scale"] == 7
    assert out.read_bytes().startswith(b"\x89PNG")


def test_xtts_speaker_name_request(stub_server):
    wav = synthesize_line_xtts("Damien Black", "Γεια σου κόσμε", language="el", base_url=stub_server)

    assert _StubHandler.seen["path"] == "/api/tts"
    params = _StubHandler.seen["params"]
    assert params["speaker_id"] == ["Damien Black"]
    assert params["language_id"] == ["el"]
    assert params["text"] == ["Γεια σου κόσμε"]
    assert wav.startswith(b"RIFF")


def test_xtts_wav_path_becomes_cloning_request(stub_server):
    synthesize_line_xtts("/voices/my_voice.wav", "hello", base_url=stub_server)

    params = _StubHandler.seen["params"]
    assert params["speaker_wav"] == ["/voices/my_voice.wav"]
    assert "speaker_id" not in params


@requires_ffmpeg
def test_wav_bytes_transcode_to_mp3(tmp_path):
    real_wav = subprocess.run(
        ["ffmpeg", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.3", "-f", "wav", "pipe:1"],
        capture_output=True, check=True,
    ).stdout
    out = tmp_path / "line.mp3"
    _wav_bytes_to_mp3(real_wav, out)
    assert out.exists() and out.stat().st_size > 0


def test_local_providers_need_no_keys(monkeypatch):
    from anime_factory.validation import validate_api_keys

    monkeypatch.setenv("IMAGE_PROVIDER", "drawthings")
    monkeypatch.setenv("TTS_PROVIDER", "xtts")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("STABILITY_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)

    validate_api_keys(skip_images=False, skip_audio=False)  # must not raise
