import os
import json
import discord
from discord.ext import commands
from discord.ui import View
from datetime import datetime
import random

class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        self.image_utils = self.data_utils = None

        # Load configuration from JSON file
        with open('config.json', 'r') as f:
            config = json.load(f)

        self.FORM_LEVELS = config['FORM_LEVELS']
        self.ALIGNMENTS = config['ALIGNMENTS']
        self.FRUIT_TICKS_RANGE = config['FRUIT_TICKS_RANGE']
        self.FRUIT_STATS = config['FRUIT_STATS']

        # Initialize variables that depend on the constants
        self.FORM_LEVEL_2 = self.FORM_LEVELS[0]
        self.FORM_LEVEL_3 = self.FORM_LEVELS[1]
        self.FORM_LEVEL_4 = self.FORM_LEVELS[2]
        self.HERO_ALIGNMENT = self.ALIGNMENTS['hero']
        self.DARK_ALIGNMENT = self.ALIGNMENTS['dark']
        self.FRUIT_TICKS_MIN = self.FRUIT_TICKS_RANGE[0]
        self.FRUIT_TICKS_MAX = self.FRUIT_TICKS_RANGE[1]

        # Other constants
        self.GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.GRADE_TO_VALUE = dict(zip(self.GRADES, range(-1, 7)))
        self.CUSTOM_EMOJI_ID = 1176313914464681984
        self.eye_types = ['normal', 'happy', 'angry', 'sad', 'sleep', 'tired', 'pain']
        self.mouth_types = ['happy', 'unhappy', 'mean', 'grumble', 'evil']
        self.chao_names = [
            "Chaoko", "Chaowser", "Chaorunner", "Chaozart", "Chaobacca", "Chaowder",
            "Chaocolate", "Chaolesterol", "Chao Mein", "Chaoster", "Chaomanji", "Chaosmic",
            "Chaozilla", "Chaoseidon", "Chaosferatu", "Chaolin", "Chow", "Chaotzhu",
            "Chaoblin", "Count Chaocula", "Chaozil", "Chaoz"
        ]

        # Thresholds
        self.RUN_POWER_THRESHOLD = 5
        self.SWIM_FLY_THRESHOLD = 5

        # Initialize variables that will be set in cog_load
        self.assets_dir = None
        self.TEMPLATE_PATH = None
        self.TEMPLATE_PAGE_2_PATH = None
        self.OVERLAY_PATH = None
        self.ICON_PATH = None
        self.NEUTRAL_PATH = None
        self.BACKGROUND_PATH = None
        self.TICK_POSITIONS = None
        self.EYES_DIR = None
        self.MOUTH_DIR = None
        self.fruits = None
        self.fruit_prices = 15  # Assuming this remains constant

    def cog_load(self):
        self.image_utils = self.bot.get_cog('ImageUtils')
        self.data_utils = self.bot.get_cog('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("ImageUtils or DataUtils cog not loaded.")

        self.assets_dir = self.image_utils.assets_dir
        self.TEMPLATE_PATH = os.path.join(self.assets_dir, 'graphics/cards/stats_page_1.png')
        self.TEMPLATE_PAGE_2_PATH = os.path.join(self.assets_dir, 'graphics/cards/stats_page_2.png')
        self.OVERLAY_PATH = os.path.join(self.assets_dir, 'graphics/ticks/tick_filled.png')
        self.ICON_PATH = os.path.join(self.assets_dir, 'graphics/icons/Stats.png')
        self.NEUTRAL_PATH = os.path.join(self.assets_dir, 'chao/normal/neutral/neutral_normal_1.png')
        self.BACKGROUND_PATH = os.path.join(self.assets_dir, 'graphics/thumbnails/neutral_background.png')
        # Adjusted TICK_POSITIONS to remove the "mind" stat
        self.TICK_POSITIONS = [(446, y) for y in [1176, 315, 591, 883, 1469]]
        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')
        emojis = "🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍"
        names = [
            "Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit",
            "Heart Fruit", "Square Fruit", "Chao Fruit", "Power Fruit",
            "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"
        ]
        self.fruits = [{"emoji": e, "name": n} for e, n in zip(emojis, names)]
        self.fruit_prices = 15

    def calculate_exp_gain(self, grade):
        return self.GRADE_TO_VALUE[grade] * 3 + 13

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

    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)

    async def hatch(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inventory_df = self.data_utils.load_inventory(inventory_path)
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {}
        chao_egg_qty = int(current_inventory.get('Chao Egg', 0))
        if chao_egg_qty < 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', '')
        chao_name = random.choice(self.chao_names)
        os.makedirs(chao_dir, exist_ok=True)
        while chao_name in os.listdir(chao_dir):
            chao_name = random.choice(self.chao_names)
        chao_stats_path = os.path.join(chao_dir, chao_name, f'{chao_name}_stats.parquet')
        os.makedirs(os.path.dirname(chao_stats_path), exist_ok=True)
        current_inventory['Chao Egg'] = chao_egg_qty - 1
        self.data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        chao_stats = {
            'date': datetime.now().date().strftime("%Y-%m-%d"),
            'hatched': 1,
            'birth_date': datetime.now().date().strftime("%Y-%m-%d"),
            'hp_ticks': 0,
            'Form': '1',
            **{f"{stat}_ticks": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run']},
            **{f"{stat}_level": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run']},
            **{f"{stat}_exp": 0 for stat in ['swim', 'fly', 'run', 'power', 'stamina']},
            **{f"{stat}_grade": 'D' for stat in ['power', 'swim', 'stamina', 'fly', 'run']},
            'evolved': 0,
            'Type': 'Normal',
            'swim_fly': 0,
            'run_power': 0,
            'dark_hero': 0,
            'eyes': random.choice(self.eye_types),
            'mouth': random.choice(self.mouth_types),
        }
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)
        chao_image_path = self.NEUTRAL_PATH
        thumbnail_path = os.path.join(chao_dir, chao_name, f"{chao_name}_thumbnail.png")
        eyes, mouth = chao_stats['eyes'], chao_stats['mouth']
        alignment_str = 'neutral'
        eyes_image_path = os.path.join(self.EYES_DIR, f"{alignment_str}_{eyes}.png")
        if not os.path.exists(eyes_image_path):
            eyes_image_path = os.path.join(self.EYES_DIR, f"{alignment_str}.png")
        mouth_image_path = os.path.join(self.MOUTH_DIR, f"{mouth}.png")
        if not os.path.exists(mouth_image_path):
            mouth_image_path = os.path.join(self.MOUTH_DIR, "happy.png")
        self.image_utils.combine_images_with_face(
            self.BACKGROUND_PATH, chao_image_path, eyes_image_path, mouth_image_path, thumbnail_path
        )
        await ctx.reply(
            file=discord.File(thumbnail_path, filename=f"{chao_name}_thumbnail.png"),
            embed=discord.Embed(
                title="Your Chao Egg has hatched!",
                description=f"Your Chao Egg has hatched into a Regular Two-tone Chao named {chao_name}!",
                color=discord.Color.blue()
            ).set_image(url=f"attachment://{chao_name}_thumbnail.png")
        )

    def update_chao_type_and_thumbnail(self, guild_id, user_id, chao_name, latest_stats):
        try:
            print(f"[update_chao_type_and_thumbnail] Updating Chao: {chao_name}")
            chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

            # Use latest_stats directly
            stat_levels = {
                stat: latest_stats.get(f'{stat}_level', 0) for stat in ['power', 'swim', 'stamina', 'fly', 'run']
            }
            max_stat = max(stat_levels, key=stat_levels.get)
            max_level = stat_levels[max_stat]
            dark_hero = latest_stats.get('dark_hero', 0)
            current_form = latest_stats.get('Form', "1")
            current_type = latest_stats.get('Type', 'normal').lower()

            print(f"[update_chao_type_and_thumbnail] Current Form: {current_form}, "
                f"Max Level: {max_level}, Max Stat: {max_stat}")

            # Initialize variables
            chao_type = current_type
            form = current_form

            # Determine alignment based on form
            if current_form in ["1", "2"]:
                # Update alignment based on dark_hero
                if dark_hero >= self.HERO_ALIGNMENT:
                    alignment = "hero"
                elif dark_hero <= self.DARK_ALIGNMENT:
                    alignment = "dark"
                else:
                    alignment = "neutral"
                latest_stats['Alignment'] = alignment
            else:
                # Keep existing alignment
                alignment = latest_stats.get('Alignment', 'neutral')  # Default to neutral if not set

            # Evolution logic
            if current_form == "1" and max_level >= self.FORM_LEVEL_2:
                form = "2"
                # Form 1 to Form 2 transformations
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                if run_power >= self.RUN_POWER_THRESHOLD:
                    chao_type = f"{current_type}_power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    chao_type = f"{current_type}_run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    chao_type = f"{current_type}_fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    chao_type = f"{current_type}_swim"
                else:
                    chao_type = f"{current_type}_normal"
            elif current_form == "2" and max_level >= self.FORM_LEVEL_3:
                form = "3"
                # Form 2 to Form 3 transformations
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                if run_power >= self.RUN_POWER_THRESHOLD:
                    chao_type = "power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    chao_type = "run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    chao_type = "fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    chao_type = "swim"
                else:
                    chao_type = "normal"
                # Store alignment permanently in latest_stats
                latest_stats['Alignment'] = alignment
            elif current_form == "3" and max_level >= self.FORM_LEVEL_4:
                form = "4"
                # Form 3 to Form 4 transformations
                base_type = current_type if current_type in ['power', 'run', 'swim', 'fly', 'normal'] else 'normal'

                # Determine second evolution
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                if run_power >= self.RUN_POWER_THRESHOLD:
                    second_evolution = "power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    second_evolution = "run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    second_evolution = "fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    second_evolution = "swim"
                else:
                    second_evolution = "normal"

                chao_type = f"{base_type}_{second_evolution}"

            # Ensure the chao_type has two descriptors for Form 4
            if form == "4" and "_" not in chao_type:
                chao_type = f"{chao_type}_normal"

            # Update latest_stats with new Type and Form
            latest_stats['Type'] = chao_type
            latest_stats['Form'] = form

            print(f"[update_chao_type_and_thumbnail] Determined Form: {form}, "
                f"Type: {chao_type}, Alignment: {alignment}")

            # Determine eyes alignment based on form
            if form in ["1", "2"]:
                eyes_alignment = "neutral"
            else:
                eyes_alignment = alignment

            # Get eyes and mouth attributes
            eyes = latest_stats['eyes']
            mouth = latest_stats['mouth']

            # Paths to facial features
            eyes_image_filename = f"{eyes_alignment}_{eyes}.png"
            eyes_image_path = os.path.join(self.EYES_DIR, eyes_image_filename)
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(self.EYES_DIR, f"neutral_{eyes}.png")
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(self.EYES_DIR, f"{eyes_alignment}.png")

            mouth_image_filename = f"{mouth}.png"
            mouth_image_path = os.path.join(self.MOUTH_DIR, mouth_image_filename)
            if not os.path.exists(mouth_image_path):
                mouth_image_path = os.path.join(self.MOUTH_DIR, "happy.png")

            # Build the sprite image filename
            chao_image_filename = f"{alignment}_{chao_type}_{form}.png"

            # Construct the sprite image path
            base_type = chao_type.split('_')[0]
            chao_image_path = os.path.join(
                self.assets_dir, 'chao', base_type,
                alignment, chao_image_filename)

            # Check if the sprite image exists
            if not os.path.exists(chao_image_path):
                print(f"[update_chao_type_and_thumbnail] Sprite not found: {chao_image_path}")
                chao_image_path = os.path.join(self.assets_dir, 'chao', 'chao_missing.png')

            print(f"[update_chao_type_and_thumbnail] Using sprite: {chao_image_path}")

            # Combine images with facial features using image_utils
            self.image_utils.combine_images_with_face(
                self.BACKGROUND_PATH,
                chao_image_path,
                eyes_image_path,
                mouth_image_path,
                thumbnail_path
            )

            return chao_type, form
        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] An error occurred: {e}")
            return None, None


        async def market(self, ctx):
            embed = discord.Embed(title="**Black Market**", description="**Here's what you can buy:**", color=self.embed_color)
            custom_emoji = f'<:custom_emoji:{self.CUSTOM_EMOJI_ID}>'
            for fruit in self.fruits:
                embed.add_field(
                    name=f'**{fruit["emoji"]} {fruit["name"]}**',
                    value=f'**{custom_emoji} x {self.fruit_prices}**',
                    inline=True
                )
            await ctx.send(embed=embed)

    async def give_egg(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inventory_df = self.data_utils.load_inventory(inventory_path)
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {}
        chao_egg_qty = int(current_inventory.get('Chao Egg', 0))
        if chao_egg_qty >= 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg! Hatch it first before receiving another one.")
        current_inventory['Chao Egg'] = chao_egg_qty + 1
        self.data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has received a Chao Egg! You now have {current_inventory['Chao Egg']} Chao Egg(s).")

    async def buy(self, ctx, *, item_quantity: str):
        try:
            *item_parts, quantity = item_quantity.rsplit(' ', 1)
            item_name, quantity = ' '.join(item_parts), int(quantity)
        except ValueError:
            return await self.send_embed(ctx, f"{ctx.author.mention}, please specify the item and quantity correctly. For example: `$buy garden fruit 10`")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_df = self.data_utils.load_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        )
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {'rings': 0}
        rings = current_inventory.get('rings', 0)
        fruit = next((f for f in self.fruits if f['name'].lower() == item_name.lower()), None)
        if not fruit:
            return await self.send_embed(ctx, f"{ctx.author.mention}, the item '{item_name}' is not available in the market.")
        total_cost = self.fruit_prices * quantity
        if rings < total_cost:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have enough rings to buy {quantity} '{fruit['name']}'. You need {total_cost} rings.")
        current_inventory['rings'] -= total_cost
        current_inventory[fruit['name']] = current_inventory.get(fruit['name'], 0) + quantity
        self.data_utils.save_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'),
            inventory_df,
            current_inventory
        )
        await self.send_embed(ctx, f"{ctx.author.mention} has purchased {quantity} '{fruit['name']}(s)' for {total_cost} rings! You now have {current_inventory['rings']} rings.")

    async def inventory(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_df = self.data_utils.load_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        ).fillna(0)
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {'rings': 0}
        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.embed_color)
        embed.add_field(name='Rings', value=str(current_inventory.get("rings", 0)), inline=False)
        embed.add_field(name='Last Updated', value=current_inventory.get("date", "N/A"), inline=False)
        for fruit in self.fruits:
            qty = int(current_inventory.get(fruit['name'], 0))
            if qty > 0:
                embed.add_field(name=f'{fruit["emoji"]} {fruit["name"]}', value=f'Quantity: {qty}', inline=True)
        chao_eggs = int(current_inventory.get('Chao Egg', 0))
        if chao_eggs > 0:
            embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {chao_eggs}', inline=True)
        await ctx.send(embed=embed)

    async def stats(self, ctx, *, chao_name: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        
        # Check if the Chao exists
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")
        
        # Load Chao stats
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()
        
        # Update Chao type and thumbnail
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_stats)
        
        # Determine how to display the Chao type
        if form in ["1", "2"]:
            chao_type_display = "Normal"
        elif form == "4":
            chao_type_display = chao_type.replace("_", "/").capitalize()
        else:
            chao_type_display = chao_type.capitalize()
        
        # Retrieve alignment from chao_stats
        alignment_label = chao_stats.get('Alignment', 'Neutral').capitalize()
        
        # Prepare the stats image path
        stats_image_path = os.path.join(chao_dir, f'{chao_name}_stats.png')
        
        # Generate the stats image
        self.image_utils.paste_image(
            self.TEMPLATE_PATH,
            self.OVERLAY_PATH,
            stats_image_path,
            self.TICK_POSITIONS,
            chao_stats["power_ticks"],
            chao_stats["swim_ticks"],
            chao_stats["fly_ticks"],
            chao_stats["run_ticks"],
            chao_stats["stamina_ticks"],
            chao_stats["power_level"],
            chao_stats["swim_level"],
            chao_stats["fly_level"],
            chao_stats["run_level"],
            chao_stats["stamina_level"],
            chao_stats.get("swim_exp", 0),
            chao_stats.get("fly_exp", 0),
            chao_stats.get("run_exp", 0),
            chao_stats.get("power_exp", 0),
            chao_stats.get("stamina_exp", 0)
        )
        
        # Create the embed message
        embed = discord.Embed(color=self.embed_color)
        embed.set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://output_image.png")
        
        # Create the StatsView for pagination if applicable
        view = StatsView(
            chao_name,
            guild_id,
            user_id,
            self.TICK_POSITIONS,
            self.image_utils.EXP_POSITIONS,
            self.image_utils.num_images,
            self.image_utils.LEVEL_POSITION_OFFSET,
            self.image_utils.LEVEL_SPACING,
            self.image_utils.TICK_SPACING,
            chao_type_display,
            alignment_label,
            self.TEMPLATE_PATH,
            self.TEMPLATE_PAGE_2_PATH,
            self.OVERLAY_PATH,
            self.ICON_PATH,
            self.image_utils,
            self.data_utils
        )
        
        # Send the embed with the attached images
        await ctx.send(
            files=[
                discord.File(stats_image_path, "output_image.png"),
                discord.File(self.ICON_PATH),
                discord.File(os.path.join(chao_dir, f'{chao_name}_thumbnail.png'), "chao_thumbnail.png")
            ],
            embed=embed,
            view=view
        )


    async def feed(self, ctx, *, chao_name_and_fruit: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        parts = chao_name_and_fruit.split()
        fruit_name, chao_name = None, None

        # Extract the Chao name and fruit name
        for i in range(1, len(parts) + 1):
            potential_fruit = ' '.join(parts[-i:])
            fruit_match = next((f['name'] for f in self.fruits if f['name'].lower() == potential_fruit.lower()), None)
            if fruit_match:
                fruit_name = fruit_match
                chao_name = ' '.join(parts[:-i])
                break

        if not chao_name or not fruit_name:
            return await self.send_embed(ctx, f"{ctx.author.mention}, please provide both a valid Chao name and a fruit.")

        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        inventory_df = self.data_utils.load_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        )
        current_inventory = inventory_df.iloc[-1].to_dict() if not inventory_df.empty else {}
        if int(current_inventory.get(fruit_name, 0)) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any {fruit_name} to feed your Chao.")

        latest_stats = chao_df.iloc[-1].copy()
        stat_key = f"{self.FRUIT_STATS[fruit_name]}_ticks"
        level_key = f"{self.FRUIT_STATS[fruit_name]}_level"
        latest_stats[stat_key] = latest_stats.get(stat_key, 0) + random.randint(self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX)

        # Level up if ticks exceed threshold
        if latest_stats[stat_key] >= 10:
            latest_stats[stat_key] %= 10
            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
            exp_key = f"{self.FRUIT_STATS[fruit_name]}_exp"
            grade_key = f"{self.FRUIT_STATS[fruit_name]}_grade"
            latest_stats[exp_key] = latest_stats.get(exp_key, 0) + self.calculate_exp_gain(latest_stats.get(grade_key, 'D'))

        # Get current form
        current_form = latest_stats.get('Form', '1')

        # Adjust alignment and attributes only if Form is 1 or 2
        if current_form in ["1", "2"]:
            if fruit_name.lower() == 'hero fruit':
                latest_stats['dark_hero'] = min(self.HERO_ALIGNMENT, latest_stats.get('dark_hero', 0) + 1)
            elif fruit_name.lower() == 'dark fruit':
                latest_stats['dark_hero'] = max(self.DARK_ALIGNMENT, latest_stats.get('dark_hero', 0) - 1)

        # Adjust attributes regardless of form
        if fruit_name.lower() == 'swim fruit':
            latest_stats['swim_fly'] = max(-self.SWIM_FLY_THRESHOLD, latest_stats.get('swim_fly', 0) - 1)
            latest_stats['run_power'] += 1 if latest_stats.get('run_power', 0) < 0 else -1
        elif fruit_name.lower() == 'fly fruit':
            latest_stats['swim_fly'] = min(self.SWIM_FLY_THRESHOLD, latest_stats.get('swim_fly', 0) + 1)
            latest_stats['run_power'] += 1 if latest_stats.get('run_power', 0) < 0 else -1
        elif fruit_name.lower() == 'run fruit':
            latest_stats['run_power'] = max(-self.RUN_POWER_THRESHOLD, latest_stats.get('run_power', 0) - 1)
            latest_stats['swim_fly'] += 1 if latest_stats.get('swim_fly', 0) < 0 else -1
        elif fruit_name.lower() == 'power fruit':
            latest_stats['run_power'] = min(self.RUN_POWER_THRESHOLD, latest_stats.get('run_power', 0) + 1)
            latest_stats['swim_fly'] += 1 if latest_stats.get('swim_fly', 0) < 0 else -1

        # Update Chao type and thumbnail
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, latest_stats)

        # Update inventory
        current_inventory[fruit_name] -= 1
        self.data_utils.save_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'),
            inventory_df,
            current_inventory
        )

        # Save updated Chao stats
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats.to_dict())

        # Prepare the updated thumbnail
        thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

        # Create an embed with the updated thumbnail
        embed = discord.Embed(
            description=f"{chao_name} ate {fruit_name}!\n"
            f"{chao_name}'s {stat_key.split('_')[0].capitalize()} stat has increased!\n"
            f"Ticks: {latest_stats[stat_key]}/10\n"
            f"Level: {latest_stats.get(level_key, 0)} (Type: {latest_stats.get('Type', 'Normal')})\n"
            f"**Current Values:** swim_fly: {latest_stats.get('swim_fly', 0)}, "
            f"run_power: {latest_stats.get('run_power', 0)}, dark_hero: {latest_stats.get('dark_hero', 0)}",
            color=self.embed_color
        )
        embed.set_image(url=f"attachment://{chao_name}_thumbnail.png")
        await ctx.send(
            file=discord.File(thumbnail_path, filename=f"{chao_name}_thumbnail.png"),
            embed=embed
        )



class StatsView(View):
    def __init__(self, chao_name, guild_id, user_id, tick_positions, exp_positions, num_images, level_position_offset, level_spacing, tick_spacing, chao_type_display, alignment_label, template_path, template_page_2_path, overlay_path, icon_path, image_utils, data_utils):
        super().__init__(timeout=None)
        self.chao_name = chao_name
        self.guild_id = guild_id
        self.user_id = user_id
        self.tick_positions = tick_positions
        self.exp_positions = exp_positions
        self.num_images = num_images
        self.level_position_offset = level_position_offset
        self.level_spacing = level_spacing
        self.tick_spacing = tick_spacing
        self.chao_type_display = chao_type_display
        self.alignment_label = alignment_label
        self.TEMPLATE_PATH = template_path
        self.TEMPLATE_PAGE_2_PATH = template_page_2_path
        self.OVERLAY_PATH = overlay_path
        self.ICON_PATH = icon_path
        self.image_utils = image_utils
        self.data_utils = data_utils

    @discord.ui.button(label="Page 1", style=discord.ButtonStyle.primary)
    async def page_1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_stats(interaction, "Page 1")

    @discord.ui.button(label="Page 2", style=discord.ButtonStyle.secondary)
    async def page_2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_stats(interaction, "Page 2")

    async def update_stats(self, interaction: discord.Interaction, page: str):
        chao_dir = self.data_utils.get_path(self.guild_id, self.user_id, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_to_view = chao_df.iloc[-1].to_dict()

        print(f"[update_stats] Displaying {page} for Chao: {self.chao_name}, User: {self.user_id}")

        if page == "Page 1":
            template_path = self.TEMPLATE_PATH
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_1.png')
        else:
            template_path = self.TEMPLATE_PAGE_2_PATH
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_2.png')

        self.image_utils.paste_image(
            template_path,
            self.OVERLAY_PATH,
            image_path,
            self.tick_positions,
            chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["fly_ticks"],
            chao_to_view["run_ticks"], chao_to_view["stamina_ticks"],
            chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["fly_level"],
            chao_to_view["run_level"], chao_to_view["stamina_level"],
            chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0),
            chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0),
            chao_to_view.get("stamina_exp", 0)
        )

        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=self.chao_type_display, inline=True).add_field(name="Alignment", value=self.alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://{os.path.basename(image_path)}")

        await interaction.response.edit_message(embed=embed, view=self, attachments=[
            discord.File(image_path, os.path.basename(image_path)),
            discord.File(self.ICON_PATH),
            discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
        ])

async def setup(bot):
    await bot.add_cog(Chao(bot))
