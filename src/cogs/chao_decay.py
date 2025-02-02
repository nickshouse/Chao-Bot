# cogs/chao_decay.py
import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

class ChaoDecay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_utils = None

        # Default decay settings (from chao_helper originally)
        self.belly_decay_amount = 1
        self.belly_decay_minutes = 180

        self.happiness_decay_amount = 1
        self.happiness_decay_minutes = 240

        self.energy_decay_amount = 2
        self.energy_decay_minutes = 240

        self.hp_decay_amount = 1
        self.hp_decay_minutes = 720

        # Start decay loops
        self.force_belly_decay_loop.start()
        self.force_happiness_decay_loop.start()
        self.force_energy_decay_loop.start()
        self.force_hp_decay_loop.start()

    async def cog_load(self):
        """
        Runs after the cog is fully loaded.
        Fetch required cogs (like DataUtils).
        """
        self.data_utils = self.bot.get_cog("DataUtils")
        if not self.data_utils:
            raise RuntimeError("DataUtils cog not found. Make sure DataUtils is loaded before ChaoDecay.")

    def cog_unload(self):
        """Cancel loops on cog unload."""
        self.force_belly_decay_loop.cancel()
        self.force_happiness_decay_loop.cancel()
        self.force_energy_decay_loop.cancel()
        self.force_hp_decay_loop.cancel()

    # ----------------------------------------------------------------------
    # BELLY DECAY
    # ----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_belly_decay_loop(self):
        """Every minute, subtract belly ticks based on elapsed time."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue
            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[0].isdigit():
                    continue
                user_path = os.path.join(server_folder, user_folder_name)
                chao_data_dir = os.path.join(user_path, "chao_data")
                if not os.path.exists(chao_data_dir):
                    continue
                for chao_name in os.listdir(chao_data_dir):
                    stats_file = os.path.join(chao_data_dir, chao_name, f"{chao_name}_stats.parquet")
                    if not os.path.exists(stats_file):
                        continue
                    df = self.data_utils.load_chao_stats(stats_file)
                    if df.empty:
                        continue
                    latest_stats = df.iloc[-1].to_dict()

                    if "last_belly_update" not in latest_stats:
                        latest_stats["last_belly_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    try:
                        old_time = datetime.strptime(latest_stats["last_belly_update"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        latest_stats["last_belly_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    now = datetime.now()
                    passed_minutes = int((now - old_time).total_seconds() // 60)
                    blocks = passed_minutes // self.belly_decay_minutes
                    if blocks > 0:
                        old_val = latest_stats.get("belly_ticks", 0)
                        reduce_amount = self.belly_decay_amount * blocks
                        new_val = max(0, old_val - reduce_amount)
                        latest_stats["belly_ticks"] = new_val

                        used_time = old_time + timedelta(minutes=(blocks * self.belly_decay_minutes))
                        if used_time > now:
                            used_time = now
                        latest_stats["last_belly_update"] = used_time.strftime("%Y-%m-%d %H:%M:%S")

                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    async def before_force_belly_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] force_belly_decay_loop is starting up...")
    force_belly_decay_loop.before_loop = before_force_belly_decay_loop

    async def force_belly_decay(self, ctx, ticks: int, minutes: int):
        """Admin command to update belly decay settings."""
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")
        self.belly_decay_amount = ticks
        self.belly_decay_minutes = minutes
        await ctx.reply(
            f"Belly decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    # ----------------------------------------------------------------------
    # ENERGY DECAY
    # ----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_energy_decay_loop(self):
        """Every minute, subtract energy ticks based on elapsed time."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue
            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[0].isdigit():
                    continue
                user_path = os.path.join(server_folder, user_folder_name)
                chao_data_dir = os.path.join(user_path, "chao_data")
                if not os.path.exists(chao_data_dir):
                    continue
                for chao_name in os.listdir(chao_data_dir):
                    stats_file = os.path.join(chao_data_dir, chao_name, f"{chao_name}_stats.parquet")
                    if not os.path.exists(stats_file):
                        continue
                    df = self.data_utils.load_chao_stats(stats_file)
                    if df.empty:
                        continue
                    latest_stats = df.iloc[-1].to_dict()

                    if "last_energy_update" not in latest_stats:
                        latest_stats["last_energy_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    try:
                        old_time = datetime.strptime(latest_stats["last_energy_update"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        latest_stats["last_energy_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    now = datetime.now()
                    passed_minutes = int((now - old_time).total_seconds() // 60)
                    blocks = passed_minutes // self.energy_decay_minutes
                    if blocks > 0:
                        old_val = latest_stats.get("energy_ticks", 0)
                        reduce_amount = self.energy_decay_amount * blocks
                        new_val = max(0, old_val - reduce_amount)
                        latest_stats["energy_ticks"] = new_val

                        used_time = old_time + timedelta(minutes=(blocks * self.energy_decay_minutes))
                        if used_time > now:
                            used_time = now
                        latest_stats["last_energy_update"] = used_time.strftime("%Y-%m-%d %H:%M:%S")

                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    async def before_force_energy_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] force_energy_decay_loop is starting up...")
    force_energy_decay_loop.before_loop = before_force_energy_decay_loop

    async def force_energy_decay(self, ctx, ticks: int, minutes: int):
        """Admin command to update energy decay settings."""
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")
        self.energy_decay_amount = ticks
        self.energy_decay_minutes = minutes
        await ctx.reply(
            f"Energy decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    # ----------------------------------------------------------------------
    # HAPPINESS DECAY
    # ----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_happiness_decay_loop(self):
        """Every minute, subtract happiness ticks based on elapsed time."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue
            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[0].isdigit():
                    continue
                user_path = os.path.join(server_folder, user_folder_name)
                chao_data_dir = os.path.join(user_path, "chao_data")
                if not os.path.exists(chao_data_dir):
                    continue
                for chao_name in os.listdir(chao_data_dir):
                    stats_file = os.path.join(chao_data_dir, chao_name, f"{chao_name}_stats.parquet")
                    if not os.path.exists(stats_file):
                        continue
                    df = self.data_utils.load_chao_stats(stats_file)
                    if df.empty:
                        continue
                    latest_stats = df.iloc[-1].to_dict()

                    if "last_happiness_update" not in latest_stats:
                        latest_stats["last_happiness_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    try:
                        old_time = datetime.strptime(latest_stats["last_happiness_update"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        latest_stats["last_happiness_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    now = datetime.now()
                    passed_minutes = int((now - old_time).total_seconds() // 60)
                    blocks = passed_minutes // self.happiness_decay_minutes
                    if blocks > 0:
                        old_val = latest_stats.get("happiness_ticks", 0)
                        reduce_amount = self.happiness_decay_amount * blocks
                        new_val = max(0, old_val - reduce_amount)
                        latest_stats["happiness_ticks"] = new_val

                        used_time = old_time + timedelta(minutes=(blocks * self.happiness_decay_minutes))
                        if used_time > now:
                            used_time = now
                        latest_stats["last_happiness_update"] = used_time.strftime("%Y-%m-%d %H:%M:%S")

                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    async def before_force_happiness_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] force_happiness_decay_loop is starting up...")
    force_happiness_decay_loop.before_loop = before_force_happiness_decay_loop

    async def force_happiness_decay(self, ctx, ticks: int, minutes: int):
        """Admin command to update happiness decay settings."""
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")
        self.happiness_decay_amount = ticks
        self.happiness_decay_minutes = minutes
        await ctx.reply(
            f"Happiness decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    # ----------------------------------------------------------------------
    # HP DECAY
    # ----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_hp_decay_loop(self):
        """
        Every minute, check if ANY one of belly, energy, or happiness is drained (== 0).
        If so, subtract HP ticks based on elapsed time and notify the user at thresholds.
        """
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue
            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[0].isdigit():
                    continue
                user_path = os.path.join(server_folder, user_folder_name)
                chao_data_dir = os.path.join(user_path, "chao_data")
                if not os.path.exists(chao_data_dir):
                    continue
                for chao_name in os.listdir(chao_data_dir):
                    stats_file = os.path.join(chao_data_dir, chao_name, f"{chao_name}_stats.parquet")
                    if not os.path.exists(stats_file):
                        continue
                    df = self.data_utils.load_chao_stats(stats_file)
                    if df.empty:
                        continue
                    latest_stats = df.iloc[-1].to_dict()
                    # If ALL of belly, energy, and happiness ticks are above 0, skip HP decay.
                    if (latest_stats.get("belly_ticks", 0) > 0 and
                        latest_stats.get("energy_ticks", 0) > 0 and
                        latest_stats.get("happiness_ticks", 0) > 0):
                        latest_stats["last_hp_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue
                    # Otherwise, if at least one stat is 0, proceed with HP decay.
                    if "last_hp_update" not in latest_stats:
                        latest_stats["last_hp_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue
                    try:
                        old_time = datetime.strptime(latest_stats["last_hp_update"], "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        latest_stats["last_hp_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue
                    now = datetime.now()
                    passed_minutes = int((now - old_time).total_seconds() // 60)
                    blocks = passed_minutes // self.hp_decay_minutes
                    if blocks > 0:
                        old_val = latest_stats.get("hp_ticks", 0)
                        reduce_amount = self.hp_decay_amount * blocks
                        new_val = max(0, old_val - reduce_amount)
                        latest_stats["hp_ticks"] = new_val

                        used_time = old_time + timedelta(minutes=(blocks * self.hp_decay_minutes))
                        if used_time > now:
                            used_time = now
                        latest_stats["last_hp_update"] = used_time.strftime("%Y-%m-%d %H:%M:%S")

                        # If HP has decreased, check thresholds and notify the user
                        if new_val < old_val:
                            await self.check_hp_thresholds(
                                guild_id=guild.id,
                                user_folder_name=user_folder_name,
                                chao_name=chao_name,
                                old_hp=old_val,
                                new_hp=new_val
                            )
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    async def before_force_hp_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] force_hp_decay_loop is starting up...")
    force_hp_decay_loop.before_loop = before_force_hp_decay_loop

    async def check_hp_thresholds(self, guild_id: int, user_folder_name: str, chao_name: str,
                                  old_hp: int, new_hp: int):
        """
        Check if HP has dropped to critical thresholds (3, 1, or 0)
        and notify the user via DM.
        """
        user_id_str = user_folder_name.split()[0]
        try:
            user_id_int = int(user_id_str)
            user = self.bot.get_user(user_id_int)
            if not user:
                return
        except ValueError:
            return  # Unable to parse user ID

        if new_hp == 0 and old_hp > 0:
            await user.send(
                f"**Oh no!** Your chao **{chao_name}** has reached **0 HP**.\n"
                "This means your chao may have died (or is effectively at no health)."
            )
        elif new_hp == 1 and old_hp > 1:
            await user.send(
                f"**ALERT:** Your chao **{chao_name}** is at **1 HP** and is dangerously low.\n"
                "Please restore its health soon, or it may die!"
            )
        elif new_hp == 3 and old_hp > 3:
            await user.send(
                f"**Warning:** Your chao **{chao_name}** is at only **3 HP** and is in low health!"
            )

    async def force_hp_decay(self, ctx, ticks: int, minutes: int):
        """
        Admin command to update HP decay settings.
        HP decay will subtract the given ticks every block of <minutes>,
        but only if at least one of belly, energy, or happiness is empty.
        """
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")
        self.hp_decay_amount = ticks
        self.hp_decay_minutes = minutes
        await ctx.reply(
            f"HP decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s), "
            "if any of belly, energy, or happiness is drained."
        )

# -----------------------------
# Setup function for the cog
# -----------------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(ChaoDecay(bot))
