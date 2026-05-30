import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

from bot.config import Settings
from bot.deals import STORE_IDS, fetch_deals
from bot.formatters import format_arabic_date, format_price
from bot.groq_client import generate_description

logger = logging.getLogger("game_deals_bot.client")


class GameDealsBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.settings = settings
        self._groq_api_key = settings.groq_api_key
        self._channel_id = settings.channel_id

    # ── lifecycle ──────────────────────────────────────────────

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        self.daily_deals_task.start()

    # ── task loop ──────────────────────────────────────────────

    @tasks.loop(hours=24)
    async def daily_deals_task(self) -> None:
        channel = self.get_channel(self._channel_id)
        if channel is None:
            logger.error("Channel %s not found — check CHANNEL_ID", self._channel_id)
            return

        for store_name, store_id in STORE_IDS.items():
            deals = await fetch_deals(store_id)
            if not deals:
                logger.info("No deals returned from %s", store_name)
                continue

            lines: list[str] = []
            for deal in deals:
                line = await self._build_deal_line(deal)
                lines.append(line)
                await asyncio.sleep(0.5)

            embed = discord.Embed(
                title=f"🎮 عروض {store_name} اليوم",
                description="\n\n".join(lines),
                color=0x00AEFF if store_name == "Steam" else 0x9147FF,
            )
            embed.set_footer(text="يتم التحديث يومياً")

            await channel.send(embed=embed)
            await asyncio.sleep(1)

    @daily_deals_task.before_loop
    async def before_daily_deals(self) -> None:
        await self.wait_until_ready()

    # ── helpers ────────────────────────────────────────────────

    async def _build_deal_line(self, deal: dict) -> str:
        game_name = deal.get("title", "Unknown")
        original = format_price(deal.get("normalPrice", "0"))
        current = format_price(deal.get("salePrice", "0"))

        last_change = int(deal.get("lastChange", 0))
        expiry = self._estimate_expiry(last_change)
        expiry_str = format_arabic_date(expiry)

        description = await generate_description(game_name, self._groq_api_key)

        return (
            f"- **{game_name}** {description} "
            f"تم تنزيل السعر من {original} إلى {current} "
            f"وينتهي هذا العرض يوم {expiry_str}"
        )

    @staticmethod
    def _estimate_expiry(last_change_unix: int) -> int:
        week_seconds = 7 * 24 * 3600
        estimated = last_change_unix + week_seconds
        now = int(datetime.now(timezone.utc).timestamp())
        return estimated if estimated > now else now + week_seconds
