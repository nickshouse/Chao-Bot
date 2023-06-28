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
            self.states_path = os.path.join(self.data_path, 'states')
            os.makedirs(self.states_path, exist_ok=True)
            self.data_queue = deque()
            self.locks = {}
            self.bot.loop.create_task(self.process_data_queue())
            self.bot.loop.create_task(self.save_state_periodically())
            self.bot.loop.create_task(self.create_database_files())

    async def process_data_queue(self):
        while True:
            tasks = [self.process_queue_item() for _ in range(10)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.1)

    async def process_queue_item(self):
        if self.data_queue:
            guild_id, user_id, data, data_type = self.data_queue.popleft()
            if (guild_id, user_id) not in self.locks:
                self.locks[(guild_id, user_id)] = asyncio.Lock()

            async with self.locks[(guild_id, user_id)]:
                items_for_user = [(data, data_type)]
                for i in range(len(self.data_queue) - 1, -1, -1):
                    if self.data_queue[i][:2] == (guild_id, user_id):
                        items_for_user.append(self.data_queue[i][2:])
                        del self.data_queue[i]

                await self.store_data(guild_id, user_id, items_for_user)

    async def store_data(self, guild_id, user_id, items):
        guild_folder = os.path.join(self.data_path, str(guild_id))
        os.makedirs(guild_folder, exist_ok=True)
        file_path = os.path.join(guild_folder, f'{user_id}.parquet')

        df = pd.DataFrame({data_type: [data] for data, data_type in items})

        if os.path.exists(file_path):
            old_data = pd.read_parquet(file_path, engine='pyarrow')
            df = pd.concat([old_data, df], ignore_index=True)
        else:
            df = df
        df.to_parquet(file_path, engine='pyarrow')

    async def get_data(self, guild_id, user_id, data_type):
        file_path = os.path.join(self.data_path, str(guild_id), f'{user_id}.parquet')

        if os.path.exists(file_path):
            df = pd.read_parquet(file_path, engine='pyarrow')
            if data_type in df.columns:
                return df[[data_type]]  
        return pd.DataFrame()  # return an empty DataFrame if no data exists


    async def save_state_periodically(self):
        while True:
            await asyncio.sleep(10)
            state_path = os.path.join(self.states_path, f"{datetime.now().isoformat().replace(':', '-')}.parquet")
            state_data = pd.DataFrame(list(self.data_queue), columns=['guild_id', 'user_id', 'data', 'data_type'])
            state_data.to_parquet(state_path, engine='pyarrow')

            # Delete the oldest state file if there are more than 1000
            state_files = sorted(os.listdir(self.states_path))
            if len(state_files) > 1000:
                oldest_state_file = state_files[0]
                os.remove(os.path.join(self.states_path, oldest_state_file))
    
    async def create_database_files(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            guild_folder = os.path.join(self.data_path, guild_id)
            os.makedirs(guild_folder, exist_ok=True)
            for member in guild.members:
                user_id = str(member.id)
                file_path = os.path.join(guild_folder, f'{user_id}.parquet')
                if not os.path.exists(file_path):
                    df = pd.DataFrame()
                    df.to_parquet(file_path, engine='pyarrow')

async def setup(bot):
    await bot.add_cog(Database(bot))
    print("Database cog loaded")
