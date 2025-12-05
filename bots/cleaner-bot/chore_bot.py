import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


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

REWARDS = {}
# -------------------------------
# Predefined time reset config
# -------------------------------

DEFAULT_CONFIG = {
    "reset_interval": "biweekly",
    "reset_day": "monday",
    "next_reset_date": None  # Auto-calculated
}


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
            title="Cleaner bot commands",
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
async def chore(ctx, chore_name: str):
    """Completes a chore and adds the appropriate points."""
    chore_name = chore_name.lower()

    if not chore_name:  # Catches None and empty string
        await ctx.send("❌ Please specify a chore! Example: `!chore sweep`")
        return

    if chore_name not in CHORE_POINTS:
        await ctx.send(
            f"❌ Unknown chore: **{chore_name}**\n"
            f"Use `!chorelist` to see all available chores."
        )
        return

    user_id = str(ctx.author.id)

    if user_id not in points:
        points[user_id] = 0

    earned = CHORE_POINTS[chore_name]
    points[user_id] += earned
    save_points(points)

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
async def chorelist(ctx):
    """List all predefined chores and point values."""
    msg = "**🧹 Available Chores & Points:**\n\n"
    for chore, pts in CHORE_POINTS.items():
        msg += f"• **{chore}** — {pts} points\n"

    await ctx.send(msg)

# ---------------------------
# Run Bot
# ---------------------------
load_dotenv()
bot.run(os.getenv('DISCORD_TOKEN'))
