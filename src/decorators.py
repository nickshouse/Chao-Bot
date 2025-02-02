# cogs/decorators.py

import discord
import os
from datetime import datetime
from functools import wraps

def ensure_user_initialized(func):
    """
    A decorator to ensure the user is initialized in the Chao system
    before running the decorated command. We assume the command's Cog
    has a reference to `data_utils` that provides `is_user_initialized`.
    """
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        if not self.data_utils.is_user_initialized(guild_id, guild_name, user):
            return await ctx.reply(
                f"{ctx.author.mention}, please use the `$chao` command to start using the Chao Bot."
            )

        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")
            raise
    return wrapper

def ensure_chao_alive(func):
    """
    A decorator to ensure the specified Chao is not at 0 HP (i.e. not dead).
    If it's dead, we build an embed showing the Chao's name, date of death,
    and a 'chao_grave.png' thumbnail from your assets path.
    """
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        # We'll look for 'chao_name' in kwargs or in args if needed.
        chao_name = kwargs.get('chao_name')
        if not chao_name and args:
            chao_name = args[0]  # e.g. if the command is def feed(self, ctx, chao_name: str)

        # If we still have no chao_name, just proceed without the alive check
        if not chao_name:
            return await func(self, ctx, *args, **kwargs)

        # Now load the Chao stats to check HP
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        if chao_df.empty:
            return await ctx.reply(f"{ctx.author.mention}, no stats found for **{chao_name}**.")

        latest_stats = chao_df.iloc[-1].to_dict()
        hp = latest_stats.get("hp_ticks", 0)

        if hp <= 0:
            # If there's a stored date_of_death, use it; otherwise treat "now" as date_of_death
            date_of_death = latest_stats.get("date_of_death")
            if not date_of_death:
                date_of_death = datetime.now().strftime("%Y-%m-%d")
                # Optionally, you could store it back in the stats if you want:
                # latest_stats["date_of_death"] = date_of_death
                # self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

            # Create the embed
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"**Date of Death:** {date_of_death}",
                color=discord.Color.dark_gray()
            )

            # Set thumbnail
            thumbnail_path = r"C:\Users\You\Documents\GitHub\Chao-Bot-Dev\assets\graphics\thumbnails\chao_grave.png"
            # If we want to send the file directly:
            file = discord.File(thumbnail_path, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")

            return await ctx.reply(
                f"{ctx.author.mention}, **{chao_name}** is at 0 HP and cannot be interacted with (Dead Chao).",
                file=file,
                embed=embed
            )

        # If alive, proceed with the command
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")
            raise

    return wrapper
