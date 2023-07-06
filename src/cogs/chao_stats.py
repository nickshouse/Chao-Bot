from discord.ext import commands
import random

class ChaoStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_cog = self.bot.get_cog("Database")

    

async def setup(bot):
    await bot.add_cog(ChaoStats(bot))
    print("Chao Stats cog loaded")
