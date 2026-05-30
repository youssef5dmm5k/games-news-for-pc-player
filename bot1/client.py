import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

from config import Settings
from llm import ask_groq

logger = logging.getLogger("bot1.news")

DEALS = [
    {"store": "Epic Games", "title": "Suicide Squad: Kill the Justice League", "original": 69.99, "sale": 3.49, "ends": "1 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "Suicide Squad: Kill the Justice League - Digital Deluxe Edition", "original": 99.99, "sale": 4.99, "ends": "4 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "EA SPORTS PGA TOUR", "original": 69.99, "sale": 6.99, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "Gotham Knights: Deluxe", "original": 79.99, "sale": 11.99, "ends": "1 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "LONESTAR", "original": 12.99, "sale": 0, "ends": "4 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "WILD HEARTS Standard Edition", "original": 69.99, "sale": 6.99, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "Immortals of Aveum Deluxe Edition", "original": 69.99, "sale": 6.99, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "EA SPORTS PGA TOUR Deluxe Edition", "original": 84.99, "sale": 8.49, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "WILD HEARTS Karakuri Edition", "original": 89.99, "sale": 8.99, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Epic Games", "title": "RAVEN2 Half anniversary Starter Pack", "original": 69.99, "sale": 0, "ends": "6 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Steam", "title": "Red Dead Redemption 2", "original": 59.99, "sale": 23.99, "ends": "10 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Steam", "title": "Elden Ring", "original": 59.99, "sale": 35.99, "ends": "10 \u064a\u0648\u0646\u064a\u0648"},
    {"store": "Steam", "title": "Cyberpunk 2077", "original": 59.99, "sale": 29.99, "ends": "11 \u064a\u0648\u0646\u064a\u0648"},
]

FALLBACK_DESC = "\u0644\u0639\u0628\u0629 \u0645\u063a\u0627\u0645\u0631\u0627\u062a \u0648\u062a\u062d\u062f\u064a \u0645\u0645\u064a\u0632\u0629 \u0644\u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0643\u0645\u0628\u064a\u0648\u062a\u0631."


class GameNewsBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.all())
        self.settings = settings
        self._channel_id = settings.channel_id_1
        self._groq_api_key = settings.groq_api_key

    async def on_ready(self) -> None:
        print(f"[Bot1] ONLINE \u2014 {self.user}", flush=True)
        self.daily_deals.start()

    @tasks.loop(hours=24)
    async def daily_deals(self) -> None:
        channel = self.get_channel(self._channel_id)
        if channel is None:
            logger.error("Channel %s not found", self._channel_id)
            return

        store_groups = {}
        for deal in DEALS:
            store_groups.setdefault(deal["store"], []).append(deal)

        for store, deals in store_groups.items():
            lines = [f"\u2728 **\u0639\u0631\u0648\u0636 {store} \u0627\u0644\u064a\u0648\u0645**\n"]
            for deal in deals:
                desc = await self._get_ar_desc(deal["title"])
                sale_str = "\u0645\u062c\u0627\u0646\u0627\u064b" if deal["sale"] == 0 else f"{deal['sale']:.2f}$"
                lines.append(
                    f"\u2022 **{deal['title']}**\n"
                    f"  {desc}\n"
                    f"  \u062a\u0645 \u062a\u0646\u0632\u064a\u0644 \u0627\u0644\u0633\u0639\u0631 \u0645\u0646 {deal['original']:.2f}$ \u0625\u0644\u0649 {sale_str} "
                    f"\u0648\u064a\u0646\u062a\u0647\u064a \u0647\u0630\u0627 \u0627\u0644\u0639\u0631\u0636 \u064a\u0648\u0645 {deal['ends']}.\n"
                )

            color = 0x00AEFF if store == "Steam" else 0x9147FF
            embed = discord.Embed(
                description="\n".join(lines),
                color=color,
                timestamp=datetime.now(timezone.utc),
            )
            await channel.send(embed=embed)

    async def _get_ar_desc(self, title: str) -> str:
        try:
            result = await ask_groq(
                self._groq_api_key,
                "You are a professional Middle Eastern gaming reviewer. "
                "Write a very brief, single-sentence catchy premise/description in pure, natural Arabic "
                f"for the game: {title}. "
                "Do not include any English translations, markdown tags, or preambles. Output only the sentence.",
                f"Describe the game {title} in one short Arabic sentence.",
                max_tokens=60,
            )
            return result or FALLBACK_DESC
        except Exception:
            return FALLBACK_DESC

    @daily_deals.before_loop
    async def before_daily_deals(self) -> None:
        await self.wait_until_ready()
