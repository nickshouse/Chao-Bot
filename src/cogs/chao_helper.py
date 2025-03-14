# cogs/chao_helper.py

import os, random, asyncio, discord, pandas as pd
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
from views.stats_view import StatsView  # Assuming you still need this for stats.

PERSISTENT_VIEWS_FILE = "persistent_views.json"

class ChaoHelper(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_utils = None
        self.image_utils = None
        self.assets_dir = None
        
        # Thresholds & alignment
        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4
        self.ALIGNMENTS = ALIGNMENTS
        self.HERO_ALIGNMENT = ALIGNMENTS.get('hero', 5)
        self.DARK_ALIGNMENT = ALIGNMENTS.get('dark', -5)

        # Fruit data, stats, and basic config
        self.fruit_stats_adjustments = FRUIT_STATS_ADJUSTMENTS
        self.fruits = FRUITS
        self.embed_color = discord.Color.blue()
        self.GRADES = list(GRADE_RANGES.keys())
        self.GRADE_RANGES = GRADE_RANGES

    async def cog_load(self):
        # Grab your utility cogs
        self.data_utils = self.bot.get_cog("DataUtils")
        self.image_utils = self.bot.get_cog("ImageUtils")
        if not self.data_utils or not self.image_utils:
            raise Exception("ChaoHelper requires DataUtils and ImageUtils cogs to be loaded.")
        
        self.assets_dir = ASSETS_DIR
        graphics = os.path.join(self.assets_dir, 'graphics')
        # Basic asset paths (for your reference; used by stats)
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

    async def graveyard(self, interaction: discord.Interaction):
        """
        Lists all dead chao in the server, complete with a graveyard thumbnail.
        Usage: /graveyard
        """
        guild = interaction.guild
        server_folder = self.data_utils.update_server_folder(guild)
        if not os.path.exists(server_folder):
            return await interaction.response.send_message("No server folder found. Something is wrong.")

        all_folders = os.listdir(server_folder)
        chao_entries = []

        for uf in all_folders:
            user_folder = os.path.join(server_folder, uf)
            if not os.path.isdir(user_folder):
                continue

            chao_dir = os.path.join(user_folder, 'chao_data')
            if not os.path.exists(chao_dir):
                continue

            chao_list = [
                d for d in os.listdir(chao_dir)
                if os.path.isdir(os.path.join(chao_dir, d))
            ]

            for chao_name in chao_list:
                stats_file = os.path.join(chao_dir, chao_name, f"{chao_name}_stats.parquet")
                if not os.path.exists(stats_file):
                    continue

                chao_df = self.data_utils.load_chao_stats(stats_file)
                if chao_df.empty:
                    continue

                latest_stats = chao_df.iloc[-1].to_dict()
                if latest_stats.get("dead", False):
                    # Save for listing
                    chao_entries.append((chao_name, uf))

        if not chao_entries:
            return await interaction.response.send_message("No chao are dead in this server! The graveyard is empty.")

        embed = discord.Embed(
            title="Chao Graveyard",
            description="Here rests all the Chao in the server that were unable to make it to the next life...",
            color=discord.Color.dark_grey()
        )

        # If you have a local path to a 'chao_grave.png', attach it
        grave_path = r"C:\Users\You\Documents\GitHub\Chao-Bot-Dev\assets\graphics\thumbnails\chao_grave.png"
        if os.path.exists(grave_path):
            with open(grave_path, "rb") as f:
                grave_file = discord.File(f, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
        else:
            grave_file = None

        for cname, folder_name in chao_entries:
            # Attempt to parse the user ID from the folder name
            user_id_str = folder_name.split()[0]
            owner_line = "Unknown Owner"
            if user_id_str.isdigit():
                member = guild.get_member(int(user_id_str))
                if member:
                    owner_line = f"{member.display_name} ({member.name})"
            embed.add_field(name=cname, value=f"Owner: {owner_line}", inline=False)

        embed.set_footer(text="Graphics Pending...")

        if grave_file:
            await interaction.response.send_message(embed=embed, file=grave_file)
        else:
            await interaction.response.send_message(embed=embed)

    async def stats(self, interaction: discord.Interaction, *, chao_name: str):
        """
        Displays a chao's stats, using the ChaoLifecycle cog's methods to update type/form
        and to save the StatsView persistently.
        Usage: /stats chao_name:<chao_name>
        """
        lifecycle_cog = self.bot.get_cog("ChaoLifecycle")
        if not lifecycle_cog:
            return await interaction.response.send_message("ChaoLifecycle cog not loaded; cannot update type or form.")

        user = interaction.user
        guild_id, guild_name = str(interaction.guild.id), interaction.guild.name
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await interaction.response.send_message(f"{interaction.user.mention}, no Chao named **{chao_name}** exists.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()

        # Use ChaoLifecycle's update_chao_type_and_thumbnail
        chao_type, form = lifecycle_cog.update_chao_type_and_thumbnail(
            guild_id, guild_name, user, chao_name, chao_stats
        )

        # If anything changed, save it back
        if chao_stats.get("Form") != form or chao_stats.get("Type") != chao_type:
            chao_stats["Form"], chao_stats["Type"] = form, chao_type
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)

        # Mapping from type-string to friendlier display label
        type_mapping = {
            **{f"{a}_fly_3": "Fly" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_fly_{s}_4": f"Fly/{s.capitalize()}"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
            **{f"{a}_normal_1": "Normal" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_normal_3": "Normal" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_normal_{s}_2": "Normal"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
            **{f"{a}_normal_{s}_4": f"Normal/{s.capitalize()}"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
            **{f"{a}_power_3": "Power" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_power_{s}_4": f"Power/{s.capitalize()}"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
            **{f"{a}_run_3": "Run" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_run_{s}_4": f"Run/{s.capitalize()}"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
            **{f"{a}_swim_3": "Swim" for a in ["dark", "hero", "neutral"]},
            **{f"{a}_swim_{s}_4": f"Swim/{s.capitalize()}"
               for a in ["dark", "hero", "neutral"] for s in ["fly", "normal", "power", "run", "swim"]},
        }
        chao_type_display = type_mapping.get(chao_type, "Unknown")
        alignment_label = chao_stats.get("Alignment", "Neutral").capitalize()

        # We'll generate two stat images (page 1 & page 2)
        stats_image_paths = {
            1: os.path.join(chao_dir, f"{chao_name}_stats_page_1.png"),
            2: os.path.join(chao_dir, f"{chao_name}_stats_page_2.png")
        }
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        await asyncio.gather(
            asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.TEMPLATE_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[1],
                self.PAGE1_TICK_POSITIONS,
                *[int(chao_stats.get(f"{s}_ticks", 0)) for s in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[int(chao_stats.get(f"{s}_level", 0)) for s in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[int(chao_stats.get(f"{s}_exp", 0)) for s in ['power', 'swim', 'fly', 'run', 'stamina']]
            ),
            asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.TEMPLATE_PAGE_2_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[2],
                self.PAGE2_TICK_POSITIONS,
                {k: chao_stats.get(f"{k}_ticks", 0) for k in self.PAGE2_TICK_POSITIONS}
            )
        )

        embed = discord.Embed(color=self.embed_color)
        embed.set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://stats_page.png")
        embed.set_footer(text="Page 1 / 2")

        # Build data for StatsView
        view_data = {
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user.id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        }
        # Use ChaoLifecycle's save_persistent_view
        lifecycle_cog.save_persistent_view(view_data)

        # Create the view
        view = StatsView.from_data(view_data, self)

        await interaction.response.send_message(
            files=[
                discord.File(stats_image_paths[1], "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(thumbnail_path, filename="chao_thumbnail.png")
            ],
            embed=embed,
            view=view
        )

async def setup(bot):
    await bot.add_cog(ChaoHelper(bot))
