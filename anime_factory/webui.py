"""Anime Factory Studio: a local web page that drives the whole pipeline.

Run with `python -m anime_factory.webui` (or the "Open Studio.command" button)
and open http://127.0.0.1:8765 — write the story in a form, check that
everything is connected, make a free test or a real video, watch live
progress, and play the result. Runs only on this machine; nothing is exposed
to the internet.
"""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from anime_factory.check_setup import run_all_checks

PORT = 8765
OUTPUT_DIR = Path("output")

app = Flask(__name__)

_state_lock = threading.Lock()
_state: dict = {"running": False, "log": [], "done": False, "ok": False, "video": None}


def _run_generation(config_path: Path, mock: bool) -> None:
    cmd = [sys.executable, "-m", "anime_factory.cli",
           "--config", str(config_path), "--output-dir", str(OUTPUT_DIR)]
    if mock:
        cmd.append("--mock")

    # Make the package importable no matter where the Studio was started from.
    package_root = str(Path(__file__).resolve().parent.parent)
    env = dict(os.environ)
    env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, env=env)
    episode_dir = None
    for line in process.stdout:
        line = line.rstrip()
        if line.startswith("Episode written to "):
            episode_dir = Path(line.removeprefix("Episode written to "))
        with _state_lock:
            _state["log"].append(line)
    process.wait()

    video = None
    if episode_dir and (episode_dir / "episode.mp4").exists():
        video = "/output/" + str((episode_dir / "episode.mp4").relative_to(OUTPUT_DIR))
    with _state_lock:
        _state.update(running=False, done=True, ok=process.returncode == 0 and video is not None,
                      video=video)
        if process.returncode != 0:
            _state["log"].append("*** Something went wrong — the messages above say why. ***")


@app.get("/api/status")
def api_status():
    return jsonify(run_all_checks())


@app.post("/api/generate")
def api_generate():
    with _state_lock:
        if _state["running"]:
            return jsonify({"error": "A video is already being made — wait for it to finish."}), 409
        _state.update(running=True, log=[], done=False, ok=False, video=None)

    payload = request.get_json(force=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    config_path = OUTPUT_DIR / "_studio_config.json"
    config_path.write_text(json.dumps(payload["config"], ensure_ascii=False, indent=2))

    threading.Thread(target=_run_generation, args=(config_path, bool(payload.get("mock"))),
                     daemon=True).start()
    return jsonify({"started": True})


@app.get("/api/progress")
def api_progress():
    with _state_lock:
        return jsonify(dict(_state))


@app.get("/output/<path:relpath>")
def serve_output(relpath: str):
    return send_from_directory(OUTPUT_DIR.resolve(), relpath)


@app.get("/")
def index():
    return INDEX_HTML


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Anime Factory Studio</title>
<style>
  :root { --bg:#12121c; --card:#1b1b2b; --line:#2e2e46; --text:#e8e8f2; --dim:#9a9ab5;
          --accent:#8b5cf6; --ok:#34d399; --bad:#f87171; }
  * { box-sizing:border-box; }
  body { margin:0; background:var(--bg); color:var(--text);
         font:16px/1.5 -apple-system, "Segoe UI", sans-serif; }
  .wrap { max-width:820px; margin:0 auto; padding:24px 16px 80px; }
  h1 { font-size:26px; margin:8px 0 2px; } .sub { color:var(--dim); margin:0 0 24px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px;
          padding:20px; margin-bottom:18px; }
  h2 { font-size:18px; margin:0 0 14px; }
  label { display:block; font-size:13px; color:var(--dim); margin:12px 0 4px; }
  input, textarea, select { width:100%; background:#12121e; color:var(--text);
    border:1px solid var(--line); border-radius:8px; padding:9px 11px; font:inherit; }
  textarea { min-height:70px; resize:vertical; }
  .row { display:flex; gap:12px; } .row > div { flex:1; }
  .char { border:1px solid var(--line); border-radius:10px; padding:12px; margin-top:10px; }
  button { background:var(--accent); color:#fff; border:0; border-radius:10px;
    padding:12px 18px; font:inherit; font-weight:600; cursor:pointer; }
  button.ghost { background:transparent; border:1px solid var(--line); color:var(--text); }
  button:disabled { opacity:.45; cursor:default; }
  .btns { display:flex; gap:10px; flex-wrap:wrap; margin-top:16px; }
  .check { padding:6px 0; } .check b { font-weight:600; }
  .okc { color:var(--ok); } .badc { color:var(--bad); }
  .fix { color:var(--dim); font-size:13px; margin-left:26px; }
  #log { background:#0c0c14; border:1px solid var(--line); border-radius:10px;
    padding:12px; font:13px/1.6 ui-monospace, monospace; white-space:pre-wrap;
    max-height:260px; overflow-y:auto; display:none; }
  video { width:100%; max-width:330px; border-radius:12px; margin-top:14px; display:block; }
  .note { color:var(--dim); font-size:13px; }
</style>
</head>
<body><div class="wrap">
  <h1>🎬 Anime Factory Studio</h1>
  <p class="sub">Write a story, press a button, get an anime short.</p>

  <div class="card">
    <h2>1 · Is everything connected?</h2>
    <button class="ghost" onclick="checkSetup()">Run check</button>
    <div id="checks"></div>
  </div>

  <div class="card">
    <h2>2 · Your story</h2>
    <div class="row">
      <div><label>Show name</label><input id="title" value="Shadow Protocol"></div>
      <div><label>Episode number</label><input id="epnum" type="number" value="1" min="1"></div>
    </div>
    <label>What happens in this episode?</label>
    <textarea id="premise">Kaito infiltrates a corporate server and finds evidence that the company has been running experiments on people with abilities like his.</textarea>
    <div class="row">
      <div><label>Art style</label>
        <select id="style">
          <option value="dark_fantasy">Dark fantasy (Solo Leveling vibe)</option>
          <option value="wholesome">Wholesome (Shinkai vibe)</option>
          <option value="cyberpunk">Cyberpunk</option>
        </select></div>
      <div><label>Language</label>
        <select id="language"><option value="en">English</option><option value="el">Ελληνικά</option></select></div>
      <div><label>Length (minutes)</label><input id="minutes" type="number" value="1" min="1" max="15"></div>
    </div>
    <div id="chars"></div>
    <button class="ghost" style="margin-top:10px" onclick="addChar()">+ Add character</button>
  </div>

  <div class="card">
    <h2>3 · Make the video</h2>
    <div class="btns">
      <button id="btnMock" onclick="generate(true)">🧪 Free test video</button>
      <button id="btnReal" onclick="generate(false)">🎬 Make REAL video</button>
    </div>
    <p class="note">The free test uses placeholder art and silent voice — it costs nothing and
    checks that the machine works. The real one uses your connected art &amp; voice services.</p>
    <div id="log"></div>
    <div id="result"></div>
  </div>

<script>
const VOICE_HINT = 'ElevenLabs: adam / antoni / bella · Local XTTS: e.g. "Damien Black" or a .wav path';

function charRow(c) {
  const div = document.createElement('div');
  div.className = 'char';
  div.innerHTML = `
    <div class="row">
      <div><label>Name</label><input class="c-name" value="${c.name}"></div>
      <div><label>Role</label>
        <select class="c-role">
          <option value="main character"${c.role==='main character'?' selected':''}>character</option>
          <option value="narrator"${c.role==='narrator'?' selected':''}>narrator</option>
        </select></div>
      <div><label>Voice</label><input class="c-voice" value="${c.voice}" title="${VOICE_HINT}"></div>
    </div>
    <label>What do they look like? (leave empty for the narrator)</label>
    <input class="c-desc" value="${c.desc}">`;
  return div;
}
function addChar(c) {
  document.getElementById('chars').appendChild(
    charRow(c || {name:'', role:'main character', voice:'adam', desc:''}));
}
addChar({name:'Kaito', role:'main character', voice:'adam',
  desc:'anime teen boy, dark messy hair, sharp eyes, black hoodie, fingerless gloves, glowing blue code reflections'});
addChar({name:'Narrator', role:'narrator', voice:'antoni', desc:''});

function buildConfig() {
  const characters = [...document.querySelectorAll('.char')].map(d => ({
    name: d.querySelector('.c-name').value.trim(),
    role: d.querySelector('.c-role').value,
    visual_description: d.querySelector('.c-desc').value.trim() || null,
    voice: d.querySelector('.c-voice').value.trim(),
  }));
  return {
    series_title: document.getElementById('title').value.trim(),
    total_episodes: 12,
    episode_number: parseInt(document.getElementById('epnum').value) || 1,
    premise: document.getElementById('premise').value.trim(),
    tone: 'dark', pacing: 'fast, with a cliffhanger ending',
    total_minutes: parseInt(document.getElementById('minutes').value) || 1,
    style: document.getElementById('style').value,
    language: document.getElementById('language').value,
    characters,
  };
}

async function checkSetup() {
  const el = document.getElementById('checks');
  el.innerHTML = '<p class="note">Checking…</p>';
  const checks = await (await fetch('/api/status')).json();
  el.innerHTML = checks.map(c =>
    `<div class="check"><b class="${c.ok?'okc':'badc'}">${c.ok?'✓':'✗'}</b> ${c.title}` +
    c.fixes.map(f => `<div class="fix">→ ${f}</div>`).join('') + '</div>').join('');
}

let poller = null;
async function generate(mock) {
  const res = await fetch('/api/generate', {method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({config: buildConfig(), mock})});
  if (!res.ok) { alert((await res.json()).error || 'Could not start'); return; }
  document.getElementById('btnMock').disabled = true;
  document.getElementById('btnReal').disabled = true;
  document.getElementById('result').innerHTML = '';
  const log = document.getElementById('log');
  log.style.display = 'block'; log.textContent = 'Starting…';
  poller = setInterval(poll, 1200);
}

async function poll() {
  const s = await (await fetch('/api/progress')).json();
  const log = document.getElementById('log');
  log.textContent = s.log.join('\\n') || 'Working…';
  log.scrollTop = log.scrollHeight;
  if (s.done) {
    clearInterval(poller);
    document.getElementById('btnMock').disabled = false;
    document.getElementById('btnReal').disabled = false;
    document.getElementById('result').innerHTML = s.ok
      ? `<p><b class="okc">Done!</b> Your video:</p><video controls src="${s.video}"></video>
         <p class="note">Right-click the video → “Save Video As…” to keep it.</p>`
      : '<p><b class="badc">Something went wrong</b> — the log above says why.</p>';
  }
}
</script>
</div></body></html>"""


def main() -> None:
    print(f"Anime Factory Studio running — open http://127.0.0.1:{PORT} in your browser.")
    print("(Keep this window open while you use it. Press Ctrl+C to stop.)")
    app.run(host="127.0.0.1", port=PORT, debug=False)


if __name__ == "__main__":
    main()
