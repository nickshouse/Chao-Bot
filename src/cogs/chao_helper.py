# cogs/chao_helper.py

import os, json, random, asyncio, discord, shutil, pandas as pd
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional

PERSISTENT_VIEWS_FILE = "persistent_views.json"

class ChaoHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_utils = None
        self.image_utils = None
        self.assets_dir = None  # Will be set in cog_load

        # Default belly: 2 ticks per block, every 180 min (3h)
        self.belly_decay_amount = 2
        self.belly_decay_minutes = 180

        # Default happiness: 1 tick per block, every 240 min (4h)
        self.happiness_decay_amount = 1
        self.happiness_decay_minutes = 240

        # Default energy: 2 ticks per block, every 240 min (4h)
        self.energy_decay_amount = 2
        self.energy_decay_minutes = 240

        # NEW: HP decays by 1 tick per block, every 720 minutes (12h)
        # *only* if belly=0, energy=0, and happiness=0
        self.hp_decay_amount = 1
        self.hp_decay_minutes = 720

        # Attempt to load config
        try:
            with open('config.json', 'r') as f:
                c = json.load(f)
        except FileNotFoundError:
            print("[ChaoHelper] config.json not found. Please ensure it exists.")
            c = {}
        except json.JSONDecodeError as e:
            print(f"[ChaoHelper] Error decoding config.json: {e}")
            c = {}

        try:
            self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = c['FORM_LEVELS']
            self.ALIGNMENTS = c['ALIGNMENTS']
            self.HERO_ALIGNMENT = self.ALIGNMENTS['hero']
            self.DARK_ALIGNMENT = self.ALIGNMENTS['dark']
            self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX = c['FRUIT_TICKS_RANGE']
        except KeyError:
            # Fallback defaults
            self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = 10, 20, 30
            self.HERO_ALIGNMENT = "hero"
            self.DARK_ALIGNMENT = "dark"
            self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX = 5, 15

        # Start decay loops (1 min checks)
        self.force_belly_decay_loop.change_interval(minutes=1)
        self.force_belly_decay_loop.start()

        self.force_happiness_decay_loop.change_interval(minutes=1)
        self.force_happiness_decay_loop.start()

        self.force_energy_decay_loop.change_interval(minutes=1)
        self.force_energy_decay_loop.start()

        # NEW: Start HP decay loop (only triggers if belly=0, energy=0, happiness=0)
        self.force_hp_decay_loop.change_interval(minutes=1)
        self.force_hp_decay_loop.start()

        # Define fruit stats adjustments
        self.fruit_stats_adjustments = {
            "round fruit": {        "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "triangle fruit": {     "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "square fruit": {       "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "hero fruit": {         "stamina_ticks": (1, 3),      "dark_hero": 1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "dark fruit": {         "stamina_ticks": (1, 3),      "dark_hero": -1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "chao fruit": {         "swim_ticks": 4,              "fly_ticks": 4,           "run_ticks": 4,       "power_ticks": 4,     "stamina_ticks": 4,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "strong fruit": {       "stamina_ticks": 2,                                                                                                             "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "tasty fruit": {        "stamina_ticks": (3, 6),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "heart fruit": {        "stamina_ticks": (1, 2),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "garden nut": {         "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "orange fruit": {       "swim_ticks": 3,              "fly_ticks": -2,          "run_ticks": -2,      "power_ticks": 3,     "stamina_ticks": 1,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "blue fruit": {         "swim_ticks": 2,              "fly_ticks": 5,           "run_ticks": -1,      "power_ticks": -1,    "stamina_ticks": 3,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "pink fruit": {         "swim_ticks": 4,              "fly_ticks": -3,          "run_ticks": 4,       "power_ticks": -3,    "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "green fruit": {        "swim_ticks": 0,              "fly_ticks": -1,          "run_ticks": 3,       "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "purple fruit": {       "swim_ticks": -2,             "fly_ticks": 3,           "run_ticks": 3,       "power_ticks": -2,    "stamina_ticks": 1,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "yellow fruit": {       "swim_ticks": -3,             "fly_ticks": 4,           "run_ticks": -3,      "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "red fruit": {          "swim_ticks": 3,              "fly_ticks": 1,           "run_ticks": 3,       "power_ticks": 2,     "stamina_ticks": -5,        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "power fruit": {        "power_ticks": (1,4),           "run_power": 1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "swim fruit": {         "swim_ticks": (1,4),            "swim_fly": -1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "run fruit": {          "run_ticks": (1,4),             "run_power": -1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "fly fruit": {          "fly_ticks": (1,4),             "swim_fly": 1,                                                                                    "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "strange mushroom": {},  # Add custom logic for randomizing ticks
        }
        
        self.fruits = [fruit.title() for fruit in self.fruit_stats_adjustments.keys()]
        self.embed_color = discord.Color.blue()
        self.GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']

    async def cog_load(self):
        """Called when this Cog is loaded."""
        self.data_utils = self.bot.get_cog("DataUtils")
        self.image_utils = self.bot.get_cog("ImageUtils")
        if not self.data_utils or not self.image_utils:
            raise Exception("ChaoHelper requires DataUtils and ImageUtils cogs to be loaded.")

        # Assets
        self.assets_dir = self.image_utils.assets_dir

        # Path definitions
        self.TEMPLATE_PATH = os.path.join(self.assets_dir, 'graphics', 'cards', 'stats_page_1.png')
        self.TEMPLATE_PAGE_2_PATH = os.path.join(self.assets_dir, 'graphics', 'cards', 'stats_page_2.png')
        self.OVERLAY_PATH = os.path.join(self.assets_dir, 'graphics', 'ticks', 'tick_filled.png')
        self.ICON_PATH = os.path.join(self.assets_dir, 'graphics', 'icons', 'Stats.png')
        self.BACKGROUND_PATH = os.path.join(self.assets_dir, 'graphics', 'thumbnails', 'neutral_background.png')
        self.NEUTRAL_PATH = os.path.join(self.assets_dir, 'chao', 'normal', 'neutral', 'neutral_normal_1.png')
        self.HERO_BG_PATH = os.path.join(self.assets_dir, 'graphics', 'thumbnails', 'hero_background.png')
        self.DARK_BG_PATH = os.path.join(self.assets_dir, 'graphics', 'thumbnails', 'dark_background.png')
        self.NEUTRAL_BG_PATH = os.path.join(self.assets_dir, 'graphics', 'thumbnails', 'neutral_background.png')

        self.PAGE1_TICK_POSITIONS = [(446, y) for y in [1176, 315, 591, 883, 1469]]
        self.PAGE2_TICK_POSITIONS = {
            'belly': (272, 314),
            'happiness': (272, 590),
            'illness': (272, 882),
            'energy': (272, 1175),
            'hp': (272, 1468)
        }

        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')

        self.load_persistent_views()

    def cog_unload(self):
        self.force_belly_decay_loop.cancel()
        self.force_happiness_decay_loop.cancel()
        self.force_energy_decay_loop.cancel()
        self.force_hp_decay_loop.cancel()  # New

    #----------------------------------------------------------------------
    # BELLY DECAY
    #----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_belly_decay_loop(self):
        """Block-based decay for belly."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue

            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[:1].isdigit():
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

                    old_time_str = latest_stats["last_belly_update"]
                    try:
                        old_time = datetime.strptime(old_time_str, "%Y-%m-%d %H:%M:%S")
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

    @force_belly_decay_loop.before_loop
    async def before_force_belly_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoHelper] force_belly_decay_loop is starting up...")

    async def force_belly_decay(self, ctx, ticks: int, minutes: int):
        """Admin sets how many belly ticks to remove per block, and block size in minutes."""
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")

        self.belly_decay_amount = ticks
        self.belly_decay_minutes = minutes
        await ctx.reply(
            f"Belly decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    #----------------------------------------------------------------------
    # ENERGY DECAY
    #----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_energy_decay_loop(self):
        """Block-based decay for energy."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue

            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[:1].isdigit():
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

                    # Initialize if missing
                    if "last_energy_update" not in latest_stats:
                        latest_stats["last_energy_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    old_time_str = latest_stats["last_energy_update"]
                    try:
                        old_time = datetime.strptime(old_time_str, "%Y-%m-%d %H:%M:%S")
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

    @force_energy_decay_loop.before_loop
    async def before_force_energy_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoHelper] force_energy_decay_loop is starting up...")

    async def force_energy_decay(self, ctx, ticks: int, minutes: int):
        """
        Admin-only command to set how many energy ticks are subtracted
        and how often (in minutes).
        Usage: $force_energy_decay <ticks> <minutes>
        """
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")

        self.energy_decay_amount = ticks
        self.energy_decay_minutes = minutes
        await ctx.reply(
            f"Energy decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    #----------------------------------------------------------------------
    # HAPPINESS DECAY
    #----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_happiness_decay_loop(self):
        """Block-based decay for happiness."""
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue

            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[:1].isdigit():
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

                    old_time_str = latest_stats["last_happiness_update"]
                    try:
                        old_time = datetime.strptime(old_time_str, "%Y-%m-%d %H:%M:%S")
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

    @force_happiness_decay_loop.before_loop
    async def before_force_happiness_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoHelper] force_happiness_decay_loop is starting up...")

    async def force_happiness_decay(self, ctx, ticks: int, minutes: int):
        """
        Admin-only command to set how many happiness ticks are subtracted
        and how often (in minutes).
        """
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")

        self.happiness_decay_amount = ticks
        self.happiness_decay_minutes = minutes
        await ctx.reply(
            f"Happiness decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s)."
        )

    #----------------------------------------------------------------------
    # HP DECAY (NEW!) - Only if belly=0, energy=0, happiness=0
    #----------------------------------------------------------------------
    @tasks.loop(minutes=1)
    async def force_hp_decay_loop(self):
        """
        Every minute, we check if belly=0, energy=0, and happiness=0.
        If so, HP decays by self.hp_decay_amount per full block of
        self.hp_decay_minutes (default 1 tick every 12 hours).
        If ANY of belly, energy, or happiness is above 0, we skip HP decay.
        """
        for guild in self.bot.guilds:
            server_folder = self.data_utils.get_server_folder(str(guild.id), guild.name)
            if not os.path.exists(server_folder):
                continue

            for user_folder_name in os.listdir(server_folder):
                if not user_folder_name[:1].isdigit():
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

                    # If any of belly, energy, or happiness is above zero, skip HP decay
                    belly = latest_stats.get("belly_ticks", 0)
                    energy = latest_stats.get("energy_ticks", 0)
                    happiness = latest_stats.get("happiness_ticks", 0)
                    if belly > 0 or energy > 0 or happiness > 0:
                        # Reset last_hp_update to now (so it doesn't do a big jump
                        # next time everything is 0 again)
                        latest_stats["last_hp_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    # So at this point, belly=0, energy=0, happiness=0 => HP decays
                    if "last_hp_update" not in latest_stats:
                        latest_stats["last_hp_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)
                        continue

                    old_time_str = latest_stats["last_hp_update"]
                    try:
                        old_time = datetime.strptime(old_time_str, "%Y-%m-%d %H:%M:%S")
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

                        self.data_utils.save_chao_stats(stats_file, df, latest_stats)

    @force_hp_decay_loop.before_loop
    async def before_force_hp_decay_loop(self):
        await self.bot.wait_until_ready()
        print("[ChaoHelper] force_hp_decay_loop is starting up...")

    # Optional admin command to tweak HP decay if you want
    async def force_hp_decay(self, ctx, ticks: int, minutes: int):
        """
        Admin-only command to set how many HP ticks are subtracted
        every block of <minutes> -- but ONLY if belly=0, energy=0, happiness=0.
        Usage: $force_hp_decay <ticks> <minutes>
        Default: 1 tick every 720 minutes (12h).
        """
        if ticks < 1 or minutes < 1:
            return await ctx.reply("Please provide integers >= 1 for both ticks and minutes.")

        self.hp_decay_amount = ticks
        self.hp_decay_minutes = minutes
        await ctx.reply(
            f"HP decay set to subtract **{ticks}** tick(s) every **{minutes}** minute(s), "
            f"if belly, energy, and happiness are all empty."
        )


    def save_persistent_view(self, view_data: Dict):
        """Save the persistent view data."""
        try:
            with open(PERSISTENT_VIEWS_FILE, "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}

        key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data['chao_name']}"
        data[key] = view_data

        with open(PERSISTENT_VIEWS_FILE, "w") as f:
            json.dump(data, f)

    def load_persistent_views(self):
        """Load and re-register all persistent views."""
        if os.path.exists(PERSISTENT_VIEWS_FILE):
            with open(PERSISTENT_VIEWS_FILE, "r") as f:
                persistent_views = json.load(f)

            for key, view_data in persistent_views.items():
                required_keys = {
                    "chao_name", "guild_id", "user_id",
                    "chao_type_display", "alignment_label", "total_pages"
                }
                if not required_keys.issubset(view_data.keys()):
                    print(f"[ChaoHelper] Key={key} missing fields. Adding defaults.")
                    view_data.setdefault("chao_type_display", "Unknown")
                    view_data.setdefault("alignment_label", "Neutral")
                    view_data.setdefault("total_pages", 2)
                    view_data.setdefault("current_page", 1)

                view = StatsView.from_data(view_data, self)
                self.bot.add_view(view)

    def send_embed(self, ctx, description: str, title: str = "Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.reply(embed=embed)

    def get_stat_increment(self, grade: str) -> int:
        """
        Returns a random stat increment based on the grade of the stat.
        """
        grade_ranges = {
            'F': (8, 12),
            'E': (11, 15),
            'D': (14, 18),
            'C': (17, 21),
            'B': (20, 24),
            'A': (23, 27),
            'S': (26, 30),
            'X': (30, 35)
        }
        return random.randint(*grade_ranges.get(grade.upper(), (8, 12)))

    def update_chao_type_and_thumbnail(self, guild_id: str, guild_name: str, user: discord.Member, chao_name: str, latest_stats: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Updates the Chao type and form based on current stats and evolution rules.
        Generates the updated thumbnail for the Chao.
        """
        try:
            if not self.assets_dir:
                raise ValueError("assets_dir is not set. Ensure cog_load initializes it correctly.")
            chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
            stat_levels = {s: latest_stats.get(f"{s}_level", 0) for s in ["power", "swim", "stamina", "fly", "run"]}
            dark_hero = latest_stats.get("dark_hero", 0)
            run_power = latest_stats.get("run_power", 0)
            swim_fly = latest_stats.get("swim_fly", 0)
            current_form = str(latest_stats.get("Form", "1"))
            max_level = max(stat_levels.values())
            latest_stats["dark_hero"] = max(min(dark_hero, 5), -5)
            latest_stats["run_power"] = max(min(run_power, 5), -5)
            latest_stats["swim_fly"] = max(min(swim_fly, 5), -5)
            alignment = "hero" if latest_stats["dark_hero"] == 5 else "dark" if latest_stats["dark_hero"] == -5 else "neutral"
            latest_stats["Alignment"] = alignment

            def determine_suffix(rp: int, sf: int) -> str:
                if rp == 5:
                    return "power"
                elif rp == -5:
                    return "run"
                elif sf == 5:
                    return "fly"
                elif sf == -5:
                    return "swim"
                return "normal"

            old_type = latest_stats.get("Type", "neutral_normal_1")
            old_form = str(latest_stats.get("Form", "1"))
            if old_form == "3" and max_level < self.FORM_LEVEL_4:
                return old_type, old_form
            if old_form == "4":
                return old_type, old_form

            suffix = determine_suffix(latest_stats["run_power"], latest_stats["swim_fly"])
            if current_form == "1" and max_level >= self.FORM_LEVEL_2:
                current_form = "2"
            if current_form == "2" and max_level >= self.FORM_LEVEL_3:
                current_form = "3"
            if current_form == "3" and max_level >= self.FORM_LEVEL_4:
                current_form = "4"

            if current_form == "1":
                chao_type = f"{alignment}_normal_1"
            elif current_form == "2":
                chao_type = f"{alignment}_normal_{suffix}_2"
            elif current_form == "3":
                chao_type = f"{alignment}_{suffix}_3"
            else:
                base_suffix = suffix
                if old_type.endswith("_3"):
                    base_suffix = old_type.split("_")[1]
                chao_type = f"{alignment}_{base_suffix}_{suffix}_4"
                if base_suffix == "normal" and suffix == "normal":
                    chao_type = f"{alignment}_normal_normal_4"

            print(f"[DEBUG] alignment={alignment}, suffix={suffix}, form={current_form}, type={chao_type}")
            latest_stats["Form"] = current_form
            latest_stats["Type"] = chao_type
            subfolders = chao_type.split("_")
            base_folder = subfolders[1] if len(subfolders) > 1 else "normal"
            sprite_path = os.path.join(self.assets_dir, "chao", base_folder, alignment, f"{chao_type}.png")
            print(f"[DEBUG] Sprite path => {sprite_path}")
            if not os.path.exists(sprite_path):
                print(f"[DEBUG] Sprite not found. Defaulting to chao_missing.png")
                sprite_path = os.path.join(self.assets_dir, "chao", "chao_missing.png")
            eyes = latest_stats.get("eyes", "neutral")
            mouth = latest_stats.get("mouth", "happy")
            eyes_alignment = "neutral" if current_form in ["1", "2"] else alignment
            eyes_image_path = os.path.join(self.EYES_DIR, f"{eyes_alignment}_{eyes}.png")
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(self.EYES_DIR, "neutral.png")
            mouth_image_path = os.path.join(self.MOUTH_DIR, f"{mouth}.png")
            if not os.path.exists(mouth_image_path):
                mouth_image_path = os.path.join(self.MOUTH_DIR, "happy.png")
            bg_path = self.HERO_BG_PATH if current_form in ["3", "4"] and alignment=="hero" else \
                      self.DARK_BG_PATH if current_form in ["3", "4"] and alignment=="dark" else \
                      (self.NEUTRAL_BG_PATH if current_form in ["3", "4"] else self.BACKGROUND_PATH)
            self.image_utils.combine_images_with_face(bg_path, sprite_path, eyes_image_path, mouth_image_path, thumbnail_path)
            return chao_type, current_form
        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] An error occurred: {e}")
            return "normal", "1"


    async def feed(self, ctx, *, chao_name_and_fruit: str):
        """
        Feeds a particular fruit to a Chao multiple times.
        Syntax:
        $feed <chao_name> <fruit_name> [quantity]

        Notes:
        - If quantity is omitted, defaults to 1.
        - Only allows multiple units of the SAME fruit in one command.
        - Form 2 Chao can shift alignment on each feeding.
        - Form 3/4 Chao remain locked in advanced form alignment.
        - Level-ups and changes are aggregated into a single summary.
        """
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        # 1) Parse user input
        tokens = chao_name_and_fruit.split()
        if not tokens:
            return await ctx.reply("Please provide a Chao name and fruit.")

        quantity = 1
        if tokens[-1].isdigit():
            quantity = int(tokens[-1])
            tokens = tokens[:-1]

        matched_fruit = None
        chao_name_tokens = tokens[:]
        for i in range(len(tokens), 0, -1):
            candidate = " ".join(tokens[i - 1 :])
            if candidate.lower() in [f.lower() for f in self.fruits]:
                matched_fruit = candidate
                chao_name_tokens = tokens[: i - 1]
                break

        if not matched_fruit:
            valid_list = ", ".join(sorted(self.fruits))
            return await self.send_embed(
                ctx,
                f"{ctx.author.mention}, provide a valid Chao name and fruit.\n"
                f"Valid fruits: {valid_list}"
            )

        chao_name = " ".join(chao_name_tokens).strip()
        if not chao_name:
            return await ctx.reply("Please specify which Chao you want to feed.")

        matched_fruit_lower = matched_fruit.lower()

        # 2) Confirm that the Chao exists
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_dir):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, stats file is missing for **{chao_name}**.")

        # 3) Confirm user has enough fruit
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}

        normalized_inventory = {k.lower(): v for k, v in current_inv.items()}
        have_amount = normalized_inventory.get(matched_fruit_lower, 0)
        if have_amount < quantity:
            return await self.send_embed(
                ctx,
                f"{ctx.author.mention}, you only have **{have_amount}** {matched_fruit}, "
                f"but you tried to feed {quantity}."
            )

        # 4) Load the Chao's stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].to_dict()

        # 5) Track changes in aggregated form
        import collections
        ticks_changes = collections.defaultdict(int)
        alignment_changes = collections.defaultdict(int)
        levels_gained = collections.defaultdict(int)

        def clamp(value, lo, hi):
            return max(lo, min(value, hi))

        # 6) Apply the fruit once (single iteration)
        def apply_fruit_once():
            nonlocal latest_stats

            adjustments = self.fruit_stats_adjustments.get(matched_fruit_lower, {})
            for stat, adjustment in adjustments.items():
                increment = random.randint(*adjustment) if isinstance(adjustment, tuple) else adjustment

                # A) Stats capped at 10 (hp/belly/energy/happiness/illness)
                if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"]:
                    old_val = latest_stats.get(stat, 0)
                    if old_val < 10:
                        new_val = clamp(old_val + increment, 0, 10)
                        net_gain = new_val - old_val
                        if net_gain > 0:
                            ticks_changes[stat] += net_gain
                            latest_stats[stat] = new_val

                # B) Trainable stats (range 0–9, reset at 10 => level up)
                elif stat.endswith("_ticks"):
                    remaining = increment
                    while remaining > 0:
                        old_val = latest_stats.get(stat, 0)
                        space_until_level = 9 - old_val
                        to_add = min(remaining, space_until_level + 1)
                        new_val = old_val + to_add
                        remaining -= to_add

                        if new_val > 9:
                            level_key = stat.replace("_ticks", "_level")
                            grade_key = stat.replace("_ticks", "_grade")
                            exp_key = stat.replace("_ticks", "_exp")

                            old_level = latest_stats.get(level_key, 0)
                            latest_stats[level_key] = old_level + 1
                            levels_gained[level_key] += 1

                            grade = latest_stats.get(grade_key, 'F')
                            old_exp = latest_stats.get(exp_key, 0)
                            latest_stats[exp_key] = old_exp + self.get_stat_increment(grade)
                            latest_stats[stat] = 0
                        else:
                            net_gain = new_val - old_val
                            ticks_changes[stat] += net_gain
                            latest_stats[stat] = new_val

                # C) Alignment stats
                elif stat in ["run_power", "swim_fly", "dark_hero"]:
                    old_val = latest_stats.get(stat, 0)
                    new_val = clamp(old_val + increment, -5, 5)
                    net_gain = new_val - old_val
                    if net_gain != 0:
                        alignment_changes[stat] += net_gain
                    latest_stats[stat] = new_val

            # D) If Form 2, shift the *other* alignment stat one step toward 0
            current_form = str(latest_stats.get("Form", "1"))
            if current_form == "2":
                # e.g. handle run_power and swim_fly pulling to 0
                if matched_fruit_lower in ["swim fruit", "blue fruit", "green fruit", "purple fruit", "pink fruit", "fly fruit"]:
                    old_rp = latest_stats.get("run_power", 0)
                    new_rp = old_rp + 1 if old_rp < 0 else (old_rp - 1 if old_rp > 0 else old_rp)
                    new_rp = clamp(new_rp, -5, 5)
                    if new_rp != old_rp:
                        alignment_changes["run_power"] += (new_rp - old_rp)
                        latest_stats["run_power"] = new_rp

                if matched_fruit_lower in ["run fruit", "red fruit", "power fruit"]:
                    old_sf = latest_stats.get("swim_fly", 0)
                    new_sf = old_sf + 1 if old_sf < 0 else (old_sf - 1 if old_sf > 0 else old_sf)
                    new_sf = clamp(new_sf, -5, 5)
                    if new_sf != old_sf:
                        alignment_changes["swim_fly"] += (new_sf - old_sf)
                        latest_stats["swim_fly"] = new_sf

        # 7) Feed multiple times
        for _ in range(quantity):
            apply_fruit_once()

        # 8) Deduct fruit
        normalized_inventory[matched_fruit_lower] = have_amount - quantity
        updated_inventory = {k: normalized_inventory.get(k.lower(), 0) for k in current_inv.keys()}
        self.data_utils.save_inventory(inv_path, inv_df, updated_inventory)

        # 9) Update chao form / thumbnail
        prev_form = str(latest_stats.get("Form", "1"))
        chao_type, form = self.update_chao_type_and_thumbnail(
            guild_id, guild_name, user, chao_name, latest_stats
        )
        latest_stats["Form"] = form
        latest_stats["Type"] = chao_type

        # Possibly handle form evolution from 2 -> 3
        if prev_form == "2" and form == "3":
            suffix = chao_type.split("_")[1]
            stat_to_upgrade = {
                "fly": "fly_grade",
                "power": "power_grade",
                "run": "run_grade",
                "swim": "swim_grade"
            }.get(suffix)
            if stat_to_upgrade and stat_to_upgrade in latest_stats:
                grades = self.GRADES
                current_grade = latest_stats.get(stat_to_upgrade, 'F')
                if current_grade in grades:
                    new_grade_index = min(len(grades) - 1, grades.index(current_grade) + 1)
                    latest_stats[stat_to_upgrade] = grades[new_grade_index]
                    levels_gained[stat_to_upgrade] += 1

        # Save updated stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # 10) Build final embed message
        feed_summary = f"{chao_name} ate {quantity} {matched_fruit}!"
        if quantity == 1:
            feed_summary = f"{chao_name} ate a {matched_fruit}!"

        stat_lines = []
        # Summarize stat changes
        for stat, net_gain in ticks_changes.items():
            base_name = stat.replace("_ticks", "").capitalize()
            final_val = latest_stats.get(stat, 0)
            cap = 10 if stat in ["hp_ticks","belly_ticks","energy_ticks","happiness_ticks","illness_ticks"] else 9
            sign = "+" if net_gain > 0 else ""
            stat_lines.append(f"{base_name} {sign}{net_gain} ({final_val}/{cap})")

        for a_stat, net_align in alignment_changes.items():
            if a_stat == "dark_hero":
                continue  # Hide dark/hero changes
            sign = "+" if net_align > 0 else ""
            final_val = latest_stats.get(a_stat, 0)
            base = a_stat.replace("_","/").capitalize()
            stat_lines.append(f"{base} {sign}{net_align} (→ {final_val}/5)")

        for lvl_key, times_gained in levels_gained.items():
            if lvl_key.endswith("_level"):
                short_name = lvl_key.replace("_level","").capitalize()
                new_level = latest_stats.get(lvl_key, 0)
                stat_lines.append(f"{short_name} leveled up to {new_level}")
            elif lvl_key.endswith("_grade"):
                short_name = lvl_key.replace("_grade","").capitalize()
                new_grade = latest_stats.get(lvl_key, "F")
                stat_lines.append(f"{short_name} grade improved to {new_grade}")

        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
        if not os.path.exists(thumbnail_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, thumbnail file is missing for **{chao_name}**.")

        description = feed_summary
        if stat_lines:
            description += "\n\n" + "\n".join(stat_lines)

        embed = discord.Embed(
            title="Chao Feed Success",
            description=description,
            color=self.embed_color
        )
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")

        with open(thumbnail_path, 'rb') as file:
            thumbnail = discord.File(file, filename="chao_thumbnail.png")
            await ctx.reply(embed=embed, file=thumbnail)

    async def stats(self, ctx, *, chao_name: str):
        """
        Command to display the stats of a specific Chao.
        Generates Page 1 & 2 stat cards and sends them.
        """
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)
        guild_name = ctx.guild.name

        chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()

        chao_type, form = self.update_chao_type_and_thumbnail(
            guild_id, guild_name, ctx.author, chao_name, chao_stats
        )

        # Ensure the database is updated if Type or Form changes
        if chao_stats.get("Form", None) != form or chao_stats.get("Type", None) != chao_type:
            chao_stats["Form"] = form
            chao_stats["Type"] = chao_type
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)

        # Map chao_type to display-friendly format
        type_mapping = {
            # Fly types
            **{f"{alignment}_fly_3": "Fly" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_fly_{suffix}_4": f"Fly/{suffix.capitalize()}" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
            # Normal types
            **{f"{alignment}_normal_1": "Normal" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_normal_3": "Normal" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_normal_{suffix}_2": "Normal" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
            **{f"{alignment}_normal_{suffix}_4": f"Normal/{suffix.capitalize()}" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
            # Power types
            **{f"{alignment}_power_3": "Power" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_power_{suffix}_4": f"Power/{suffix.capitalize()}" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
            # Run types
            **{f"{alignment}_run_3": "Run" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_run_{suffix}_4": f"Run/{suffix.capitalize()}" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
            # Swim types
            **{f"{alignment}_swim_3": "Swim" for alignment in ["dark", "hero", "neutral"]},
            **{f"{alignment}_swim_{suffix}_4": f"Swim/{suffix.capitalize()}" for alignment in ["dark", "hero", "neutral"]
            for suffix in ["fly", "normal", "power", "run", "swim"]},
        }

        # Retrieve the display type from the mapping
        chao_type_display = type_mapping.get(chao_type, "Unknown")

        # Retrieve alignment from the database
        alignment_label = chao_stats.get('Alignment', 'Neutral').capitalize()

        # Paths for the generated images
        stats_image_paths = {
            1: os.path.join(chao_dir, f"{chao_name}_stats_page_1.png"),
            2: os.path.join(chao_dir, f"{chao_name}_stats_page_2.png"),
        }
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        # Levels and ticks
        power_level = int(chao_stats.get("power_level", 0))
        swim_level = int(chao_stats.get("swim_level", 0))
        fly_level = int(chao_stats.get("fly_level", 0))
        run_level = int(chao_stats.get("run_level", 0))
        stamina_level = int(chao_stats.get("stamina_level", 0))

        power_ticks = int(chao_stats.get("power_ticks", 0))
        swim_ticks = int(chao_stats.get("swim_ticks", 0))
        fly_ticks = int(chao_stats.get("fly_ticks", 0))
        run_ticks = int(chao_stats.get("run_ticks", 0))
        stamina_ticks = int(chao_stats.get("stamina_ticks", 0))

        power_exp = int(chao_stats.get("power_exp", 0))
        swim_exp = int(chao_stats.get("swim_exp", 0))
        fly_exp = int(chao_stats.get("fly_exp", 0))
        run_exp = int(chao_stats.get("run_exp", 0))
        stamina_exp = int(chao_stats.get("stamina_exp", 0))

        # Generate images in parallel
        await asyncio.gather(
            asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.TEMPLATE_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[1],
                self.PAGE1_TICK_POSITIONS,
                power_ticks, swim_ticks, fly_ticks, run_ticks, stamina_ticks,
                power_level, swim_level, fly_level, run_level, stamina_level,
                power_exp, swim_exp, fly_exp, run_exp, stamina_exp
            ),
            asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.TEMPLATE_PAGE_2_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[2],
                self.PAGE2_TICK_POSITIONS,
                {
                    k: chao_stats.get(f"{k}_ticks", 0)
                    for k in self.PAGE2_TICK_POSITIONS
                }
            )
        )

        # Build embed
        embed = discord.Embed(color=self.embed_color)
        embed.set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://stats_page.png")
        embed.set_footer(text="Page 1 / 2")

        # Create StatsView
        view = StatsView.from_data(
            {
                "chao_name": chao_name,
                "guild_id": guild_id,
                "user_id": user_id,
                "chao_type_display": chao_type_display,
                "alignment_label": alignment_label,
                "total_pages": 2,
                "current_page": 1
            },
            self
        )

        self.save_persistent_view({
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user_id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        })

        await ctx.reply(
            files=[
                discord.File(stats_image_paths[1], "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(thumbnail_path, filename="chao_thumbnail.png"),
            ],
            embed=embed,
            view=view
        )

class StatsView(View):
    def __init__(
        self,
        bot: commands.Bot,
        chao_name: str,
        guild_id: str,
        user_id: str,
        page1_tick_positions: List[Tuple[int, int]],
        page2_tick_positions: Dict[str, Tuple[int, int]],
        exp_positions: Dict[str, List[Tuple[int, int]]],
        num_images: Dict[str, discord.File],
        level_position_offset: Tuple[int, int],
        level_spacing: int,
        tick_spacing: int,
        chao_type_display: str,
        alignment_label: str,
        template_path: str,
        template_page_2_path: str,
        overlay_path: str,
        icon_path: str,
        image_utils,
        data_utils,
        total_pages: int = 2,
        current_page: int = 1,
        state_file: str = PERSISTENT_VIEWS_FILE
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.chao_name = chao_name
        self.guild_id = guild_id
        self.user_id = user_id
        self.page1_tick_positions = page1_tick_positions
        self.page2_tick_positions = page2_tick_positions
        self.exp_positions = exp_positions
        self.num_images = num_images
        self.level_position_offset = level_position_offset
        self.level_spacing = level_spacing
        self.tick_spacing = tick_spacing
        self.chao_type_display = chao_type_display
        self.alignment_label = alignment_label
        self.template_path = template_path
        self.template_page_2_path = template_page_2_path
        self.overlay_path = overlay_path
        self.icon_path = icon_path
        self.image_utils = image_utils
        self.data_utils = data_utils
        self.total_pages = total_pages
        self.state_file = state_file

        # Load and validate the initial page state
        self.current_page = self.load_state(default_page=current_page)
        self.save_state()  # Ensure the state is immediately persisted

        # Add navigation buttons
        self.add_navigation_buttons()

    def save_state(self):
        """Save the current page to the persistent views file."""
        try:
            with open(self.state_file, "r") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}

        key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
        data[key] = {
            "chao_name": self.chao_name,
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "chao_type_display": self.chao_type_display or "Unknown",
            "alignment_label": self.alignment_label or "Neutral",
            "total_pages": self.total_pages,
            "current_page": self.current_page,
        }

        with open(self.state_file, "w") as f:
            json.dump(data, f)

    def load_state(self, default_page: int = 1) -> int:
        """Load the saved current page from the persistent views file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                try:
                    data = json.load(f)
                    key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
                    page = data.get(key, {}).get("current_page", default_page)
                    return max(1, min(page, self.total_pages))
                except json.JSONDecodeError:
                    pass  # Return default if JSON is corrupted
        return default_page

    def add_navigation_buttons(self):
        """Add navigation buttons to the view."""
        self.clear_items()
        self.add_item(self.create_button("⬅️", "previous_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_prev"))
        self.add_item(self.create_button("➡️", "next_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_next"))

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to the previous page."""
        self.current_page = self.total_pages if self.current_page == 1 else self.current_page - 1
        self.save_state()
        await self.update_stats(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Navigate to the next page."""
        self.current_page = 1 if self.current_page == self.total_pages else self.current_page + 1
        self.save_state()
        await self.update_stats(interaction)

    async def update_stats(self, interaction: discord.Interaction):
        """Update the stats display based on the current page."""
        guild = self.bot.get_guild(int(self.guild_id))
        if not guild:
            return await interaction.response.send_message("Error: Could not find the guild.", ephemeral=True)

        member = guild.get_member(int(self.user_id))
        if not member:
            return await interaction.response.send_message("Error: Could not find the user in this guild.", ephemeral=True)

        chao_dir = self.data_utils.get_path(self.guild_id, guild.name, member, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)

        if chao_df.empty:
            return await interaction.response.send_message("No stats data available for this Chao.", ephemeral=True)

        chao_to_view = chao_df.iloc[-1].to_dict()
        page_image_filename = f'{self.chao_name}_stats_page_{self.current_page}.png'
        image_path = os.path.join(chao_dir, page_image_filename)

        if self.current_page == 1:
            await asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.template_path,
                self.overlay_path,
                image_path,
                self.page1_tick_positions,
                *[chao_to_view.get(f"{stat}_ticks", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_to_view.get(f"{stat}_level", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_to_view.get(f"{stat}_exp", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']]
            )
        else:
            stats_values_page2 = {
                stat: chao_to_view.get(f"{stat}_ticks", 0)
                for stat in self.page2_tick_positions
            }
            await asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.template_page_2_path,
                self.overlay_path,
                image_path,
                self.page2_tick_positions,
                stats_values_page2
            )

        embed = (
            discord.Embed(color=discord.Color.blue())
            .set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
            .add_field(name="Type", value=self.chao_type_display, inline=True)
            .add_field(name="Alignment", value=self.alignment_label, inline=True)
            .set_thumbnail(url="attachment://chao_thumbnail.png")
            .set_image(url="attachment://stats_page.png")
            .set_footer(text=f"Page {self.current_page} / {self.total_pages}")
        )

        await interaction.response.edit_message(
            embed=embed,
            attachments=[
                discord.File(image_path, "stats_page.png"),
                discord.File(self.icon_path, filename="Stats.png"),
                discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png"),
            ],
            view=self
        )



    @classmethod
    def from_data(cls, view_data: Dict, cog):
        """Recreate a StatsView from stored data."""
        return cls(
            bot=cog.bot,
            chao_name=view_data["chao_name"],
            guild_id=view_data["guild_id"],
            user_id=view_data["user_id"],
            page1_tick_positions=cog.PAGE1_TICK_POSITIONS,
            page2_tick_positions=cog.PAGE2_TICK_POSITIONS,
            exp_positions=cog.image_utils.EXP_POSITIONS,
            num_images=cog.image_utils.num_images,
            level_position_offset=cog.image_utils.LEVEL_POSITION_OFFSET,
            level_spacing=cog.image_utils.LEVEL_SPACING,
            tick_spacing=cog.image_utils.TICK_SPACING,
            chao_type_display=view_data["chao_type_display"],
            alignment_label=view_data["alignment_label"],
            template_path=cog.TEMPLATE_PATH,
            template_page_2_path=cog.TEMPLATE_PAGE_2_PATH,
            overlay_path=cog.OVERLAY_PATH,
            icon_path=cog.ICON_PATH,
            image_utils=cog.image_utils,
            data_utils=cog.data_utils,
            total_pages=view_data["total_pages"],
            current_page=view_data.get("current_page", 1)
        )


async def setup(bot):
    """Standard async setup for this cog."""
    await bot.add_cog(ChaoHelper(bot))
