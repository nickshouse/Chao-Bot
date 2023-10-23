import discord
from discord.ext import commands
from PIL import Image

# Global constants
TEMPLATE_PATH = '../assets/stats_template.png'
OVERLAY_PATH = '../assets/tick_filled.png'
OUTPUT_PATH = './output_image.png'
TICK_SPACING = 105
LEVEL_POSITION_OFFSET = (826, -106)
LEVEL_SPACING = 60
TICK_POSITIONS = [(446, 1176), (446, 315), (446, 1747), (446, 591), (446, 883), (446, 1469)]
EXP_POSITIONS = [(183, 302), (243, 302), (303, 302), (363, 302)]
GRADE_TO_POINTS = {'E': 13, 'D': 16, 'C': 19, 'B': 22, 'A': 25, 'S': 28, 'F': 10}  # Points = (Grade x 3) + 13

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.num_images = {str(i): Image.open(f'../assets/resized/{i}.png') for i in range(10)}

    def paste_image(self, template_path, overlay_path, output_path, tick_positions, swim_grade, *stats):
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            if overlay.mode != 'RGBA':
                overlay = overlay.convert('RGBA')

            def paste_ticks(start_position, ticks, tick_spacing):
                for i in range(ticks):
                    x_position = start_position[0] + i * tick_spacing
                    position = (x_position, start_position[1])
                    template.paste(overlay, position, overlay)

            def paste_level(start_position, level):
                tens_image = self.num_images[str(level // 10)]
                ones_image = self.num_images[str(level % 10)]
                template.paste(tens_image, start_position, tens_image)
                template.paste(ones_image, (start_position[0] + LEVEL_SPACING, start_position[1]), ones_image)

            def paste_exp(start_positions, exp):
                exp_str = f'{exp:04}'
                for position, digit in zip(start_positions, exp_str):
                    exp_image = self.num_images[digit]
                    template.paste(exp_image, position, exp_image)

            for position, ticks, level in zip(tick_positions, stats[:6], stats[6:]):
                paste_ticks(position, ticks, TICK_SPACING)
                level_position = (position[0] + LEVEL_POSITION_OFFSET[0], position[1] + LEVEL_POSITION_OFFSET[1])
                paste_level(level_position, level)

            exp_points = GRADE_TO_POINTS.get(swim_grade, 10)
            paste_exp(EXP_POSITIONS, exp_points)

            template.save(output_path)

    @commands.command()
    async def generate_image(self, ctx, chao_name, swim_grade, power_ticks=None, swim_ticks=None, stamina_ticks=None, fly_ticks=None, run_ticks=None, intel_ticks=None):
        if any(tick is None for tick in [power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks]):
            chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
            chao_to_view = next((chao for chao in chao_list if chao['name'] == chao_name), None)
            if chao_to_view is None:
                await ctx.send(f"You don't have a Chao named {chao_name}.")
                return
            # Extracting stats and grade from the database
            power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks = \
                chao_to_view['power_ticks'], chao_to_view['swim_ticks'], chao_to_view['stamina_ticks'], \
                chao_to_view['fly_ticks'], chao_to_view['run_ticks'], chao_to_view['intel_ticks']
            swim_grade = chao_to_view['swim_grade']

        self.paste_image(TEMPLATE_PATH, OVERLAY_PATH, OUTPUT_PATH, TICK_POSITIONS, swim_grade, power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks)

        embed = discord.Embed(
            title=f"Generated Image for {chao_name}",
            color=discord.Color.blue()
        )

        with open(OUTPUT_PATH, 'rb') as file:
            file = discord.File(file, 'output_image.png')
            embed.set_image(url=f'attachment://{file.filename}')

        await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Generator(bot))
    print("Generator cog loaded")
