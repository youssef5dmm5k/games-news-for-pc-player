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


async def run_bot(bot, token: str, name: str) -> None:
    """Start a single bot instance — no `async with` wrapping to avoid close conflicts."""
    print(f"[main] {name} — connecting...", flush=True)
    try:
        await bot.start(token)
    except Exception as exc:
        print(f"[main] {name} — CRASHED: {exc}", flush=True)
        logger.critical("%s crashed: %s", name, exc)
    finally:
        await bot.close()
        print(f"[main] {name} — fully closed", flush=True)


async def main() -> None:
    print("[main] Loading .env...", flush=True)
    load_dotenv()

    print("[main] Validating configuration...", flush=True)
    settings = validate_settings()

    tasks: list = []

    if settings.bot1_token and settings.channel_id_1:
        print("[main] Bot 1 (Game News) is configured — will start", flush=True)
        tasks.append(
            run_bot(
                GameNewsBot(settings),
                settings.bot1_token,
                "Bot 1 – Game News",
            )
        )
    else:
        print("[main] Skipping Bot 1 — missing DISCORD_TOKEN or CHANNEL_ID_1", flush=True)

    if settings.bot2_token and settings.channel_id_2:
        print("[main] Bot 2 (Price Compare) is configured — will start", flush=True)
        tasks.append(
            run_bot(
                PriceCompareBot(settings),
                settings.bot2_token,
                "Bot 2 – Price Compare",
            )
        )
    else:
        print("[main] Skipping Bot 2 — missing BOT_TOKEN_2 or CHANNEL_ID_2", flush=True)

    if not tasks:
        print("[main] FATAL: No bots configured — check your .env file", flush=True)
        return

    print(f"[main] Launching {len(tasks)} bot(s) via asyncio.gather...", flush=True)
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    print("[main] Application starting...", flush=True)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[main] Shutdown requested.", flush=True)
        logger.info("Shutdown requested.")
