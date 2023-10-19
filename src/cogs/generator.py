import discord
from discord.ext import commands
from PIL import Image

class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def paste_image(template_path, overlay_path, output_path, tick_positions, power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, hp_ticks):
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

        # Paste power, swim, stamina, fly, run, and hp ticks
        for position, ticks, spacing in zip(tick_positions, [power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, hp_ticks], [118, 105, 118, 118, 118, 118]):
            paste_ticks(position, ticks, spacing)

        template.save(output_path)

    @commands.command()
    async def generate_image(self, ctx, chao_name, power_ticks=None, swim_ticks=None, stamina_ticks=None, fly_ticks=None, run_ticks=None, hp_ticks=None):
        # If ticks are None, fetch them from the database
        if any(tick is None for tick in [power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, hp_ticks]):
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
            hp_ticks = chao_to_view['hp_ticks']  # Get the hp ticks from the database

        # Paths to the images
        template_path = '../assets/stats_template.png'
        overlay_path = '../assets/tick_filled.png'
        output_path = './output_image.png'

        # Starting positions for power, swim, stamina, fly, run, and hp ticks
        tick_positions = [(178, 1162), (457, 315), (178, 1448), (178, 625), (178, 890), (178, 1729)]

        # Call the function
        self.paste_image(template_path, overlay_path, output_path, tick_positions, power_ticks, swim_ticks, stamina_ticks, fly_ticks, run_ticks, hp_ticks)

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
