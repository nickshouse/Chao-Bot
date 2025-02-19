# cogs/commands.py

import discord
import os
from discord.ext import commands
from decorators import ensure_user_initialized, ensure_chao_alive, ensure_chao_lifecycle, ensure_chao_hatched, ensure_not_in_cacoon


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None
        self.chao_helper_cog = None
        self.data_utils = None
        self.black_market_cog = None
        self.chao_decay_cog = None

    async def cog_load(self):
        self.chao_cog = self.bot.get_cog('Chao')
        self.chao_helper_cog = self.bot.get_cog('ChaoHelper')
        self.data_utils = self.bot.get_cog('DataUtils')
        self.black_market_cog = self.bot.get_cog('BlackMarket')
        self.chao_decay_cog = self.bot.get_cog('ChaoDecay')

        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.data_utils:
            raise Exception("DataUtils cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.black_market_cog:
            raise Exception("BlackMarket cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.chao_decay_cog:
            raise Exception("ChaoDecay cog is not loaded. Ensure it is loaded before the Commands cog.")

    @commands.command(name='chao', help="Start your Chao journey!")
    async def chao(self, ctx):
        # This command does not require the user to be initialized (it initializes them)
        await self.chao_cog.chao(ctx)

    @commands.command(name='hatch', help="Hatch a new Chao egg!")
    @ensure_user_initialized
    async def hatch(self, ctx):
        await self.chao_cog.hatch(ctx)


    @commands.command(name='market', help="Access the Chao black market.")
    @ensure_user_initialized
    async def market(self, ctx, *, market_type: str = None):
        await self.black_market_cog.market(ctx, market_type=market_type)

    @commands.command(name='buy', help="Buy items from the Chao black market.")
    @ensure_user_initialized
    async def buy(self, ctx, *, item_quantity: str):
        await self.black_market_cog.buy(ctx, item_quantity=item_quantity)

    @commands.command(name='inventory', help="View your current inventory.")
    @ensure_user_initialized
    async def inventory(self, ctx):
        await self.chao_cog.inventory(ctx)



    @commands.command(name='egg', help="Give yourself a Chao egg.")
    @ensure_user_initialized
    @ensure_chao_lifecycle
    async def egg(self, ctx):
        await self.chao_cog.egg(ctx)

    @commands.command(name='give_rings', help="(Admin only) Add rings to your account.")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)
    async def give_rings(self, ctx):
        await self.chao_cog.give_rings(ctx)

    @commands.command(name='listchao', help='List all the Chao you own.')
    @ensure_user_initialized
    async def list_chao(self, ctx):
        await self.chao_cog.list_chao(ctx)



    @commands.command(name='force_belly_decay', help="(Admin) Adjust how often belly is reduced.")
    @commands.has_permissions(administrator=True)
    async def force_belly_decay(self, ctx, ticks: int, minutes: int):
        await self.chao_decay_cog.force_belly_decay(ctx, ticks=ticks, minutes=minutes)

    @commands.command(name='force_energy_decay', help="(Admin) Adjust how often energy is reduced.")
    @commands.has_permissions(administrator=True)
    async def force_energy_decay(self, ctx, ticks: int, minutes: int):
        await self.chao_decay_cog.force_energy_decay(ctx, ticks=ticks, minutes=minutes)

    @commands.command(name='force_happiness_decay', help="(Admin) Adjust how often happiness is reduced.")
    @commands.has_permissions(administrator=True)
    async def force_happiness_decay(self, ctx, ticks: int, minutes: int):
        await self.chao_decay_cog.force_happiness_decay(ctx, ticks=ticks, minutes=minutes)

    @commands.command(name='force_hp_decay', help="(Admin) Adjust how often hp is reduced.")
    @commands.has_permissions(administrator=True)
    async def force_hp_decay(self, ctx, ticks: int, minutes: int):
        await self.chao_decay_cog.force_hp_decay(ctx, ticks=ticks, minutes=minutes)

    @commands.command(name='force_life_check', help="(Admin only) Force a Chao life check.")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)
    async def force_life_check(self, ctx, *, chao_name: str):
        await self.chao_helper_cog.force_life_check(ctx, chao_name=chao_name)

    @commands.command(name="force_grade_change", help="(Admin) Force a grade change on a chao. Usage: %force_grade_change @User ChaoName stat new_grade")
    @commands.has_permissions(administrator=True)
    async def force_grade_change(self, ctx, target: discord.Member, *, args: str):
        """
        Force-change a chao's grade for a given stat.
        
        Example:
        %force_grade_change @nickshouse Ka Chao power A
        This sets nickshouse's chao named "Ka Chao" so that its power grade is set to A.
        """
        # Split the arguments into words.
        args_list = args.split()
        if len(args_list) < 3:
            return await ctx.reply("Usage: %force_grade_change @User ChaoName stat new_grade")
        
        # The new grade is the last word, the stat is the second-to-last,
        # and the remaining words form the chao's name.
        new_grade = args_list[-1].upper()
        stat = args_list[-2].lower()
        chao_name = " ".join(args_list[:-2])
        
        valid_stats = ["power", "fly", "run", "swim"]
        if stat not in valid_stats:
            return await ctx.reply(f"{ctx.author.mention}, the stat must be one of: {', '.join(valid_stats)}.")
        
        # Retrieve the chao's data folder for the target.
        guild_id = str(ctx.guild.id)
        guild_name = ctx.guild.name
        # Update the server folder and then the user's folder.
        server_folder = self.data_utils.update_server_folder(ctx.guild)
        user_folder = self.data_utils.get_user_folder(server_folder, target)
        # The chao folder is expected to be in user_folder/chao_data/{chao_name}
        chao_folder = os.path.join(user_folder, "chao_data", chao_name)
        stats_file = os.path.join(chao_folder, f"{chao_name}_stats.parquet")
        if not os.path.exists(stats_file):
            return await ctx.reply(f"{ctx.author.mention}, no stats file found for **{chao_name}** of {target.mention}.")
        
        # Load the chao stats.
        chao_df = self.data_utils.load_chao_stats(stats_file)
        if chao_df.empty:
            return await ctx.reply(f"{ctx.author.mention}, no stats data found for **{chao_name}** of {target.mention}.")
        latest_stats = chao_df.iloc[-1].to_dict()
        
        # Determine which grade key to update.
        grade_key = f"{stat}_grade"
        # Get the valid grades list (assumed to be set in the ChaoHelper cog).
        grade_list = self.chao_helper_cog.GRADES  # e.g., ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
        if new_grade not in grade_list:
            return await ctx.reply(f"{ctx.author.mention}, {new_grade} is not a valid grade. Valid grades: {', '.join(grade_list)}.")
        
        # Update the grade.
        latest_stats[grade_key] = new_grade
        self.data_utils.save_chao_stats(stats_file, chao_df, latest_stats)
        await ctx.reply(f"{ctx.author.mention}, {target.mention}'s chao **{chao_name}** now has its {stat.capitalize()} grade set to {new_grade}.")




    @commands.command(name='force_happiness', help="Manually set Chao happiness (0-10).")
    @ensure_user_initialized
    @commands.has_permissions(administrator=True)
    async def force_happiness(self, ctx, chao_name: str, happiness_value: int):
        if not (0 <= happiness_value <= 10):
            return await ctx.reply(
                f"{ctx.author.mention}, happiness must be a value between 0 and 10."
            )
        await self.chao_helper_cog.force_happiness(
            ctx, chao_name=chao_name, happiness_value=happiness_value
        )

    @commands.command(name='restore', help="Restore your Chao data.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    async def restore(self, ctx, *, args: str):
        await self.data_utils.restore(ctx, args=args)

    @commands.command(name='goodbye', help="Send Chao away to the faraway Chao Forest.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def goodbye(self, ctx, *, chao_name: str = None):
        await self.chao_cog.goodbye(ctx, chao_name=chao_name)

    @commands.command(name='pet', help="Pet your Chao to make it happy!")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def pet(self, ctx, *, chao_name: str):
        await self.chao_cog.pet(ctx, chao_name=chao_name)

    @commands.command(name='grades', help="View a Chao's grades.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def grades(self, ctx, *, chao_name: str):
        await self.chao_cog.grades(ctx, chao_name=chao_name)

    @commands.command(name='throw', help="Throw your Chao!")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def throw(self, ctx, *, chao_name: str):
        await self.chao_cog.throw_chao(ctx, chao_name=chao_name)

    @commands.command(name='stats', help="View a Chao's stats.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def stats(self, ctx, *, chao_name: str):
        await self.chao_helper_cog.stats(ctx, chao_name=chao_name)

    @commands.command(name='feed', help="Feed a fruit to your Chao.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    async def feed(self, ctx, *, chao_name_and_fruit: str):
        chao_helper_cog = self.bot.get_cog("ChaoHelper")
        if not chao_helper_cog:
            return await ctx.reply("ChaoHelper cog not loaded.")
        await chao_helper_cog.feed(ctx, chao_name_and_fruit=chao_name_and_fruit)

    @commands.command(name='rename', help="Rename your Chao.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_lifecycle
    @ensure_chao_hatched
    @ensure_not_in_cacoon
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
        help_text += "**$rename** - Rename your Chao. 15 character limit.\nExample: `$rename Chaozhu BetterChaozhu`\n\n"
        help_text += "**$listchao** - See a list of your Chao.\nExample: `$listchao`\n\n"
        help_text += "**Source Code** - `https://github.com/nickshouse/Chao-Bot`\n"

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
