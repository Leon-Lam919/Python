#create bot
#imported libs
import json
import os
import asyncio
import requests
import discord
from discord.ext import commands, tasks
import youtube_dl
from dotenv import load_dotenv

intents = discord.Intents.default()
intents.message_content = True
<<<<<<< HEAD
bot = commands.Bot(command_prefix='$', intents=intents)
=======
intents.members = True
client = discord.Client(intents=intents)
bot = commands.bot(command_prefix='$', intents=intents)
>>>>>>> 0d7bc6cefa3a3c45e981bbc9036b4e14adaaea5e

# calls DISCORD_TOKEN to get discord token from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

#youtube music
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options ={
    'format' : 'bestaudio/best',
    'restrictfilenames' : True,
    'noplaylist' : True,
    'nocheckcertificate' : True, 
    'ignoreerrors' : False, 
    'logtostderr' : False, 
    'quiet' : True, 
    'no_warnings' : True, 
    'default_search' : 'auto', 
    'source_address' : '0.0.0.0'
}

ffmeg_options = {
    'options' : '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

#YT volume transformer
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    # gets the filename for YT
    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename
        
@bot.command(name='join', help='Tells bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.voice))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
    
@bot.command(name='leave', help='To make bot leave channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("The bot is not connected to a voice channel.")
    

# func to pull quotes from website
def get_quote():
    response = requests.get("https://zenquotes.io/api/random")
    json_data = json.loads(response.text)
    quote = json_data[0]['q'] + ' - ' + json_data[0]['a']
    return(quote)

#lets discord server know bot has entered server
@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord')
    
# reads user input and will outputt hello
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
    
    if message.content.startswith('$butt'):
        await message.channel.send('butt hehe')
    
    #inspire quote command
    if message.content.startswith('$inspire'):
        quote = get_quote()
        await message.channel.send(quote)
    
    if message.content.startswith('$heh'):
        print('heh')
    
bot.run(TOKEN)