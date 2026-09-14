import argparse
import os

from dotenv import load_dotenv

from app.ai_provider import AIProviderError
from app.content_generator import ContentGenerationError, ContentGenerator
from app.gemini_provider import GeminiProvider
from app.hotel_repository import HotelFileError, load_hotel

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Экспертный контент об одном отеле"
    )
    parser.add_argument(
        "hotel_file",
        help="Путь к JSON-файлу одного отеля",
    )
    args = parser.parse_args()
    load_dotenv()

    try:
        hotel = load_hotel(args.hotel_file)
        provider = GeminiProvider(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", ""),
        )
        result = ContentGenerator(provider).generate(hotel)
    except (
        HotelFileError,
        AIProviderError,
        ContentGenerationError,
    ) as exc:
        print(f"Ошибка: {exc}")
        return 1

    for title, text in result.as_sections().items():
        print(f"\n## {title}\n\n{text}")

    print("\nПроверьте все факты вручную перед публикацией.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
