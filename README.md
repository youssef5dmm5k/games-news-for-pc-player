# NexusGaming OmniHub — Advanced Multi-Instance Autonomous AI Platform

A production-grade Python framework that orchestrates **two fully autonomous Discord bots** within a single process using `asyncio.gather`. Zero interactive commands. Zero databases. Every operation runs on scheduled background loops with AI-generated content via Groq LLM. Designed for set-and-forget deployment on Railway.

---

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                      main.py                            │
│              asyncio.gather (dual loop)                 │
├─────────────────────────┬──────────────────────────────┤
│     Bot 1               │     Bot 2                    │
│     Gaming News Hub     │     Steam Price Monitor      │
│                         │                              │
│  ┌───────────────────┐  │  ┌────────────────────────┐  │
│  │ عروض وتخفيضات اليوم│  │  │ Hardcoded price matrix │  │
│  │ (Deals Section)    │  │  │ Steam $10 / $20 / $50  │  │
│  ├───────────────────┤  │  │ Kinguin · Eneba · G2A  │  │
│  │ أهم أخبار الألعاب  │  │  │ Groq AI Price Analysis │  │
│  │ (News Section)     │  │  │ 24h background loop    │  │
│  ├───────────────────┤  │  └────────────────────────┘  │
│  │ مواعيد النزول     │  │                              │
│  │ (Releases Section) │  │                              │
│  │ Groq AI TL;DR × 3  │  │                              │
│  │ 24h background loop│  │                              │
│  └───────────────────┘  │                              │
└─────────────────────────┴──────────────────────────────┘
```

Both bots authenticate with separate Discord tokens, maintain independent Gateway connections, and target separate channels — yet share the same Python process, configuration, and event loop.

---

## Core Features

### Fully Autonomous Operation
- **Zero slash commands** — bots post automatically on a 24-hour cycle
- **Zero databases** — all data is hardcoded, no external dependencies
- **Zero user interaction** — deploy and forget

### Bot 1 — Autonomous Gaming News Hub

Posts a single embed every 24 hours containing three Arabic sections with individual AI TL;DR summaries:

| Section | Content | AI Integration |
|---------|---------|----------------|
| **عروض وتخفيضات اليوم** | 5 curated deals from Steam & Epic Games with discount percentages and store links | Groq generates a sharp Arabic summary of today's best discounts |
| **أهم أخبار الألعاب العالمية** | 5 trending gaming industry headlines with summaries | Groq generates an insightful Arabic news roundup |
| **مواعيد نزول الألعاب القادمة** | 5 upcoming game releases with dates and platforms | Groq generates an exciting Arabic release calendar preview |

All three Groq calls run **concurrently** via `asyncio.gather` for optimal performance.

### Bot 2 — Autonomous Steam Price Monitor

- Posts a **professional grid-style embed** every 24 hours comparing Steam Gift Cards across Kinguin, Eneba, and G2A
- Three card denominations: $10, $20, $50
- Dual-format display: card-by-card breakdown table + store-by-store cross-reference grid
- **Groq AI Price Analysis Insight** identifies the best value deal with dollar amounts and store names
- Auto-calculated footer showing the card with the highest absolute saving versus face value

### AI Integration (Groq LLM)

- Shared `llm.py` module wraps the official `AsyncGroq` SDK
- Bot 1 performs **3 concurrent** Groq calls per cycle for each section's TL;DR
- Bot 2 performs **1** Groq call per cycle for pricing analysis
- Graceful degradation — if any Groq call fails, the section posts without AI content

---

## Setup

### Prerequisites
- Python 3.10 or newer
- Two Discord bot tokens ([Discord Developer Portal](https://discord.com/developers/applications))
- A Groq API key ([Groq Console](https://console.groq.com/keys))
- Two Discord text channels in your server

### Installation

```bash
git clone https://github.com/your-username/nexusgaming-omnihub.git
cd nexusgaming-omnihub

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

Generate OAuth2 invite URLs for both applications with the `bot` scope and **Send Messages**, **Embed Links**, and **View Channels** permissions. No `applications.commands` scope required.

---

## Usage

```bash
python main.py
```

Both bots connect simultaneously. Each 24-hour background loop fires **immediately on `on_ready`**, then every 24 hours thereafter.

---

## Deployment (Railway)

1. Push the repository to GitHub
2. Create a new Railway project from the GitHub repo
3. Set the **five environment variables** in Railway Dashboard
4. Railway detects `requirements.txt` and installs dependencies automatically
5. Start command: `python main.py`

No `Dockerfile`, no `Procfile`, no configuration files needed.

---

## Project Structure

```
nexusgaming-omnihub/
├── main.py                  # Entry point — asyncio.gather dual-boot
├── config.py                # Shared Settings dataclass (env vars)
├── llm.py                   # Shared AsyncGroq wrapper
├── bot1/
│   └── client.py            # GameNewsBot — 24h loop with 3 AI sections
├── bot2/
│   └── client.py            # SteamPriceBot — 24h loop with price grid
├── .env / .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Performance

Two bot instances in a single process share the Python interpreter, the event loop, and cached modules. Typical RAM usage on Railway (512 MB plan): ~80–110 MB for both bots combined.

---

## License

MIT
