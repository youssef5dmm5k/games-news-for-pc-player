import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

from config import Settings
from llm import ask_groq

logger = logging.getLogger("bot2.steam")

STEAM_CARDS = {
    "$10 Card": {
        "denomination": 10,
        "stores": {
            "Kinguin": {"price": 9.45, "url": "https://www.kinguin.net/steam-10"},
            "Eneba":   {"price": 9.39, "url": "https://www.eneba.com/steam-10"},
            "G2A":     {"price": 9.69, "url": "https://www.g2a.com/steam-10"},
        },
    },
    "$20 Card": {
        "denomination": 20,
        "stores": {
            "Kinguin": {"price": 18.25, "url": "https://www.kinguin.net/steam-20"},
            "Eneba":   {"price": 18.10, "url": "https://www.eneba.com/steam-20"},
            "G2A":     {"price": 18.90, "url": "https://www.g2a.com/steam-20"},
        },
    },
    "$50 Card": {
        "denomination": 50,
        "stores": {
            "Kinguin": {"price": 45.99, "url": "https://www.kinguin.net/steam-50"},
            "Eneba":   {"price": 45.50, "url": "https://www.eneba.com/steam-50"},
            "G2A":     {"price": 46.80, "url": "https://www.g2a.com/steam-50"},
        },
    },
}


class SteamPriceBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        super().__init__(intents=discord.Intents.all())
        self.settings = settings
        self._channel_id = settings.channel_id_2
        self._groq_api_key = settings.groq_api_key

    async def on_ready(self) -> None:
        print(f"[Bot2] ONLINE — {self.user}", flush=True)
        self.daily_price_report.start()

    @tasks.loop(hours=24)
    async def daily_price_report(self) -> None:
        channel = self.get_channel(self._channel_id)
        if channel is None:
            logger.error("Channel %s not found", self._channel_id)
            return

        store_names = list(next(iter(STEAM_CARDS.values()))["stores"].keys())
        header = "| Card | " + " | ".join(store_names) + " |"
        separator = "|------|" + "|".join("------" for _ in store_names) + "|"

        rows = []
        analysis_lines = []
        for name, info in STEAM_CARDS.items():
            prices = [f"${info['stores'][s]['price']:.2f}" for s in store_names]
            rows.append(f"| {name} | " + " | ".join(prices) + " |")
            analysis_lines.append(f"{name}: " + ", ".join(
                f"{s}=${d['price']:.2f}" for s, d in info["stores"].items()
            ))

        grid = f"```\n{header}\n{separator}\n" + "\n".join(rows) + "\n```"

        embed = discord.Embed(
            title="Steam Gift Card Price Matrix",
            description="Real-time price comparison across trusted marketplaces.\n\n" + grid,
            color=0x9147FF,
            timestamp=datetime.now(timezone.utc),
        )

        insight = await ask_groq(
            self._groq_api_key,
            "You are a sharp AI shopping analyst. Provide one witty, insightful sentence about the best Steam card deal based on the price data.",
            "Analyse these Steam Gift Card prices: " + "; ".join(analysis_lines),
        )
        if insight:
            embed.add_field(
                name="AI Shopping Insight",
                value=insight,
                inline=False,
            )

        await channel.send(embed=embed)

    @daily_price_report.before_loop
    async def before_daily_price_report(self) -> None:
        await self.wait_until_ready()
