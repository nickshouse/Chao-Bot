# cogs/chao_helper.py

import os, json, random, asyncio, discord, shutil, pandas as pd
import collections
from PIL import Image
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional

PERSISTENT_VIEWS_FILE = "persistent_views.json"
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets"))

class ChaoHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_utils = None
        self.image_utils = None
        self.assets_dir = None  # Will be set in cog_load

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

        # Define fruit stats adjustments
        self.fruit_stats_adjustments = {
            "round fruit": {        "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
            "triangle fruit": {     "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
            "square fruit": {       "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
            "hero fruit": {         "stamina_ticks": (1, 3),      "dark_hero": 1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "dark fruit": {         "stamina_ticks": (1, 3),      "dark_hero": -1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "chao fruit": {         "swim_ticks": 4,              "fly_ticks": 4,           "run_ticks": 4,       "power_ticks": 4,     "stamina_ticks": 4,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "strong fruit": {       "stamina_ticks": 2,                                                                                                             "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 3},
            "tasty fruit": {        "stamina_ticks": (3, 6),                                                                                                        "belly_ticks": (2, 3), "hp_ticks": (2, 3), "energy_ticks": 1},
            "heart fruit": {        "stamina_ticks": 1,                                                                                                             "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "garden nut": {         "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "orange fruit": {       "swim_ticks": 3,              "fly_ticks": -2,          "run_ticks": -2,      "power_ticks": 3,     "stamina_ticks": 1,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "blue fruit": {         "swim_ticks": 2,              "fly_ticks": 5,           "run_ticks": -1,      "power_ticks": -1,    "stamina_ticks": 3,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "pink fruit": {         "swim_ticks": 4,              "fly_ticks": -3,          "run_ticks": 4,       "power_ticks": -3,    "stamina_ticks": 2,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "green fruit": {        "swim_ticks": 0,              "fly_ticks": -1,          "run_ticks": 3,       "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "purple fruit": {       "swim_ticks": -2,             "fly_ticks": 3,           "run_ticks": 3,       "power_ticks": -2,    "stamina_ticks": 1,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "yellow fruit": {       "swim_ticks": -3,             "fly_ticks": 4,           "run_ticks": -3,      "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "red fruit": {          "swim_ticks": 3,              "fly_ticks": 1,           "run_ticks": 3,       "power_ticks": 2,     "stamina_ticks": -5,        "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
            "power fruit": {        "power_ticks": (1, 4),           "run_power": 1,                                                                                 "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "swim fruit": {         "swim_ticks": (1, 4),            "swim_fly": -1,                                                                                 "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "run fruit": {          "run_ticks": (1, 4),             "run_power": -1,                                                                                "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "fly fruit": {          "fly_ticks": (1, 4),             "swim_fly": 1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
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


    def get_guild_user(ctx):
        return str(ctx.guild.id), ctx.guild.name, ctx.author

    def safe_int(val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def get_stat_levels(latest_stats):
        stats = ['swim', 'fly', 'run', 'power', 'stamina']
        return [safe_int(latest_stats.get(f"{s}_level") or latest_stats.get(f"{s.capitalize()}_level")) for s in stats]


    def get_background_for_chao_evolution(self, latest_stats: Dict) -> str:
        """Return background path for evolution, using the same logic as get_bg_path."""
        if not self.image_utils:
            return self.NEUTRAL_BG_PATH  # fallback if no ImageUtils cog

        align = latest_stats.get("Alignment", "neutral")
        form = str(latest_stats.get("Form", "1"))
        if form in ["3", "4"]:
            if align == "hero":
                return self.HERO_BG_PATH
            elif align == "dark":
                return self.DARK_BG_PATH
            else:
                return self.NEUTRAL_BG_PATH
        return self.NEUTRAL_BG_PATH

    def generate_evolution_image(self, bg_path, overlay_img, safe_name):
        """
        Generates a lifecycle/evolution image by overlaying `overlay_img` onto `bg_path`.
        Returns a discord.File object of the composite image.
        """
        # Use self.assets_dir instead of ASSETS_DIR
        temp_folder = os.path.join(self.assets_dir, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")


        with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_img).convert("RGBA") as overlay:
            overlay = overlay.resize(bg.size)
            Image.alpha_composite(bg, overlay).save(temp_output)

        return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")




    async def feed(self, ctx, *, chao_name_and_fruit: str):
        """
        Feeds a particular fruit to a Chao multiple times.
        Syntax:
        $feed <chao_name> <fruit_name> [quantity]

        - If quantity is omitted, defaults to 1.
        - Only allows multiple units of the SAME fruit in one command.
        - Form 2 Chao can shift alignment on each feeding.
        - Form 3/4 Chao remain locked in advanced form alignment.
        - Level-ups and changes are aggregated into a single summary.
        - A Chao's stat level can NOT exceed level 99.
        - If a Chao is Form 3 and any stat >= 20 after feeding, evolution triggers immediately.
        (Evolution is now stored in the DB, so it persists if the bot restarts.)
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

                # B) Trainable stats => 0-9 ticks => level up => up to level 99
                elif stat.endswith("_ticks"):
                    level_key = stat.replace("_ticks", "_level")
                    grade_key = stat.replace("_ticks", "_grade")
                    exp_key = stat.replace("_ticks", "_exp")

                    old_level = latest_stats.get(level_key, 0)
                    if old_level >= 99:
                        continue  # Already maxed

                    remaining = increment
                    while remaining > 0:
                        curr_ticks = latest_stats.get(stat, 0)
                        space_until_level = 9 - curr_ticks
                        to_add = min(remaining, space_until_level + 1)
                        new_val = curr_ticks + to_add
                        remaining -= to_add

                        if new_val > 9:
                            old_level = latest_stats.get(level_key, 0)
                            new_level = old_level + 1
                            if new_level > 99:
                                new_level = 99
                            latest_stats[level_key] = new_level
                            if new_level > old_level and new_level <= 99:
                                levels_gained[level_key] += 1
                                grade = latest_stats.get(grade_key, 'F')
                                old_exp = latest_stats.get(exp_key, 0)
                                latest_stats[exp_key] = old_exp + self.get_stat_increment(grade)
                            latest_stats[stat] = 0
                            if new_level >= 99:
                                break
                        else:
                            net_gain = new_val - curr_ticks
                            if net_gain > 0:
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
        updated_inventory = {
            k: normalized_inventory.get(k.lower(), 0)
            for k in current_inv.keys()
        }
        self.data_utils.save_inventory(inv_path, inv_df, updated_inventory)

        # 9) Update chao form / thumbnail
        prev_form = str(latest_stats.get("Form", "1"))
        chao_type, form = self.update_chao_type_and_thumbnail(
            guild_id, guild_name, user, chao_name, latest_stats
        )
        latest_stats["Form"] = form
        latest_stats["Type"] = chao_type

        # --- Evolve from Form 2 -> Form 3: Upgrade grade letter accordingly ---
        if prev_form == "2" and form == "3":
            # Instead of checking run_power, derive the type from the new chao_type.
            suffix = chao_type.split("_")[1]  # e.g. "power", "fly", "run", or "swim"
            stat_to_upgrade = {
                "fly": "fly_grade",
                "power": "power_grade",
                "run": "run_grade",
                "swim": "swim_grade"
            }.get(suffix)
            if stat_to_upgrade:
                current_grade = latest_stats.get(stat_to_upgrade, 'F')
                new_grade_index = min(len(self.GRADES) - 1, self.GRADES.index(current_grade) + 1)
                latest_stats[stat_to_upgrade] = self.GRADES[new_grade_index]
                levels_gained[stat_to_upgrade] += 1

        # Save updated stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # -----------------------------
        #  MERGED EVOLUTION LOGIC HERE
        # -----------------------------
        current_form = str(latest_stats.get("Form", "1"))
        if current_form == "3":
            stats_of_interest = ["swim_level", "fly_level", "run_level", "power_level", "stamina_level"]
            if any(int(latest_stats.get(s, 0)) >= 20 for s in stats_of_interest):
                # If not already evolving:
                if not latest_stats.get("evolution_end_time"):
                    now = datetime.now()
                    evolution_end = now + timedelta(seconds=60)
                    latest_stats["evolution_end_time"] = evolution_end.isoformat()
                    latest_stats["evolution_seconds_left"] = 60
                    latest_stats["cacoon"] = 1  # Mark that the Chao is in a cocoon

                    self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

                    # Always use NEUTRAL background for the evolving embed:
                    bg_path = os.path.join(self.assets_dir, "graphics", "thumbnails", "neutral_background.png")
                    overlay_img = os.path.join(self.assets_dir, "graphics", "cacoons", "cacoon_evolve.png")
                    safe_name = chao_name.replace(" ", "_")
                    file = self.generate_evolution_image(bg_path, overlay_img, safe_name)

                    embed = discord.Embed(
                        title="Chao Is Evolving!",
                        description=(
                            f"{ctx.author.mention}, your chao **{chao_name}** is evolving.\n"
                            "You cannot interact for 60 seconds. "
                        ),
                        color=discord.Color.purple()
                    )
                    embed.set_thumbnail(url=f"attachment://{file.filename}")
                    await ctx.reply(embed=embed, file=file)
                    return

        # If NOT evolving, show normal feed results
        feed_summary = f"{chao_name} ate {quantity} {matched_fruit}!"
        if quantity == 1:
            feed_summary = f"{chao_name} ate a {matched_fruit}!"

        stat_lines = []
        for stat, net_gain in ticks_changes.items():
            base_name = stat.replace("_ticks", "").capitalize()
            final_val = latest_stats.get(stat, 0)
            cap = 10 if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"] else 9
            sign = "+" if net_gain > 0 else ""
            stat_lines.append(f"{base_name} {sign}{net_gain} ({final_val}/{cap})")

        for a_stat, net_align in alignment_changes.items():
            if a_stat == "dark_hero":
                continue
            sign = "+" if net_align > 0 else ""
            final_val = latest_stats.get(a_stat, 0)
            base = a_stat.replace("_", "/").capitalize()
            stat_lines.append(f"{base} {sign}{net_align} (→ {final_val}/5)")

        for lvl_key, times_gained in levels_gained.items():
            if lvl_key.endswith("_level"):
                short_name = lvl_key.replace("_level", "").capitalize()
                new_level = latest_stats.get(lvl_key, 0)
                stat_lines.append(f"{short_name} leveled up to {new_level}")
            elif lvl_key.endswith("_grade"):
                short_name = lvl_key.replace("_grade", "").capitalize()
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

        chao_dir = self.data_utils.get_path(guild_id, guild_name, ctx.author, 'chao_data', chao_name)
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

        # CREATE THE VIEW. If this is a fresh command, we might assume page=1
        view_data = {
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user_id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        }

        view = StatsView.from_data(view_data, self)



        def save_persistent_view(self, view_data: Dict):
            """Example function that saves the view to JSON, so we can restore on startup."""
            try:
                with open(PERSISTENT_VIEWS_FILE, "r") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}

            key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data['chao_name']}"
            data[key] = view_data

            with open(PERSISTENT_VIEWS_FILE, "w") as f:
                json.dump(data, f)

        def load_persistent_views(self):
            """
            On bot startup, we read from JSON for each old view, call `StatsView.from_data` once,
            and then do `self.bot.add_view(...)` so it can handle button clicks for that old view.
            """
            if os.path.exists(PERSISTENT_VIEWS_FILE):
                with open(PERSISTENT_VIEWS_FILE, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        return

                for key, view_data in data.items():
                    # Check required keys, etc.
                    if not all(k in view_data for k in ("chao_name", "guild_id", "user_id", "chao_type_display", "alignment_label", "total_pages", "current_page")):
                        continue

                    # If the user left the view on page2, we see "current_page": 2
                    view = StatsView.from_data(view_data, self)
                    self.bot.add_view(view)


        # Optionally, save so that if the bot restarts, we can restore
        self.save_persistent_view(view_data)

        await ctx.reply(
            files=[
                discord.File(stats_image_paths[1], "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(thumbnail_path, filename="chao_thumbnail.png"),
            ],
            embed=embed,
            view=view
        )




    async def force_life_check(self, ctx, *, chao_name: str):
        """Force check a chao's life cycle: either reincarnate or die if older than 60 days."""
        g, u = str(ctx.guild.id), str(ctx.author.id)
        p, l, s, o, t, e = self.data_utils.get_path, self.data_utils.load_chao_stats, \
                           self.data_utils.save_chao_stats, os.path, datetime.now, discord.Embed

        f = o.join(p(g, u, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not o.exists(f):
            return await ctx.reply(embed=e(description=f"{ctx.author.mention}, no Chao named **{chao_name}** exists.", color=0xFF0000))

        c, d = l(f), l(f).iloc[-1].to_dict()
        m = (
            f"✨ **{chao_name} has reincarnated! A fresh start begins!**"
            if d.get('happiness_ticks', 0) > 5
            else f"😢 **{chao_name} has passed away due to low happiness.**"
        )

        if d.get('happiness_ticks', 0) > 5:
            new_data = {
                "reincarnations": d.get('reincarnations', 0) + 1,
                "happiness_ticks": 10,
                "birth_date": t().strftime("%Y-%m-%d"),
                **{
                    f"{x}_{y}": 0
                    for x in ['swim', 'fly', 'run', 'power', 'stamina']
                    for y in ['ticks', 'level', 'exp']
                }
            }
        else:
            new_data = {**d, "dead": 1}

        s(f, c, new_data)
        color_val = 0x00FF00 if "reincarnated" in m else 0x8B0000
        await ctx.reply(embed=e(description=m, color=color_val))

    async def force_happiness(self, ctx, *, chao_name: str, happiness_value: int):
        """Set a chao's happiness to a specific value."""
        g, u = str(ctx.guild.id), str(ctx.author.id)
        p, l, s, o, e = self.data_utils.get_path, self.data_utils.load_chao_stats, \
                        self.data_utils.save_chao_stats, os.path, discord.Embed

        f = o.join(p(g, u, 'chao_data', chao_name), f"{chao_name}_stats.parquet")
        if not o.exists(f):
            return await ctx.reply(embed=e(description=f"{ctx.author.mention}, no Chao named **{chao_name}** exists.", color=0xFF0000))

        c = l(f)
        d = c.iloc[-1].to_dict()
        d['happiness_ticks'] = happiness_value
        s(f, c, d)

        await ctx.reply(embed=e(
            description=f"✅ **{chao_name}'s happiness has been set to {happiness_value}.**",
            color=0x00FF00
        ))



        def save_persistent_view(self, view_data: Dict):
            """Example function that saves the view to JSON, so we can restore on startup."""
            try:
                with open(PERSISTENT_VIEWS_FILE, "r") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}

            key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data['chao_name']}"
            data[key] = view_data

            with open(PERSISTENT_VIEWS_FILE, "w") as f:
                json.dump(data, f)

        def load_persistent_views(self):
            """
            On bot startup, we read from JSON for each old view, call `StatsView.from_data` once,
            and then do `self.bot.add_view(...)` so it can handle button clicks for that old view.
            """
            if os.path.exists(PERSISTENT_VIEWS_FILE):
                with open(PERSISTENT_VIEWS_FILE, "r") as f:
                    try:
                        data = json.load(f)
                    except json.JSONDecodeError:
                        return

                for key, view_data in data.items():
                    # Check required keys, etc.
                    if not all(k in view_data for k in ("chao_name", "guild_id", "user_id", "chao_type_display", "alignment_label", "total_pages", "current_page")):
                        continue

                    # If the user left the view on page2, we see "current_page": 2
                    view = StatsView.from_data(view_data, self)
                    self.bot.add_view(view)


        # Optionally, save so that if the bot restarts, we can restore
        self.save_persistent_view(view_data)

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

        # IMPORTANT:
        # Instead of overwriting self.current_page with whatever's in the JSON,
        # we trust the constructor argument if we are building a brand-new View:
        self.current_page = current_page

        # We can still do a one-time save if we want:
        self.save_state()

        # Add navigation
        self.add_navigation_buttons()

    def save_state(self):
        """
        Only call *once* or on changes. Do *not* re-load again in the same button click,
        or you'll revert to old JSON data.
        """
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
        """
        If we do want to restore from disk, do so only once at init if needed.
        But typically you won't re-call this inside the same button press,
        because it overwrites the new page change.
        """
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                try:
                    data = json.load(f)
                    key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
                    return data.get(key, {}).get("current_page", default_page)
                except json.JSONDecodeError:
                    pass
        return default_page

    def add_navigation_buttons(self):
        self.clear_items()
        self.add_item(
            self.create_button("⬅️", "previous_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_prev")
        )
        self.add_item(
            self.create_button("➡️", "next_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_next")
        )

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def previous_page(self, interaction: discord.Interaction):
        # Decrement in memory
        self.current_page = self.total_pages if self.current_page == 1 else self.current_page - 1
        # Save to JSON so if the bot restarts, we pick up here
        self.save_state()
        await self.update_stats(interaction)

    async def next_page(self, interaction: discord.Interaction):
        # Increment in memory
        self.current_page = 1 if self.current_page == self.total_pages else self.current_page + 1
        self.save_state()
        await self.update_stats(interaction)

    async def update_stats(self, interaction: discord.Interaction):
        """Just re-draw using the in-memory page (self.current_page)."""
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

        # Build the page image name based on self.current_page
        page_image_filename = f'{self.chao_name}_stats_page_{self.current_page}.png'
        image_path = os.path.join(chao_dir, page_image_filename)

        if self.current_page == 1:
            # Generate page 1
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
            # Generate page 2
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

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=self.chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=self.alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://stats_page.png")
        embed.set_footer(text=f"Page {self.current_page} / {self.total_pages}")

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
        """
        If we want to restore from disk, we do it once here.
        But once the user is actively paging, do not keep re-calling from_data.
        """
        # If we want to use the JSON-saved 'current_page' from the dictionary, we can do so directly:
        current_page = view_data.get("current_page", 1)

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
            current_page=current_page,  # <-- keep it
            state_file=PERSISTENT_VIEWS_FILE
        )


async def setup(bot):
    """Standard async setup for this cog."""
    await bot.add_cog(ChaoHelper(bot))
