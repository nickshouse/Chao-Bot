# cogs/chao_lifecycle.py

import os, json, random, asyncio, discord, pandas as pd, collections
from PIL import Image
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Dict, Optional
from views.stats_view import StatsView
from config import (
    FRUIT_STATS_ADJUSTMENTS, FRUITS,
    FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4,
    ALIGNMENTS,
    HERO_BG_PATH, DARK_BG_PATH, NEUTRAL_BG_PATH,
    ASSETS_DIR,
    PAGE1_TICK_POSITIONS, PAGE2_TICK_POSITIONS,
    GRADE_RANGES,
    PERSISTENT_VIEWS_FILE,
    CHAO_TYPES
)

class ChaoLifecycle(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.fruit_stats_adjustments = FRUIT_STATS_ADJUSTMENTS
        self.fruits = FRUITS
        self.assets_dir = ASSETS_DIR
        self.GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.embed_color = discord.Color.blue()
        # Template and asset paths
        self.TEMPLATE_PATH = os.path.join(ASSETS_DIR, "graphics", "cards", "stats_page_1.png")
        self.TEMPLATE_PAGE_2_PATH = os.path.join(ASSETS_DIR, "graphics", "cards", "stats_page_2.png")
        self.OVERLAY_PATH = os.path.join(ASSETS_DIR, "graphics", "ticks", "tick_filled.png")
        self.ICON_PATH = os.path.join(ASSETS_DIR, "graphics", "icons", "Stats.png")
        self.PAGE1_TICK_POSITIONS = PAGE1_TICK_POSITIONS
        self.PAGE2_TICK_POSITIONS = PAGE2_TICK_POSITIONS
        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4
        self.HERO_BG_PATH, self.DARK_BG_PATH, self.NEUTRAL_BG_PATH = HERO_BG_PATH, DARK_BG_PATH, NEUTRAL_BG_PATH
        self.BACKGROUND_PATH = NEUTRAL_BG_PATH
        self.EYES_DIR = os.path.join(ASSETS_DIR, "face", "eyes")
        self.MOUTH_DIR = os.path.join(ASSETS_DIR, "face", "mouth")
        self.PERSISTENT_VIEWS_FILE = PERSISTENT_VIEWS_FILE

    async def cog_load(self):
        self.data_utils = self.bot.get_cog("DataUtils")
        if not self.data_utils:
            raise Exception("ChaoLifecycle requires DataUtils cog to be loaded.")
        self.image_utils = self.bot.get_cog("ImageUtils")
        if not self.image_utils:
            print("Warning: ImageUtils cog not loaded. Some features may fail.")

    async def _send(self, interaction: discord.Interaction, **kwargs):
        """
        Helper to send a response with interactions. Uses the initial response if not done,
        otherwise sends a followup.
        """
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)

    @staticmethod
    def _read_json(file_path: str, default: dict = None) -> dict:
        default = default or {}
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    @staticmethod
    def _write_json(file_path: str, data: dict):
        with open(file_path, "w") as f:
            json.dump(data, f)

    def save_persistent_view(self, view_data: Dict):
        data = self._read_json(PERSISTENT_VIEWS_FILE)
        key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data['chao_name']}"
        data[key] = view_data
        self._write_json(PERSISTENT_VIEWS_FILE, data)

    def load_persistent_views(self):
        for view_data in self._read_json(PERSISTENT_VIEWS_FILE).values():
            if not all(k in view_data for k in ("chao_name", "guild_id", "user_id", "chao_type_display", "alignment_label", "total_pages", "current_page")):
                continue
            view = StatsView.from_data(view_data, self)
            self.bot.add_view(view)

    def safe_int(self, val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    def generate_evolution_image(self, bg_path, overlay_img, safe_name):
        temp_folder = os.path.join(self.assets_dir, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")
        with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_img).convert("RGBA") as overlay:
            overlay = overlay.resize(bg.size)
            Image.alpha_composite(bg, overlay).save(temp_output)
        return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

    def generate_reincarnation_image(self, latest_stats: dict, safe_name: str):
        """
        Pick a background based on the chao's stats (e.g., alignment),
        overlay the reincarnation cocoon, and return a discord.File.
        """
        alignment_val = latest_stats.get("dark_hero", 0)
        if alignment_val > 0:
            bg_file = "hero_background.png"
        elif alignment_val < 0:
            bg_file = "dark_background.png"
        else:
            bg_file = "neutral_background.png"

        bg_path = os.path.join(self.assets_dir, "graphics", "thumbnails", bg_file)
        overlay_path = os.path.join(self.assets_dir, "graphics", "cacoons", "cacoon_reincarnate.png")
        
        temp_folder = os.path.join(self.assets_dir, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")

        with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
            overlay = overlay.resize(bg.size)
            Image.alpha_composite(bg, overlay).save(temp_output)

        return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

    def generate_death_image(self, latest_stats: dict, safe_name: str):
        """
        Pick a background based on the chao's stats (e.g., alignment),
        overlay the death cocoon, and return a discord.File.
        """
        alignment_val = latest_stats.get("dark_hero", 0)
        if alignment_val > 0:
            bg_file = "hero_background.png"
        elif alignment_val < 0:
            bg_file = "dark_background.png"
        else:
            bg_file = "neutral_background.png"

        bg_path = os.path.join(self.assets_dir, "graphics", "thumbnails", bg_file)
        overlay_path = os.path.join(self.assets_dir, "graphics", "cacoons", "cacoon_death.png")
        
        temp_folder = os.path.join(self.assets_dir, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")

        with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
            overlay = overlay.resize(bg.size)
            Image.alpha_composite(bg, overlay).save(temp_output)

        return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

    def update_chao_type_and_thumbnail(
        self, guild_id: str, guild_name: str, user: discord.Member, chao_name: str, latest_stats: Dict
    ) -> (str, str):
        try:
            chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

            stat_levels = {s: latest_stats.get(f"{s}_level", 0) for s in ["power", "swim", "stamina", "fly", "run"]}
            max_level = max(stat_levels.values())

            print(f"[update_chao_type_and_thumbnail] >> Chao: {chao_name}")
            print(f"[update_chao_type_and_thumbnail] >> Stat levels: {stat_levels}, max_level={max_level}")

            for stat in ["dark_hero", "run_power", "swim_fly"]:
                old_val = latest_stats.get(stat, 0)
                clamped_val = max(min(old_val, 5), -5)
                latest_stats[stat] = clamped_val
                if old_val != clamped_val:
                    print(f"[update_chao_type_and_thumbnail] >> Clamped {stat}: {old_val} -> {clamped_val}")

            old_type = latest_stats.get("Type", "neutral_normal_1")
            old_form = str(latest_stats.get("Form", "1"))

            print(f"[update_chao_type_and_thumbnail] >> old_type={old_type}, old_form={old_form}")

            locked_alignment = None
            if old_form in {"3", "4"}:
                locked_alignment = old_type.split("_")[0] if "_" in old_type else "neutral"
            print(f"[update_chao_type_and_thumbnail] >> locked_alignment={locked_alignment}")

            if old_form in {"3", "4"} and max_level < self.FORM_LEVEL_4:
                print(f"[update_chao_type_and_thumbnail] >> No re-type needed; form={old_form}, max_level={max_level}, threshold={self.FORM_LEVEL_4}")
                return old_type, old_form

            if locked_alignment is not None:
                alignment = locked_alignment
            else:
                dh_val = latest_stats["dark_hero"]
                if dh_val == 5:
                    alignment = "hero"
                elif dh_val == -5:
                    alignment = "dark"
                else:
                    alignment = "neutral"
            latest_stats["Alignment"] = alignment
            print(f"[update_chao_type_and_thumbnail] >> alignment={alignment}")

            def determine_suffix(rp, sf):
                if rp == 5:
                    return "power"
                elif rp == -5:
                    return "run"
                elif sf == 5:
                    return "fly"
                elif sf == -5:
                    return "swim"
                else:
                    return "normal"

            rp_val = latest_stats["run_power"]
            sf_val = latest_stats["swim_fly"]
            suffix = determine_suffix(rp_val, sf_val)

            print(f"[update_chao_type_and_thumbnail] >> run_power={rp_val}, swim_fly={sf_val}, suffix={suffix}")

            current_form = str(latest_stats.get("Form", "1"))
            print(f"[update_chao_type_and_thumbnail] >> current_form before thresholds: {current_form}")
            if current_form == "1" and max_level >= self.FORM_LEVEL_2:
                current_form = "2"
            if current_form == "2" and max_level >= self.FORM_LEVEL_3:
                current_form = "3"
            if current_form == "3" and max_level >= self.FORM_LEVEL_4:
                current_form = "4"
            print(f"[update_chao_type_and_thumbnail] >> current_form after thresholds: {current_form}")

            if current_form == "1":
                chao_type = f"{alignment}_normal_1"
            elif current_form == "2":
                chao_type = f"{alignment}_normal_{suffix}_2"
            elif current_form == "3":
                chao_type = f"{alignment}_{suffix}_3"
            else:
                old_parts = old_type.split("_")
                print(f"[update_chao_type_and_thumbnail] >> Evolving to form 4. old_parts={old_parts}")
                if old_form == "4" and len(old_parts) == 4:
                    prefix = old_parts[1]
                    chao_type = f"{old_parts[0]}_{prefix}_{suffix}_4"
                    print(f"[update_chao_type_and_thumbnail] >> Re-used prefix from old form 4: prefix={prefix}")
                elif old_form == "3" and old_type.endswith("_3"):
                    if len(old_parts) >= 3:
                        old_prefix = old_parts[-2]
                        print(f"[update_chao_type_and_thumbnail] >> Re-using prefix from old form 3: old_prefix={old_prefix}")
                        if old_prefix != "normal":
                            prefix = old_prefix
                        else:
                            prefix = suffix
                        chao_type = f"{alignment}_{prefix}_{suffix}_4"
                    else:
                        chao_type = f"{alignment}_normal_{suffix}_4"
                else:
                    chao_type = f"{alignment}_normal_{suffix}_4"

                if chao_type.endswith("normal_normal_4"):
                    print(f"[update_chao_type_and_thumbnail] >> normal_normal_4 found, unifying to {alignment}_normal_normal_4")
                    chao_type = f"{alignment}_normal_normal_4"

            print(f"[update_chao_type_and_thumbnail] >> Final computed chao_type={chao_type}")
            latest_stats["Form"] = current_form
            latest_stats["Type"] = chao_type

            subfolder = chao_type.split("_")[1] if "_" in chao_type else "normal"
            sprite_path = os.path.join(self.assets_dir, "chao", subfolder, alignment, f"{chao_type}.png")
            if not os.path.exists(sprite_path):
                sprite_path = os.path.join(self.assets_dir, "chao", "chao_missing.png")
                print(f"[update_chao_type_and_thumbnail] >> sprite_path missing, using chao_missing.png")

            eyes = latest_stats.get("eyes", "neutral")
            mouth = latest_stats.get("mouth", "happy")
            eyes_image = os.path.join(
                self.EYES_DIR,
                f"{'neutral' if current_form in {'1','2'} else alignment}_{eyes}.png"
            )
            if not os.path.exists(eyes_image):
                eyes_image = os.path.join(self.EYES_DIR, "neutral.png")
                print(f"[update_chao_type_and_thumbnail] >> eyes_image missing, defaulting to neutral.png")

            mouth_image = os.path.join(self.MOUTH_DIR, f"{mouth}.png")
            if not os.path.exists(mouth_image):
                mouth_image = os.path.join(self.MOUTH_DIR, "happy.png")
                print(f"[update_chao_type_and_thumbnail] >> mouth_image missing, defaulting to happy.png")

            if current_form in {"3", "4"} and alignment == "hero":
                bg_path = self.HERO_BG_PATH
            elif current_form in {"3", "4"} and alignment == "dark":
                bg_path = self.DARK_BG_PATH
            elif current_form in {"3", "4"}:
                bg_path = self.NEUTRAL_BG_PATH
            else:
                bg_path = self.BACKGROUND_PATH

            print(f"[update_chao_type_and_thumbnail] >> Combining images with face. BG={bg_path}, sprite={sprite_path}")
            self.image_utils.combine_images_with_face(bg_path, sprite_path, eyes_image, mouth_image, thumbnail_path)

            print(f"[update_chao_type_and_thumbnail] >> DONE for {chao_name}: {old_form}->{current_form}, old_type={old_type}, new_type={chao_type}")
            return chao_type, current_form

        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] >> Exception: {e}")
            return "normal", "1"

    def lookup_chao_type(chao_type: str):
        """Given a chao type string (e.g. 'neutral_normal_1'), returns the description and form label
        from CHAO_TYPES. If not found, returns defaults."""
        filename = chao_type + ".png"
        for entry in CHAO_TYPES:
            if entry[0] == filename:
                return entry[1], entry[2]
        return "Unknown", "Unknown"

    async def feed(self, interaction: discord.Interaction, chao_name: str, fruit: str, amount: int):
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user

        chao_name = chao_name.strip()
        if not chao_name:
            return await self._send(interaction, content="Please specify which Chao you want to feed.")

        # Validate fruit
        if fruit.lower() not in [f.lower() for f in self.fruits]:
            valid = ", ".join(sorted(self.fruits))
            return await self._send(interaction, content=f"{interaction.user.mention}, provide a valid fruit. Valid fruits: {valid}")

        quantity = amount
        fruit_lower = fruit.lower()

        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(chao_dir) or not os.path.exists(chao_stats_path):
            return await self._send(interaction, content=f"{interaction.user.mention}, no Chao named **{chao_name}** exists or stats file is missing.")

        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        norm_inv = {k.lower(): v for k, v in current_inv.items()}
        have_amount = norm_inv.get(fruit_lower, 0)

        if have_amount < quantity:
            return await self._send(interaction, content=f"{interaction.user.mention}, you only have **{have_amount}** {fruit}, but tried to feed {quantity}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].to_dict()

        ticks_changes, align_changes, levels_gained = (
            collections.defaultdict(int),
            collections.defaultdict(int),
            collections.defaultdict(int)
        )
        clamp = lambda v, lo, hi: max(lo, min(v, hi))

        def apply_fruit_once():
            nonlocal latest_stats
            special = fruit_lower in {"swim fruit", "fly fruit", "run fruit", "power fruit"}

            if special:
                if fruit_lower == "swim fruit":
                    old = latest_stats.get("swim_fly", 0)
                    new = max(old - 1, -5)
                    latest_stats["swim_fly"] = new
                    old_run = latest_stats.get("run_power", 0)
                    if old_run > 0:
                        latest_stats["run_power"] = old_run - 1
                    elif old_run < 0:
                        latest_stats["run_power"] = old_run + 1
                    align_changes["swim_fly"] += new - old

                elif fruit_lower == "fly fruit":
                    old = latest_stats.get("swim_fly", 0)
                    new = min(old + 1, 5)
                    latest_stats["swim_fly"] = new
                    old_run = latest_stats.get("run_power", 0)
                    if old_run > 0:
                        latest_stats["run_power"] = old_run - 1
                    elif old_run < 0:
                        latest_stats["run_power"] = old_run + 1
                    align_changes["swim_fly"] += new - old

                elif fruit_lower == "run fruit":
                    old = latest_stats.get("run_power", 0)
                    new = max(old - 1, -5)
                    latest_stats["run_power"] = new
                    old_swim = latest_stats.get("swim_fly", 0)
                    if old_swim > 0:
                        latest_stats["swim_fly"] = old_swim - 1
                    elif old_swim < 0:
                        latest_stats["swim_fly"] = old_swim + 1
                    align_changes["run_power"] += new - old

                elif fruit_lower == "power fruit":
                    old = latest_stats.get("run_power", 0)
                    new = min(old + 1, 5)
                    latest_stats["run_power"] = new
                    old_swim = latest_stats.get("swim_fly", 0)
                    if old_swim > 0:
                        latest_stats["swim_fly"] = old_swim - 1
                    elif old_swim < 0:
                        latest_stats["swim_fly"] = old_swim + 1
                    align_changes["run_power"] += new - old

            adjustments = self.fruit_stats_adjustments.get(fruit_lower, {})
            if special:
                adjustments = {k: v for k, v in adjustments.items() if k not in {"run_power", "swim_fly"}}

            for stat, adj in adjustments.items():
                inc = random.randint(*adj) if isinstance(adj, tuple) else adj
                if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"]:
                    old = latest_stats.get(stat, 0)
                    if old < 10:
                        new = clamp(old + inc, 0, 10)
                        gain = new - old
                        if gain > 0:
                            ticks_changes[stat] += gain
                            latest_stats[stat] = new

                elif stat.endswith("_ticks"):
                    level_key = stat.replace("_ticks", "_level")
                    grade_key = stat.replace("_ticks", "_grade")
                    exp_key = stat.replace("_ticks", "_exp")
                    if latest_stats.get(level_key, 0) >= 99:
                        continue
                    remaining = inc
                    while remaining > 0:
                        curr = latest_stats.get(stat, 0)
                        to_add = min(remaining, 10 - curr)
                        new = curr + to_add
                        remaining -= to_add
                        if new >= 10:
                            old_level = latest_stats.get(level_key, 0)
                            new_level = min(old_level + 1, 99)
                            latest_stats[level_key] = new_level
                            if new_level > old_level:
                                levels_gained[level_key] += 1
                                grade = latest_stats.get(grade_key, 'F')
                                chao_cog = self.bot.get_cog("Chao")
                                latest_stats[exp_key] = latest_stats.get(exp_key, 0) + chao_cog.get_stat_increment(grade)
                            latest_stats[stat] = 0
                        else:
                            gain = new - curr
                            if gain > 0:
                                ticks_changes[stat] += gain
                                latest_stats[stat] = new

                elif stat in ["run_power", "swim_fly", "dark_hero"]:
                    old = latest_stats.get(stat, 0)
                    new = clamp(old + inc, -5, 5)
                    delta = new - old
                    if delta:
                        align_changes[stat] += delta
                    latest_stats[stat] = new

        for _ in range(quantity):
            apply_fruit_once()

        norm_inv[fruit_lower] = have_amount - quantity
        updated_inv = {k: norm_inv.get(k.lower(), 0) for k in current_inv}
        self.data_utils.save_inventory(inv_path, inv_df, updated_inv)

        old_form = str(latest_stats.get("Form", "1"))
        old_type = latest_stats.get("Type", "")

        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, guild_name, user, chao_name, latest_stats)
        latest_stats["Form"] = form
        latest_stats["Type"] = chao_type

        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        if latest_stats.get("happiness_ticks", 0) > 5:
            if await self.reincarnation(
                interaction, chao_name, latest_stats, chao_df, chao_stats_path,
                f"{chao_name} ate {'a' if quantity == 1 else quantity} {fruit}!",
                ticks_changes, align_changes, levels_gained
            ):
                return
        elif latest_stats.get("happiness_ticks", 0) <= 5:
            if await self.death(
                interaction, chao_name, latest_stats, chao_df, chao_stats_path,
                f"{chao_name} ate {'a' if quantity == 1 else quantity} {fruit}!",
                ticks_changes, align_changes, levels_gained
            ):
                return

        if await self.evolution(
            interaction, chao_name, latest_stats, chao_df, chao_stats_path,
            f"{chao_name} ate {'a' if quantity == 1 else quantity} {fruit}!",
            ticks_changes, align_changes, levels_gained
        ):
            return

        feed_summary = f"ate {'a' if quantity == 1 else quantity} {fruit}!"
        stat_lines = []
        for stat, gain in ticks_changes.items():
            base = stat.replace("_ticks", "").capitalize()
            final = latest_stats.get(stat, 0)
            cap = 10 if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"] else 9
            stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} ({final}/{cap})")

        for a, gain in align_changes.items():
            if a == "dark_hero":
                continue
            final = latest_stats.get(a, 0)
            base = a.replace("_", "/").capitalize()
            stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} (→ {final}/5)")

        for key, times in levels_gained.items():
            if key.endswith("_level"):
                stat_lines.append(f"{key.replace('_level','').capitalize()} leveled up to {latest_stats.get(key, 0)}")
            elif key.endswith("_grade"):
                stat_lines.append(f"{key.replace('_grade','').capitalize()} grade improved to {latest_stats.get(key, 'F')}")

        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
        if not os.path.exists(thumbnail_path):
            return await self._send(interaction, content=f"{interaction.user.mention}, thumbnail file is missing for **{chao_name}**.")

        evolution_text = "has finished evolving!\n" if latest_stats.get("evolve_cacoon", 0) == 1 else ""
        description = (
            f"{interaction.user.mention}, your chao **{chao_name}** {evolution_text}"
            + feed_summary
            + ("\n\n" + "\n".join(stat_lines) if stat_lines else "")
        )
        embed = discord.Embed(
            title="Chao Feed Success",
            description=description,
            color=self.embed_color
        )
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")

        with open(thumbnail_path, 'rb') as f:
            thumb = discord.File(f, filename="chao_thumbnail.png")
            await self._send(interaction, embed=embed, file=thumb)

    async def evolution(self, interaction: discord.Interaction, chao_name: str, latest_stats: dict, chao_df, chao_stats_path: str,
                        feed_summary: str = "", ticks_changes: dict = None,
                        align_changes: dict = None, levels_gained: dict = None) -> bool:
        if ticks_changes is None:
            ticks_changes = {}
        if align_changes is None:
            align_changes = {}
        if levels_gained is None:
            levels_gained = {}

        if latest_stats.get("evolved", 0) == 1:
            return False

        if str(latest_stats.get("Form", "1")) == "3" and any(
            int(latest_stats.get(s, 0)) >= 20 for s in ["swim_level", "fly_level", "run_level", "power_level", "stamina_level"]
        ):
            now = datetime.now()
            evolution_end = now + timedelta(seconds=60)
            latest_stats["evolution_end_time"] = evolution_end.isoformat()
            latest_stats["evolution_seconds_left"] = 60
            latest_stats["evolve_cacoon"] = 1
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)
            
            seconds_left = 60

            stat_lines = []
            for stat, gain in ticks_changes.items():
                base = stat.replace("_ticks", "").capitalize()
                final = latest_stats.get(stat, 0)
                cap = 10 if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"] else 9
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} ({final}/{cap})")

            for a, gain in align_changes.items():
                if a == "dark_hero":
                    continue
                final = latest_stats.get(a, 0)
                base = a.replace("_", "/").capitalize()
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} (→ {final}/5)")

            for key, times in levels_gained.items():
                if key.endswith("_level"):
                    stat_lines.append(f"{key.replace('_level','').capitalize()} leveled up to {latest_stats.get(key, 0)}")
                elif key.endswith("_grade"):
                    stat_lines.append(f"{key.replace('_grade','').capitalize()} grade improved to {latest_stats.get(key, 'F')}")

            feed_results = feed_summary + ("\n\n" + "\n".join(stat_lines) if stat_lines else "")
            desc_static = f"{feed_results}\n\n **{chao_name}** is evolving!\n"

            embed = discord.Embed(
                title="Chao Is Evolving!",
                description=f"{desc_static}\nTime remaining: {seconds_left} seconds.",
                color=discord.Color.purple()
            )
            bg_path = os.path.join(self.assets_dir, "graphics", "thumbnails", "neutral_background.png")
            overlay_img = os.path.join(self.assets_dir, "graphics", "cacoons", "cacoon_evolve.png")
            safe_name = chao_name.replace(" ", "_")
            file = self.generate_evolution_image(bg_path, overlay_img, safe_name)
            embed.set_thumbnail(url=f"attachment://{file.filename}")
            await self._send(interaction, embed=embed, file=file)

            await asyncio.sleep(seconds_left)

            chao_type = latest_stats.get("Type", "")
            if chao_type:
                parts = chao_type.split("_")
                if len(parts) >= 3:
                    suffix = parts[1]
                    type_grade_mapping = {
                        "run": "run_grade",
                        "fly": "fly_grade",
                        "power": "power_grade",
                        "swim": "swim_grade",
                        "normal": "stamina_grade"
                    }
                    stat_key = type_grade_mapping.get(suffix)
                    if stat_key:
                        current_grade = latest_stats.get(stat_key, "F")
                        try:
                            new_index = min(len(self.GRADES) - 1, self.GRADES.index(current_grade) + 1)
                            latest_stats[stat_key] = self.GRADES[new_index]
                        except ValueError:
                            pass

            latest_stats.pop("evolution_end_time", None)
            latest_stats.pop("evolution_seconds_left", None)
            latest_stats["evolve_cacoon"] = 0
            latest_stats["evolved"] = 1

            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
            chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
            if not os.path.exists(thumbnail_path):
                await self._send(interaction, content=f"{interaction.user.mention}, thumbnail file is missing for **{chao_name}**.")
            else:
                final_embed = discord.Embed(
                    title="Chao Evolved!",
                    description=f"{interaction.user.mention}, your chao **{chao_name}** has finished evolving!",
                    color=self.embed_color
                )
                final_embed.set_thumbnail(url="attachment://chao_thumbnail.png")
                with open(thumbnail_path, 'rb') as f:
                    thumb = discord.File(f, filename="chao_thumbnail.png")
                    await self._send(interaction, embed=final_embed, file=thumb)

            return True

        return False

    async def reincarnation(self, interaction: discord.Interaction, chao_name: str, latest_stats: dict, chao_df, chao_stats_path: str,
                            feed_summary: str = "", ticks_changes: dict = None,
                            align_changes: dict = None, levels_gained: dict = None) -> bool:
        if ticks_changes is None:
            ticks_changes = {}
        if align_changes is None:
            align_changes = {}
        if levels_gained is None:
            levels_gained = {}

        if (str(latest_stats.get("Form", "1")) == "4" and 
            latest_stats.get("happiness_ticks", 0) >= 5 and
            any(int(latest_stats.get(s, 0)) >= 99 for s in ["swim_level", "fly_level", "run_level", "power_level", "stamina_level"])):
            now = datetime.now()
            reincarnation_end = now + timedelta(seconds=60)
            latest_stats["reincarnation_end_time"] = reincarnation_end.isoformat()
            latest_stats["reincarnation_seconds_left"] = 60
            latest_stats["reincarnate_cacoon"] = 1
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            seconds_left = 60

            stat_lines = []
            for stat, gain in ticks_changes.items():
                base = stat.replace("_ticks", "").capitalize()
                final = latest_stats.get(stat, 0)
                cap = 10 if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"] else 9
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} ({final}/{cap})")
            for a, gain in align_changes.items():
                if a == "dark_hero":
                    continue
                final = latest_stats.get(a, 0)
                base = a.replace("_", "/").capitalize()
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} (→ {final}/5)")
            for key, times in levels_gained.items():
                if key.endswith("_level"):
                    stat_lines.append(f"{key.replace('_level','').capitalize()} leveled up to {latest_stats.get(key, 0)}")
                elif key.endswith("_grade"):
                    stat_lines.append(f"{key.replace('_grade','').capitalize()} grade improved to {latest_stats.get(key, 'F')}")
            feed_results = feed_summary + ("\n\n" + "\n".join(stat_lines) if stat_lines else "")
            desc_static = f"{feed_results}\n\n **{chao_name}** is reincarnating!\n"
            embed = discord.Embed(
                title="Chao Is Reincarnating!",
                description=f"{desc_static}\nTime remaining: {seconds_left} seconds.",
                color=discord.Color.purple()
            )
            safe_name = chao_name.replace(" ", "_")
            file = self.generate_reincarnation_image(latest_stats, safe_name)
            embed.set_thumbnail(url=f"attachment://{file.filename}")
            await self._send(interaction, embed=embed, file=file)

            await asyncio.sleep(seconds_left)

            latest_stats["reincarnations"] = int(latest_stats.get("reincarnations", 0)) + 1
            latest_stats["hatched"] = 0
            latest_stats.pop("reincarnation_end_time", None)
            latest_stats.pop("reincarnation_seconds_left", None)
            latest_stats["reincarnate_cacoon"] = 0
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
            inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
            inv_df = self.data_utils.load_inventory(inv_path)
            current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
            norm_inv = {k.lower(): v for k, v in current_inv.items()}
            egg_key = "chao egg"
            norm_inv[egg_key] = norm_inv.get(egg_key, 0) + 1
            if current_inv:
                updated_inv = {k: norm_inv.get(k.lower(), 0) for k in current_inv}
                if "Chao Egg" not in updated_inv:
                    updated_inv["Chao Egg"] = norm_inv[egg_key]
            else:
                updated_inv = {"Chao Egg": norm_inv[egg_key]}
            self.data_utils.save_inventory(inv_path, inv_df, updated_inv)

            egg_bg_path = os.path.join(self.assets_dir, "graphics", "thumbnails", "egg_background.png")
            if not os.path.exists(egg_bg_path):
                await self._send(interaction, content=f"{interaction.user.mention}, egg background file is missing.")
            else:
                final_embed = discord.Embed(
                    title="Chao Reincarnated!",
                    description=f"{interaction.user.mention}, your chao **{chao_name}** has been reborn and is now in an egg!",
                    color=self.embed_color
                )
                final_embed.set_thumbnail(url="attachment://egg_background.png")
                egg_file = discord.File(egg_bg_path, filename="egg_background.png")
                await self._send(interaction, embed=final_embed, file=egg_file)
            return True
        return False

    async def death(self, interaction: discord.Interaction, chao_name: str, latest_stats: dict, chao_df, chao_stats_path: str,
                    feed_summary: str = "", ticks_changes: dict = None,
                    align_changes: dict = None, levels_gained: dict = None) -> bool:
        if ticks_changes is None:
            ticks_changes = {}
        if align_changes is None:
            align_changes = {}
        if levels_gained is None:
            levels_gained = {}

        if (str(latest_stats.get("Form", "1")) == "4" and 
            latest_stats.get("happiness_ticks", 0) <= 5 and
            any(int(latest_stats.get(s, 0)) >= 99 for s in ["swim_level", "fly_level", "run_level", "power_level", "stamina_level"])):
            now = datetime.now()
            death_end = now + timedelta(seconds=60)
            latest_stats["death_end_time"] = death_end.isoformat()
            latest_stats["death_seconds_left"] = 60
            latest_stats["death_cacoon"] = 1
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            seconds_left = 60

            stat_lines = []
            for stat, gain in ticks_changes.items():
                base = stat.replace("_ticks", "").capitalize()
                final = latest_stats.get(stat, 0)
                cap = 10 if stat in ["hp_ticks", "belly_ticks", "energy_ticks", "happiness_ticks", "illness_ticks"] else 9
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} ({final}/{cap})")
            for a, gain in align_changes.items():
                if a == "dark_hero":
                    continue
                final = latest_stats.get(a, 0)
                base = a.replace("_", "/").capitalize()
                stat_lines.append(f"{base} {'+' if gain > 0 else ''}{gain} (→ {final}/5)")
            for key, times in levels_gained.items():
                if key.endswith("_level"):
                    stat_lines.append(f"{key.replace('_level','').capitalize()} leveled up to {latest_stats.get(key, 0)}")
                elif key.endswith("_grade"):
                    stat_lines.append(f"{key.replace('_grade','').capitalize()} grade improved to {latest_stats.get(key, 'F')}")
            feed_results = feed_summary + ("\n\n" + "\n".join(stat_lines) if stat_lines else "")
            desc_static = f"{feed_results}\n\n **{chao_name}** is dying!\n"
            embed = discord.Embed(
                title="Chao Is Dying!",
                description=f"{desc_static}\nTime remaining: {seconds_left} seconds.",
                color=discord.Color.dark_red()
            )
            safe_name = chao_name.replace(" ", "_")
            file = self.generate_death_image(latest_stats, safe_name)
            embed.set_thumbnail(url=f"attachment://{file.filename}")
            await self._send(interaction, embed=embed, file=file)

            await asyncio.sleep(seconds_left)

            latest_stats["deaths"] = int(latest_stats.get("deaths", 0)) + 1
            if not latest_stats.get("date_of_death"):
                latest_stats["date_of_death"] = datetime.now().strftime("%Y-%m-%d")
            latest_stats["dead"] = 1
            latest_stats["hp_ticks"] = 0
            latest_stats.pop("death_end_time", None)
            latest_stats.pop("death_seconds_left", None)
            latest_stats["death_cacoon"] = 0
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            d = latest_stats.get("date_of_death", datetime.now().strftime("%Y-%m-%d"))
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"{chao_name} can no longer be interacted with.\n\n**Date of Death:** {d}",
                color=discord.Color.dark_gray()
            )
            thumb = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "chao_grave.png")
            file = discord.File(thumb, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
            return await self._send(interaction, file=file, embed=embed)
        return False

async def setup(bot: commands.Bot):
    await bot.add_cog(ChaoLifecycle(bot))
