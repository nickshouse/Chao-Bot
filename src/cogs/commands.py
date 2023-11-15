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

async def setup(bot):
    await bot.add_cog(Commands(bot))
    print("Commands cog loaded")
