import os
import pandas as pd
from datetime import datetime
from dateutil.parser import parse as date_parse
from discord.ext import commands

class DataUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def sanitize_folder_name(self, folder_name):
        """Sanitize the folder name to make it filesystem-safe."""
        return "".join([c if c.isalnum() or c in " -_()" else "_" for c in folder_name])

    def get_server_folder(self, guild_id, guild_name):
        """Constructs the folder path for a server, ensuring it includes the sanitized server name."""
        sanitized_name = self.sanitize_folder_name(guild_name)
        folder_name = f"{guild_id} ({sanitized_name})"
        return os.path.join(self.base_dir, '../../database', folder_name)

    def update_server_folder(self, guild):
        """Ensures the server folder matches the current server name and renames it if needed."""
        base_path = os.path.join(self.base_dir, '../../database')
        sanitized_name = self.sanitize_folder_name(guild.name)
        correct_folder_name = f"{guild.id} ({sanitized_name})"
        correct_path = os.path.join(base_path, correct_folder_name)

        # Find the current folder
        current_folder = next(
            (f for f in os.listdir(base_path) if f.startswith(str(guild.id))),
            None
        )

        if current_folder:
            current_path = os.path.join(base_path, current_folder)
            if current_folder != correct_folder_name:
                os.rename(current_path, correct_path)
        else:
            # Create the correct folder if it doesn't exist
            os.makedirs(correct_path, exist_ok=True)

        return correct_path

    def get_user_folder(self, guild_folder, user):
        """
        Constructs the folder path for a user, ensuring it includes their ID, account name, and display name.
        """
        # Ensure 'user' is a Member or User object
        if isinstance(user, str):  # If it's a user ID, resolve it to a Member object
            guild = self.bot.get_guild(int(guild_folder.split(" ")[0]))  # Extract guild ID from folder name
            user = guild.get_member(int(user)) if guild else None

        if not user or not hasattr(user, "name") or not hasattr(user, "display_name"):
            raise ValueError(f"Invalid user object: {user}")

        account_name = user.name
        display_name = user.display_name
        sanitized_account = self.sanitize_folder_name(account_name)
        sanitized_display = self.sanitize_folder_name(display_name)
        folder_name = f"{user.id} ({sanitized_account}) ({sanitized_display})"

        # Find the current folder if it exists
        current_folder = next(
            (f for f in os.listdir(guild_folder) if f.startswith(str(user.id))),
            None
        )

        correct_path = os.path.join(guild_folder, folder_name)

        # If the folder name doesn't match, rename it
        if current_folder:
            current_path = os.path.join(guild_folder, current_folder)
            if current_folder != folder_name:
                os.rename(current_path, correct_path)
        else:
            # Create the correct folder if it doesn't exist
            os.makedirs(correct_path, exist_ok=True)

        return correct_path

    def is_user_initialized(self, guild_id, guild_name, user):
        """
        Checks if a user is initialized by verifying the existence of their folder and database files
        with valid content (e.g., inventory).
        """
        guild_folder = self.update_server_folder(self.bot.get_guild(int(guild_id)))

        # Ensure user is a Member or User object
        if isinstance(user, str):
            guild = self.bot.get_guild(int(guild_id))
            user = guild.get_member(int(user)) if guild else None

        if not user or not hasattr(user, "name") or not hasattr(user, "display_name"):
            raise ValueError(f"Invalid user object or ID: {user}")

        # Check user folder
        user_folder = self.get_user_folder(guild_folder, user)
        if not os.path.exists(user_folder):
            return False

        # Check for meaningful inventory data
        inventory_path = os.path.join(user_folder, 'user_data', 'inventory.parquet')
        if not os.path.exists(inventory_path):
            return False

        inventory_df = self.load_inventory(inventory_path)
        if inventory_df.empty:
            return False

        latest_inventory = inventory_df.iloc[-1].to_dict()
        # If neither rings nor a Chao Egg is present, not initialized
        if not latest_inventory.get('rings') and not latest_inventory.get('Chao Egg'):
            return False

        return True

    def get_path(self, guild_id, guild_name, user, folder, filename):
        """Returns a path under server_folder -> user_folder -> folder -> filename."""
        guild_folder = self.update_server_folder(self.bot.get_guild(int(guild_id)))

        if isinstance(user, str):
            guild = self.bot.get_guild(int(guild_id))
            user = guild.get_member(int(user)) if guild else None

        if not user or not hasattr(user, "name") or not hasattr(user, "display_name"):
            raise ValueError(f"Invalid user object or ID: {user}")

        user_folder = self.get_user_folder(guild_folder, user)
        target_folder = os.path.join(user_folder, folder)   # <-- folder can be 'chao_data/Chow'
        os.makedirs(target_folder, exist_ok=True)
        return os.path.join(target_folder, filename)

    def save_inventory(self, path, inventory_df, current_inventory):
        """
        Saves the user's inventory to Parquet, either appending or overwriting today's row.
        """
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        current_inventory.setdefault('Chao Egg', 0)

        if not inventory_df.empty:
            if current_date_str in inventory_df['date'].values:
                index = inventory_df[inventory_df['date'] == current_date_str].index[0]
                for key, val in current_inventory.items():
                    if key != 'date':
                        inventory_df.at[index, key] = val
            else:
                current_inventory['date'] = current_date_str
                all_cols = ['date'] + sorted([c for c in current_inventory if c != 'date'])
                new_entry_df = pd.DataFrame([current_inventory])[all_cols]
                inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
        else:
            current_inventory['date'] = current_date_str
            all_cols = ['date'] + sorted([c for c in current_inventory if c != 'date'])
            inventory_df = pd.DataFrame([current_inventory])[all_cols]

        inventory_df.to_parquet(path, index=False)

    def load_inventory(self, path):
        if os.path.exists(path):
            inv_df = pd.read_parquet(path).fillna(0)
            cols = ['date'] + [col for col in inv_df.columns if col != 'date']
            inv_df = inv_df[cols]
            return inv_df
        else:
            return pd.DataFrame(columns=['date'])

    def save_chao_stats(self, chao_stats_path, chao_df, chao_stats):
        """
        Saves Chao stats for the current date, ensuring zero-padded date.
        Also forces any 'last_*_update' columns to be strings to avoid ArrowInvalid.
        """
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        new_entry = {**chao_stats, 'date': current_date_str}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]

        if not chao_df.empty and current_date_str in chao_df['date'].values:
            chao_df.loc[chao_df['date'] == current_date_str, columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True).fillna(0)

        # Force alignment as str if present
        if 'Alignment' in chao_df.columns:
            chao_df['Alignment'] = chao_df['Alignment'].astype(str)

        # Force all 'last_*_update' columns to string
        for col in chao_df.columns:
            if col.startswith("last_") and col.endswith("_update"):
                chao_df[col] = chao_df[col].astype(str)

        chao_df.to_parquet(chao_stats_path, index=False)

    def load_chao_stats(self, chao_stats_path):
        if os.path.exists(chao_stats_path):
            df = pd.read_parquet(chao_stats_path).fillna(0)
            columns = ['date'] + [c for c in df.columns if c != 'date']
            df = df[columns]
            return df
        else:
            return pd.DataFrame(columns=['date'])

    def _restore_parquet_data(self, df: pd.DataFrame, old_date: str) -> pd.DataFrame:
        if old_date not in df['date'].values:
            raise ValueError(f"No data found for {old_date}")

        restored_row = df.loc[df['date'] == old_date].iloc[0].to_dict()
        new_date_str = datetime.now().strftime("%Y-%m-%d")
        restored_row['date'] = new_date_str

        cols = ['date'] + [c for c in restored_row if c != 'date']
        new_entry_df = pd.DataFrame([restored_row])[cols]

        if new_date_str in df['date'].values:
            df.loc[df['date'] == new_date_str, cols[1:]] = new_entry_df.iloc[0][cols[1:]].values
        else:
            df = pd.concat([df, new_entry_df], ignore_index=True).fillna(0)
        return df

    async def restore(self, ctx, *, args: str):
        """
        $restore inventory YYYY-MM-DD
        $restore <ChaoName> YYYY-MM-DD
        """
        parts = args.rsplit(' ', 1)
        if len(parts) < 2:
            return await ctx.reply(
                "Usage:\n"
                "`$restore inventory YYYY-MM-DD`\n"
                "`$restore <chao_name> YYYY-MM-DD`"
            )

        target_raw, date_str_raw = parts[0], parts[1]

        # parse date
        try:
            parsed_date = date_parse(date_str_raw)
            date_str = parsed_date.strftime("%Y-%m-%d")
        except:
            return await ctx.reply("Please provide a valid date (YYYY-MM-DD).")

        guild_id, user = ctx.guild.id, ctx.author

        if target_raw.lower() == 'inventory':
            # inventory restore
            file_path = self.get_path(guild_id, ctx.guild.name, user,
                                      'user_data',
                                      'inventory.parquet')
            inv_df = self.load_inventory(file_path)
            try:
                updated = self._restore_parquet_data(inv_df, date_str)
            except ValueError:
                return await ctx.reply(f"No inventory data found for {date_str}.")
            updated.to_parquet(file_path, index=False)
            return await ctx.reply(f"Inventory restored to {date_str}")

        # else: treat as Chao name
        chao_name = target_raw
        # *** Here's the CRITICAL difference: add 'chao_name' as a subfolder ***
        # so the file path is chao_data/Chow/Chow_stats.parquet
        chao_stats_path = self.get_path(
            guild_id,
            ctx.guild.name,
            user,
            os.path.join('chao_data', chao_name),  # <== Subfolder named after the Chao
            f"{chao_name}_stats.parquet"
        )
        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"No Chao stats file found for {chao_name}.")

        chao_df = self.load_chao_stats(chao_stats_path)
        try:
            updated_chao_df = self._restore_parquet_data(chao_df, date_str)
        except ValueError:
            return await ctx.reply(f"No Chao data found for {chao_name} on {date_str}.")

        updated_chao_df.to_parquet(chao_stats_path, index=False)
        return await ctx.reply(f"{chao_name} restored to {date_str}.")


async def setup(bot):
    await bot.add_cog(DataUtils(bot))
