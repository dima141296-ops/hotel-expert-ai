from typing import Any

from google import genai
from google.genai import errors

from app.ai_provider import AIProviderError


class GeminiProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise AIProviderError(
                "Не задан GEMINI_API_KEY "
                "в локальном файле .env."
            )

        if not model.strip():
            raise AIProviderError(
                "Не задана модель GEMINI_MODEL."
            )

        self.model = model.strip()
        self.client = client or genai.Client(
            api_key=api_key.strip()
        )

    def generate(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )

        except errors.APIError as exc:
            raise AIProviderError(
                f"Ошибка Gemini API: {exc.code}"
            ) from exc

        except Exception as exc:
            raise AIProviderError(
                "Не удалось связаться с Gemini API."
            ) from exc

        if (
            not isinstance(response.text, str)
            or not response.text.strip()
        ):
            raise AIProviderError(
                "Gemini вернул пустой ответ."
            )

        return response.text
