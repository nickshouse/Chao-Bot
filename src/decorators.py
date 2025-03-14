import os
import shutil
import asyncio
import random
import discord
import pandas as pd
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image

ASSETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets")
)

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

def generate_evolution_image(bg_path, overlay_img, safe_name):
    temp_folder = os.path.join(ASSETS_DIR, "temp")
    os.makedirs(temp_folder, exist_ok=True)
    temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")
    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_img).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)
    return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

def generate_reincarnation_image(latest_stats: dict, safe_name: str):
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

    bg_path = os.path.join(ASSETS_DIR, "graphics", "thumbnails", bg_file)
    overlay_path = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_reincarnate.png")
    
    temp_folder = os.path.join(ASSETS_DIR, "temp")
    os.makedirs(temp_folder, exist_ok=True)
    temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")

    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)

    return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

def generate_death_image(latest_stats: dict, safe_name: str):
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

    bg_path = os.path.join(ASSETS_DIR, "graphics", "thumbnails", bg_file)
    overlay_path = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_death.png")
    
    temp_folder = os.path.join(ASSETS_DIR, "temp")
    os.makedirs(temp_folder, exist_ok=True)
    temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")

    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_path).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)

    return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")


# --------------------------
# Parsing / Decorator Helpers
# --------------------------

def parse_chao_name(interaction: discord.Interaction, chao_name_raw: str, data_utils) -> str:
    """
    Attempt to find a valid chao directory matching 'chao_name_raw'
    within the user’s 'chao_data' folder. Return the validated name if found.
    """
    if not chao_name_raw:
        return None

    # Build the user’s directory
    if not interaction.guild:
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
            # If there's no guild or user, respond gracefully
            return await interaction.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )

        if not data_utils.is_user_initialized(guild_id, guild_name, user):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, please use the `/chao` command to start using the Chao Bot.",
                ephemeral=True
            )

        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred: {e}", ephemeral=True
            )
            raise

    return wrapper


def ensure_chao_alive(func):
    """
    Ensures the targeted chao is not dead.
    """
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        chao_raw = (
            kwargs.get('chao_name')
            or kwargs.get('chao_name_and_fruit')
            or (args[0] if args else None)
        )
        if not chao_raw:
            # If no chao name is provided, just run the command
            return await func(self, interaction, *args, **kwargs)

        data_utils = self.data_utils
        chao_name = parse_chao_name(interaction, chao_raw, data_utils)
        if not chao_name:
            return await interaction.response.send_message(
                "No valid Chao name found.", ephemeral=True
            )

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
        # If the chao is "dead" or hp_ticks=0 => show the grave embed
        if safe_int(latest.get("dead", 0)) == 1 or safe_int(latest.get("hp_ticks", 0)) == 0:
            d = latest.get("date_of_death", datetime.now().strftime("%Y-%m-%d"))
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"{chao_name} can no longer be interacted with.\n\n**Date of Death:** {d}",
                color=discord.Color.dark_gray()
            )
            thumb = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "chao_grave.png")
            file = discord.File(thumb, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
            await interaction.response.send_message(file=file, embed=embed)
            return

        # If alive, proceed
        try:
            return await func(self, interaction, *args, **kwargs)
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {e}", ephemeral=True
            )
            raise

    return wrapper


def ensure_chao_hatched(func):
    @wraps(func)
    async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
        chao_raw = (
            kwargs.get('chao_name') 
            or kwargs.get('chao_name_and_fruit')
            or kwargs.get('chao_name_and_new_name')
            or (args[0] if args else None)
        )
        # If no name is provided, we skip the check and just call the command.
        if not chao_raw:
            return await func(self, interaction, *args, **kwargs)

        # Otherwise, proceed with the normal "hatching" validation
        data_utils = self.data_utils
        chao_name = parse_chao_name(interaction, chao_raw, data_utils)
        if not chao_name:
            return await interaction.response.send_message(
                "No valid Chao name found.", ephemeral=True
            )

        guild_id, guild_name, user = get_guild_user_interaction(interaction)
        chao_dir = data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(stats_path):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, no Chao named **{chao_name}** exists.",
                ephemeral=True
            )

        chao_df = data_utils.load_chao_stats(stats_path)
        if chao_df.empty or safe_int(chao_df.iloc[-1].to_dict().get("hatched", 0)) == 0:
            # (Show "still an egg" message)
            return

        return await func(self, interaction, *args, **kwargs)
    return wrapper


def ensure_not_in_cacoon(func):
    """
    Ensures the chao is not currently in an evolve/reincarnate/death cacoon.
    If it is, show a relevant embed and wait out the time (or block).
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
            return await interaction.response.send_message(
                "No valid Chao name found.", ephemeral=True
            )

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

        # --- Check if Evolving ---
        if latest.get("evolve_cacoon", 0) == 1:
            evolution_end_time_str = latest.get("evolution_end_time")
            now = datetime.now()
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
                bg_path = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "neutral_background.png")
                overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_evolve.png")
                file = generate_evolution_image(bg_path, overlay_img, safe_name)

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
            now = datetime.now()
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

        # --- Check if in Death Cacoon ---
        if latest.get("death_cacoon", 0) == 1:
            death_end_time_str = latest.get("death_end_time")
            now = datetime.now()
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

        # If none of the cacoon states are active, proceed
        return await func(self, interaction, *args, **kwargs)

    return wrapper
