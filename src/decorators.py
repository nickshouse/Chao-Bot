import os
import shutil
import asyncio
import random
import discord
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image
from pathlib import Path

# Import your config paths instead of hardcoding
from config import (
    ASSETS_DIR,
    HERO_BG_PATH,
    DARK_BG_PATH,
    NEUTRAL_BG_PATH
)

# Example: directories for cacoons/thumbnails, assuming they're under /assets/graphics/
CACOONS_DIR = ASSETS_DIR / "graphics" / "cacoons"
THUMBNAILS_DIR = ASSETS_DIR / "graphics" / "thumbnails"
TEMP_DIR = ASSETS_DIR / "temp"


# --------------------------
# Helper Functions
# --------------------------

def get_guild_user_interaction(interaction: discord.Interaction):
    """
    Extract (guild_id, guild_name, user) from the given Interaction.
    """
    if not interaction.guild:
        raise ValueError("This command must be used in a guild.")
    return str(interaction.guild.id), interaction.guild.name, interaction.user

def safe_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

def generate_evolution_image(safe_name: str):
    """
    Use NEUTRAL_BG_PATH + 'cacoon_evolve.png' overlay to show evolution.
    Save in TEMP_DIR, return a discord.File object.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    bg_path = NEUTRAL_BG_PATH
    overlay_img = CACOONS_DIR / "cacoon_evolve.png"
    temp_output = TEMP_DIR / f"lifecycle_{safe_name}.png"

    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_img).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)

    return discord.File(temp_output, filename=temp_output.name)

def generate_reincarnation_image(latest_stats: dict, safe_name: str):
    """
    Pick a background based on alignment, overlay 'cacoon_reincarnate.png'.
    """
    alignment_val = latest_stats.get("dark_hero", 0)
    if alignment_val > 0:
        bg_path = HERO_BG_PATH
    elif alignment_val < 0:
        bg_path = DARK_BG_PATH
    else:
        bg_path = NEUTRAL_BG_PATH

    overlay_path = CACOONS_DIR / "cacoon_reincarnate.png"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_output = TEMP_DIR / f"lifecycle_{safe_name}.png"

    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)

    return discord.File(temp_output, filename=temp_output.name)

def generate_death_image(latest_stats: dict, safe_name: str):
    """
    Pick a background based on alignment, overlay 'cacoon_death.png'.
    """
    alignment_val = latest_stats.get("dark_hero", 0)
    if alignment_val > 0:
        bg_path = HERO_BG_PATH
    elif alignment_val < 0:
        bg_path = DARK_BG_PATH
    else:
        bg_path = NEUTRAL_BG_PATH

    overlay_path = CACOONS_DIR / "cacoon_death.png"
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    temp_output = TEMP_DIR / f"lifecycle_{safe_name}.png"

    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)

    return discord.File(temp_output, filename=temp_output.name)


# --------------------------
# Parsing / Decorator Helpers
# --------------------------

def parse_chao_name(interaction: discord.Interaction, chao_name_raw: str, data_utils) -> str:
    """
    Attempt to find a valid chao directory matching 'chao_name_raw'
    within the user's 'chao_data' folder. Return the validated name if found.
    """
    if not chao_name_raw or not interaction.guild:
        return None

    guild_folder = data_utils.update_server_folder(interaction.guild)
    user_folder = data_utils.get_user_folder(guild_folder, interaction.user)
    chao_dir = os.path.join(user_folder, "chao_data")

    tokens = chao_name_raw.split()
    # Try chunking from longest to shortest
    for i in range(len(tokens), 0, -1):
        candidate = " ".join(tokens[:i])
        stats_file = os.path.join(chao_dir, candidate, f"{candidate}_stats.parquet")
        if os.path.exists(os.path.join(chao_dir, candidate)) and os.path.exists(stats_file):
            return candidate

    # Last resort: scan subfolders
    if os.path.exists(chao_dir):
        for folder in os.listdir(chao_dir):
            folder_path = os.path.join(chao_dir, folder)
            if os.path.isdir(folder_path):
                stats_file = os.path.join(folder_path, f"{chao_name_raw}_stats.parquet")
                if os.path.exists(stats_file):
                    return folder

    return None


# --------------------------
# Decorators
# --------------------------

def ensure_user_initialized(func):
    """
    Ensures the user has used the 'Chao' command before (is initialized).
    Uses interaction instead of ctx.
    """
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        try:
            data_utils = self.data_utils
            guild_id, guild_name, user = get_guild_user_interaction(interaction)
        except Exception:
            return await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )

        # Check if the user has run /chao
        if not data_utils.is_user_initialized(guild_id, guild_name, user):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, please use the `/chao` command to start using the Chao Bot.",
                ephemeral=True
            )

        # If they have, proceed
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            # If an error occurs, respond once
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            raise

    return wrapper


def ensure_chao_alive(func):
    """
    Ensures the targeted chao is not dead, and updates every chao in the user's chao_data:
    if a chao has 0 hp_ticks, mark it dead.
    """
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        data_utils = self.data_utils
        guild_id, guild_name, user = get_guild_user_interaction(interaction)

        # Update all chao's hp/dead state
        guild_folder = data_utils.update_server_folder(interaction.guild)
        user_folder = data_utils.get_user_folder(guild_folder, user)
        chao_data_dir = os.path.join(user_folder, "chao_data")
        if os.path.exists(chao_data_dir):
            for root, _, files in os.walk(chao_data_dir):
                for filename in files:
                    if filename.endswith("_stats.parquet"):
                        stats_path = os.path.join(root, filename)
                        chao_df = data_utils.load_chao_stats(stats_path)
                        if not chao_df.empty:
                            latest = chao_df.iloc[-1].to_dict()
                            hp = safe_int(latest.get("hp_ticks", 0))
                            if hp == 0 and safe_int(latest.get("dead", 0)) != 1:
                                chao_df.iloc[-1, chao_df.columns.get_loc("dead")] = 1
                                chao_df.to_parquet(stats_path, index=False)

        # Check if there's a target chao
        chao_raw = kwargs.get("chao_name") or kwargs.get("chao_name_and_fruit") or (args[0] if args else None)
        if not chao_raw:
            return await func(self, interaction, *args, **kwargs)

        chao_name = parse_chao_name(interaction, chao_raw, data_utils)
        if not chao_name:
            return await interaction.response.send_message("No valid Chao name found.", ephemeral=True)

        chao_dir = data_utils.get_path(guild_id, guild_name, user, "chao_data", chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no Chao named **{chao_name}** exists.",
                ephemeral=True
            )

        chao_df = data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats found for **{chao_name}**.",
                ephemeral=True
            )

        latest = chao_df.iloc[-1].to_dict()
        if safe_int(latest.get("dead", 0)) == 1 or safe_int(latest.get("hp_ticks", 0)) == 0:
            d = latest.get("date_of_death", datetime.now().strftime("%Y-%m-%d"))
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"{chao_name} can no longer be interacted with.\n\n**Date of Death:** {d}",
                color=discord.Color.dark_gray()
            )
            # Grave thumbnail
            grave_img = THUMBNAILS_DIR / "chao_grave.png"
            file = discord.File(grave_img, filename="chao_grave.png") if grave_img.exists() else None
            if file:
                embed.set_thumbnail(url="attachment://chao_grave.png")
                await interaction.response.send_message(file=file, embed=embed)
            else:
                await interaction.response.send_message(embed=embed)
            return

        # If the chao is alive, proceed
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            raise

    return wrapper


def ensure_chao_hatched(func):
    """
    Checks if the Chao is hatched. If not, do nothing or show 'still an egg' message.
    """
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        chao_raw = (
            kwargs.get('chao_name') 
            or kwargs.get('chao_name_and_fruit')
            or kwargs.get('chao_name_and_new_name')
            or (args[0] if args else None)
        )
        # No name: skip check
        if not chao_raw:
            return await func(self, interaction, *args, **kwargs)

        data_utils = self.data_utils
        chao_name = parse_chao_name(interaction, chao_raw, data_utils)
        if not chao_name:
            return await interaction.response.send_message("No valid Chao name found.", ephemeral=True)

        guild_id, guild_name, user = get_guild_user_interaction(interaction)
        chao_dir = data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(stats_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no Chao named **{chao_name}** exists.",
                ephemeral=True
            )

        chao_df = data_utils.load_chao_stats(stats_path)
        if chao_df.empty or safe_int(chao_df.iloc[-1].get("hatched", 0)) == 0:
            # If it's not hatched, optionally respond or just block:
            return

        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
            raise

    return wrapper


def ensure_not_in_cacoon(func):
    """
    Ensures the chao is not currently in an evolve/reincarnate/death cocoon.
    If it is, show an embed with a wait timer, then return.
    """
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        chao_raw = (
            kwargs.get('chao_name')
            or kwargs.get('chao_name_and_fruit')
            or kwargs.get('chao_name_and_new_name')
            or (args[0] if args else None)
        )
        if not chao_raw:
            return await func(self, interaction, *args, **kwargs)

        data_utils = self.data_utils
        chao_name = parse_chao_name(interaction, chao_raw, data_utils)
        if not chao_name:
            return await interaction.response.send_message("No valid Chao name found.", ephemeral=True)

        guild_id, guild_name, user = get_guild_user_interaction(interaction)
        chao_dir = data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no Chao named **{chao_name}** exists.",
                ephemeral=True
            )

        chao_df = data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no stats found for **{chao_name}**.",
                ephemeral=True
            )

        latest = chao_df.iloc[-1].to_dict()
        now = datetime.now()

        # --- Check if Evolving ---
        if latest.get("evolve_cacoon", 0) == 1:
            evolution_end_time_str = latest.get("evolution_end_time")
            if evolution_end_time_str:
                try:
                    evolution_end = datetime.fromisoformat(evolution_end_time_str)
                except:
                    evolution_end = now + timedelta(seconds=60)
            else:
                evolution_end = now + timedelta(seconds=60)

            remaining = (evolution_end - now).total_seconds()
            if remaining > 0:
                safe_name = chao_name.replace(" ", "_")
                file = generate_evolution_image(safe_name)
                embed = discord.Embed(
                    title="Chao Is Evolving!",
                    description=(
                        f"{interaction.user.mention}, your chao **{chao_name}** is evolving. "
                        f"You cannot interact for {int(remaining)} seconds."
                    ),
                    color=discord.Color.purple()
                )
                embed.set_thumbnail(url=f"attachment://{file.filename}")
                await interaction.response.send_message(embed=embed, file=file)
                await asyncio.sleep(remaining)
                return

        # --- Check if Reincarnating ---
        if latest.get("reincarnate_cacoon", 0) == 1:
            reincarnation_end_time_str = latest.get("reincarnation_end_time")
            if reincarnation_end_time_str:
                try:
                    reincarnation_end = datetime.fromisoformat(reincarnation_end_time_str)
                except:
                    reincarnation_end = now + timedelta(seconds=60)
            else:
                reincarnation_end = now + timedelta(seconds=60)

            remaining = (reincarnation_end - now).total_seconds()
            if remaining > 0:
                safe_name = chao_name.replace(" ", "_")
                file = generate_reincarnation_image(latest, safe_name)
                embed = discord.Embed(
                    title="Chao Is Reincarnating!",
                    description=(
                        f"{interaction.user.mention}, your chao **{chao_name}** is reincarnating. "
                        f"You cannot interact for {int(remaining)} seconds."
                    ),
                    color=discord.Color.purple()
                )
                embed.set_thumbnail(url=f"attachment://{file.filename}")
                await interaction.response.send_message(embed=embed, file=file)
                await asyncio.sleep(remaining)
                return

        # --- Check if Dying ---
        if latest.get("death_cacoon", 0) == 1:
            death_end_time_str = latest.get("death_end_time")
            if death_end_time_str:
                try:
                    death_end = datetime.fromisoformat(death_end_time_str)
                except:
                    death_end = now + timedelta(seconds=60)
            else:
                death_end = now + timedelta(seconds=60)

            remaining = (death_end - now).total_seconds()
            if remaining > 0:
                safe_name = chao_name.replace(" ", "_")
                file = generate_death_image(latest, safe_name)
                embed = discord.Embed(
                    title="Chao Is Dying!",
                    description=(
                        f"{interaction.user.mention}, your chao **{chao_name}** is dying. "
                        f"You cannot interact for {int(remaining)} seconds."
                    ),
                    color=discord.Color.dark_red()
                )
                embed.set_thumbnail(url=f"attachment://{file.filename}")
                await interaction.response.send_message(embed=embed, file=file)
                await asyncio.sleep(remaining)
                return

        # If no cacoon is active, proceed
        return await func(self, interaction, *args, **kwargs)

    return wrapper
