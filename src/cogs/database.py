import os
import pandas as pd
from discord.ext import commands
from collections import deque
import asyncio
from datetime import datetime

class Database(commands.Cog):
    def __init__(self, bot):
            self.bot = bot
            self.data_path = '../database'  
            os.makedirs(self.data_path, exist_ok=True)
 
 
async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
