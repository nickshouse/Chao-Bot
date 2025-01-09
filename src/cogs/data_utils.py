import os
import pandas as pd
from datetime import datetime
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

        account_name = user.name  # The account's username
        display_name = user.display_name  # The display name (may differ from account name)
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
        guild_folder = self.update_server_folder(guild=self.bot.get_guild(int(guild_id)))

        # Ensure user is a Member or User object
        if isinstance(user, str):  # If it's a user ID, resolve it
            guild = self.bot.get_guild(int(guild_id))
            user = guild.get_member(int(user)) if guild else None

        if not user or not hasattr(user, "name") or not hasattr(user, "display_name"):
            raise ValueError(f"Invalid user object or ID: {user}")

        # Check for user folder
        user_folder = self.get_user_folder(guild_folder, user)
        if not os.path.exists(user_folder):
            return False

        # Check for meaningful inventory data
        inventory_path = os.path.join(user_folder, 'user_data', 'inventory.parquet')
        if not os.path.exists(inventory_path):
            return False

        inventory_df = self.load_inventory(inventory_path)
        if inventory_df.empty:
            return False  # No inventory data found

        # Verify if the inventory contains at least one meaningful item (e.g., Rings or Chao Egg)
        latest_inventory = inventory_df.iloc[-1].to_dict()
        if not latest_inventory.get('rings') and not latest_inventory.get('Chao Egg'):
            return False

        # User is initialized if they have valid inventory data
        return True

    #
    # ------------------------------
    # IMPORTANT: The function below:
    # ------------------------------
    #
    def get_path(self, guild_id, guild_name, user, folder, filename):
        """
        Gets the full path for a specific file, ensuring both server and user folders are correct.
        Expects 5 arguments: (guild_id, guild_name, user, folder, filename).
        """
        guild_folder = self.update_server_folder(guild=self.bot.get_guild(int(guild_id)))

        # Ensure user is a Member or User object
        if isinstance(user, str):  # If it's a user ID, resolve it
            guild = self.bot.get_guild(int(guild_id))
            user = guild.get_member(int(user)) if guild else None

        if not user or not hasattr(user, "name") or not hasattr(user, "display_name"):
            raise ValueError(f"Invalid user object or ID: {user}")

        user_folder = self.get_user_folder(guild_folder, user)
        target_folder = os.path.join(user_folder, folder)
        os.makedirs(target_folder, exist_ok=True)
        return os.path.join(target_folder, filename)
    #
    # ------------------------------
    #

    def save_inventory(self, path, inventory_df, current_inventory):
        """
        Save the inventory to the specified Parquet file. Ensures no duplicate rows with the same date.
        If a row with the current date exists, updates it. Otherwise, appends a new row.
        """
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        current_inventory.setdefault('Chao Egg', 0)

        # If inventory_df is not empty, update the current row if today's date exists
        if not inventory_df.empty:
            if current_date_str in inventory_df['date'].values:
                # Update the existing row for today's date
                index = inventory_df[inventory_df['date'] == current_date_str].index[0]
                for key, value in current_inventory.items():
                    if key != 'date':  # Don't overwrite the date column
                        inventory_df.at[index, key] = value
            else:
                # Add a new row for today's date
                current_inventory['date'] = current_date_str
                all_columns = ['date'] + sorted([col for col in current_inventory if col != 'date'])
                new_entry_df = pd.DataFrame([current_inventory])[all_columns]
                inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
        else:
            # Create a new DataFrame with the current inventory
            current_inventory['date'] = current_date_str
            all_columns = ['date'] + sorted([col for col in current_inventory if col != 'date'])
            inventory_df = pd.DataFrame([current_inventory])[all_columns]

        # Save the updated inventory to the Parquet file
        inventory_df.to_parquet(path, index=False)

    def load_inventory(self, path):
        if os.path.exists(path):
            inventory_df = pd.read_parquet(path).fillna(0)
            columns = ['date'] + [col for col in inventory_df.columns if col != 'date']
            inventory_df = inventory_df[columns]
            return inventory_df
        else:
            return pd.DataFrame(columns=['date'])

    def save_chao_stats(self, chao_stats_path, chao_df, chao_stats):
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        new_entry = {**chao_stats, 'date': current_date_str}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]

        if not chao_df.empty and current_date_str in chao_df['date'].values:
            chao_df.loc[chao_df['date'] == current_date_str, columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True).fillna(0)

        # --- Fix schema mismatch here ---
        if 'Alignment' in chao_df.columns:
            chao_df['Alignment'] = chao_df['Alignment'].astype(str)

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
            return await ctx.reply(f"{ctx.author.mention}, please use the command in the format: `$restore inventory YYYY-MM-DD`")
        date_str = parts[1]
        guild_id, user = ctx.guild.id, ctx.author
        file_path = self.get_path(guild_id, ctx.guild.name, user, 'user_data', 'inventory.parquet')
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return await ctx.reply(f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")
        inventory_df = self.load_inventory(file_path)
        if date_str not in inventory_df['date'].values:
            return await ctx.reply(f"{ctx.author.mention}, no inventory data found for {date_str}.")
        restored_inventory = inventory_df[inventory_df['date'] == date_str].iloc[0].to_dict()
        restored_inventory['date'] = datetime.now().date().strftime("%Y-%m-%d")
        columns = ['date'] + [col for col in restored_inventory if col != 'date']
        new_entry_df = pd.DataFrame([restored_inventory])[columns]
        if restored_inventory['date'] in inventory_df['date'].values:
            inventory_df.loc[inventory_df['date'] == restored_inventory['date'], columns[1:]] = new_entry_df.iloc[0][columns[1:]].values
        else:
            inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
        inventory_df.to_parquet(file_path, index=False)
        await ctx.reply(f"{ctx.author.mention}, your inventory has been restored to the state from {date_str}.")

async def setup(bot):
    await bot.add_cog(DataUtils(bot))
