from discord.ext import commands
import asyncio
import random

class Egg(commands.Cog):
    egg_colors = ['White', 'Blue', 'Red', 'Yellow', 'Orange', 'Sky Blue', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    egg_types = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']

    def __init__(self, bot):
        self.bot = bot
        self.database_cog = self.bot.get_cog("Database")
        self.fortune_teller_cog = self.bot.get_cog("FortuneTeller")

    async def hatch_egg(self, ctx, egg):
        """Hatch the user's Chao Egg"""
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        egg_data = await self.database_cog.get_data(guild_id, user_id, 'egg')

        if egg_data.empty or egg_data['egg'].isnull().all():
            await ctx.send("You don't have any Chao Eggs to hatch.")
        else:
            color, _, _ = egg.split(' ', 2)
            chao = f"{color} Chao"
            chao_name = self.fortune_teller_cog.generate_chao_name()  # generate a random Chao name
            chao = f"{chao_name}, the {chao}"  # add the name to the Chao

            self.database_cog.data_queue.append((guild_id, user_id, chao, 'chao'))
            await ctx.send(f"Your {egg} has hatched into {chao}!")

    @commands.command()
    async def give_egg(self, ctx):
        """Give a Chao Egg to the user and hatch it after 5 seconds"""
        color = random.choice(self.egg_colors)
        egg_type = random.choice(self.egg_types)
        egg = f"{color} {egg_type} Chao Egg"
        
        # Store the egg in the user's database
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        self.database_cog.data_queue.append((guild_id, user_id, egg, 'egg'))
        
        await ctx.send(f"You received a {egg}! It will hatch in 5 seconds.")
        await self.hatch_egg(ctx, egg)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Give an egg to all members when the bot joins a server"""
        for member in guild.members:
            await self.give_egg_to_member(member, guild.id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Give an egg to a new member when they join a server"""
        await self.give_egg_to_member(member, member.guild.id)

    async def give_egg_to_member(self, member, guild_id):
        """Check if a member has at least one Chao Egg, and give an egg if they don't"""
        user_id = member.id
        egg_data = await self.database_cog.get_data(guild_id, user_id, 'egg')
        if egg_data.empty or egg_data['egg'].isnull().all():
            color = random.choice(self.egg_colors)
            egg_type = 'Monotone'
            egg = f"{color} {egg_type} Chao Egg"
            self.database_cog.data_queue.append((guild_id, user_id, egg, 'egg'))


async def setup(bot):
    await bot.add_cog(Egg(bot))
    print("Chao Egg cog loaded")
