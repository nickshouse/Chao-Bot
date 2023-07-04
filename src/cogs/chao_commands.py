from discord.ext import commands
import asyncio
import random
import discord

class ChaoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(ChaoCommands(bot))
    print("Chao Commands cog loaded")
