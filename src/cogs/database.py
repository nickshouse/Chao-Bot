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

    async def get_inventory(self, guild_id, user_id):
        filename = f"{self.data_path}/{guild_id}_{user_id}.parquet"
        if os.path.exists(filename):
            df = pd.read_parquet(filename)
            return df
        return None

    async def store_inventory(self, guild_id, user_id, inventory):
        filename = f"{self.data_path}/{guild_id}_{user_id}.parquet"
        df = pd.DataFrame(inventory, columns=['time', 'type', 'value'])
        df.to_parquet(filename)
        
    # get_data and store_data methods

 
async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
