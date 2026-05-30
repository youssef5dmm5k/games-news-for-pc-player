import logging

from groq import AsyncGroq

logger = logging.getLogger("groq")


async def ask_groq(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    model: str = "llama-3.1-8b-instant",
    max_tokens: int = 100,
) -> str:
    client = AsyncGroq(api_key=api_key)
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("Groq API call failed: %s", e)
        return ""
