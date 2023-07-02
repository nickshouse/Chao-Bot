import asyncio
import os
import subprocess

import discord
from discord.ext import commands
from dotenv import load_dotenv

intents = discord.Intents.all()  # Set all intents if needed
bot = commands.Bot(command_prefix='$', intents=intents)  # Initialize bot

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

async def load_all_cogs():
    await bot.load_extension('cogs.database')
    await bot.load_extension('cogs.black_market')
    await bot.load_extension('cogs.fortune_teller')
    await bot.load_extension('cogs.chao_egg')
    await bot.load_extension('cogs.chao_stats')
    await bot.load_extension('cogs.chao_commands')

@bot.event
async def on_ready():
    print(f'We have connected as {bot.user.name}')
    bot.loop.create_task(load_all_cogs())

bot.run(token)  # Using the bot token from .env file
