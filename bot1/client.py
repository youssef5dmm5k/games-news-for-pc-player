import asyncio
import logging
from datetime import datetime, timezone

import discord
from discord.ext import tasks

from config import Settings
from llm import ask_groq

logger = logging.getLogger("bot1.news")

DEALS = [
    {"store": "Steam", "title": "Elden Ring", "original": 59.99, "sale": 35.99, "ends": "2025-06-10", "url": "https://store.steampowered.com/app/1245620"},
    {"store": "Steam", "title": "Red Dead Redemption 2", "original": 59.99, "sale": 23.99, "ends": "2025-06-12", "url": "https://store.steampowered.com/app/1174180"},
    {"store": "Steam", "title": "Cyberpunk 2077", "original": 59.99, "sale": 29.99, "ends": "2025-06-11", "url": "https://store.steampowered.com/app/1091500"},
    {"store": "Epic Games", "title": "Alan Wake 2", "original": 39.99, "sale": 27.99, "ends": "2025-06-15", "url": "https://store.epicgames.com/alan-wake-2"},
    {"store": "Epic Games", "title": "Hades II", "original": 29.99, "sale": 26.99, "ends": "2025-06-14", "url": "https://store.epicgames.com/hades-2"},
]

NEWS = [
    {"title": "Nintendo Switch 2 Officially Announced", "summary": "Nintendo confirms 2026 release with backward compatibility and 4K support.", "url": "https://www.nintendo.com"},
    {"title": "GTA VI Development Update", "summary": "Rockstar Games enters final polishing phase; pre-orders expected Q3 2025.", "url": "https://www.rockstargames.com"},
    {"title": "Unity 7 Engine Revealed", "summary": "New real-time path tracing and AI-driven NPC behaviour toolkit announced.", "url": "https://unity.com"},
    {"title": "PlayStation Game Pass Competitor", "summary": "Sony expands PlayStation Plus Premium with day-one first-party titles.", "url": "https://www.playstation.com"},
    {"title": "ESL & Faceit Merge", "summary": "Combined esports platform valued at $2.4B; unified tournament ecosystem incoming.", "url": "https://www.eslgaming.com"},
]

RELEASES = [
    {"title": "Metroid Prime 4: Beyond", "date": "2025-06-12", "platform": "Switch", "url": "https://www.nintendo.com"},
    {"title": "Assassin's Creed Shadows", "date": "2025-07-15", "platform": "PS5, Xbox, PC", "url": "https://www.ubisoft.com"},
    {"title": "Fable (Reboot)", "date": "2025-09-09", "platform": "Xbox, PC", "url": "https://playfable.com"},
    {"title": "Half-Life 3", "date": "TBA 2026", "platform": "PC", "url": "https://www.valvesoftware.com"},
    {"title": "Borderlands 4", "date": "2025-08-08", "platform": "PS5, Xbox, PC", "url": "https://www.borderlands.com"},
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

        deals_tldr, news_tldr, releases_tldr = await asyncio.gather(
            self._generate_tldr(
                "You are a gaming deals analyst. Summarise today's best discounts in one sharp sentence in Arabic.",
                "Today's top game deals: " + "; ".join(f"{d['title']} -{int((1-d['sale']/d['original'])*100)}% on {d['store']}" for d in DEALS),
            ),
            self._generate_tldr(
                "You are a gaming industry analyst. Summarise the top news in one insightful sentence in Arabic.",
                "Gaming news today: " + "; ".join(n["title"] for n in NEWS),
            ),
            self._generate_tldr(
                "You are a release-date tracker. Summarise the upcoming releases in one exciting sentence in Arabic.",
                "Upcoming game releases: " + "; ".join(f"{r['title']} on {r['date']}" for r in RELEASES),
            ),
        )

        embed = discord.Embed(
            title="\u200f\u0627\u0644\u0645\u0631\u0643\u0632 \u0627\u0644\u0623\u0633\u0627\u0633\u064a \u0644\u0644\u0623\u0644\u0639\u0627\u0628 \u0648\u0627\u0644\u0623\u062e\u0628\u0627\u0631 \u0648\u0627\u0644\u0639\u0631\u0648\u0636",
            color=0x00AEFF,
            timestamp=datetime.now(timezone.utc),
        )

        deals_lines = []
        for d in DEALS:
            discount = int((1 - d["sale"] / d["original"]) * 100)
            deals_lines.append(
                f"**{d['title']}** "
                f"\u274c ~~${d['original']:.2f}~~ \u279c **${d['sale']:.2f}** (\u2013{discount}%) "
                f"\u200f\u0639\u0644\u0649 {d['store']} "
                f"| [\u0639\u0631\u0636 \u0627\u0644\u0635\u0641\u062d\u0629]({d['url']})"
            )
        deals_value = "\n".join(deals_lines)
        if deals_tldr:
            deals_value = f"*{deals_tldr}*\n\n" + deals_value

        news_lines = []
        for n in NEWS:
            news_lines.append(
                f"**{n['title']}**\n{n['summary']} "
                f"| [\u0627\u0642\u0631\u0623 \u0627\u0644\u0645\u0632\u064a\u062f]({n['url']})"
            )
        news_value = "\n\n".join(news_lines)
        if news_tldr:
            news_value = f"*{news_tldr}*\n\n" + news_value

        releases_lines = []
        for r in RELEASES:
            releases_lines.append(
                f"**{r['title']}** \u2014 {r['date']} ({r['platform']}) "
                f"| [\u0627\u0644\u0645\u0632\u064a\u062f]({r['url']})"
            )
        releases_value = "\n".join(releases_lines)
        if releases_tldr:
            releases_value = f"*{releases_tldr}*\n\n" + releases_value

        embed.add_field(
            name="\u200f\u0639\u0631\u0648\u0636 \u0648\u062a\u062e\u0641\u064a\u0636\u0627\u062a \u0627\u0644\u064a\u0648\u0645",
            value=deals_value,
            inline=False,
        )
        embed.add_field(
            name="\u200f\u0623\u0647\u0645 \u0623\u062e\u0628\u0627\u0631 \u0627\u0644\u0623\u0644\u0639\u0627\u0628 \u0627\u0644\u0639\u0627\u0644\u0645\u064a\u0629",
            value=news_value,
            inline=False,
        )
        embed.add_field(
            name="\u200f\u0645\u0648\u0627\u0639\u064a\u062f \u0646\u0632\u0648\u0644 \u0627\u0644\u0623\u0644\u0639\u0627\u0628 \u0627\u0644\u0642\u0627\u062f\u0645\u0629",
            value=releases_value,
            inline=False,
        )

        await channel.send(embed=embed)

    async def _generate_tldr(self, system: str, prompt: str) -> str:
        return await ask_groq(self._groq_api_key, system, prompt)

    @daily_news.before_loop
    async def before_daily_news(self) -> None:
        await self.wait_until_ready()
