import os, json, random, asyncio, discord, pandas as pd
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime
from typing import List, Tuple, Dict, Optional

PERSISTENT_VIEWS_FILE = "persistent_views.json"

class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        c = json.load(open('config.json'))
        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4, a = *c['FORM_LEVELS'], c['ALIGNMENTS']
        self.HERO_ALIGNMENT, self.DARK_ALIGNMENT, self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX = (
            a['hero'], a['dark'], *c['FRUIT_TICKS_RANGE']
        )
        self.FRUIT_STATS, self.GRADES = c['FRUIT_STATS'], ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.GRADE_TO_VALUE = {g: v for g, v in zip(self.GRADES, range(-1, 7))}
        self.eye_types, self.mouth_types = [
            'normal', 'happy', 'angry', 'sad', 'sleep', 'tired', 'pain'
        ], ['happy', 'unhappy', 'mean', 'grumble', 'evil']
        self.chao_names = ["Chaoko", "Chaowser", "Chaorunner", "Chaozart", "Chaozilla"]
        self.fruits = ["Hero Fruit", "Dark Fruit", "Swim Fruit", "Fly Fruit", "Run Fruit", "Power Fruit"]

        # Add missing thresholds
        self.RUN_POWER_THRESHOLD = c.get("RUN_POWER_THRESHOLD", 5)  # Default to 5
        self.SWIM_FLY_THRESHOLD = c.get("SWIM_FLY_THRESHOLD", 5)    # Default to 5

        self.assets_dir = None



    async def cog_load(self):
        i, p, a = self.bot.get_cog, os.path.join, self.__setattr__
        self.image_utils, self.data_utils = i('ImageUtils'), i('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("Required cogs not loaded.")

        self.assets_dir = self.image_utils.assets_dir
        [a(k, p(self.assets_dir, v)) for k, v in {
            'TEMPLATE_PATH': 'graphics/cards/stats_page_1.png',
            'TEMPLATE_PAGE_2_PATH': 'graphics/cards/stats_page_2.png',
            'OVERLAY_PATH': 'graphics/ticks/tick_filled.png',
            'ICON_PATH': 'graphics/icons/Stats.png',
            'BACKGROUND_PATH': 'graphics/thumbnails/neutral_background.png',  # Add this
            'NEUTRAL_PATH': 'chao/normal/neutral/neutral_normal_1.png'        # Add this
        }.items()]
        a('PAGE1_TICK_POSITIONS', [(446, y) for y in [1176, 315, 591, 883, 1469]])
        a('PAGE2_TICK_POSITIONS', {k: (272, v) for k, v in zip(['belly', 'happiness', 'illness', 'energy', 'hp'], [314, 590, 882, 1175, 1468])})

        # Add these lines for EYES_DIR and MOUTH_DIR
        a('EYES_DIR', p(self.assets_dir, 'face', 'eyes'))
        a('MOUTH_DIR', p(self.assets_dir, 'face', 'mouth'))

        # Reload persistent views
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
                view = StatsView.from_data(view_data, self)
                self.bot.add_view(view)

    def send_embed(self, ctx, description: str, title: str = "Chao Bot"):
        """Sends an embed with a given description and title."""
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)  # Ensure embed is sent properly

    def check_life_cycle(self, c: Dict) -> str:
        if (datetime.now() - datetime.strptime(c['birth_date'], "%Y-%m-%d")).days < 60: return "alive"
        return "reincarnated" if c.get('happiness_ticks', 0) > 5 and not c.update({k: 0 for k in [f"{x}_{y}" for x in ['swim', 'fly', 'run', 'power', 'stamina'] for y in ['ticks', 'level', 'exp']]} | {'reincarnations': c.get('reincarnations', 0) + 1, 'happiness_ticks': 10, 'birth_date': datetime.now().strftime("%Y-%m-%d")}) else c.update({'dead': 1}) or "died"


    async def force_life_check(self, ctx, *, chao_name: str):
        g, u, p, l, s, o, t, e = str(ctx.guild.id), str(ctx.author.id), self.data_utils.get_path, self.data_utils.load_chao_stats, self.data_utils.save_chao_stats, os.path, datetime.now, discord.Embed
        f = o.join(p(g, u, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not o.exists(f): return await ctx.send(embed=e(description=f"{ctx.author.mention}, no Chao named **{chao_name}** exists.", color=0xFF0000))
        c, d = l(f), l(f).iloc[-1].to_dict(); m = f"✨ **{chao_name} has reincarnated! A fresh start begins!**" if d.get('happiness_ticks', 0) > 5 else f"😢 **{chao_name} has passed away due to low happiness.**"
        s(f, c, {"reincarnations": d.get('reincarnations', 0) + 1, "happiness_ticks": 10, "birth_date": t().strftime("%Y-%m-%d"), **{f"{x}_{y}": 0 for x in ['swim', 'fly', 'run', 'power', 'stamina'] for y in ['ticks', 'level', 'exp']}} if d.get('happiness_ticks', 0) > 5 else {**d, "dead": 1})
        await ctx.send(embed=e(description=m, color=0x00FF00 if "reincarnated" in m else 0x8B0000))

    async def force_happiness(self, ctx, *, chao_name: str, happiness_value: int):
        g, u, p, l, s, o, e = str(ctx.guild.id), str(ctx.author.id), self.data_utils.get_path, self.data_utils.load_chao_stats, self.data_utils.save_chao_stats, os.path, discord.Embed
        f = o.join(p(g, u, 'chao_data', chao_name), f"{chao_name}_stats.parquet")
        if not o.exists(f): return await ctx.send(embed=e(description=f"{ctx.author.mention}, no Chao named **{chao_name}** exists.", color=0xFF0000))
        c = l(f); d = c.iloc[-1].to_dict(); d['happiness_ticks'] = happiness_value; s(f, c, d)
        await ctx.send(embed=e(description=f"✅ **{chao_name}'s happiness has been set to {happiness_value}.**", color=0x00FF00))

    async def chao(self, ctx):
        await self.initialize_inventory(
            ctx, str(ctx.guild.id), str(ctx.author.id),
            "Welcome to Chao Bot!",
            "**You Receive:**\n- `1x Chao Egg`\n- `500x Rings`\n- `5x Garden Nut`\n\n"
            "**Example Commands:**\n- `$feed [Chao name] [item]` to feed your Chao.\n"
            "- `$race [Chao name]` to enter your Chao in a race.\n"
            "- `$train [Chao name] [stat]` to train a specific stat.\n"
            "- `$stats [Chao name]` to view your Chao's stats."
        )

    async def initialize_inventory(self, ctx, guild_id, user_id, embed_title, embed_desc):
        if self.data_utils.is_user_initialized(guild_id, user_id):
            return await ctx.send(f"{ctx.author.mention}, you have already started using the Chao Bot.")
        inventory_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        self.data_utils.save_inventory(
            inventory_path,
            self.data_utils.load_inventory(inventory_path),
            {'rings': 500, 'Chao Egg': 1, 'Garden Fruit': 5}
        )
        await ctx.reply(
            file=discord.File(self.NEUTRAL_PATH, filename="neutral_normal_1.png"),
            embed=discord.Embed(title=embed_title, description=embed_desc, color=self.embed_color)
            .set_image(url="attachment://neutral_normal_1.png")
        )

    
    async def give_rings(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inventory_df = self.data_utils.load_inventory(inventory_path)
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {'rings': 0}
        current_inventory['rings'] = current_inventory.get('rings', 0) + 10000
        self.data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has been given 10000 rings! Your current rings: {current_inventory['rings']}")
        print(f"[give_rings] 10000 Rings added to User: {user_id}. New balance: {current_inventory['rings']}")


    async def hatch(self, ctx):
        """
        Command to hatch a Chao Egg. Initializes the Chao's database with default stats
        and generates the initial thumbnail for the Chao.
        """
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data')
        inventory_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')

        # Load the user's inventory
        inventory_df = self.data_utils.load_inventory(inventory_path)
        inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {}

        # Check if the user has a Chao Egg to hatch
        if inventory.get('Chao Egg', 0) < 1:
            return await ctx.send(f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")

        # Decrement the Chao Egg count in the inventory
        inventory['Chao Egg'] -= 1
        self.data_utils.save_inventory(inventory_path, inventory_df, inventory)

        # Generate a unique name for the Chao
        os.makedirs(chao_dir, exist_ok=True)
        chao_name = next(name for name in (random.choice(self.chao_names) for _ in range(100)) if name not in os.listdir(chao_dir))

        # Create the Chao's stats directory
        chao_path = os.path.join(chao_dir, chao_name)
        os.makedirs(chao_path, exist_ok=True)

        # Initialize the Chao's database with the required stats
        chao_stats = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'birth_date': datetime.now().strftime("%Y-%m-%d"),
            'Form': '1',
            'Type': 'Normal',
            'hatched': 1,
            'evolved': 0,
            'dead': 0,
            'immortal': 0,
            'reincarnations': 0,
            'eyes': random.choice(self.eye_types),
            'mouth': random.choice(self.mouth_types),
            'dark_hero': 0,
            'belly_ticks': 5,
            'happiness_ticks': 10,
            'illness_ticks': 0,
            'energy_ticks': 10,
            'hp_ticks': 10,
            'swim_exp': 0,
            'swim_grade': 'D',
            'swim_level': 0,
            'swim_fly': 0,
            'fly_exp': 0,
            'fly_grade': 'D',
            'fly_level': 0,
            'fly_ticks': 0,
            'power_exp': 0,
            'power_grade': 'D',
            'power_level': 0,
            'power_ticks': 0,
            'run_exp': 0,
            'run_grade': 'D',
            'run_level': 0,
            'run_power': 0,
            'run_ticks': 0,
            'stamina_exp': 0,
            'stamina_grade': 'D',
            'stamina_level': 0,
            'stamina_ticks': 0
        }

        # Save the Chao's stats to a Parquet file
        chao_stats_path = os.path.join(chao_path, f'{chao_name}_stats.parquet')
        self.data_utils.save_chao_stats(chao_stats_path, pd.DataFrame([chao_stats]))

        # Generate the Chao's initial thumbnail image
        eyes_image_path = os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png") \
            if os.path.exists(os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png")) else \
            os.path.join(self.EYES_DIR, "neutral.png")
        mouth_image_path = os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png") \
            if os.path.exists(os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png")) else \
            os.path.join(self.MOUTH_DIR, "happy.png")
        thumbnail_path = os.path.join(chao_path, f"{chao_name}_thumbnail.png")

        self.image_utils.combine_images_with_face(
            self.BACKGROUND_PATH,
            self.NEUTRAL_PATH,
            eyes_image_path,
            mouth_image_path,
            thumbnail_path
        )

        # Send a confirmation message with the Chao's thumbnail
        embed = discord.Embed(
            title="Your Chao Egg has hatched!",
            description=f"Your Chao Egg hatched into a Regular Two-tone Chao named **{chao_name}**!",
            color=discord.Color.blue()
        ).set_image(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")

        await ctx.reply(
            file=discord.File(thumbnail_path, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"),
            embed=embed
        )


    def update_chao_type_and_thumbnail(self, guild_id: str, user_id: str, chao_name: str, latest_stats: Dict) -> Tuple[Optional[str], Optional[str]]:
        try:
            # Check if assets_dir is properly set
            if not self.assets_dir:
                raise ValueError("assets_dir is not set. Ensure cog_load initializes it correctly.")
            
            chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

            stat_levels = {s: latest_stats.get(f'{s}_level', 0) for s in ['power', 'swim', 'stamina', 'fly', 'run']}
            max_stat, max_level = max(stat_levels, key=stat_levels.get), max(stat_levels.values())
            dark_hero, form = latest_stats.get('dark_hero', 0), latest_stats.get('Form', "1")
            current_type = latest_stats.get('Type', 'normal').lower()
            chao_type = current_type or "normal"

            alignment = "neutral"
            if form in ["1", "2"]:
                alignment = "hero" if dark_hero >= self.HERO_ALIGNMENT else \
                            "dark" if dark_hero <= self.DARK_ALIGNMENT else "neutral"
                latest_stats['Alignment'] = alignment
            else:
                alignment = latest_stats.get('Alignment', 'neutral')

            def evolve_type(form_num, current_type, stats):
                run_power, swim_fly = stats.get('run_power', 0), stats.get('swim_fly', 0)
                if form_num == 2:
                    return f"{current_type}_power" if run_power >= self.RUN_POWER_THRESHOLD else \
                        f"{current_type}_run" if run_power <= -self.RUN_POWER_THRESHOLD else \
                        f"{current_type}_fly" if swim_fly >= self.SWIM_FLY_THRESHOLD else \
                        f"{current_type}_swim" if swim_fly <= -self.SWIM_FLY_THRESHOLD else f"{current_type}_normal"
                elif form_num == 3:
                    return "power" if run_power >= self.RUN_POWER_THRESHOLD else \
                        "run" if run_power <= -self.RUN_POWER_THRESHOLD else \
                        "fly" if swim_fly >= self.SWIM_FLY_THRESHOLD else \
                        "swim" if swim_fly <= -self.SWIM_FLY_THRESHOLD else "normal"
                elif form_num == 4:
                    second = "power" if run_power >= self.RUN_POWER_THRESHOLD else \
                            "run" if run_power <= -self.RUN_POWER_THRESHOLD else \
                            "fly" if swim_fly >= self.SWIM_FLY_THRESHOLD else \
                            "swim" if swim_fly <= -self.SWIM_FLY_THRESHOLD else "normal"
                    base = current_type if current_type in ['power', 'run', 'swim', 'fly', 'normal'] else 'normal'
                    return f"{base}_{second}"
                return current_type

            if form == "1" and max_level >= self.FORM_LEVEL_2:
                form, chao_type = "2", evolve_type(2, chao_type, latest_stats)
            elif form == "2" and max_level >= self.FORM_LEVEL_3:
                form, chao_type = "3", evolve_type(3, chao_type, latest_stats)
            elif form == "3" and max_level >= self.FORM_LEVEL_4:
                form, chao_type = "4", evolve_type(4, chao_type, latest_stats)
                chao_type = f"{chao_type}_normal" if "_" not in chao_type else chao_type

            latest_stats.update({'Type': chao_type, 'Form': form})

            eyes = latest_stats['eyes']
            mouth = latest_stats['mouth']
            eyes_alignment = "neutral" if form in ["1", "2"] else alignment

            eyes_image_path = os.path.join(self.EYES_DIR, f"{eyes_alignment}_{eyes}.png") \
                if os.path.exists(os.path.join(self.EYES_DIR, f"{eyes_alignment}_{eyes}.png")) else \
                os.path.join(self.EYES_DIR, f"{eyes_alignment}.png") if os.path.exists(os.path.join(self.EYES_DIR, f"{eyes_alignment}.png")) else \
                os.path.join(self.EYES_DIR, "neutral.png")
            mouth_image_path = os.path.join(self.MOUTH_DIR, f"{mouth}.png") \
                if os.path.exists(os.path.join(self.MOUTH_DIR, f"{mouth}.png")) else \
                os.path.join(self.MOUTH_DIR, "happy.png")

            chao_image_filename = f"{alignment}_{chao_type}_{form}.png"
            chao_image_path = os.path.join(self.assets_dir, 'chao', chao_type.split('_')[0], alignment, chao_image_filename)
            if not os.path.exists(chao_image_path):
                chao_image_path = os.path.join(self.assets_dir, 'chao', 'chao_missing.png')

            self.image_utils.combine_images_with_face(
                self.BACKGROUND_PATH,
                chao_image_path,
                eyes_image_path,
                mouth_image_path,
                thumbnail_path
            )
            return chao_type, form
        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] Error: {e}")
            return "normal", "1"  # Fallback to default values


    async def stats(self, ctx, *, chao_name: str):
        """
        Command to display the stats of a specific Chao. This generates the Page 1 and Page 2
        stat cards dynamically and sends them as Discord embeds with attached images.
        """
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')

        # Ensure the Chao exists
        if not os.path.exists(chao_stats_path):
            return await ctx.send(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        # Load the Chao stats from the database
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()  # Get the most recent stats

        # Debugging: Print the loaded stats
        print("DEBUG - Chao Stats Loaded from Database:")
        for key, value in chao_stats.items():
            print(f"{key}: {value}")

        # Update Chao type and thumbnail (this function also updates alignment/type visuals)
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_stats)
        chao_type_display = "Normal" if form in ["1", "2"] else chao_type.replace("_", "/").capitalize()
        alignment_label = chao_stats.get('Alignment', 'Neutral').capitalize()

        # Image paths
        stats_image_paths = {
            1: os.path.join(chao_dir, f'{chao_name}_stats_page_1.png'),
            2: os.path.join(chao_dir, f'{chao_name}_stats_page_2.png')
        }
        thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

        # Extract the relevant levels and ticks from the database (and convert to integers)
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

        # Debugging: Confirm extracted values before passing them to the image function
        print("DEBUG - Extracted Levels and Ticks:")
        print(f"Power Level: {power_level}, Ticks: {power_ticks}, EXP: {power_exp}")
        print(f"Swim Level: {swim_level}, Ticks: {swim_ticks}, EXP: {swim_exp}")
        print(f"Fly Level: {fly_level}, Ticks: {fly_ticks}, EXP: {fly_exp}")
        print(f"Run Level: {run_level}, Ticks: {run_ticks}, EXP: {run_exp}")
        print(f"Stamina Level: {stamina_level}, Ticks: {stamina_ticks}, EXP: {stamina_exp}")

        # Generate images for stats (Page 1 and Page 2)
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
                {stat: chao_stats.get(f"{stat}_ticks", 0) for stat in self.PAGE2_TICK_POSITIONS}
            )
        )

        # Prepare Embed
        embed = discord.Embed(color=self.embed_color).set_author(
            name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png"
        ).add_field(
            name="Type", value=chao_type_display, inline=True
        ).add_field(
            name="Alignment", value=alignment_label, inline=True
        ).set_thumbnail(
            url="attachment://chao_thumbnail.png"
        ).set_image(
            url="attachment://stats_page.png"
        ).set_footer(
            text="Page 1 / 2"
        )

        # StatsView Instance
        view = StatsView.from_data({
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user_id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        }, self)

        # Save the persistent view
        self.save_persistent_view({
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user_id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        })

        # Send the embed with files
        await ctx.send(
            files=[
                discord.File(stats_image_paths[1], "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(thumbnail_path, filename="chao_thumbnail.png")
            ],
            embed=embed,
            view=view
        )


    async def give_egg(self, ctx):
        p, i, d = self.data_utils.get_path, self.data_utils.load_inventory, self.data_utils.save_inventory
        u, g = str(ctx.author.id), str(ctx.guild.id)
        c, e = ctx.send, discord.Embed(title="🎉 Congratulations!", description="**You received a Chao Egg!**", color=self.embed_color)
        f = lambda x: x.iloc[-1].to_dict() if not x.empty else {}
        v, w = p(g, u, 'user_data', 'inventory.parquet'), os.path.join(self.assets_dir, "graphics/icons/ChaoEgg.png")
        h = i(v); s = f(h); k = 'Chao Egg'
        if s.get(k, 0) >= 1: return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg!")
        s[k] = s.get(k, 0) + 1; d(v, h, s)
        await c(file=discord.File(w, "ChaoEgg.png"), embed=e.set_thumbnail(url="attachment://ChaoEgg.png")) if os.path.exists(w) else await c(embed=e)


    async def inventory(self, ctx):
        i, p, l, f = self.data_utils.get_path, self.data_utils.load_inventory, discord.Embed, self.fruits
        c, g, u = ctx.send, str(ctx.guild.id), str(ctx.author.id)
        v = l(i(g, u, 'user_data', 'inventory.parquet')).fillna(0)
        d = v.iloc[-1].to_dict() if not v.empty else {'rings': 0}
        e = f(title="Your Inventory", description="Here's what you have:", color=self.embed_color)
        e.add_field(name='Rings', value=d.get("rings", 0), inline=False).add_field(name='Last Updated', value=d.get("date", "N/A"), inline=False)
        [e.add_field(name=k, value=f"Quantity: {int(d[k])}", inline=True) for k in f if int(d.get(k, 0)) > 0]
        e.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f"Quantity: {int(d['Chao Egg'])}", inline=True) if int(d.get('Chao Egg', 0)) > 0 else None
        await c(embed=e)

    async def feed(self, ctx, *, chao_name_and_fruit: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        parts = chao_name_and_fruit.split()

        # Identify fruit and Chao name
        for i in range(1, len(parts) + 1):
            potential = ' '.join(parts[-i:])
            if fruit := next((f for f in self.fruits if f.lower() == potential.lower()), None):
                chao_name = ' '.join(parts[:-i])
                fruit_name = fruit
                break
        else:
            return await self.send_embed(ctx, f"{ctx.author.mention}, provide a valid Chao name and fruit.")

        # Check if the Chao exists
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        # Check inventory for fruit
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        if current_inv.get(fruit_name, 0) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you have no **{fruit_name}**.")

        # Load and modify Chao stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].copy()
        days_elapsed = (datetime.now() - datetime.strptime(latest_stats.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")).days
        latest_stats['belly'] = max(0, latest_stats.get('belly', 0) - days_elapsed)
        latest_stats['belly'] = min(10, latest_stats['belly'] + 2)  # Feeding increases belly
        latest_stats['date'] = datetime.now().strftime("%Y-%m-%d")

        # Update ticks and levels
        stat_key = f"{self.FRUIT_STATS[fruit_name]}_ticks"
        level_key = f"{self.FRUIT_STATS[fruit_name]}_level"
        latest_stats[stat_key] += random.randint(self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX)

        level_up_message = ""
        if latest_stats[stat_key] >= 10:
            latest_stats[stat_key] %= 10
            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
            exp_key = f"{self.FRUIT_STATS[fruit_name]}_exp"
            grade_key = f"{self.FRUIT_STATS[fruit_name]}_grade"
            latest_stats[exp_key] += self.calculate_exp_gain(latest_stats.get(grade_key, 'D'))
            level_up_message = f"🎉 **{chao_name} leveled up!** {level_key.split('_')[0].capitalize()} is now Level {latest_stats[level_key]}.\n"

        # Handle alignment and stat adjustments based on the fruit type
        current_form = latest_stats.get('Form', '1')
        if current_form in ["1", "2"]:
            if fruit_name.lower() == 'hero fruit':
                latest_stats['dark_hero'] = min(self.HERO_ALIGNMENT, latest_stats.get('dark_hero', 0) + 1)
            elif fruit_name.lower() == 'dark fruit':
                latest_stats['dark_hero'] = max(self.DARK_ALIGNMENT, latest_stats.get('dark_hero', 0) - 1)

        run_power, swim_fly = latest_stats.get('run_power', 0), latest_stats.get('swim_fly', 0)
        fname = fruit_name.lower()
        if fname == 'swim fruit':
            latest_stats['swim_fly'] = max(-self.SWIM_FLY_THRESHOLD, swim_fly - 1)
            latest_stats['run_power'] += 1 if run_power < 0 else -1
        elif fname == 'fly fruit':
            latest_stats['swim_fly'] = min(self.SWIM_FLY_THRESHOLD, swim_fly + 1)
            latest_stats['run_power'] += 1 if run_power < 0 else -1
        elif fname == 'run fruit':
            latest_stats['run_power'] = max(-self.RUN_POWER_THRESHOLD, run_power - 1)
            latest_stats['swim_fly'] += 1 if swim_fly < 0 else -1
        elif fname == 'power fruit':
            latest_stats['run_power'] = min(self.RUN_POWER_THRESHOLD, run_power + 1)
            latest_stats['swim_fly'] += 1 if swim_fly < 0 else -1

        # Update Chao type and thumbnail
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, latest_stats)
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        # Deduct fruit and save data
        current_inv[fruit_name] -= 1
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats.to_dict())

        # Send confirmation message with updated thumbnail
        description = (
            f"🍽️ **{chao_name} ate a {fruit_name}!**\n"
            f"{level_up_message}"
            f"🍏 **Belly:** {latest_stats['belly']}/10\n"
            f"🔧 **Ticks:** {latest_stats[stat_key]}/10\n"
            f"📈 **Level:** {latest_stats[level_key]}\n"
            f"**Alignment:** {latest_stats.get('dark_hero', 0)}\n"
            f"**Run/Power Balance:** {latest_stats.get('run_power', 0)}\n"
            f"**Swim/Fly Balance:** {latest_stats.get('swim_fly', 0)}"
        )

        embed = discord.Embed(
            title="Chao Feed Success",
            description=description,
            color=self.embed_color
        ).set_image(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")

        await ctx.send(
            file=discord.File(thumbnail_path, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"),
            embed=embed
        )




    def calculate_exp_gain(self, grade: str) -> int:
        return {
            'F': 1, 'E': 2, 'D': 3, 'C': 4, 'B': 5, 'A': 6, 'S': 7, 'X': 8
        }.get(grade.upper(), 3)


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
        current_page: int = 1
    ):
        super().__init__(timeout=None)  # Persistent views require timeout=None
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
        self.current_page = current_page
        self.sanitized_chao_name = chao_name.replace(" ", "_")

        # Add navigation buttons
        self.add_item(self.create_button("⬅️", "previous_page", f"{guild_id}_{user_id}_{chao_name}_prev"))
        self.add_item(self.create_button("➡️", "next_page", f"{guild_id}_{user_id}_{chao_name}_next"))

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        """Create a navigation button with a dynamic callback."""
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def previous_page(self, interaction: discord.Interaction):
        """Handle the 'Previous Page' button."""
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("You cannot interact with this view.", ephemeral=True)
        self.current_page = self.total_pages if self.current_page == 1 else self.current_page - 1
        await self.update_stats(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Handle the 'Next Page' button."""
        if interaction.user.id != int(self.user_id):
            return await interaction.response.send_message("You cannot interact with this view.", ephemeral=True)
        self.current_page = 1 if self.current_page == self.total_pages else self.current_page + 1
        await self.update_stats(interaction)

    async def update_stats(self, interaction: discord.Interaction):
        """Update the stats image and embed dynamically."""
        # Fetch the latest Chao data
        chao_dir = self.data_utils.get_path(self.guild_id, self.user_id, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)

        if chao_df.empty:
            return await interaction.response.send_message("No stats data available for this Chao.", ephemeral=True)

        chao_to_view = chao_df.iloc[-1].to_dict()
        image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_{self.current_page}.png')

        # Generate the correct stats image based on the current page
        if self.current_page == 1:
            await asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.template_path, self.overlay_path, image_path, self.page1_tick_positions,
                *[chao_to_view.get(f"{stat}_ticks", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_to_view.get(f"{stat}_level", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_to_view.get(f"{stat}_exp", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']]
            )
        else:
            stats_values_page2 = {stat: chao_to_view.get(f"{stat}_ticks", 0) for stat in self.page2_tick_positions}
            await asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.template_page_2_path, self.overlay_path, image_path,
                self.page2_tick_positions, stats_values_page2
            )

        # Update the embed
        embed = discord.Embed(color=discord.Color.blue()).set_author(
            name=f"{self.chao_name}'s Stats",
            icon_url="attachment://Stats.png"
        ).add_field(name="Type", value=self.chao_type_display, inline=True)\
         .add_field(name="Alignment", value=self.alignment_label, inline=True)\
         .set_thumbnail(url="attachment://chao_thumbnail.png")\
         .set_image(url="attachment://stats_page.png")\
         .set_footer(text=f"Page {self.current_page} / {self.total_pages}")

        # Edit the message with updated content
        await interaction.response.edit_message(
            embed=embed,
            attachments=[
                discord.File(image_path, "stats_page.png"),
                discord.File(self.icon_path, filename="Stats.png"),
                discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
            ],
            view=self
        )

    @classmethod
    def from_data(cls, view_data: Dict, cog):
        """Reconstruct a StatsView instance from saved data."""
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
    await bot.add_cog(Chao(bot))
