# cogs/chao.py
import os, json, random, asyncio, discord, shutil, pandas as pd
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

        # Extract thresholds and alignments
        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4, a = *c['FORM_LEVELS'], c['ALIGNMENTS']
        self.HERO_ALIGNMENT, self.DARK_ALIGNMENT, self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX = (
            a['hero'], a['dark'], *c['FRUIT_TICKS_RANGE']
        )

        # Fruit stats and grading
        self.FRUIT_STATS, self.GRADES = c['FRUIT_STATS'], ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.GRADE_TO_VALUE = {g: v for g, v in zip(self.GRADES, range(-1, 7))}

        # Define fruit stats adjustments
        self.fruit_stats_adjustments = {
            "round fruit": {        "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "triangle fruit": {     "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "square fruit": {       "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "hero fruit": {         "stamina_ticks": (1, 3),      "dark_hero": 1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "dark fruit": {         "stamina_ticks": (1, 3),      "dark_hero": -1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "chao fruit": {         "swim_ticks": 4,              "fly_ticks": 4,           "run_ticks": 4,       "power_ticks": 4,     "stamina_ticks": 4,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "strong fruit": {       "stamina_ticks": 2,                                                                                                             "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "tasty fruit": {        "stamina_ticks": (3, 6),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "heart fruit": {        "stamina_ticks": (1, 2),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "garden nut": {         "stamina_ticks": (1, 3),                                                                                                        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "orange fruit": {       "swim_ticks": 3,              "fly_ticks": -2,          "run_ticks": -2,      "power_ticks": 3,     "stamina_ticks": 1,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "blue fruit": {         "swim_ticks": 2,              "fly_ticks": 5,           "run_ticks": -1,      "power_ticks": -1,    "stamina_ticks": 3,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "pink fruit": {         "swim_ticks": 4,              "fly_ticks": -3,          "run_ticks": 4,       "power_ticks": -3,    "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "green fruit": {        "swim_ticks": 0,              "fly_ticks": -1,          "run_ticks": 3,       "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "purple fruit": {       "swim_ticks": -2,             "fly_ticks": 3,           "run_ticks": 3,       "power_ticks": -2,    "stamina_ticks": 1,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "yellow fruit": {       "swim_ticks": -3,             "fly_ticks": 4,           "run_ticks": -3,      "power_ticks": 4,     "stamina_ticks": 2,         "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "red fruit": {          "swim_ticks": 3,              "fly_ticks": 1,           "run_ticks": 3,       "power_ticks": 2,     "stamina_ticks": -5,        "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "power fruit": {        "power_ticks": (8),           "run_power": 1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "swim fruit": {         "swim_ticks": (8),            "swim_fly": -1,                                                                                   "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "run fruit": {          "run_ticks": (8),             "run_power": -1,                                                                                  "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "fly fruit": {          "fly_ticks": (8),             "swim_fly": 1,                                                                                    "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
            "strange mushroom": {},  # Add custom logic for randomizing ticks
        }

        # Eye and mouth variations
        self.eye_types = ['normal', 'happy', 'angry', 'tired']
        self.mouth_types = ['happy', 'unhappy', 'evil', 'none']

        # Example chao names
        self.chao_names = [
            "Chaoko", "Chaowser", "Chaorunner", "Chaozart", "Chaobacca", "Chaowder",
            "Chaocolate", "Chaolesterol", "Chao Mein", "Chaoster", "Chaomanji", "Chaosmic",
            "Chaozilla", "Chaoseidon", "Chaosferatu", "Chaolin", "Chow", "Chaotzhu",
            "Chaoblin", "Count Chaocula", "Chaozil", "Chaoz"
        ]

        # Fruits list
        self.fruits = [fruit.title() for fruit in self.fruit_stats_adjustments.keys()]

        # Thresholds for run_power / swim_fly
        self.RUN_POWER_THRESHOLD = c.get("RUN_POWER_THRESHOLD", 5)
        self.SWIM_FLY_THRESHOLD = c.get("SWIM_FLY_THRESHOLD", 5)

        self.assets_dir = None  # Will be set in cog_load


    async def cog_load(self):
        """Called automatically when this Cog is loaded. We set up all required file paths here."""
        i, p, a = self.bot.get_cog, os.path.join, self.__setattr__
        self.image_utils, self.data_utils = i('ImageUtils'), i('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("Required cogs not loaded.")

        # Assets directory from ImageUtils
        self.assets_dir = self.image_utils.assets_dir

        # Define relevant file paths
        [a(k, p(self.assets_dir, v)) for k, v in {
            'TEMPLATE_PATH': 'graphics/cards/stats_page_1.png',
            'TEMPLATE_PAGE_2_PATH': 'graphics/cards/stats_page_2.png',
            'OVERLAY_PATH': 'graphics/ticks/tick_filled.png',
            'ICON_PATH': 'graphics/icons/Stats.png',
            # Default background for forms 1 & 2
            'BACKGROUND_PATH': 'graphics/thumbnails/neutral_background.png',
            'NEUTRAL_PATH': 'chao/normal/neutral/neutral_normal_1.png'
        }.items()]

        # Additional backgrounds for forms 3 & 4
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

        # Directories for eyes and mouth
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
                required_keys = {
                    "chao_name", "guild_id", "user_id",
                    "chao_type_display", "alignment_label", "total_pages"
                }

                # Add missing defaults
                if not required_keys.issubset(view_data.keys()):
                    print(f"[load_persistent_views] Key={key} is missing fields. Adding defaults.")
                    view_data.setdefault("chao_type_display", "Unknown")
                    view_data.setdefault("alignment_label", "Neutral")
                    view_data.setdefault("total_pages", 2)
                    view_data.setdefault("current_page", 1)

                view = StatsView.from_data(view_data, self)
                self.bot.add_view(view)


    def send_embed(self, ctx, description: str, title: str = "Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.reply(embed=embed)

    def check_life_cycle(self, c: Dict) -> str:
        """Check if a Chao is older than 60 days and decide if it reincarnates or dies."""
        if (datetime.now() - datetime.strptime(c['birth_date'], "%Y-%m-%d")).days < 60:
            return "alive"
        return (
            "reincarnated"
            if c.get('happiness_ticks', 0) > 5 and not c.update({
                k: 0 for k in [
                    f"{x}_{y}"
                    for x in ['swim', 'fly', 'run', 'power', 'stamina']
                    for y in ['ticks', 'level', 'exp']
                ]
            } | {
                'reincarnations': c.get('reincarnations', 0) + 1,
                'happiness_ticks': 10,
                'birth_date': datetime.now().strftime("%Y-%m-%d")
            })
            else c.update({'dead': 1}) or "died"
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

    async def chao(self, ctx):
        """Initialize a user in the Chao system if not done already."""
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        if self.data_utils.is_user_initialized(guild_id, guild_name, user):
            return await ctx.reply(f"{ctx.author.mention}, you have already started using the Chao Bot.")

        inventory_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        self.data_utils.save_inventory(
            inventory_path,
            self.data_utils.load_inventory(inventory_path),
            {'rings': 500, 'Chao Egg': 1, 'Garden Fruit': 5}
        )

        embed = discord.Embed(
            title="Welcome to Chao Bot!",
            description=(
                "**Chao Bot** is a fun bot that allows you to hatch, raise, and train your own Chao!\n\n"
                "Below is a quick reference of some helpful commands to get you started. "
                "Have fun raising your Chao!\n\n"
                "**Example Commands**:\n"
                "`$feed [Chao name] [item]` - Feed your Chao.\n"
                "`$race [Chao name]` - Enter your Chao in a race.\n"
                "`$train [Chao name] [stat]` - Train your Chao in a specific stat.\n"
                "`$stats [Chao name]` - View your Chao's stats.\n\n"
                "**You Receive:**\n"
                "- `1x Chao Egg`\n"
                "- `500x Rings`\n"
                "- `5x Garden Nut`\n"
            ),
            color=self.embed_color
        )
        welcome_image_path = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\graphics\misc\welcome_message.png"
        embed.set_image(url="attachment://welcome_message.png")

        await ctx.reply(
            file=discord.File(welcome_image_path, filename="welcome_message.png"),
            embed=embed
        )

    async def initialize_inventory(self, ctx, guild_id, user_id, embed_title, embed_desc):
        """Initialize the user's inventory with default items."""
        if self.data_utils.is_user_initialized(guild_id, user_id):
            return await ctx.reply(f"{ctx.author.mention}, you have already started using the Chao Bot.")

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
        """Give the user 10,000 rings."""
        guild_id, guild_name, user = str(ctx.guild.id), ctx.guild.name, ctx.author
        inventory_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')

        inventory_df = self.data_utils.load_inventory(inventory_path)
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {'rings': 0}

        current_inventory['rings'] = current_inventory.get('rings', 0) + 10000
        self.data_utils.save_inventory(inventory_path, inventory_df, current_inventory)

        await self.send_embed(
            ctx,
            f"{ctx.author.mention} has been given 10,000 rings! Your current rings: {current_inventory['rings']}"
        )
        print(f"[give_rings] 10,000 Rings added to User: {user.id}. New balance: {current_inventory['rings']}")


    async def list_chao(self, ctx):
        """
        Lists all Chao owned by the user in an embed with properly formatted type and alignment.
        """
        guild_id = str(ctx.guild.id)
        user = ctx.author

        # Get Chao data directory from DataUtils
        guild_folder = self.data_utils.update_server_folder(ctx.guild)
        user_folder = self.data_utils.get_user_folder(guild_folder, user)
        chao_dir = os.path.join(user_folder, 'chao_data')

        if not os.path.exists(chao_dir):
            return await ctx.reply(f"{user.mention}, you don't have any Chao yet.")

        # Gather all Chao folders
        chao_list = []
        for folder in os.listdir(chao_dir):
            chao_path = os.path.join(chao_dir, folder)
            if os.path.isdir(chao_path):
                chao_list.append(folder)

        if not chao_list:
            return await ctx.reply(f"{user.mention}, you don't have any Chao yet.")

        # Mapping for type display
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

        # Build the embed
        embed = discord.Embed(
            title=f"{user.display_name}'s Chao",
            description="Here are your Chao:",
            color=discord.Color.blue()
        )

        for chao_name in chao_list:
            chao_stats_path = os.path.join(chao_dir, chao_name, f"{chao_name}_stats.parquet")
            if os.path.exists(chao_stats_path):
                chao_data = self.data_utils.load_chao_stats(chao_stats_path).iloc[-1].to_dict()
                chao_type_raw = chao_data.get("Type", "unknown")
                chao_type = type_mapping.get(chao_type_raw, "Unknown")
                alignment = chao_data.get("Alignment", "Neutral").capitalize()
                embed.add_field(
                    name=chao_name,
                    value=f"Type: {chao_type}\nAlignment: {alignment}",
                    inline=False
                )
            else:
                embed.add_field(name=chao_name, value="No stats available", inline=False)

        embed.set_footer(text=f"Total Chao: {len(chao_list)}")
        await ctx.reply(embed=embed)


    async def grades(self, ctx, chao_name: str):
        """
        Retrieve and display the grades of a specified Chao.
        """
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        # Locate the Chao's stats file
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        # Load Chao stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].to_dict()

        # Extract grades
        grades = {stat: latest_stats.get(f"{stat}_grade", "F") for stat in ["power", "swim", "fly", "run", "stamina"]}

        # Extract Chao thumbnail path
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        # Create an embed to display the grades
        embed = discord.Embed(
            title=f"{chao_name}'s Grades",
            description="Here are the current grades for your Chao:",
            color=discord.Color.blue()
        )

        # Add grades as a list
        grade_list = "\n".join([f"**{stat.capitalize()}**: {grade}" for stat, grade in grades.items()])
        embed.add_field(name="", value=grade_list, inline=False)

        # Add thumbnail if it exists
        if os.path.exists(thumbnail_path):
            file_url = f"attachment://{os.path.basename(thumbnail_path)}"
            embed.set_thumbnail(url=file_url)

        # Add footer
        embed.set_footer(text="Graphics Pending...")

        # Send the embed as a reply
        file = discord.File(thumbnail_path, filename=os.path.basename(thumbnail_path)) if os.path.exists(thumbnail_path) else None
        await ctx.reply(embed=embed, file=file)


    def get_random_grade(self):
        """Select a random grade based on weighted probabilities."""
        grades = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
        probabilities = [4, 20, 25, 25, 20, 5, 1]  # Probabilities for each grade
        return random.choices(grades, probabilities, k=1)[0]

    async def hatch(self, ctx):
        """
        Command to hatch a Chao Egg. Initializes the Chao's stats
        and generates the initial thumbnail for the Chao.
        """
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', '')
        inventory_path = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'user_data', 'inventory.parquet')

        inventory_df = self.data_utils.load_inventory(inventory_path)
        inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {}

        # Check for Chao Egg
        if inventory.get('Chao Egg', 0) < 1:
            return await ctx.reply(f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")

        # Decrement egg
        inventory['Chao Egg'] -= 1
        self.data_utils.save_inventory(inventory_path, inventory_df, inventory)

        # Ensure chao_data folder
        os.makedirs(chao_dir, exist_ok=True)

        # Figure out used names
        used_names = set()
        for folder in os.listdir(chao_dir):
            folder_path = os.path.join(chao_dir, folder)
            if os.path.isdir(folder_path):
                stats_file = os.path.join(folder_path, f"{folder}_stats.parquet")
                if os.path.exists(stats_file):
                    used_names.add(folder)

        # Pick a name from self.chao_names
        available_names = [n for n in self.chao_names if n not in used_names]

        if not available_names:
            return await ctx.reply(
                f"{ctx.author.mention}, all default chao names are used up. "
                f"Please remove an old Chao or extend self.chao_names!"
            )

        chao_name = random.choice(available_names)
        chao_path = os.path.join(chao_dir, chao_name)
        os.makedirs(chao_path, exist_ok=True)

        # Default stats
        chao_stats = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'birth_date': datetime.now().strftime("%Y-%m-%d"),
            'Form': '1',
            'Type': 'neutral_normal_1',
            'hatched': 1,
            'evolved': 0,
            'dead': 0,
            'immortal': 0,
            'reincarnations': 0,
            'eyes': random.choice(self.eye_types),
            'mouth': random.choice(self.mouth_types),
            'dark_hero': 0,
            'belly_ticks': random.randint(3, 10),
            'happiness_ticks': random.randint(3, 10),
            'illness_ticks': 0,
            'energy_ticks': random.randint(3, 10),
            'hp_ticks': 10,
            'swim_exp': 0,
            'swim_grade': self.get_random_grade(),
            'swim_level': 0,
            'swim_fly': 0,
            'fly_exp': 0,
            'fly_grade': self.get_random_grade(),
            'fly_level': 0,
            'fly_ticks': 0,
            'power_exp': 0,
            'power_grade': self.get_random_grade(),
            'power_level': 0,
            'power_ticks': 0,
            'run_exp': 0,
            'run_grade': self.get_random_grade(),
            'run_level': 0,
            'run_power': 0,
            'run_ticks': 0,
            'stamina_exp': 0,
            'stamina_grade': self.get_random_grade(),
            'stamina_level': 0,
            'stamina_ticks': 0
        }

        # Save stats
        chao_stats_path = os.path.join(chao_path, f'{chao_name}_stats.parquet')
        self.data_utils.save_chao_stats(chao_stats_path, pd.DataFrame(), chao_stats)

        # Build face images
        eyes_image_path = os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png") \
            if os.path.exists(os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png")) else \
            os.path.join(self.EYES_DIR, "neutral.png")
        mouth_image_path = os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png") \
            if os.path.exists(os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png")) else \
            os.path.join(self.MOUTH_DIR, "happy.png")
        thumbnail_path = os.path.join(chao_path, f"{chao_name}_thumbnail.png")

        # Combine to create the chao's initial image
        self.image_utils.combine_images_with_face(
            self.BACKGROUND_PATH,
            self.NEUTRAL_PATH,
            eyes_image_path,
            mouth_image_path,
            thumbnail_path
        )

        # Send embed
        embed = discord.Embed(
            title="Your Chao Egg has hatched!",
            description=f"Your Chao Egg hatched into a Chao named **{chao_name}**!\n"
                        f"Use `$rename` if you want to give it your own name.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")  # Use as thumbnail
        await ctx.reply(
            file=discord.File(thumbnail_path, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"),
            embed=embed
        )


    def update_chao_type_and_thumbnail(
        self,
        guild_id: str,
        guild_name: str,
        user: discord.Member,
        chao_name: str,
        latest_stats: Dict
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Updates the Chao type and form based on current stats and evolution rules.
        Generates the updated thumbnail for the Chao.
        """
        try:
            if not self.assets_dir:
                raise ValueError("assets_dir is not set. Ensure cog_load initializes it correctly.")

            chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

            # Current Stats
            stat_levels = {s: latest_stats.get(f"{s}_level", 0) for s in ["power", "swim", "stamina", "fly", "run"]}
            dark_hero = latest_stats.get("dark_hero", 0)
            run_power = latest_stats.get("run_power", 0)
            swim_fly = latest_stats.get("swim_fly", 0)
            current_form = str(latest_stats.get("Form", "1"))
            max_level = max(stat_levels.values())

            # Cap thresholds for dark_hero, run_power, swim_fly
            latest_stats["dark_hero"] = max(min(dark_hero, 5), -5)
            latest_stats["run_power"] = max(min(run_power, 5), -5)
            latest_stats["swim_fly"] = max(min(swim_fly, 5), -5)

            # Determine alignment
            alignment = (
                "hero" if latest_stats["dark_hero"] == 5 else
                "dark" if latest_stats["dark_hero"] == -5 else
                "neutral"
            )
            latest_stats["Alignment"] = alignment

            # Helper function to determine suffix
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

            suffix = determine_suffix(run_power, swim_fly)
            chao_type = latest_stats.get("Type", f"{alignment}_normal_1")  # Default type for Form 1

            # Update type for Form 1 based on alignment
            if current_form == "1":
                chao_type = f"{alignment}_normal_1"

            # Evolution logic for Forms 2, 3, and 4
            if current_form == "1" and max_level >= self.FORM_LEVEL_2:
                suffix = determine_suffix(latest_stats["run_power"], latest_stats["swim_fly"])
                current_form = "2"
                chao_type = f"{alignment}_normal_{suffix}_2"
            elif current_form == "2" and max_level >= self.FORM_LEVEL_3:
                suffix = determine_suffix(latest_stats["run_power"], latest_stats["swim_fly"])
                current_form = "3"
                chao_type = f"{alignment}_{suffix}_3"
            elif current_form == "3" and max_level >= self.FORM_LEVEL_4:
                base_suffix = chao_type.split("_")[1] if chao_type.endswith("_3") else "normal"
                suffix = determine_suffix(latest_stats["run_power"], latest_stats["swim_fly"])
                current_form = "4"
                chao_type = f"{alignment}_{base_suffix}_{suffix}_4"

                # Handle special case for neutral/normal at Form 4
                if suffix == "normal" and base_suffix == "normal":
                    chao_type = f"{alignment}_normal_normal_4"

            # Save final form and type
            latest_stats["Form"] = current_form
            latest_stats["Type"] = chao_type

            # Build sprite paths
            sprite_path = os.path.join(
                self.assets_dir,
                "chao",
                chao_type.split("_")[1],
                alignment,
                f"{chao_type}.png"
            )
            if not os.path.exists(sprite_path):
                sprite_path = os.path.join(self.assets_dir, "chao", "chao_missing.png")

            # Build eyes and mouth paths
            eyes = latest_stats.get("eyes", "neutral")
            mouth = latest_stats.get("mouth", "happy")
            eyes_alignment = "neutral" if current_form in ["1", "2"] else alignment

            eyes_image_path = os.path.join(self.EYES_DIR, f"{eyes_alignment}_{eyes}.png")
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(self.EYES_DIR, "neutral.png")

            mouth_image_path = os.path.join(self.MOUTH_DIR, f"{mouth}.png")
            if not os.path.exists(mouth_image_path):
                mouth_image_path = os.path.join(self.MOUTH_DIR, "happy.png")

            # Choose background
            if current_form in ["3", "4"]:
                bg_path = (
                    self.HERO_BG_PATH if alignment == "hero" else
                    self.DARK_BG_PATH if alignment == "dark" else
                    self.NEUTRAL_BG_PATH
                )
            else:
                bg_path = self.BACKGROUND_PATH

            # Generate thumbnail
            self.image_utils.combine_images_with_face(
                bg_path,
                sprite_path,
                eyes_image_path,
                mouth_image_path,
                thumbnail_path
            )

            return chao_type, current_form

        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] An error occurred: {e}")
            return "normal", "1"


    # Additional helper methods
    def _strip_form_digit(self, chao_type: str) -> str:
        segments = chao_type.rsplit("_", 1)
        if len(segments) == 2 and segments[1] in {"1","2","3","4"}:
            return segments[0]
        return chao_type

    def _ensure_form4_double_type(self, chao_type: str) -> str:
        parts = chao_type.split("_")
        if len(parts) == 3 and parts[-1] == "4":
            parts.insert(2, parts[1])
        return "_".join(parts)

    def _extract_base_for_subfolder(self, chao_type: str, alignment: str) -> str:
        prefix = f"{alignment}_"
        if chao_type.startswith(prefix):
            chao_type = chao_type[len(prefix):]
        segs = chao_type.rsplit("_", 1)
        if len(segs) == 2 and segs[1] in {"1","2","3","4"}:
            chao_type = segs[0]
        return chao_type.split("_", 1)[0] if "_" in chao_type else chao_type or "normal"

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


    async def goodbye(self, ctx, *, chao_name: str = None):
        if chao_name is None:
            # If no Chao name is specified, provide an explanation of the command
            embed = discord.Embed(
                title="Goodbye Command",
                description=(
                    "The `$goodbye` command allows you to send one of your Chao to live happily "
                    "in a faraway forest. 🌳\n\n"
                    "**Usage:**\n"
                    "`$goodbye Chaoko`\n\n"
                    "If you use this command, the specified Chao will be removed from your ownership, "
                    "and their data will be stored safely in the Chao Forest. However, you might never see that Chao again."
                ),
                color=discord.Color.blue(),
            )

            # Add the thumbnail
            goodbye_thumbnail_path = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\graphics\thumbnails\goodbye_background.png"
            embed.set_thumbnail(url=f"attachment://goodbye_background.png")

            with open(goodbye_thumbnail_path, 'rb') as file:
                thumbnail = discord.File(file, filename="goodbye_background.png")
                await ctx.reply(embed=embed, file=thumbnail)
            return

        # Proceed with Chao removal if a Chao name is provided
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        # Confirm Chao existence
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)

        if not os.path.exists(chao_dir):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        # Prepare the Chao Forest directory
        server_db_folder = self.data_utils.get_server_folder(guild_id, guild_name)
        chao_forest_dir = os.path.join(server_db_folder, "Chao Forest")
        os.makedirs(chao_forest_dir, exist_ok=True)

        # Determine the new name for the Chao in the Chao Forest
        existing_chao_folders = [d for d in os.listdir(chao_forest_dir) if os.path.isdir(os.path.join(chao_forest_dir, d))]
        lost_chao_count = sum(1 for name in existing_chao_folders if name.startswith("Lost Chao"))
        new_chao_name = f"Lost Chao {lost_chao_count + 1}"

        # Move the Chao's data folder to the Chao Forest with the new name
        target_dir = os.path.join(chao_forest_dir, new_chao_name)
        try:
            shutil.move(chao_dir, target_dir)
        except Exception as e:
            return await self.send_embed(ctx, f"{ctx.author.mention}, failed to move **{chao_name}** to the Chao Forest. Error: {str(e)}")

        # Thumbnail for the goodbye message
        goodbye_thumbnail_path = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\graphics\thumbnails\goodbye_background.png"

        # Confirm success with an embed
        embed = discord.Embed(
            title=f"Goodbye, {chao_name}!",
            description=(
                f"{chao_name} has been sent to live happily in a faraway forest. 🌲\n\n"
                f"They will surely live a happy life."
            ),
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=f"attachment://goodbye_background.png")

        with open(goodbye_thumbnail_path, 'rb') as file:
            thumbnail = discord.File(file, filename="goodbye_background.png")
            await ctx.reply(embed=embed, file=thumbnail)


    async def feed(self, ctx, *, chao_name_and_fruit: str):
        """
        Feed a particular fruit to a Chao, applying its effects and updating stats.
        """
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author

        # Parsing Chao name and fruit
        matched_fruit = None
        chao_name = None

        # Match fruit dynamically
        for fruit in self.fruits:
            if chao_name_and_fruit.lower().endswith(f" {fruit.lower()}"):
                matched_fruit = fruit
                chao_name = chao_name_and_fruit[: -(len(fruit) + 1)].strip()
                break

        if not chao_name or not matched_fruit:
            return await self.send_embed(
                ctx,
                f"{ctx.author.mention}, provide a valid Chao name and fruit.\n"
                f"Valid fruits: {', '.join(self.fruits)}"
            )

        # Confirm Chao existence
        chao_dir = self.data_utils.get_path(guild_id, guild_name, user, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_dir):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, stats file is missing for **{chao_name}**.")

        # Confirm user has fruit
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}

        normalized_inventory = {k.lower(): v for k, v in current_inv.items()}
        if normalized_inventory.get(matched_fruit.lower(), 0) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you have no **{matched_fruit}**.")

        # Load Chao stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].to_dict()

        # Update hp_ticks and belly_ticks
        max_ticks = 9
        latest_stats['hp_ticks'] = min(latest_stats.get('hp_ticks', 0) + 1, max_ticks)
        latest_stats['belly_ticks'] = min(latest_stats.get('belly_ticks', 0) + 1, 10)  # Cap at 10

        # Update belly and date
        days_elapsed = (datetime.now() - datetime.strptime(latest_stats.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")).days
        latest_stats['belly'] = max(0, latest_stats.get('belly', 0) - days_elapsed)
        latest_stats['belly'] = min(10, latest_stats['belly'] + 2)
        latest_stats['date'] = datetime.now().strftime("%Y-%m-%d")

        # Apply fruit effects
        if matched_fruit.lower() == "strange mushroom":
            # Randomize the ticks for power, run, swim, fly, and stamina
            for stat in ['power_ticks', 'run_ticks', 'swim_ticks', 'fly_ticks', 'stamina_ticks']:
                latest_stats[stat] = random.randint(0, max_ticks)
        else:
            adjustments = self.fruit_stats_adjustments.get(matched_fruit.lower(), {})
            for stat, adjustment in adjustments.items():
                increment = random.randint(*adjustment) if isinstance(adjustment, tuple) else adjustment

                if stat in ["run_power", "swim_fly"]:
                    latest_stats[stat] = max(-5, min(5, latest_stats.get(stat, 0) + increment))
                    opposing_stat = "swim_fly" if stat == "run_power" else "run_power"
                    if latest_stats[opposing_stat] > 0:
                        latest_stats[opposing_stat] -= 1
                    elif latest_stats[opposing_stat] < 0:
                        latest_stats[opposing_stat] += 1

                    if latest_stats["Form"] == "2":
                        if latest_stats["run_power"] == 5:
                            latest_stats["Type"] = "neutral_normal_power_2"
                        elif latest_stats["run_power"] == -5:
                            latest_stats["Type"] = "neutral_normal_run_2"
                        elif latest_stats["swim_fly"] == 5:
                            latest_stats["Type"] = "neutral_normal_fly_2"
                        elif latest_stats["swim_fly"] == -5:
                            latest_stats["Type"] = "neutral_normal_swim_2"
                elif stat.endswith("_ticks"):
                    # Ensure energy_ticks and belly_ticks do not reset at 10
                    if stat in ["energy_ticks", "belly_ticks", "happiness_ticks", "illness_ticks", "hp_ticks"]:
                        latest_stats[stat] = min(latest_stats.get(stat, 0) + increment, 10)
                    else:  # For stats that reset
                        current_value = latest_stats.get(stat, 0)
                        new_value = current_value + increment
                        if new_value >= 10:
                            latest_stats[stat] = new_value - 10
                            level_key = stat.replace("_ticks", "_level")
                            grade_key = stat.replace("_ticks", "_grade")
                            exp_key = stat.replace("_ticks", "_exp")

                            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
                            grade = latest_stats.get(grade_key, 'F')
                            latest_stats[exp_key] = latest_stats.get(exp_key, 0) + self.get_stat_increment(grade)
                        else:
                            latest_stats[stat] = new_value
                else:
                    latest_stats[stat] = latest_stats.get(stat, 0) + increment

        # Deduct fruit
        normalized_inventory[matched_fruit.lower()] -= 1
        updated_inventory = {k: normalized_inventory[k.lower()] for k in current_inv.keys()}
        self.data_utils.save_inventory(inv_path, inv_df, updated_inventory)

        # Save updated stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # Possibly evolve and update thumbnail
        chao_type, form = self.update_chao_type_and_thumbnail(
            guild_id, guild_name, user, chao_name, latest_stats
        )
        latest_stats["Form"] = form
        latest_stats["Type"] = chao_type
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # Ensure thumbnail file matches the expected format
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        if not os.path.exists(thumbnail_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, thumbnail file is missing for **{chao_name}**.")

        # Use a fixed filename for the attachment
        attachment_filename = "chao_thumbnail.png"

        # Build embed
        description = f"{chao_name} ate a {matched_fruit}!\n\n"
        embed = discord.Embed(title="Chao Feed Success", description=description, color=self.embed_color)
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")

        # Send the embed with the attached file
        with open(thumbnail_path, 'rb') as file:
            thumbnail = discord.File(file, filename=attachment_filename)
            await ctx.reply(embed=embed, file=thumbnail)



    async def stats(self, ctx, *, chao_name: str):
        """
        Command to display the stats of a specific Chao.
        Generates Page 1 & 2 stat cards and sends them.
        """
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()

        chao_type, form = self.update_chao_type_and_thumbnail(
            guild_id, ctx.guild.name, ctx.author, chao_name, chao_stats
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

        # Create StatsView
        view = StatsView.from_data(
            {
                "chao_name": chao_name,
                "guild_id": guild_id,
                "user_id": user_id,
                "chao_type_display": chao_type_display,
                "alignment_label": alignment_label,
                "total_pages": 2,
                "current_page": 1
            },
            self
        )

        self.save_persistent_view({
            "chao_name": chao_name,
            "guild_id": guild_id,
            "user_id": user_id,
            "chao_type_display": chao_type_display,
            "alignment_label": alignment_label,
            "total_pages": 2,
            "current_page": 1
        })

        await ctx.reply(
            files=[
                discord.File(stats_image_paths[1], "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(thumbnail_path, filename="chao_thumbnail.png"),
            ],
            embed=embed,
            view=view
        )

    async def pet(self, ctx, chao_name: str):
        """
        Handles the logic for the pet command, increasing a Chao's happiness and updating its display.
        """
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Locate Chao stats
        chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f"{chao_name}_stats.parquet")

        if not os.path.exists(chao_stats_path):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{chao_name}** exists.")

        # Load Chao stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        latest_stats = chao_df.iloc[-1].to_dict()

        # Increase happiness
        latest_stats['happiness_ticks'] = min(latest_stats.get('happiness_ticks', 0) + 1, 10)

        # Get Chao type and form
        chao_type = latest_stats.get("Type", "neutral_normal_1")
        chao_form = latest_stats.get("Form", "1")
        chao_alignment = latest_stats.get("Alignment", "neutral")

        # Determine the background path based on form and alignment
        if chao_form in ["3", "4"]:  # Form 3 or greater uses alignment-based backgrounds
            background_path = (
                self.HERO_BG_PATH if chao_alignment == "hero" else
                self.DARK_BG_PATH if chao_alignment == "dark" else
                self.NEUTRAL_BG_PATH
            )
        else:  # Forms 1 and 2 use a neutral background
            background_path = os.path.join(self.assets_dir, "graphics/thumbnails/neutral_background.png")

        # Get Chao image path
        chao_image_path = os.path.join(
            self.assets_dir,
            "chao",
            chao_type.split("_")[1],  # Base type folder (e.g., fly, normal, power, etc.)
            chao_type.split("_")[0],  # Alignment folder (e.g., hero, dark, neutral)
            f"{chao_type}.png"
        )

        if not os.path.exists(chao_image_path):
            chao_image_path = os.path.join(self.assets_dir, "chao", "chao_missing.png")  # Fallback

        # Save updated stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # Ensure the happy thumbnail path
        happy_thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail_happy.png")

        # Generate the happy thumbnail using combine_images_with_face
        self.image_utils.combine_images_with_face(
            background_path=background_path,  # Background determined by form and alignment
            chao_image_path=chao_image_path,
            eyes_image_path=os.path.join(self.EYES_DIR, "neutral_happy.png"),
            mouth_image_path=os.path.join(self.MOUTH_DIR, "happy.png"),
            output_path=happy_thumbnail_path
        )

        # Use a fixed filename for the attachment
        attachment_filename = "happy_thumbnail.png"

        # Create embed with the fixed filename
        embed = discord.Embed(
            title=f"You pet {chao_name}!",
            description=f"{chao_name} looks so happy! \nHappiness increased by 10%.",
            color=self.embed_color
        )
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")

        # Send the embed with the updated thumbnail
        with open(happy_thumbnail_path, 'rb') as file:
            thumbnail = discord.File(file, filename=attachment_filename)
            await ctx.reply(embed=embed, file=thumbnail)



    async def rename(self, ctx, *, chao_name_and_new_name: str):
        guild_id = str(ctx.guild.id)

        # Split the input into current_name and new_name
        parts = chao_name_and_new_name.split()
        if len(parts) < 2:
            return await ctx.reply(
                f"{ctx.author.mention}, please provide both the current Chao name and the new name.\n"
                f"Usage: `$rename <current_name> <new_name>`"
            )
        # Assume the first part(s) is the current name and the last part(s) is the new name
        current_name = ' '.join(parts[:-2]) if len(parts) > 2 else parts[0]
        new_name = ' '.join(parts[-2:]) if len(parts) > 2 else parts[1]

        # Validate the new name
        if len(new_name) > 15:
            return await ctx.reply(f"{ctx.author.mention}, the new name **{new_name}** exceeds the 15-character limit.")
        if not (new_name.isalnum() or (' ' in new_name and len(new_name.split()) == 2 and all(part.isalpha() for part in new_name.split()))):
            return await ctx.reply(
                f"{ctx.author.mention}, the new name **{new_name}** must be either a single name with no spaces "
                "or two words separated by one space. Example: `Chaozilla` or `Count Chaocula`."
            )

        # Paths for Chao data
        chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', current_name)
        new_chao_dir = self.data_utils.get_path(guild_id, ctx.guild.name, ctx.author, 'chao_data', new_name)

        if not os.path.exists(chao_dir):
            return await ctx.reply(f"{ctx.author.mention}, no Chao named **{current_name}** exists.")

        if os.path.exists(new_chao_dir):
            return await ctx.reply(f"{ctx.author.mention}, a Chao named **{new_name}** already exists.")

        # Rename the Chao directory
        os.rename(chao_dir, new_chao_dir)

        # Update stats file
        stats_file = os.path.join(new_chao_dir, f"{current_name}_stats.parquet")
        new_stats_file = os.path.join(new_chao_dir, f"{new_name}_stats.parquet")
        if os.path.exists(stats_file):
            os.rename(stats_file, new_stats_file)

        # Rename all relevant image files in the Chao directory
        for filename in os.listdir(new_chao_dir):
            if current_name in filename:
                old_file_path = os.path.join(new_chao_dir, filename)
                new_file_path = old_file_path.replace(current_name, new_name)
                os.rename(old_file_path, new_file_path)

        # Confirmation message
        await ctx.reply(
            f"{ctx.author.mention}, your Chao has been successfully renamed from **{current_name}** to **{new_name}**!"
        )



    async def egg(self, ctx):
        """Give the user a Chao Egg (if they don't already have one)."""
        p, i, d = self.data_utils.get_path, self.data_utils.load_inventory, self.data_utils.save_inventory
        u, g = str(ctx.author.id), str(ctx.guild.id)
        c, e = ctx.reply, discord.Embed(
            title="Obtained Chao Egg!",
            description="**You received a Chao Egg.**\nUse `$hatch` to hatch the Chao egg and see your new Chao!",
            color=self.embed_color
        )
        f = lambda x: x.iloc[-1].to_dict() if not x.empty else {}

        # Paths to inventory and egg background
        v = p(g, ctx.guild.name, ctx.author, 'user_data', 'inventory.parquet')
        egg_background_path = os.path.join(
            self.assets_dir,
            "graphics/thumbnails/egg_background.png"
        )

        # Load and update inventory
        h = i(v)
        s = f(h)
        k = 'Chao Egg'
        if s.get(k, 0) >= 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg!")

        s[k] = s.get(k, 0) + 1
        d(v, h, s)

        # Attach the egg background if it exists
        if os.path.exists(egg_background_path):
            await c(
                file=discord.File(egg_background_path, "egg_background.png"),
                embed=e.set_thumbnail(url="attachment://egg_background.png")
            )
        else:
            await c(embed=e)



    async def inventory(self, ctx):
        """Show the user their current inventory."""
        get_path = self.data_utils.get_path
        load_inventory = self.data_utils.load_inventory

        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        user = ctx.author
        current_date_str = datetime.now().strftime("%Y-%m-%d")

        inventory_path = get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inventory_df = load_inventory(inventory_path)

        if not inventory_df.empty and current_date_str in inventory_df['date'].values:
            current_inventory = inventory_df[inventory_df['date'] == current_date_str].iloc[-1].to_dict()
        else:
            current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {'Rings': 0}

        # Ensure 'Rings' key is capitalized
        if 'rings' in current_inventory:
            current_inventory['Rings'] = current_inventory.pop('rings')

        embed = discord.Embed(
            title="Your Inventory",
            description="Here's what you have today:",
            color=self.embed_color
        )

        for item, amount in current_inventory.items():
            if item == 'date':
                continue
            if amount > 0:
                # Display integer amounts with no decimals
                embed.add_field(
                    name=item,
                    value=f"x {int(amount)}",
                    inline=True
                )

        # Add footer
        embed.set_footer(text="Graphics Pending...")

        await ctx.reply(embed=embed)


    def calculate_exp_gain(self, grade: str) -> int:
        return {
            'F': 1, 'E': 2, 'D': 3, 'C': 4, 'B': 5, 'A': 6, 'S': 7, 'X': 8
        }.get(grade.upper(), 3)


class StatsView(View):
    """Two-page stats display with next/prev buttons."""

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

        # Load and validate the initial page state
        self.current_page = self.load_state(default_page=current_page)
        self.save_state()  # Ensure the state is immediately persisted

        # Add navigation buttons
        self.add_navigation_buttons()

    def save_state(self):
        """Save the current page to the persistent views file."""
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
        """Load the saved current page from the persistent views file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                try:
                    data = json.load(f)
                    key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
                    page = data.get(key, {}).get("current_page", default_page)
                    return max(1, min(page, self.total_pages))
                except json.JSONDecodeError:
                    pass  # Return default if JSON is corrupted
        return default_page

    def add_navigation_buttons(self):
        """Add navigation buttons to the view."""
        self.clear_items()
        self.add_item(self.create_button("⬅️", "previous_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_prev"))
        self.add_item(self.create_button("➡️", "next_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_next"))

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to the previous page."""
        self.current_page = self.total_pages if self.current_page == 1 else self.current_page - 1
        self.save_state()
        await self.update_stats(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Navigate to the next page."""
        self.current_page = 1 if self.current_page == self.total_pages else self.current_page + 1
        self.save_state()
        await self.update_stats(interaction)

    async def update_stats(self, interaction: discord.Interaction):
        """Update the stats display based on the current page."""
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
        page_image_filename = f'{self.chao_name}_stats_page_{self.current_page}.png'
        image_path = os.path.join(chao_dir, page_image_filename)

        if self.current_page == 1:
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

        embed = (
            discord.Embed(color=discord.Color.blue())
            .set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
            .add_field(name="Type", value=self.chao_type_display, inline=True)
            .add_field(name="Alignment", value=self.alignment_label, inline=True)
            .set_thumbnail(url="attachment://chao_thumbnail.png")
            .set_image(url="attachment://stats_page.png")
            .set_footer(text=f"Page {self.current_page} / {self.total_pages}")
        )

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
        """Recreate a StatsView from stored data."""
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
