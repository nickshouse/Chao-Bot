import datetime
import os
import pandas as pd
from discord.ext import commands
from collections import OrderedDict, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
        self.executor = ThreadPoolExecutor(max_workers=16)  # Adjusted max_workers

    async def get_file(self, filename):
        data = self.cache.get(filename)
        if data is None:
            async with self.locks[filename]:
                if os.path.exists(filename):
                    # Runs the I/O operation in a separate thread
                    loop = asyncio.get_running_loop()
                    data = await loop.run_in_executor(self.executor, pd.read_parquet, filename)
                    self.cache.put(filename, data)
        return data

    async def write_file(self, filename, data):
        async with self.locks[filename]:
            # Runs the I/O operation in a separate thread
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, data.to_parquet, filename)
            self.cache.put(filename, data)

    # ...rest of your methods remain the same...

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
