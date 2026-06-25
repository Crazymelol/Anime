"""Thin abstraction over Anthropic/OpenAI so script_writer.py doesn't care which is configured."""

import os


class LLMClient:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider or os.environ.get("LLM_PROVIDER", "anthropic")
        if self.provider == "anthropic":
            self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        elif self.provider == "openai":
            self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def generate(self, system: str, user: str, max_tokens: int = 4096) -> str:
        if self.provider == "anthropic":
            return self._generate_anthropic(system, user, max_tokens)
        return self._generate_openai(system, user, max_tokens)

    def _generate_anthropic(self, system: str, user: str, max_tokens: int) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in response.content if block.type == "text")

    def _generate_openai(self, system: str, user: str, max_tokens: int) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content
