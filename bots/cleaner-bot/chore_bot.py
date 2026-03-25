import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, time
import logging
import pytz
from tplinkrouterc6u import TplinkRouterProvider, Connection, TplinkRouter
from tplinkrouterc6u.common.exception import ClientError
import asyncio
import time as time_module


# ===== ROUTER CONFIGURATION =====
load_dotenv()
ROUTER_IP = os.getenv('ROUTER_IP', '')
ROUTER_PASSWORD = os.getenv('ROUTER_PASSWORD','')
TARGET_MAC = os.getenv('TARGET_MAC','')
GUEST_BAND= Connection.GUEST_5G

# Get the client class once
RouterClient = TplinkRouterProvider.get_client(ROUTER_IP, ROUTER_PASSWORD).__class__

def block_wifi_indefinite(state=False):
    try:
        if not state:
            print("Blocking wifi.")
        else: 
            print("Unblocking wifi.")

        client = RouterClient(ROUTER_IP, ROUTER_PASSWORD)
        client.authorize()
        client.set_wifi(GUEST_BAND, state)
        time_module.sleep(2)
        status = client.get_status()
        current_state = status.guest_5g_enable
        
        if state == False:
            if current_state == False:
                print("The wifi is off.")
                return True
            else: 
                print("Wifi failed to turn off.")
                return False
        
        if state == True:
            if current_state == True:
                print("Wifi is turned on.")
                return True
            else:
                print("Wifi failed to turn on.")
                return False

        client.logout()

    except Exception as e:
        print(f"❌ Error in wifi turning off: {e}")
        return False

async def async_wifi_control(state: bool) -> bool:
    """Helper to run WiFi control in thread pool"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, block_wifi_indefinite, state)



# ---------------------------
# Predefined Chores & Points
# ---------------------------

CHORE_POINTS = {
    "scoop": 5,
    "sweepbath": 15, 
    "sweep": 10, 
    "laundry": 5, 
    "fold": 30,
    "hang": 10,
    "workout": 30,
    "vaclive": 15, 
    "vacoffice": 10,
    "vacbed": 10,
    "dust": 2,
    "mirror": 3,
    "mopbath": 15,
    "mop": 12,
    "dusteverything": 5,
    "declutter": 7,
    "fridge": 5,
    "random": 10,
    "work": 3, 
    "foodprep": 8,
    "souschef": 25,
    "gradschool": 10,
    "workout": 40,
    "study": 10,
}

LEON_TASKS = {
    "code": 5, 
    "work": 15,
    "network": 5,
    "workout": 10,
    "leetcode": 20,
    "keyboard": 5,
    "cardio": 10,
}

LEON_REWARDS = {
    "game": 30,
    "takeout": 100,
    "videos": 30,
}

REWARDS = {
    "TV: 1 point = 1 minute",
    "Leon reading comic: 1 point = 1 minute",
}

# -------------------------------
# Predefined time reset config
# -------------------------------

DEFAULT_CONFIG = {
    "reset_interval": "biweekly",
    "reset_day": "monday",
    "next_reset_date": None  # Auto-calculated
}

# -------------------------------
# Setting up logging for the bot
# -------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(filename="bot.log", encoding="utf-8", level=logging.INFO)
logging.getLogger('discord').setLevel(logging.WARNING)


# ---------------------------
# Bot Setup
# ---------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


# ------------------------------
# Bot commands for wifi control
# ------------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def wifi(ctx, status:str):
    status = status.lower()
    if status == 'on':
        success = await asyncio.get_event_loop().run_in_executor(None, block_wifi_indefinite, True)
        if success:
            await ctx.send(f"Wifi turned on!")
        else:
            await ctx.send("Wif was not turned on!")
    if status == 'off':
        success = await asyncio.get_event_loop().run_in_executor(None, block_wifi_indefinite, False)
        if success:
            await ctx.send(f"Wifi turned off!")
        else:
            await ctx.send("Wif was not turned off!")
    else:
        ctx.send("Wifi was unable to change to on/off.")

async def timed_wifi(ctx, duration_minutes: int, label: str = "session"):
    """Turn WiFi on for a duration, then off"""
    # Turn ON
    duration_minutes = duration_minutes - 1

    if not await async_wifi_control(True):
        await ctx.send("❌ Failed to turn on WiFi")
        return False
    
    await asyncio.sleep(60)
    await ctx.send(f"✅ WiFi enabled!")
    
    # Wait
    duration_minutes = duration_minutes + 1
    await asyncio.sleep(duration_minutes * 60)
    
    # Turn OFF
    await ctx.send(f"⏰ {label.capitalize()} time over! Turning WiFi OFF...")
    
    if await async_wifi_control(False):
        await ctx.send("🚫 WiFi is now OFF")
        return True
    else:
        await ctx.send("❌ Failed to turn off WiFi")
        return False

@bot.command(help="Turn on Wifi for 45 minutes for breakfast")
async def breakfast(ctx):
    epoch = int((datetime.now() + timedelta(minutes=46)).timestamp())
    await ctx.send(f"Breakfast will end at: <t:{epoch}:t>")
    await ctx.send(f"Breakfast will end in: <t:{epoch}:R>.")
    await timed_wifi(ctx, 46, "breakfast")
    

@bot.command(help="Turn on Wifi for 60 minutes for lunch")
async def lunch(ctx):
    epoch = int((datetime.now() + timedelta(minutes=61)).timestamp())
    await ctx.send(f"Lunch will end at: <t:{epoch}:t>")
    await ctx.send(f"Lunch will end in: <t:{epoch}:R>.")
    await timed_wifi(ctx, 61, "lunch")


@bot.command(help="Turn on Wifi for 60 minutes for dinner")
async def dinner(ctx):
    epoch = int((datetime.now() + timedelta(minutes=61)).timestamp())
    await ctx.send(f"Dinner will end at: <t:{epoch}:t>")
    await ctx.send(f"Dinner will end in: <t:{epoch}:R>.")
    await timed_wifi(ctx, 61, "dinner")


# ---------------------------
# Load & Save Point Data
# ---------------------------

POINTS_FILE = "points.json"

def load_points():
    if not os.path.exists(POINTS_FILE):
        return {}
    with open(POINTS_FILE, "r") as f:
        return json.load(f)

def save_points(data):
    with open(POINTS_FILE, "w") as f:
        json.dump(data, f, indent=4)

points = load_points()

# ------------------------------
# Custom point reset functions
# ------------------------------

def load_config():
    try:
        with open('reset_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open('reset_config.json', 'w') as f:
        json.dump(config, f, indent=2)

def clear_all_points():
    data = load_points()
    for points in data:
        data[points] = 0
    save_points(data)

def calculate_next_reset(interval, reset_day=None, custom_date=None):
    now = datetime.now()
    
    if interval == "daily":
        return now.replace(hour=0, minute=0, second=0) + timedelta(days=1)
    
    elif interval == "weekly":
        # reset_day = "monday", "tuesday", etc.
        days = {"monday": 0, "tuesday": 1, "wednesday": 2, 
                "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
        target_day = days[reset_day.lower()]
        days_ahead = (target_day - now.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return now + timedelta(days=days_ahead)
    
    elif interval == "biweekly":
        # Calculate 2 weeks from last reset
        config = load_config()
        last_reset = datetime.fromisoformat(config.get("last_reset", str(now.date())))
        return last_reset + timedelta(weeks=2)
    
    elif interval == "custom":
        return datetime.fromisoformat(custom_date)

# Check if reset needed
def check_and_reset_points():
    config = load_config()
    now = datetime.now()
    next_reset = datetime.fromisoformat(config["next_reset_date"])
    
    if now >= next_reset:
        # DO THE RESET
        clear_all_points()
        
        # Calculate next reset
        config["last_reset"] = str(now.date())
        config["next_reset_date"] = str(calculate_next_reset(
            config["reset_interval"], 
            config.get("reset_day")
        ).date())
        
        save_config(config)
        return True
    return False

cst = pytz.timezone('America/Chicago')

#@tasks.loop(time=time(minute=1))

#time loops for scooping reminder
@tasks.loop(time=time(hour=16, minute=0, tzinfo=cst))  # 4 PM
async def afternoon_reminder():
    now = datetime.now()
    day = now.weekday()  # 0=Monday, 6=Sunday
    channel = bot.get_channel(1450629690497962075)
    
    # Monday, Wednesday, Friday
    if day in [0, 2, 4]:
        await channel.send("🐱 Sophia scoop check-in time!")

#time loops for scooping reminder
@tasks.loop(time=time(hour=19, minute=0, tzinfo=cst))  # 7 PM
async def evening_reminder():
    now = datetime.now()
    day = now.weekday()  # 0=Monday, 6=Sunday
    
    channel = bot.get_channel(1450629690497962075)
    
    # Monday, Wednesday, Friday
    if day in [0, 2, 4]:
        await channel.send("🐱 Sophia scoop check-in time!")

@bot.event
async def on_ready():
    afternoon_reminder.start()
    evening_reminder.start()

# Discord commands
@bot.command()
@commands.has_permissions(administrator=True)
async def set_reset(ctx, interval: str, *, details: str = "monday"):
    """
    Usage:
    !set_reset daily
    !set_reset weekly monday
    !set_reset biweekly
    !set_reset custom 2024-12-15
    """
    config = load_config()
    config["reset_interval"] = interval.lower()
    
    if interval.lower() == "weekly":
        config["reset_day"] = details.lower()
    elif interval.lower() == "custom":
        config["custom_date"] = details
    
    # Recalculate next reset
    config["next_reset_date"] = str(calculate_next_reset(
        config["reset_interval"],
        config.get("reset_day"),
        config.get("custom_date")
    ).date())
    
    save_config(config)
    
    await ctx.send(
        f"✅ Reset schedule updated!\n"
        f"Interval: **{interval}**\n"
        f"Next reset: **{config['next_reset_date']}**"
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def force_reset(ctx):
    """Immediately clear all points"""
    clear_all_points()
    config = load_config()
    config["last_reset"] = str(datetime.now().date())
    config["next_reset_date"] = str(calculate_next_reset(
        config["reset_interval"],
        config.get("reset_day")
    ).date())
    save_config(config)
    
    await ctx.send("💥 All points have been reset!")

@bot.command()
async def next_reset(ctx):
    """Check when points reset"""
    config = load_config()
    await ctx.send(
        f"📅 Next points reset: **{config['next_reset_date']}**\n"
        f"Reset interval: **{config['reset_interval']}**"
    )

# ---------------------------
# Help menu
# ---------------------------

@bot.event
async def on_message(message):
    if message.content.strip() == "!":
        embed = discord.Embed(
            title="Bank bot commands",
            description="Here are the commands you can use:",
            color=0x00ff00
        )
        for cmd in bot.commands:
            embed.add_field(
                name=f"!{cmd.name}",
                value=cmd.help or "No description provided",
                inline=False
            )
        await message.channel.send(embed=embed)

    await bot.process_commands(message)

# ---------------------------
# Commands
# ---------------------------

@bot.command(help="Adds points to your account based on what chore completed.")
async def finish(ctx, chore_name: str, amount: int=0):
    """Completes a chore and adds the appropriate points."""
    chore_name = chore_name.lower()
    user_id = str(ctx.author.id)
    
    if not chore_name:  # Catches None and empty string
        await ctx.send("❌ Please specify a task! Example: `!finish sweep`")
        return

    if chore_name == 'study' and amount != 0:
        amount = amount // 2
        points[user_id] += amount
        save_points(points)
        
        logging.info(f"user {ctx.author.name} completed {chore_name}")
        await ctx.send(
            f"✅ {ctx.author.mention} completed **{chore_name}** "
            f"and earned **{amount} points!**\n"
            f"💰 New total: **{points[user_id]} points**"
        )
        return


    if amount > 0:
        points[user_id] += amount
        save_points(points)
        
        logging.info(f"user {ctx.author.name} completed {chore_name}")
        await ctx.send(
            f"✅ {ctx.author.mention} completed **{chore_name}** "
            f"and earned **{amount} points!**\n"
            f"💰 New total: **{points[user_id]} points**"
        )
        return
     
    if chore_name not in CHORE_POINTS:
        await ctx.send(
            f"❌ Unknown chore: **{chore_name}**\n"
            f"Use `!list` to see all available chores."
        )
        return


    if user_id not in points:
        points[user_id] = 0

    earned = CHORE_POINTS[chore_name]
    points[user_id] += earned
    save_points(points)
    
    logging.info(f"user {ctx.author.name} completed {chore_name}")
    await ctx.send(
        f"✅ {ctx.author.mention} completed **{chore_name}** "
        f"and earned **{earned} points!**\n"
        f"💰 New total: **{points[user_id]} points**"
    )


@bot.command(help="Adds points to your account based on what task is completed.")
async def lf(ctx, chore_name: str, amount: int=0):
    """Completes a task and adds the appropriate points."""
    chore_name = chore_name.lower()
    user_id = str(ctx.author.id)
    
    if not chore_name:  # Catches None and empty string
        await ctx.send("❌ Please specify a task! Example: `!lf code`")
        return

    if chore_name == 'study' and amount != 0:
        amount = amount // 2
        points[user_id] += amount
        save_points(points)
        
        logging.info(f"user {ctx.author.name} completed {chore_name}")
        await ctx.send(
            f"✅ {ctx.author.mention} completed **{chore_name}** "
            f"and earned **{amount} points!**\n"
            f"💰 New total: **{points[user_id]} points**"
        )
        return


    if amount > 0:
        points[user_id] += amount
        save_points(points)
        
        logging.info(f"user {ctx.author.name} completed {chore_name}")
        await ctx.send(
            f"✅ {ctx.author.mention} completed **{chore_name}** "
            f"and earned **{amount} points!**\n"
            f"💰 New total: **{points[user_id]} points**"
        )
        return
     
    if chore_name not in LEON_TASKS:
        await ctx.send(
            f"❌ Unknown chore: **{chore_name}**\n"
            f"Use `!list` to see all available chores."
        )
        return


    if user_id not in points:
        points[user_id] = 0

    earned = LEON_TASKS[chore_name]
    points[user_id] += earned
    save_points(points)
    
    logging.info(f"user {ctx.author.name} completed {chore_name}")
    await ctx.send(
        f"✅ {ctx.author.mention} completed **{chore_name}** "
        f"and earned **{earned} points!**\n"
        f"💰 New total: **{points[user_id]} points**"
    )


@bot.command(help="Used for no bones day (will take 50 points)")
async def no_bones(ctx):
    user_id = str(ctx.author.id)
    if points[user_id] < 50:
        await ctx.send("Not enough points to spend on No bones day. :(")
        return
    
    points[user_id] -= 50
    
    await ctx.send("Turning on wifi.")
    block_wifi_indefinite(True)
    await asyncio.sleep(5)

    now = datetime.now()
    # Target: 9 PM today (or tomorrow if past 9 PM)
    nine_pm = datetime.combine(now.date(), time(21, 0))
    if now >= nine_pm:
        nine_pm += timedelta(days=1)
    
    # Delta as total minutes (integer)
    delta_minutes = int((nine_pm - now).total_seconds() // 60)
    epoch = int((datetime.now() + timedelta(minutes=delta_minutes)).timestamp())
    
    await ctx.send(f"Wifi on, will turn off at: {epoch}")

    await asyncio.sleep(delta_minutes*60)
    await ctx.send("Turning off wifi...")
    block_wifi_indefinite()

@bot.command()
async def spend(ctx, amount: int):
    """Spend points."""
    user_id = str(ctx.author.id)
    if user_id not in points:
        points[user_id] = 0

    if amount <= 0:
        await ctx.send("❌ You cannot spend negative points\n")
        return

    if points[user_id] < amount:
        await ctx.send(
            f"❌ Not enough points!\n"
            f"You have: **{points[user_id]} points**"
        )
        return

    points[user_id] -= amount
    save_points(points)

    amount = amount + 1
    epoch = int((datetime.now() + timedelta(minutes=amount)).timestamp())
    await ctx.send(f"Break will end at: <t:{epoch}:t>")
    await ctx.send(f"Break will end in: <t:{epoch}:R>.")
    await timed_wifi(ctx, amount, "Break")

    amount = amount - 1

    logging.info(f"user {ctx.author.name} spent {amount} points.")

    await ctx.send(
        f"💸 {ctx.author.mention} spent **{amount} points**.\n"
        f"Remaining balance: **{points[user_id]} points**"
    )


@bot.command()
async def total(ctx):
    """Check your point total."""
    user_id = str(ctx.author.id)
    total = points.get(user_id, 0)

    await ctx.send(
        f"💰 {ctx.author.mention}, you currently have **{total} points**!"
    )


@bot.command()
async def list(ctx):
    """List all predefined chores and point values."""
    msg = "**🧹 Available Tasks & Points:**\n\n"
    for chore, pts in CHORE_POINTS.items():
        msg += f"• **{chore}** — {pts} points\n"

    await ctx.send(msg)

@bot.command()
async def leon(ctx):
    """List all predefined chores and point values."""
    msg = "**🧹 Available Tasks & Points:**\n\n"
    for chore, pts in LEON_TASKS.items():
        msg += f"• **{chore}** — {pts} points\n"

    await ctx.send(msg)


# ---------------------------
# Run Bot
# ---------------------------
load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))
