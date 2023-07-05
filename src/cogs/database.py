import datetime
import os
import shutil
import pandas as pd
from discord.ext import commands
from collections import OrderedDict, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time  # Import time for performance monitoring

class TimeAwareLRUCache:
    def __init__(self, capacity: int, ttl: int = 3600):
        self.capacity = capacity
        self.ttl = ttl  # Time-to-live in seconds
        self.cache = OrderedDict()

    def get(self, key):
        current_time = time.time()
        if key not in self.cache or current_time - self.cache[key][1] > self.ttl:
            return None
        self.cache.move_to_end(key)
        return self.cache[key][0]

    def put(self, key, value):
        current_time = time.time()
        self.cache[key] = (value, current_time)
        self.cache.move_to_end(key)
        while len(self.cache) > self.capacity:
            self.cache.popitem(last=False)


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_path = '../database'  
        os.makedirs(self.data_path, exist_ok=True)
        self.queues = defaultdict(asyncio.Queue)
        self.locks = defaultdict(asyncio.Lock)
        self.cache = TimeAwareLRUCache(500)  # TTL is 3600 seconds (1 hour) by default
        self.executor = ThreadPoolExecutor(max_workers=16)  # Adjusted max_workers
        self.tasks = {}  # To store worker tasks

    @tasks.loop(hours=1)
    async def backup_data(self):
        """Backup the database every hour."""
        backup_path = f"{self.data_path}_backup"
        shutil.rmtree(backup_path, ignore_errors=True)  # Delete any existing backup
        shutil.copytree(self.data_path, backup_path)  # Create a new backup
        print(f"Backup taken at {datetime.datetime.now()}")

    async def restore_backup(self):
        """Restore data from the backup."""
        backup_path = f"{self.data_path}_backup"
        if os.path.exists(backup_path):
            shutil.rmtree(self.data_path, ignore_errors=True)  # Delete current database
            shutil.copytree(backup_path, self.data_path)  # Replace with backup
            print("Backup restored")

    def cog_unload(self):
        """Clean up when the cog is unloaded."""
        self.backup_data.cancel()

    async def worker(self, filename):
        """A worker task that writes data from a queue to a file."""
        while True:
            data = await self.queues[filename].get()
            if data is None:  # We send None to stop the worker.
                break
            async with self.locks[filename]:  # Acquire the lock.
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self.executor, data.to_parquet, filename)
                self.cache.put(filename, data)

    async def write_file(self, filename, data):
        start_time = time.time()
        if filename not in self.tasks or self.tasks[filename].done():
            # Start a worker task if it's not already running.
            self.tasks[filename] = asyncio.create_task(self.worker(filename))
        await self.queues[filename].put(data)  # Put data into the queue.
        print(f"write_file operation took {(time.time() - start_time) * 1000} milliseconds")

    async def get_file(self, filename):
        start_time = time.time()  # Start the timer
        data = self.cache.get(filename)
        if data is None:
            async with self.locks[filename]:  # Acquire the lock.
                if os.path.exists(filename):
                    loop = asyncio.get_running_loop()
                    data = await loop.run_in_executor(self.executor, pd.read_parquet, filename)
                    self.cache.put(filename, data)
        print(f"get_file operation took {(time.time() - start_time) * 1000} milliseconds")
        return data
    
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
    db = Database(bot)
    await bot.add_cog(db)
    print("Database cog loaded")
    db.backup_data.start()
