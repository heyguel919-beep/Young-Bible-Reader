import os
import discord
from discord.ext import commands, tasks
import requests
import re

DEFAULT_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
daily_channel_id = DEFAULT_CHANNEL_ID


# --- API FUNCTION ---
def get_bible_verse(reference, lang="en"):
    try:
        # Detect language automatically
        if re.search(r"Jo[aã]o|Romanos|G[eê]nesis|Salmos|Mateus", reference, re.I):
            lang = "pt"
        elif re.search(r"John|Romans|Genesis|Psalms|Matthew", reference, re.I):
            lang = "en"

        api_url = f"https://bible-api.com/{reference}?translation={'almeida' if lang == 'pt' else 'kjv'}"
        res = requests.get(api_url)
        if res.status_code != 200:
            return "❌ Verse not found."
        data = res.json()

        # Format verses (1, 2, 3)
        verses_text = "\n".join([f"^{v['verse']} {v['text'].strip()}" for v in data["verses"]])
        return f"📖 **{data['reference']}**\n\n{verses_text}"

    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# --- COMMAND: Get verse ---
@bot.command()
async def verse(ctx, *, ref):
    """Fetch any Bible verse, e.g., !verse João 1:1 or !verse John 1:1"""
    await ctx.send("⏳ Searching...")
    result = get_bible_verse(ref)
    await ctx.send(result)


# --- COMMAND: Set daily verse channel ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setdaily(ctx):
    """Set the current channel as the daily verse channel"""
    global daily_channel_id
    daily_channel_id = ctx.channel.id
    await ctx.send(f"✅ Daily verse channel set to: {ctx.channel.mention}")


# --- TASK: Daily verse (runs automatically) ---
@tasks.loop(hours=24)
async def send_daily_verse():
    if daily_channel_id == 0:
        return
    channel = bot.get_channel(daily_channel_id)
    if not channel:
        return

    # Default daily verse (random)
    res = requests.get("https://labs.bible.org/api/?passage=random&type=json")
    if res.status_code == 200:
        data = res.json()[0]
        verse = f"📖 **{data['bookname']} {data['chapter']}:{data['verse']}**\n\n{data['text']}"
        await channel.send(f"🌅 Daily Verse:\n{verse}")
    else:
        await channel.send("⚠️ Could not fetch the daily verse.")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not send_daily_verse.is_running():
        send_daily_verse.start()


bot.run("MTQzNzk0Njk4NDM3MDc5ODc0Mw.G0ccJo.NNbd6JiMOLzt1KXw-R5iL-DIHO9su_MDGMExiY")
