import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the bot with a command prefix and intents
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

async def load_all_cogs():
    cogs = [
        'cogs.chao',     # Load the Chao cog first as Commands cog depends on it
        'cogs.commands', # Load the Commands cog
        
    ]
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f'Successfully loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}.', e)

@bot.event
async def on_ready():
    await load_all_cogs()
    print(f'We have connected as {bot.user.name}')

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_TOKEN'))
