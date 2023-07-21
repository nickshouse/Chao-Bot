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
    await bot.load_extension('cogs.logger')
    await bot.load_extension('cogs.database')
    await bot.load_extension('cogs.black_market')
    await bot.load_extension('cogs.fortune_teller')
    await bot.load_extension('cogs.chao')

@bot.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        # The member's nickname has changed, store the new one.
        guild_id = after.guild.id
        user_id = after.id
        new_nickname = after.nick
        await bot.get_cog("Database").store_nickname(guild_id, user_id, new_nickname)

@bot.event
async def on_ready():
    print(f'We have connected as {bot.user.name}')
    bot.loop.create_task(load_all_cogs())

@bot.command()
async def restore_backup(ctx):
    await bot.get_cog("Database").restore_backup()
    await ctx.send("Backup restored!")

bot.run(token)  # Using the bot token from .env file
