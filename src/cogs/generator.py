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
SWIM_EXP_POSITIONS = [(183, 302), (243, 302), (303, 302), (363, 302)]
FLY_EXP_POSITIONS = [(183, 576), (243, 576), (303, 576), (363, 576)]
RUN_EXP_POSITIONS = [(183, 868), (243, 868), (303, 868), (363, 868)]
POWER_EXP_POSITIONS = [(183, 1161), (243, 1161), (303, 1161), (363, 1161)]
INTEL_EXP_POSITIONS = [(183, 1454), (243, 1454), (303, 1454), (363, 1454)]
STAMINA_EXP_POSITIONS = [(183, 1732), (243, 1732), (303, 1732), (363, 1732)]  # Added this line

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.num_images = {str(i): Image.open(f'../assets/resized/{i}.png') for i in range(10)}

    def paste_image(self, template_path, overlay_path, output_path, tick_positions, swim_exp_positions, fly_exp_positions, run_exp_positions, power_exp_positions, intel_exp_positions, stamina_exp_positions, *stats):  # Added stamina_exp_positions
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            if overlay.mode != 'RGBA':
                overlay = overlay.convert('RGBA')

            def paste_exp(template, exp, positions):
                exp_str = f"{exp:04d}"
                for i, digit in enumerate(exp_str):
                    digit_image = self.num_images[digit]
                    template.paste(digit_image, positions[i], digit_image)

            def paste_ticks(start_position, ticks):
                for i in range(ticks):
                    position = (start_position[0] + i * TICK_SPACING, start_position[1])
                    template.paste(overlay, position, overlay)

            def paste_level(start_position, level):
                tens_image = self.num_images[str(level // 10)]
                ones_image = self.num_images[str(level % 10)]
                template.paste(tens_image, start_position, tens_image)
                template.paste(ones_image, (start_position[0] + LEVEL_SPACING, start_position[1]), ones_image)

            for position, ticks, level in zip(tick_positions, stats[:6], stats[6:12]):
                paste_ticks(position, ticks)
                level_position = (position[0] + LEVEL_POSITION_OFFSET[0], position[1] + LEVEL_POSITION_OFFSET[1])
                paste_level(level_position, level)

            paste_exp(template, stats[-6], swim_exp_positions)
            paste_exp(template, stats[-5], fly_exp_positions)
            paste_exp(template, stats[-4], run_exp_positions)
            paste_exp(template, stats[-3], power_exp_positions)
            paste_exp(template, stats[-2], intel_exp_positions)
            paste_exp(template, stats[-1], stamina_exp_positions)  # Added this line

            template.save(output_path)

    @commands.command()
    async def generate_image(self, ctx, chao_name, stat_to_update=None, stat_value=None):
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        chao_to_view = next((chao for chao in chao_list if chao['name'] == chao_name), None)
        if chao_to_view is None:
            await ctx.send(f"You don't have a Chao named {chao_name}.")
            return

        swim_exp = chao_to_view.get('swim_exp', 0)
        fly_exp = chao_to_view.get('fly_exp', 0)
        run_exp = chao_to_view.get('run_exp', 0)
        power_exp = chao_to_view.get('power_exp', 0)
        intel_exp = chao_to_view.get('intel_exp', 0)
        stamina_exp = chao_to_view.get('stamina_exp', 0)  # Added this line

        self.paste_image(TEMPLATE_PATH, OVERLAY_PATH, OUTPUT_PATH, TICK_POSITIONS, SWIM_EXP_POSITIONS, FLY_EXP_POSITIONS, RUN_EXP_POSITIONS, POWER_EXP_POSITIONS, INTEL_EXP_POSITIONS, STAMINA_EXP_POSITIONS,  # Added STAMINA_EXP_POSITIONS
                         chao_to_view['power_ticks'], chao_to_view['swim_ticks'], chao_to_view['stamina_ticks'],
                         chao_to_view['fly_ticks'], chao_to_view['run_ticks'], chao_to_view['intel_ticks'],
                         chao_to_view['power_level'], chao_to_view['swim_level'], chao_to_view['stamina_level'],
                         chao_to_view['fly_level'], chao_to_view['run_level'], chao_to_view['intel_level'], 
                         swim_exp, fly_exp, run_exp, power_exp, intel_exp, stamina_exp)  # Added stamina_exp

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
