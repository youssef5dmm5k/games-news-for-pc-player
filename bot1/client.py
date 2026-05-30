import asyncio
import logging
from datetime import datetime, timezone, timedelta

import aiohttp
import discord
from discord.ext import tasks

from config import Settings
from llm import ask_groq

logger = logging.getLogger("bot1.news")

EPIC_URL = (
    "https://store-site-backend-static.ak.epicgames.com/"
    "freeGamesPromotions?locale=en-US&country=US"
)
STEAM_URL = (
    "https://store.steampowered.com/api/featuredcategories/?l=english"
)
FALLBACK_DESC = "\u0644\u0639\u0628\u0629 \u0645\u063a\u0627\u0645\u0631\u0627\u062a \u0648\u062a\u062d\u062f\u064a \u0645\u0645\u064a\u0632\u0629 \u0644\u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0643\u0645\u0628\u064a\u0648\u062a\u0631."
ARABIC_MONTHS = {
    1: "\u064a\u0646\u0627\u064a\u0631", 2: "\u0641\u0628\u0631\u0627\u064a\u0631",
    3: "\u0645\u0627\u0631\u0633", 4: "\u0623\u0628\u0631\u064a\u0644",
    5: "\u0645\u0627\u064a\u0648", 6: "\u064a\u0648\u0646\u064a\u0648",
    7: "\u064a\u0648\u0644\u064a\u0648", 8: "\u0623\u063a\u0633\u0637\u0633",
    9: "\u0633\u0628\u062a\u0645\u0628\u0631", 10: "\u0623\u0643\u062a\u0648\u0628\u0631",
    11: "\u0646\u0648\u0641\u0645\u0628\u0631", 12: "\u062f\u064a\u0633\u0645\u0628\u0631",
}
STEAM_TIMEOUT = 15
EPIC_TIMEOUT = 15


def _cents_to_dollars(cents: int) -> float:
    return round(cents / 100, 2)


def _format_ar_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        day = dt.day
        month = ARABIC_MONTHS[dt.month]
        return f"{day} {month}"
    except Exception:
        return iso_str


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

        epic_result, steam_result = await asyncio.gather(
            self._fetch_epic_deals(),
            self._fetch_steam_deals(),
            return_exceptions=True,
        )

        if isinstance(epic_result, Exception):
            logger.error("Epic fetch failed: %s", epic_result)
            epic_result = []
        if isinstance(steam_result, Exception):
            logger.error("Steam fetch failed: %s", steam_result)
            steam_result = []

        print(f"[Bot1] Fetched {len(epic_result)} Epic deals, {len(steam_result)} Steam deals", flush=True)

        if epic_result:
            await self._post_deals(channel, "Epic Games", epic_result)
        else:
            logger.error("No Epic Games deals fetched \u2014 skipping")

        if steam_result:
            await self._post_deals(channel, "Steam", steam_result)
        else:
            logger.error("No Steam deals fetched \u2014 skipping")

    async def _fetch_epic_deals(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(EPIC_URL, timeout=EPIC_TIMEOUT) as resp:
                if resp.status != 200:
                    logger.error("Epic API returned status %s", resp.status)
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
            price = el.get("price") or {}
            total = price.get("totalPrice") or {}
            orig = total.get("originalPrice", 0)
            disc = total.get("discountPrice", 0)
            promo = el.get("promotions")
            is_free_promo = bool(promo and promo.get("promotionalOffers"))
            if orig == disc and not is_free_promo:
                continue
            end_date = None
            if promo:
                offers = promo.get("promotionalOffers", [])
                if offers:
                    for bundle in offers:
                        inner = bundle.get("promotionalOffers", [])
                        for offer in inner:
                            ed = offer.get("endDate")
                            if ed:
                                end_date = ed
            title = el.get("title", "Unknown Title")
            has_price = orig > 0
            deals.append({
                "title": title,
                "original": _cents_to_dollars(orig) if has_price else None,
                "sale": _cents_to_dollars(disc),
                "ends": _format_ar_date(end_date) if end_date else None,
                "_free": not has_price and disc == 0,
            })
        return deals

    async def _fetch_steam_deals(self) -> list[dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(STEAM_URL, timeout=STEAM_TIMEOUT) as resp:
                if resp.status != 200:
                    logger.error("Steam API returned status %s", resp.status)
                    return []
                data = await resp.json()

        items = data.get("specials", {}).get("items", [])
        now = datetime.now(timezone.utc)
        default_end = now + timedelta(days=7)

        deals = []
        for item in items:
            name = item.get("name")
            if not name:
                continue
            orig_cents = item.get("original_price", 0)
            final_cents = item.get("final_price", 0)
            if orig_cents == 0 or orig_cents == final_cents:
                continue
            deals.append({
                "title": name,
                "original": _cents_to_dollars(orig_cents),
                "sale": _cents_to_dollars(final_cents),
                "ends": _format_ar_date(default_end.isoformat()),
            })
        return deals

    async def _post_deals(self, channel, store: str, deals: list[dict]) -> None:
        lines = [f"\u2728 **\u0639\u0631\u0648\u0636 {store} \u0627\u0644\u064a\u0648\u0645**\n"]
        for deal in deals:
            desc = await self._get_ar_desc(deal["title"])
            ends_str = (
                f"\u064a\u0648\u0645 {deal['ends']}"
                if deal["ends"]
                else "\u0642\u0631\u064a\u0628\u0627\u064b"
            )
            if deal.get("_free"):
                price_line = f"\u0645\u062a\u0648\u0641\u0631\u0629 \u0645\u062c\u0627\u0646\u0627\u064b \u0627\u0644\u0622\u0646 \u0648\u064a\u0646\u062a\u0647\u064a \u0647\u0630\u0627 \u0627\u0644\u0639\u0631\u0636 {ends_str}."
            else:
                sale_str = "\u0645\u062c\u0627\u0646\u0627\u064b" if deal["sale"] == 0 else f"{deal['sale']:.2f}$"
                price_line = f"\u062a\u0645 \u062a\u0646\u0632\u064a\u0644 \u0627\u0644\u0633\u0639\u0631 \u0645\u0646 {deal['original']:.2f}$ \u0625\u0644\u0649 {sale_str} \u0648\u064a\u0646\u062a\u0647\u064a \u0647\u0630\u0627 \u0627\u0644\u0639\u0631\u0636 {ends_str}."
            lines.append(
                f"\u2022 {deal['title']}\n"
                f"{desc}\n"
                f"{price_line}\n"
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
