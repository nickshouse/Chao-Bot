import asyncio
import random
import datetime
import discord
from discord.ext import commands


class Chao(commands.Cog):
    chao_colors = ['White', 'Blue', 'Red', 'Yellow', 'Orange', 'Sky Blue', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    chao_types = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def give_egg(self, ctx):
        """Give a Chao Egg to the user"""
        color = random.choice(self.chao_colors)
        chao_type = random.choice(self.chao_types)
        chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()

        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        while any(chao['name'] == chao_name for chao in chao_list):
            chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()
        
        grades = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
        stats = ['Swim', 'Fly', 'Run', 'Power', 'Intel', 'Stamina']
        chao = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None,
        }

        for stat in stats:
            grade = random.choice(grades)
            chao[f'{stat.lower()}_grade'] = grade
            chao[f'{stat.lower()}_ticks'] = 0
            chao[f'{stat.lower()}_exp'] = 0
            chao[f'{stat.lower()}_level'] = 0

        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        
        # Send egg received message
        await ctx.send(f"You received a {color} {chao_type} Chao Egg named {chao_name}! It will hatch in 5 seconds.")

        # Simulate waiting for 5 seconds before the egg hatches
        await asyncio.sleep(5)
        
        chao['hatched'] = 1
        chao['birth_date'] = datetime.datetime.utcnow().date()  # Save the birth date in UTC
        chao['hp_ticks'] = 10  # Set hp_ticks to 10 upon hatching
        
        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)
        
        # Send egg hatched message
        await ctx.send(f"Your {chao_name} Egg has hatched into a {color} {chao_type} Chao named {chao_name}!")

    @commands.command()
    async def view_chao(self, ctx, chao_name):
        """View the stats of a specified Chao"""
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)

        chao_to_view = next((chao for chao in chao_list if chao['name'] == chao_name), None)

        if chao_to_view:
            embed = discord.Embed(title=f"{chao_name}'s Stats", color=discord.Color.blue())
            embed.add_field(name="Color", value=chao_to_view['color'], inline=True)
            embed.add_field(name="Type", value=chao_to_view['type'], inline=True)
            embed.add_field(name="Hatched", value="Yes" if chao_to_view['hatched'] else "No", inline=True)
            # ... add more fields as desired

            embed.set_image(url="https://i.imgur.com/mrYeC6K.png")

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"You don't have a Chao named {chao_name}.")

    @commands.command()
    async def feed(self, ctx, chao_name, *args):
        """Feed a Chao a specified item"""
        db_cog = self.bot.get_cog('Database')

        item_name = ' '.join(args).rstrip('s').lower()

        # Check if the user has a Chao with the specified name
        chao_list = await db_cog.get_chao(ctx.guild.id, ctx.author.id)
        chao_to_feed = next((chao for chao in chao_list if chao['name'].lower() == chao_name.lower()), None)

        if chao_to_feed is None:
            await ctx.send(f"You don't have a Chao named {chao_name}.")
            return

        # Check if the user has the specified item in their inventory
        inventory_df = await db_cog.get_inventory(ctx.guild.id, ctx.author.id)
        if inventory_df is not None and not inventory_df[inventory_df['item'].str.lower() == item_name].empty:
            inventory_item = inventory_df.loc[inventory_df['item'].str.lower() == item_name]

            # Check if the user has enough quantity of the item
            if inventory_item.empty or inventory_item.iloc[0]['quantity'] <= 0:
                await ctx.send(f"You don't have a(n) {item_name} in your inventory.")
                return

            inventory_df.loc[inventory_df['item'].str.lower() == item_name, 'quantity'] -= 1
            await db_cog.store_inventory(ctx.guild.id, ctx.author.id, inventory_df)
            
        else:
            await ctx.send(f"You don't have a(n) {item_name} in your inventory.")
            return

        # Update Chao's stats based on the item
        item_stat_effects = {
            'power fruit': 'power_ticks',
            'run fruit': 'run_ticks',
            'swim fruit': 'swim_ticks',
            'fly fruit': 'fly_ticks',
            'garden fruit': 'stamina_ticks',
            'smart fruit': 'intel_ticks'  # smart fruit added
        }

        stat_to_update = item_stat_effects.get(item_name.lower(), None)
        if stat_to_update is not None:
            chao_to_feed[stat_to_update] += 1  # increment the stat
            chao_to_feed['hp_ticks'] = min(chao_to_feed['hp_ticks'] + 1, 10)  # increment hp_ticks for any fruit, but cap at 10
            level_up_message = ""

            # Check if the ticks have reached 10
            if chao_to_feed[stat_to_update] >= 10:
                chao_to_feed[stat_to_update] = 0  # reset ticks
                stat_level = stat_to_update.rsplit('_', 1)[0] + '_level'  # corresponding level stat
                chao_to_feed[stat_level] += 1  # level up
                level_up_message = f"\n{chao_name}'s {stat_level.replace('_', ' ')} has increased to level {chao_to_feed[stat_level]}!"

        # Update the image if a stat-affecting fruit is fed
        if item_name.lower() in item_stat_effects:
            # Getting the stat name from stat_to_update e.g. 'power' from 'power_ticks'
            stat_name = stat_to_update.rsplit('_', 1)[0]
            
            # Save the updated chao data back to the database and await its completion
            await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)
            
            # Now call generate_image after store_chao has completed
            await self.bot.cogs['Generator'].generate_image(ctx, chao_name, stat_name, chao_to_feed[stat_to_update])

            await ctx.send(f"You fed a(n) {item_name} to {chao_name}! {chao_name}'s {stat_to_update.replace('_', ' ')} increased!{level_up_message}")
        else:
            # If it's not a stat-affecting fruit, just store the updated chao data
            await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)


async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
