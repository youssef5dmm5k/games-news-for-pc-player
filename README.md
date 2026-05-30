# NexusGaming Tracker — Autonomous AI Gaming Deals Bot

A single-bot system that fetches **live game deals** from Epic Games and Steam every 24 hours and posts them to a Discord channel with **AI-generated Arabic descriptions** powered by Groq (Llama 3.3 70B).

## Features

- **Epic Games** — Fetches free-game promotions & discounts via the `freeGamesPromotions` GraphQL endpoint
- **Steam** — Fetches live specials via the `featuredcategories` API (`specials` array)
- **AI Descriptions** — Per-game, one-sentence Arabic description generated asynchronously by Groq's `llama-3.3-70b-versatile` model
- **Autonomous** — Runs on a 24-hour `tasks.loop`; fires immediately on startup, then every 24 hours
- **No database, no slash commands** — Zero configuration beyond 3 environment variables

## Architecture

The bot runs as a single `discord.Client` (not `commands.Bot`). On `on_ready`, a `@tasks.loop(hours=24)` begins:

1. **Parallel fetch** — Epic Games and Steam APIs are called concurrently via `asyncio.gather` with `return_exceptions=True`
2. **AI enrichment** — Each deal title is passed to Groq for a concise Arabic description; a fallback sentence is used if the API fails
3. **Format & post** — Deals are assembled into a pure-Markdown message (no embeds) and sent to the target channel, split at Discord's 2000-character limit

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Environment Variables

| Variable       | Description                      |
|----------------|----------------------------------|
| `DISCORD_TOKEN` | Discord bot token               |
| `CHANNEL_ID_1`  | Target channel ID for deals     |
| `GROQ_API_KEY`  | Groq API key for AI descriptions|

Copy `.env.example` to `.env` and fill in your values.

## Output Format

Messages follow this exact structure:

```
🎮 **عروض Epic Games اليوم**
• Game Title
AI-generated Arabic description sentence.
تم تنزيل السعر من 39.99$ إلى 29.99$ وينتهي هذا العرض يوم 15 يونيو.

🎮 **عروض Steam اليوم**
• Another Game
AI-generated Arabic description sentence.
تم تنزيل السعر من 19.99$ إلى 9.99$ وينتهي هذا العرض يوم 22 يونيو.
```

Free-to-keep promotions use a distinct format:

```
• Free Game Title
AI-generated Arabic description sentence.
متوفرة مجاناً الآن وينتهي هذا العرض يوم 15 يونيو.
```

## Deployment

No Dockerfile needed. Start command:

```
python main.py
```

Set the 3 environment variables in your hosting dashboard (Railway, Heroku, etc.).

## Bot Permissions

- **Scope**: `bot`
- **Permissions**: Send Messages, Embed Links, View Channels
- **Intents**: All privileged intents enabled in Discord Developer Portal

## Tech Stack

- Python 3.10+
- discord.py (with `@tasks.loop`)
- aiohttp (transitive dependency of discord.py)
- Groq (Llama 3.3 70B Versatile)
- python-dotenv
