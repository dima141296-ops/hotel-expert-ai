from app.ai_provider import AIProvider, AIProviderError
from app.generated_content import (
    GeneratedContent,
    InvalidGeneratedContent,
)
from app.hotel_data import HotelData
from app.prompts import InvalidHotelData, build_expert_prompt


class ContentGenerationError(RuntimeError):
    pass


class ContentGenerator:
    def __init__(self, provider: AIProvider) -> None:
        self.provider = provider

    def generate(
        self,
        hotel: HotelData,
    ) -> GeneratedContent:
        try:
            prompt = build_expert_prompt(hotel)
            raw = self.provider.generate(prompt)
            return GeneratedContent.from_json(raw)

        except InvalidHotelData as exc:
            raise ContentGenerationError(
                str(exc)
            ) from exc

        except AIProviderError as exc:
            raise ContentGenerationError(
                "Не удалось получить ответ AI. "
                "Проверьте подключение. "
                "Повторите попытку."
            ) from exc

        except InvalidGeneratedContent as exc:
            raise ContentGenerationError(
                "AI вернул неполный результат. "
                "Повторите попытку и проверьте ответ."
            ) from exc
