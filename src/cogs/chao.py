import asyncio
import random
from discord.ext import commands

class Chao(commands.Cog):
    chao_colors = ['White', 'Blue', 'Red', 'Yellow', 'Orange', 'Sky Blue', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    chao_types = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def give_egg(self, ctx):
        """Give a Chao Egg to the user and hatch it after 5 seconds"""
        color = random.choice(self.chao_colors)
        egg_type = random.choice(self.chao_types)
        egg = f"{color} {egg_type} Chao Egg"

        await ctx.send(f"You received a {egg}! It will hatch in 5 seconds.")
        await asyncio.sleep(5)
        await self.hatch_egg(ctx, egg)

    async def hatch_egg(self, ctx, egg):
        """Hatch the user's Chao Egg"""
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        color, _, egg_type = egg.split(' ', 2)
        chao = {"color": color, "type": egg_type.rstrip(" Chao Egg")}

        await self.bot.get_cog("Database").store_chao(guild_id, user_id, chao)
        await ctx.send(f"Your {egg} has hatched into a {color} {egg_type} Chao!")


async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
