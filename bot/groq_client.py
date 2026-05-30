import asyncio
import logging

import aiohttp

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"
MAX_RETRIES = 3
FALLBACK_PHRASE = "لعبة مميزة"

logger = logging.getLogger("game_deals_bot.groq")


async def generate_description(game_name: str, api_key: str) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = (
        f"أعطني جملة وصفية قصيرة وجذابة من 3 إلى 6 كلمات باللغة العربية "
        f"عن لعبة الفيديو \"{game_name}\". اذكر موضوع اللعبة أو الاستوديو "
        f"إذا كان مشهوراً. لا تذكر اسم اللعبة في الوصف نفسه. أرسل الجملة فقط."
    )

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 50,
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    API_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status == 429:
                        logger.warning("Groq rate limited — retry %d/%d", attempt, MAX_RETRIES)
                        await asyncio.sleep(2 ** attempt)
                        continue

                    if not resp.ok:
                        error_text = await resp.text()
                        logger.error("Groq HTTP %d: %s", resp.status, error_text)
                        return FALLBACK_PHRASE

                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    return content if content else FALLBACK_PHRASE

        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, IndexError) as exc:
            logger.warning("Groq attempt %d/%d failed: %s", attempt, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)

    return FALLBACK_PHRASE
