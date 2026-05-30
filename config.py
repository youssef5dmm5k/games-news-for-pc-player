import os
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot1_token: str
    bot2_token: str
    channel_id_1: int
    channel_id_2: int
    groq_api_key: str


def validate_settings() -> Settings:
    warnings: list[str] = []

    bot1_token = os.getenv("BOT_TOKEN_1", "")
    if not bot1_token:
        warnings.append("BOT_TOKEN_1 is missing — Bot 1 (News Tracker) will not start")

    bot2_token = os.getenv("BOT_TOKEN_2", "")
    groq_api_key = os.getenv("GROQ_API_KEY", "")
    if not groq_api_key:
        warnings.append("GROQ_API_KEY is missing — Bot 1 Arabic descriptions will fail")

    try:
        channel_id_1 = int(os.getenv("CHANNEL_ID_1", "0"))
    except ValueError:
        channel_id_1 = 0
        warnings.append("CHANNEL_ID_1 is not a valid integer")

    try:
        channel_id_2 = int(os.getenv("CHANNEL_ID_2", "0"))
    except ValueError:
        channel_id_2 = 0
        warnings.append("CHANNEL_ID_2 is not a valid integer")

    if warnings:
        print("Warnings during configuration:", file=sys.stderr)
        for w in warnings:
            print(f"  ⚠ {w}", file=sys.stderr)

    return Settings(
        bot1_token=bot1_token,
        bot2_token=bot2_token,
        channel_id_1=channel_id_1,
        channel_id_2=channel_id_2,
        groq_api_key=groq_api_key,
    )
