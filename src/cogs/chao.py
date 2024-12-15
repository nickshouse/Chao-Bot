import os
import json
import discord
from discord.ext import commands
from datetime import datetime
import random
from discord.ui import View  # Add this line


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

    @discord.ui.button(label="Page 1", style=discord.ButtonStyle.primary, custom_id="stats_page_1")
    async def page_1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_stats(interaction, "Page 1")

    @discord.ui.button(label="Page 2", style=discord.ButtonStyle.secondary, custom_id="stats_page_2")
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

        embed = discord.Embed(color=discord.Color.blue()).set_author(
            name=f"{self.chao_name}'s Stats",
            icon_url="attachment://Stats.png"
        )
        embed.add_field(name="Type", value=self.chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=self.alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url=f"attachment://{os.path.basename(image_path)}")

        await interaction.response.edit_message(embed=embed, view=self, attachments=[
            discord.File(image_path, os.path.basename(image_path)),
            discord.File(self.ICON_PATH, filename="Stats.png"),
            discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
        ])


class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        self.image_utils = self.data_utils = None
        self.market_message_id = None

        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)

        self.FORM_LEVELS = config['FORM_LEVELS']
        self.ALIGNMENTS = config['ALIGNMENTS']
        self.FRUIT_TICKS_RANGE = config['FRUIT_TICKS_RANGE']
        self.FRUIT_STATS = config['FRUIT_STATS']

        self.FORM_LEVEL_2 = self.FORM_LEVELS[0]
        self.FORM_LEVEL_3 = self.FORM_LEVELS[1]
        self.FORM_LEVEL_4 = self.FORM_LEVELS[2]
        self.HERO_ALIGNMENT = self.ALIGNMENTS['hero']
        self.DARK_ALIGNMENT = self.ALIGNMENTS['dark']
        self.FRUIT_TICKS_MIN = self.FRUIT_TICKS_RANGE[0]
        self.FRUIT_TICKS_MAX = self.FRUIT_TICKS_RANGE[1]

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

        self.RUN_POWER_THRESHOLD = 5
        self.SWIM_FLY_THRESHOLD = 5

        self.assets_dir = None
        self.TEMPLATE_PATH = None
        self.TEMPLATE_PAGE_2_PATH = None
        self.OVERLAY_PATH = None
        self.ICON_PATH = None
        self.NEUTRAL_PATH = None
        self.BACKGROUND_PATH = None
        self.BLACK_MARKET_THUMBNAIL_PATH = None
        self.BLACK_MARKET_FRUITS_PAGE_1_PATH = None
        self.BLACK_MARKET_FRUITS_PAGE_2_PATH = None
        self.BLACK_MARKET_ICON_PATH = None
        self.TICK_POSITIONS = None
        self.EYES_DIR = None
        self.MOUTH_DIR = None

        # Just store fruit names now; no emojis
        names = [
            "Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit",
            "Heart Fruit", "Square Fruit", "Chao Fruit", "Power Fruit",
            "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"
        ]
        self.fruits = names
        self.fruit_prices = 15

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
        self.BLACK_MARKET_THUMBNAIL_PATH = os.path.join(self.assets_dir, 'graphics/thumbnails/black_market.png')
        self.BLACK_MARKET_FRUITS_PAGE_1_PATH = os.path.join(self.assets_dir, 'graphics/cards/black_market_fruits_page_1.png')
        self.BLACK_MARKET_FRUITS_PAGE_2_PATH = os.path.join(self.assets_dir, 'graphics/cards/black_market_fruits_page_2.png')
        self.BLACK_MARKET_ICON_PATH = os.path.join(self.assets_dir, 'graphics/icons/Black_Market.png')

        self.TICK_POSITIONS = [(446, y) for y in [1176, 315, 591, 883, 1469]]
        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')


    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)

    
    async def hatch(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}

        if current_inv.get('Chao Egg', 0) < 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")

        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', '')
        os.makedirs(chao_dir, exist_ok=True)
        chao_name = random.choice(self.chao_names)
        while chao_name in os.listdir(chao_dir):
            chao_name = random.choice(self.chao_names)

        chao_path = os.path.join(chao_dir, chao_name)
        os.makedirs(chao_path, exist_ok=True)
        chao_stats_path = os.path.join(chao_path, f'{chao_name}_stats.parquet')
        current_inv['Chao Egg'] = current_inv.get('Chao Egg', 0) - 1
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)

        base_stats = {f"{stat}_ticks": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run']}
        base_stats.update({f"{stat}_level": 0 for stat in ['power', 'swim', 'stamina', 'fly', 'run']})
        base_stats.update({f"{stat}_exp": 0 for stat in ['swim', 'fly', 'run', 'power', 'stamina']})
        base_stats.update({f"{stat}_grade": 'D' for stat in ['power', 'swim', 'stamina', 'fly', 'run']})

        chao_stats = {
            'date': datetime.now().date().strftime("%Y-%m-%d"),
            'hatched': 1,
            'birth_date': datetime.now().date().strftime("%Y-%m-%d"),
            'hp_ticks': 0,
            'Form': '1',
            'evolved': 0,
            'Type': 'Normal',
            'swim_fly': 0,
            'run_power': 0,
            'dark_hero': 0,
            'eyes': random.choice(self.eye_types),
            'mouth': random.choice(self.mouth_types),
            'happiness': 50,
            'mating': 0,
            'belly': 0,
            'illness': 0,
            'hp': 1000,
            **base_stats
        }

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)

        eyes, mouth = chao_stats['eyes'], chao_stats['mouth']
        alignment_str = 'neutral'
        eyes_path = os.path.join(self.EYES_DIR, f"{alignment_str}_{eyes}.png")
        if not os.path.exists(eyes_path):
            eyes_path = os.path.join(self.EYES_DIR, f"{alignment_str}.png")
        mouth_path = os.path.join(self.MOUTH_DIR, f"{mouth}.png")
        if not os.path.exists(mouth_path):
            mouth_path = os.path.join(self.MOUTH_DIR, "happy.png")

        thumbnail_path = os.path.join(chao_path, f"{chao_name}_thumbnail.png")
        self.image_utils.combine_images_with_face(
            self.BACKGROUND_PATH,
            self.NEUTRAL_PATH,
            eyes_path,
            mouth_path,
            thumbnail_path
        )

        embed = discord.Embed(
            title="Your Chao Egg has hatched!",
            description=f"Your Chao Egg hatched into a Regular Two-tone Chao named {chao_name}!",
            color=discord.Color.blue()
        ).set_image(url=f"attachment://{chao_name}_thumbnail.png")

        await ctx.reply(file=discord.File(thumbnail_path, filename=f"{chao_name}_thumbnail.png"), embed=embed)


    def update_chao_type_and_thumbnail(self, guild_id, user_id, chao_name, latest_stats):
        try:
            chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

            stat_levels = {s: latest_stats.get(f'{s}_level', 0) for s in ['power', 'swim', 'stamina', 'fly', 'run']}
            max_stat = max(stat_levels, key=stat_levels.get)
            max_level = stat_levels[max_stat]
            dark_hero = latest_stats.get('dark_hero', 0)
            form = latest_stats.get('Form', "1")
            current_type = latest_stats.get('Type', 'normal').lower()
            chao_type = current_type

            # Alignment
            if form in ["1", "2"]:
                if dark_hero >= self.HERO_ALIGNMENT:
                    alignment = "hero"
                elif dark_hero <= self.DARK_ALIGNMENT:
                    alignment = "dark"
                else:
                    alignment = "neutral"
                latest_stats['Alignment'] = alignment
            else:
                alignment = latest_stats.get('Alignment', 'neutral')

            # Evolution logic
            def evolve_to_form_2():
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                if run_power >= self.RUN_POWER_THRESHOLD:
                    return f"{current_type}_power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    return f"{current_type}_run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    return f"{current_type}_fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    return f"{current_type}_swim"
                return f"{current_type}_normal"

            def evolve_to_form_3():
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                new_type = "normal"
                if run_power >= self.RUN_POWER_THRESHOLD:
                    new_type = "power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    new_type = "run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    new_type = "fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    new_type = "swim"
                latest_stats['Alignment'] = alignment
                return new_type

            def evolve_to_form_4():
                base_type = current_type if current_type in ['power', 'run', 'swim', 'fly', 'normal'] else 'normal'
                run_power = latest_stats.get('run_power', 0)
                swim_fly = latest_stats.get('swim_fly', 0)
                second = "normal"
                if run_power >= self.RUN_POWER_THRESHOLD:
                    second = "power"
                elif run_power <= -self.RUN_POWER_THRESHOLD:
                    second = "run"
                elif swim_fly >= self.SWIM_FLY_THRESHOLD:
                    second = "fly"
                elif swim_fly <= -self.SWIM_FLY_THRESHOLD:
                    second = "swim"
                return f"{base_type}_{second}"

            if form == "1" and max_level >= self.FORM_LEVEL_2:
                form, chao_type = "2", evolve_to_form_2()
            elif form == "2" and max_level >= self.FORM_LEVEL_3:
                form, chao_type = "3", evolve_to_form_3()
            elif form == "3" and max_level >= self.FORM_LEVEL_4:
                form, chao_type = "4", evolve_to_form_4()
                if "_" not in chao_type:
                    chao_type = f"{chao_type}_normal"

            latest_stats['Type'], latest_stats['Form'] = chao_type, form

            eyes = latest_stats['eyes']
            mouth = latest_stats['mouth']
            eyes_alignment = "neutral" if form in ["1", "2"] else alignment

            def valid_path(base, name, fallback):
                p = os.path.join(base, name)
                return p if os.path.exists(p) else os.path.join(base, fallback)

            eyes_image_path = valid_path(self.EYES_DIR, f"{eyes_alignment}_{eyes}.png",
                                        f"{eyes_alignment}.png" if os.path.exists(os.path.join(self.EYES_DIR, f"{eyes_alignment}.png")) else "happy.png")
            if not os.path.exists(eyes_image_path) and "neutral_" in eyes_image_path:
                eyes_image_path = os.path.join(self.EYES_DIR, "neutral.png")

            mouth_image_path = valid_path(self.MOUTH_DIR, f"{mouth}.png", "happy.png")

            chao_image_filename = f"{alignment}_{chao_type}_{form}.png"
            base_type = chao_type.split('_')[0]
            chao_image_path = os.path.join(self.assets_dir, 'chao', base_type, alignment, chao_image_filename)
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
            return None, None

    async def give_egg(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}

        if current_inv.get('Chao Egg', 0) >= 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg!")

        current_inv['Chao Egg'] = current_inv.get('Chao Egg', 0) + 1
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)
        await self.send_embed(ctx, f"{ctx.author.mention} received a Chao Egg! You now have {current_inv['Chao Egg']} Egg(s).")
    
    async def inventory(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_df = self.data_utils.load_inventory(
            self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        ).fillna(0)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}

        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.embed_color)
        embed.add_field(name='Rings', value=str(current_inv.get("rings", 0)), inline=False)
        embed.add_field(name='Last Updated', value=current_inv.get("date", "N/A"), inline=False)

        for fruit in self.fruits:
            qty = int(current_inv.get(fruit, 0))
            if qty > 0:
                embed.add_field(name=fruit, value=f'Quantity: {qty}', inline=True)

        eggs = int(current_inv.get('Chao Egg', 0))
        if eggs > 0:
            embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {eggs}', inline=True)

        await ctx.send(embed=embed)

    
    async def stats(self, ctx, *, chao_name: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()
        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_stats)

        if form in ["1", "2"]:
            chao_type_display = "Normal"
        elif form == "4":
            chao_type_display = chao_type.replace("_", "/").capitalize()
        else:
            chao_type_display = chao_type.capitalize()

        alignment_label = chao_stats.get('Alignment', 'Neutral').capitalize()
        stats_image_path = os.path.join(chao_dir, f'{chao_name}_stats.png')

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

        embed = discord.Embed(color=self.embed_color)
        embed.set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://output_image.png")

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

        sent_message = await ctx.send(
            files=[
                discord.File(stats_image_path, "output_image.png"),
                discord.File(self.ICON_PATH),
                discord.File(os.path.join(chao_dir, f'{chao_name}_thumbnail.png'), "chao_thumbnail.png")
            ],
            embed=embed,
            view=view
        )

        self.bot.add_view(view, message_id=sent_message.id)


    
    async def feed(self, ctx, *, chao_name_and_fruit: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        parts = chao_name_and_fruit.split()

        fruit_name, chao_name = None, None
        # Identify fruit and chao name from the user input
        for i in range(1, len(parts) + 1):
            potential = ' '.join(parts[-i:])
            if any(f.lower() == potential.lower() for f in self.fruits):
                fruit_name = next(f for f in self.fruits if f.lower() == potential.lower())
                chao_name = ' '.join(parts[:-i])
                break

        if not chao_name or not fruit_name:
            return await self.send_embed(ctx, f"{ctx.author.mention}, provide a valid Chao name and fruit.")

        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        inv_df = self.data_utils.load_inventory(self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'))
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        if current_inv.get(fruit_name, 0) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you have no {fruit_name}.")

        latest_stats = chao_df.iloc[-1].copy()
        last_update = datetime.strptime(latest_stats.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        days_elapsed = (datetime.now() - last_update).days
        latest_stats['belly'] = max(0, latest_stats.get('belly', 0) - days_elapsed)
        latest_stats['date'] = datetime.now().strftime("%Y-%m-%d")

        if latest_stats['belly'] >= 10:
            return await self.send_embed(ctx, f"{ctx.author.mention}, {chao_name} is too full.")

        latest_stats['belly'] = min(10, latest_stats['belly'] + 2)
        stat_key = f"{self.FRUIT_STATS[fruit_name]}_ticks"
        level_key = f"{self.FRUIT_STATS[fruit_name]}_level"
        latest_stats[stat_key] = latest_stats.get(stat_key, 0) + random.randint(self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX)

        if latest_stats[stat_key] >= 10:
            latest_stats[stat_key] %= 10
            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
            exp_key = f"{self.FRUIT_STATS[fruit_name]}_exp"
            grade_key = f"{self.FRUIT_STATS[fruit_name]}_grade"
            latest_stats[exp_key] = latest_stats.get(exp_key, 0) + self.calculate_exp_gain(latest_stats.get(grade_key, 'D'))

        current_form = latest_stats.get('Form', '1')

        def adjust_alignment(fruit):
            if fruit.lower() == 'hero fruit':
                latest_stats['dark_hero'] = min(self.HERO_ALIGNMENT, latest_stats.get('dark_hero', 0) + 1)
            elif fruit.lower() == 'dark fruit':
                latest_stats['dark_hero'] = max(self.DARK_ALIGNMENT, latest_stats.get('dark_hero', 0) - 1)

        def adjust_stats(fruit):
            run_power = latest_stats.get('run_power', 0)
            swim_fly = latest_stats.get('swim_fly', 0)
            fname = fruit.lower()
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

        if current_form in ["1", "2"]:
            adjust_alignment(fruit_name)
        adjust_stats(fruit_name)

        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, latest_stats)

        current_inv[fruit_name] -= 1
        self.data_utils.save_inventory(self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'),
                                    inv_df, current_inv)
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats.to_dict())

        thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')
        embed = discord.Embed(
            description=f"{chao_name} ate {fruit_name}!\n"
                        f"{chao_name}'s {stat_key.split('_')[0].capitalize()} stat increased!\n"
                        f"Ticks: {latest_stats[stat_key]}/10\n"
                        f"Level: {latest_stats.get(level_key, 0)} (Type: {latest_stats.get('Type', 'Normal')})\n"
                        f"Belly: {latest_stats['belly']}/10\n"
                        f"**Current Values:** swim_fly: {latest_stats.get('swim_fly', 0)}, run_power: {latest_stats.get('run_power', 0)}, dark_hero: {latest_stats.get('dark_hero', 0)}",
            color=self.embed_color
        ).set_image(url=f"attachment://{chao_name}_thumbnail.png")
        await ctx.send(file=discord.File(thumbnail_path, filename=f"{chao_name}_thumbnail.png"), embed=embed)

async def setup(bot):
    await bot.add_cog(Chao(bot))
