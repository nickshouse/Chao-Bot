import discord
from discord.ext import commands
from functools import wraps

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None
        self.data_utils = None

    def cog_load(self):
        self.chao_cog = self.bot.get_cog('Chao')
        self.data_utils = self.bot.get_cog('DataUtils')
        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Make sure it is loaded before the Commands cog.")
        if not self.data_utils:
            raise Exception("DataUtils cog is not loaded. Make sure it is loaded before the Commands cog.")

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
    async def market(self, ctx):
        await self.chao_cog.market(ctx)

    @commands.command(name='give_rings')
    @ensure_user_initialized
    async def give_rings(self, ctx):
        await self.chao_cog.give_rings(ctx)

    @commands.command(name='buy')
    @ensure_user_initialized
    async def buy(self, ctx, *, item_quantity: str):
        await self.chao_cog.buy(ctx, item_quantity=item_quantity)

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
