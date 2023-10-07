import discord
from discord.ext import commands
from PIL import Image

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def paste_image(template_path, overlay_path, output_path, start_position, ticks):
        template = Image.open(template_path)
        overlay = Image.open(overlay_path)

        # Ensure the overlay image has an alpha channel
        if overlay.mode != 'RGBA':
            overlay = overlay.convert('RGBA')

        # Determine the position for each tick and paste the overlay image
        for i in range(ticks):
            x_position = start_position[0] + i * 118  # 118 pixels apart on the x-axis
            position = (x_position, start_position[1])  # Same y-axis
            template.paste(overlay, position, overlay)

        template.save(output_path)

    @commands.command()
    async def generate_image(self, ctx, ticks: int):
        # Paths to the images
        template_path = './assets/stats_template.png'
        overlay_path = './assets/tick_filled.png'
        output_path = './output_image.png'

        # Starting position where the first overlay image should be pasted onto the template
        start_position = (174, 351)

        # Call the function
        self.paste_image(template_path, overlay_path, output_path, start_position, ticks)

        # Send the generated image to the channel
        with open(output_path, 'rb') as file:
            await ctx.send(file=discord.File(file, 'output_image.png'))

async def setup(bot):
    await bot.add_cog(Generator(bot))
    print("Generator cog loaded")
