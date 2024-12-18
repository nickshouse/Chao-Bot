import discord
from discord.ext import commands
from functools import wraps

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None
        self.data_utils = None
        self.black_market_cog = None  # Add this line

    def cog_load(self):
        self.chao_cog = self.bot.get_cog('Chao')
        self.data_utils = self.bot.get_cog('DataUtils')
        self.black_market_cog = self.bot.get_cog('BlackMarket')  # Add this line
        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Make sure it is loaded before the Commands cog.")
        if not self.data_utils:
            raise Exception("DataUtils cog is not loaded. Make sure it is loaded before the Commands cog.")
        if not self.black_market_cog:
            raise Exception("BlackMarket cog is not loaded. Make sure it is loaded before the Commands cog.")

    def ensure_user_initialized(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            guild_id = str(ctx.guild.id)
            user_id = str(ctx.author.id)
            if not self.data_utils.is_user_initialized(guild_id, user_id):
                return await ctx.send(f"{ctx.author.mention}, please use the `$chao` command to start using the Chao Bot.")
            return await func(self, ctx, *args, **kwargs)
        return wrapper

    @commands.command(name='chao')
    async def chao(self, ctx):
        await self.chao_cog.chao(ctx)

    @commands.command(name='hatch')
    @ensure_user_initialized
    async def hatch(self, ctx):
        await self.chao_cog.hatch(ctx)

    @commands.command(name='market')
    @ensure_user_initialized
    async def market(self, ctx, *, market_type: str = None):
        await self.black_market_cog.market(ctx, market_type=market_type)  # Update reference

    @commands.command(name='buy')
    @ensure_user_initialized
    async def buy(self, ctx, *, item_quantity: str):
        await self.black_market_cog.buy(ctx, item_quantity=item_quantity)  # Update reference

    @commands.command(name='inventory')
    @ensure_user_initialized
    async def inventory(self, ctx):
        await self.chao_cog.inventory(ctx)

    @commands.command(name='restore')
    @ensure_user_initialized
    async def restore(self, ctx, *, args: str):
        await self.data_utils.restore(ctx, args=args)

    @commands.command(name='give_egg')
    @ensure_user_initialized
    async def give_egg(self, ctx):
        await self.chao_cog.give_egg(ctx)

    @commands.command(name='give_rings')
    @ensure_user_initialized
    async def give_rings(self, ctx):
        await self.chao_cog.give_rings(ctx)

    @commands.command(name='force_life_check')
    @ensure_user_initialized
    async def force_life_check(self, ctx, *, chao_name: str):
        """Force a life check based solely on happiness."""
        await self.chao_cog.force_life_check(ctx, chao_name=chao_name)

    @commands.command(name='force_happiness')
    @ensure_user_initialized
    async def force_happiness(self, ctx, chao_name: str, happiness_value: int):
        """Manually set a Chao's happiness value between 0 and 10."""
        if not (0 <= happiness_value <= 10):
            return await ctx.send(f"{ctx.author.mention}, happiness must be a value between 0 and 10.")
        await self.chao_cog.force_happiness(ctx, chao_name=chao_name, happiness_value=happiness_value)

    @commands.command(name='stats')
    @ensure_user_initialized
    async def stats(self, ctx, *, chao_name: str):
        await self.chao_cog.stats(ctx, chao_name=chao_name)

    @commands.command(name='feed')
    @ensure_user_initialized
    async def feed(self, ctx, *, chao_name_and_fruit: str):
        await self.chao_cog.feed(ctx, chao_name_and_fruit=chao_name_and_fruit)

async def setup(bot): 
    await bot.add_cog(Commands(bot))
