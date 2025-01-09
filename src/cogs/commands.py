import discord
from discord.ext import commands
from functools import wraps

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None
        self.data_utils = None
        self.black_market_cog = None

    def cog_load(self):
        self.chao_cog = self.bot.get_cog('Chao')
        self.data_utils = self.bot.get_cog('DataUtils')
        self.black_market_cog = self.bot.get_cog('BlackMarket')
        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.data_utils:
            raise Exception("DataUtils cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.black_market_cog:
            raise Exception("BlackMarket cog is not loaded. Ensure it is loaded before the Commands cog.")

    def ensure_user_initialized(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            guild_id = str(ctx.guild.id)
            guild_name = ctx.guild.name
            user = ctx.author

            if not self.data_utils.is_user_initialized(guild_id, guild_name, user):
                return await ctx.reply(f"{ctx.author.mention}, please use the `$chao` command to start using the Chao Bot.")
            
            try:
                return await func(self, ctx, *args, **kwargs)
            except Exception as e:
                await ctx.reply(f"An error occurred: {e}")
                raise  # Log or re-raise the exception for debugging
        return wrapper

    @commands.command(name='chao', help="Start your Chao journey!")
    async def chao(self, ctx):
        await self.chao_cog.chao(ctx)

    @commands.command(name='hatch', help="Hatch a new Chao egg!")
    @ensure_user_initialized
    async def hatch(self, ctx):
        await self.chao_cog.hatch(ctx)

    @commands.command(name='grades', help="View a Chao's grades.")
    @ensure_user_initialized
    async def grades(self, ctx, *, chao_name: str):
        await self.chao_cog.grades(ctx, chao_name=chao_name)

    @commands.command(name='market', help="Access the Chao black market.")
    @ensure_user_initialized
    async def market(self, ctx, *, market_type: str = None):
        await self.black_market_cog.market(ctx, market_type=market_type)

    @commands.command(name='buy', help="Buy items from the Chao black market.")
    @ensure_user_initialized
    async def buy(self, ctx, *, item_quantity: str):
        await self.black_market_cog.buy(ctx, item_quantity=item_quantity)

    @commands.command(name='pet', help="Pet your Chao to make it happy!")
    @ensure_user_initialized
    async def pet(self, ctx, *, chao_name: str):
        await self.chao_cog.pet(ctx, chao_name=chao_name)

    @commands.command(name='inventory', help="View your current inventory.")
    @ensure_user_initialized
    async def inventory(self, ctx):
        await self.chao_cog.inventory(ctx)

    @commands.command(name='restore', help="Restore your Chao data.")
    @ensure_user_initialized
    async def restore(self, ctx, *, args: str):
        await self.data_utils.restore(ctx, args=args)

    @commands.command(name='egg', help="Give yourself a Chao egg.")
    @ensure_user_initialized
    async def egg(self, ctx):
        await self.chao_cog.egg(ctx)

    @commands.command(name='goodbye', help="Send Chao away to the faraway Chao Forest.")
    @ensure_user_initialized
    async def goodbye(self, ctx, *, chao_name: str = None):
        await self.chao_cog.goodbye(ctx, chao_name=chao_name)

    @commands.command(name='give_rings', help="(Admin only) Add rings to your account.")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)  # Restrict to admins
    async def give_rings(self, ctx):
        await self.chao_cog.give_rings(ctx)

    @commands.command(name='force_life_check', help="(Admin only) Force a Chao life check.")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)
    async def force_life_check(self, ctx, *, chao_name: str):
        await self.chao_cog.force_life_check(ctx, chao_name=chao_name)

    @commands.command(name='force_happiness', help="Manually set Chao happiness (0-10).")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)
    async def force_happiness(self, ctx, chao_name: str, happiness_value: int):
        if not (0 <= happiness_value <= 10):
            return await ctx.reply(f"{ctx.author.mention}, happiness must be a value between 0 and 10.")
        await self.chao_cog.force_happiness(ctx, chao_name=chao_name, happiness_value=happiness_value)

    @commands.command(name='stats', help="View a Chao's stats.")
    @ensure_user_initialized
    async def stats(self, ctx, *, chao_name: str):
        await self.chao_cog.stats(ctx, chao_name=chao_name)

    @commands.command(name='feed', help="Feed a fruit to your Chao.")
    @ensure_user_initialized
    async def feed(self, ctx, *, chao_name_and_fruit: str):
        await self.chao_cog.feed(ctx, chao_name_and_fruit=chao_name_and_fruit)

    @commands.command(name='listchao', help='List all the Chao you own.')
    @ensure_user_initialized
    async def list_chao(self, ctx):
        await self.chao_cog.list_chao(ctx)


    @commands.command(name='rename', help="Rename your Chao.")
    @ensure_user_initialized
    async def rename(self, ctx, *, chao_name_and_new_name: str = None):
        await self.chao_cog.rename(ctx, chao_name_and_new_name=chao_name_and_new_name)

    @commands.command(name='help', help="Show all available commands.")
    async def help(self, ctx):
        help_text = "**Available Commands:**\n\n"
        help_text += "**$chao** - Start using Chao Bot.\nExample: `$chao`\n\n"
        help_text += "**$plans** - View upcoming features and plans for the Chao Bot.\nExample: `$plans`\n\n"
        help_text += "**$hatch** - Hatch a new Chao egg.\nExample: `$hatch`\n\n"
        help_text += "**$egg** - Receive a new Chao egg. Only 1 at a time.\nExample: `$egg`\n\n"
        help_text += "**$goodbye** - Read about the goodbye command.\nExample: `$goodbye`\n\n"
        help_text += "**$grades** - View a Chao's grades.\nExample: `$grades Chaozart`\n\n"
        help_text += "**$market** - Access the Black Market.\nExample: `$market`\n\n"
        help_text += "**$buy** - Buy items from the Chao black market.\nExample: `$buy garden nut 3`\n\n"
        help_text += "**$pet** - Pet your Chao to make it happy.\nExample: `$pet Chaowser`\n\n"
        help_text += "**$inventory** - View your current inventory.\nExample: `$inventory`\n\n"
        help_text += "**$restore** - Restore your Chao's data to an earlier date. USE WITH CAUTION. \nExample: `$restore Chaozilla 2024-07-22`\n\n"
        help_text += "**$stats** - View a Chao's stats.\nExample: `$stats Chaolin`\n\n"
        help_text += "**$feed** - Feed a fruit to your Chao.\nExample: `$feed Chaoko Run Fruit`\n\n"
        help_text += "**$rename** - Rename your Chao. 15 character limit.\nExample: `$rename Chaozhu BetterChaozhu`\n"

        embed = discord.Embed(title="Chao Bot Help", description=help_text, color=discord.Color.blue())
        await ctx.reply(embed=embed)

    @commands.command(name='plans', help="View upcoming features and plans for the Chao Bot.")
    async def plans(self, ctx):
        """
        Displays a list of upcoming features and plans for the Chao Bot.
        """
        plans_text = (
            "Here are the upcoming features and plans for the Chao Bot:\n\n"
            "- Dynamic emoticon ball\n"
            "- Dizzy eyes\n"
            "- Chaos drives\n"
            "- Shiny Chao\n"
            "- Monotone Chao\n"
            "- Purchasable eggs\n"
            "- Sell to Black Market\n"
            "- Trade requests between users\n"
            "- Chao Graveyard\n"
            "- Chao Mating\n"
            "- Throw your Chao (at your own risk)\n"
            "- Purchasable background colors for stat cards\n"
            "- X rank\n"
            "- Chao export tool\n"
            "- Chao forest\n"
            "- Daily drops\n"
            "- Chao fishing\n"
            "- Chao Racing collab?\n"
        )
        embed = discord.Embed(title="Upcoming Features and Plans", description=plans_text, color=discord.Color.green())
        await ctx.reply(embed=embed)

async def setup(bot): 
    await bot.add_cog(Commands(bot))
