import os, json, random, asyncio, discord, pandas as pd
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class StatsView(View):
    def __init__(
        self,
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
        total_pages: int = 2
    ):
        super().__init__(timeout=None)
        attrs = [
            'chao_name', 'sanitized_chao_name', 'guild_id', 'user_id',
            'page1_tick_positions', 'page2_tick_positions', 'exp_positions',
            'num_images', 'level_position_offset', 'level_spacing',
            'tick_spacing', 'chao_type_display', 'alignment_label',
            'TEMPLATE_PATH', 'TEMPLATE_PAGE_2_PATH', 'OVERLAY_PATH',
            'ICON_PATH', 'image_utils', 'data_utils', 'total_pages',
            'current_page'
        ]
        values = [
            chao_name, chao_name.replace(" ", "_"), guild_id, user_id,
            page1_tick_positions, page2_tick_positions, exp_positions,
            num_images, level_position_offset, level_spacing,
            tick_spacing, chao_type_display, alignment_label,
            template_path, template_page_2_path, overlay_path,
            icon_path, image_utils, data_utils, total_pages,
            1
        ]
        for attr, value in zip(attrs, values):
            setattr(self, attr, value)

        # Add navigation buttons with custom_id
        self.add_item(self.create_button("⬅️", self.previous_page, custom_id=f"{chao_name}_prev"))
        self.add_item(self.create_button("➡️", self.next_page, custom_id=f"{chao_name}_next"))

    def create_button(self, emoji: str, callback, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = callback
        return button

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page - 1 if self.current_page > 1 else self.total_pages
        await self.update_stats(interaction, f"Page {self.current_page}")

    async def next_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page + 1 if self.current_page < self.total_pages else 1
        await self.update_stats(interaction, f"Page {self.current_page}")

    async def update_stats(self, interaction: discord.Interaction, page: str):
        chao_dir = self.data_utils.get_path(self.guild_id, self.user_id, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)

        if chao_df.empty:
            await interaction.response.send_message("No stats data available for this Chao.", ephemeral=True)
            return

        chao_to_view = {
            "power_ticks": 0, "swim_ticks": 0, "fly_ticks": 0, "run_ticks": 0, "stamina_ticks": 0,
            "happiness_ticks": 0, "illness_ticks": 0, "energy_ticks": 0, "hp_ticks": 0,
            "power_level": 0, "swim_level": 0, "fly_level": 0, "run_level": 0, "stamina_level": 0,
            "power_exp": 0, "swim_exp": 0, "fly_exp": 0, "run_exp": 0, "stamina_exp": 0,
            **chao_df.iloc[-1].to_dict()
        }

        image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_{self.current_page}.png')
        footer_text = f"Page {self.current_page} / {self.total_pages}"

        if self.current_page == 1:
            await asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.TEMPLATE_PATH,
                self.OVERLAY_PATH,
                image_path,
                self.page1_tick_positions,
                chao_to_view["power_ticks"],
                chao_to_view["swim_ticks"],
                chao_to_view["fly_ticks"],
                chao_to_view["run_ticks"],
                chao_to_view["stamina_ticks"],
                chao_to_view["power_level"],
                chao_to_view["swim_level"],
                chao_to_view["fly_level"],
                chao_to_view["run_level"],
                chao_to_view["stamina_level"],
                chao_to_view["power_exp"],
                chao_to_view["swim_exp"],
                chao_to_view["fly_exp"],
                chao_to_view["run_exp"],
                chao_to_view["stamina_exp"]
            )
        else:
            stats_positions_page2 = {
                'happiness': (272, 590),
                'illness': (272, 882),
                'energy': (272, 1175),
                'hp': (272, 1468),
                'belly': (272, 314)  # Belly tick position
            }

            stats_values_page2 = {
                stat: chao_to_view.get(f"{stat}_ticks", 0)
                for stat in stats_positions_page2
            }

            # Generate the stats page 2 image with percentages
            await asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.TEMPLATE_PAGE_2_PATH,
                self.OVERLAY_PATH,
                image_path,
                stats_positions_page2,
                stats_values_page2
            )


        chao_type_display = "Normal" if chao_to_view.get("Form") in ["1", "2"] else chao_to_view.get("Type", "Normal").replace("_", "/").capitalize()
        alignment_label = chao_to_view.get('Alignment', 'Neutral').capitalize()
        sanitized_chao_name = self.chao_name.replace(" ", "_")

        embed = discord.Embed(color=discord.Color.blue()).set_author(
            name=f"{self.chao_name}'s Stats",
            icon_url="attachment://Stats.png"
        ).add_field(name="Type", value=chao_type_display, inline=True)\
         .add_field(name="Alignment", value=alignment_label, inline=True)\
         .set_thumbnail(url="attachment://chao_thumbnail.png")\
         .set_image(url="attachment://stats_page.png")\
         .set_footer(text=footer_text)

        try:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[
                discord.File(image_path, "stats_page.png"),
                discord.File(self.ICON_PATH, filename="Stats.png"),
                discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png")
            ])
        except Exception as e:
            print(f"[update_stats] Failed to edit message: {e}")
            await interaction.response.send_message("An error occurred while updating the stats.", ephemeral=True)


class Chao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        self.image_utils = self.data_utils = None
        self.market_message_id = None

        # Load configuration
        with open('config.json') as f:
            config = json.load(f)

        self.FORM_LEVEL_2, self.FORM_LEVEL_3, self.FORM_LEVEL_4 = config['FORM_LEVELS']
        self.HERO_ALIGNMENT, self.DARK_ALIGNMENT = config['ALIGNMENTS']['hero'], config['ALIGNMENTS']['dark']
        self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX = config['FRUIT_TICKS_RANGE']
        self.FRUIT_STATS = config['FRUIT_STATS']

        self.GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        self.GRADE_TO_VALUE = {grade: val for grade, val in zip(self.GRADES, range(-1, 7))}
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

        self.assets_dir = self.TEMPLATE_PATH = self.TEMPLATE_PAGE_2_PATH = self.OVERLAY_PATH = self.ICON_PATH = None
        self.NEUTRAL_PATH = self.BACKGROUND_PATH = self.BLACK_MARKET_THUMBNAIL_PATH = None
        self.BLACK_MARKET_FRUITS_PAGE_1_PATH = self.BLACK_MARKET_FRUITS_PAGE_2_PATH = self.BLACK_MARKET_ICON_PATH = None
        self.PAGE1_TICK_POSITIONS = self.PAGE2_TICK_POSITIONS = self.EYES_DIR = self.MOUTH_DIR = None

        self.fruits = [
            "Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit",
            "Heart Fruit", "Square Fruit", "Chao Fruit", "Power Fruit",
            "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"
        ]
        self.fruit_prices = 15

    async def cog_load(self):
        self.image_utils = self.bot.get_cog('ImageUtils')
        self.data_utils = self.bot.get_cog('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("ImageUtils or DataUtils cog not loaded.")

        self.assets_dir = self.image_utils.assets_dir
        paths = {
            'TEMPLATE_PATH': 'graphics/cards/stats_page_1.png',
            'TEMPLATE_PAGE_2_PATH': 'graphics/cards/stats_page_2.png',
            'OVERLAY_PATH': 'graphics/ticks/tick_filled.png',
            'ICON_PATH': 'graphics/icons/Stats.png',
            'NEUTRAL_PATH': 'chao/normal/neutral/neutral_normal_1.png',
            'BACKGROUND_PATH': 'graphics/thumbnails/neutral_background.png',
            'BLACK_MARKET_THUMBNAIL_PATH': 'graphics/thumbnails/black_market.png',
            'BLACK_MARKET_FRUITS_PAGE_1_PATH': 'graphics/cards/black_market_fruits_page_1.png',
            'BLACK_MARKET_FRUITS_PAGE_2_PATH': 'graphics/cards/black_market_fruits_page_2.png',
            'BLACK_MARKET_ICON_PATH': 'graphics/icons/Black_Market.png'
        }
        for attr, rel_path in paths.items():
            setattr(self, attr, os.path.join(self.assets_dir, rel_path))

        self.PAGE1_TICK_POSITIONS = [(446, y) for y in [1176, 315, 591, 883, 1469]]
        self.PAGE2_TICK_POSITIONS = {
            'happiness': (272, 590),
            'illness': (272, 882),
            'energy': (272, 1175),
            'hp': (272, 1468)
        }
        self.EYES_DIR = os.path.join(self.assets_dir, 'face', 'eyes')
        self.MOUTH_DIR = os.path.join(self.assets_dir, 'face', 'mouth')

    def send_embed(self, ctx, description: str, title: str = "Chao Bot"):
        return ctx.send(discord.Embed(title=title, description=description, color=self.embed_color))

    def check_life_cycle(self, chao_stats: Dict) -> str:
        age_in_days = (datetime.now() - datetime.strptime(chao_stats['birth_date'], "%Y-%m-%d")).days
        if age_in_days >= 60:
            if chao_stats.get('happiness_ticks', 0) > 5:
                chao_stats.update({
                    'reincarnations': chao_stats.get('reincarnations', 0) + 1,
                    'happiness_ticks': 10,
                    'swim_ticks': 0, 'fly_ticks': 0, 'run_ticks': 0, 'power_ticks': 0, 'stamina_ticks': 0,
                    'swim_level': 0, 'fly_level': 0, 'run_level': 0, 'power_level': 0, 'stamina_level': 0,
                    'swim_exp': 0, 'fly_exp': 0, 'run_exp': 0, 'power_exp': 0, 'stamina_exp': 0,
                    'birth_date': datetime.now().strftime("%Y-%m-%d")
                })
                return "reincarnated"
            chao_stats['dead'] = 1
            return "died"
        return "alive"

    async def force_life_check(self, ctx, *, chao_name: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()

        if chao_stats.get('happiness_ticks', 0) > 5:
            chao_stats.update({
                'reincarnations': chao_stats.get('reincarnations', 0) + 1,
                'happiness_ticks': 10,
                'swim_ticks': 0, 'fly_ticks': 0, 'run_ticks': 0, 'power_ticks': 0, 'stamina_ticks': 0,
                'swim_level': 0, 'fly_level': 0, 'run_level': 0, 'power_level': 0, 'stamina_level': 0,
                'swim_exp': 0, 'fly_exp': 0, 'run_exp': 0, 'power_exp': 0, 'stamina_exp': 0,
                'birth_date': datetime.now().strftime("%Y-%m-%d")
            })
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)
            await self.send_embed(ctx, f"✨ **{chao_name} has reincarnated! A fresh start begins!**")
        else:
            chao_stats['dead'] = 1
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)
            await self.send_embed(ctx, f"😢 **{chao_name} has passed away due to low happiness.**")

    async def force_happiness(self, ctx, *, chao_name: str, happiness_value: int):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()
        chao_stats['happiness_ticks'] = happiness_value
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)
        await self.send_embed(ctx, f"✅ **{chao_name}'s happiness has been set to {happiness_value}.**")

    async def hatch(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}

        if current_inv.get('Chao Egg', 0) < 1:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")

        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', '')
        os.makedirs(chao_dir, exist_ok=True)

        # Use a while loop to ensure unique chao_name
        while True:
            chao_name = random.choice(self.chao_names)
            if chao_name not in os.listdir(chao_dir):
                break

        chao_path = os.path.join(chao_dir, chao_name)
        os.makedirs(chao_path, exist_ok=True)
        chao_stats_path = os.path.join(chao_path, f'{chao_name}_stats.parquet')
        current_inv['Chao Egg'] -= 1
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)

        # Initialize chao_stats with all required fields
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

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)

        # Paths for eyes and mouth images
        eyes_path = os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png") \
            if os.path.exists(os.path.join(self.EYES_DIR, f"neutral_{chao_stats['eyes']}.png")) else \
            os.path.join(self.EYES_DIR, "neutral.png")
        mouth_path = os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png") \
            if os.path.exists(os.path.join(self.MOUTH_DIR, f"{chao_stats['mouth']}.png")) else \
            os.path.join(self.MOUTH_DIR, "happy.png")

        # Combine images to create the thumbnail
        thumbnail_path = os.path.join(chao_path, f"{chao_name}_thumbnail.png")
        self.image_utils.combine_images_with_face(
            self.BACKGROUND_PATH,
            self.NEUTRAL_PATH,
            eyes_path,
            mouth_path,
            thumbnail_path
        )

        # Create and send the embed with the thumbnail image
        embed = discord.Embed(
            title="Your Chao Egg has hatched!",
            description=f"Your Chao Egg hatched into a Regular Two-tone Chao named {chao_name}!",
            color=discord.Color.blue()
        ).set_image(url=f"attachment://{chao_name.replace(' ', '_')}_thumbnail.png")

        await ctx.reply(
            file=discord.File(thumbnail_path, filename=f"{chao_name.replace(' ', '_')}_thumbnail.png"),
            embed=embed
        )

    def update_chao_type_and_thumbnail(self, guild_id: str, user_id: str, chao_name: str, latest_stats: Dict) -> Tuple[Optional[str], Optional[str]]:
        try:
            chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
            thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')

            stat_levels = {s: latest_stats.get(f'{s}_level', 0) for s in ['power', 'swim', 'stamina', 'fly', 'run']}
            max_stat, max_level = max(stat_levels, key=stat_levels.get), max(stat_levels.values())
            dark_hero, form = latest_stats.get('dark_hero', 0), latest_stats.get('Form', "1")
            current_type = latest_stats.get('Type', 'normal').lower()
            chao_type = current_type

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
                form, chao_type = "2", evolve_type(2, current_type, latest_stats)
            elif form == "2" and max_level >= self.FORM_LEVEL_3:
                form, chao_type = "3", evolve_type(3, current_type, latest_stats)
            elif form == "3" and max_level >= self.FORM_LEVEL_4:
                form, chao_type = "4", evolve_type(4, current_type, latest_stats)
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
            chao_image_path = chao_image_path if os.path.exists(chao_image_path) else os.path.join(self.assets_dir, 'chao', 'chao_missing.png')

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

    async def stats(self, ctx, *, chao_name: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')

        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        chao_stats = chao_df.iloc[-1].to_dict()

        life_status = self.check_life_cycle(chao_stats)
        if life_status in {"died", "reincarnated"}:
            self.data_utils.save_chao_stats(chao_stats_path, chao_df, chao_stats)
            message = f"😢 **{chao_name} has passed away due to low happiness.**" if life_status == "died" else f"✨ **{chao_name} has reincarnated! A fresh start begins!**"
            return await self.send_embed(ctx, message)

        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_stats)
        chao_type_display = "Normal" if form in ["1", "2"] else chao_type.replace("_", "/").capitalize()
        alignment_label = chao_stats.get('Alignment', 'Neutral').capitalize()
        sanitized_chao_name = chao_name.replace(" ", "_")

        stats_image_paths = {
            1: os.path.join(chao_dir, f'{chao_name}_stats_page_1.png'),
            2: os.path.join(chao_dir, f'{chao_name}_stats_page_2.png')
        }

        stats_values_page2 = {stat: chao_stats.get(f"{stat}_ticks", 0) for stat in self.PAGE2_TICK_POSITIONS}

        await asyncio.gather(
            asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.TEMPLATE_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[1],
                self.PAGE1_TICK_POSITIONS,
                *[chao_stats.get(f"{stat}_ticks", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_stats.get(f"{stat}_level", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']],
                *[chao_stats.get(f"{stat}_exp", 0) for stat in ['power', 'swim', 'fly', 'run', 'stamina']]
            ),
            asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.TEMPLATE_PAGE_2_PATH,
                self.OVERLAY_PATH,
                stats_image_paths[2],
                self.PAGE2_TICK_POSITIONS,
                stats_values_page2
            )
        )

        embed = discord.Embed(color=self.embed_color).set_author(
            name=f"{chao_name}'s Stats",
            icon_url="attachment://Stats.png"
        ).add_field(name="Type", value=chao_type_display, inline=True)\
         .add_field(name="Alignment", value=alignment_label, inline=True)\
         .set_thumbnail(url="attachment://chao_thumbnail.png")\
         .set_image(url="attachment://stats_page.png")\
         .set_footer(text="Page 1 / 2")

        view = StatsView(
            chao_name=chao_name,
            guild_id=guild_id,
            user_id=user_id,
            page1_tick_positions=self.PAGE1_TICK_POSITIONS,
            page2_tick_positions=self.PAGE2_TICK_POSITIONS,
            exp_positions=self.image_utils.EXP_POSITIONS,
            num_images=self.image_utils.num_images,
            level_position_offset=self.image_utils.LEVEL_POSITION_OFFSET,
            level_spacing=self.image_utils.LEVEL_SPACING,
            tick_spacing=self.image_utils.TICK_SPACING,
            chao_type_display=chao_type_display,
            alignment_label=alignment_label,
            template_path=self.TEMPLATE_PATH,
            template_page_2_path=self.TEMPLATE_PAGE_2_PATH,
            overlay_path=self.OVERLAY_PATH,
            icon_path=self.ICON_PATH,
            image_utils=self.image_utils,
            data_utils=self.data_utils,
            total_pages=2
        )

        try:
            sent_message = await ctx.send(
                files=[
                    discord.File(stats_image_paths[1], "stats_page.png"),
                    discord.File(self.ICON_PATH, filename="Stats.png"),
                    discord.File(os.path.join(chao_dir, f'{chao_name}_thumbnail.png'), "chao_thumbnail.png")
                ],
                embed=embed,
                view=view
            )
            self.bot.add_view(view, message_id=sent_message.id)
        except Exception as e:
            print(f"[stats] Failed to send message: {e}")
            await ctx.send("An error occurred while sending the stats.")

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
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path).fillna(0)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}

        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.embed_color)
        embed.add_field(name='Rings', value=str(current_inv.get("rings", 0)), inline=False)
        embed.add_field(name='Last Updated', value=current_inv.get("date", "N/A"), inline=False)

        # Add fruit fields using comprehension
        embed.add_fields([
            discord.Embed.Field(name=fruit, value=f'Quantity: {int(current_inv.get(fruit, 0))}', inline=True)
            for fruit in self.fruits if int(current_inv.get(fruit, 0)) > 0
        ])

        eggs = int(current_inv.get('Chao Egg', 0))
        if eggs > 0:
            embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {eggs}', inline=True)

        await ctx.send(embed=embed)

    async def feed(self, ctx, *, chao_name_and_fruit: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        parts = chao_name_and_fruit.split()

        # Identify fruit and chao name using comprehension
        for i in range(1, len(parts) + 1):
            potential = ' '.join(parts[-i:])
            if fruit := next((f for f in self.fruits if f.lower() == potential.lower()), None):
                chao_name = ' '.join(parts[:-i])
                fruit_name = fruit
                break
        else:
            return await self.send_embed(ctx, f"{ctx.author.mention}, provide a valid Chao name and fruit.")

        chao_dir = self.data_utils.get_path(guild_id, user_id, 'chao_data', chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path):
            return await self.send_embed(ctx, f"{ctx.author.mention}, no Chao named {chao_name}.")

        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {}
        if current_inv.get(fruit_name, 0) <= 0:
            return await self.send_embed(ctx, f"{ctx.author.mention}, you have no {fruit_name}.")

        latest_stats = chao_df.iloc[-1].copy()
        days_elapsed = (datetime.now() - datetime.strptime(latest_stats.get('date', datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")).days
        latest_stats['belly'] = max(0, latest_stats.get('belly', 0) - days_elapsed)
        latest_stats['date'] = datetime.now().strftime("%Y-%m-%d")

        # Update stats
        stat_key = f"{self.FRUIT_STATS[fruit_name]}_ticks"
        level_key = f"{self.FRUIT_STATS[fruit_name]}_level"
        latest_stats[stat_key] += random.randint(self.FRUIT_TICKS_MIN, self.FRUIT_TICKS_MAX)

        if latest_stats[stat_key] >= 10:
            latest_stats[stat_key] %= 10
            latest_stats[level_key] = latest_stats.get(level_key, 0) + 1
            exp_key = f"{self.FRUIT_STATS[fruit_name]}_exp"
            grade_key = f"{self.FRUIT_STATS[fruit_name]}_grade"
            latest_stats[exp_key] += self.calculate_exp_gain(latest_stats.get(grade_key, 'D'))

        latest_stats['belly'] = min(10, latest_stats['belly'] + 2)

        current_form = latest_stats.get('Form', '1')

        # Adjust alignment and stats
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

        chao_type, form = self.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, latest_stats)

        current_inv[fruit_name] -= 1
        self.data_utils.save_inventory(
            inv_path,
            inv_df,
            current_inv
        )
        self.data_utils.save_chao_stats(chao_stats_path, chao_df, latest_stats.to_dict())

        thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')
        sanitized_chao_name = chao_name.replace(" ", "_")
        embed = discord.Embed(
            description=(
                f"{chao_name} ate {fruit_name}!\n"
                f"{chao_name}'s {stat_key.split('_')[0].capitalize()} stat increased!\n"
                f"Ticks: {latest_stats[stat_key]}/10\n"
                f"Level: {latest_stats.get(level_key, 0)} (Type: {latest_stats.get('Type', 'Normal')})\n"
                f"Belly: {latest_stats['belly']}/10\n"
                f"**Current Values:** swim_fly: {latest_stats.get('swim_fly', 0)}, "
                f"run_power: {latest_stats.get('run_power', 0)}, dark_hero: {latest_stats.get('dark_hero', 0)}"
            ),
            color=self.embed_color
        ).set_image(url=f"attachment://{sanitized_chao_name}_thumbnail.png")

        await ctx.send(
            file=discord.File(thumbnail_path, filename=f"{sanitized_chao_name}_thumbnail.png"),
            embed=embed
        )

    def calculate_exp_gain(self, grade: str) -> int:
        return {
            'F': 1, 'E': 2, 'D': 3, 'C': 4, 'B': 5, 'A': 6, 'S': 7, 'X': 8
        }.get(grade.upper(), 3)

async def setup(bot):
    await bot.add_cog(Chao(bot))
