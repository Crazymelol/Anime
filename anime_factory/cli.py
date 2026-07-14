import argparse
import json
import sys
from pathlib import Path

from anime_factory.config import load_env_file
from anime_factory.pipeline import run_pipeline
from anime_factory.validation import ConfigError


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an anime episode script, images, voiceover, and video.")
    parser.add_argument("--config", required=True, type=Path, help="Path to episode config JSON")
    parser.add_argument("--output-dir", default=Path("output"), type=Path)
    parser.add_argument("--mock", action="store_true", help="Skip real LLM/image/TTS calls, write placeholder content")
    parser.add_argument("--skip-audio", action="store_true", help="Skip voiceover generation entirely")
    parser.add_argument("--skip-images", action="store_true", help="Skip image generation (also skips video)")
    parser.add_argument("--skip-video", action="store_true", help="Skip final video assembly")
    parser.add_argument("--no-captions", action="store_true", help="Don't burn on-screen captions into the video")
    args = parser.parse_args()

    # Make `python -m anime_factory.cli` see the same keys as the launcher
    # scripts: load .env from the CWD and from next to the config file.
    load_env_file(Path(".env"))
    load_env_file(args.config.resolve().parent / ".env")

    try:
        episode_config = json.loads(args.config.read_text())
    except FileNotFoundError:
        sys.exit(f"Config file not found: {args.config}")
    except json.JSONDecodeError as e:
        sys.exit(f"Config file {args.config} is not valid JSON: {e}")

    try:
        episode_dir = run_pipeline(
            episode_config,
            args.output_dir,
            mock=args.mock,
            skip_audio=args.skip_audio,
            skip_images=args.skip_images,
            skip_video=args.skip_video,
            captions=not args.no_captions,
        )
    except ConfigError as e:
        sys.exit(f"Config problem: {e}")

    print(f"Episode written to {episode_dir}")


if __name__ == "__main__":
    main()
