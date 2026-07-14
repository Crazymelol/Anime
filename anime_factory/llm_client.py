"""Thin abstraction over Anthropic/OpenAI so script_writer.py doesn't care which is configured."""

import os

from anime_factory.validation import ConfigError


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
        # Build the SDK client once: missing keys fail here (before any spend)
        # and repeated generate() calls reuse the pooled connection.
        if self.provider == "anthropic":
            self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
            self._client = self._make_anthropic()
        elif self.provider == "openai":
            self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
            self._client = self._make_openai()
        else:
            raise ConfigError(f"Unknown LLM provider: {self.provider}")

    def _make_anthropic(self):
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ConfigError("ANTHROPIC_API_KEY is not set (check your .env).")
        return anthropic.Anthropic()

    def _make_openai(self):
        from openai import OpenAI

        if not os.environ.get("OPENAI_API_KEY"):
            raise ConfigError("OPENAI_API_KEY is not set (check your .env).")
        return OpenAI()

    def generate(self, system: str, user: str, max_tokens: int = 4096) -> str:
        if self.provider == "anthropic":
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(block.text for block in response.content if block.type == "text")

        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content
