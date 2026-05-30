# NexusGaming Tracker

## Architecture
- `main.py` — standalone script with everything in one file
- Single `discord.Client` (NOT `commands.Bot`) — no slash commands, no `tree.sync()`, no `setup_hook`
- `@tasks.loop(hours=24)` fires **immediately** on `on_ready`, then every 24h
- 3 env vars: `DISCORD_TOKEN`, `CHANNEL_ID_1`, `GROQ_API_KEY`
- `llm.py` — `AsyncGroq` wrapper. Named `llm.py` (NOT `groq.py`) because pip package `groq` shadows it

## Data fetching
- Epic Games: `freeGamesPromotions` → `data.Catalog.searchStore.elements[]`
- Steam: `featuredcategories` → `specials.items[]` — no `endDate` from API, hardcoded to `now + 7 days`
- Prices in cents → `_cents_to_dollars()`
- Filter: skips `origPrice == discPrice` **unless** active `promotionalOffers` exist (free-to-keep promos)
- Both API calls via `asyncio.gather` with `return_exceptions=True`
- `_free` flag = `orig == 0 and disc == 0` → uses "متوفرة مجاناً الآن" text; distinct from `sale == 0` which uses "مجاناً"

## Output format
- Plain markdown message (no embed)
- Format: `🎮 **عروض {store} اليوم**` then per deal `• **{TITLE.upper()}**\n  {desc}.\n  {price_line}.`
- Desc punctuation: Groq output is stripped of `.`/`!` then format re-adds `.` — prevents double punctuation
- Prices: `39.99$` (`:.2f$`)
- Arabic dates via `_format_ar_date()` → `ARABIC_MONTHS` dict
- Messages auto-split at 2000-char Discord limit (header sent first, then chunks)

## Gotchas
- **`llm.py` naming**: MUST stay `llm.py` — renaming to `groq.py` breaks imports
- **`aiohttp`**: not in `requirements.txt`, available as transitive dep of `discord.py` — do not add it manually
- **First loop**: fires on `on_ready` (not after 24h), uses `before_loop` with `wait_until_ready`
- **No tests, no lint, no CI** in this repo
- **`load_dotenv()`**: runs at entrypoint for local `.env` support (main.py:204)
- **Groq model**: `llama-3.1-8b-instant` in `llm.py:12`, `max_tokens=60` in `_get_desc`
## bot form


- NEW — for paid games with known orig price:
f"• {deal['title']}\n"
f"{desc}\n"
f"تم تنزيل السعر من {deal['original']:.2f}$ إلى {sale_str} وينتهي هذا العرض {ends_str}.\n"

- NEW — for free games with unknown orig (original == -1):
f"• {deal['title']}\n"
f"{desc}\n"
f"متوفرة مجاناً الآن وينتهي هذا العرض {ends_str}.\n"