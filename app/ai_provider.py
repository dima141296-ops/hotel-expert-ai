from typing import Protocol


class AIProviderError(RuntimeError):
    pass


class AIProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...
