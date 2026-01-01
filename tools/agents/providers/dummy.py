from .base import LLMResult


class DummyProvider:
    """Deterministic placeholder provider for testing."""

    def generate(self, prompt: str) -> LLMResult:
        return LLMResult(content=f"[dummy] prompt_length={len(prompt)}")
