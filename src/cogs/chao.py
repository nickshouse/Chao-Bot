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

        # Get all the user's Chao
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)

        # Check if generated name is already taken and generate new names until a unique one is found
        while any(chao['name'] == chao_name for chao in chao_list):
            chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()
        
        grades = ['F', 'E', 'D', 'C', 'B', 'A', 'S']

        stats = ['Fly', 'Run', 'Swim', 'Power', 'Stamina']
        chao_stats = {}

        for stat in stats:
            chao_stats[stat] = {
                'grade': random.choice(grades),
                'ticks': 0,
                'exp': 0,
                'level': 0,
            }

        chao = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None,
            'stats': chao_stats,
        }
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"You received a {color} {chao_type} Chao Egg named {chao_name}! It will hatch in 5 seconds.")
        await asyncio.sleep(5)
        chao['hatched'] = 1
        chao['birth_date'] = datetime.datetime.now().date()
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"Your {chao_name} Egg has hatched into a {color} {chao_type} Chao named {chao_name}!")



async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
