import os
import asyncio
import aiohttp
import discord
from discord.ext import tasks
from groq import AsyncGroq
from datetime import datetime

# 1. Environment Variables & Setup
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_1 = int(os.getenv('CHANNEL_ID_1'))
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# 5. Isolated Groq AI Instruction
async def get_groq_description(title: str) -> str:
    system_prompt = "Write a brief, single-sentence catchy premise/description in natural Arabic for the game title provided. Do not mention any prices, store names, discounts, or dates. Output only the pure Arabic sentence."
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": title}
            ],
            model="llama3-8b-8192"
        )
        # Clean up the AI response to guarantee NO inner line breaks
        ai_text = chat_completion.choices[0].message.content.strip().replace('\n', ' ')
        return ai_text
    except Exception as e:
        print(f"Groq API failed for {title}: {e}")
        return "لعبة مغامرات وتحدي مميزة لأجهزة الكمبيوتر."

# 4. Bulletproof & Accurate Fetching Engines
async def fetch_epic_games() -> list:
    url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=en-US&country=US&allowCountries=US"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    games = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
                    epic_games = []
                    
                    for game in games:
                        title = game.get('title', 'Unknown')
                        price_info = game.get('price', {}).get('totalPrice', {})
                        original_price = price_info.get('originalPrice', 0) / 100.0
                        discount_price_cents = price_info.get('discountPrice', 0)
                        
                        promotions = game.get('promotions', {})
                        promotional_offers = promotions.get('promotionalOffers', [])
                        
                        expiry_date = "N/A"
                        if promotional_offers:
                            for offer_group in promotional_offers:
                                for offer in offer_group.get('promotionalOffers', []):
                                    end_date = offer.get('endDate')
                                    if end_date:
                                        expiry_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
                                        break
                        
                        if discount_price_cents == 0:
                            new_price_str = "مجاناً"
                        else:
                            new_price_str = f"{discount_price_cents / 100.0:.2f}$"
                            
                        epic_games.append({
                            'title': title,
                            'original_price': f"{original_price:.2f}$",
                            'new_price': new_price_str,
                            'expiry_date': expiry_date
                        })
                    return epic_games
                else:
                    print(f"Epic Games fetch failed with status: {response.status}")
        except Exception as e:
            print(f"Exception fetching Epic Games: {e}")
    return []

async def fetch_steam_games() -> list:
    url = "https://store.steampowered.com/api/featuredcategories/?cc=US&l=english"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    specials = data.get('specials', {})
                    items = specials.get('items', [])
                    steam_games = []
                    
                    for item in items:
                        title = item.get('name', 'Unknown')
                        original_price = item.get('original_price', 0) / 100.0
                        final_price = item.get('final_price', 0) / 100.0
                        
                        steam_games.append({
                            'title': title,
                            'original_price': f"{original_price:.2f}$",
                            'new_price': f"{final_price:.2f}$",
                            'expiry_date': "N/A"
                        })
                    return steam_games
                else:
                    print(f"Steam fetch failed with status: {response.status}")
        except Exception as e:
            print(f"Exception fetching Steam games: {e}")
    return []

# 6. Output Requirement (Background Loop)
@tasks.loop(hours=24)
async def daily_deals():
    channel = bot.get_channel(CHANNEL_ID_1)
    if not channel:
        print(f"Channel {CHANNEL_ID_1} not found.")
        return
        
    epic_games = await fetch_epic_games()
    steam_games = await fetch_steam_games()
    
    # 2. Premium Visual Style (Embed with Left Sidebar) & 3. Exact Description Form
    epic_desc = ""
    if epic_games:
        for game in epic_games:
            ai_desc = await get_groq_description(game['title'])
            # Continuous, single-line bulleted text block
            epic_desc += f"• **{game['title'].upper()}** {ai_desc}. تم تنزيل السعر من {game['original_price']} إلى {game['new_price']} وينتهي هذا العرض يوم {game['expiry_date']}.\n"
    else:
        epic_desc = "لا توجد عروض متاحة حالياً."
        
    epic_embed = discord.Embed(
        title="✨ عروض Epic Games اليوم",
        description=epic_desc,
        color=0x00df6d
    )
    await channel.send(embed=epic_embed)
    
    steam_desc = ""
    if steam_games:
        for game in steam_games:
            ai_desc = await get_groq_description(game['title'])
            # Continuous, single-line bulleted text block
            steam_desc += f"• **{game['title'].upper()}** {ai_desc}. تم تنزيل السعر من {game['original_price']} إلى {game['new_price']} وينتهي هذا العرض يوم {game['expiry_date']}.\n"
    else:
        steam_desc = "لا توجد عروض متاحة حالياً."
        
    steam_embed = discord.Embed(
        title="🎮 عروض Steam اليوم",
        description=steam_desc,
        color=0x1b2838
    )
    await channel.send(embed=steam_embed)

@daily_deals.before_loop
async def before_daily_deals():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    if not daily_deals.is_running():
        daily_deals.start()

if __name__ == "__main__":
    bot.run(TOKEN)