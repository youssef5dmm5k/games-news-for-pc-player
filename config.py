import os
import sys
from dataclasses import dataclass


REQUIRED_ENV = {
    "BOT_TOKEN_1": "Bot 1 (Game News Tracker) token",
    "BOT_TOKEN_2": "Bot 2 (Price Comparator) token",
    "CHANNEL_ID_1": "Channel for Bot 1 daily deal posts",
    "CHANNEL_ID_2": "Channel for Bot 2 slash command responses",
    "GROQ_API_KEY": "Groq API key for Arabic descriptions (Bot 1)",
}


@dataclass(frozen=True)
class Settings:
    bot1_token: str
    bot2_token: str
    channel_id_1: int
    channel_id_2: int
    groq_api_key: str


def validate_settings() -> Settings:
    missing = [k for k in REQUIRED_ENV if not os.getenv(k)]

    if missing:
        print("Missing required environment variables:", file=sys.stderr)
        for k in missing:
            print(f"  {k}  — {REQUIRED_ENV[k]}", file=sys.stderr)
        print("\nCreate a .env file in the project root with these values.", file=sys.stderr)
        sys.exit(1)

    try:
        return Settings(
            bot1_token=os.environ["BOT_TOKEN_1"],
            bot2_token=os.environ["BOT_TOKEN_2"],
            channel_id_1=int(os.environ["CHANNEL_ID_1"]),
            channel_id_2=int(os.environ["CHANNEL_ID_2"]),
            groq_api_key=os.environ["GROQ_API_KEY"],
        )
    except ValueError:
        print("CHANNEL_ID_1 and CHANNEL_ID_2 must be valid integers.", file=sys.stderr)
        sys.exit(1)
