# cogs/chao.py
import os, json, random, asyncio, discord, shutil, pandas as pd
from discord.ext import commands, tasks
from discord.ui import View, Button
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Optional


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

        # Eye and mouth variations
        self.eye_types = ['normal', 'happy', 'angry', 'tired']
        self.mouth_types = ['happy', 'unhappy', 'grumble', 'evil', 'none']

        # Example chao names
        self.chao_names = [
            "Chaoko", "Chaowser", "Chaorunner", "Chaozart", "Chaobacca", "Chaowder",
            "Chaocolate", "Chaolesterol", "Chao Mein", "Chaoster", "Chaomanji", "Chaosmic",
            "Chaozilla", "Chaoseidon", "Chaosferatu", "Chaolin", "Chow", "Chaotzhu",
            "Chaoblin", "Count Chaocula", "Chaozil", "Chaoz", "Chaokie Chan", "Chaobama", "Chaombie", 
            "Xin Chao", "Ka Chao", "Chow Wow", "Ciao" "Chaomin Ultra"
        ]

        # Thresholds for run_power / swim_fly
        self.RUN_POWER_THRESHOLD = c.get("RUN_POWER_THRESHOLD", 5)
        self.SWIM_FLY_THRESHOLD = c.get("SWIM_FLY_THRESHOLD", 5)


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




    def send_embed(self, ctx, description: str, title: str = "Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.reply(embed=embed)


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
            {'rings': 500, 'Chao Egg': 1, 'Garden Nut': 5}
        )

        embed = discord.Embed(
            title="Welcome to Chao Bot!",
            description=(
                "**Chao Bot** is a W.I.P. bot that allows you to hatch, raise, and train your own Chao!\n\n"
                "Below is a quick reference of some helpful commands to get you started. "
                "Have fun raising your Chao!\n\n"
                "**$help** - View a full list of commands.\n"
                "**$market** - Access the Black Market.\n"
                "**$feed** - Feed a fruit to your Chao.\n"
                "**$egg** - Receive a new Chao egg. Only 1 at a time.\n"
                "**$hatch** - Hatch a new Chao egg.\n\n"
                "**You Receive:**\n"
                "- `1x Chao Egg`\n"
                "- `500x Rings`\n"
                "- `5x Garden Nut`\n"
            ),
            color=self.embed_color
        )

        # Use egg_background.png as the thumbnail
        egg_thumbnail_path = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\graphics\thumbnails\egg_background.png"
        embed.set_thumbnail(url="attachment://egg_background.png")

        # Add welcome_message.png at the bottom
        welcome_image_path = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\graphics\misc\welcome_message.png"
        embed.set_image(url="attachment://welcome_message.png")
        await ctx.reply(
            files=[
                discord.File(egg_thumbnail_path, filename="egg_background.png"),
                discord.File(welcome_image_path, filename="welcome_message.png")
            ],
            embed=embed
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

        embed.set_footer(text=f"Total Chao: {len(chao_list)} | Graphics Pending...")
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
            # Replace spaces with underscores in the filename
            safe_filename = os.path.basename(thumbnail_path).replace(" ", "_")
            embed.set_thumbnail(url=f"attachment://{safe_filename}")
            file = discord.File(thumbnail_path, filename=safe_filename)
        else:
            file = None

        # Add footer
        embed.set_footer(text="Graphics Pending...")

        # Send the embed as a reply
        await ctx.reply(embed=embed, file=file if file else None)


    def get_random_grade(self):
        """Select a random grade based on weighted probabilities."""
        grades = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
        probabilities = [4, 20, 25, 35, 10, 5, 1]  # Probabilities for each grade
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
                    "in a faraway forest. 🌲\n\n"
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


    async def throw_chao(self, ctx, chao_name: str):
        """
        Throw a Chao, doing the opposite of 'pet':
        - Decreases happiness (down to a minimum of 0).
        - Decreases HP (down to a minimum of 0).
        - Shows the Chao with a "grumble" mouth and "pain" (or "angry") eyes.
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

        # Decrease happiness by 1 (min 0)
        old_happiness = latest_stats.get('happiness_ticks', 0)
        new_happiness = max(0, old_happiness - 1)
        latest_stats['happiness_ticks'] = new_happiness

        # Decrease HP by 1 (min 0)
        old_hp = latest_stats.get('hp_ticks', 0)
        new_hp = max(0, old_hp - 1)
        latest_stats['hp_ticks'] = new_hp

        # Get Chao type and form
        chao_type = latest_stats.get("Type", "neutral_normal_1")
        chao_form = latest_stats.get("Form", "1")
        chao_alignment = latest_stats.get("Alignment", "neutral")

        # Determine the background path based on form and alignment
        if chao_form in ["3", "4"]:
            background_path = (
                self.HERO_BG_PATH if chao_alignment == "hero" else
                self.DARK_BG_PATH if chao_alignment == "dark" else
                self.NEUTRAL_BG_PATH
            )
        else:
            background_path = os.path.join(self.assets_dir, "graphics/thumbnails/neutral_background.png")

        # Get Chao image path
        chao_image_path = os.path.join(
            self.assets_dir,
            "chao",
            chao_type.split("_")[1],  # e.g. 'fly', 'normal', 'power', etc.
            chao_type.split("_")[0],  # e.g. 'hero', 'dark', 'neutral'
            f"{chao_type}.png"
        )

        if not os.path.exists(chao_image_path):
            chao_image_path = os.path.join(self.assets_dir, "chao", "chao_missing.png")  # fallback

        # Save updated stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats)

        # Ensure the "unhappy" thumbnail path
        throw_thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail_throw.png")

        # Face images for "throw" scenario:
        #   eyes = "pain.png" if it exists, else "angry.png"
        #   mouth = "grumble.png"
        eyes_path = os.path.join(self.EYES_DIR, "neutral_pain.png")
        if not os.path.exists(eyes_path):
            # fallback to "angry"
            eyes_path = os.path.join(self.EYES_DIR, "neutral_angry.png")
            if not os.path.exists(eyes_path):
                # fallback to default neutral
                eyes_path = os.path.join(self.EYES_DIR, "neutral.png")

        mouth_path = os.path.join(self.MOUTH_DIR, "grumble.png")
        if not os.path.exists(mouth_path):
            # fallback to "unhappy"
            mouth_path = os.path.join(self.MOUTH_DIR, "unhappy.png")

        # Generate the "throw" thumbnail
        self.image_utils.combine_images_with_face(
            background_path=background_path,
            chao_image_path=chao_image_path,
            eyes_image_path=eyes_path,
            mouth_image_path=mouth_path,
            output_path=throw_thumbnail_path
        )

        # Send embed
        attachment_filename = "throw_thumbnail.png"
        embed = discord.Embed(
            title=f"You threw {chao_name}!",
            description=(
                f"{chao_name} looks hurt! \n"
                f"Happiness decreased by 1 (now {new_happiness}).\n"
                f"HP decreased by 1 (now {new_hp})."
            ),
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=f"attachment://{attachment_filename}")

        with open(throw_thumbnail_path, 'rb') as file:
            thumbnail = discord.File(file, filename=attachment_filename)
            await ctx.reply(embed=embed, file=thumbnail)


    async def rename(self, ctx, *, chao_name_and_new_name: str = None):
        """
        Rename a Chao.  
        
        - Allows: 
            - 1-word → multi-word, e.g. $rename Chaoz Count Chaocula
            - multi-word → 1-word, e.g. $rename Count Chaocula Chaoz
          by guessing which tokens form the old name vs. the new name.
          
        - Called externally like:
            await self.chao_cog.rename(ctx, chao_name_and_new_name="Chaoz Count Chaocula")
        """

        # --- 1) Basic usage check ---
        if not chao_name_and_new_name:
            embed = discord.Embed(
                title="Rename Command",
                description=(
                    "Usage:\n"
                    "`$rename <old_name> <new_name>`\n\n"
                    "Examples:\n"
                    "`$rename Chaoz Count Chaocula`\n"
                    "  → Renames 'Chaoz' to 'Count Chaocula'\n\n"
                    "`$rename Count Chaocula Chaoz`\n"
                    "  → Renames 'Count Chaocula' to 'Chaoz'\n\n"
                    "If your old name or new name has spaces and the bot guesses incorrectly, "
                    "use quotes:\n"
                    "`$rename \"Chaoz Count\" \"Chaocula Prime\"`"
                ),
                color=discord.Color.blue(),
            )
            return await ctx.reply(embed=embed)

        # Split the user-provided string into tokens
        # e.g. "Chaoz Count Chaocula" -> ["Chaoz", "Count", "Chaocula"]
        args = chao_name_and_new_name.split()

        # We need at least 2 tokens to form an old name + new name
        if len(args) < 2:
            return await ctx.reply(
                f"{ctx.author.mention}, please provide both the old Chao name and the new name.\n"
                "Usage: `$rename <old_name> <new_name>`"
            )

        # --- 2) Attempt #1: old=first token, new=rest ---
        attempt1_old = args[0]                   # e.g. "Chaoz"
        attempt1_new = " ".join(args[1:])        # e.g. "Count Chaocula"

        # Path for attempt #1
        user_folder = self.data_utils.get_user_folder(
            self.data_utils.update_server_folder(ctx.guild), ctx.author
        )
        attempt1_old_path = os.path.join(user_folder, "chao_data", attempt1_old)

        if os.path.exists(attempt1_old_path):
            # If that folder exists, we assume attempt #1 is correct
            old_name = attempt1_old
            new_name = attempt1_new
        else:
            # --- 3) Attempt #2: old=all but last, new=last token ---
            # e.g. ["Count", "Chaocula", "Chaoz"] => old="Count Chaocula", new="Chaoz"
            attempt2_old = " ".join(args[:-1])
            attempt2_new = args[-1]
            attempt2_old_path = os.path.join(user_folder, "chao_data", attempt2_old)

            if os.path.exists(attempt2_old_path):
                old_name = attempt2_old
                new_name = attempt2_new
            else:
                # Both guesses failed
                return await ctx.reply(
                    f"{ctx.author.mention}, I couldn't find a Chao folder matching "
                    f"**{attempt1_old}** or **{attempt2_old}**.\n"
                    "Please check your spelling or use quotes if the old name has spaces."
                )

        # --- 4) Now we have old_name and new_name properly determined ---

        # Validate new_name length
        if len(new_name) > 15:
            return await ctx.reply(
                f"{ctx.author.mention}, the new name **{new_name}** exceeds the 15-character limit."
            )

        # Validate characters (letters, numbers, spaces)
        if not new_name.replace(" ", "").isalnum():
            return await ctx.reply(
                f"{ctx.author.mention}, the new name **{new_name}** must be letters/numbers only, "
                "with spaces allowed."
            )

        # Build final paths
        old_path = os.path.join(user_folder, "chao_data", old_name)
        new_path = os.path.join(user_folder, "chao_data", new_name)

        # Check if the new folder name already exists
        if os.path.exists(new_path):
            return await ctx.reply(
                f"{ctx.author.mention}, a Chao named **{new_name}** already exists!"
            )

        # Rename the main chao_data directory
        os.rename(old_path, new_path)

        # Rename stats file (e.g. "Chaoz_stats.parquet" → "Count Chaocula_stats.parquet")
        old_stats = os.path.join(new_path, f"{old_name}_stats.parquet")
        new_stats = os.path.join(new_path, f"{new_name}_stats.parquet")
        if os.path.exists(old_stats):
            os.rename(old_stats, new_stats)

        # Rename any other files containing the old name
        for filename in os.listdir(new_path):
            if old_name in filename:
                old_file_path = os.path.join(new_path, filename)
                new_file_path = os.path.join(
                    new_path, filename.replace(old_name, new_name)
                )
                os.rename(old_file_path, new_file_path)

        # Confirmation
        await ctx.reply(
            f"{ctx.author.mention}, your Chao has been successfully renamed from "
            f"**{old_name}** to **{new_name}**!"
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
                    value=f"Quantity: {int(amount)}",
                    inline=True
                )

        # Add footer
        embed.set_footer(text="Graphics Pending...")

        await ctx.reply(embed=embed)


    def calculate_exp_gain(self, grade: str) -> int:
        return {
            'F': 1, 'E': 2, 'D': 3, 'C': 4, 'B': 5, 'A': 6, 'S': 7, 'X': 8
        }.get(grade.upper(), 3)


async def setup(bot):
    await bot.add_cog(Chao(bot))
