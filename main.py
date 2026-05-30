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
    try:
        logger.info("Starting %s...", name)
        async with bot:
            await bot.start(token)
    except Exception as exc:
        logger.critical("%s crashed: %s", name, exc)


async def main() -> None:
    load_dotenv()
    settings = validate_settings()

    tasks: list = []

    if settings.bot1_token and settings.channel_id_1:
        tasks.append(
            _run_bot(
                GameNewsBot(settings),
                settings.bot1_token,
                "Bot 1 — Game News",
            )
        )
    else:
        logger.warning("Skipping Bot 1 — missing DISCORD_TOKEN or CHANNEL_ID_1")

    if settings.bot2_token and settings.channel_id_2:
        tasks.append(
            _run_bot(
                PriceCompareBot(settings),
                settings.bot2_token,
                "Bot 2 — Price Compare",
            )
        )
    else:
        logger.warning("Skipping Bot 2 — missing BOT_TOKEN_2 or CHANNEL_ID_2")

    if not tasks:
        logger.error("No bots configured — check your .env file")
        return

    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")
