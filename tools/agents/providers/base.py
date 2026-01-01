from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMResult:
    content: str


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> LLMResult: ...
