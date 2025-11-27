import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv

# ---------------------------
# Predefined Chores & Points
# ---------------------------

CHORE_POINTS = {
    "scoop": 5,
    "sweep bathroom": 15, 
    "sweep": 10, 
    "laundry": 5, 
    "fold laundry": 30,
    "hang laundry": 10,
    "work out": 30,
    "Vacuum living": 15, 
    "Vacuum office": 10,
    "Vacuum bedroom": 10,
    "Dust tv stand": 2,
    "Bathroom mirror": 3, 
}

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

# ---------------------------
# Bot Setup
# ---------------------------

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
