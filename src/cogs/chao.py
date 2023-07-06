import asyncio
import random
import datetime
from discord.ext import commands

class Chao(commands.Cog):
    chao_colors = ['White', 'Blue', 'Red', 'Yellow', 'Orange', 'Sky Blue', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    chao_types = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def give_egg(self, ctx):
        """Give a Chao Egg to the user"""
        color = random.choice(self.chao_colors)
        chao_type = random.choice(self.chao_types)
        chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()
        chao = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None
        }
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"You received a {color} {chao_type} Chao Egg named {chao_name}! It will hatch in 5 seconds.")
        await asyncio.sleep(5)
        chao['hatched'] = 1
        chao['birth_date'] = datetime.datetime.now().date()
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"Your {chao_name} Egg has hatched into a {color} {chao_type} Chao named {chao_name}!")


    @commands.command()
    async def name(self, ctx, old_name, new_name):
        """Rename a user's Chao"""
        # Get all the user's Chao
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)

        # Find the Chao with the specified old name
        for chao in chao_list:
            if chao['name'] == old_name:
                chao['name'] = new_name  # Change the name
                await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)  # Store the updated Chao
                await ctx.send(f"{old_name} has been renamed to {new_name}!")
                break
        else:
            await ctx.send(f"You don't have a Chao named {old_name}.")


async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
