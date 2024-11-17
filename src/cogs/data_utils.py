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
        # Ensure 'date' is set to current_date_str, overriding any existing 'date' in current_inventory
        new_entry = {**current_inventory, 'date': current_date_str}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]

        # Check if there is an existing entry for the current date
        if current_date_str in inventory_df['date'].values:
            # Update the existing entry for the current date
            inventory_df.loc[inventory_df['date'] == current_date_str, columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            # Append the new entry
            inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)

        # Save the updated DataFrame
        inventory_df.to_parquet(path, index=False)

    def load_inventory(self, path):
        if os.path.exists(path):
            inventory_df = pd.read_parquet(path).fillna(0)
            columns = ['date'] + [col for col in inventory_df.columns if col != 'date']
            inventory_df = inventory_df[columns]
            return inventory_df
        else:
            current_date_str = datetime.now().date().strftime("%Y-%m-%d")
            return pd.DataFrame({
                'date': [current_date_str],
                'rings': [0], 'Chao Egg': [0], 'Garden Fruit': [0]
            })

    def is_user_initialized(self, guild_id, user_id):
        return os.path.exists(
            os.path.join(
                self.base_dir, '../../database', guild_id, user_id))

    def save_chao_stats(self, chao_stats_path, chao_df, chao_stats):
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        # Ensure 'date' is set to current_date_str, overriding any existing 'date' in chao_stats
        new_entry = {**chao_stats, 'date': current_date_str}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]

        # Check if there is an existing entry for the current date
        if current_date_str in chao_df['date'].values:
            # Update the existing entry for the current date
            chao_df.loc[chao_df['date'] == current_date_str, columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            # Append the new entry
            chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True).fillna(0)

        # Save the updated DataFrame
        chao_df.to_parquet(chao_stats_path, index=False)

    def load_chao_stats(self, chao_stats_path):
        if os.path.exists(chao_stats_path):
            chao_df = pd.read_parquet(chao_stats_path).fillna(0)
            columns = ['date'] + [col for col in chao_df.columns if col != 'date']
            chao_df = chao_df[columns]
            return chao_df
        else:
            return pd.DataFrame(columns=['date'])

async def setup(bot):
    await bot.add_cog(DataUtils(bot))
