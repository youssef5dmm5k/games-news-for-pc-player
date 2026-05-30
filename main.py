import logging
import sys

from dotenv import load_dotenv

from bot import GameDealsBot, validate_settings

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s",
    stream=sys.stdout,
)


def main() -> None:
    load_dotenv()

    settings = validate_settings()
    bot = GameDealsBot(settings)
    bot.run(settings.token)


if __name__ == "__main__":
    main()
