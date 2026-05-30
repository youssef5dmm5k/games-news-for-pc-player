import json
import asyncio
import logging

import aiohttp

STORE_IDS = {
    "Steam": 1,
    "Epic Games": 25,
}

DEFAULT_PAGE_SIZE = 15
MAX_RETRIES = 3

logger = logging.getLogger("game_deals_bot.deals")


async def fetch_deals(store_id: int) -> list[dict]:
    url = "https://www.cheapshark.com/api/1.0/deals"
    params = {"storeID": store_id, "pageSize": DEFAULT_PAGE_SIZE, "onSale": "true"}

    async with aiohttp.ClientSession() as session:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 429:
                        retry_after = int(resp.headers.get("Retry-After", 60))
                        logger.warning("CheapShark rate limited — waiting %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        continue

                    resp.raise_for_status()
                    data = await resp.json()
                    return data if isinstance(data, list) else []

            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as exc:
                logger.warning("CheapShark attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(2 ** attempt)

        return []
