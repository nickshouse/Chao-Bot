import discord
from discord.ext import commands
from discord import Embed
import pandas as pd

class BlackMarket(commands.Cog):
    fruits = [
        {"emoji": "🍎", "name": "Garden Fruit"},
        {"emoji": "🍏", "name": "Hero Fruit"},
        {"emoji": "🍊", "name": "Dark Fruit"},
        {"emoji": "🍋", "name": "Round Fruit"},
        {"emoji": "🍌", "name": "Triangle Fruit"},
        {"emoji": "🍉", "name": "Heart Fruit"},
        {"emoji": "🍆", "name": "Square Fruit"},
        {"emoji": "🍇", "name": "Chao Fruit"},
        {"emoji": "🍓", "name": "Smart Fruit"},
        {"emoji": "🍒", "name": "Power Fruit"},
        {"emoji": "🍑", "name": "Run Fruit"},
        {"emoji": "🍐", "name": "Swim Fruit"},
        {"emoji": "🍍", "name": "Fly Fruit"},
        {"emoji": "🥝", "name": "Tasty Fruit"},
        {"emoji": "🍄", "name": "Strange Mushroom"},
    ]

    chaos_drives = [
        {"emoji": "🪛", "name": "Hero Drive"},
        {"emoji": "🪛", "name": "Dark Drive"},
        {"emoji": "🪛", "name": "Smart Drive"},
        {"emoji": "🪛", "name": "Luck Drive"},
        {"emoji": "🪛", "name": "Power Drive"},
        {"emoji": "🪛", "name": "Swim Drive"},
        {"emoji": "🪛", "name": "Run Drive"},
        {"emoji": "🪛", "name": "Swim Drive"},
        {"emoji": "🪛", "name": "Fly Drive"},
        {"emoji": "🪛", "name": "Strange Drive"},
    ]

    def __init__(self, bot):
        self.bot = bot
        self.embed_color = 0x1abc9c  # Replace this with the color you want to use for your embeds

    @commands.command()
    async def buy(self, ctx, *args):
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

        item = item.rstrip('s')  # remove trailing 's'

        # If no item specified, send an error message
        if item is None:
            await ctx.send("You didn't specify an item to buy.")
            return

        fruit = next((fruit for fruit in self.fruits if fruit['name'].lower() == item), None)
        if fruit is None:
            await ctx.send(f"Item '{item}' does not exist.")
            return

        price = 15 * quantity

        balance = await db_cog.get_rings(str(ctx.guild.id), str(ctx.author.id))

        if balance < price:
            await ctx.send(f"You do not have enough rings to buy {quantity} '{item}'.")
            return

        new_balance = balance - price
        await db_cog.store_rings(str(ctx.guild.id), str(ctx.author.id), new_balance)

        inventory = await db_cog.get_inventory(str(ctx.guild.id), str(ctx.author.id))
        new_data = pd.DataFrame([(quantity, item)], columns=['quantity', 'item'])
        if inventory is None:
            inventory = new_data
        else:
            inventory = pd.concat([inventory, new_data], ignore_index=True)
        await db_cog.store_inventory(str(ctx.guild.id), str(ctx.author.id), inventory)

        # Adjust item name for quantity
        item_name = item if quantity == 1 else item + 's'

        await ctx.send(f"You have bought {quantity} '{item_name}' for {price} rings.")


            
    @commands.command()
    async def market(self, ctx):
        embed = Embed(title="Black Market", description="Here's what you can buy:", color=self.embed_color)

        fruits = [dict(fruit, price=15) for fruit in self.fruits]

        for i in range(0, len(fruits), 3):
            for j in range(3):
                if i+j < len(fruits):
                    fruit = fruits[i+j]
                    embed.add_field(name=f'{fruit["emoji"]} {fruit["name"]}', value=f'Price: {fruit["price"]} rings\n', inline=True)
                else:
                    embed.add_field(name='\u200b', value='\u200b', inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    async def inventory(self, ctx):
        db_cog = self.bot.get_cog('Database')
        user_id = str(ctx.author.id)
        embed = Embed(title=f"{ctx.author.name}'s Inventory", description="Here's what you have:", color=self.embed_color)

        df = await db_cog.get_inventory(str(ctx.guild.id), user_id)
        
        if df is not None:
            grouped_df = df.groupby('item').sum().reset_index()
            inventory_items = grouped_df.to_dict('records')

            for i in range(0, len(inventory_items), 3):
                for j in range(3):
                    if i+j < len(inventory_items):
                        item = inventory_items[i+j]
                        embed.add_field(name=item['item'].capitalize(), value=f'Quantity: {item["quantity"]}\n', inline=True)
                    else:
                        embed.add_field(name='\u200b', value='\u200b', inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    async def give_rings(self, ctx):
        db_cog = self.bot.get_cog('Database')
        guild_id = str(ctx.guild.id)
        user_id = str(ctx.author.id)

        # Add the rings to the user's current rings
        current_rings = await db_cog.get_rings(guild_id, user_id)
        if current_rings is None:
            new_rings = 100000
        else:
            new_rings = current_rings + 100000

        # Store the new amount of rings
        await db_cog.store_rings(guild_id, user_id, new_rings)

        await ctx.send(f"You have been given 100,000 rings! You now have {new_rings} rings.")



async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
    print("Black Market cog loaded")
