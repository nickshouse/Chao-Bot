# cogs/chao_decay.py

import os
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks

class ChaoDecay(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_utils = None

        # Decay settings
        self.belly_decay_amount, self.belly_decay_minutes = 1, 720
        self.happiness_decay_amount, self.happiness_decay_minutes = 1, 960
        self.energy_decay_amount, self.energy_decay_minutes = 2, 1080
        self.hp_decay_amount, self.hp_decay_minutes = 1, 1440

        # Start decay loops
        self.force_belly_decay_loop.start()
        self.force_happiness_decay_loop.start()
        self.force_energy_decay_loop.start()
        self.force_hp_decay_loop.start()

    async def cog_load(self):
        self.data_utils = self.bot.get_cog("DataUtils")
        if not self.data_utils:
            raise RuntimeError("DataUtils cog not found. Load DataUtils before ChaoDecay.")

    def cog_unload(self):
        self.force_belly_decay_loop.cancel()
        self.force_happiness_decay_loop.cancel()
        self.force_energy_decay_loop.cancel()
        self.force_hp_decay_loop.cancel()

    def iter_chao_stats(self):
        """
        Generator yielding (stats_file, df, latest_stats, guild, user_folder, chao_name).
        """
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue

            for user_folder in os.listdir(server_folder):
                user_path = os.path.join(server_folder, user_folder)
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
                    yield stats_file, df, latest_stats, guild, user_folder, chao_name

    def _single_block_decay(self, stats_file, df, latest_stats, decay_minutes, decay_amount,
                            tick_key, time_key):
        """
        Only subtract 'decay_amount' once if enough time has passed.
        This ensures we don't drain multiple blocks at once.
        """
        now = datetime.now()
        if time_key not in latest_stats:
            # If there's no last_*_update key, set it now and bail
            latest_stats[time_key] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)
            return

        try:
            old_time = datetime.strptime(latest_stats[time_key], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            # If we can't parse it, reset to now
            latest_stats[time_key] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)
            return

        # How many minutes have passed since old_time?
        passed = (now - old_time).total_seconds() / 60
        if passed >= decay_minutes:
            old_val = latest_stats.get(tick_key, 0)
            new_val = max(0, old_val - decay_amount)
            latest_stats[tick_key] = new_val

            # Advance the stored time by exactly 'decay_minutes' worth
            used_time = old_time + timedelta(minutes=decay_minutes)
            if used_time > now:
                used_time = now

            latest_stats[time_key] = used_time.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    def _process_decay(self, stats_file, df, latest_stats, decay_minutes, decay_amount,
                       tick_key, time_key):
        """
        This function is called each minute by the loops.
        It attempts a single-block decay each time.
        """
        self._single_block_decay(
            stats_file, df, latest_stats,
            decay_minutes, decay_amount,
            tick_key, time_key
        )

    async def _process_hp_decay(self, stats_file, df, latest_stats, guild, user_folder, chao_name):
        """
        Similar single-block logic for HP. HP decays only if belly/energy/happiness is 0.
        """
        now = datetime.now()
        # If all key stats are above 0, update last_hp_update and skip HP decay
        if (latest_stats.get("belly_ticks", 0) > 0 and
            latest_stats.get("energy_ticks", 0) > 0 and
            latest_stats.get("happiness_ticks", 0) > 0):
            latest_stats["last_hp_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)
            return

        if "last_hp_update" not in latest_stats:
            latest_stats["last_hp_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)
            return

        try:
            old_time = datetime.strptime(latest_stats["last_hp_update"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            latest_stats["last_hp_update"] = now.strftime("%Y-%m-%d %H:%M:%S")
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)
            return

        passed = (now - old_time).total_seconds() / 60
        if passed >= self.hp_decay_minutes:
            old_val = latest_stats.get("hp_ticks", 0)
            new_val = max(0, old_val - self.hp_decay_amount)
            latest_stats["hp_ticks"] = new_val

            used_time = old_time + timedelta(minutes=self.hp_decay_minutes)
            if used_time > now:
                used_time = now
            latest_stats["last_hp_update"] = used_time.strftime("%Y-%m-%d %H:%M:%S")

            if new_val < old_val:
                await self.check_hp_thresholds(
                    guild_id=guild.id,
                    user_folder_name=user_folder,
                    chao_name=chao_name,
                    old_hp=old_val,
                    new_hp=new_val
                )
            self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    # ------------------- Decay Loops -------------------
    @tasks.loop(minutes=1)
    async def force_belly_decay_loop(self):
        for stats_file, df, latest_stats, *_ in self.iter_chao_stats():
            self._process_decay(
                stats_file, df, latest_stats,
                self.belly_decay_minutes, self.belly_decay_amount,
                "belly_ticks", "last_belly_update"
            )

    async def before_force_belly_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] Belly decay loop starting...")
    force_belly_decay_loop.before_loop = before_force_belly_decay_loop

    @tasks.loop(minutes=1)
    async def force_energy_decay_loop(self):
        for stats_file, df, latest_stats, *_ in self.iter_chao_stats():
            self._process_decay(
                stats_file, df, latest_stats,
                self.energy_decay_minutes, self.energy_decay_amount,
                "energy_ticks", "last_energy_update"
            )

    async def before_force_energy_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] Energy decay loop starting...")
    force_energy_decay_loop.before_loop = before_force_energy_decay_loop

    @tasks.loop(minutes=1)
    async def force_happiness_decay_loop(self):
        for stats_file, df, latest_stats, *_ in self.iter_chao_stats():
            self._process_decay(
                stats_file, df, latest_stats,
                self.happiness_decay_minutes, self.happiness_decay_amount,
                "happiness_ticks", "last_happiness_update"
            )

    async def before_force_happiness_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] Happiness decay loop starting...")
    force_happiness_decay_loop.before_loop = before_force_happiness_decay_loop

    @tasks.loop(minutes=1)
    async def force_hp_decay_loop(self):
        for stats_file, df, latest_stats, guild, user_folder, chao_name in self.iter_chao_stats():
            await self._process_hp_decay(stats_file, df, latest_stats, guild, user_folder, chao_name)

    async def before_force_hp_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoDecay] HP decay loop starting...")
    force_hp_decay_loop.before_loop = before_force_hp_decay_loop

    # ------------------- Admin Commands -------------------
    async def force_belly_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        if ticks < 1 or minutes < 1:
            return await interaction.response.send_message("Please provide integers >= 1 for both ticks and minutes.")
        self.belly_decay_amount, self.belly_decay_minutes = ticks, minutes
        await interaction.response.send_message(f"Belly decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s).")

    async def force_energy_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        if ticks < 1 or minutes < 1:
            return await interaction.response.send_message("Please provide integers >= 1 for both ticks and minutes.")
        self.energy_decay_amount, self.energy_decay_minutes = ticks, minutes
        await interaction.response.send_message(f"Energy decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s).")

    async def force_happiness_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        if ticks < 1 or minutes < 1:
            return await interaction.response.send_message("Please provide integers >= 1 for both ticks and minutes.")
        self.happiness_decay_amount, self.happiness_decay_minutes = ticks, minutes
        await interaction.response.send_message(f"Happiness decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s).")

    async def force_hp_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        if ticks < 1 or minutes < 1:
            return await interaction.response.send_message("Please provide integers >= 1 for both ticks and minutes.")
        self.hp_decay_amount, self.hp_decay_minutes = ticks, minutes
        await interaction.response.send_message(
            f"HP decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s), if any of belly, energy, or happiness is drained."
        )

    async def check_hp_thresholds(self, guild_id: int, user_folder_name: str, chao_name: str,
                                  old_hp: int, new_hp: int):
        pass  # You can implement notifications here if desired

async def setup(bot: commands.Bot):
    await bot.add_cog(ChaoDecay(bot))
