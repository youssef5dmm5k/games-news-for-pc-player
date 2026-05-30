import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bot1_token: str
    bot2_token: str
    channel_id_1: int
    channel_id_2: int
    groq_api_key: str


def validate_settings() -> Settings:
    def get_int(key: str) -> int:
        try:
            return int(os.getenv(key, "0"))
        except ValueError:
            return 0

    return Settings(
        bot1_token=os.getenv("DISCORD_TOKEN", ""),
        bot2_token=os.getenv("BOT_TOKEN_2", ""),
        channel_id_1=get_int("CHANNEL_ID_1"),
        channel_id_2=get_int("CHANNEL_ID_2"),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
    )
