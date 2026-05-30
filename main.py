import asyncio
import logging
import sys

from dotenv import load_dotenv

from config import validate_settings
from bot1.client import GameNewsBot
from bot2.client import PriceCompareBot

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("main")


async def _run_bot(bot, token: str, name: str) -> None:
    """Start a single bot instance and keep it running."""
    try:
        logger.info("Starting %s...", name)
        async with bot:
            await bot.start(token)
    except Exception as exc:
        logger.critical("%s crashed: %s", name, exc)
        raise


async def main() -> None:
    load_dotenv()
    settings = validate_settings()

    bot1 = GameNewsBot(settings)
    bot2 = PriceCompareBot(settings)

    await asyncio.gather(
        _run_bot(bot1, settings.bot1_token, "Bot 1 — Game News"),
        _run_bot(bot2, settings.bot2_token, "Bot 2 — Price Compare"),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
