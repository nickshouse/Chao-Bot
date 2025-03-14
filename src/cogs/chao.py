# cogs/chao.py

import os, random, asyncio, discord, shutil, pandas as pd
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional
from config import (
    ASSETS_DIR, CHAO_NAMES, MOUTH_TYPES, EYE_TYPES, 
    FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4, GRADE_TO_VALUE,
    FRUIT_STATS_ADJUSTMENTS, SWIM_FLY_THRESHOLD, RUN_POWER_THRESHOLD,
    HERO_BG_PATH, DARK_BG_PATH, NEUTRAL_BG_PATH, EGG_BG_PATH, GRADES
)

class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        # Import chao names and facial variations from config.py.
        self.chao_names = CHAO_NAMES
        self.mouth_types = MOUTH_TYPES
        self.eye_types = EYE_TYPES

        # Use config.py values for configuration.
        self.FORM_LEVEL_2 = FORM_LEVEL_2
        self.FORM_LEVEL_3 = FORM_LEVEL_3
        self.FORM_LEVEL_4 = FORM_LEVEL_4
        self.GRADE_TO_VALUE = GRADE_TO_VALUE
        self.FRUIT_STATS_ADJUSTMENTS = FRUIT_STATS_ADJUSTMENTS
        self.RUN_POWER_THRESHOLD = RUN_POWER_THRESHOLD
        self.SWIM_FLY_THRESHOLD = SWIM_FLY_THRESHOLD
        self.HERO_BG_PATH = HERO_BG_PATH
        self.DARK_BG_PATH = DARK_BG_PATH
        self.NEUTRAL_BG_PATH = NEUTRAL_BG_PATH
        self.EGG_BG_PATH = EGG_BG_PATH
        self.GRADES = GRADES

    async def cog_load(self):
        """Called automatically when this Cog is loaded. We set up all required file paths here."""
        i, p, a = self.bot.get_cog, os.path.join, self.__setattr__
        self.image_utils, self.data_utils = i('ImageUtils'), i('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("Required cogs not loaded.")

        # Instead of using self.image_utils.assets_dir, we use the value from config.py.
        self.assets_dir = ASSETS_DIR

        # Define relevant file paths.
        [a(k, p(self.assets_dir, v)) for k, v in {
            'TEMPLATE_PATH': 'graphics/cards/stats_page_1.png',
            'TEMPLATE_PAGE_2_PATH': 'graphics/cards/stats_page_2.png',
            'OVERLAY_PATH': 'graphics/ticks/tick_filled.png',
            'ICON_PATH': 'graphics/icons/Stats.png',
            # Default background for forms 1 & 2.
            'BACKGROUND_PATH': 'graphics/thumbnails/neutral_background.png',
            'NEUTRAL_PATH': 'chao/normal/neutral/neutral_normal_1.png'
        }.items()]

        # Additional backgrounds (the paths here are still defined relative to ASSETS_DIR)
        a('HERO_BG_PATH', p(self.assets_dir, 'graphics', 'thumbnails', 'hero_background.png'))
        a('DARK_BG_PATH', p(self.assets_dir, 'graphics', 'thumbnails', 'dark_background.png'))
        a('NEUTRAL_BG_PATH', p(self.assets_dir, 'graphics', 'thumbnails', 'neutral_background.png'))

        a('PAGE1_TICK_POSITIONS', [(446, y) for y in [1176, 315, 591, 883, 1469]])
        a('PAGE2_TICK_POSITIONS', {
            k: (272, v) for k, v in zip(
                ['belly', 'happiness', 'illness', 'energy', 'hp'],
                [314, 590, 882, 1175, 1468]
            )
        })

        # Directories for eyes and mouth.
        a('EYES_DIR', p(self.assets_dir, 'face', 'eyes'))
        a('MOUTH_DIR', p(self.assets_dir, 'face', 'mouth'))

    def send_embed(self, interaction: discord.Interaction, description: str, title: str = "Chao Bot"):
        return interaction.response.send_message(embed=discord.Embed(title=title, description=description, color=self.embed_color))

    async def chao(self, interaction: discord.Interaction):
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        if self.data_utils.is_user_initialized(guild_id, guild_name, user):
            return await interaction.response.send_message(f"{interaction.user.mention}, you have already started using the Chao Bot.")
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        self.data_utils.save_inventory(inv_path, self.data_utils.load_inventory(inv_path),
                                       {'rings': 500, 'Chao Egg': 1, 'Garden Nut': 5})
        embed = discord.Embed(
            title="Welcome to Chao Bot!",
            description=("**Chao Bot** is a W.I.P. bot that lets you hatch, raise, and train your own Chao!\n\n"
                         "**/help** - List commands\n**/market** - Black Market\n**/feed** - Feed a fruit\n"
                         "**/egg** - Get a new egg\n**/hatch** - Hatch an egg\n\n**You Receive:**\n- `1x Chao Egg`\n- `500x Rings`\n- `5x Garden Nut`"),
            color=self.embed_color
        )
        egg_thumb = os.path.join(self.assets_dir, "graphics", "thumbnails", "egg_background.png")
        welcome_img = os.path.join(self.assets_dir, "graphics", "misc", "welcome_message.png")
        embed.set_thumbnail(url="attachment://egg_background.png")
        embed.set_image(url="attachment://welcome_message.png")
        await interaction.response.send_message(files=[discord.File(egg_thumb, filename="egg_background.png"),
                                                         discord.File(welcome_img, filename="welcome_message.png")],
                                                embed=embed)

    async def give_rings(self, interaction: discord.Interaction):
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        inv['rings'] = inv.get('rings', 0) + 1000000
        self.data_utils.save_inventory(inv_path, inv_df, inv)
        await interaction.response.send_message(f"{interaction.user.mention} has been given 1,000,000 rings! Current rings: {inv['rings']}")
        print(f"[give_rings] 1,000,000 Rings added to {user.id}. New balance: {inv['rings']}")

    async def list_chao(self, interaction: discord.Interaction):
        guild_id, user = str(interaction.guild.id), interaction.user
        guild_folder = self.data_utils.update_server_folder(interaction.guild)
        user_folder = self.data_utils.get_user_folder(guild_folder, user)
        chao_dir = os.path.join(user_folder, 'chao_data')
        if not os.path.exists(chao_dir):
            return await interaction.response.send_message(f"{user.mention}, you don't have any Chao yet.")

        chao_list = [d for d in os.listdir(chao_dir) if os.path.isdir(os.path.join(chao_dir, d))]
        if not chao_list:
            return await interaction.response.send_message(f"{user.mention}, you don't have any Chao yet.")

        tm = {f"{a}_fly_3": "Fly" for a in ["dark", "hero", "neutral"]}
        tm.update({f"{a}_fly_{s}_4": f"Fly/{s.capitalize()}" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})
        tm.update({f"{a}_normal_1": "Normal" for a in ["dark", "hero", "neutral"]})
        tm.update({f"{a}_normal_3": "Normal" for a in ["dark", "hero", "neutral"]})
        tm.update({f"{a}_normal_{s}_2": "Normal" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})
        tm.update({f"{a}_normal_{s}_4": f"Normal/{s.capitalize()}" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})
        tm.update({f"{a}_power_3": "Power" for a in ["dark", "hero", "neutral"]})
        tm.update({f"{a}_power_{s}_4": f"Power/{s.capitalize()}" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})
        tm.update({f"{a}_run_3": "Run" for a in ["dark", "hero", "neutral"]})
        tm.update({f"{a}_run_{s}_4": f"Run/{s.capitalize()}" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})
        tm.update({f"{a}_swim_3": "Swim" for a in ["dark", "hero", "neutral"]})
        tm.update({f"{a}_swim_{s}_4": f"Swim/{s.capitalize()}" for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]})

        embed = discord.Embed(
            title=f"{user.display_name}'s Chao",
            description="Here are your Chao:",
            color=discord.Color.blue()
        )

        alive_chao_count = 0
        for cn in chao_list:
            stats_file = os.path.join(chao_dir, cn, f"{cn}_stats.parquet")
            if not os.path.exists(stats_file):
                embed.add_field(name=cn, value="No stats available", inline=False)
                continue
            
            data = self.data_utils.load_chao_stats(stats_file).iloc[-1].to_dict()

            if data.get("dead", False):
                continue

            chao_type = data.get("Type", "unknown")
            ct = tm.get(chao_type, "Unknown")
            al = data.get("Alignment", "Neutral").capitalize()
            embed.add_field(name=cn, value=f"Type: {ct}\nAlignment: {al}", inline=False)
            alive_chao_count += 1

        if alive_chao_count == 0:
            return await interaction.response.send_message(f"{user.mention}, you have no living Chao.")

        embed.set_footer(text=f"Graphics Pending...")
        await interaction.response.send_message(embed=embed)

    async def grades(self, interaction: discord.Interaction, chao_name: str):
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_file = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(f"{interaction.user.mention}, no Chao named **{chao_name}** exists.")
        latest = self.data_utils.load_chao_stats(stats_file).iloc[-1].to_dict()
        grades_dict = {s: latest.get(f"{s}_grade", "F") for s in ["power", "swim", "fly", "run", "stamina"]}
        thumb = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
        embed = discord.Embed(title=f"{chao_name}'s Grades", description="Current grades:", color=discord.Color.blue())
        embed.add_field(name="", value="\n".join([f"**{k.capitalize()}**: {v}" for k, v in grades_dict.items()]), inline=False)
        file = None
        if os.path.exists(thumb):
            safe_fn = os.path.basename(thumb).replace(" ", "_")
            embed.set_thumbnail(url=f"attachment://{safe_fn}")
            file = discord.File(thumb, filename=safe_fn)
        embed.set_footer(text="Graphics Pending...")
        await interaction.response.send_message(embed=embed, file=file)

    def get_random_grade(self):
        return random.choices(['F', 'E', 'D', 'C', 'B', 'A', 'S'], [4, 20, 25, 35, 10, 5, 1], k=1)[0]

    async def hatch(self, interaction: discord.Interaction):
        guild_id, user_id = str(interaction.guild.id), str(interaction.user.id)
        chao_dir = self.data_utils.get_path(guild_id, interaction.guild.name, interaction.user, 'chao_data', '')
        inv_path = self.data_utils.get_path(guild_id, interaction.guild.name, interaction.user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        # Look for a reincarnated chao that is still an egg (hatched == 0)
        reincarnated = None
        for folder in os.listdir(chao_dir):
            fp = os.path.join(chao_dir, folder)
            if not os.path.isdir(fp):
                continue
            stats_file = os.path.join(fp, f"{folder}_stats.parquet")
            if os.path.exists(stats_file):
                df_temp = self.data_utils.load_chao_stats(stats_file)
                if df_temp.empty:
                    continue
                ls = df_temp.iloc[-1].to_dict()
                if ls.get("hatched", 0) == 0:
                    reincarnated = folder
                    break

        if reincarnated:
            chao_name = reincarnated
            chao_path = os.path.join(chao_dir, chao_name)
            stats_file = os.path.join(chao_path, f"{chao_name}_stats.parquet")
            if inv.get('Chao Egg', 0) < 1:
                return await interaction.response.send_message(f"{interaction.user.mention}, you need at least 1 Chao Egg to hatch this reincarnated chao!")
            inv['Chao Egg'] = max(inv.get('Chao Egg', 0) - 1, 0)
            self.data_utils.save_inventory(inv_path, inv_df, inv)
            df_temp = self.data_utils.load_chao_stats(stats_file)
            ls = df_temp.iloc[-1].to_dict()
            ls["hatched"] = 1
            ls["date"] = datetime.now().strftime("%Y-%m-%d")

            # Reset the chao's form and type to baby state so it can evolve normally
            ls["Form"] = "1"
            ls["Type"] = "neutral_normal_1"
            ls["swim_level"] = 0
            ls["fly_level"] = 0
            ls["run_level"] = 0
            ls["power_level"] = 0
            ls["stamina_level"] = 0
            ls["run_power"] = 0
            ls["swim_fly"] = 0
            ls["dark_hero"] = 0

            old_eyes = ls.get("eyes", "happy")
            final_eyes = old_eyes.split("_", 1)[1] if "_" in old_eyes else old_eyes
            ls["Alignment"], ls["eyes"], ls["mouth"] = "neutral", final_eyes, ls.get("mouth", "happy")
            self.data_utils.save_chao_stats(stats_file, df_temp, ls)
            eyes_img = os.path.join(self.EYES_DIR, f"neutral_{final_eyes}.png")
            if not os.path.exists(eyes_img):
                eyes_img = os.path.join(self.EYES_DIR, "neutral.png")
            mouth_img = os.path.join(self.MOUTH_DIR, f"{ls.get('mouth', 'happy')}.png")
            if not os.path.exists(mouth_img):
                mouth_img = os.path.join(self.MOUTH_DIR, "happy.png")
            thumb = os.path.join(chao_path, f"{chao_name}_thumbnail.png")
            self.image_utils.combine_images_with_face(self.BACKGROUND_PATH, self.NEUTRAL_PATH, eyes_img, mouth_img, thumb)
            embed = discord.Embed(
                title="Your Reincarnated Chao has Hatched!",
                description=f"{interaction.user.mention}, your **reincarnated** chao **{chao_name}** has hatched and is now a baby!\nUse `/rename` to change its name.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")
            return await interaction.response.send_message(file=discord.File(thumb, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"), embed=embed)
        
        # Normal hatching
        if inv.get('Chao Egg', 0) < 1:
            return await interaction.response.send_message(f"{interaction.user.mention}, you do not have any Chao Eggs to hatch.")
        inv['Chao Egg'] = max(inv.get('Chao Egg', 0) - 1, 0)
        self.data_utils.save_inventory(inv_path, inv_df, inv)
        os.makedirs(chao_dir, exist_ok=True)
        used = {d for d in os.listdir(chao_dir) if os.path.isdir(os.path.join(chao_dir, d))}
        available = [n for n in self.chao_names if n not in used]
        if not available:
            return await interaction.response.send_message(f"{interaction.user.mention}, all default chao names are used. Remove an old one or extend the list!")
        chao_name = random.choice(available)
        chao_path = os.path.join(chao_dir, chao_name)
        os.makedirs(chao_path, exist_ok=True)
        stats = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'birth_date': datetime.now().strftime("%Y-%m-%d"),
            'Form': '1', 'Type': 'neutral_normal_1', 'hatched': 1, 'evolved': 0,
            'evolve_cacoon': 0, 'reincarnate_cacoon': 0, 'death_cacoon': 0,
            'dead': 0, 'immortal': 0, 'reincarnations': 0,
            'eyes': random.choice(self.eye_types), 'mouth': random.choice(self.mouth_types),
            'dark_hero': 0, 'belly_ticks': random.randint(3, 10), 'happiness_ticks': random.randint(3, 10),
            'illness_ticks': 0, 'energy_ticks': random.randint(3, 10), 'hp_ticks': 10,
            'swim_exp': 0, 'swim_grade': self.get_random_grade(), 'swim_level': 0, 'swim_ticks': 0, 'swim_fly': 0,
            'fly_exp': 0, 'fly_grade': self.get_random_grade(), 'fly_level': 0, 'fly_ticks': 0,
            'power_exp': 0, 'power_grade': self.get_random_grade(), 'power_level': 0, 'power_ticks': 0,
            'run_exp': 0, 'run_grade': self.get_random_grade(), 'run_level': 0, 'run_power': 0, 'run_ticks': 0,
            'stamina_exp': 0, 'stamina_grade': self.get_random_grade(), 'stamina_level': 0, 'stamina_ticks': 0
        }
        stats_file = os.path.join(chao_path, f'{chao_name}_stats.parquet')
        self.data_utils.save_chao_stats(stats_file, pd.DataFrame(), stats)
        eyes_img = os.path.join(self.EYES_DIR, f"neutral_{stats['eyes']}.png")
        if not os.path.exists(eyes_img):
            eyes_img = os.path.join(self.EYES_DIR, "neutral.png")
        mouth_img = os.path.join(self.MOUTH_DIR, f"{stats['mouth']}.png")
        if not os.path.exists(mouth_img):
            mouth_img = os.path.join(self.MOUTH_DIR, "happy.png")
        thumb = os.path.join(chao_path, f"{chao_name}_thumbnail.png")
        self.image_utils.combine_images_with_face(self.BACKGROUND_PATH, self.NEUTRAL_PATH, eyes_img, mouth_img, thumb)
        embed = discord.Embed(
            title="Your Chao Egg has Hatched!",
            description=f"Your egg hatched into **{chao_name}**!\nUse `/rename` to change its name.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")
        await interaction.response.send_message(file=discord.File(thumb, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"), embed=embed)

    def _strip_form_digit(self, t: str) -> str:
        return t.rsplit("_", 1)[0] if "_" in t and t.rsplit("_", 1)[1] in {"1", "2", "3", "4"} else t

    def _ensure_form4_double_type(self, t: str) -> str:
        parts = t.split("_")
        return "_".join(parts[:2] + [parts[1]] + parts[2:]) if len(parts) == 3 and parts[-1] == "4" else t

    def _extract_base_for_subfolder(self, t: str, alignment: str) -> str:
        t = t[len(f"{alignment}_"):] if t.startswith(f"{alignment}_") else t
        t = t.rsplit("_", 1)[0] if "_" in t and t.rsplit("_", 1)[1] in {"1", "2", "3", "4"} else t
        return t.split("_", 1)[0] if "_" in t else t or "normal"

    def get_stat_increment(self, grade: str) -> int:
        r = {'F': (8, 12), 'E': (11, 15), 'D': (14, 18), 'C': (17, 21), 'B': (20, 24), 'A': (23, 27), 'S': (26, 30), 'X': (30, 35)}
        return random.randint(*r.get(grade.upper(), (8, 12)))

    async def goodbye(self, interaction: discord.Interaction, *, chao_name: str = None):
        if not chao_name:
            embed = discord.Embed(
                title="Goodbye Command",
                description=(
                    "The `/goodbye` command allows you to send one of your Chao to live happily "
                    "in a faraway forest. 🌲\n\n"
                    "**Usage:**\n"
                    "`/goodbye Chaoko`\n\n"
                    "If you use this command, the specified Chao will be removed from your ownership, "
                    "and their data will be stored safely in the Chao Forest. However, you might never see that Chao again."
                ),
                color=discord.Color.blue(),
            )
            gf = os.path.join(self.assets_dir, "graphics", "thumbnails", "goodbye_background.png")
            embed.set_thumbnail(url="attachment://goodbye_background.png")
            with open(gf, 'rb') as f:
                await interaction.response.send_message(embed=embed, file=discord.File(f, filename="goodbye_background.png"))
            return
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        chao_dir = self.data_utils.get_path(guild_id, guild_name, interaction.user, 'chao_data', chao_name)
        if not os.path.exists(chao_dir):
            return await self.send_embed(interaction, f"{interaction.user.mention}, no Chao named **{chao_name}** exists.")
        server_db = self.data_utils.get_server_folder(guild_id, guild_name)
        forest = os.path.join(server_db, "Chao Forest")
        os.makedirs(forest, exist_ok=True)
        lost = [d for d in os.listdir(forest) if os.path.isdir(os.path.join(forest, d)) and d.startswith("Lost Chao")]
        new_name = f"Lost Chao {len(lost) + 1}"
        target = os.path.join(forest, new_name)
        try:
            shutil.move(chao_dir, target)
        except Exception as e:
            return await self.send_embed(interaction, f"{interaction.user.mention}, failed to move **{chao_name}**: {e}")
        gf = os.path.join(self.assets_dir, "graphics", "thumbnails", "goodbye_background.png")
        embed = discord.Embed(title=f"Goodbye, {chao_name}!", description=f"{chao_name} has been sent to live happily in a faraway forest.", color=discord.Color.green())
        embed.set_thumbnail(url="attachment://goodbye_background.png")
        with open(gf, 'rb') as f:
            await interaction.response.send_message(embed=embed, file=discord.File(f, filename="goodbye_background.png"))

    async def pet(self, interaction: discord.Interaction, chao_name: str):
        guild_id = str(interaction.guild.id)
        chao_dir = self.data_utils.get_path(guild_id, interaction.guild.name, interaction.user, 'chao_data', chao_name)
        stats_file = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(f"{interaction.user.mention}, no Chao named **{chao_name}** exists.")
        df = self.data_utils.load_chao_stats(stats_file)
        ls = df.iloc[-1].to_dict()
        ls['happiness_ticks'] = min(ls.get('happiness_ticks', 0) + 1, 10)
        chao_type, form, align = ls.get("Type", "neutral_normal_1"), ls.get("Form", "1"), ls.get("Alignment", "neutral")
        bg = (self.HERO_BG_PATH if form in ["3", "4"] and align == "hero" else self.DARK_BG_PATH if form in ["3", "4"] and align == "dark" else os.path.join(self.assets_dir, "graphics", "thumbnails", "neutral_background.png"))
        img = os.path.join(self.assets_dir, "chao", chao_type.split("_")[1], chao_type.split("_")[0], f"{chao_type}.png")
        if not os.path.exists(img):
            img = os.path.join(self.assets_dir, "chao", "chao_missing.png")
        self.data_utils.save_chao_stats(stats_file, df, ls)
        happy_thumb = os.path.join(chao_dir, f"{chao_name}_thumbnail_happy.png")
        self.image_utils.combine_images_with_face(bg, img, os.path.join(self.EYES_DIR, "neutral_happy.png"), os.path.join(self.MOUTH_DIR, "happy.png"), happy_thumb)
        embed = discord.Embed(title=f"You pet {chao_name}!", description=f"{chao_name} looks so happy!\nHappiness increased!", color=self.embed_color)
        embed.set_thumbnail(url="attachment://happy_thumbnail.png")
        await interaction.response.send_message(embed=embed, file=discord.File(happy_thumb, filename="happy_thumbnail.png"))

    async def throw_chao(self, interaction: discord.Interaction, chao_name: str):
        guild_id = str(interaction.guild.id)
        chao_dir = self.data_utils.get_path(guild_id, interaction.guild.name, interaction.user, 'chao_data', chao_name)
        stats_file = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(f"{interaction.user.mention}, no Chao named **{chao_name}** exists.")
        df = self.data_utils.load_chao_stats(stats_file)
        ls = df.iloc[-1].to_dict()
        ls['happiness_ticks'] = max(0, ls.get('happiness_ticks', 0) - 1)
        ls['hp_ticks'] = max(0, ls.get('hp_ticks', 0) - 1)
        chao_type, form, align = ls.get("Type", "neutral_normal_1"), ls.get("Form", "1"), ls.get("Alignment", "neutral")
        bg = (self.HERO_BG_PATH if form in ["3", "4"] and align == "hero" else self.DARK_BG_PATH if form in ["3", "4"] and align == "dark" else os.path.join(self.assets_dir, "graphics", "thumbnails", "neutral_background.png"))
        img = os.path.join(self.assets_dir, "chao", chao_type.split("_")[1], chao_type.split("_")[0], f"{chao_type}.png")
        if not os.path.exists(img):
            img = os.path.join(self.assets_dir, "chao", "chao_missing.png")
        self.data_utils.save_chao_stats(stats_file, df, ls)
        throw_thumb = os.path.join(chao_dir, f"{chao_name}_thumbnail_throw.png")
        eyes = os.path.join(self.EYES_DIR, "neutral_pain.png")
        if not os.path.exists(eyes):
            eyes = os.path.join(self.EYES_DIR, "neutral_angry.png") or os.path.join(self.EYES_DIR, "neutral.png")
        mouth = os.path.join(self.MOUTH_DIR, "grumble.png")
        if not os.path.exists(mouth):
            mouth = os.path.join(self.MOUTH_DIR, "unhappy.png")
        self.image_utils.combine_images_with_face(bg, img, eyes, mouth, throw_thumb)
        embed = discord.Embed(title=f"You threw {chao_name}!", description=f"{chao_name} looks hurt! Happiness and HP decreased.", color=discord.Color.red())
        embed.set_thumbnail(url="attachment://throw_thumbnail.png")
        with open(throw_thumb, 'rb') as f:
            await interaction.response.send_message(embed=embed, file=discord.File(f, filename="throw_thumbnail.png"))

    async def rename(self, interaction: discord.Interaction, current_name: str, new_name: str):
        current_name = current_name.strip()
        new_name = new_name.strip()
        if not current_name or not new_name:
            embed = discord.Embed(
                title="Rename Command",
                description=(
                    "Usage: `/rename <old_name> <new_name>`\n"
                    "Examples:\n"
                    "`/rename Chaoz Count Chaocula`\n"
                    "`/rename \"Old Name\" \"New Name\"`"
                ),
                color=discord.Color.blue()
            )
            return await interaction.response.send_message(embed=embed)

        user_folder = self.data_utils.get_user_folder(
            self.data_utils.update_server_folder(interaction.guild), interaction.user
        )
        chao_data_folder = os.path.join(user_folder, "chao_data")
        old_path = os.path.join(chao_data_folder, current_name)
        if not os.path.exists(old_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no Chao named **{current_name}** exists!"
            )
        if len(new_name) > 15 or not new_name.replace(" ", "").isalnum():
            return await interaction.response.send_message(
                f"{interaction.user.mention}, the new name **{new_name}** is invalid (max 15 alphanumeric characters, spaces allowed)."
            )
        new_path = os.path.join(chao_data_folder, new_name)
        if os.path.exists(new_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, a Chao named **{new_name}** already exists!"
            )

        os.rename(old_path, new_path)
        old_stats = os.path.join(new_path, f"{current_name}_stats.parquet")
        new_stats = os.path.join(new_path, f"{new_name}_stats.parquet")
        if os.path.exists(old_stats):
            os.rename(old_stats, new_stats)
        for f in os.listdir(new_path):
            if f == f"{new_name}_stats.parquet":
                continue
            if current_name in f:
                os.rename(os.path.join(new_path, f), os.path.join(new_path, f.replace(current_name, new_name)))
        await interaction.response.send_message(
            f"{interaction.user.mention}, your Chao has been successfully renamed from **{current_name}** to **{new_name}**!"
        )


    async def egg(self, interaction: discord.Interaction):
        p, load_inv, save_inv = self.data_utils.get_path, self.data_utils.load_inventory, self.data_utils.save_inventory
        guild_id = str(interaction.guild.id)
        embed = discord.Embed(title="Obtained Chao Egg!", description="**You received a Chao Egg.**\nUse `/hatch` to hatch it!", color=self.embed_color)
        inv_path = p(guild_id, interaction.guild.name, interaction.user, 'user_data', 'inventory.parquet')
        inv_df = load_inv(inv_path)
        inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        if inv.get('Chao Egg', 0) >= 1:
            return await interaction.response.send_message(f"{interaction.user.mention}, you already have a Chao Egg!")
        inv['Chao Egg'] = inv.get('Chao Egg', 0) + 1
        save_inv(inv_path, inv_df, inv)
        if os.path.exists(self.EGG_BG_PATH):
            egg_file = discord.File(self.EGG_BG_PATH, filename="egg_background.png")
            embed.set_thumbnail(url="attachment://egg_background.png")
            await interaction.response.send_message(embed=embed, file=egg_file)
        else:
            await interaction.response.send_message(embed=embed)

    async def inventory(self, interaction: discord.Interaction):
        get_path, load_inv = self.data_utils.get_path, self.data_utils.load_inventory
        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        inv_path = get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = load_inv(inv_path)
        current_date = datetime.now().strftime("%Y-%m-%d")
        if not inv_df.empty and current_date in inv_df['date'].values:
            inv = inv_df[inv_df['date'] == current_date].iloc[-1].to_dict()
        else:
            inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'Rings': 0}
        if 'rings' in inv:
            inv['Rings'] = inv.pop('rings')
        embed = discord.Embed(title="Your Inventory", description="Here's what you have today:", color=self.embed_color)
        for item, amt in inv.items():
            if item == 'date':
                continue
            if amt > 0:
                embed.add_field(name=item, value=f"Quantity: {int(amt)}", inline=True)
        embed.set_footer(text="Graphics Pending...")
        await interaction.response.send_message(embed=embed)

    def calculate_exp_gain(self, grade: str) -> int:
        return {'F': 1, 'E': 2, 'D': 3, 'C': 4, 'B': 5, 'A': 6, 'S': 7}.get(grade.upper(), 3)

async def setup(bot):
    await bot.add_cog(Chao(bot))
