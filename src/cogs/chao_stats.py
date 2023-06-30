from discord.ext import commands
import random

class ChaoStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_cog = self.bot.get_cog("Database")

    async def get_stat(self, guild_id, user_id, stat):
        stat_data = await self.database_cog.get_data(guild_id, user_id, f"{stat}_level")
        tick_data = await self.database_cog.get_data(guild_id, user_id, f"{stat}_ticks")
        return stat_data, tick_data

    async def set_stat(self, guild_id, user_id, stat, stat_value, tick_value):
        self.database_cog.data_queue.append((guild_id, user_id, stat_value, f"{stat}_level"))
        self.database_cog.data_queue.append((guild_id, user_id, tick_value, f"{stat}_ticks"))

    @commands.command()
    async def feed(self, ctx, chao_name, fruit_name):
        black_market_cog = self.bot.get_cog("BlackMarket")
        stat = black_market_cog.get_fruit_stat(fruit_name)

        # Check if the fruit affects stats
        if stat is None:
            await ctx.send(f"{fruit_name} does not affect stats.")
            return

        guild_id = ctx.guild.id
        user_id = ctx.author.id

        # Check if the user has the fruit in their inventory
        inventory = await self.database_cog.get_data(guild_id, user_id, "inventory")
        if fruit_name not in inventory:
            await ctx.send(f"You do not have any {fruit_name}.")
            return

        # Check if the user has the specified Chao
        chao_data = await self.database_cog.get_data(guild_id, user_id, "chao")
        if chao_name not in chao_data:
            await ctx.send(f"You do not own a Chao named {chao_name}.")
            return

        # Feed the Chao
        await self.feed_chao(ctx, stat)

        # Update the inventory
        inventory[fruit_name] -= 1
        self.database_cog.data_queue.append((guild_id, user_id, inventory, 'inventory'))
    @commands.command()
    async def feed(self, ctx, stat):
        await self.feed_chao(ctx, stat)

async def setup(bot):
    await bot.add_cog(ChaoStats(bot))
    print("Chao Stats cog loaded")
