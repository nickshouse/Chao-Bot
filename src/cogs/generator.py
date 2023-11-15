import discord
from discord import SelectOption, ui
from discord.ext import commands
from discord.ui import View, Select
from discord.ui.select import SelectOption
from PIL import Image

# Global constants
TEMPLATE_PATH = "../assets/graphics/stats_template.png"
OVERLAY_PATH = "../assets/graphics/tick_filled.png"
OUTPUT_PATH = "./output_image.png"
ICON_PATH = "./Stats.png"
THUMBNAIL_PATH = "./neutral_normal_normal_child.png"
TICK_SPACING = 105
LEVEL_POSITION_OFFSET = (826, -106)
LEVEL_SPACING = 60
TICK_POSITIONS = [
    (446, 1176),
    (446, 315),
    (446, 1747),
    (446, 591),
    (446, 883),
    (446, 1469),
]
SWIM_EXP_POSITIONS = [(183, 302), (243, 302), (303, 302), (363, 302)]
FLY_EXP_POSITIONS = [(183, 576), (243, 576), (303, 576), (363, 576)]
RUN_EXP_POSITIONS = [(183, 868), (243, 868), (303, 868), (363, 868)]
POWER_EXP_POSITIONS = [(183, 1161), (243, 1161), (303, 1161), (363, 1161)]
INTEL_EXP_POSITIONS = [(183, 1454), (243, 1454), (303, 1454), (363, 1454)]
STAMINA_EXP_POSITIONS = [
    (183, 1732),
    (243, 1732),
    (303, 1732),
    (363, 1732),
]

class Select(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Appearance", description="View chao's physical appearance", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662672597626950)),
            discord.SelectOption(label="Behaviours", description="Current behaviours of chao", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662673386143744)),
            discord.SelectOption(label="DNA", description="Genetic information about chao", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662674820599910)),
            discord.SelectOption(label="Friendships", description="See which chao are friends with this chao", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662675521060875)),
            discord.SelectOption(label="General", description="General information about chao", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662676691267645)),
            discord.SelectOption(label="Lessons", description="Lessons that chao has learned in school", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662677647556689)),
            discord.SelectOption(label="Personality", description="View chao's personality traits", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662678763257886)),
            discord.SelectOption(label="Stats", description="Chao's main stats", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662715870269492)),
            discord.SelectOption(label="Toys", description="Look at chao's favourite toys", emoji=discord.PartialEmoji(name="custom_emoji", id=1171662680625528934)),
        ]

        super().__init__(placeholder="Select a page", max_values=1, min_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # 1. get the role object from the guild
        role = discord.utils.get(interaction.guild.roles, name=str(self.values[0]))
        # 2a. if not found, add to member
        if interaction.user.get_role(role.id) is None:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("Role assigned", ephemeral=True)
        # 2b. if found, remove the role from member
        else:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("Role removed", ephemeral=True)

class SelectView(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.add_item(Select())


class Generator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.num_images = {
            str(i): Image.open(f"../assets/resized/{i}.png") for i in range(10)
        }

    def paste_image(
        self,
        template_path,
        overlay_path,
        output_path,
        tick_positions,
        swim_exp_positions,
        fly_exp_positions,
        run_exp_positions,
        power_exp_positions,
        intel_exp_positions,
        stamina_exp_positions,
        *stats,
    ):
        with Image.open(template_path) as template, Image.open(overlay_path) as overlay:
            if overlay.mode != "RGBA":
                overlay = overlay.convert("RGBA")

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
                template.paste(
                    ones_image,
                    (start_position[0] + LEVEL_SPACING, start_position[1]),
                    ones_image,
                )

            for position, ticks, level in zip(tick_positions, stats[:6], stats[6:12]):
                paste_ticks(position, ticks)
                level_position = (
                    position[0] + LEVEL_POSITION_OFFSET[0],
                    position[1] + LEVEL_POSITION_OFFSET[1],
                )
                paste_level(level_position, level)

            paste_exp(template, stats[-6], swim_exp_positions)
            paste_exp(template, stats[-5], fly_exp_positions)
            paste_exp(template, stats[-4], run_exp_positions)
            paste_exp(template, stats[-3], power_exp_positions)
            paste_exp(template, stats[-2], intel_exp_positions)
            paste_exp(template, stats[-1], stamina_exp_positions)

            template.save(output_path)

    async def generate_image_command(self, ctx, chao_name, stat_to_update=None, stat_value=None):
        chao_list = await self.bot.cogs["Database"].get_chao(
            ctx.guild.id, ctx.author.id
        )
        chao_to_view = next(
            (chao for chao in chao_list if chao["name"] == chao_name), None
        )
        if chao_to_view is None:
            await ctx.send(f"You don't have a Chao named {chao_name}.")
            return

        swim_exp = chao_to_view.get("swim_exp", 0)
        fly_exp = chao_to_view.get("fly_exp", 0)
        run_exp = chao_to_view.get("run_exp", 0)
        power_exp = chao_to_view.get("power_exp", 0)
        intel_exp = chao_to_view.get("intel_exp", 0)
        stamina_exp = chao_to_view.get("stamina_exp", 0)

        self.paste_image(
            TEMPLATE_PATH,
            OVERLAY_PATH,
            OUTPUT_PATH,
            TICK_POSITIONS,
            SWIM_EXP_POSITIONS,
            FLY_EXP_POSITIONS,
            RUN_EXP_POSITIONS,
            POWER_EXP_POSITIONS,
            INTEL_EXP_POSITIONS,
            STAMINA_EXP_POSITIONS,
            chao_to_view["power_ticks"],
            chao_to_view["swim_ticks"],
            chao_to_view["stamina_ticks"],
            chao_to_view["fly_ticks"],
            chao_to_view["run_ticks"],
            chao_to_view["intel_ticks"],
            chao_to_view["power_level"],
            chao_to_view["swim_level"],
            chao_to_view["stamina_level"],
            chao_to_view["fly_level"],
            chao_to_view["run_level"],
            chao_to_view["intel_level"],
            swim_exp,
            fly_exp,
            run_exp,
            power_exp,
            intel_exp,
            stamina_exp,
        )

        embed = discord.Embed(title=f"{chao_name}", color=discord.Color.blue())

        # Setting the author icon and thumbnail
        embed.set_author(name="Chao Stats", icon_url="attachment://Stats.png")
        embed.set_thumbnail(url="attachment://neutral_normal_normal_child.png")

        with open(OUTPUT_PATH, "rb") as file:
            output_image = discord.File(file, "output_image.png")
            embed.set_image(url=f"attachment://{output_image.filename}")

        embed.set_footer(text="Page 1 / ?")

        # Sending the files along with the embed
        await ctx.send(files=[output_image, discord.File(ICON_PATH), discord.File(THUMBNAIL_PATH)], embed=embed)
        await ctx.send(view=SelectView())

async def setup(bot):
    await bot.add_cog(Generator(bot))
    print("Generator cog loaded")
