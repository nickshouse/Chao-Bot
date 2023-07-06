import asyncio
import random
import datetime
import discord
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

        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        while any(chao['name'] == chao_name for chao in chao_list):
            chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()
        
        grades = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
        stats = ['Fly', 'Run', 'Swim', 'Power', 'Stamina']
        chao = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None,
        }

        # Create separate fields for each attribute and stat
        for stat in stats:
            grade = random.choice(grades)
            chao[f'{stat.lower()}_grade'] = grade
            chao[f'{stat.lower()}_ticks'] = 0
            chao[f'{stat.lower()}_exp'] = 0
            chao[f'{stat.lower()}_level'] = 0

        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        # Rest of the method remains the same

    @commands.command()
    async def view_chao(self, ctx, chao_name):
        """View the stats of a specified Chao"""
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        for chao in chao_list:
            if chao['name'] == chao_name:
                embed = discord.Embed(title=f"{chao_name}'s Stats", color=discord.Color.blue())
                embed.set_thumbnail(url="https://example.com/chao_image.png")
                stats = ['Fly', 'Run', 'Swim', 'Power', 'Stamina']

                for stat in stats:
                    grade = chao[f'{stat.lower()}_grade']
                    ticks = chao[f'{stat.lower()}_ticks']
                    exp = chao[f'{stat.lower()}_exp']
                    level = chao[f'{stat.lower()}_level']
                    embed.add_field(name=stat, value=f"Grade: {grade}\nTicks: {ticks}\nExp: {exp}\nLevel: {level}", inline=True)

                await ctx.send(embed=embed)
                break
        else:
            await ctx.send(f"You don't have a Chao named {chao_name}.")

async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
