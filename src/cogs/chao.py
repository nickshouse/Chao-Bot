import asyncio
import random
import datetime
import discord
from discord.ext import commands


class Chao(commands.Cog):
    chao_colors = ['White', 'Blue', 'Red', 'Yellow', 'Orange', 'Sky Blue', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    chao_types = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']
    grade_to_value = {'F': -1, 'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'X': 6}  # Mapping from grade to value

    def __init__(self, bot):
        self.bot = bot

    def calculate_exp_gain(self, grade):
        return (self.grade_to_value[grade] * 3) + 13

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
            'smart fruit': 'intel_ticks'
        }

        stat_to_update = item_stat_effects.get(item_name.lower(), None)
        if stat_to_update is not None:
            random_tick_increase = random.randint(1, 3)  # Random tick increase between 1 and 3 inclusive
            new_ticks = chao_to_feed[stat_to_update] + random_tick_increase
            level_up = False

            # Check for level up
            if new_ticks >= 10:
                level_up = True
                new_ticks = new_ticks % 10  # roll over the ticks

            chao_to_feed[stat_to_update] = new_ticks
            chao_to_feed['hp_ticks'] = min((chao_to_feed['hp_ticks'] + random_tick_increase) % 10, 10)  # increment hp_ticks and roll over if >= 10, but cap at 10
            level_up_message = ""

            if level_up:
                stat_level = stat_to_update.rsplit('_', 1)[0] + '_level'
                stat_exp = stat_to_update.rsplit('_', 1)[0] + '_exp'
                stat_grade = stat_to_update.rsplit('_', 1)[0] + '_grade'

                chao_to_feed[stat_level] += 1  # level up

                exp_gain = self.calculate_exp_gain(chao_to_feed[stat_grade])
                chao_to_feed[stat_exp] += exp_gain  # add calculated experience points to the stat

                level_up_message = f"\n{chao_name}'s {stat_level.replace('_', ' ')} has increased to level {chao_to_feed[stat_level]} and gained {exp_gain} {stat_exp.replace('_', ' ')}!"

            await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)

            # Now call generate_image after store_chao has completed
            await self.bot.cogs['Generator'].generate_image(ctx, chao_name, stat_to_update.rsplit('_', 1)[0], chao_to_feed[stat_to_update])

            await ctx.send(f"You fed a(n) {item_name} to {chao_name}! {chao_name}'s {stat_to_update.replace('_', ' ')} increased by {random_tick_increase}!{level_up_message}")
        else:
            # If it's not a stat-affecting fruit, just store the updated chao data
            await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)


async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
