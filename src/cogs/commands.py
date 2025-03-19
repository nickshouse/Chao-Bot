# cogs/commands.py

import discord
import os
from discord.ext import commands
from discord import app_commands
from decorators import (
    ensure_user_initialized, ensure_chao_alive,
    ensure_chao_hatched, ensure_not_in_cacoon
)

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None
        self.chao_helper_cog = None
        self.chao_admin_cog = None
        self.chao_lifecycle_cog = None
        self.data_utils = None
        self.black_market_cog = None
        self.chao_decay_cog = None

    async def cog_load(self):
        """
        Fetch the relevant cogs from the bot. We must also fetch 'ChaoLifecycle'
        so that self.chao_lifecycle_cog is not None.
        """
        self.chao_cog = self.bot.get_cog('Chao')
        self.chao_helper_cog = self.bot.get_cog('ChaoHelper')
        self.chao_admin_cog = self.bot.get_cog('ChaoAdmin')
        self.chao_lifecycle_cog = self.bot.get_cog('ChaoLifecycle')
        self.data_utils = self.bot.get_cog('DataUtils')
        self.black_market_cog = self.bot.get_cog('BlackMarket')
        self.chao_decay_cog = self.bot.get_cog('ChaoDecay')

        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.chao_helper_cog:
            raise Exception("ChaoHelper cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.chao_admin_cog:
            raise Exception("ChaoAdmin cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.chao_lifecycle_cog:
            raise Exception("ChaoLifecycle cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.data_utils:
            raise Exception("DataUtils cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.black_market_cog:
            raise Exception("BlackMarket cog is not loaded. Ensure it is loaded before the Commands cog.")
        if not self.chao_decay_cog:
            raise Exception("ChaoDecay cog is not loaded. Ensure it is loaded before the Commands cog.")

    # --------------------------------------------------
    # Slash Command Implementations
    # --------------------------------------------------

    @app_commands.command(name="chao", description="Start your Chao journey!")
    async def chao(self, interaction: discord.Interaction):
        await self.chao_cog.chao(interaction)

    @app_commands.command(name="hatch", description="Hatch a new Chao egg!")
    @ensure_user_initialized
    async def hatch(self, interaction: discord.Interaction):
        await self.chao_cog.hatch(interaction)

    @app_commands.command(name="market", description="Access the Chao black market.")
    @ensure_user_initialized
    @app_commands.describe(market_type="Optional market type (e.g. 'fruit', 'eggs').")
    async def market(self, interaction: discord.Interaction, market_type: str = None):
        await self.black_market_cog.market(interaction, market_type=market_type)

    @app_commands.command(name="buy", description="Buy items from the Chao black market.")
    @ensure_user_initialized
    @app_commands.describe(
        item="Item to buy",
        amount="Quantity of the item to buy"
    )
    async def buy(self, interaction: discord.Interaction, item: str, amount: int):
        await self.black_market_cog.buy(interaction, item=item, amount=amount)

    @buy.autocomplete("item")
    async def buy_item_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.black_market_cog.buy_item_autocomplete(interaction, current)

    @app_commands.command(name="inventory", description="View your current inventory.")
    @ensure_user_initialized
    async def inventory(self, interaction: discord.Interaction):
        await self.chao_cog.inventory(interaction)

    @app_commands.command(name="egg", description="Give yourself a Chao egg.")
    @ensure_user_initialized
    async def egg(self, interaction: discord.Interaction):
        await self.chao_cog.egg(interaction)

    @app_commands.command(name="give_rings", description="(Admin) Add rings to your account.")
    @ensure_user_initialized
    @app_commands.checks.has_permissions(administrator=True)
    async def give_rings(self, interaction: discord.Interaction):
        await self.chao_cog.give_rings(interaction)

    @app_commands.command(name="listchao", description="List all the Chao you own.")
    @ensure_user_initialized
    @ensure_chao_alive
    async def listchao(self, interaction: discord.Interaction):
        await self.chao_cog.list_chao(interaction)

    @app_commands.command(name="force_belly_decay", description="(Admin) Adjust how often belly is reduced.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(ticks="Number of ticks", minutes="Delay in minutes")
    async def force_belly_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        await self.chao_decay_cog.force_belly_decay(interaction, ticks=ticks, minutes=minutes)

    @app_commands.command(name="force_energy_decay", description="(Admin) Adjust how often energy is reduced.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(ticks="Number of ticks", minutes="Delay in minutes")
    async def force_energy_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        await self.chao_decay_cog.force_energy_decay(interaction, ticks=ticks, minutes=minutes)

    @app_commands.command(name="force_happiness_decay", description="(Admin) Adjust how often happiness is reduced.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(ticks="Number of ticks", minutes="Delay in minutes")
    async def force_happiness_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        await self.chao_decay_cog.force_happiness_decay(interaction, ticks=ticks, minutes=minutes)

    @app_commands.command(name="force_hp_decay", description="(Admin) Adjust how often hp is reduced.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(ticks="Number of ticks", minutes="Delay in minutes")
    async def force_hp_decay(self, interaction: discord.Interaction, ticks: int, minutes: int):
        await self.chao_decay_cog.force_hp_decay(interaction, ticks=ticks, minutes=minutes)

    @app_commands.command(name="force_life_check", description="(Admin) Force a Chao life check.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(chao_name="Name of the Chao")
    async def force_life_check(self, interaction: discord.Interaction, chao_name: str):
        await self.chao_admin_cog.force_life_check(interaction, chao_name=chao_name)

    @app_commands.command(name="force_grade_change", description="(Admin) Force a grade change on a Chao.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(target="User", args="ChaoName stat new_grade")
    async def force_grade_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        await self.chao_admin_cog.force_grade_change(interaction, target, args)

    @app_commands.command(name="force_exp_change", description="(Admin) Force change a Chao's EXP for a given stat")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(target="User", args="ChaoName stat new_exp_value")
    async def force_exp_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        await self.chao_admin_cog.force_exp_change(interaction, target, args)

    @app_commands.command(name="force_level_change", description="(Admin) Force change a Chao's level for a given stat.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(target="User", args="ChaoName stat new_level_value")
    async def force_level_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        await self.chao_admin_cog.force_level_change(interaction, target, args)

    @app_commands.command(name="force_face_change", description="(Admin) Force change a Chao's face attribute.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(target="User", args="ChaoName face_type new_value")
    async def force_face_change(self, interaction: discord.Interaction, target: discord.Member, args: str):
        await self.chao_admin_cog.force_face_change(interaction, target, args)

    @app_commands.command(name="force_happiness", description="(Admin) Manually set Chao happiness (0-10).")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(chao_name="Chao's name", happiness_value="Happiness (0-10)")
    async def force_happiness(self, interaction: discord.Interaction, chao_name: str, happiness_value: int):
        if not (0 <= happiness_value <= 10):
            return await interaction.response.send_message(
                f"{interaction.user.mention}, happiness must be between 0 and 10.", ephemeral=True
            )
        await self.chao_admin_cog.force_happiness(interaction, chao_name=chao_name, happiness_value=happiness_value)

    @app_commands.command(name="graveyard", description="See a list of all the Chao in the server that have passed on.")
    async def graveyard(self, interaction: discord.Interaction):
        await self.chao_helper_cog.graveyard(interaction)

    @app_commands.command(name="stats", description="View a Chao's stats.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(chao_name="Name of the Chao")
    async def stats(self, interaction: discord.Interaction, chao_name: str):
        await self.chao_helper_cog.stats(interaction, chao_name=chao_name)
    
    @stats.autocomplete("chao_name")
    async def stats_chao_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.chao_helper_cog.stats_autocomplete(interaction, current)

    @app_commands.command(name="restore", description="Restore your Chao's data to an earlier date.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_not_in_cacoon
    @app_commands.describe(args="E.g. 'Chaozilla 2024-07-22'")
    async def restore(self, interaction: discord.Interaction, args: str):
        await self.data_utils.restore(interaction, args=args)

    @app_commands.command(name="goodbye", description="Send your Chao away to the faraway Chao Forest.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(chao_name="Optional: Name of the Chao to send away")
    async def goodbye(self, interaction: discord.Interaction, chao_name: str = None):
        await self.chao_cog.goodbye(interaction, chao_name=chao_name)

    @app_commands.command(name="pet", description="Pet your Chao to make it happy!")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(chao_name="Name of the Chao")
    async def pet(self, interaction: discord.Interaction, chao_name: str):
        await self.chao_cog.pet(interaction, chao_name=chao_name)

    @app_commands.command(name="grades", description="View a Chao's grades.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(chao_name="Name of the Chao")
    async def grades(self, interaction: discord.Interaction, chao_name: str):
        await self.chao_cog.grades(interaction, chao_name=chao_name)

    @app_commands.command(name="throw", description="Throw your Chao! (Makes it unhappy).")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(chao_name="Name of the Chao")
    async def throw(self, interaction: discord.Interaction, chao_name: str):
        await self.chao_cog.throw_chao(interaction, chao_name=chao_name)

    @app_commands.command(name="feed", description="Feed a fruit to your Chao.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(
        chao_name="Name of the Chao",
        fruit="Type of fruit to feed",
        amount="Amount of the specified fruit (default: 1)"
    )
    async def feed(self, interaction: discord.Interaction, chao_name: str, fruit: str, amount: int = 1):
        await self.chao_lifecycle_cog.feed(interaction, chao_name=chao_name, fruit=fruit, amount=amount)

    @feed.autocomplete("chao_name")
    async def feed_chao_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.chao_lifecycle_cog.feed_chao_autocomplete(interaction, current)

    @feed.autocomplete("fruit")
    async def feed_fruit_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.chao_lifecycle_cog.feed_fruit_autocomplete(interaction, current)

    @app_commands.command(name="rename", description="Rename your Chao.")
    @ensure_user_initialized
    @ensure_chao_alive
    @ensure_chao_hatched
    @ensure_not_in_cacoon
    @app_commands.describe(current_name="Current name of your Chao", new_name="New name for your Chao")
    async def rename(self, interaction: discord.Interaction, current_name: str, new_name: str):
        await self.chao_cog.rename(interaction, current_name=current_name, new_name=new_name)
    
    @rename.autocomplete("current_name")
    async def rename_current_autocomplete(self, interaction: discord.Interaction, current: str):
        return await self.chao_cog.rename_autocomplete(interaction, current)

    @app_commands.command(name="help", description="Show all available commands.")
    async def help(self, interaction: discord.Interaction):
        help_text = "**Available Commands:**\n\n"
        help_text += "**/chao** - Start using Chao Bot.\nExample: `/chao`\n\n"
        help_text += "**/plans** - View upcoming features and plans for the Chao Bot.\nExample: `/plans`\n\n"
        help_text += "**/hatch** - Hatch a new Chao egg.\nExample: `/hatch`\n\n"
        help_text += "**/egg** - Receive a new Chao egg. Only 1 at a time.\nExample: `/egg`\n\n"
        help_text += "**/grades** - View a Chao's grades.\nExample: `/grades Chaozart`\n\n"
        help_text += "**/goodbye** - Send your Chao away from the server.\nExample: `/goodbye`\n\n"
        help_text += "**/throw** - Throw your Chao to make it unhappy. Use carefully!\nExample: `/throw Chaoster`\n\n"
        help_text += "**/market** - Access the Black Market.\nExample: `/market`\n\n"
        help_text += "**/buy** - Buy items from the Chao black market.\nExample: `/buy garden nut 3`\n\n"
        help_text += "**/pet** - Pet your Chao to make it happy.\nExample: `/pet Chaowser`\n\n"
        help_text += "**/inventory** - View your current inventory.\nExample: `/inventory`\n\n"
        help_text += "**/restore** - Restore your Chao's data to an earlier date. USE WITH CAUTION.\nExample: `/restore \"Chaozilla 2024-07-22\"`\n\n"
        help_text += "**/stats** - View a Chao's stats.\nExample: `/stats Chaolin`\n\n"
        help_text += "**/feed** - Feed a fruit to your Chao.\nExample: `/feed \"Chaoko Run Fruit\"`\n\n"
        help_text += "**/rename** - Rename your Chao. 15 character limit.\nExample: `/rename \"Chaozhu BetterChaozhu\"`\n\n"
        help_text += "**/listchao** - See a list of your Chao.\nExample: `/listchao`\n\n"
        help_text += "**/graveyard** - See a list of all the Chao in the server that have passed on...\nExample: `/graveyard`\n\n"
        help_text += "**Source Code** - `https://github.com/nickshouse/Chao-Bot`\n"

        embed = discord.Embed(title="Chao Bot Help", description=help_text, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="plans", description="View upcoming features and plans for the Chao Bot.")
    async def plans(self, interaction: discord.Interaction):
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
            "- Chao Mating\n"
            "- Purchasable background colors for stat cards\n"
            "- X rank\n"
            "- Chao export tool\n"
            "- Chao forest\n"
            "- Daily drops\n"
            "- Chao fishing\n"
            "- Chao Racing collab?\n"
        )
        embed = discord.Embed(title="Upcoming Features and Plans", description=plans_text, color=discord.Color.green())
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot): 
    await bot.add_cog(Commands(bot))
