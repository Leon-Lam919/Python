import discord
from discord.ext import commands, tasks
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, time
import logging

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

def clear_all_points(ctx):
    user_id = str(ctx.author.id)
    points[user_id] = 0
    with open('points.json', 'w') as f:
        json.dump(points, f, indent=2)


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
        clear_all_points(ctx)
        
        # Calculate next reset
        config["last_reset"] = str(now.date())
        config["next_reset_date"] = str(calculate_next_reset(
            config["reset_interval"], 
            config.get("reset_day")
        ).date())
        
        save_config(config)
        return True
    return False


@tasks.loop(time=time(hour=16, minute=0))  # 4 PM
async def afternoon_reminder():
    now = datetime.now()
    day = now.weekday()  # 0=Monday, 6=Sunday
    
    channel = bot.get_channel(1450629690497962075)
    
    # Monday, Wednesday, Friday
    if day in [0, 2, 4]:
        await channel.send("🐱 Sophia scoop check-in time!")

@tasks.loop(time=time(hour=19, minute=0))  # 7 PM
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
    clear_all_points(ctx)
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

# ---------------------------
# Run Bot
# ---------------------------
load_dotenv()
bot.run(os.getenv('DISCORD_TEST'))
