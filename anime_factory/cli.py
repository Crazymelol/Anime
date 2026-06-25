import argparse
import json
from pathlib import Path

from anime_factory.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an anime episode script, image prompts, and voiceover.")
    parser.add_argument("--config", required=True, type=Path, help="Path to episode config JSON")
    parser.add_argument("--output-dir", default=Path("output"), type=Path)
    parser.add_argument("--mock", action="store_true", help="Skip real LLM/TTS calls, write placeholder content")
    parser.add_argument("--skip-audio", action="store_true", help="Skip voiceover generation entirely")
    args = parser.parse_args()

    episode_config = json.loads(args.config.read_text())
    episode_dir = run_pipeline(episode_config, args.output_dir, mock=args.mock, skip_audio=args.skip_audio)
    print(f"Episode written to {episode_dir}")


if __name__ == "__main__":
    main()
