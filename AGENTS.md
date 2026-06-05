# NexusGaming Tracker

## Architecture
- `main.py` — standalone script, everything in one file
- `commands.Bot` (NOT `discord.Client`) — but no slash commands used, only `@tasks.loop`
- `@tasks.loop(hours=24)` starts inside `on_ready()` via `if not loop.is_running()` — no `before_loop` / `wait_until_ready()`
- 3 env vars from `os.getenv()`: `DISCORD_TOKEN`, `CHANNEL_ID_1` (int), `GROQ_API_KEY`
- **No `load_dotenv()`** — Railway sets env natively; run locally with `$env:DISCORD_TOKEN="..."` or `set DISCORD_TOKEN=...`
- Inline `AsyncGroq` at module level (not inside a class)
- Deploy: `worker: python main.py` via Procfile

## Data fetching (sequential, not parallel)
- **Epic**: `freeGamesPromotions?locale=en-US&country=US&allowCountries=US` → `data.Catalog.searchStore.elements[]`
  - Price: Epic returns in cents or dollars inconsistently; code divides by 100 only when `> 100`
  - Expiry: `promotionalOffers[0].promotionalOffers[0].endDate`, falls back to `upcomingPromotionalOffers`
- **Steam**: `featuredcategories/?cc=US&l=english` → `specials.items[]`
  - Price: ALWAYS cents, always divide by 100.0
  - Expiry: `discount_expiration` (unix timestamp); if absent → `"غير محدد"`
- **No error handling** around HTTP calls — if an API fails, the entire loop crashes

## Groq AI
- Model: literally `"llama3"` (not versioned like `llama-3.3-70b-versatile`)
- **No `max_tokens` or `temperature`** — uses Groq defaults
- System prompt: "Write a brief, single-sentence catchy premise/description in natural Arabic for the game title provided. Do not mention any prices, store names, discounts, or dates. Output only the pure Arabic sentence."
- Fallback on failure: `"لعبة مغامرات وتحدي مميزة لأجهزة الكمبيوتر."`

## Output format
- `discord.Embed` per platform:
  - Epic: green sidebar `0x00df6d`, title `✨ عروض Epic Games اليوم`
  - Steam: dark blue sidebar `0x1b2838`, title `🎮 عروض Steam اليوم`
- Inside embed description: `• **{TITLE}** {ai_desc}. تم تنزيل السعر من {orig_price}$ إلى {disc_price}$ وينتهي هذا العرض يوم {date}.`
- **Known bug** (line 174, 187): when `discount_price` is `"مجاناً"`, the hardcoded `$` produces `مجاناً$` — fix would be `{game['discount_price']}` without the trailing `$`
- Dates: ISO format `YYYY-MM-DD`, NOT Arabic months
- `.upper()` applied to all game titles
- No embed splitting at 4096 chars — all deals in one embed

## Gotchas
- **Duplicate imports**: `os`, `asyncio`, `aiohttp`, `discord` each imported twice (lines 1–4 and 5–8) — harmless but ugly
- **No CI, no tests, no lint**
- **No `aiohttp.ClientSession` context manager error handling** — no try/except around `session.get()`
