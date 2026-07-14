import os

from anime_factory.config import DEFAULT_IMAGE_STYLE_SUFFIX, load_env_file
from anime_factory.pipeline import series_slug


def test_style_suffix_has_no_midjourney_flags():
    # CLI flags like --ar/--v are Midjourney syntax; they'd be sent as literal
    # prompt text to Stability and describe the wrong (landscape) framing.
    assert "--" not in DEFAULT_IMAGE_STYLE_SUFFIX
    assert "16:9" not in DEFAULT_IMAGE_STYLE_SUFFIX


def test_series_slug_strips_apostrophes_and_punctuation():
    assert series_slug("Kaito's Blade!") == "kaito_s_blade"
    assert series_slug("Shadow Protocol") == "shadow_protocol"
    assert series_slug("???") == "series"


def test_load_env_file_sets_missing_vars_only(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nTEST_ANIME_KEY=abc123\nTEST_ANIME_EXISTING=from_file\n\nBROKEN LINE\n")
    monkeypatch.setenv("TEST_ANIME_EXISTING", "already_set")
    monkeypatch.delenv("TEST_ANIME_KEY", raising=False)

    load_env_file(env)

    assert os.environ["TEST_ANIME_KEY"] == "abc123"
    assert os.environ["TEST_ANIME_EXISTING"] == "already_set"  # env wins over file
