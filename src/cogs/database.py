import datetime
import os
import pandas as pd
from discord.ext import commands
from collections import OrderedDict, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time  # Import time for performance monitoring

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
        start_time = time.time()  # Start the timer
        data = self.cache.get(filename)
        if data is None:
            async with self.locks[filename]:
                if os.path.exists(filename):
                    loop = asyncio.get_running_loop()
                    data = await loop.run_in_executor(self.executor, pd.read_parquet, filename)
                    self.cache.put(filename, data)
        print(f"get_file operation took {time.time() - start_time} seconds")  # Print the elapsed time
        return data

    async def write_file(self, filename, data):
        start_time = time.time()  # Start the timer
        async with self.locks[filename]:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(self.executor, data.to_parquet, filename)
            self.cache.put(filename, data)
        print(f"write_file operation took {time.time() - start_time} seconds")  # Print the elapsed time

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

    async def store_inventory(self, guild_id, user_id, inventory):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/inventory.parquet"
        df = pd.DataFrame(inventory, columns=['quantity', 'item'])
        await self.write_file(filename, df)

    async def get_inventory(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/inventory.parquet"
        return await self.get_file(filename)

    async def store_chao(self, guild_id, user_id, chao):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/{chao['name']}.parquet"
        df = await self.get_file(filename)
        if df is not None:  # If the chao already exists, we need to update it
            df.update(pd.DataFrame(chao, index=[0]))
        else:  # If it's a new chao, we create it
            df = pd.DataFrame(chao, index=[0])
        await self.write_file(filename, df)

    async def get_chao(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
        chao = []
        for file in os.listdir(dir_path):
            if file.endswith(".parquet"):
                df = await self.get_file(f"{dir_path}/{file}")
                chao_dict = df.to_dict(orient='records')[0]
                if 'name' in chao_dict:
                    chao.append(chao_dict)
        return chao

    async def store_nickname(self, guild_id, user_id, nickname):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/nicknames.parquet"
        df = await self.get_file(filename)
        new_data = pd.DataFrame([{'time': datetime.datetime.now(), 'nickname': nickname}])
        if df is not None:
            df = df.append(new_data, ignore_index=True)
        else:
            df = new_data
        await self.write_file(filename, df)

    async def get_nickname(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/nicknames.parquet"
        return await self.get_file(filename)

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
