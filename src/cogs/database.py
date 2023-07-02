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

    async def get_rings(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/rings.parquet"
        if os.path.exists(filename):
            df = pd.read_parquet(filename)
            return df
        return None

    async def store_rings(self, guild_id, user_id, value):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/rings.parquet"
        df = pd.DataFrame([{'time': datetime.now(), 'value': value}])
        df.to_parquet(filename)

    async def get_inventory(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/inventory.parquet"
        if os.path.exists(filename):
            df = pd.read_parquet(filename)
            return df
        return None

    async def store_inventory(self, guild_id, user_id, inventory):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/inventory.parquet"
        df = pd.DataFrame(inventory, columns=['time', 'type', 'value'])
        df.to_parquet(filename)

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
