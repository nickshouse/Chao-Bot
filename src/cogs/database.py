import datetime
import os
import shutil
import pandas as pd
import errno
from discord.ext import commands, tasks
from collections import OrderedDict, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

import pytz  # Import time for performance monitoring

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
        now = datetime.datetime.now(pytz.timezone('US/Central'))
        print(f"Backup taken at {now.strftime('%m-%d-%Y %I:%M:%S %p')}")

    @backup_data.before_loop
    async def before_backup_data(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready
        await asyncio.sleep(3600)  # Wait for 1 hour before the first run


    def handle_error(func, path, exc_info):
        if not os.path.isdir(path):
            raise

    async def restore_backup(self):
        """Restore data from the backup."""
        backup_path = f"{self.data_path}_backup"
        if os.path.exists(backup_path):
            for filename in os.listdir(self.data_path):  # Delete current database content
                file_path = os.path.join(self.data_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
            try:
                shutil.copytree(backup_path, self.data_path, dirs_exist_ok=True)
            except Exception as e:
                print(f"Failed to copy {backup_path} to {self.data_path}. Reason: {e}")
            else:
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
        
    async def store_inventory(self, guild_id, user_id, inventory_df):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/inventory.parquet"

        # Read the existing inventory
        existing_inventory_df = await self.get_file(filename)
        
        if existing_inventory_df is not None:
            for index, row in inventory_df.iterrows():
                item_name = row['item']
                # Check if the item already exists in the inventory
                existing_item_index = existing_inventory_df.index[existing_inventory_df['item'] == item_name]
                if not existing_item_index.empty:
                    # Set the quantity directly if the item already exists
                    existing_inventory_df.at[existing_item_index[0], 'quantity'] = row['quantity']
                else:
                    # Append a new row if the item doesn't exist
                    new_row_df = pd.DataFrame([row])
                    existing_inventory_df = pd.concat([existing_inventory_df, new_row_df], ignore_index=True)
            final_df = existing_inventory_df
        else:
            final_df = inventory_df  # If no existing inventory, use the new inventory data
        
        await self.write_file(filename, final_df)

    async def get_inventory(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/inventory.parquet"
        return await self.get_file(filename)

    async def store_chao(self, guild_id, user_id, chao):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/chao_data.parquet"

        # Retrieve the existing Chao data
        existing_chao_df = await self.get_file(filename)

        if existing_chao_df is not None:
            # Check if the Chao already exists and update it
            chao_index = existing_chao_df.index[existing_chao_df['name'] == chao['name']]
            if not chao_index.empty:
                print(f"Updating Chao: {chao}")  # Debug print
                for key, value in chao.items():
                    existing_chao_df.at[chao_index[0], key] = value
                final_df = existing_chao_df
            else:
                # Append the new Chao data
                new_row_df = pd.DataFrame([chao])
                final_df = pd.concat([existing_chao_df, new_row_df], ignore_index=True)
        else:
            # Create a new DataFrame for the Chao data
            final_df = pd.DataFrame([chao])

        await self.write_file(filename, final_df)




    async def get_chao(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/chao_data"
        filename = f"{dir_path}/chao_data.parquet"

        if not os.path.exists(filename):
            return []

        df = await self.get_file(filename)
        return df.to_dict(orient='records')


    async def store_nickname(self, guild_id, user_id, nickname):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/nicknames.parquet"
        df = await self.get_file(filename)
        new_data = pd.DataFrame([{'time': datetime.datetime.now(), 'nickname': nickname}])
        if df is not None:
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df = new_data
        await self.write_file(filename, df)

    async def get_nickname(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/nicknames.parquet"
        return await self.get_file(filename)
    
    async def store_username(self, guild_id, user_id, username):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        os.makedirs(dir_path, exist_ok=True)
        filename = f"{dir_path}/usernames.parquet"
        df = await self.get_file(filename)
        new_data = pd.DataFrame([{'time': datetime.datetime.now(), 'username': username}])
        if df is not None:
            df = pd.concat([df, new_data], ignore_index=True)
        else:
            df = new_data
        await self.write_file(filename, df)

    async def get_username(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}/user_data"
        filename = f"{dir_path}/usernames.parquet"
        return await self.get_file(filename)
    
    async def initialize_user_data(self, guild_id, user_id):
        user_dir_path = f"{self.data_path}/{guild_id}/{user_id}"
        os.makedirs(user_dir_path, exist_ok=True)
        # Here you can create and initialize directories and files as needed
        # For example, create empty parquet files for chao, inventory, etc.

    
    async def is_user_initialized(self, guild_id, user_id):
        dir_path = f"{self.data_path}/{guild_id}/{user_id}"
        return os.path.exists(dir_path)


async def setup(bot):
    db = Database(bot)
    await bot.add_cog(db)
    print("Database cog loaded")
    db.backup_data.start()
