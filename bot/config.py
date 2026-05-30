import os
import sys
from dataclasses import dataclass


REQUIRED_ENV_VARS = {
    "DISCORD_TOKEN": "Discord bot token",
    "GROQ_API_KEY": "Groq API key",
    "CHANNEL_ID": "Discord channel snowflake for deal messages",
}


@dataclass(frozen=True)
class Settings:
    token: str
    groq_api_key: str
    channel_id: int


def validate_settings() -> Settings:
    missing = [k for k, desc in REQUIRED_ENV_VARS.items() if not os.getenv(k)]

    if missing:
        print("Missing required environment variables:", file=sys.stderr)
        for key in missing:
            print(f"  {key}  — {REQUIRED_ENV_VARS[key]}", file=sys.stderr)
        print("\nCreate a .env file in the project root with these values.", file=sys.stderr)
        sys.exit(1)

    token = os.environ["DISCORD_TOKEN"]
    groq_api_key = os.environ["GROQ_API_KEY"]

    try:
        channel_id = int(os.environ["CHANNEL_ID"])
    except ValueError:
        print("CHANNEL_ID must be a valid integer (Discord snowflake).", file=sys.stderr)
        sys.exit(1)

    return Settings(token=token, groq_api_key=groq_api_key, channel_id=channel_id)
