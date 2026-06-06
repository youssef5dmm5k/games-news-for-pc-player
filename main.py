import os
import asyncio
import aiohttp
import discord
from discord.ext import tasks
from groq import AsyncGroq
from datetime import datetime, timedelta

# Environment Variables & Setup
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID_1 = int(os.getenv('CHANNEL_ID_1'))
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

intents = discord.Intents.all()
bot = discord.Client(intents=intents)
groq_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Cache to prevent duplicate descriptions
description_cache = {}

async def get_groq_description(title: str) -> str:
    """Get AI-generated Arabic description for a game"""
    if title in description_cache:
        return description_cache[title]
    
    if not groq_client:
        fallback_descs = [
            "مغامرة مثيرة تأخذك إلى عوالم جديدة",
            "تجربة لعب فريدة مليئة بالتحديات",
            "لعبة استراتيجية تتطلب التفكير والتخطيط",
            "مغامرة أكشن مليئة بالإثارة",
            "لعبة تقمص أدوار غامرة"
        ]
        desc = fallback_descs[hash(title) % len(fallback_descs)]
        description_cache[title] = desc
        return desc
    
    system_prompt = "اكتب جملة واحدة قصيرة وجذابة بالعربية تصف اللعبة. لا تذكر اسم اللعبة ولا الأسعار ولا المتجر. فقط صف طبيعة اللعبة."
    
    try:
        chat_completion = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"اكتب وصفاً مختصراً للعبة: {title}"}
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=60
        )
        ai_text = chat_completion.choices[0].message.content.strip().replace('\n', ' ')
        
        # Remove common prefixes that repeat the title
        prefixes_to_remove = [title.lower(), "لعبة", "اللعبة"]
        for prefix in prefixes_to_remove:
            if ai_text.lower().startswith(prefix):
                ai_text = ai_text[len(prefix):].strip()
                ai_text = ai_text.lstrip(':-., ')
                break
        
        if not ai_text:
            ai_text = "مغامرة مثيرة تأخذك إلى عوالم جديدة"
            
        description_cache[title] = ai_text
        return ai_text
        
    except Exception as e:
        print(f"Groq API failed for {title}: {e}")
        fallback_descs = [
            "مغامرة مثيرة تأخذك إلى عوالم جديدة",
            "تجربة لعب فريدة مليئة بالتحديات",
            "لعبة استراتيجية تتطلب التفكير والتخطيط"
        ]
        desc = fallback_descs[hash(title) % len(fallback_descs)]
        description_cache[title] = desc
        return desc

async def fetch_epic_games() -> list:
    """Fetch 10 games on sale from Epic Games Store with accurate prices"""
    url = "https://store.epicgames.com/graphql"
    
    query = """
    query searchStoreQuery($count: Int, $country: String!) {
      Catalog {
        searchStore(
          count: $count
          country: $country
          onSale: true
          sortBy: "discount"
          sortDir: "DESC"
        ) {
          elements {
            title
            namespace
            id
            promotions {
              promotionalOffers {
                promotionalOffers {
                  endDate
                  discountSetting {
                    discountPercentage
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {"count": 20, "country": "US"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    games_list = []
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json={"query": query, "variables": variables}, headers=headers) as response:
                if response.status != 200:
                    print(f"Epic GraphQL failed: {response.status}")
                    return []
                    
                data = await response.json()
                elements = data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
                
                # Get detailed pricing for each game
                for game in elements[:15]:  # Fetch more to filter
                    title = game.get('title', 'Unknown')
                    namespace = game.get('namespace')
                    game_id = game.get('id')
                    
                    # Get pricing details
                    price_query = """
                    query getProduct($namespace: String!, $slug: String!) {
                      Catalog {
                        searchStore(namespace: $namespace, slug: $slug, count: 1) {
                          elements {
                            price(country: "US") {
                              totalPrice {
                                originalPrice
                                discountPrice
                                fmtPrice(locale: "en-US") {
                                  originalPrice
                                  discountPrice
                                }
                              }
                            }
                            promotions {
                              promotionalOffers {
                                promotionalOffers {
                                  endDate
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    """
                    
                    try:
                        async with session.post(
                            url, 
                            json={"query": price_query, "variables": {"namespace": namespace, "slug": title.lower().replace(' ', '-')}},
                            headers=headers
                        ) as price_resp:
                            if price_resp.status == 200:
                                price_data = await price_resp.json()
                                price_elements = price_data.get('data', {}).get('Catalog', {}).get('searchStore', {}).get('elements', [])
                                
                                if price_elements:
                                    price_info = price_elements[0].get('price', {}).get('totalPrice', {})
                                    fmt_price = price_info.get('fmtPrice', {})
                                    
                                    original = fmt_price.get('originalPrice', '').replace('$', '').strip()
                                    discount = fmt_price.get('discountPrice', '').replace('$', '').strip()
                                    
                                    # Parse dates
                                    expiry = "N/A"
                                    promos = price_elements[0].get('promotions', {})
                                    if promos:
                                        offers = promos.get('promotionalOffers', [])
                                        if offers:
                                            for offer_group in offers:
                                                for offer in offer_group.get('promotionalOffers', []):
                                                    end_date = offer.get('endDate')
                                                    if end_date:
                                                        try:
                                                            expiry = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
                                                        except:
                                                            expiry = "N/A"
                                                        break
                    
                                    if original and discount and original != discount:
                                        games_list.append({
                                            'title': title,
                                            'original_price': f"{original}$" if original else "0$",
                                            'new_price': f"{discount}$" if discount != "0" else "مجاناً",
                                            'expiry_date': expiry
                                        })
                    except Exception as e:
                        print(f"Error fetching price for {title}: {e}")
                        continue
                    
                    if len(games_list) >= 10:
                        break
                        
        except Exception as e:
            print(f"Exception in Epic Games fetch: {e}")
    
    return games_list[:10]

async def fetch_steam_games() -> list:
    """Fetch 10 games on sale from Steam with accurate prices"""
    base_url = "https://store.steampowered.com/api/featuredcategories"
    params = {"cc": "US", "l": "english"}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(base_url, params=params, headers=headers) as response:
                if response.status != 200:
                    print(f"Steam API failed: {response.status}")
                    return []
                    
                data = await response.json()
                specials = data.get('specials', {})
                items = specials.get('items', [])
                
                games_list = []
                
                for item in items[:15]:  # Get more to filter
                    appid = item.get('id')
                    title = item.get('name', 'Unknown')
                    
                    # Get detailed pricing from appdetails API
                    details_url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=US"
                    
                    try:
                        async with session.get(details_url, headers=headers) as details_resp:
                            if details_resp.status == 200:
                                details_data = await details_resp.json()
                                app_data = details_data.get(str(appid), {})
                                
                                if app_data.get('success'):
                                    price_overview = app_data.get('data', {}).get('price_overview', {})
                                    
                                    if price_overview:
                                        original = price_overview.get('initial', 0) / 100.0
                                        final = price_overview.get('final', 0) / 100.0
                                        discount_percent = price_overview.get('discount_percent', 0)
                                        
                                        # Only include if there's an actual discount
                                        if discount_percent > 0 and original > final:
                                            games_list.append({
                                                'title': title,
                                                'original_price': f"{original:.2f}$",
                                                'new_price': f"{final:.2f}$",
                                                'expiry_date': "N/A"
                                            })
                    except Exception as e:
                        print(f"Error fetching details for {title}: {e}")
                        continue
                    
                    if len(games_list) >= 10:
                        break
                        
        except Exception as e:
            print(f"Exception in Steam fetch: {e}")
    
    return games_list[:10]

@tasks.loop(hours=24)
async def daily_deals():
    channel = bot.get_channel(CHANNEL_ID_1)
    if not channel:
        print(f"Channel {CHANNEL_ID_1} not found.")
        return
    
    # Clear cache for fresh descriptions
    description_cache.clear()
    
    epic_games = await fetch_epic_games()
    steam_games = await fetch_steam_games()
    
    # Epic Games Embed
    epic_desc = ""
    if epic_games:
        for i, game in enumerate(epic_games, 1):
            ai_desc = await get_groq_description(game['title'])
            epic_desc += f"• **{game['title'].upper()}** {ai_desc}. تم تنزيل السعر من {game['original_price']} إلى {game['new_price']} وينتهي هذا العرض يوم {game['expiry_date']}.\n"
            if i < len(epic_games):
                epic_desc += "\n"
    else:
        epic_desc = "لا توجد عروض متاحة حالياً."
        
    epic_embed = discord.Embed(
        title="✨ عروض Epic Games اليوم",
        description=epic_desc,
        color=0x00df6d,
        timestamp=datetime.utcnow()
    )
    epic_embed.set_footer(text="تم التحديث")
    await channel.send(embed=epic_embed)
    
    # Steam Embed
    steam_desc = ""
    if steam_games:
        for i, game in enumerate(steam_games, 1):
            ai_desc = await get_groq_description(game['title'])
            steam_desc += f"• **{game['title'].upper()}** {ai_desc}. تم تنزيل السعر من {game['original_price']} إلى {game['new_price']} وينتهي هذا العرض يوم {game['expiry_date']}.\n"
            if i < len(steam_games):
                steam_desc += "\n"
    else:
        steam_desc = "لا توجد عروض متاحة حالياً."
        
    steam_embed = discord.Embed(
        title="🎮 عروض Steam اليوم",
        description=steam_desc,
        color=0x1b2838,
        timestamp=datetime.utcnow()
    )
    steam_embed.set_footer(text="تم التحديث")
    await channel.send(embed=steam_embed)

@daily_deals.before_loop
async def before_daily_deals():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('Starting daily deals loop...')
    if not daily_deals.is_running():
        daily_deals.start()
        # Send immediately on startup
        await asyncio.sleep(5)
        await daily_deals()

if __name__ == "__main__":
    bot.run(TOKEN)