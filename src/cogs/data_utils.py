import os
import pandas as pd
from datetime import datetime
from discord.ext import commands

class DataUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def get_path(self, guild_id, user_id, folder, filename):
        base = os.path.join(
            self.base_dir, '../../database', guild_id, user_id, folder)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    def save_inventory(self, path, inventory_df, current_inventory):
        current_inventory.setdefault('Chao Egg', 0)
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        if not inventory_df.empty:
            latest_inventory = inventory_df.iloc[-1].to_dict()
            for key, value in latest_inventory.items():
                if key not in current_inventory and key != 'date':
                    current_inventory[key] = value
        current_inventory['date'] = current_date_str
        all_columns = ['date'] + sorted([col for col in current_inventory if col != 'date'])
        new_entry_df = pd.DataFrame([current_inventory])[all_columns]
        inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
        inventory_df.to_parquet(path, index=False)

    def load_inventory(self, path):
        if os.path.exists(path):
            inventory_df = pd.read_parquet(path).fillna(0)
            columns = ['date'] + [col for col in inventory_df.columns if col != 'date']
            inventory_df = inventory_df[columns]
            return inventory_df
        else:
            return pd.DataFrame(columns=['date'])

    def is_user_initialized(self, guild_id, user_id):
        return os.path.exists(
            os.path.join(
                self.base_dir, '../../database', guild_id, user_id))

    def save_chao_stats(self, chao_stats_path, chao_df, chao_stats):
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        new_entry = {**chao_stats, 'date': current_date_str}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]
        if current_date_str in chao_df['date'].values:
            chao_df.loc[chao_df['date'] == current_date_str, columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True).fillna(0)
        chao_df.to_parquet(chao_stats_path, index=False)

    def load_chao_stats(self, chao_stats_path):
        if os.path.exists(chao_stats_path):
            chao_df = pd.read_parquet(chao_stats_path).fillna(0)
            columns = ['date'] + [col for col in chao_df.columns if col != 'date']
            chao_df = chao_df[columns]
            return chao_df
        else:
            return pd.DataFrame(columns=['date'])

    async def restore(self, ctx, *, args: str):
        parts = args.split()
        if len(parts) != 2 or parts[0].lower() != 'inventory':
            return await ctx.send(f"{ctx.author.mention}, please use the command in the format: `$restore inventory YYYY-MM-DD`")
        date_str = parts[1]
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        file_path = self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return await ctx.send(f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")
        inventory_df = self.load_inventory(file_path)
        if date_str not in inventory_df['date'].values:
            return await ctx.send(f"{ctx.author.mention}, no inventory data found for {date_str}.")
        restored_inventory = inventory_df[inventory_df['date'] == date_str].iloc[0].to_dict()
        restored_inventory['date'] = datetime.now().date().strftime("%Y-%m-%d")
        columns = ['date'] + [col for col in restored_inventory if col != 'date']
        new_entry_df = pd.DataFrame([restored_inventory])[columns]
        if restored_inventory['date'] in inventory_df['date'].values:
            inventory_df.loc[inventory_df['date'] == restored_inventory['date'], columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
        inventory_df.to_parquet(file_path, index=False)
        await ctx.send(f"{ctx.author.mention}, your inventory has been restored to the state from {date_str}.")

async def setup(bot):
    await bot.add_cog(DataUtils(bot))
