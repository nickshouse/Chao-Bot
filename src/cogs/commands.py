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


async def setup(bot):
    await bot.add_cog(Commands(bot))
    print("Commands cog loaded")
