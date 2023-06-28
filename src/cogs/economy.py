import discord
from discord.ext import commands
from discord import Embed
import pandas as pd

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_cog = self.bot.get_cog("Database")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        guild_id = message.guild.id
        user_id = str(message.author.id)
        data_type = 'rings'
        user_data = await self.database_cog.get_data(guild_id, user_id, data_type)

        if user_data is None:
            await self.database_cog.store_data(guild_id, user_id, [(100, data_type)])
        else:
            await self.database_cog.store_data(guild_id, user_id, [(10, data_type)])

async def setup(bot):
    await bot.add_cog(Economy(bot))
    print("Economy cog loaded")
