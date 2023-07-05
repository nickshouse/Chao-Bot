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
        
        # Wait for 5 seconds
        await asyncio.sleep(5)

        # Retrieve all existing Chao owned by the user
        db_cog = self.bot.get_cog('Database')
        existing_chao = await db_cog.get_chao(ctx.guild.id, ctx.author.id)
        existing_chao_names = {chao['name'] for chao in existing_chao}

        # Generate a unique name for the new Chao
        fortune_teller_cog = self.bot.get_cog('FortuneTeller')
        chao_name = fortune_teller_cog.generate_chao_name()
        while chao_name in existing_chao_names:
            chao_name = fortune_teller_cog.generate_chao_name()

        # Create a new Chao
        chao = {
            'name': f'{color} {chao_type} Chao Egg',
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None  # We'll update this when the egg hatches
        }

        # Store the Chao in the user's database
        await db_cog.store_chao(ctx.guild.id, ctx.author.id, chao)
        
        await ctx.send(f"Your {egg} has hatched into {chao_name}, a {egg_type} chao.")


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
