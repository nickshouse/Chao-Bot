# cogs/chao_admin.py

import os, random, discord, pandas as pd
from PIL import Image
from discord.ext import commands
from datetime import datetime
from typing import Dict
from config import (
    FRUIT_STATS_ADJUSTMENTS, FRUITS,
    FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4,
    ALIGNMENTS, HERO_BG_PATH, DARK_BG_PATH, NEUTRAL_BG_PATH,
    ASSETS_DIR, PAGE1_TICK_POSITIONS, PAGE2_TICK_POSITIONS, GRADE_RANGES
)

class ChaoAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_utils = self.image_utils = self.assets_dir = None
        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4
        self.ALIGNMENTS = ALIGNMENTS
        self.HERO_ALIGNMENT = ALIGNMENTS.get('hero', 5)
        self.DARK_ALIGNMENT = ALIGNMENTS.get('dark', -5)
        self.fruit_stats_adjustments, self.fruits = FRUIT_STATS_ADJUSTMENTS, FRUITS
        self.embed_color = discord.Color.blue()
        self.GRADES, self.GRADE_RANGES = list(GRADE_RANGES.keys()), GRADE_RANGES

    async def cog_load(self):
        self.data_utils = self.bot.get_cog("DataUtils")
        self.image_utils = self.bot.get_cog("ImageUtils")
        if not self.data_utils or not self.image_utils:
            raise Exception("ChaoAdmin requires DataUtils and ImageUtils cogs to be loaded.")
        self.assets_dir = ASSETS_DIR
        graphics = os.path.join(self.assets_dir, 'graphics')
        self.TEMPLATE_PATH = os.path.join(graphics, 'cards', 'stats_page_1.png')
        self.TEMPLATE_PAGE_2_PATH = os.path.join(graphics, 'cards', 'stats_page_2.png')
        self.OVERLAY_PATH = os.path.join(graphics, 'ticks', 'tick_filled.png')
        self.ICON_PATH = os.path.join(graphics, 'icons', 'Stats.png')
        thumbs = os.path.join(graphics, 'thumbnails')
        self.BACKGROUND_PATH = os.path.join(thumbs, 'neutral_background.png')
        self.HERO_BG_PATH = os.path.join(thumbs, 'hero_background.png')
        self.DARK_BG_PATH = os.path.join(thumbs, 'dark_background.png')
        self.NEUTRAL_BG_PATH = os.path.join(thumbs, 'neutral_background.png')
        self.PAGE1_TICK_POSITIONS, self.PAGE2_TICK_POSITIONS = PAGE1_TICK_POSITIONS, PAGE2_TICK_POSITIONS
        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')
        self.NEUTRAL_PATH = os.path.join(self.assets_dir, 'chao', 'normal', 'neutral', 'neutral_normal_1.png')

    def send_embed(self, interaction: discord.Interaction, description: str, title: str = "Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return interaction.response.send_message(embed=embed)

    def get_stat_increment(self, grade: str) -> int:
        return random.randint(*self.GRADE_RANGES.get(grade.upper(), (8, 12)))

    @staticmethod
    def get_guild_user(interaction: discord.Interaction):
        return str(interaction.guild.id), interaction.guild.name, interaction.user

    @staticmethod
    def safe_int(val):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def get_stat_levels(latest_stats):
        stats = ['swim', 'fly', 'run', 'power', 'stamina']
        return [ChaoAdmin.safe_int(latest_stats.get(f"{s}_level") or latest_stats.get(f"{s.capitalize()}_level")) for s in stats]

    def get_background_for_chao_evolution(self, latest_stats: Dict) -> str:
        align = latest_stats.get("Alignment", "neutral")
        form = str(latest_stats.get("Form", "1"))
        if form in {"3", "4"}:
            return self.HERO_BG_PATH if align == "hero" else self.DARK_BG_PATH if align == "dark" else self.NEUTRAL_BG_PATH
        return self.NEUTRAL_BG_PATH

    async def force_life_check(self, interaction: discord.Interaction, *, chao_name: str):
        g, u = str(interaction.guild.id), str(interaction.user.id)
        get_path, load_stats, save_stats = self.data_utils.get_path, self.data_utils.load_chao_stats, self.data_utils.save_chao_stats
        file_path = os.path.join(get_path(g, u, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not os.path.exists(file_path):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{interaction.user.mention}, no Chao named **{chao_name}** exists.", 
                    color=0xFF0000
                )
            )
        stats_df = load_stats(file_path)
        latest = stats_df.iloc[-1].to_dict()
        reincarnated = latest.get('happiness_ticks', 0) > 5
        msg = (f"✨ **{chao_name} has reincarnated! A fresh start begins!**" 
               if reincarnated else f"😢 **{chao_name} has passed away due to low happiness.**")
        if reincarnated:
            new_data = {
                "reincarnations": latest.get('reincarnations', 0) + 1,
                "happiness_ticks": 10,
                "birth_date": datetime.now().strftime("%Y-%m-%d"),
                **{f"{s}_{prop}": 0 for s in ['swim', 'fly', 'run', 'power', 'stamina'] for prop in ['ticks', 'level', 'exp']}
            }
        else:
            new_data = {**latest, "dead": 1}
        save_stats(file_path, stats_df, new_data)
        color = 0x00FF00 if reincarnated else 0x8B0000
        await interaction.response.send_message(embed=discord.Embed(description=msg, color=color))

    async def force_happiness(self, interaction: discord.Interaction, *, chao_name: str, happiness_value: int):
        g, u = str(interaction.guild.id), str(interaction.user.id)
        get_path, load_stats, save_stats = self.data_utils.get_path, self.data_utils.load_chao_stats, self.data_utils.save_chao_stats
        file_path = os.path.join(get_path(g, u, 'chao_data', chao_name), f"{chao_name}_stats.parquet")
        if not os.path.exists(file_path):
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{interaction.user.mention}, no Chao named **{chao_name}** exists.", 
                    color=0xFF0000
                )
            )
        stats_df = load_stats(file_path)
        latest = stats_df.iloc[-1].to_dict()
        latest['happiness_ticks'] = happiness_value
        save_stats(file_path, stats_df, latest)
        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"✅ **{chao_name}'s happiness has been set to {happiness_value}.**", 
                color=0x00FF00
            )
        )

    async def force_grade_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        args_list = args.split()
        if len(args_list) < 3:
            return await interaction.response.send_message("Usage: /force_grade_change @User ChaoName stat new_grade")
        new_grade = args_list[-1].upper()
        stat = args_list[-2].lower()
        chao_name = " ".join(args_list[:-2])
        valid_stats = ["power", "fly", "run", "swim", "stamina"]
        if stat not in valid_stats:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, the stat must be one of: {', '.join(valid_stats)}."
            )
        server_folder = self.data_utils.update_server_folder(interaction.guild)
        user_folder = self.data_utils.get_user_folder(server_folder, target)
        chao_folder = os.path.join(user_folder, "chao_data", chao_name)
        stats_file = os.path.join(chao_folder, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats file found for **{chao_name}** of {target.mention}."
            )
        chao_df = self.data_utils.load_chao_stats(stats_file)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats data found for **{chao_name}** of {target.mention}."
            )
        latest_stats = chao_df.iloc[-1].to_dict()
        grade_key = f"{stat}_grade"
        if new_grade not in self.GRADES:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, {new_grade} is not a valid grade. Valid grades: {', '.join(self.GRADES)}."
            )
        latest_stats[grade_key] = new_grade
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        await interaction.response.send_message(
            f"{interaction.user.mention}, {target.mention}'s chao **{chao_name}** now has its {stat.capitalize()} grade set to {new_grade}."
        )

    async def force_exp_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        args_list = args.split()
        if len(args_list) < 3:
            return await interaction.response.send_message("Usage: /force_exp_change @User ChaoName stat new_exp_value")
        try:
            new_exp = int(args_list[-1])
        except ValueError:
            return await interaction.response.send_message(f"{interaction.user.mention}, the new EXP value must be an integer.")
        stat = args_list[-2].lower()
        chao_name = " ".join(args_list[:-2])
        valid_stats = ["power", "swim", "fly", "run", "stamina"]
        if stat not in valid_stats:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, the stat must be one of: {', '.join(valid_stats)}."
            )
        server_folder = self.data_utils.update_server_folder(interaction.guild)
        user_folder = self.data_utils.get_user_folder(server_folder, target)
        chao_folder = os.path.join(user_folder, "chao_data", chao_name)
        stats_file = os.path.join(chao_folder, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats file found for **{chao_name}** of {target.mention}."
            )
        chao_df = self.data_utils.load_chao_stats(stats_file)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats data found for **{chao_name}** of {target.mention}."
            )
        latest_stats = chao_df.iloc[-1].to_dict()
        exp_key = f"{stat}_exp"
        latest_stats[exp_key] = new_exp
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        await interaction.response.send_message(
            f"{interaction.user.mention}, {target.mention}'s chao **{chao_name}** now has its {stat.capitalize()} EXP set to {new_exp}."
        )

    async def force_level_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        args_list = args.split()
        if len(args_list) < 3:
            return await interaction.response.send_message("Usage: /force_level_change @User ChaoName stat new_level_value")
        try:
            new_level = int(args_list[-1])
        except ValueError:
            return await interaction.response.send_message(f"{interaction.user.mention}, the new level value must be an integer.")
        stat = args_list[-2].lower()
        chao_name = " ".join(args_list[:-2])
        valid_stats = ["power", "swim", "fly", "run", "stamina"]
        if stat not in valid_stats:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, the stat must be one of: {', '.join(valid_stats)}."
            )
        server_folder = self.data_utils.update_server_folder(interaction.guild)
        user_folder = self.data_utils.get_user_folder(server_folder, target)
        chao_folder = os.path.join(user_folder, "chao_data", chao_name)
        stats_file = os.path.join(chao_folder, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats file found for **{chao_name}** of {target.mention}."
            )
        chao_df = self.data_utils.load_chao_stats(stats_file)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats data found for **{chao_name}** of {target.mention}."
            )
        latest_stats = chao_df.iloc[-1].to_dict()
        level_key = f"{stat}_level"
        latest_stats[level_key] = new_level
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        await interaction.response.send_message(
            f"{interaction.user.mention}, {target.mention}'s chao **{chao_name}** now has its {stat.capitalize()} level set to {new_level}."
        )

    async def force_face_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        args_list = args.split()
        if len(args_list) < 3:
            return await interaction.response.send_message("Usage: /force_face_change @User ChaoName face_type new_value")
        chao_name = " ".join(args_list[:-2])
        face_type = args_list[-2].lower()
        new_value = args_list[-1]
        if face_type not in ["eyes", "mouth"]:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, face type must be either 'eyes' or 'mouth'."
            )
        server_folder = self.data_utils.update_server_folder(interaction.guild)
        user_folder = self.data_utils.get_user_folder(server_folder, target)
        chao_folder = os.path.join(user_folder, "chao_data", chao_name)
        stats_file = os.path.join(chao_folder, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats file found for **{chao_name}** of {target.mention}."
            )
        chao_df = self.data_utils.load_chao_stats(stats_file)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats data found for **{chao_name}** of {target.mention}."
            )
        latest_stats = chao_df.iloc[-1].to_dict()
        latest_stats[face_type] = new_value
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        updated_type, updated_form = self.update_chao_type_and_thumbnail(interaction.guild.id, interaction.guild.name, target, chao_name, latest_stats)
        latest_stats["Form"] = updated_form
        latest_stats["Type"] = updated_type
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        await interaction.response.send_message(
            f"{interaction.user.mention}, {target.mention}'s chao **{chao_name}** now has its {face_type} set to {new_value} and its thumbnail updated."
        )

async def setup(bot):
    await bot.add_cog(ChaoAdmin(bot))
