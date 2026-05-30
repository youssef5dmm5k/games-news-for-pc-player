# AGENTS.md — NexusAutomation Hub

## Architecture
- `main.py` — entrypoint, `asyncio.gather` launches both bots concurrently
- Both bots are `discord.Client` (NOT `commands.Bot`) — no slash commands, no `tree.sync()`, no `setup_hook`
- Both use `@tasks.loop(hours=24)` — fires **immediately** on `on_ready`, then every 24h
- `config.py` — uses `os.getenv()` (returns `""`/`0` for missing vars, never crashes)
- `llm.py` — shared `AsyncGroq` wrapper. Named `llm.py` (NOT `groq.py`) because the pip package `groq` would shadow it and cause a circular import

## Data
- **Bot 1** (`bot1/client.py`): hardcoded `NEWS_TEMPLATES` list — 5 articles
- **Bot 2** (`bot2/client.py`): hardcoded `STEAM_CARDS` dict — 3 denominations × 3 stores
- No databases, no JSON files, no external APIs (other than Groq)

## Environment vars (all read by `config.py`)
```
DISCORD_TOKEN     Bot 1 token
BOT_TOKEN_2       Bot 2 token
CHANNEL_ID_1      Target channel for Bot 1 (int)
CHANNEL_ID_2      Target channel for Bot 2 (int)
GROQ_API_KEY      Groq LLM key
```
Missing vars → bot is silently skipped, no crash.

## Run
```bash
pip install -r requirements.txt
python main.py
```

## Gotchas
- **Intents**: `discord.Intents.all()` — must be enabled in Discord Developer Portal
- **Bot invite**: only needs `bot` scope + Send Messages / Embed Links / View Channels. No `applications.commands` scope needed
- **Railway**: No Dockerfile needed. Start command is `python main.py`
- **Groq model**: `llama-3.1-8b-instant` in `llm.py:12`
- **`llm.py` naming**: MUST stay `llm.py` — renaming to `groq.py` breaks imports
- **First loop**: fires on `on_ready`, not after 24h. No `wait_until_ready` needed (handled by `before_loop`)
