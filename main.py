import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

import aiohttp
import discord
from discord.ext import tasks
from groq import AsyncGroq

logger = logging.getLogger("game_deals_bot.client")

EPIC_URL = (
    "https://store-site-backend-static.ak.epicgames.com/"
    "freeGamesPromotions?locale=en-US&country=US"
)
STEAM_URL = "https://store.steampowered.com/api/featuredcategories/?l=english"
FALLBACK_DESC = "\u0644\u0639\u0628\u0629 \u0645\u063a\u0627\u0645\u0631\u0627\u062a \u0648\u062a\u062d\u062f\u064a \u0645\u0645\u064a\u0632\u0629 \u0644\u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0643\u0645\u0628\u064a\u0648\u062a\u0631."
TIMEOUT = 15

ARABIC_MONTHS = {
    1: "\u064a\u0646\u0627\u064a\u0631", 2: "\u0641\u0628\u0631\u0627\u064a\u0631",
    3: "\u0645\u0627\u0631\u0633", 4: "\u0623\u0628\u0631\u064a\u0644",
    5: "\u0645\u0627\u064a\u0648", 6: "\u064a\u0648\u0646\u064a\u0648",
    7: "\u064a\u0648\u0644\u064a\u0648", 8: "\u0623\u063a\u0633\u0637\u0633",
    9: "\u0633\u0628\u062a\u0645\u0628\u0631", 10: "\u0623\u0643\u062a\u0648\u0628\u0631",
    11: "\u0646\u0648\u0641\u0645\u0628\u0631", 12: "\u062f\u064a\u0633\u0645\u0628\u0631",
}


def _cents_to_dollars(cents: int) -> float:
    return round(cents / 100, 2)


def _format_ar_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return f"{dt.day} {ARABIC_MONTHS[dt.month]}"
    except Exception:
        return iso_str


class GameDealsBot(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())
        self.channel_id = int(os.getenv("CHANNEL_ID_1", "0"))
        self.groq_key = os.getenv("GROQ_API_KEY", "")

    async def on_ready(self) -> None:
        print(f"[+] ONLINE \u2014 {self.user}", flush=True)
        self.daily_deals.start()

    @tasks.loop(hours=24)
    async def daily_deals(self) -> None:
        channel = self.get_channel(self.channel_id)
        if channel is None:
            logger.error("Channel %s not found", self.channel_id)
            return

        epic, steam = await asyncio.gather(
            self._fetch_epic(), self._fetch_steam(), return_exceptions=True
        )

        if isinstance(epic, Exception):
            logger.error("Epic fetch error: %s", epic)
            epic = []
        if isinstance(steam, Exception):
            logger.error("Steam fetch error: %s", steam)
            steam = []

        for store, deals in [("Epic Games", epic), ("Steam", steam)]:
            if deals:
                await self._post_deals(channel, store, deals)
            else:
                logger.warning("No %s deals fetched \u2014 skipping", store)

    async def _fetch_epic(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(EPIC_URL, timeout=TIMEOUT) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        elements = (
            data.get("data", {})
            .get("Catalog", {})
            .get("searchStore", {})
            .get("elements", [])
        )

        deals = []
        for el in elements:
            price_info = el.get("price") or {}
            total = price_info.get("totalPrice") or {}
            orig = total.get("originalPrice", 0)
            disc = total.get("discountPrice", 0)
            promo = el.get("promotions")
            has_active_promo = bool(promo and promo.get("promotionalOffers"))

            if orig == disc and not has_active_promo:
                continue

            end_date = None
            if promo:
                for bundle in promo.get("promotionalOffers", []):
                    for offer in bundle.get("promotionalOffers", []):
                        if offer.get("endDate"):
                            end_date = offer["endDate"]

            if orig == 0 and disc == 0:
                deals.append({
                    "title": el.get("title", "Unknown"),
                    "original": -1,
                    "sale": 0.0,
                    "ends": _format_ar_date(end_date) if end_date else None,
                })
            else:
                deals.append({
                    "title": el.get("title", "Unknown"),
                    "original": _cents_to_dollars(orig),
                    "sale": _cents_to_dollars(disc),
                    "ends": _format_ar_date(end_date) if end_date else None,
                })
        return deals

    async def _fetch_steam(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(STEAM_URL, timeout=TIMEOUT) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        items = data.get("specials", {}).get("items", [])
        default_end = datetime.now(timezone.utc) + timedelta(days=7)

        deals = []
        for item in items:
            name = item.get("name")
            if not name:
                continue
            orig_c = item.get("original_price", 0)
            final_c = item.get("final_price", 0)
            if orig_c == 0 or orig_c == final_c:
                continue
            deals.append({
                "title": name,
                "original": _cents_to_dollars(orig_c),
                "sale": _cents_to_dollars(final_c),
                "ends": _format_ar_date(default_end.isoformat()),
            })
        return deals

    async def _get_desc(self, title: str) -> str:
        try:
            client = AsyncGroq(api_key=self.groq_key)
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Write a brief, single-sentence catchy description "
                            "in natural Arabic for the game title provided. "
                            "Do not mention any prices, discounts, or dates. "
                            "Output only the pure Arabic sentence."
                        ),
                    },
                    {
                        "role": "user",
                        "content": title,
                    },
                ],
                max_tokens=60,
                temperature=0.7,
            )
            result = response.choices[0].message.content.strip()
            return result if result else FALLBACK_DESC
        except Exception:
            return FALLBACK_DESC

    async def _post_deals(self, channel, store: str, deals: list[dict]) -> None:
        lines = [f"\u2728 **\u0639\u0631\u0648\u0636 {store} \u0627\u0644\u064a\u0648\u0645**"]

        for d in deals:
            desc = await self._get_desc(d["title"])
            ends_str = f"\u064a\u0648\u0645 {d['ends']}" if d["ends"] else "\u0642\u0631\u064a\u0628\u0627\u064b"

            if d["original"] == -1:
                price_line = f"\u0645\u062a\u0648\u0641\u0631\u0629 \u0645\u062c\u0627\u0646\u0627\u064b \u0627\u0644\u0622\u0646 \u0648\u064a\u0646\u062a\u0647\u064a \u0647\u0630\u0627 \u0627\u0644\u0639\u0631\u0636 {ends_str}."
            else:
                sale_str = "\u0645\u062c\u0627\u0646\u0627\u064b" if d["sale"] == 0 else f"{d['sale']:.2f}$"
                price_line = f"\u062a\u0645 \u062a\u0646\u0632\u064a\u0644 \u0627\u0644\u0633\u0639\u0631 \u0645\u0646 {d['original']:.2f}$ \u0625\u0644\u0649 {sale_str} \u0648\u064a\u0646\u062a\u0647\u064a \u0647\u0630\u0627 \u0627\u0644\u0639\u0631\u0636 {ends_str}."

            lines.append(f"\u2022 **{d['title']}** {desc} {price_line}")

        full = lines[0] + "\n\n" + "\n".join(lines[1:])
        if len(full) <= 2000:
            await channel.send(full)
            return

        header = lines[0]
        await channel.send(header)
        chunk = []
        size = 0
        for line in lines[1:]:
            l = len(line)
            if size + l > 1900:
                await channel.send("\n".join(chunk))
                chunk = [line]
                size = l
            else:
                chunk.append(line)
                size += l
        if chunk:
            await channel.send("\n".join(chunk))

    @daily_deals.before_loop
    async def before_daily_deals(self) -> None:
        await self.wait_until_ready()


if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set")

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)-7s] %(name)s: %(message)s",
    )

    bot = GameDealsBot()
    bot.run(token)
