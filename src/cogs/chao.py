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
    TEMPLATE_PATH = "../assets/graphics/cards/stats_page_1.png"
    TEMPLATE_PAGE_2_PATH = "../assets/graphics/cards/stats_page_2.png"
    OVERLAY_PATH = "../assets/graphics/ticks/tick_filled.png"
    OUTPUT_PATH = "./output_image.png"
    ICON_PATH = "../assets/graphics/icons/Stats.png"
    NEUTRAL_PATH = "../assets/chao/normal/neutral/neutral_normal_1.png"
    DARK_PATH = "../assets/chao/normal/dark/dark_normal_1.png"
    HERO_PATH = "../assets/chao/normal/hero/hero_normal_1.png"
    BACKGROUND_PATH = "../assets/graphics/thumbnails/neutral_background.png"
    TICK_SPACING = 105
    LEVEL_POSITION_OFFSET = (826, -106)
    LEVEL_SPACING = 60
    TICK_POSITIONS = [(446, 1176), (446, 315), (446, 1747), (446, 591), (446, 883), (446, 1469)]
    EXP_POSITIONS = {stat: [(183 + i * 60, y) for i in range(4)] for stat, y in zip(['swim', 'fly', 'run', 'power', 'mind', 'stamina'], [302, 576, 868, 1161, 1454, 1732])}
    GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
    GRADE_TO_VALUE = {'F': -1, 'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'X': 6}
    CUSTOM_EMOJI_ID = 1176313914464681984

    def __init__(self, bot):
        self.bot, self.embed_color = bot, discord.Color.blue()
        self.fruits = [{"emoji": emoji, "name": name} for emoji, name in zip("���������������", ["Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit", "Heart Fruit", "Square Fruit", "Chao Fruit", "Smart Fruit", "Power Fruit", "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"])]
        self.fruit_prices, self.chao_names = 15, ["Chaoko", "Chaolin", "Chow", "Chaoblin", "Count Chaocula", "Chaozil", "Chaos", "Chaoz"]
        self.current_date, self.num_images = datetime.now().date(), {str(i): Image.open(f"../assets/resized/{i}.png") for i in range(10)}

    def get_path(self, guild_id, user_id, folder, filename):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../database', guild_id, user_id, folder)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    def save_inventory(self, path, inventory_df, current_inventory):
        current_inventory.setdefault('Chao Egg', 0)
        pd.concat([inventory_df[inventory_df['date'] != self.current_date.strftime("%Y-%m-%d")], pd.DataFrame([{**{'date': self.current_date.strftime("%Y-%m-%d")}, **{key: value or 0 for key, value in current_inventory.items()}}])], ignore_index=True).fillna(0).to_parquet(path, index=False)

    def load_inventory(self, path): 
        return pd.read_parquet(path).fillna(0).assign(**{'Chao Egg': lambda df: df['Chao Egg'].fillna(0)}) if os.path.exists(path) else pd.DataFrame({'date': [self.current_date.strftime("%Y-%m-%d")], 'rings': [0], 'Chao Egg': [0], 'Garden Fruit': [0]})

    def is_user_initialized(self, guild_id, user_id): 
        return os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../database', guild_id, user_id))

    def calculate_exp_gain(self, grade): return (self.GRADE_TO_VALUE[grade] * 3) + 13

    def combine_images(self, background_path, overlay_path, output_path):
        with Image.open(background_path).convert("RGBA") as background:
            with Image.open(overlay_path).convert("RGBA") as overlay:
                combined = Image.alpha_composite(background, overlay)
                combined.save(output_path)

    def paste_image(self, template_path, overlay_path, output_path, tick_positions, *stats):
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA")
            [template.paste(self.num_images[digit], pos, self.num_images[digit]) for stat, exp in zip(["swim", "fly", "run", "power", "mind", "stamina"], stats[-6:]) for pos, digit in zip(self.EXP_POSITIONS[stat], f"{exp:04d}")]
            [template.paste(overlay, (pos[0] + i * self.TICK_SPACING, pos[1]), overlay) for pos, ticks in zip(tick_positions, stats[:6]) for i in range(ticks)]
            [template.paste(self.num_images[str(level // 10)], (pos[0] + self.LEVEL_POSITION_OFFSET[0], pos[1] + self.LEVEL_POSITION_OFFSET[1]), self.num_images[str(level // 10)]) or template.paste(self.num_images[str(level % 10)], (pos[0] + self.LEVEL_POSITION_OFFSET[0] + self.LEVEL_SPACING, pos[1] + self.LEVEL_POSITION_OFFSET[1]), self.num_images[str(level % 10)]) for pos, level in zip(tick_positions, stats[6:12])]
            template.save(output_path)

    def change_image_hue(self, image_path, output_path, hue, saturation):
        img = ImageEnhance.Color(Image.fromarray(np.stack([(hue * np.ones_like(h)).astype(np.uint8), s, v], axis=-1), 'HSV').convert('RGBA').enhance(saturation))
        img.save(output_path)


    def update_chao_type_and_thumbnail(self, guild_id, user_id, chao_name, chao_df):
        try:
            print(f"[update_chao_type_and_thumbnail] Updating Chao: {chao_name}")
            chao_dir = self.get_path(guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')
            stat_levels = {stat: chao_df.iloc[0][f'{stat}_level'] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']}
            max_stat = max(stat_levels, key=stat_levels.get)
            max_level = stat_levels[max_stat]
            swim_fly = chao_df.iloc[0]['swim_fly']
            run_power = chao_df.iloc[0]['run_power']
            dark_hero = chao_df.iloc[0]['dark_hero']
            current_form = chao_df.iloc[0].get('Form', "1")

            print(f"[update_chao_type_and_thumbnail] Current Form: {current_form}, Max Level: {max_level}, Max Stat: {max_stat}")

            if current_form in ["1", "2"]:
                if dark_hero >= HERO_ALIGNMENT:
                    alignment = "hero"
                elif dark_hero <= DARK_ALIGNMENT:
                    alignment = "dark"
                else:
                    alignment = "neutral"
            else:
                alignment = "hero" if dark_hero >= HERO_ALIGNMENT else "dark" if dark_hero <= DARK_ALIGNMENT else "neutral"

            chao_type = chao_df.iloc[0]['Type']
            form = current_form

            if max_level >= FORM_LEVEL_4:
                form = "4"
            elif max_level >= FORM_LEVEL_3:
                form = "3"
            elif max_level >= FORM_LEVEL_2:
                form = "2"
            else:
                form = "1"

            print(f"[update_chao_type_and_thumbnail] Determined Form: {form}, Alignment: {alignment}")

            if form == "1":
                chao_type = "normal"
                thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_1.png"
            elif form == "2":
                chao_type = "normal"
                if run_power == 5:
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_power_2.png"
                elif run_power == -5:
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_run_2.png"
                elif swim_fly == 5:
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_fly_2.png"
                elif swim_fly == -5:
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_swim_2.png"
                else:
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_normal_2.png"
            elif form == "3":
                if chao_type not in ["fly", "swim", "power", "run"]:
                    if swim_fly == 5:
                        chao_type = "fly"
                    elif swim_fly == -5:
                        chao_type = "swim"
                    elif run_power == 5:
                        chao_type = "power"
                    elif run_power == -5:
                        chao_type = "run"
                    else:
                        chao_type = "normal"
                thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/{chao_type}/{alignment}/{alignment}_{chao_type}_3.png"
            elif form == "4":
                allowed_transforms = {
                    "run": ["run_run_4", "run_power_4", "run_swim_4", "run_fly_4", "run_normal_4"],
                    "power": ["power_run_4", "power_power_4", "power_swim_4", "power_fly_4", "power_normal_4"],
                    "swim": ["swim_run_4", "swim_power_4", "swim_swim_4", "swim_fly_4", "swim_normal_4"],
                    "fly": ["fly_run_4", "fly_power_4", "fly_swim_4", "fly_fly_4", "fly_normal_4"],
                    "normal": ["normal_run_4", "normal_power_4", "normal_swim_4", "normal_fly_4", "normal_normal_4"],
                }

                base_type = chao_type
                if run_power == 5:
                    new_type = "power"
                elif run_power == -5:
                    new_type = "run"
                elif swim_fly == 5:
                    new_type = "fly"
                elif swim_fly == -5:
                    new_type = "swim"
                else:
                    new_type = "normal"

                new_form = f"{base_type}_{new_type}_4"

                if new_form in allowed_transforms.get(base_type, []):
                    chao_type = base_type
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/{base_type}/{alignment}/{alignment}_{new_form}.png"
                else:
                    chao_type = base_type
                    new_form = f"{base_type}_{base_type}_4"
                    thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/{base_type}/{alignment}/{alignment}_{new_form}.png"
            else:
                # Default to form 1 normal chao
                chao_type = "normal"
                form = "1"
                thumbnail_image = f"C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/normal/{alignment}/{alignment}_normal_1.png"

            print(f"[update_chao_type_and_thumbnail] Chao Type: {chao_type}, Thumbnail Image: {thumbnail_image}")

            # Check if the thumbnail image exists
            if not os.path.exists(thumbnail_image):
                print(f"[update_chao_type_and_thumbnail] Sprite image not found at {thumbnail_image}, using default 'chao_missing.png'.")
                thumbnail_image = "C:/Users/You/Documents/GitHub/Chao-Bot/assets/chao/chao_missing.png"

            # Combine images and save
            self.combine_images(self.BACKGROUND_PATH, thumbnail_image, thumbnail_path)
            print(f"[update_chao_type_and_thumbnail] Thumbnail created at {thumbnail_path}")

            # Use .loc[] to assign multiple values
            chao_df.loc[0, ['Type', 'Form']] = [chao_type, form]
            chao_df.to_parquet(os.path.join(chao_dir, f'{chao_name}_stats.parquet'), index=False)
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
        if await self.initialize_inventory(ctx, str(ctx.guild.id), str(ctx.author.id), "Welcome to Chao Bot!",
                                        "**You Receive:**\n- `1x Chao Egg`\n- `500x Rings`\n- `5x Garden Nut`\n\n"
                                        "**Example Commands:**\n- `$feed [Chao name] [item]` to feed your Chao.\n- `$race [Chao name]` to enter your Chao in a race.\n- `$train [Chao name] [stat]` to train a specific stat.\n- `$stats [Chao name]` to view your Chao's stats."): return

    async def hatch(self, ctx):
        print(f"[hatch] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        if (chao_egg_quantity := int(inventory_df.iloc[-1].get('Chao Egg', 0))) < 1:
            print(f"[hatch] No Chao Egg available for User: {user_id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")
        chao_dir, chao_name = self.get_path(guild_id, user_id, 'chao_data', ''), random.choice(self.chao_names)
        os.makedirs(chao_dir, exist_ok=True)
        while chao_name in [name for name in os.listdir(chao_dir) if os.path.isdir(os.path.join(chao_dir, name))]:
            chao_name = random.choice(self.chao_names)
        chao_path = os.path.join(self.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        os.makedirs(os.path.dirname(chao_path), exist_ok=True)
        inventory_df.at[inventory_df.index[-1], 'Chao Egg'] = chao_egg_quantity - 1
        self.save_inventory(file_path, inventory_df, inventory_df.iloc[-1].to_dict())

        # Ensure 'Form' is initialized as "1" during Chao creation
        chao_stats = {
            'hatched': [1],
            'birth_date': [self.current_date.strftime("%Y-%m-%d")],
            'hp_ticks': [0],
            'Form': ['1'],  # Initialize Form as "1"
            **{f"{stat}_ticks": [0] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            **{f"{stat}_level": [0] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            **{f"{stat}_exp": [0] for stat in ['swim', 'fly', 'run', 'power', 'mind', 'stamina']},
            **{f"{stat}_grade": ['D'] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
            'evolved': [False],
            'Type': ['Normal'],
            'swim_fly': [0],
            'run_power': [0],
            'dark_hero': [0],  # Initialize dark_hero as 0
        }

        pd.DataFrame(chao_stats).to_parquet(chao_path, index=False)
        await ctx.reply(file=discord.File(self.NEUTRAL_PATH, filename="neutral_normal_1.png"),
                        embed=discord.Embed(title="Your Chao Egg has hatched!", description=f"Your Chao Egg has hatched into a Regular Two-tone Chao named {chao_name}!", color=discord.Color.blue()).set_image(url="attachment://neutral_normal_1.png"))
        print(f"[hatch] Chao Egg hatched into {chao_name} for User: {user_id}. Chao data saved to {chao_path}")


    async def market(self, ctx):
        print(f"[market] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        embed = discord.Embed(title="**Black Market**", description="**Here's what you can buy:**", color=self.embed_color)
        custom_emoji = f'<:custom_emoji:{self.CUSTOM_EMOJI_ID}>'
        for i in range(len(self.fruits)):
            embed.add_field(name=f'**{self.fruits[i]["emoji"]} {self.fruits[i]["name"]}**', value=f'**{custom_emoji} x {self.fruit_prices}**', inline=True)
        await ctx.send(embed=embed)
        print(f"[market] Market items displayed to User: {ctx.author.id}")

    async def give_rings(self, ctx):
        print(f"[give_rings] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.load_inventory(file_path)
        rings = inventory_df.iloc[-1]['rings'] + 1000
        self.save_inventory(file_path, inventory_df, {'rings': rings, **{fruit['name']: int(inventory_df.iloc[-1].get(fruit['name'], 0)) for fruit in self.fruits}})
        await self.send_embed(ctx, f"{ctx.author.mention} has been given 1000 rings! Your current rings: {rings}")
        print(f"[give_rings] 1000 Rings added to User: {user_id}. New balance: {rings}")

    async def buy(self, ctx, *, item_quantity: str):
        print(f"[buy] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        try: *item_name_parts, quantity = item_quantity.rsplit(' ', 1); item_name, quantity = ' '.join(item_name_parts), int(quantity)
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
        current_inventory = {'rings': rings - total_cost, **{fruit_item['name']: int(inventory_df.iloc[-1].get(fruit_item['name'], 0)) + (quantity if fruit_item == fruit else 0) for fruit_item in self.fruits}, 'Chao Egg': int(inventory_df.iloc[-1].get('Chao Egg', 0))}
        self.save_inventory(file_path, inventory_df, current_inventory)
        await self.send_embed(ctx, f"{ctx.author.mention} has purchased {quantity} '{fruit['name']}(s)' for {total_cost} rings! You now have {current_inventory['rings']} rings.")
        print(f"[buy] User: {ctx.author.id} bought {quantity}x {fruit['name']} for {total_cost} rings. Remaining rings: {current_inventory['rings']}")

    async def inventory(self, ctx):
        print(f"[inventory] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_df = self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0)
        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.embed_color).add_field(name='Rings', value=f'{int(inventory_df.iloc[-1]["rings"])}', inline=False).add_field(name='Last Updated', value=f'{inventory_df.iloc[-1]["date"]}', inline=False)
        [embed.add_field(name=f'{fruit["emoji"]} {fruit["name"]}', value=f'Quantity: {int(inventory_df.iloc[-1].get(fruit["name"], 0))}', inline=True) for fruit in self.fruits if fruit["name"] in inventory_df.columns and int(inventory_df.iloc[-1].get(fruit["name"], 0)) > 0]
        chao_egg_quantity = int(inventory_df.iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity > 0: embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {chao_egg_quantity}', inline=True)
        await ctx.send(embed=embed)
        print(f"[inventory] Inventory displayed for User: {ctx.author.id}")

    async def restore(self, ctx, *, args: str):
        print(f"[restore] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        parts = args.split()
        if len(parts) != 2 or parts[0].lower() != 'inventory':
            print(f"[restore] Invalid input: {args} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, please use the command in the format: $restore inventory YYYY-MM-DD")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        try: restore_date = datetime.strptime(parts[1], "%Y-%m-%d").date()
        except ValueError: 
            print(f"[restore] Invalid date format: {parts[1]} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")
        inventory_df = self.load_inventory(file_path)
        if parts[1] not in inventory_df['date'].values:
            print(f"[restore] No data found for date: {parts[1]} by User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, no inventory data found for {parts[1]}.")
        restored_inventory, current_date_str = inventory_df[inventory_df['date'] == parts[1]].iloc[0].to_dict(), self.current_date.strftime("%Y-%m-%d")
        restored_inventory['date'] = current_date_str
        pd.concat([inventory_df[inventory_df['date'] != current_date_str], pd.DataFrame([restored_inventory])], ignore_index=True).to_parquet(file_path, index=False)
        await self.send_embed(ctx, f"{ctx.author.mention}, your inventory has been restored to the state from {parts[1]}.")
        print(f"[restore] Inventory restored to {parts[1]} for User: {ctx.author.id}")

    async def give_egg(self, ctx):
        print(f"[give_egg] Command called by User: {ctx.author.id} in Guild: {ctx.guild.id}")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df, chao_egg_quantity = self.load_inventory(file_path), int(self.load_inventory(file_path).iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity >= 1: 
            print(f"[give_egg] User: {ctx.author.id} already has a Chao Egg.")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg! Hatch it first before receiving another one.")
        self.save_inventory(file_path, inventory_df, {'Chao Egg': chao_egg_quantity + 1, 'rings': int(inventory_df.iloc[-1]['rings']), **{fruit['name']: int(inventory_df.iloc[-1].get(fruit['name'], 0)) for fruit in self.fruits}})
        await self.send_embed(ctx, f"{ctx.author.mention} has received a Chao Egg! You now have {chao_egg_quantity + 1} Chao Egg(s).")
        print(f"[give_egg] Chao Egg given to User: {ctx.author.id}. New count: {chao_egg_quantity + 1}")

    async def stats(self, ctx, *, chao_name: str):
        print(f"[stats] Command called by User: {ctx.author.id} for Chao: {chao_name} in Guild: {ctx.guild.id}")
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir, chao_stats_path = self.get_path(guild_id, user_id, 'chao_data', chao_name), os.path.join(self.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            print(f"[stats] Chao {chao_name} not found for User: {ctx.author.id}")
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

        chao_df = pd.read_parquet(chao_stats_path).fillna(0)
        chao_to_view, (chao_type, form) = chao_df.iloc[0].to_dict(), self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)

        if form in ["1", "2"]:
            chao_type_display = "Normal"
        elif form == "3":
            chao_type_display = chao_type
        else:
            chao_type_display = chao_type.replace("_", "/")

        chao_df.to_parquet(chao_stats_path, index=False)
        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")

        # Determine alignment based on dark_hero value
        dark_hero = chao_to_view.get('dark_hero', 0)
        alignment_label = "Hero" if dark_hero >= HERO_ALIGNMENT else "Dark" if dark_hero <= DARK_ALIGNMENT else "Neutral"

        self.paste_image(self.TEMPLATE_PATH, self.OVERLAY_PATH, os.path.join(chao_dir, f'{chao_name}_stats.png'), self.TICK_POSITIONS, chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"], chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"], chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"], chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"], chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0), chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0), chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))
        embed.add_field(name="Type", value=chao_type_display, inline=True).add_field(name="Alignment", value=alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://output_image.png")

        view = StatsView(chao_name, guild_id, user_id, self.TICK_POSITIONS, self.EXP_POSITIONS, self.num_images, self.LEVEL_POSITION_OFFSET, self.LEVEL_SPACING, self.TICK_SPACING, chao_type_display)

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
        
        # Attempt to match the last word with a fruit name
        fruit_name = None
        chao_name = None

        # Check if the last part is a fruit name
        for i in range(1, len(parts) + 1):
            potential_fruit_name = ' '.join(parts[-i:])
            fruit_name_match = next((fruit_item['name'] for fruit_item in self.fruits if fruit_item['name'].lower() == potential_fruit_name.lower()), None)
            if fruit_name_match:
                fruit_name = fruit_name_match
                chao_name = ' '.join(parts[:-i])
                break
        
        if not chao_name or not fruit_name:
            return await self.send_embed(ctx, f"{ctx.author.mention}, please provide both a valid Chao name and a fruit.")

        chao_dir_path, chao_stats_path = self.get_path(guild_id, user_id, 'chao_data', chao_name), os.path.join(self.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path): 
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")

        chao_df, inventory_df, fruit = pd.read_parquet(chao_stats_path).fillna(0), self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0), next((fruit_item for fruit_item in self.fruits if fruit_item['name'].lower() == fruit_name.lower()), None)

        if not fruit or fruit['name'] not in inventory_df.columns or int(inventory_df.iloc[-1].get(fruit['name'], 0)) <= 0: 
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any {fruit_name} to feed your Chao.")

        # Log before feeding
        print(f"[feed] Command called by User: {user_id} for Chao: {chao_name} with Fruit: {fruit_name} in Guild: {guild_id}")
        print(f"[feed] Before feeding {fruit_name.capitalize()} | Chao: {chao_name} | {FRUIT_STATS[fruit_name]}_ticks: {chao_df.at[0, f'{FRUIT_STATS[fruit_name]}_ticks']} | Level: {chao_df.at[0, f'{FRUIT_STATS[fruit_name]}_level']} | swim_fly: {chao_df.at[0, 'swim_fly']} | run_power: {chao_df.at[0, 'run_power']}")

        # Adjust swim_fly and run_power according to the logic
        if fruit_name.lower() == 'swim fruit':
            chao_df.at[0, 'swim_fly'] = max(-5, chao_df.at[0, 'swim_fly'] - 1)
            if chao_df.at[0, 'run_power'] > 0:
                chao_df.at[0, 'run_power'] -= 1
            elif chao_df.at[0, 'run_power'] < 0:
                chao_df.at[0, 'run_power'] += 1
        elif fruit_name.lower() == 'fly fruit':
            chao_df.at[0, 'swim_fly'] = min(5, chao_df.at[0, 'swim_fly'] + 1)
            if chao_df.at[0, 'run_power'] > 0:
                chao_df.at[0, 'run_power'] -= 1
            elif chao_df.at[0, 'run_power'] < 0:
                chao_df.at[0, 'run_power'] += 1
        elif fruit_name.lower() == 'run fruit':
            chao_df.at[0, 'run_power'] = max(-5, chao_df.at[0, 'run_power'] - 1)
            if chao_df.at[0, 'swim_fly'] > 0:
                chao_df.at[0, 'swim_fly'] -= 1
            elif chao_df.at[0, 'swim_fly'] < 0:
                chao_df.at[0, 'swim_fly'] += 1
        elif fruit_name.lower() == 'power fruit':
            chao_df.at[0, 'run_power'] = min(5, chao_df.at[0, 'run_power'] + 1)
            if chao_df.at[0, 'swim_fly'] > 0:
                chao_df.at[0, 'swim_fly'] -= 1
            elif chao_df.at[0, 'swim_fly'] < 0:
                chao_df.at[0, 'swim_fly'] += 1

        # Adjust dark_hero based on Hero or Dark Fruit
        if fruit_name.lower() == 'hero fruit':
            chao_df.at[0, 'dark_hero'] = min(5, chao_df.at[0, 'dark_hero'] + 1)  # Increase dark_hero value
        elif fruit_name.lower() == 'dark fruit':
            chao_df.at[0, 'dark_hero'] = max(-5, chao_df.at[0, 'dark_hero'] - 1)  # Decrease dark_hero value

        # Update stat ticks and level
        stat_key = f"{FRUIT_STATS[fruit['name']]}_ticks"
        chao_df.at[0, stat_key] += random.randint(FRUIT_TICKS_MIN, FRUIT_TICKS_MAX)
        if chao_df.at[0, stat_key] >= 10:
            chao_df.at[0, stat_key] %= 10
            chao_df.at[0, f"{FRUIT_STATS[fruit_name]}_level"] += 1
            chao_df.at[0, f"{FRUIT_STATS[fruit_name]}_exp"] += self.calculate_exp_gain(chao_df.at[0, f"{FRUIT_STATS[fruit_name]}_grade"])
            chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)
        else:
            chao_type, form = chao_df.at[0, 'Type'], chao_df.at[0, 'Form']

        # Construct the sprite path
        sprite_path = f"../assets/chao/{chao_type}/neutral/neutral_{chao_type}_{form}.png"
        print(f"[feed] Using sprite image: {sprite_path}")

        # Save and update Chao data
        self.save_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'), inventory_df, inventory_df.iloc[-1].to_dict())
        chao_df.to_parquet(chao_stats_path, index=False)

        # Log after feeding
        print(f"[feed] After feeding {fruit_name.capitalize()} | Chao: {chao_name} | {FRUIT_STATS[fruit_name]}_ticks: {chao_df.at[0, stat_key]} | Level: {chao_df.at[0, f'{FRUIT_STATS[fruit_name]}_level']} | swim_fly: {chao_df.at[0, 'swim_fly']} | run_power: {chao_df.at[0, 'run_power']} | dark_hero: {chao_df.at[0, 'dark_hero']}")

        await self.send_embed(ctx, f"{chao_name} ate {fruit_name}!\n{chao_name}'s {stat_key.split('_')[0].capitalize()} stat has increased!\nTicks: {chao_df.at[0, stat_key]}/10\nLevel: {chao_df.at[0, f'{FRUIT_STATS[fruit_name]}_level']} (Type: {chao_df.at[0, 'Type']})\n**Current Values:** swim_fly: {chao_df.at[0, 'swim_fly']}, run_power: {chao_df.at[0, 'run_power']}, dark_hero: {chao_df.at[0, 'dark_hero']}")

class StatsView(View):
    def __init__(self, chao_name, guild_id, user_id, tick_positions, exp_positions, num_images, level_position_offset, level_spacing, tick_spacing, chao_type_display):
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
        chao_to_view = chao_df.iloc[0].to_dict()

        print(f"[update_stats] Displaying {page} for Chao: {self.chao_name}, User: {self.user_id}")

        if page == "Page 1":
            template_path = "../assets/graphics/cards/stats_page_1.png"
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_1.png')
            self.paste_image(template_path, "../assets/graphics/ticks/tick_filled.png", image_path, self.tick_positions,
                             chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"],
                             chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"],
                             chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"],
                             chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"],
                             chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0),
                             chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0),
                             chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))
        else:
            template_path = "../assets/graphics/cards/stats_page_2.png"
            image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_2.png')
            self.paste_image(template_path, "../assets/graphics/ticks/tick_filled.png", image_path, self.tick_positions,
                             chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"],
                             chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"],
                             chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"],
                             chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"],
                             chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0),
                             chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0),
                             chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))

        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
        alignment_label = "Hero" if chao_to_view.get('alignment', 0) >= 5 else "Dark" if chao_to_view.get('alignment', 0) <= -5 else "Neutral"
        embed.add_field(name="Type", value=self.chao_type_display, inline=True).add_field(name="Alignment", value=alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://{os.path.basename(image_path)}")

        await interaction.response.edit_message(embed=embed, view=self, attachments=[
            discord.File(image_path, os.path.basename(image_path)),
            discord.File("../assets/graphics/icons/Stats.png"),
            discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
        ])

    def paste_image(self, template_path, overlay_path, output_path, tick_positions, *stats):
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA")
            [template.paste(self.num_images[digit], pos, self.num_images[digit]) for stat, exp in zip(["swim", "fly", "run", "power", "mind", "stamina"], stats[-6:]) for pos, digit in zip(self.exp_positions[stat], f"{exp:04d}")]
            [template.paste(overlay, (pos[0] + i * self.tick_spacing, pos[1]), overlay) for pos, ticks in zip(tick_positions, stats[:6]) for i in range(ticks)]
            [template.paste(self.num_images[str(level // 10)], (pos[0] + self.level_position_offset[0], pos[1] + self.level_position_offset[1]), self.num_images[str(level // 10)]) or template.paste(self.num_images[str(level % 10)], (pos[0] + self.level_position_offset[0] + self.level_spacing, pos[1] + self.level_position_offset[1]), self.num_images[str(level % 10)]) for pos, level in zip(tick_positions, stats[6:12])]
            template.save(output_path)

    def get_path(self, guild_id, user_id, folder, filename):
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../database', guild_id, user_id, folder)
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

async def setup(bot): 
    await bot.add_cog(Chao(bot))
