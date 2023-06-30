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

    async def feed_chao(self, ctx, stat):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        stat_data, tick_data = await self.get_stat(guild_id, user_id, stat)

        tick_increase = random.randint(2, 3)
        new_tick_data = (tick_data or 0) + tick_increase
        level_increase = new_tick_data // 10
        new_stat_data = (stat_data or 0) + level_increase
        new_tick_data %= 10

        await self.set_stat(guild_id, user_id, stat, new_stat_data, new_tick_data)
        await ctx.send(f"Your Chao's {stat} level is now {new_stat_data} and it has {new_tick_data} ticks towards the next level.")

    @commands.command()
    async def feed(self, ctx, stat):
        await self.feed_chao(ctx, stat)

async def setup(bot):
    await bot.add_cog(ChaoStats(bot))
    print("Chao Stats cog loaded")
