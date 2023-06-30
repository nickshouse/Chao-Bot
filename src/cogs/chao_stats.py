from discord.ext import commands

class ChaoStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_cog = self.bot.get_cog("Database")

    async def get_stats(self, guild_id, user_id):
        stats = ['fly', 'run', 'swim', 'power', 'stamina']
        user_stats = {stat: await self.database_cog.get_data(guild_id, user_id, stat) for stat in stats}
        return user_stats

    async def set_stats(self, guild_id, user_id, stats):
        for stat, value in stats.items():
            self.database_cog.data_queue.append((guild_id, user_id, value, stat))

    @commands.command()
    async def show_stats(self, ctx):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        user_stats = await self.get_stats(guild_id, user_id)
        stats_message = '\n'.join(f"{stat.capitalize()}: {value}" for stat, value in user_stats.items())
        await ctx.send(f"Your Chao's stats:\n{stats_message}")

    @commands.command()
    async def set_stat(self, ctx, stat, value: int):
        guild_id = ctx.guild.id
        user_id = ctx.author.id
        await self.set_stats(guild_id, user_id, {stat: value})
        await ctx.send(f"Set {stat} to {value}.")

async def setup(bot):
    await bot.add_cog(ChaoStats(bot))
    print("Chao Stats cog loaded")
