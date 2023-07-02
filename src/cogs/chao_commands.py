from discord.ext import commands
import asyncio
import random
import discord

class ChaoCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.egg_cog = self.bot.get_cog("Egg")
        self.database_cog = self.bot.get_cog("Database")
        self.black_market_cog = self.bot.get_cog("BlackMarket")
        self.embed_color = 0xADD8E6


    @commands.command()
    async def check_chao(self, ctx, member: discord.Member = None):
        """Show the user or a specified member all of their Chao"""
        member = member or ctx.author
        guild_id = ctx.guild.id
        user_id = member.id
        chao_data = await self.database_cog.get_data(guild_id, user_id, 'chao')

        if chao_data.empty:
            await ctx.send(f"{member.name} doesn't have any Chao.")
        else:
            chao_list = [chao for chao in chao_data['chao'].tolist() if chao is not None]
            if chao_list:
                await ctx.send(f"{member.name} has the following Chao:\n- " + "\n- ".join(chao_list))
            else:
                await ctx.send(f"{member.name} doesn't have any Chao.")

    @commands.command()
    async def check_eggs(self, ctx, member: discord.Member = None):
        """Show the user or a specified member all of their Chao Eggs"""
        member = member or ctx.author
        guild_id = ctx.guild.id
        user_id = member.id
        egg_data = await self.database_cog.get_data(guild_id, user_id, 'egg')

        if egg_data.empty:
            await ctx.send(f"{member.name} doesn't have any Chao Eggs.")
        else:
            egg_list = [egg for egg in egg_data['egg'].tolist() if egg is not None]
            if egg_list:
                await ctx.send(f"{member.name} has the following Chao Eggs:\n- " + "\n- ".join(egg_list))
            else:
                await ctx.send(f"{member.name} doesn't have any Chao Eggs.")



    @commands.command()
    async def rings(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        df = await self.bot.cogs['Database'].get_data(ctx.guild.id, str(member.id), 'rings')

        if df is None or 'rings' not in df.columns or df['rings'].sum() < 0:
            await ctx.send(f"{member.name} has no Rings yet.")
        else:
            rings = int(df['rings'].sum())
            embed = discord.Embed(title=f"{member.name}'s Rings", description=f"{member.name} has {rings} Rings!", color=self.embed_color)
            await ctx.send(embed=embed)


    @commands.command()
    async def gift(self, ctx, *args):
        member = None
        amount = 1
        item = None

        # parse args for member, item, and amount
        for arg in args:
            if arg.startswith('<@') and arg.endswith('>'):  # this is how mentions look in the message content
                # remove special characters to get the user ID, convert it to an int, then get the corresponding member object
                member_id = int(arg.strip('<@!>'))
                member = ctx.guild.get_member(member_id)
            elif arg.isdigit():
                amount = int(arg)
            else:
                if item is None:
                    item = arg.lower()
                else:
                    item = item + " " + arg.lower()

        if member is None:
            await ctx.send("You didn't mention a member.")
            return

        if item is None:
            await ctx.send("You didn't specify an item.")
            return

        # making the item name plural if it's not
        if item.endswith("s"):
            item_singular = item[:-1]
            item_plural = item
        else:
            item_singular = item
            item_plural = item + "s"

        if item_singular == 'ring':
            # handle gifting rings
            df = await self.bot.cogs['Database'].get_data(ctx.guild.id, str(ctx.author.id), 'rings')

            if df.empty or df['rings'].sum() < amount:
                await ctx.send("You do not have enough rings to make this gift.")
                return

            await self.bot.cogs['Database'].store_data(ctx.guild.id, str(ctx.author.id), [(-amount, 'rings')])
            await self.bot.cogs['Database'].store_data(ctx.guild.id, str(member.id), [(amount, 'rings')])

            item = item_singular if amount == 1 else item_plural
            await ctx.send(f"You have gifted {amount} {item} to {member.name}.")
        else:
            # handle gifting items
            self.database_cog = self.bot.get_cog('Database')
            df = await self.database_cog.get_data(str(ctx.guild.id), str(ctx.author.id), item_singular)

            if df is None:
                await ctx.send(f"The item '{item_singular}' doesn't exist in your inventory.")
                return

            if df[item_singular].sum() < amount:
                await ctx.send(f"You do not have enough '{item_singular}' to gift.")
                return

            await self.database_cog.store_data(str(ctx.guild.id), str(ctx.author.id), [(-amount, item_singular)])
            await self.database_cog.store_data(str(ctx.guild.id), str(member.id), [(amount, item_singular)])

            item = item_singular if amount == 1 else item_plural
            await ctx.send(f"You have gifted {amount} '{item}' to {member.name}.")


    @commands.command()
    async def sell(self, ctx, *args):
        db_cog = self.bot.get_cog('Database')

        item = None
        quantity = 1

        # Parse args for item and quantity
        for arg in args:
            if arg.isdigit():
                quantity = int(arg)
            else:
                if item is None:
                    item = arg.lower()
                else:
                    item = item + " " + arg.lower()

        # If no item specified, send an error message
        if item is None:
            await ctx.send("You didn't specify an item to sell.")
            return

        item = item.rstrip('s')  # remove trailing 's'

        fruit = next((fruit for fruit in self.black_market_cog.fruits if fruit['name'].lower() == item), None)
        if fruit is None:
            await ctx.send(f"Item '{item}' does not exist.")
            return

        df = await db_cog.get_data(str(ctx.guild.id), str(ctx.author.id), item)

        if df is None or df[item].sum() < quantity:
            await ctx.send(f"You do not have enough '{item}' to sell.")
            return

        price = int(0.8 * 15 * quantity)  # 80% of the black market price

        await db_cog.store_data(str(ctx.guild.id), str(ctx.author.id), [(price, 'rings'), (-quantity, item)])

        # Adjust item name for quantity
        item_name = item if quantity == 1 else item + 's'

        await ctx.send(f"You have sold {quantity} '{item_name}' for {price} rings.")


async def setup(bot):
    await bot.add_cog(ChaoCommands(bot))
    print("Chao Commands cog loaded")
