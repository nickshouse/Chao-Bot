import discord, os, pandas as pd, numpy as np, random
from discord.ext import commands
from datetime import datetime
from PIL import Image, ImageEnhance

# Configuration Constants
EVOLVE_LEVEL_1 = 20
EVOLVE_LEVEL_2 = 60

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
    TEMPLATE_PATH = "../assets/graphics/stats_template.png"
    OVERLAY_PATH = "../assets/graphics/tick_filled.png"
    OUTPUT_PATH = "./output_image.png"
    ICON_PATH = "../assets/graphics/Stats.png"
    NEUTRAL_PATH = "../assets/chao/neutral_normal_child.png"
    DARK_PATH = "../assets/chao/dark_normal_child.png"
    HERO_PATH = "../assets/chao/hero_normal_child.png"
    BACKGROUND_PATH = "../assets/chao/neutral_background.png"
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
        self.fruits = [{"emoji": emoji, "name": name} for emoji, name in zip(
            "🍎🍏🍊🍋🍌🍉🍆🍇🍓🍒🍑🍐🍍🥝🍄",
            ["Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit", "Heart Fruit", "Square Fruit", "Chao Fruit", "Smart Fruit", "Power Fruit", "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"]
        )]
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
        chao_dir = self.get_path(guild_id, user_id, 'chao_data', chao_name)
        thumbnail_path = os.path.join(chao_dir, f'{chao_name}_thumbnail.png')
        stat_levels = {stat: chao_df.iloc[0][f'{stat}_level'] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']}
        max_stat = max(stat_levels, key=stat_levels.get)
        max_level = stat_levels[max_stat]
        current_type = chao_df.iloc[0]['Type']
        evolved = chao_df.iloc[0]['evolved']

        if chao_df.iloc[0]['alignment'] >= HERO_ALIGNMENT:
            alignment = "hero"
        elif chao_df.iloc[0]['alignment'] <= DARK_ALIGNMENT:
            alignment = "dark"
        else:
            alignment = "neutral"

        # Freeze the alignment when the Chao evolves
        if max_level >= EVOLVE_LEVEL_1 and not evolved:
            if alignment == "hero":
                chao_df.at[0, 'alignment'] = HERO_ALIGNMENT
            elif alignment == "dark":
                chao_df.at[0, 'alignment'] = DARK_ALIGNMENT
            else:
                chao_df.at[0, 'alignment'] = NEUTRAL_ALIGNMENT
            chao_df.at[0, 'evolved'] = True

        primary_stat = current_type.split('/')[0] if '/' in current_type else "normal"
        secondary_stat = current_type.split('/')[1] if '/' in current_type else "normal"

        # Determine the new type based on the level and stats
        if max_level >= EVOLVE_LEVEL_1:
            chao_df.at[0, 'Type'] = max_stat.capitalize()
            thumbnail_image = f"../assets/chao/{alignment}_{max_stat}_normal_adult.png"
            if not os.path.exists(thumbnail_image):
                thumbnail_image = f"../assets/chao/{alignment}_normal_normal_adult.png"
        elif max_level >= EVOLVE_LEVEL_2:
            primary_stat = max_stat.capitalize() if primary_stat == "normal" else primary_stat
            chao_df.at[0, 'Type'] = f"{primary_stat}/{max_stat.capitalize()}"
            thumbnail_image = f"../assets/chao/{alignment}_{primary_stat.lower()}_{primary_stat.lower() if primary_stat == max_stat.capitalize() else max_stat.lower()}_adult.png"
            if not os.path.exists(thumbnail_image):
                thumbnail_image = f"../assets/chao/{alignment}_normal_normal_adult.png"
        else:
            thumbnail_image = f"../assets/chao/{alignment}_normal_normal_adult.png"

        # Check for level 50
        if max_level >= 50:
            chao_df.at[0, 'Type'] = f"{max_stat.capitalize()}/{max_stat.capitalize()}"
            thumbnail_image = f"../assets/chao/{alignment}_{max_stat.lower()}_{max_stat.lower()}_adult.png"
            if not os.path.exists(thumbnail_image):
                thumbnail_image = f"../assets/chao/{alignment}_normal_normal_adult.png"

        # Use neutral_normal_normal_adult.png if specific image does not exist
        if not os.path.exists(thumbnail_image):
            thumbnail_image = f"../assets/chao/neutral_normal_normal_adult.png"

        self.combine_images(self.BACKGROUND_PATH, thumbnail_image, thumbnail_path)
        chao_df.to_parquet(os.path.join(chao_dir, f'{chao_name}_stats.parquet'), index=False)
        return chao_df.iloc[0]['Type'] if chao_df.iloc[0]['Type'] != "Stamina" else "Normal"

    async def initialize_inventory(self, ctx, guild_id, user_id, embed_title, embed_desc):
        if self.is_user_initialized(guild_id, user_id):
            return await ctx.send(f"{ctx.author.mention}, you have already started using the Chao Bot.")
        self.save_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'), self.load_inventory(self.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')), {'rings': 500, 'Chao Egg': 1, 'Garden Fruit': 5})
        await ctx.reply(file=discord.File(self.NEUTRAL_PATH, filename="neutral_normal_child.png"), embed=discord.Embed(title=embed_title, description=embed_desc, color=self.embed_color).set_image(url="attachment://neutral_normal_child.png"))

    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(Chao(bot))
