import discord
from discord.ext import commands

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def chao(self, ctx):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await chao_cog.chao_command(ctx)

    @commands.command()
    async def give_egg(self, ctx):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await chao_cog.give_egg_command(ctx)

    @commands.command()
    async def feed(self, ctx, *, full_input: str):
        chao_cog = self.bot.get_cog('Chao')
        if chao_cog:
            await chao_cog.feed_command(ctx, full_input)

    @commands.command()
    async def generate_image(self, ctx, chao_name, stat_to_update=None, stat_value=None):
        generator_cog = self.bot.get_cog('Generator')
        if generator_cog:
            await generator_cog.generate_image_command(ctx, chao_name, stat_to_update, stat_value)

    @commands.command()
    async def buy(self, ctx, *args):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await black_market_cog.buy_command(ctx, *args)

    @commands.command()
    async def market(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await black_market_cog.market_command(ctx)

    @commands.command()
    async def inventory(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await black_market_cog.inventory_command(ctx)

    @commands.command()
    async def give_rings(self, ctx):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await black_market_cog.give_rings_command(ctx)

    @commands.command()
    async def rings(self, ctx, member: discord.Member = None):
        black_market_cog = self.bot.get_cog('BlackMarket')
        if black_market_cog:
            await black_market_cog.rings_command(ctx, member)

async def setup(bot):
    await bot.add_cog(Commands(bot))
    print("Commands cog loaded")
