# Discord Game Deals Bot

A multilingual Discord bot that automatically tracks daily game discounts from **Steam** and **Epic Games Store**, generates concise Arabic descriptions for each game via the Groq LLM API, and posts a formatted summary to a configured channel every 24 hours.

Built with discord.py, asyncio, and the CheapShark public API — no external database required. Designed for zero-maintenance 24/7 deployment.

---

## Key Features

- **Automated deal aggregation** — Fetches real-time discounts from Steam and Epic Games Store via the CheapShark API every 24 hours.
- **LLM-powered Arabic descriptions** — For each discounted game, calls Groq's `llama-3.1-8b-instant` model to generate a short, catchy Arabic phrase (3–6 words) describing the game's theme or studio.
- **Arabic-first output** — Dates are displayed with Arabic month names; 100%-off games show "مجاناً" instead of "$0".
- **Resilient error handling** — Exponential backoff on API rate limits (CheapShark and Groq); graceful fallback descriptions when the LLM is unavailable.
- **Stateless & lightweight** — No database. No slash commands. Pure loop-and-send architecture.

---

## Architecture

```
main.py                  # Entry point — loads .env, validates config, boots client
└── bot/
    ├── config.py        # Environment variable validation
    ├── client.py        # Discord client with 24-hour background task
    ├── deals.py         # CheapShark API interaction
    ├── groq_client.py   # Groq API interaction
    └── formatters.py    # Arabic date / price formatting
```

The bot does not listen to user commands. It connects to Discord, waits for the Gateway to confirm readiness, then immediately runs its first deal-fetch cycle. Subsequent cycles repeat every 24 hours.

---

## Setup

### Prerequisites

- Python 3.10 or newer
- A Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Groq API key ([Groq Console](https://console.groq.com/keys))
- A Discord server with a text channel to receive deal messages

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/discord-game-deals-bot.git
cd discord-game-deals-bot

# Create a virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux / macOS

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```ini
DISCORD_TOKEN=your_discord_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
CHANNEL_ID=123456789012345678
```

> **Note:** The `.env` file contains secrets and is excluded from version control via `.gitignore`.

### Invite the bot to your server

Generate an OAuth2 invite URL in the Discord Developer Portal with the following permissions:

- Scope: `bot`
- Permissions: `Send Messages` + `Embed Links` + `View Channels`

Use the generated URL to add the bot to your server.

---

## Usage

```bash
python main.py
```

On first startup the bot will:

1. Connect to Discord.
2. Fetch the latest deals from Steam and Epic Games Store.
3. Generate Arabic descriptions via Groq.
4. Post the results to the configured channel.

Thereafter the cycle repeats every 24 hours automatically.

---

## Deployment

For 24/7 operation, run the bot inside a persistent environment:

### Docker (recommended)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

```bash
docker build -t game-deals-bot .
docker run -d --env-file .env --name deals-bot game-deals-bot
```

### systemd (Linux)

Create a service file at `/etc/systemd/system/deals-bot.service`:

```ini
[Unit]
Description=Discord Game Deals Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project
EnvironmentFile=/path/to/project/.env
ExecStart=/path/to/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now deals-bot
```

### Process manager (pm2 / supervisor)

Use any process manager that supports Python and auto-restart on failure. Ensure the `.env` file is present in the working directory.

---

## Output Example

A typical daily message posted to the configured Discord channel:

> **🎮 عروض Steam اليوم**
>
> - **Red Dead Redemption 2** لعبة الـ Cowboy والشرق المتوحش الشهيرة من Rockstar تم تنزيل السعر من 60$ إلى 15$ وينتهي هذا العرض يوم 15 يونيو
> - **Hades** لعبة الأكشن والروغولايك الحائزة على جوائز تم تنزيل السعر من 25$ إلى 10$ وينتهي هذا العرض يوم 20 يونيو

---

## Project Status

Active. Feature requests and pull requests are welcome.
