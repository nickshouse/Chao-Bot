import datetime
import os
import pandas as pd
from discord.ext import commands
from collections import OrderedDict, defaultdict
import asyncio

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = OrderedDict()

    def get(self, key):
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = '../database'  
        os.makedirs(self.data_path, exist_ok=True)
        self.locks = defaultdict(asyncio.Lock)
        self.cache = LRUCache(500)

    async def get_file(self, filename):
        data = self.cache.get(filename)
        if data is None:
            async with self.locks[filename]:
                if os.path.exists(filename):
                    data = pd.read_parquet(filename)
                    self.cache.put(filename, data)
        return data

    async def write_file(self, filename, data):
        async with self.locks[filename]:
            data.to_parquet(filename)
            self.cache.put(filename, data)

    async def store_rings(self, guild_id, user_id, value):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/rings.parquet"
        df = pd.DataFrame([{'value': value}])
        await self.write_file(filename, df)

    async def get_rings(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/rings.parquet"
        df = await self.get_file(filename)
        return df['value'].sum() if df is not None else 0

    # ... Add other methods here, in the same pattern ...

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
