import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

from config import Settings
from llm import ask_groq

logger = logging.getLogger("bot1.news")

NEWS_TEMPLATES = [
    {
        "title": "Elden Ring Shadow of the Erdtree",
        "description": "New gameplay footage reveals expanded map with 10+ legacy dungeons.",
        "url": "https://www.gamespot.com/elden-ring-shadow-erdtree",
    },
    {
        "title": "Steam Summer Sale 2025",
        "description": "Up to 90% off on thousands of titles starting next week.",
        "url": "https://store.steampowered.com",
    },
    {
        "title": "Cyberpunk 2077 Phantom Liberty",
        "description": "CD Projekt reports 5 million copies sold since the 2.0 overhaul.",
        "url": "https://www.cyberpunk.net",
    },
    {
        "title": "NVIDIA GeForce RTX 5090",
        "description": "Next-gen GPU rumored to ship with 32 GB GDDR7 and 4 nm process.",
        "url": "https://www.nvidia.com",
    },
    {
        "title": "Valve Steam Deck 2",
        "description": "Leaked specs suggest AMD Zen 5 APU with ray tracing support.",
        "url": "https://www.steamdeck.com",
    },
]


class GameNewsBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.all())
        self.settings = settings
        self._channel_id = settings.channel_id_1
        self._groq_api_key = settings.groq_api_key

    async def on_ready(self) -> None:
        print(f"[Bot1] ONLINE — {self.user}", flush=True)
        self.daily_news.start()

    @tasks.loop(hours=24)
    async def daily_news(self) -> None:
        channel = self.get_channel(self._channel_id)
        if channel is None:
            logger.error("Channel %s not found", self._channel_id)
            return

        embed = discord.Embed(
            title="Daily Gaming News Roundup",
            color=0x00AEFF,
            timestamp=datetime.now(timezone.utc),
        )

        for article in NEWS_TEMPLATES:
            embed.add_field(
                name=article["title"],
                value=f"{article['description']}\n[Read more]({article['url']})",
                inline=False,
            )

        tldr = await ask_groq(
            self._groq_api_key,
            "You are a gaming industry analyst. Summarise today's gaming news in one witty sentence.",
            "Summarise the following gaming news headlines: "
            + ", ".join(n["title"] for n in NEWS_TEMPLATES),
        )
        if tldr:
            embed.set_footer(text=f"AI TL;DR — {tldr}")

        await channel.send(embed=embed)

    @daily_news.before_loop
    async def before_daily_news(self) -> None:
        await self.wait_until_ready()
