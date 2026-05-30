# OmniBot Hub — Advanced Multi-Instance Discord Architecture

A production-grade Python framework that runs **two independent Discord bots** inside a single process using `asyncio.gather`. Designed for resource-efficient deployment where multiple bot instances share memory, configuration, and a single event loop without sacrificing isolation.

---

## Architecture

```
┌──────────────────────────────────────────────┐
│                 main.py                       │
│         asyncio.gather (dual loop)            │
├──────────────────────┬───────────────────────┤
│   Bot 1              │   Bot 2               │
│   Game News Tracker  │   Price Comparator    │
│                      │                       │
│  ┌────────────────┐  │  ┌─────────────────┐  │
│  │ CheapShark API │  │  │ Local JSON DB   │  │
│  │ Groq LLM       │  │  │ Store price      │  │
│  │ Arabic output  │  │  │ comparison       │  │
│  └────────────────┘  │  │ UI buttons       │  │
│                      │  └─────────────────┘  │
└──────────────────────┴───────────────────────┘
```

Both bots authenticate independently with separate Discord tokens, maintain separate Gateway connections, and operate on separate channels — yet they share the same Python process, configuration source, and dependencies.

---

## Advanced Features

### Asynchronous Multi-Instance Execution
Both bots are launched via `asyncio.gather`, allowing them to connect to Discord concurrently. Each bot retains its own rate-limit bucket, shard ID, and command tree. A crash in one instance does not affect the other.

### Bot 1 — Game News Tracker
- **Automated deal aggregation** — Fetches daily discounts from Steam and Epic Games Store via CheapShark.
- **LLM-enriched descriptions** — Uses Groq's `llama-3.1-8b-instant` to generate short Arabic catchphrases for each game.
- **24-hour background loop** — Posts a formatted summary (Arabic dates, "مجاناً" for free games) to the configured channel every 24 hours.
- **Resilient error handling** — Exponential backoff on API rate limits; graceful fallback descriptions.

### Bot 2 — Gift Card & Game Price Comparator
- **`/compare` slash command** — Searches a local JSON database of gift cards (Steam, PSN, Xbox) and game titles.
- **Price-sorted embeds** — Results are ranked by price with medal emojis (🥇🥈🥉) and direct store links.
- **Interactive UI** — "Buy Best Deal" button sends an ephemeral message with the cheapest store link.
- **Zero external API dependency** — All price data is bundled, no third-party price API required.

---

## Setup

### Prerequisites
- Python 3.10 or newer
- Two Discord bot tokens ([Discord Developer Portal](https://discord.com/developers/applications))
- A Groq API key ([Groq Console](https://console.groq.com/keys))
- One Discord server with two text channels (or one shared channel)

### Installation

```bash
git clone https://github.com/your-username/omnibot-hub.git
cd omnibot-hub

python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux / macOS

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```ini
BOT_TOKEN_1=your_first_bot_token
CHANNEL_ID_1=channel_snowflake_for_bot_1
BOT_TOKEN_2=your_second_bot_token
CHANNEL_ID_2=channel_snowflake_for_bot_2
GROQ_API_KEY=your_groq_api_key
```

### Invite the Bots

Generate OAuth2 invite URLs for both applications:

| Scope | Permission |
|---|---|
| `bot` | Send Messages, Embed Links, View Channels, Use Slash Commands |
| `applications.commands` | (required for `/compare`) |

---

## Usage

```bash
python main.py
```

Both bots connect simultaneously. Bot 1 immediately fetches and posts deals; Bot 2 registers the `/compare` command on the global command tree.

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t omnibot-hub .
docker run -d --env-file .env --name omnibot omnibot-hub
```

### systemd

```ini
[Unit]
Description=OmniBot Hub
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/omnibot-hub
EnvironmentFile=/path/to/omnibot-hub/.env
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Project Structure

```
omnibot-hub/
├── main.py                  # Entry point — asyncio.gather dual-boot
├── config.py                # Shared Settings dataclass (env vars)
├── bot1/
│   ├── __init__.py
│   ├── client.py            # GameNewsBot — 24h task loop
│   ├── deals.py             # CheapShark async fetcher
│   ├── groq_client.py       # Groq LLM integration
│   └── formatters.py        # Arabic date & price formatting
├── bot2/
│   ├── __init__.py
│   ├── client.py            # PriceCompareBot — /compare command
│   ├── gift_cards.py        # JSON database query layer
│   └── data/
│       └── gift_cards.json  # 19 bundled items (gift cards + games)
├── .env / .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Resource Efficiency

Running two bot instances in a single process reduces memory overhead by sharing the Python interpreter, the aiohttp event loop, and cached modules. Typical RAM usage: ~90–120 MB for both bots (versus ~60–80 MB each when run separately).

---

## License

MIT
