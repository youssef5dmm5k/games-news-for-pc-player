# NexusGaming Tracker

## Architecture
- `main.py` — standalone script with everything in one file
- Single `discord.Client` (NOT `commands.Bot`) — no slash commands, no `tree.sync()`, no `setup_hook`
- `@tasks.loop(hours=24)` fires **immediately** on `on_ready`, then every 24h
- 3 env vars: `DISCORD_TOKEN`, `CHANNEL_ID_1`, `GROQ_API_KEY`
- Inline `AsyncGroq` in `main.py` (not a separate module) — named `main.py` to avoid `groq` pip package shadowing

## Data fetching
- Epic Games: `freeGamesPromotions` → `data.Catalog.searchStore.elements[]`
- Steam: `featuredcategories` → `specials.items[]` — no `endDate` from API, hardcoded to `now + 7 days`
- Prices in cents → `_cents_to_dollars()`
- Filter: skips `origPrice == discPrice` **unless** active `promotionalOffers` exist (free-to-keep promos)
- Both API calls via `asyncio.gather` with `return_exceptions=True`
- `_free` flag = `orig == 0 and disc == 0` → uses "متوفرة مجاناً الآن" text; distinct from `sale == 0` which uses "مجاناً"

## Output format
- Plain markdown message (no embed)
- Header: `✨ **عروض {store} اليوم**` then blank line
- Per deal: `• **{title}** {desc} {price_line}` (single line, no inner line breaks)
- Price lines:
  - `original == -1` → `متوفرة مجاناً الآن وينتهي هذا العرض {ends_str}.`
  - `original > 0, sale == 0` → `تم تنزيل السعر من {orig}$ إلى مجاناً وينتهي هذا العرض {ends_str}.`
  - `original > 0, sale > 0` → `تم تنزيل السعر من {orig}$ إلى {sale}$ وينتهي هذا العرض {ends_str}.`
- Prices: `39.99$` (`:.2f$`), sale == 0 → `مجاناً`
- Arabic dates via `_format_ar_date()` → `ARABIC_MONTHS` dict
- Messages auto-split at 2000-char Discord limit (header sent first, then chunks)
- Join separator between deals: `\n` (no blank lines between deals)

## Gotchas
- **`aiohttp`**: not in `requirements.txt`, available as transitive dep of `discord.py` — do not add it manually
- **First loop**: fires on `on_ready` (not after 24h), uses `before_loop` with `wait_until_ready`
- **No tests, no lint, no CI** in this repo
- **`load_dotenv()`**: runs at entrypoint for local `.env` support (main.py:204)
- **Groq model**: `llama-3.3-70b-versatile` in `main.py:158`, `max_tokens=60` in `_get_desc`
- **Groq import**: `from groq import AsyncGroq` in `main.py:10`

## Bot form — exact message layout

```
✨ **عروض Epic Games اليوم**

• **Phonopolis** لعبة رائعة من الاستوديو "ستيموفاركس" تعيد إحياء الذكريات الصوتية. تم تنزيل السعر من 35.98$ إلى 20.38$ وينتهي هذا العرض يوم 6 يونيو.
• **Suicide Squad: Kill the Justice League** لعبة بطل خارق من استوديو روكستيد. تم تنزيل السعر من 69.99$ إلى 3.49$ وينتهي هذا العرض يوم 1 يونيو.
```

- Header: `✨ **عروض {store} اليوم**` followed by blank line
- Per deal block: `• **{title}** {desc} {price_line}`
- `{desc}` ends with period (from AI) + space + `{price_line}` (ends with period) — all on one line, no inner line breaks
- Join between deals: `\n` (no blank lines between deals — all deals one after another)
- Free-to-keep (original == -1): `price_line` = `متوفرة مجاناً الآن وينتهي هذا العرض {ends_str}.`
- Paid on sale (original > 0, sale == 0): `price_line` = `تم تنزيل السعر من {orig}$ إلى مجاناً وينتهي هذا العرض {ends_str}.`
- Paid on sale (original > 0, sale > 0): `price_line` = `تم تنزيل السعر من {orig}$ إلى {sale}$ وينتهي هذا العرض {ends_str}.`
- No emoji decorations on price lines, no strikethrough, no bold on prices