import asyncio
import random
import datetime
from discord.ext import commands
from typing import Dict, Optional, List

class Chao(commands.Cog):
    CHAO_COLORS = ['Regular', 'White', 'Blue', 'Red', 'Yellow', 'Orange', 'Pink', 'Green', 'Mint', 'Brown', 'Purple', 'Grey', 'Lime Green', 'Black']
    CHAO_TYPES = ['Monotone', 'Two-tone', 'Jewel Monotone', 'Shiny Monotone', 'Jewel Two-tone', 'Shiny Two-tone', 'Shiny Jewel']
    GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S', 'X']
    GRADE_TO_VALUE = {'F': -1, 'E': 0, 'D': 1, 'C': 2, 'B': 3, 'A': 4, 'S': 5, 'X': 6}
    STATS = ['Swim', 'Fly', 'Run', 'Power', 'Mind', 'Stamina']

    def __init__(self, bot):
        self.bot = bot

    def calculate_exp_gain(self, grade: str) -> int:
        return (self.GRADE_TO_VALUE[grade] * 3) + 13
    
    
    async def chao_command(self, ctx):
        db_cog = self.bot.get_cog('Database')
        user_initialized = await db_cog.is_user_initialized(ctx.guild.id, ctx.author.id)

        if user_initialized:
            await ctx.send(f"{ctx.author.mention}\nYou are already using Chao Bot!")
        else:
            # Create necessary directories and initialize data as needed
            await db_cog.initialize_user_data(ctx.guild.id, ctx.author.id)
            await ctx.send(f"{ctx.author.mention}\nWelcome to Chao Bot!")


    async def give_egg_command(self, ctx):
        color, chao_type = random.choice(self.CHAO_COLORS), random.choice(self.CHAO_TYPES)
        chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()

        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)
        while any(chao['name'] == chao_name for chao in chao_list):
            chao_name = self.bot.cogs['FortuneTeller'].generate_chao_name()

        chao_data = {
            'name': chao_name,
            'color': color,
            'type': chao_type,
            'hatched': 0,
            'birth_date': None,
        }

        for stat in self.STATS:
            grade = random.choice(self.GRADES)
            chao_data.update({f'{stat.lower()}_grade': grade, f'{stat.lower()}_ticks': 0, f'{stat.lower()}_exp': 0, f'{stat.lower()}_level': 0})

        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_data)
        await ctx.send(f"You received a {color} {chao_type} Chao Egg named {chao_name}! It will hatch in 5 seconds.")
        await asyncio.sleep(5)

        chao_data['hatched'] = 1
        chao_data['birth_date'] = datetime.datetime.utcnow().date()
        chao_data['hp_ticks'] = 10

        await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao_data)
        await ctx.send(f"Your {chao_name} Egg has hatched into a {color} {chao_type} Chao named {chao_name}!")


    async def feed_command(self, ctx, full_input: str):
        db_cog = self.bot.get_cog('Database')

        # Retrieve all Chao names for this user
        chao_list = await db_cog.get_chao(ctx.guild.id, ctx.author.id)
        chao_names = [chao['name'].lower() for chao in chao_list]

        # Split the input and iterate over it to find the Chao name and item name
        split_input = full_input.split()
        chao_name = None
        item_name = None
        for i in range(1, len(split_input) + 1):
            potential_chao_name = ' '.join(split_input[:i])
            if potential_chao_name.lower() in chao_names:
                chao_name = potential_chao_name
                item_name = ' '.join(split_input[i:]).rstrip('s').lower()
                break

        if not chao_name:
            await ctx.send(f"You don't have a Chao named {' '.join(split_input[:i-2])}.")
            return

        # Find the specific Chao to feed
        chao_to_feed = next((chao for chao in chao_list if chao['name'].lower() == chao_name.lower()), None)
        if not chao_to_feed:
            await ctx.send(f"Could not find data for Chao named {chao_name}.")
            return


        inventory_df = await db_cog.get_inventory(ctx.guild.id, ctx.author.id)
        if inventory_df is not None and not inventory_df[inventory_df['item'].str.lower() == item_name].empty:
            inventory_item = inventory_df.loc[inventory_df['item'].str.lower() == item_name]

            if inventory_item.empty or inventory_item.iloc[0]['quantity'] <= 0:
                await ctx.send(f"You don't have a(n) {item_name} in your inventory.")
                return

            inventory_df.loc[inventory_df['item'].str.lower() == item_name, 'quantity'] -= 1
            await db_cog.store_inventory(ctx.guild.id, ctx.author.id, inventory_df)
        else:
            await ctx.send(f"You don't have a(n) {item_name} in your inventory.")
            return

        item_stat_effects = {
            'power fruit': 'power_ticks',
            'run fruit': 'run_ticks',
            'swim fruit': 'swim_ticks',
            'fly fruit': 'fly_ticks',
            'garden fruit': 'stamina_ticks',
            'smart fruit': 'Mind_ticks'
        }

        stat_to_update = item_stat_effects.get(item_name.lower(), None)
        if stat_to_update is not None:
            random_tick_increase = random.randint(1, 3)
            new_ticks = chao_to_feed[stat_to_update] + random_tick_increase
            level_up = False

            if new_ticks >= 10:
                level_up = True
                new_ticks = new_ticks % 10

            chao_to_feed[stat_to_update] = new_ticks
            chao_to_feed['hp_ticks'] = min((chao_to_feed['hp_ticks'] + random_tick_increase) % 10, 10)
            level_up_message = ""

            if level_up:
                stat_level = f"{stat_to_update.rsplit('_', 1)[0]}_level"
                stat_exp = f"{stat_to_update.rsplit('_', 1)[0]}_exp"
                stat_grade = f"{stat_to_update.rsplit('_', 1)[0]}_grade"
                chao_to_feed[stat_level] += 1
                exp_gain = self.calculate_exp_gain(chao_to_feed[stat_grade])
                chao_to_feed[stat_exp] += exp_gain
                level_up_message = f"\n{chao_name}'s {stat_level.replace('_', ' ')} has increased to level {chao_to_feed[stat_level]} and gained {exp_gain} {stat_exp.replace('_', ' ')}!"

            await db_cog.store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)
            await self.bot.cogs['Generator'].generate_image_command(ctx, chao_name, stat_to_update.rsplit('_', 1)[0], chao_to_feed[stat_to_update])
            await ctx.send(f"You fed a(n) {item_name} to {chao_name}! {chao_name}'s {stat_to_update.replace('_', ' ')} increased by {random_tick_increase}!{level_up_message}")

        else:
            await db_cog.store_chao(ctx.guild.id, ctx.author.id, chao_to_feed)

async def setup(bot):
    await bot.add_cog(Chao(bot))
    print("Chao cog loaded")
