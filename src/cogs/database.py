import datetime
import os
import pandas as pd
from discord.ext import commands
from collections import deque
import asyncio
from functools import lru_cache

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = '../database'  
        os.makedirs(self.data_path, exist_ok=True)
        self.lock = asyncio.Lock()

    async def store_rings(self, guild_id, user_id, value):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            os.makedirs(dir_path, exist_ok=True)
            filename = f"{dir_path}/rings.parquet"
            df = pd.DataFrame([{'value': value}])
            df.to_parquet(filename)

    @lru_cache(maxsize=None)
    async def get_rings(self, guild_id, user_id):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            filename = f"{dir_path}/rings.parquet"
            if os.path.exists(filename):
                df = pd.read_parquet(filename)
                return df['value'].sum()
            return 0  # return 0 if the file doesn't exist

    async def store_inventory(self, guild_id, user_id, inventory):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            os.makedirs(dir_path, exist_ok=True)
            filename = f"{dir_path}/inventory.parquet"
            df = pd.DataFrame(inventory, columns=['quantity', 'item'])
            df.to_parquet(filename)

    @lru_cache(maxsize=None)
    async def get_inventory(self, guild_id, user_id):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            filename = f"{dir_path}/inventory.parquet"
            if os.path.exists(filename):
                df = pd.read_parquet(filename)
                return df
            return None

    async def store_chao(self, guild_id, user_id, chao):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
            os.makedirs(dir_path, exist_ok=True)
            filename = f"{dir_path}/{chao['name']}.parquet"
            if os.path.exists(filename):  # If the chao already exists, we need to update it
                df = pd.read_parquet(filename)
                df.update(pd.DataFrame(chao, index=[0]))
            else:  # If it's a new chao, we create it
                df = pd.DataFrame(chao, index=[0])
            df.to_parquet(filename, index=False)  # Don't save the index in the parquet file

    @lru_cache(maxsize=None)
    async def get_chao(self, guild_id, user_id):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
            chao = []
            for file in os.listdir(dir_path):
                if file.endswith(".parquet"):
                    df = pd.read_parquet(f"{dir_path}/{file}")
                    chao_dict = df.to_dict(orient='records')[0]
                    if 'name' in chao_dict:
                        chao.append(chao_dict)
            return chao


    async def store_nickname(self, guild_id, user_id, nickname):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            os.makedirs(dir_path, exist_ok=True)
            filename = f"{dir_path}/nicknames.parquet"
            new_data = pd.DataFrame([{'time': datetime.datetime.now(), 'nickname': nickname}])
            if os.path.exists(filename):
                df = pd.read_parquet(filename)
                df = df.append(new_data, ignore_index=True)
            else:
                df = new_data
            df.to_parquet(filename, index=False)

    @lru_cache(maxsize=None)
    async def get_nickname(self, guild_id, user_id):
        async with self.lock:
            dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
            filename = f"{dir_path}/nicknames.parquet"
            if os.path.exists(filename):
                df = pd.read_parquet(filename)
                return df
            return None
    

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
