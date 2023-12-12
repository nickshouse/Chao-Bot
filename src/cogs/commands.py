import discord
from discord.ext import commands

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def user_initialized(self, ctx):
        db_cog = self.bot.get_cog('Database')
        if db_cog:
            return await db_cog.is_user_initialized(ctx.guild.id, ctx.author.id)
        return False

    async def check_and_execute(self, ctx, command, *args):
        if await self.user_initialized(ctx):
            await command(ctx, *args)
        else:
            await ctx.reply("You need to use the `chao` command to start using Chao Bot.")

    @commands.command()
    async def chao(self, ctx):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await chao_cog.chao_command(ctx)

    @commands.command()
    async def hatch(self, ctx):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await self.check_and_execute(ctx, chao_cog.hatch_command)

    @commands.command()
    async def feed(self, ctx, *, full_input: str):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await self.check_and_execute(ctx, chao_cog.feed_command, full_input)

    @commands.command()
    async def view_stats(self, ctx, chao_name, stat_to_update=None, stat_value=None):
        generator_cog = self.bot.get_cog('Generator')
        if generator_cog:
            await self.check_and_execute(ctx, generator_cog.view_stats_command, chao_name, stat_to_update, stat_value)

    @commands.command()
    async def buy(self, ctx, *args):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await self.check_and_execute(ctx, black_market_cog.buy_command, *args)

    @commands.command()
    async def market(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await self.check_and_execute(ctx, black_market_cog.market_command)

    @commands.command()
    async def inventory(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await self.check_and_execute(ctx, black_market_cog.inventory_command)

    @commands.command()
    async def give_rings(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await self.check_and_execute(ctx, black_market_cog.give_rings_command)

    @commands.command()
    async def rings(self, ctx, member: discord.Member = None):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await self.check_and_execute(ctx, black_market_cog.rings_command, member)

async def setup(bot):
    await bot.add_cog(Commands(bot))
    print("Commands cog loaded")
