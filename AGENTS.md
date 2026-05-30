# AGENTS.md — OmniBot Hub

## Project structure
- `main.py` — entry point, `load_dotenv()` → `asyncio.gather` to boot both bots
- `config.py` — validates env vars, returns shared `Settings` dataclass
- `bot1/` — **Game News Tracker**:
  - `client.py` — `discord.Client` with 24h `@tasks.loop`
  - `deals.py` — CheapShark API (Steam=1, Epic=25)
  - `groq_client.py` — raw `aiohttp` POST to Groq
  - `formatters.py` — Arabic month names, "مجاناً" for 100% off
- `bot2/` — **Price Comparator**:
  - `client.py` — `commands.Bot` with `/compare` command + UI button
  - `gift_cards.py` — JSON DB loader & search
  - `data/gift_cards.json` — 19 bundled items

## Dual-bot architecture
- Both bots run in one process via `asyncio.gather`
- Each has its own Discord token from `.env` (`DISCORD_TOKEN`, `BOT_TOKEN_2`)
- Separate Gateway connections, separate command trees
- A crash in one bot does NOT stop the other

## Key facts
- **No `groq` SDK** — uses raw `aiohttp` POST to Groq API
- **CheapShark store IDs**: Steam=`1`, Epic Games=`25`
- **Deal cap**: 15 per store (`pageSize` param)
- **100% off → "مجاناً"** instead of `0$`
- **Arabic date formatting**: lookup dict (not `locale`)
- **Groq model**: `llama-3.1-8b-instant` (NOT decommissioned `llama3-8b-8192`)
- **Groq fallback**: `"لعبة مميزة"` after 3 retries
- **Bot 2 JSON DB**: lives at `bot2/data/gift_cards.json` — editable by user

## Commands
- Bot 1: no slash commands, background task only
- Bot 2: `/compare <query>` — searches local JSON, returns sorted embed + buy button
- Run: `python main.py`
- Dependencies: `pip install -r requirements.txt`
- Config: `cp .env.example .env`, fill in secrets

## Gotchas
- **Discord intents** — `discord.Intents.default()`, no privileged intents
- **Channel IDs** — stored as strings in `.env`, cast to `int` by `config.py`
- **First run (Bot 1)**: `@tasks.loop` fires immediately on `on_ready`, not after 24h
- **First run (Bot 2)**: slash commands need `applications.commands` scope in invite URL
- **Bot 2 token**: If `BOT_TOKEN_2` is missing or placeholder, Bot 2 is skipped gracefully (no crash)
- **CheapShark pagination**: API default is 60 results; bot passes `pageSize=15`
