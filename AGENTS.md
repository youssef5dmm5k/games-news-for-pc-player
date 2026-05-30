# AGENTS.md — Discord Game Deals Bot

## Project structure
- `main.py` — entry point, calls `load_dotenv()` then boots `GameDealsBot`
- `bot/` — package:
  - `config.py` — reads env vars (no config.json), validates, returns `Settings`
  - `client.py` — `discord.Client` subclass with a 24h `@tasks.loop`
  - `deals.py` — CheapShark API call (store IDs: Steam=1, Epic=25)
  - `groq_client.py` — raw `aiohttp` POST to Groq API
  - `formatters.py` — Arabic month names, price → "مجاناً" for 100% off
- `config.json` — **DEPRECATED**, use `.env` instead
- `.env` / `.env.example` — secrets via `python-dotenv`

## Key architecture facts
- **No `groq` PyPI package** — uses raw `aiohttp` POST to `https://api.groq.com/openai/v1/chat/completions`
- **CheapShark store IDs**: Steam=`1`, Epic Games=`25`
- **Deal cap**: 15 per store (`pageSize` param)
- **100% off → "مجاناً"** instead of `0$`
- **Arabic date formatting**: ISO date → Arabic month name via a lookup dict (not `locale`)

## Commands
- No prefix/slash commands; background task sender only
- Run: `python main.py`
- Dependencies: `pip install -r requirements.txt`
- Config: `cp .env.example .env`, fill in secrets

## Gotchas
- **Discord intents** — `discord.Intents.default()`, no privileged intents
- **Groq model**: `llama-3.1-8b-instant` (NOT decommissioned `llama3-8b-8192`)
- **Groq fallback**: `"لعبة مميزة"` if API call fails after 3 retries
- **First run**: `@tasks.loop` fires immediately on `on_ready`, not after 24h
- **Channel ID**: stored as string in `.env`, validated + cast to `int` by `config.py`
- **CheapShark pagination**: API default is 60 results; bot passes `pageSize=15`
- **`config.json`**: If present, it is ignored. Remove it to avoid confusion.
- **`AGENTS.md`** lives at repo root — update `opencode.json` if moved.
