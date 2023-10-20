import discord
from discord.ext import commands
from PIL import Image

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def paste_image(template_path, overlay_path, output_path, tick_positions, power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks):
        template = Image.open(template_path)
        overlay = Image.open(overlay_path)

        # Ensure the overlay image has an alpha channel
        if overlay.mode != 'RGBA':
            overlay = overlay.convert('RGBA')

        # Function to paste ticks at a specified start position
        def paste_ticks(start_position, ticks, tick_spacing):
            for i in range(ticks):
                x_position = start_position[0] + i * tick_spacing  # spacing between ticks
                position = (x_position, start_position[1])  # Same y-axis
                template.paste(overlay, position, overlay)

        # Paste power, swim, stamina, fly, run, and intel ticks
        for position, ticks, spacing in zip(tick_positions, [power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks], [105, 105, 105, 105, 105, 105]):
            paste_ticks(position, ticks, spacing)

        template.save(output_path)

    @commands.command()
    async def generate_image(self, ctx, chao_name, power_ticks=None, swim_ticks=None, stamina_ticks=None, fly_ticks=None, run_ticks=None, intel_ticks=None):
        # If ticks are None, fetch them from the database
        if any(tick is None for tick in [power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks]):
            chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
            chao_to_view = next((chao for chao in chao_list if chao['name'] == chao_name), None)
            if chao_to_view is None:
                await ctx.send(f"You don't have a Chao named {chao_name}.")
                return
            power_ticks = chao_to_view['power_ticks']
            swim_ticks = chao_to_view['swim_ticks']
            stamina_ticks = chao_to_view['stamina_ticks']
            fly_ticks = chao_to_view['fly_ticks']
            run_ticks = chao_to_view['run_ticks']
            intel_ticks = chao_to_view['intel_ticks']  # Get the intel ticks from the database

        # Paths to the images
        num0 = '../assets/resized/0.png'
        num1 = '../assets/resized/1.png'
        num2 = '../assets/resized/2.png'
        num3 = '../assets/resized/3.png'
        num4 = '../assets/resized/4.png'
        num5 = '../assets/resized/5.png'
        num6 = '../assets/resized/6.png'
        num7 = '../assets/resized/7.png'
        num8 = '../assets/resized/8.png'
        num9 = '../assets/resized/9.png'
    
        template_path = '../assets/stats_template.png'
        overlay_path = '../assets/tick_filled.png'
        output_path = './output_image.png'

        # Starting positions for power, swim, stamina, fly, run, and intel ticks
        tick_positions = [(446, 1176), (446, 315), (446, 1747), (446, 591), (446, 883), (446, 1469)]

        # Call the function
        self.paste_image(template_path, overlay_path, output_path, tick_positions, power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, intel_ticks)

        # Create an embed
        embed = discord.Embed(
            title=f"Generated Image for {chao_name}",
            color=discord.Color.blue()
        )

        # Attach the image to the embed
        with open(output_path, 'rb') as file:
            file = discord.File(file, 'output_image.png')
            embed.set_image(url=f'attachment://{file.filename}')

        # Send the embed with the attached image to the channel
        await ctx.send(file=file, embed=embed)

async def setup(bot):
    await bot.add_cog(Generator(bot))
    print("Generator cog loaded")
