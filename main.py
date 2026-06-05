import os
import asyncio
import aiohttp
import discord
import os
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from groq import AsyncGroq
from datetime import datetime, timezone

# ==========================================
# 1. Environment Variables & Setup
# ==========================================
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID_1 = int(os.getenv("CHANNEL_ID_1"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# ==========================================
# 4. Bulletproof & Accurate Fetching Engines
# ==========================================
async def fetch_epic_games():
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            
    games = []
    elements = data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
    for game in elements:
        title = game.get("title", "Unknown Game").upper()
        
        original_price = "0.00"
        discount_price = "مجاناً"
        expiry_date = "غير محدد"
        
        # Extract pricing safely
        price_info = game.get("price", {}).get("totalPrice", {})
        if price_info:
            orig = price_info.get("originalPrice", 0)
            disc = price_info.get("discountPrice", 0)
            
            # Epic API sometimes returns cents, sometimes dollars. Safe conversion:
            if orig > 100:
                orig = orig / 100.0
            if disc > 100:
                disc = disc / 100.0
                
            original_price = f"{float(orig):.2f}"
            if float(disc) == 0:
                discount_price = "مجاناً"
            else:
                discount_price = f"{float(disc):.2f}"
                
        # Extract promotional expiry date
        promotions = game.get("promotions")
        if promotions:
            promotional_offers = promotions.get("promotionalOffers", [])
            if promotional_offers and len(promotional_offers) > 0:
                offers = promotional_offers[0].get("promotionalOffers", [])
                if offers:
                    end_date_str = offers[0].get("endDate", "")
                    if end_date_str:
                        try:
                            dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                            expiry_date = dt.strftime("%Y-%m-%d")
                        except Exception:
                            pass
            
            # Fallback to upcoming offers if current promotional offers are missing
            if expiry_date == "غير محدد":
                upcoming_offers = promotions.get("upcomingPromotionalOffers", [])
                if upcoming_offers and len(upcoming_offers) > 0:
                    offers = upcoming_offers[0].get("promotionalOffers", [])
                    if offers:
                        end_date_str = offers[0].get("endDate", "")
                        if end_date_str:
                            try:
                                dt = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                                expiry_date = dt.strftime("%Y-%m-%d")
                            except Exception:
                                pass

        games.append({
            "title": title,
            "original_price": original_price,
            "discount_price": discount_price,
            "expiry_date": expiry_date
        })
    return games

async def fetch_steam_games():
    url = "https://store.steampowered.com/api/featuredcategories/?cc=US&l=english"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            
    games = []
    specials = data.get("specials", {}).get("items", [])
    for game in specials:
        title = game.get("name", "Unknown Game").upper()
        
        # Steam API returns prices in cents. MUST divide by 100.0
        orig_cents = game.get("original_price", 0)
        final_cents = game.get("final_price", 0)
        
        original_price = f"{orig_cents / 100.0:.2f}"
        final_price = f"{final_cents / 100.0:.2f}"
        
        # Extract expiry date from timestamp
        exp_timestamp = game.get("discount_expiration")
        if exp_timestamp:
            dt = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            expiry_date = dt.strftime("%Y-%m-%d")
        else:
            expiry_date = "غير محدد"
            
        games.append({
            "title": title,
            "original_price": original_price,
            "discount_price": final_price,
            "expiry_date": expiry_date
        })
    return games

# ==========================================
# 5. Isolated Groq AI Instruction
# ==========================================
async def get_ai_description(title):
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Write a brief, single-sentence catchy premise/description in natural Arabic for the game title provided. Do not mention any prices, store names, discounts, or dates. Output only the pure Arabic sentence."
                },
                {
                    "role": "user",
                    "content": title,
                }
            ],
            model="llama3",
        )
        desc = chat_completion.choices[0].message.content.strip()
        return desc
    except Exception as e:
        print(f"Groq AI error for {title}: {e}")
        # Graceful fallback to prevent breaking the 24-hour background loop
        return "لعبة مغامرات وتحدي مميزة لأجهزة الكمبيوتر."

# ==========================================
# 2 & 3. Premium Visual Style & Exact Form
# ==========================================
@tasks.loop(hours=24)
async def daily_deals_loop():
    channel = bot.get_channel(CHANNEL_ID_1)
    if not channel:
        print(f"Channel {CHANNEL_ID_1} not found.")
        return

    # --- Epic Games Embed ---
    epic_games = await fetch_epic_games()
    if epic_games:
        embed_epic = discord.Embed(title="✨ عروض Epic Games اليوم", color=0x00df6d)
        desc_epic = []
        for game in epic_games:
            ai_desc = await get_ai_description(game["title"])
            # Single-line bulleted text block with NO inner line breaks
            line = f"• **{game['title']}** {ai_desc}. تم تنزيل السعر من {game['original_price']}$ إلى {game['discount_price']}$ وينتهي هذا العرض يوم {game['expiry_date']}."
            desc_epic.append(line)
        embed_epic.description = "\n".join(desc_epic)
        await channel.send(embed=embed_epic)

    # --- Steam Embed ---
    steam_games = await fetch_steam_games()
    if steam_games:
        embed_steam = discord.Embed(title="🎮 عروض Steam اليوم", color=0x1b2838)
        desc_steam = []
        for game in steam_games:
            ai_desc = await get_ai_description(game["title"])
            # Single-line bulleted text block with NO inner line breaks
            line = f"• **{game['title']}** {ai_desc}. تم تنزيل السعر من {game['original_price']}$ إلى {game['discount_price']}$ وينتهي هذا العرض يوم {game['expiry_date']}."
            desc_steam.append(line)
        embed_steam.description = "\n".join(desc_steam)
        await channel.send(embed=embed_steam)

# ==========================================
# Bot Initialization & Loop Start
# ==========================================
@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    if not daily_deals_loop.is_running():
        daily_deals_loop.start()

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)