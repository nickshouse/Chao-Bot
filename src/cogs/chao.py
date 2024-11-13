import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime
from PIL import Image, ImageEnhance

# Configuration Constants
FORM_LEVEL_2 = 5
FORM_LEVEL_3 = 8
FORM_LEVEL_4 = 10

HERO_ALIGNMENT = 5
DARK_ALIGNMENT = -5
NEUTRAL_ALIGNMENT = 0

FRUIT_TICKS_MIN = 6
FRUIT_TICKS_MAX = 8

FRUIT_STATS = {
    "Garden Nut": 'stamina',
    "Hero Fruit": 'stamina',
    "Dark Fruit": 'stamina',
    "Round Fruit": 'stamina',
    "Triangle Fruit": 'stamina',
    "Heart Fruit": 'stamina',
    "Square Fruit": 'stamina',
    "Chao Fruit": 'all',
    "Smart Fruit": 'mind',
    "Power Fruit": 'power',
    "Run Fruit": 'run',
    "Swim Fruit": 'swim',
    "Fly Fruit": 'fly',
    "Tasty Fruit": 'stamina',
    "Strange Mushroom": 'stamina'
}

class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        # Base directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        # Assets directory
        self.assets_dir = os.path.join(self.base_dir, '../../assets')

        # Paths for images
        self.TEMPLATE_PATH = os.path.join(
            self.assets_dir, 'graphics/cards/stats_page_1.png')
        self.TEMPLATE_PAGE_2_PATH = os.path.join(
            self.assets_dir, 'graphics/cards/stats_page_2.png')
        self.OVERLAY_PATH = os.path.join(
            self.assets_dir, 'graphics/ticks/tick_filled.png')
        self.ICON_PATH = os.path.join(self.assets_dir, 'graphics/icons/Stats.png')
        self.NEUTRAL_PATH = os.path.join(
            self.assets_dir, 'chao/normal/neutral/neutral_normal_1.png')
        self.DARK_PATH = os.path.join(
            self.assets_dir, 'chao/normal/dark/dark_normal_1.png')
        self.HERO_PATH = os.path.join(
            self.assets_dir, 'chao/normal/hero/hero_normal_1.png')
        self.BACKGROUND_PATH = os.path.join(
            self.assets_dir, 'graphics/thumbnails/neutral_background.png')

        self.TICK_SPACING = 105
        self.LEVEL_POSITION_OFFSET = (826, -106)
        self.LEVEL_SPACING = 60
        self.TICK_POSITIONS = [
            (446, 1176), (446, 315), (446, 1747),
            (446, 591), (446, 883), (446, 1469)
        ]
        self.EXP_POSITIONS = {
            stat: [(183 + i * 60, y) for i in range(4)]
            for stat, y in zip(
                ['swim', 'fly', 'run', 'power', 'mind', 'stamina'],
                [302, 576, 868, 1161, 1454, 1732]
            )
        }
        self.GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.GRADE_TO_VALUE = {
            'F': -1, 'E': 0, 'D': 1, 'C': 2,
            'B': 3, 'A': 4, 'S': 5, 'X': 6
        }
        self.CUSTOM_EMOJI_ID = 1176313914464681984

        # Eye and mouth types
        self.eye_types = [
            'normal', 'happy', 'angry', 'sad',
            'sleep', 'tired', 'pain'
        ]
        self.mouth_types = [
            'happy', 'unhappy', 'mean', 'grumble', 'evil'
        ]

        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')

        self.fruits = [
            {"emoji": emoji, "name": name}
            for emoji, name in zip(
                "🍏🍎🍐🍊🍋🍌🍉🍇🍓🫐🍈🍒🍑🥭🍍",
                [
                    "Garden Nut", "Hero Fruit", "Dark Fruit",
                    "Round Fruit", "Triangle Fruit", "Heart Fruit",
                    "Square Fruit", "Chao Fruit", "Smart Fruit",
                    "Power Fruit", "Run Fruit", "Swim Fruit",
                    "Fly Fruit", "Tasty Fruit", "Strange Mushroom"
                ]
            )
        ]
        self.fruit_prices = 15
        self.chao_names = [
            "Chaoko", "Chaowser", "Chaorunner", "Chaozart",
            "Chaobacca", "Chaowder", "Chaocolate", "Chaolesterol",
            "Chao Mein", "Chaoster", "Chaomanji", "Chaosmic",
            "Chaozilla", "Chaoseidon", "Chaosferatu", "Chaolin",
            "Chow", "Chaotzhu", "Chaoblin", "Count Chaocula",
            "Chaozil", "Chaoz"
        ]
        # Remove self.current_date

        self.num_images = {
            str(i): Image.open(
                os.path.join(self.assets_dir, f"resized/{i}.png")
            )
            for i in range(10)
        }

    def get_path(self, guild_id, user_id, folder, filename):
        base = os.path.join(
            self.base_dir, '../../database', guild_id, user_id, folder)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    def save_inventory(self, path, inventory_df, current_inventory):
        current_inventory.setdefault('Chao Egg', 0)
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        new_entry = {**{'date': current_date_str}, **current_inventory}
        columns = ['date'] + [col for col in new_entry if col != 'date']
        new_entry_df = pd.DataFrame([new_entry])[columns]

        # Remove any existing entries for the current date
        inventory_df = inventory_df[inventory_df['date'] != current_date_str]

        # Append the new entry
        inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)

        # Save the updated DataFrame
        inventory_df.to_parquet(path, index=False)


    def load_inventory(self, path):
        if os.path.exists(path):
            inventory_df = pd.read_parquet(path).fillna(0)
            columns = ['date'] + [col for col in inventory_df.columns if col != 'date']
            inventory_df = inventory_df[columns]
            return inventory_df
        else:
            current_date_str = datetime.now().date().strftime("%Y-%m-%d")
            return pd.DataFrame({
                'date': [current_date_str],
                'rings': [0], 'Chao Egg': [0], 'Garden Fruit': [0]
            })


    def is_user_initialized(self, guild_id, user_id):
        return os.path.exists(
            os.path.join(
                self.base_dir, '../../database', guild_id, user_id))

    def calculate_exp_gain(self, grade):
        return (self.GRADE_TO_VALUE[grade] * 3) + 13

    def combine_images_with_face(
            self, background_path, chao_image_path, eyes_image_path,
            mouth_image_path, output_path):
        with Image.open(background_path).convert("RGBA") as background, \
                Image.open(chao_image_path).convert("RGBA") as chao_img, \
                Image.open(eyes_image_path).convert("RGBA") as eyes_img, \
                Image.open(mouth_image_path).convert("RGBA") as mouth_img:

            # Resize images
            chao_img = chao_img.resize((70, 70), Image.LANCZOS)
            background = background.resize((70, 70), Image.LANCZOS)
            eyes_img = eyes_img.resize((70, 70), Image.LANCZOS)
            mouth_img = mouth_img.resize((70, 70), Image.LANCZOS)

            # Composite the images
            chao_with_eyes = Image.alpha_composite(chao_img, eyes_img)
            chao_with_face = Image.alpha_composite(chao_with_eyes, mouth_img)
            final_image = Image.alpha_composite(background, chao_with_face)
            final_image.save(output_path)

    def paste_image(
            self, template_path, overlay_path, output_path,
            tick_positions, *stats):
        with Image.open(template_path) as template, \
                Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA")
            # Paste EXP numbers
            for stat, exp in zip(
                    ["swim", "fly", "run", "power", "mind", "stamina"],
                    stats[-6:]):
                exp_str = f"{int(exp):04d}"
                for pos, digit in zip(
                        self.EXP_POSITIONS[stat], exp_str):
                    template.paste(
                        self.num_images[digit], pos, self.num_images[digit])
            # Paste ticks
            for pos, ticks in zip(tick_positions, stats[:6]):
                for i in range(int(ticks)):
                    tick_pos = (pos[0] + i * self.TICK_SPACING, pos[1])
                    template.paste(overlay, tick_pos, overlay)
            # Paste levels
            for pos, level in zip(tick_positions, stats[6:12]):
                tens = int(level) // 10
                ones = int(level) % 10
                x_offset, y_offset = self.LEVEL_POSITION_OFFSET
                template.paste(
                    self.num_images[str(tens)],
                    (pos[0] + x_offset, pos[1] + y_offset),
                    self.num_images[str(tens)])
                template.paste(
                    self.num_images[str(ones)],
                    (pos[0] + x_offset + self.LEVEL_SPACING,
                     pos[1] + y_offset),
                    self.num_images[str(ones)])
            template.save(output_path)

    def change_image_hue(
            self, image_path, output_path, hue, saturation):
        img = Image.open(image_path).convert('RGB')
        hsv_img = img.convert('HSV')
        h, s, v = hsv_img.split()
        h = h.point(lambda p: hue)
        s = s.point(lambda p: int(p * saturation))
        hsv_img = Image.merge('HSV', (h, s, v))
        rgb_img = hsv_img.convert('RGB')
        rgb_img.save(output_path)

    def save_chao_stats(self, chao_stats_path, chao_df, chao_stats):
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        chao_stats['date'] = current_date_str
        columns = ['date'] + [col for col in chao_stats if col != 'date']
        new_entry_df = pd.DataFrame([chao_stats])[columns]

        # Remove any existing entries for the current date
        chao_df = chao_df[chao_df['date'] != current_date_str]

        # Append the new entry
        chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True)

        # Save the updated DataFrame
        chao_df.to_parquet(chao_stats_path, index=False)




    def load_chao_stats(self, chao_stats_path):
        if os.path.exists(chao_stats_path):
            chao_df = pd.read_parquet(chao_stats_path).fillna(0)
            columns = ['date'] + [col for col in chao_df.columns if col != 'date']
            chao_df = chao_df[columns]
            return chao_df
        else:
            return pd.DataFrame(columns=['date'])


    def update_chao_type_and_thumbnail(
            self, guild_id, user_id, chao_name, chao_df):
        try:
            print(f"[update_chao_type_and_thumbnail] Updating Chao: {chao_name}")
            chao_dir = self.get_path(
                guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(
                chao_dir, f'{chao_name}_thumbnail.png')

            # Use the latest stats
            latest_stats = chao_df.iloc[-1]

            # Extract stat levels
            stat_levels = {
                stat: latest_stats[f'{stat}_level']
                for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']
            }
            max_stat = max(stat_levels, key=stat_levels.get)
            max_level = stat_levels[max_stat]
            dark_hero = latest_stats['dark_hero']
            current_form = latest_stats.get('Form', "1")
            current_type = latest_stats.get('Type', 'normal').lower()

            print(f"[update_chao_type_and_thumbnail] Current Form: {current_form}, "
                  f"Max Level: {max_level}, Max Stat: {max_stat}")

            # Determine alignment
            if dark_hero >= HERO_ALIGNMENT:
                alignment = "hero"
            elif dark_hero <= DARK_ALIGNMENT:
                alignment = "dark"
            else:
                alignment = "neutral"

            # Get evolution parameters
            run_power = latest_stats['run_power']
            swim_fly = latest_stats['swim_fly']

            # Initialize variables
            chao_type = current_type
            form = current_form

            # Evolution logic
            if current_form == "1" and max_level >= FORM_LEVEL_2:
                form = "2"
                # Form 1 to Form 2 transformations
                if run_power >= 5:
                    chao_type = f"{current_type}_power"
                elif run_power <= -5:
                    chao_type = f"{current_type}_run"
                elif swim_fly >= 5:
                    chao_type = f"{current_type}_fly"
                elif swim_fly <= -5:
                    chao_type = f"{current_type}_swim"
                else:
                    chao_type = f"{current_type}_normal"
            elif current_form == "2" and max_level >= FORM_LEVEL_3:
                form = "3"
                # Form 2 to Form 3 transformations
                if run_power >= 5:
                    chao_type = "power"
                elif run_power <= -5:
                    chao_type = "run"
                elif swim_fly >= 5:
                    chao_type = "fly"
                elif swim_fly <= -5:
                    chao_type = "swim"
                else:
                    chao_type = "normal"
            elif current_form == "3" and max_level >= FORM_LEVEL_4:
                form = "4"
                # Form 3 to Form 4 transformations
                base_type = current_type
                if base_type not in ['power', 'run', 'swim', 'fly', 'normal']:
                    base_type = 'normal'

                # Determine second evolution
                if run_power >= 5:
                    second_evolution = "power"
                elif run_power <= -5:
                    second_evolution = "run"
                elif swim_fly >= 5:
                    second_evolution = "fly"
                elif swim_fly <= -5:
                    second_evolution = "swim"
                else:
                    second_evolution = "normal"

                chao_type = f"{base_type}_{second_evolution}"

            # Ensure the chao_type has two descriptors for Form 4
            if form == "4" and "_" not in chao_type:
                chao_type = f"{chao_type}_normal"

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
            eyes_image_path = os.path.join(
                self.EYES_DIR, eyes_image_filename)
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(
                    self.EYES_DIR, f"neutral_{eyes}.png")
            if not os.path.exists(eyes_image_path):
                eyes_image_path = os.path.join(
                    self.EYES_DIR, f"{eyes_alignment}.png")

            mouth_image_filename = f"{mouth}.png"
            mouth_image_path = os.path.join(
                self.MOUTH_DIR, mouth_image_filename)
            if not os.path.exists(mouth_image_path):
                mouth_image_path = os.path.join(
                    self.MOUTH_DIR, "happy.png")

            # Build the sprite image filename
            chao_image_filename = f"{alignment}_{chao_type}_{form}.png"

            # Construct the sprite image path
            base_type = chao_type.split('_')[0]
            chao_image_path = os.path.join(
                self.assets_dir, 'chao', base_type,
                alignment, chao_image_filename)

            # Check if the sprite image exists
            if not os.path.exists(chao_image_path):
                print(f"[update_chao_type_and_thumbnail] Sprite not found: "
                      f"{chao_image_path}")
                chao_image_path = os.path.join(
                    self.assets_dir, 'chao', 'chao_missing.png')

            print(f"[update_chao_type_and_thumbnail] Using sprite: "
                  f"{chao_image_path}")

            # Combine images with facial features
            self.combine_images_with_face(
                self.BACKGROUND_PATH,
                chao_image_path,
                eyes_image_path,
                mouth_image_path,
                thumbnail_path
            )


            # Update Chao's Type and Form in DataFrame
            chao_df.at[chao_df.index[-1], 'Type'] = chao_type
            chao_df.at[chao_df.index[-1], 'Form'] = form

            # Save updated Chao data
            chao_df.to_parquet(
                os.path.join(chao_dir, f'{chao_name}_stats.parquet'),
                index=False)
            print(f"[update_chao_type_and_thumbnail] Updated Chao stats saved.")

            return chao_type, form
        except Exception as e:
            print(f"[update_chao_type_and_thumbnail] An error occurred: {e}")
            return None

    async def initialize_inventory(self, ctx, guild_id, user_id, embed_title, embed_desc):
        print(f"[initialize_inventory] Initializing inventory for User: {user_id}, Guild: {guild_id}")
        if self.is_user_initialized(guild_id, user_id):
            print(f"[initialize_inventory] User: {user_id} is already initialized.")
            return await ctx.send(f"{ctx.author.mention}, you have already started using the Chao Bot.")
        self.save_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'), self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')), {'rings': 500, 'Chao Egg': 1, 'Garden Fruit': 5})
        await ctx.reply(file=discord.File(self.NEUTRAL_PATH, filename="neutral_normal_1.png"), embed=discord.Embed(title=embed_title, description=embed_desc, color=self.embed_color).set_image(url="attachment://neutral_normal_1.png"))
        print(f"[initialize_inventory] Inventory initialized with 500 Rings, 1 Chao Egg, 5 Garden Fruits for User: {user_id}")

    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)

    
    async def chao(self, ctx):
        print(f"[chao] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        await self.initialize_inventory(ctx, str(ctx.guild.id), str(ctx.author.id), "Welcome to Chao Bot!",
                                        "**You Receive:**\n- `1x Chao Egg`\n- `500x Rings`\n- `5x Garden Nut`\n\n"
                                        "**Example Commands:**\n- `$feed [Chao name] [item]` to feed your Chao.\n- `$race [Chao name]` to enter your Chao in a race.\n- `$train [Chao name] [stat]` to train a specific stat.\n- `$stats [Chao name]` to view your Chao's stats.")

    
    async def hatch(self, ctx):
        print(f"[hatch] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        file_path = self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        chao_egg_quantity = int(inventory_df.iloc[-1].get('Chao Egg', 0))

        if chao_egg_quantity < 1:
            print(f"[hatch] No Chao Egg available for User: {user_id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")

        chao_dir = self.get_path(guild_id, user_id, 'chao_data', '')
        chao_name = random.choice(self.chao_names)
        os.makedirs(chao_dir, exist_ok=True)
        while chao_name in [name for name in os.listdir(chao_dir) if os.path.isdir(os.path.join(chao_dir, name))]:
            chao_name = random.choice(self.chao_names)

        chao_path = os.path.join(self.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        os.makedirs(os.path.dirname(chao_path), exist_ok=True)
        inventory_df.at[inventory_df.index[-1], 'Chao Egg'] = chao_egg_quantity - 1
        self.save_inventory(file_path, inventory_df, inventory_df.iloc[-1].to_dict())

        # Ensure 'Form' is initialized as "1" during Chao creation
        current_date_str = datetime.now().date().strftime("%Y-%m-%d")
        chao_stats = {
            'hatched': 1,
            'birth_date': current_date_str,
            'hp_ticks': 0,
            'Form': '1',
            **{f"{stat}_ticks": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            **{f"{stat}_level": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            **{f"{stat}_exp": 0 for stat in ['swim', 'fly', 'run', 'power', 'mind', 'stamina']},
            **{f"{stat}_grade": 'D' for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            'evolved': False,
            'Type': 'Normal',
            'swim_fly': 0,
            'run_power': 0,
            'dark_hero': 0,
            'eyes': random.choice(self.eye_types),
            'mouth': random.choice(self.mouth_types),
        }

        chao_df = self.load_chao_stats(chao_path)
        self.save_chao_stats(chao_path, chao_df, chao_stats)

        # Generate the Chao's image with face
        chao_image_path = self.NEUTRAL_PATH  # Assuming initial Chao is neutral
        chao_dir = self.get_path(guild_id, user_id, 'chao_data', chao_name)
        thumbnail_path = os.path.join(chao_dir, f"{chao_name}_thumbnail.png")

        # Get the Chao's eyes and mouth attributes
        eyes = chao_stats['eyes']
        mouth = chao_stats['mouth']
        alignment_str = 'neutral'  # Initial alignment

        # Paths to facial features
        eyes_image_filename = f"{alignment_str}_{eyes}.png"
        eyes_image_path = os.path.join(self.EYES_DIR, eyes_image_filename)
        if not os.path.exists(eyes_image_path):
            eyes_image_path = os.path.join(self.EYES_DIR, f"{alignment_str}.png")

        mouth_image_filename = f"{mouth}.png"
        mouth_image_path = os.path.join(self.MOUTH_DIR, mouth_image_filename)
        if not os.path.exists(mouth_image_path):
            mouth_image_path = os.path.join(self.MOUTH_DIR, "happy.png")

        # Combine images with face
        self.combine_images_with_face(
            self.BACKGROUND_PATH,
            chao_image_path,
            eyes_image_path,
            mouth_image_path,
            thumbnail_path
        )

        await ctx.reply(
            file=discord.File(thumbnail_path, filename=f"{chao_name}_thumbnail.png"),
            embed=discord.Embed(
                title="Your Chao Egg has hatched!",
                description=f"Your Chao Egg has hatched into a Regular Two-tone Chao named {chao_name}!",
                color=discord.Color.blue()
            ).set_image(url=f"attachment://{chao_name}_thumbnail.png")
        )
        print(f"[hatch] Chao Egg hatched into {chao_name} for User: {user_id}. Chao data saved to {chao_path}")

    
    async def market(self, ctx):
        print(f"[market] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        embed = discord.Embed(title="**Black Market**", description="**Here's what you can buy:**", color=self.embed_color)
        custom_emoji = f'<:custom_emoji:{self.CUSTOM_EMOJI_ID}>'
        for fruit in self.fruits:
            embed.add_field(name=f'**{fruit["emoji"]} {fruit["name"]}**', value=f'**{custom_emoji} x {self.fruit_prices}**', inline=True)
        await ctx.send(embed=embed)
        print(f"[market] Market items displayed to User: {ctx.author.id}")

    
    async def give_rings(self, ctx):
        print(f"[give_rings] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        rings = inventory_df.iloc[-1]['rings'] + 1000
        current_inventory = inventory_df.iloc[-1].to_dict()
        current_inventory['rings'] = rings
        self.save_inventory(file_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has been given 1000 rings! Your current rings: {rings}")
        print(f"[give_rings] 1000 Rings added to User: {user_id}. New balance: {rings}")

    
    async def buy(self, ctx, *, item_quantity: str):
        print(f"[buy] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        try:
            *item_name_parts, quantity = item_quantity.rsplit(' ', 1)
            item_name, quantity = ' '.join(item_name_parts), int(quantity)
        except ValueError:
            print(f"[buy] Invalid input: {item_quantity} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, please specify the item and quantity correctly. For example: `$buy garden fruit 10`")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        rings, fruit = inventory_df.iloc[-1]['rings'], next((fruit_item for fruit_item in self.fruits if fruit_item['name'].lower() == item_name.lower()), None)
        if not fruit:
            print(f"[buy] Invalid item: {item_name} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, the item '{item_name}' is not available in the market.")
        total_cost = self.fruit_prices * quantity
        if rings < total_cost:
            print(f"[buy] Insufficient rings. Required: {total_cost}, Available: {rings} for User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have enough rings to buy {quantity} '{fruit['name']}'. You need {total_cost} rings.")
        current_inventory = inventory_df.iloc[-1].to_dict()
        current_inventory['rings'] -= total_cost
        current_inventory[fruit['name']] = current_inventory.get(fruit['name'], 0) + quantity
        self.save_inventory(file_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has purchased {quantity} '{fruit['name']}(s)' for {total_cost} rings! You now have {current_inventory['rings']} rings.")
        print(f"[buy] User: {ctx.author.id} bought {quantity}x {fruit['name']} for {total_cost} rings. Remaining rings: {current_inventory['rings']}")

    
    async def inventory(self, ctx):
        print(f"[inventory] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_df = self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0)
        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.embed_color)
        embed.add_field(name='Rings', value=f'{int(inventory_df.iloc[-1]["rings"])}', inline=False)
        embed.add_field(name='Last Updated', value=f'{inventory_df.iloc[-1]["date"]}', inline=False)
        for fruit in self.fruits:
            quantity = int(inventory_df.iloc[-1].get(fruit['name'], 0))
            if quantity > 0:
                embed.add_field(name=f'{fruit["emoji"]} {fruit["name"]}', value=f'Quantity: {quantity}', inline=True)
        chao_egg_quantity = int(inventory_df.iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity > 0:
            embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {chao_egg_quantity}', inline=True)
        await ctx.send(embed=embed)
        print(f"[inventory] Inventory displayed for User: {ctx.author.id}")

    
    async def restore(self, ctx, *, args: str):
        print(f"[restore] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        parts = args.split()
        if len(parts) < 2:
            print(f"[restore] Invalid input: {args} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, please use the command in the correct format.")

        if parts[0].lower() == 'inventory':
            if len(parts) != 2:
                return await self.send_embed(ctx, f"{ctx.author.mention}, please use the command in the format: $restore inventory YYYY-MM-DD")
            date_str = parts[1]
            guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
            file_path = self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
            try:
                restore_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"[restore] Invalid date format: {date_str} by User: {ctx.author.id}")
                return await self.send_embed(ctx, f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")
            inventory_df = self.load_inventory(file_path)
            if date_str not in inventory_df['date'].values:
                print(f"[restore] No data found for date: {date_str} by User: {ctx.author.id}")
                return await self.send_embed(ctx, f"{ctx.author.mention}, no inventory data found for {date_str}.")
            restored_inventory = inventory_df[inventory_df['date'] == date_str].iloc[0].to_dict()
            current_date_str = datetime.now().date().strftime("%Y-%m-%d")
            restored_inventory['date'] = current_date_str
            columns = ['date'] + [col for col in restored_inventory if col != 'date']
            new_entry_df = pd.DataFrame([restored_inventory])[columns]
            # Remove any existing entry for current date
            inventory_df = inventory_df[inventory_df['date'] != current_date_str]
            # Append the restored entry
            inventory_df = pd.concat([inventory_df, new_entry_df], ignore_index=True).fillna(0)
            # Save the updated inventory DataFrame
            inventory_df.to_parquet(file_path, index=False)
            await self.send_embed(ctx, f"{ctx.author.mention}, your inventory has been restored to the state from {date_str}.")
            print(f"[restore] Inventory restored to {date_str} for User: {ctx.author.id}")
        elif parts[0].lower() == 'chao':
            if len(parts) != 3:
                return await self.send_embed(ctx, f"{ctx.author.mention}, please use the command in the format: $restore chao [Chao name] YYYY-MM-DD")
            chao_name = parts[1]
            date_str = parts[2]
            guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
            chao_stats_path = os.path.join(
                self.get_path(guild_id, user_id, 'chao_data', chao_name),
                f'{chao_name}_stats.parquet'
            )

            if not os.path.exists(chao_stats_path):
                print(f"[restore] Chao {chao_name} not found for User: {ctx.author.id}")
                return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

            try:
                restore_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                print(f"[restore] Invalid date format: {date_str} by User: {ctx.author.id}")
                return await self.send_embed(ctx, f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")

            chao_df = self.load_chao_stats(chao_stats_path)

            if date_str not in chao_df['date'].values:
                print(f"[restore] No data found for date: {date_str} for Chao: {chao_name}")
                return await self.send_embed(ctx, f"{ctx.author.mention}, no data found for {chao_name} on {date_str}.")

            # Get the stats from the specified date
            restored_stats = chao_df[chao_df['date'] == date_str].iloc[0].to_dict()

            # Update date to current date
            current_date_str = datetime.now().date().strftime("%Y-%m-%d")
            restored_stats['date'] = current_date_str
            columns = ['date'] + [col for col in restored_stats if col != 'date']
            new_entry_df = pd.DataFrame([restored_stats])[columns]

            # Remove any existing entry for current date
            chao_df = chao_df[chao_df['date'] != current_date_str]

            # Append restored stats
            chao_df = pd.concat([chao_df, new_entry_df], ignore_index=True)
            chao_df.to_parquet(chao_stats_path, index=False)

            await self.send_embed(ctx, f"{ctx.author.mention}, {chao_name}'s stats have been restored to the state from {date_str}.")
            print(f"[restore] {chao_name}'s stats restored to {date_str} for User: {ctx.author.id}")

    
    async def give_egg(self, ctx):
        print(f"[give_egg] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        chao_egg_quantity = int(inventory_df.iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity >= 1:
            print(f"[give_egg] User: {ctx.author.id} already has a Chao Egg.")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg! Hatch it first before receiving another one.")
        current_inventory = inventory_df.iloc[-1].to_dict()
        current_inventory['Chao Egg'] = chao_egg_quantity + 1
        self.save_inventory(file_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has received a Chao Egg! You now have {chao_egg_quantity + 1} Chao Egg(s).")
        print(f"[give_egg] Chao Egg given to User: {ctx.author.id}. New count: {chao_egg_quantity + 1}")

    
    async def stats(self, ctx, *, chao_name: str):
        print(f"[stats] Command called by User: {ctx.author.id} for Chao: {chao_name} in Guild: {ctx.guild.id}")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            print(f"[stats] Chao {chao_name} not found for User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

        chao_df = self.load_chao_stats(chao_stats_path)
        # Update Chao's thumbnail and type
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)
        # Reload chao_df to get updated data
        chao_df = self.load_chao_stats(chao_stats_path)
        chao_to_view = chao_df.iloc[-1].to_dict()

        if form in ["1", "2"]:
            chao_type_display = "Normal"
        elif form == "3":
            chao_type_display = chao_type
        else:
            chao_type_display = chao_type.replace("_", "/")

        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")

        # Determine alignment based on dark_hero value
        dark_hero = chao_to_view.get('dark_hero', 0)
        alignment_label = "Hero" if dark_hero >= HERO_ALIGNMENT else "Dark" if dark_hero <= DARK_ALIGNMENT else "Neutral"

        self.paste_image(self.TEMPLATE_PATH, self.OVERLAY_PATH, os.path.join(chao_dir, f'{chao_name}_stats.png'), self.TICK_POSITIONS, chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"], chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"], chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"], chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"], chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0), chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0), chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))
        embed.add_field(name="Type", value=chao_type_display, inline=True).add_field(name="Alignment", value=alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://output_image.png")

        view = StatsView(chao_name, guild_id, user_id, self.TICK_POSITIONS, self.EXP_POSITIONS, self.num_images, self.LEVEL_POSITION_OFFSET, self.LEVEL_SPACING, self.TICK_SPACING, chao_type_display, alignment_label, self.TEMPLATE_PATH, self.TEMPLATE_PAGE_2_PATH, self.OVERLAY_PATH, self.ICON_PATH)

        print(f"[stats] Displaying stats for Chao: {chao_name}, Type: {chao_type}, Form: {form}, Alignment: {alignment_label}")

        await ctx.send(files=[
            discord.File(os.path.join(chao_dir, f'{chao_name}_stats.png'), "output_image.png"),
            discord.File(self.ICON_PATH),
            discord.File(os.path.join(chao_dir, f'{chao_name}_thumbnail.png'), "chao_thumbnail.png")
        ], embed=embed, view=view)

    
    async def feed(self, ctx, chao_name_and_fruit: str):
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Split the chao_name_and_fruit based on spaces
        parts = chao_name_and_fruit.split()

        # Attempt to match the last word(s) with a fruit name
        fruit_name = None
        chao_name = None

        # Check for fruit name
        for i in range(1, len(parts) + 1):
            potential_fruit_name = ' '.join(parts[-i:])
            fruit_name_match = next((fruit_item['name'] for fruit_item in self.fruits if fruit_item['name'].lower() == potential_fruit_name.lower()), None)
            if fruit_name_match:
                fruit_name = fruit_name_match
                chao_name = ' '.join(parts[:-i])
                break

        if not chao_name or not fruit_name:
            return await self.send_embed(ctx, f"{ctx.author.mention}, please provide both a valid Chao name and a fruit.")

        chao_dir_path = self.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir_path, f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

        chao_df = self.load_chao_stats(chao_stats_path)
        inventory_df = self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0)
        fruit = next((fruit_item for fruit_item in self.fruits if fruit_item['name'].lower() == fruit_name.lower()), None)

        if not fruit or fruit['name'] not in inventory_df.columns or int(inventory_df.iloc[-1].get(fruit['name'], 0)) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any {fruit_name} to feed your Chao.")

        # Log before feeding
        latest_stats = chao_df.iloc[-1].copy()
        print(f"[feed] Command called by User: {user_id} for Chao: {chao_name} with Fruit: {fruit_name} in Guild: {guild_id}")
        print(f"[feed] Before feeding {fruit_name.capitalize()} | Chao: {chao_name} | {FRUIT_STATS[fruit_name]}_ticks: {latest_stats.get(f'{FRUIT_STATS[fruit_name]}_ticks', 0)} | Level: {latest_stats.get(f'{FRUIT_STATS[fruit_name]}_level', 0)} | swim_fly: {latest_stats.get('swim_fly', 0)} | run_power: {latest_stats.get('run_power', 0)}")

        # Adjust swim_fly and run_power according to the logic
        if fruit_name.lower() == 'swim fruit':
            latest_stats['swim_fly'] = max(-5, latest_stats.get('swim_fly', 0) - 1)
            if latest_stats.get('run_power', 0) > 0:
                latest_stats['run_power'] -= 1
            elif latest_stats.get('run_power', 0) < 0:
                latest_stats['run_power'] += 1
        elif fruit_name.lower() == 'fly fruit':
            latest_stats['swim_fly'] = min(5, latest_stats.get('swim_fly', 0) + 1)
            if latest_stats.get('run_power', 0) > 0:
                latest_stats['run_power'] -= 1
            elif latest_stats.get('run_power', 0) < 0:
                latest_stats['run_power'] += 1
        elif fruit_name.lower() == 'run fruit':
            latest_stats['run_power'] = max(-5, latest_stats.get('run_power', 0) - 1)
            if latest_stats.get('swim_fly', 0) > 0:
                latest_stats['swim_fly'] -= 1
            elif latest_stats.get('swim_fly', 0) < 0:
                latest_stats['swim_fly'] += 1
        elif fruit_name.lower() == 'power fruit':
            latest_stats['run_power'] = min(5, latest_stats.get('run_power', 0) + 1)
            if latest_stats.get('swim_fly', 0) > 0:
                latest_stats['swim_fly'] -= 1
            elif latest_stats.get('swim_fly', 0) < 0:
                latest_stats['swim_fly'] += 1

        # Adjust dark_hero based on Hero or Dark Fruit
        if fruit_name.lower() == 'hero fruit':
            latest_stats['dark_hero'] = min(5, latest_stats.get('dark_hero', 0) + 1)  # Increase dark_hero value
        elif fruit_name.lower() == 'dark fruit':
            latest_stats['dark_hero'] = max(-5, latest_stats.get('dark_hero', 0) - 1)  # Decrease dark_hero value

        # Update stat ticks and level
        stat_key = f"{FRUIT_STATS[fruit['name']]}_ticks"
        level_key = f"{FRUIT_STATS[fruit['name']]}_level"  # Ensure level_key is defined
        latest_stats[stat_key] = latest_stats.get(stat_key, 0) + random.randint(FRUIT_TICKS_MIN, FRUIT_TICKS_MAX)
        if latest_stats[stat_key] >= 10:
            latest_stats[stat_key] %= 10
            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
            exp_key = f"{FRUIT_STATS[fruit_name]}_exp"
            grade_key = f"{FRUIT_STATS[fruit_name]}_grade"
            latest_stats[exp_key] = latest_stats.get(exp_key, 0) + self.calculate_exp_gain(latest_stats.get(grade_key, 'D'))
            chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)
        else:
            chao_type, form = latest_stats.get('Type', 'Normal'), latest_stats.get('Form', '1')

        # Update inventory
        current_inventory = inventory_df.iloc[-1].to_dict()
        current_inventory[fruit_name] = int(current_inventory.get(fruit_name, 0)) - 1
        self.save_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'), inventory_df, current_inventory)

        # Save and update Chao data
        chao_stats = latest_stats.to_dict()
        self.save_chao_stats(chao_stats_path, chao_df, chao_stats)

        # Log after feeding
        print(f"[feed] After feeding {fruit_name.capitalize()} | Chao: {chao_name} | {stat_key}: {latest_stats[stat_key]} | Level: {latest_stats.get(level_key, 0)} | swim_fly: {latest_stats.get('swim_fly', 0)} | run_power: {latest_stats.get('run_power', 0)} | dark_hero: {latest_stats.get('dark_hero', 0)}")

        await self.send_embed(ctx, f"{chao_name} ate {fruit_name}!\n{chao_name}'s {stat_key.split('_')[0].capitalize()} stat has increased!\nTicks: {latest_stats[stat_key]}/10\nLevel: {latest_stats.get(level_key, 0)} (Type: {latest_stats.get('Type', 'Normal')})\n**Current Values:** swim_fly: {latest_stats.get('swim_fly', 0)}, run_power: {latest_stats.get('run_power', 0)}, dark_hero: {latest_stats.get('dark_hero', 0)}")

class StatsView(View):
    def __init__(self, chao_name, guild_id, user_id, tick_positions, exp_positions, num_images, level_position_offset, level_spacing, tick_spacing, chao_type_display, alignment_label, template_path, template_page_2_path, overlay_path, icon_path):
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

    @discord.ui.button(label="Page 1", style=discord.ButtonStyle.primary)
    async def page_1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_stats(interaction, "Page 1")

    @discord.ui.button(label="Page 2", style=discord.ButtonStyle.secondary)
    async def page_2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_stats(interaction, "Page 2")

    async def update_stats(self, interaction: discord.Interaction, page: str):
        chao_dir = self.get_path(self.guild_id, self.user_id, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = pd.read_parquet(chao_stats_path).fillna(0)
        chao_to_view = chao_df.iloc[-1].to_dict()

        print(f"[update_stats] Displaying {page} for Chao: {self.chao_name}, User: {self.user_id}")

        if page == "Page 1":
            template_path = self.TEMPLATE_PATH
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_1.png')
        else:
            template_path = self.TEMPLATE_PAGE_2_PATH
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_2.png')

        self.paste_image(template_path, self.OVERLAY_PATH, image_path, self.tick_positions,
                         chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"],
                         chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"],
                         chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"],
                         chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"],
                         chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0),
                         chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0),
                         chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))

        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=self.chao_type_display, inline=True).add_field(name="Alignment", value=self.alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://{os.path.basename(image_path)}")

        await interaction.response.edit_message(embed=embed, view=self, attachments=[
            discord.File(image_path, os.path.basename(image_path)),
            discord.File(self.ICON_PATH),
            discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
        ])

    def paste_image(self, template_path, overlay_path, output_path, tick_positions, *stats):
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA")
            # Paste EXP numbers
            for stat, exp in zip(
                    ["swim", "fly", "run", "power", "mind", "stamina"],
                    stats[-6:]):
                exp_str = f"{int(exp):04d}"
                for pos, digit in zip(
                        self.exp_positions[stat], exp_str):
                    template.paste(
                        self.num_images[digit], pos, self.num_images[digit])
            # Paste ticks
            for pos, ticks in zip(tick_positions, stats[:6]):
                for i in range(int(ticks)):
                    tick_pos = (pos[0] + i * self.tick_spacing, pos[1])
                    template.paste(overlay, tick_pos, overlay)
            # Paste levels
            for pos, level in zip(tick_positions, stats[6:12]):
                tens = int(level) // 10
                ones = int(level) % 10
                x_offset, y_offset = self.level_position_offset
                template.paste(
                    self.num_images[str(tens)],
                    (pos[0] + x_offset, pos[1] + y_offset),
                    self.num_images[str(tens)])
                template.paste(
                    self.num_images[str(ones)],
                    (pos[0] + x_offset + self.level_spacing,
                     pos[1] + y_offset),
                    self.num_images[str(ones)])
            template.save(output_path)

    def get_path(self, guild_id, user_id, folder, filename):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../database', guild_id, user_id, folder)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

async def setup(bot):
    await bot.add_cog(Chao(bot))
