import os, discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

@bot.event
async def on_ready():
    for cog in ['cogs.chao', 'cogs.commands']:
        try:
            await bot.load_extension(cog)
            print(f'Loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')
    print(f'Connected as {bot.user.name}')

bot.run(os.getenv('DISCORD_TOKEN'))
