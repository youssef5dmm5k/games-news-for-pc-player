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
        sep = "|------|" + "|".join("------" for _ in store_names) + "|"

        rows = []
        analysis_lines = []
        best_saving = ("", 0, "")
        for name, info in STEAM_CARDS.items():
            prices = [f"${info['stores'][s]['price']:.2f}" for s in store_names]
            rows.append(f"| {name} | " + " | ".join(prices) + " |")
            store_list = ", ".join(f"{s}=${d['price']:.2f}" for s, d in info["stores"].items())
            analysis_lines.append(f"{name}: {store_list}")
            face_value = info["denomination"]
            cheapest = min(s["price"] for s in info["stores"].values())
            saving = face_value - cheapest
            if saving > best_saving[0]:
                best_saving = (saving, name, cheapest)

        table = f"```\n{header}\n{sep}\n" + "\n".join(rows) + "\n```"

        grid_lines = []
        grid_lines.append(f"`{'STORE':<12} {'$10':>8} {'$20':>8} {'$50':>8}`")
        grid_lines.append(f"`{'------':<12} {'---':>8} {'---':>8} {'---':>8}`")
        for store in store_names:
            vals = [f"${STEAM_CARDS[name]['stores'][store]['price']:.2f}" for name in STEAM_CARDS]
            grid_lines.append(f"`{store:<12} {vals[0]:>8} {vals[1]:>8} {vals[2]:>8}`")
        grid = "```\n" + "\n".join(grid_lines) + "\n```"

        embed = discord.Embed(
            title="Steam Gift Card Price Matrix",
            description=(
                "Automated cross-platform price comparison — updated every 24 hours.\n\n"
                "### Store × Denomination Grid\n" + grid
            ),
            color=0x9147FF,
            timestamp=datetime.now(timezone.utc),
        )

        embed.add_field(
            name="Card Breakdown",
            value=table,
            inline=False,
        )

        insight = await ask_groq(
            self._groq_api_key,
            "You are a sharp AI pricing analyst. Provide one clever, data-driven sentence about the best Steam card deal based on the price matrix. Mention actual store names and dollar amounts.",
            "Analyse these Steam Gift Card prices and identify the best value: "
            + "; ".join(analysis_lines),
        )
        if insight:
            embed.add_field(
                name="AI Price Analysis Insight",
                value=insight,
                inline=False,
            )

        if best_saving[0] > 0:
            embed.set_footer(
                text=f"Best value: {best_saving[1]} — save ${best_saving[0]:.2f} vs face value"
            )

        await channel.send(embed=embed)

    @daily_price_report.before_loop
    async def before_daily_price_report(self) -> None:
        await self.wait_until_ready()
