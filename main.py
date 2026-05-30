import asyncio
import logging
import sys

from dotenv import load_dotenv

from config import validate_settings
from bot1.client import GameNewsBot
from bot2.client import SteamPriceBot

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger("main")


async def launch(bot, token: str, name: str) -> None:
    print(f"[main] {name} — connecting...", flush=True)
    try:
        await bot.start(token)
    except Exception as exc:
        print(f"[main] {name} — CRASHED: {exc}", flush=True)
        logger.critical("%s crashed: %s", name, exc)
    finally:
        await bot.close()


async def main() -> None:
    load_dotenv()
    settings = validate_settings()

    bots = []
    if settings.bot1_token and settings.channel_id_1:
        bots.append(launch(GameNewsBot(settings), settings.bot1_token, "Bot 1 \u2013 Gaming News"))
    if settings.bot2_token and settings.channel_id_2:
        bots.append(launch(SteamPriceBot(settings), settings.bot2_token, "Bot 2 \u2013 Steam Prices"))

    if not bots:
        print("[main] No bots configured \u2014 check .env", flush=True)
        return

    await asyncio.gather(*bots)


if __name__ == "__main__":
    asyncio.run(main())
