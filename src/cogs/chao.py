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

        stats = ['fly', 'run', 'swim', 'power', 'stamina', 'luck', 'intelligence']
        chao_stats = {stat: {
            'grade': 'F',
            'ticks': 0,
            'exp': 0,
            'level': 0,
            'value': random.randint(1, 100)
        } for stat in stats}

        chao = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None,
            'hunger': 100,
            'HP': 100,
            'age': 0,
            'alignment': 'Neutral',
            **chao_stats
        }
        
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"You received a {color} {chao_type} Chao Egg named {chao_name}! It will hatch in 5 seconds.")
        await asyncio.sleep(5)
        chao['hatched'] = 1
        chao['birth_date'] = datetime.datetime.now().date()
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        await ctx.send(f"Your {chao_name} Egg has hatched into a {color} {chao_type} Chao named {chao_name}!")


    @commands.command()
    async def stats(self, ctx, chao_name):
        """Displays the stats of a specific Chao"""
        chao_data = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        
        for chao in chao_data:
            if chao['name'].lower() == chao_name.lower():
                embed = discord.Embed(title=f"{chao['name']}'s Stats", color=0x00ff00)
                stats = ['fly', 'run', 'swim', 'power', 'stamina', 'luck', 'intelligence']
                for stat in stats:
                    embed.add_field(name=stat.capitalize(), value=f"Grade: {chao[stat]['grade']}\nTicks: {chao[stat]['ticks']}\nExp: {chao[stat]['exp']}\nLevel: {chao[stat]['level']}\nValue: {chao[stat]['value']}", inline=True)
                embed.add_field(name='Age', value=chao['age'], inline=False)
                embed.add_field(name='HP', value=chao['HP'], inline=False)
                embed.add_field(name='Hunger', value=chao['hunger'], inline=False)
                embed.add_field(name='Alignment', value=chao['alignment'], inline=False)
                await ctx.send(embed=embed)
                return

        await ctx.send(f"No Chao named {chao_name} was found.")

async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
