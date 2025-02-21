import discord
import os
import shutil
import pandas as pd
import asyncio
import random
from datetime import datetime, timedelta
from functools import wraps
from PIL import Image

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../assets"))

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

def get_bg_path(image_utils, stats):
    # Returns a background image path based on Form and Alignment.
    if stats.get("Form", "1") in ["3", "4"]:
        align = stats.get("Alignment", "neutral")
        if align == "hero":
            return getattr(image_utils, "HERO_BG_PATH", os.path.join(image_utils.assets_dir, "graphics", "thumbnails", "hero_background.png"))
        elif align == "dark":
            return getattr(image_utils, "DARK_BG_PATH", os.path.join(image_utils.assets_dir, "graphics", "thumbnails", "dark_background.png"))
        else:
            return getattr(image_utils, "NEUTRAL_BG_PATH", os.path.join(image_utils.assets_dir, "graphics", "thumbnails", "neutral_background.png"))
    return os.path.join(image_utils.assets_dir, "graphics", "thumbnails", "neutral_background.png")

def generate_lifecycle_image(bg_path, overlay_img, safe_name):
    temp_folder = os.path.join(ASSETS_DIR, "temp")
    os.makedirs(temp_folder, exist_ok=True)
    temp_output = os.path.join(temp_folder, f"lifecycle_{safe_name}.png")
    with Image.open(bg_path).convert("RGBA") as bg, Image.open(overlay_img).convert("RGBA") as overlay:
        overlay = overlay.resize(bg.size)
        Image.alpha_composite(bg, overlay).save(temp_output)
    return discord.File(temp_output, filename=f"lifecycle_{safe_name}.png")

def ensure_user_initialized(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        guild_id, guild_name, user = get_guild_user(ctx)
        if not self.data_utils.is_user_initialized(guild_id, guild_name, user):
            return await ctx.reply(f"{ctx.author.mention}, please use the $chao command to start using the Chao Bot.")
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")
            raise
    return wrapper

def ensure_chao_alive(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        chao_name = kwargs.get('chao_name') or (args[0] if args else None)
        if not chao_name:
            return await func(self, ctx, *args, **kwargs)
        guild_id, guild_name, user = get_guild_user(ctx)
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")
        chao_df = self.data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await ctx.reply(f"{ctx.author.mention}, no stats found for **{chao_name}**.")
        latest_stats = chao_df.iloc[-1].to_dict()
        if safe_int(latest_stats.get("hp_ticks", 0)) <= 0:
            date_of_death = latest_stats.get("date_of_death", datetime.now().strftime("%Y-%m-%d"))
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"{chao_name} can no longer be interacted with.\n\n**Date of Death:** {date_of_death}",
                color=discord.Color.dark_gray()
            )
            thumb = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "chao_grave.png")
            file = discord.File(thumb, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
            return await ctx.reply(file=file, embed=embed)
        try:
            return await func(self, ctx, *args, **kwargs)
        except Exception as e:
            await ctx.reply(f"An error occurred: {e}")
            raise
    return wrapper

def parse_chao_name(ctx, chao_name_raw, data_utils):
    if not chao_name_raw:
        return None
    tokens = chao_name_raw.split()
    user_folder = data_utils.get_user_folder(data_utils.update_server_folder(ctx.guild), ctx.author)
    chao_dir = os.path.join(user_folder, "chao_data")
    # Try decreasing token combinations.
    for i in range(len(tokens), 0, -1):
        candidate = " ".join(tokens[:i])
        candidate_folder = os.path.join(chao_dir, candidate)
        candidate_stats = os.path.join(candidate_folder, f"{candidate}_stats.parquet")
        if os.path.exists(candidate_folder) and os.path.exists(candidate_stats):
            return candidate
    # Fallback: search for a matching stats file.
    for folder in os.listdir(chao_dir):
        folder_path = os.path.join(chao_dir, folder)
        if os.path.isdir(folder_path):
            stats_file = os.path.join(folder_path, f"{chao_name_raw}_stats.parquet")
            if os.path.exists(stats_file):
                return folder
    return None

def ensure_chao_hatched(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        chao_name_raw = (kwargs.get('chao_name') or kwargs.get('chao_name_and_fruit') or 
                         kwargs.get('chao_name_and_new_name') or (args[0] if args else None))
        if not chao_name_raw:
            return await ctx.reply("No valid Chao name provided.")
        chao_name = parse_chao_name(ctx, chao_name_raw, self.data_utils)
        if not chao_name:
            return await ctx.reply("No valid Chao name found.")
        guild_id, guild_name, user = get_guild_user(ctx)
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")
        chao_df = self.data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await ctx.reply(f"{ctx.author.mention}, no stats found for **{chao_name}**.")
        latest_stats = chao_df.iloc[-1].to_dict()
        if safe_int(latest_stats.get("hatched", 0)) == 0:
            embed = discord.Embed(
                title="Chao is Still an Egg",
                description=f"{ctx.author.mention}, your chao **{chao_name}** is still an egg and cannot be interacted with until it is hatched.",
                color=discord.Color.orange()
            )
            egg_thumb = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "egg_background.png")
            if os.path.exists(egg_thumb):
                embed.set_thumbnail(url="attachment://egg_background.png")
                file = discord.File(egg_thumb, filename="egg_background.png")
                return await ctx.reply(embed=embed, file=file)
            return await ctx.reply(embed=embed)
        return await func(self, ctx, *args, **kwargs)
    return wrapper


def ensure_chao_lifecycle(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        author_mention = ctx.author.mention
        guild_id, guild_name, user = get_guild_user(ctx)
        now = datetime.now()

        # If using the 'hatch' command, remove one egg for reincarnated (unhatched) chao.
        if ctx.command.name.lower() == "hatch":
            chao_name_raw = (kwargs.get('chao_name') or kwargs.get('chao_name_and_fruit') or 
                             kwargs.get('chao_name_and_new_name') or (args[0] if args else None))
            if chao_name_raw:
                found = parse_chao_name(ctx, chao_name_raw, self.data_utils)
                if found:
                    chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', found)
                    stats_path = os.path.join(chao_dir, f"{found}_stats.parquet")
                    chao_df = self.data_utils.load_chao_stats(stats_path)
                    if not chao_df.empty:
                        latest = chao_df.iloc[-1].to_dict()
                        if latest.get("hatched", 0) == 0 and safe_int(latest.get("reincarnations", 0)) > 0:
                            inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
                            inv_df = self.data_utils.load_inventory(inv_path)
                            inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
                            if inv.get("Chao Egg", 0) > 0:
                                inv["Chao Egg"] = max(inv.get("Chao Egg", 0) - 1, 0)
                                self.data_utils.save_inventory(inv_path, inv_df, inv)

        # --- Finalization helpers ---
        async def finalize_reincarnation(channel, stats_path, chao_name, safe_name, wait_time, inv_path):
            await asyncio.sleep(wait_time)
            chao_df = self.data_utils.load_chao_stats(stats_path)
            if chao_df.empty:
                return
            latest_stats = chao_df.iloc[-1].to_dict()
            old_exp = {s: latest_stats.get(f"{s}_exp", 0) for s in ["swim", "fly", "run", "power", "stamina"]}
            new_stats = {
                'date': now.strftime("%Y-%m-%d"),
                'birth_date': now.strftime("%Y-%m-%d"),
                'Form': '1',
                'Type': 'neutral_normal_1',
                'hatched': 0,
                'evolved': 0,
                'dead': 0,
                'immortal': 0,
                'reincarnations': safe_int(latest_stats.get('reincarnations', 0)) + 1,
                'eyes': latest_stats.get('eyes'),
                'mouth': latest_stats.get('mouth'),
                'dark_hero': 0,
                'belly_ticks': random.randint(3, 10),
                'happiness_ticks': random.randint(3, 10),
                'illness_ticks': 0,
                'energy_ticks': random.randint(3, 10),
                'hp_ticks': 10,
                'swim_exp': 0, 'swim_grade': latest_stats.get('swim_grade', "F"),
                'swim_level': 0, 'swim_ticks': 0, 'swim_fly': 0,
                'fly_exp': 0, 'fly_grade': latest_stats.get('fly_grade', "F"),
                'fly_level': 0, 'fly_ticks': 0,
                'power_exp': 0, 'power_grade': latest_stats.get('power_grade', "F"),
                'power_level': 0, 'power_ticks': 0,
                'run_exp': 0, 'run_grade': latest_stats.get('run_grade', "F"),
                'run_level': 0, 'run_ticks': 0,
                'stamina_exp': 0, 'stamina_grade': latest_stats.get('stamina_grade', "F"),
                'stamina_level': 0, 'stamina_ticks': 0
            }

            for s in ["swim", "fly", "run", "power", "stamina"]:
                new_stats[f"{s}_exp"] = int(old_exp[s] * 0.1)
            self.data_utils.save_chao_stats(stats_path, chao_df, new_stats)
            inv_df = self.data_utils.load_inventory(inv_path)
            inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
            if inv.get("Chao Egg", 0) < 1:
                inv["Chao Egg"] = 1
                self.data_utils.save_inventory(inv_path, inv_df, inv)
            egg_thumb = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "egg_background.png")
            egg_file = discord.File(egg_thumb, filename="egg_background.png")
            embed = discord.Embed(
                title="Chao Has Reincarnated",
                description=(f"{ctx.author.mention}, your chao **{chao_name}** has fully reincarnated and is now an egg.\n"
                             "10% of each stat’s EXP carried over!"),
                color=discord.Color.pink()
            )
            embed.set_thumbnail(url="attachment://egg_background.png")
            await channel.send(file=egg_file, embed=embed)

        async def finalize_death(channel, stats_path, chao_name, safe_name):
            chao_df = self.data_utils.load_chao_stats(stats_path)
            if chao_df.empty:
                return
            latest_stats = chao_df.iloc[-1].to_dict()
            latest_stats.update({'dead': 1, 'death_notified': True})
            latest_stats.pop('death_end_time', None)
            latest_stats.pop('death_seconds_left', None)
            self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)
            embed = discord.Embed(
                title=f"{chao_name} has passed...",
                description=f"{chao_name} can no longer be interacted with.\n\n**Date of Death:** {date_of_death}",
                color=discord.Color.dark_gray()
            )
            grave = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "chao_grave.png")
            file = discord.File(grave, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
            await channel.send(file=file, embed=embed)

        # --- 'egg' command logic ---
        if ctx.command.name.lower() == "egg":
            user_folder = self.data_utils.get_user_folder(self.data_utils.update_server_folder(ctx.guild), user)
            chao_data_folder = os.path.join(user_folder, "chao_data")
            if os.path.exists(chao_data_folder):
                for folder in os.listdir(chao_data_folder):
                    stats_path = os.path.join(chao_data_folder, folder, f"{folder}_stats.parquet")
                    if os.path.exists(stats_path):
                        df_temp = self.data_utils.load_chao_stats(stats_path)
                        if not df_temp.empty:
                            stats_temp = df_temp.iloc[-1].to_dict()
                            raw_end = stats_temp.get("reincarnation_end_time") or stats_temp.get("death_end_time")
                            if raw_end:
                                try:
                                    dt_end = datetime.fromisoformat(raw_end)
                                except ValueError:
                                    dt_end = datetime.strptime(raw_end, "%Y-%m-%d %H:%M:%S")
                                if datetime.now() < dt_end:
                                    return await ctx.reply(f"{ctx.author.mention}, you cannot obtain a new Chao Egg while a chao is evolving/dying.")
            inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
            inv_df = self.data_utils.load_inventory(inv_path)
            inv_data = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
            if inv_data.get("Chao Egg", 0) > 0:
                return await ctx.reply(f"{ctx.author.mention}, you already have a Chao Egg in your inventory.")
            return await func(self, ctx, *args, **kwargs)

        # --- Otherwise, require a valid chao ---
        chao_name_raw = (kwargs.get('chao_name') or kwargs.get('chao_name_and_fruit') or 
                         kwargs.get('chao_name_and_new_name') or (args[0] if args else None))
        if not chao_name_raw:
            return await ctx.reply("Something went wrong and this action cannot proceed.")
        chao_name = parse_chao_name(ctx, chao_name_raw, self.data_utils)
        if not chao_name:
            return await ctx.reply("No valid Chao name found.")
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")
        chao_df = self.data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await ctx.reply(f"No stats found for **{chao_name}**.")
        latest_stats = chao_df.iloc[-1].to_dict()
        safe_name = chao_name.replace(" ", "_")
        channel = ctx.channel

        # Block if chao is dead.
        if latest_stats.get('dead', 0):
            embed = discord.Embed(
                title="Chao Is Dead",
                description=f"**{chao_name}** has died and can no longer be interacted with.",
                color=discord.Color.dark_gray()
            )
            grave = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "chao_grave.png")
            file = discord.File(grave, filename="chao_grave.png")
            embed.set_thumbnail(url="attachment://chao_grave.png")
            return await ctx.reply(file=file, embed=embed)

        # --- Timer active? Show countdown and overlay ---
        end_time_str = latest_stats.get("reincarnation_end_time") or latest_stats.get("death_end_time")
        is_reinc = bool(latest_stats.get("reincarnation_end_time"))
        is_death = bool(latest_stats.get("death_end_time"))

        if end_time_str:
            # <--- HERE IS THE FIX
            if end_time_str in ("0", ""):
                # Means there's no valid date/time
                seconds_left = 0
            else:
                # Attempt to parse the stored string
                try:
                    dt_end = datetime.fromisoformat(end_time_str)
                except ValueError:
                    dt_end = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                seconds_left = (dt_end - now).total_seconds()

            if seconds_left > 0:
                # The rest of your countdown logic
                if is_reinc:
                    latest_stats["reincarnation_seconds_left"] = int(seconds_left)
                if is_death:
                    latest_stats["death_seconds_left"] = int(seconds_left)
                self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)

                # Possibly pick an overlay, show embed, etc.
                image_utils = self.bot.get_cog("ImageUtils")
                bg_path = get_bg_path(image_utils, latest_stats)
                if is_reinc:
                    overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_reincarnate.png")
                    title_str = "Cacoon In Progress"
                    desc_str = f"{author_mention}, your chao **{chao_name}** is in a cacoon. Please wait {int(seconds_left)} second(s)!"
                    color_val = discord.Color.dark_gray()
                else:
                    overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_death.png")
                    title_str = "Cacoon In Progress"
                    desc_str = f"{author_mention}, your chao **{chao_name}** is in a cacoon. Please wait {int(seconds_left)} second(s)!"
                    color_val = discord.Color.red()

                file = generate_lifecycle_image(bg_path, overlay_img, safe_name)
                embed = discord.Embed(title=title_str, description=desc_str, color=color_val)
                embed.set_thumbnail(url=f"attachment://lifecycle_{safe_name}.png")
                return await ctx.reply(file=file, embed=embed)

            if is_death and not latest_stats.get("death_notified", False):
                await finalize_death(channel, stats_path, chao_name, safe_name)
                return


        # --- Stat check: if any stat reaches ≥99, trigger reincarnation or death ---
        if any(lvl >= 99 for lvl in get_stat_levels(latest_stats)):
            happiness = safe_int(latest_stats.get('happiness_ticks', 0))
            if happiness >= 5:
                dt_end = now + timedelta(seconds=60)
                latest_stats["reincarnation_end_time"] = dt_end.strftime("%Y-%m-%d %H:%M:%S")
                latest_stats["reincarnation_seconds_left"] = 60
                self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)
                inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
                asyncio.create_task(finalize_reincarnation(channel, stats_path, chao_name, safe_name, 60, inv_path))
                image_utils = self.bot.get_cog("ImageUtils")
                bg_path = get_bg_path(image_utils, latest_stats)
                overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_reincarnate.png")
                file = generate_lifecycle_image(bg_path, overlay_img, safe_name)
                embed = discord.Embed(
                    title="Cacoon In Progress",
                    description=f"{author_mention}, your chao **{chao_name}** is in a cacoon. Please wait 60 seconds.",
                    color=discord.Color.dark_gray()
                )
                embed.set_thumbnail(url=f"attachment://lifecycle_{safe_name}.png")
                await ctx.reply(file=file, embed=embed)
                return
            else:
                dt_end = now + timedelta(seconds=60)
                latest_stats["death_end_time"] = dt_end.strftime("%Y-%m-%d %H:%M:%S")
                latest_stats["death_seconds_left"] = 60
                latest_stats.pop("death_notified", None)
                self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)
                image_utils = self.bot.get_cog("ImageUtils")
                bg_path = get_bg_path(image_utils, latest_stats)
                overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_death.png")
                file = generate_lifecycle_image(bg_path, overlay_img, safe_name)
                embed = discord.Embed(
                    title="Cacoon In Progress",
                    description=f"{author_mention}, your chao **{chao_name}** is in a cacoon. Please wait 60 seconds!",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=f"attachment://lifecycle_{safe_name}.png")
                await ctx.reply(file=file, embed=embed)
                await asyncio.sleep(60)
                final_stats = self.data_utils.load_chao_stats(stats_path).iloc[-1].to_dict()
                if not final_stats.get("dead", 0):
                    await finalize_death(channel, stats_path, chao_name, safe_name)
                return

        return await func(self, ctx, *args, **kwargs)
    return wrapper


def ensure_not_in_cacoon(func):
    @wraps(func)
    async def wrapper(self, ctx, *args, **kwargs):
        """
        Prevents interaction if the Chao is currently evolving (cacoon=1).

        - If evolution_end_time is in the past => finalize immediately,
          post 'Evolution Complete' embed, and allow the command.
        - If there's time left, spawn a background task to finalize once it expires,
          and block this command with a countdown embed.
        - The 'evolution' thumbnail always uses the NEUTRAL background.
        """
        chao_name_raw = (
            kwargs.get('chao_name')
            or kwargs.get('chao_name_and_fruit')
            or kwargs.get('chao_name_and_new_name')
            or (args[0] if args else None)
        )
        if not chao_name_raw:
            return await func(self, ctx, *args, **kwargs)

        # 1) Determine actual chao name
        chao_name = parse_chao_name(ctx, chao_name_raw, self.data_utils)
        if not chao_name:
            return await ctx.reply("No valid Chao name found.")

        # 2) Load stats
        guild_id, guild_name, user = get_guild_user(ctx)
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        chao_df = self.data_utils.load_chao_stats(stats_path)
        if chao_df.empty:
            return await ctx.reply(f"{ctx.author.mention}, no stats found for **{chao_name}**.")

        latest_stats = chao_df.iloc[-1].to_dict()
        now = datetime.now()

        # 3) If chao is not in cocoon => let them proceed
        if not latest_stats.get("cacoon", 0):
            return await func(self, ctx, *args, **kwargs)

        end_time_str = latest_stats.get("evolution_end_time")
        if not end_time_str:
            # If we have cacoon=1 but no end_time => treat as ended
            seconds_left = 0
        else:
            try:
                dt_end = datetime.fromisoformat(end_time_str)
            except ValueError:
                dt_end = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            seconds_left = (dt_end - now).total_seconds()

        # 4) If time is up => finalize now
        if seconds_left <= 0:
            if latest_stats.get("Form") == "3" and latest_stats.get("cacoon") == 1:
                latest_stats["cacoon"] = 0
                latest_stats["evolved"] = 1
                latest_stats.pop("evolution_end_time", None)
                latest_stats.pop("evolution_seconds_left", None)

                # Save
                self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)

                # Post embed about finishing
                thumb_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
                embed = discord.Embed(
                    title="Evolution Complete",
                    description=f"{ctx.author.mention}, your chao **{chao_name}** has finished evolving!",
                    color=discord.Color.green()
                )

                files = []
                if os.path.exists(thumb_path):
                    safe_thumb = os.path.basename(thumb_path).replace(" ", "_")
                    thumb_file = discord.File(thumb_path, filename=safe_thumb)
                    embed.set_thumbnail(url=f"attachment://{safe_thumb}")
                    files.append(thumb_file)

                await ctx.reply(embed=embed, files=files)

            # Let the user's command proceed now that it's done
            return await func(self, ctx, *args, **kwargs)

        # 5) Otherwise => time remains => spawn background finalize + block
        secs_left = int(seconds_left)
        latest_stats["evolution_seconds_left"] = secs_left
        self.data_utils.save_chao_stats(stats_path, chao_df, latest_stats)

        async def finalize_evolution_later():
            await asyncio.sleep(secs_left)
            df_now = self.data_utils.load_chao_stats(stats_path)
            if df_now.empty:
                return
            current = df_now.iloc[-1].to_dict()

            if current.get("cacoon", 0) == 1:
                current["cacoon"] = 0
                current["evolved"] = 1
                current.pop("evolution_end_time", None)
                current.pop("evolution_seconds_left", None)
                self.data_utils.save_chao_stats(stats_path, df_now, current)

                thumb_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")
                embed = discord.Embed(
                    title="Evolution Complete",
                    description=f"{ctx.author.mention}, your chao **{chao_name}** has finished evolving!",
                    color=discord.Color.green()
                )

                files = []
                if os.path.exists(thumb_path):
                    safe_thumb = os.path.basename(thumb_path).replace(" ", "_")
                    thumb_file = discord.File(thumb_path, filename=safe_thumb)
                    embed.set_thumbnail(url=f"attachment://{safe_thumb}")
                    files.append(thumb_file)

                await ctx.channel.send(embed=embed, files=files)

        asyncio.create_task(finalize_evolution_later())

        # Instead of using the dynamic background, we always use NEUTRAL
        bg_path = os.path.join(ASSETS_DIR, "graphics", "thumbnails", "neutral_background.png")

        overlay_img = os.path.join(ASSETS_DIR, "graphics", "cacoons", "cacoon_evolve.png")
        safe_name = chao_name.replace(" ", "_")
        file = generate_lifecycle_image(bg_path, overlay_img, safe_name)

        embed = discord.Embed(
            title="Chao Is Evolving!",
            description=(
                f"{ctx.author.mention}, your chao **{chao_name}** is evolving!\n"
                f"Please wait **{secs_left}** second(s)."
            ),
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=f"attachment://{file.filename}")
        return await ctx.reply(embed=embed, file=file)

    return wrapper
