# NexusAutomation Hub — Multi-Instance Autonomous AI Bots

A production-grade Python framework that runs **two fully autonomous Discord bots** inside a single process using `asyncio.gather`. Zero interactive commands, zero databases — every operation is driven by background task loops with AI-generated content via Groq LLM.

---

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    main.py                        │
│            asyncio.gather (dual loop)             │
├──────────────────────┬───────────────────────────┤
│   Bot 1              │   Bot 2                   │
│   Gaming News        │   Steam Price Monitor     │
│                      │                           │
│  ┌────────────────┐  │  ┌─────────────────────┐  │
│  │ Hardcoded news │  │  │ Hardcoded price     │  │
│  │ templates      │  │  │ matrix (3 cards ×   │  │
│  │ Groq AI TL;DR  │  │  │ 3 stores)           │  │
│  │ 24h loop       │  │  │ Groq AI insight     │  │
│  └────────────────┘  │  │ 24h loop            │  │
│                      │  └─────────────────────┘  │
└──────────────────────┴───────────────────────────┘
```

Both bots authenticate independently with separate Discord tokens, maintain separate Gateway connections, and operate on separate channels — yet they share the same Python process, configuration source, and event loop.

---

## Key Features

### Fully Autonomous (No Interaction Required)
- **No slash commands** — bots post automatically on a 24-hour schedule
- **No databases** — all data is hardcoded, zero external dependencies
- **No user input** — set-and-forget deployment on Railway

### Bot 1 — Autonomous Gaming News Tracker
- Posts a curated **5-story gaming news roundup** every 24 hours
- Each article includes a title, summary, and direct link
- Uses **Groq LLM** to generate a unique, witty AI TL;DR footer
- Beautiful embed with timestamp and branded colour

### Bot 2 — Autonomous Steam Price Monitor
- Posts a **price matrix embed** every 24 hours comparing Steam Gift Cards ($10, $20, $50) across Kinguin, Eneba, and G2A
- Professional monospace grid layout for at-a-glance comparison
- Uses **Groq LLM** to inject a dynamic AI Shopping Insight highlighting the best deal

### AI Integration (Groq)
- Shared `llm.py` module wraps the official `AsyncGroq` SDK
- Both bots call the same helper with different system prompts
- Graceful fallback — if the API call fails, the bot posts without AI content

---

## Setup

### Prerequisites
- Python 3.10 or newer
- Two Discord bot tokens ([Discord Developer Portal](https://discord.com/developers/applications))
- A Groq API key ([Groq Console](https://console.groq.com/keys))
- Two Discord text channels (one per bot)

### Installation

```bash
git clone https://github.com/your-username/nexus-automation-hub.git
cd nexus-automation-hub

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
DISCORD_TOKEN=your_discord_bot_token_here
CHANNEL_ID_1=channel_snowflake_for_bot_1
BOT_TOKEN_2=your_second_bot_token_here
CHANNEL_ID_2=channel_snowflake_for_bot_2
GROQ_API_KEY=your_groq_api_key_here
```

### Invite the Bots

Generate OAuth2 invite URLs for both applications with the `bot` scope and **Send Messages**, **Embed Links**, and **View Channels** permissions.

---

## Usage

```bash
python main.py
```

Both bots connect simultaneously. Each 24-hour loop fires **immediately on `on_ready`**, then every 24 hours thereafter.

---

## Deployment (Railway)

1. Push the repository to GitHub
2. Create a new Railway project from the GitHub repo
3. Set the **five environment variables** in Railway Dashboard
4. Railway detects `requirements.txt` and installs dependencies automatically
5. Start command: `python main.py`

No `Dockerfile` required — Railway's Python builder handles everything.

---

## Project Structure

```
nexus-automation-hub/
├── main.py                  # Entry point — asyncio.gather dual-boot
├── config.py                # Shared Settings dataclass (env vars)
├── llm.py                   # Shared AsyncGroq wrapper
├── bot1/
│   └── client.py            # GameNewsBot — 24h background loop
├── bot2/
│   └── client.py            # SteamPriceBot — 24h background loop
├── .env / .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Performance

Two bot instances in a single process share the Python interpreter, the event loop, and cached modules. Typical RAM usage on Railway (512 MB plan): ~80–110 MB for both bots.

---

## License

MIT
