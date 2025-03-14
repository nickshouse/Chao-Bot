# cogs/chao_transfer.py

import os
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks

class ChaoTransporter(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_utils = None

    async def cog_load(self):
        self.data_utils = self.bot.get_cog("DataUtils")
        if not self.data_utils:
            raise RuntimeError("DataUtils cog not found. Load DataUtils before ChaoDecay.")


async def setup(bot):
    await bot.add_cog(ChaoTransporter(bot))
