import discord
from discord.ext import commands
from functools import wraps
import random
import os
import pandas as pd
from datetime import datetime
from cogs.chao import Chao

# Configuration Constants
FRUIT_TICKS_MIN = 6
FRUIT_TICKS_MAX = 8

FRUIT_STATS = {
    "Garden Nut": 'stamina',
    "Hero Fruit": 'stamina',
    "Dark Fruit": 'stamina',
    "Round Fruit": 'stamina',
    "Triangle Fruit": 'stamina',
    "Heart Fruit": 'stamina',
    "Square Fruit": 'stamina',
    "Chao Fruit": 'all',
    "Smart Fruit": 'mind',
    "Power Fruit": 'power',
    "Run Fruit": 'run',
    "Swim Fruit": 'swim',
    "Fly Fruit": 'fly',
    "Tasty Fruit": 'stamina',
    "Strange Mushroom": 'stamina'
}

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chao_cog = None

    def cog_load(self):
        self.chao_cog = self.bot.get_cog('Chao')
        if not self.chao_cog:
            raise Exception("Chao cog is not loaded. Make sure it is loaded before the Commands cog.")

    def ensure_user_initialized(func):
        @wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            if not self.chao_cog.is_user_initialized(str(ctx.guild.id), str(ctx.author.id)):
                return await ctx.send(f"{ctx.author.mention}, please use the `$chao` command to start using the Chao Bot.")
            return await func(self, ctx, *args, **kwargs)
        return wrapper

    @commands.command(name='chao')
    async def chao(self, ctx):
        if await self.chao_cog.initialize_inventory(ctx, str(ctx.guild.id), str(ctx.author.id), "Welcome to Chao Bot!",
                                        "**You Receive:**\n- `1x Chao Egg`\n- `500x Rings`\n- `5x Garden Nut`\n\n"
                                        "**Example Commands:**\n- `$feed [Chao name] [item]` to feed your Chao.\n- `$race [Chao name]` to enter your Chao in a race.\n- `$train [Chao name] [stat]` to train a specific stat.\n- `$stats [Chao name]` to view your Chao's stats."): return

    @commands.command(name='hatch')
    @ensure_user_initialized
    async def hatch(self, ctx):
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.chao_cog.load_inventory(file_path)
        if (chao_egg_quantity := int(inventory_df.iloc[-1].get('Chao Egg', 0))) < 1:
            return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you do not have any Chao Eggs to hatch.")
        chao_dir, chao_name = self.chao_cog.get_path(guild_id, user_id, 'chao_data', ''), random.choice(self.chao_cog.chao_names)
        os.makedirs(chao_dir, exist_ok=True)
        while chao_name in [name for name in os.listdir(chao_dir) if os.path.isdir(os.path.join(chao_dir, name))]:
            chao_name = random.choice(self.chao_cog.chao_names)
        chao_path = os.path.join(self.chao_cog.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        os.makedirs(os.path.dirname(chao_path), exist_ok=True)
        inventory_df.at[inventory_df.index[-1], 'Chao Egg'] = chao_egg_quantity - 1
        self.chao_cog.save_inventory(file_path, inventory_df, inventory_df.iloc[-1].to_dict())
        pd.DataFrame({'hatched': [1], 'birth_date': [self.chao_cog.current_date.strftime("%Y-%m-%d")], 'hp_ticks': [0],
                    **{f"{stat}_ticks": [0] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
                    **{f"{stat}_level": [0] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
                    **{f"{stat}_exp": [0] for stat in ['swim', 'fly', 'run', 'power', 'mind', 'stamina']},
                    **{f"{stat}_grade": ['D'] for stat in ['power', 'swim', 'stamina', 'fly', 'run', 'mind']},
                    'alignment': [0], 'evolved': [False], 'Type': ['Normal']}).to_parquet(chao_path, index=False)
        await ctx.reply(file=discord.File(self.chao_cog.NEUTRAL_PATH, filename="neutral_normal_child.png"),
                        embed=discord.Embed(title="Your Chao Egg has hatched!", description=f"Your Chao Egg has hatched into a Regular Two-tone Chao named {chao_name}!", color=discord.Color.blue()).set_image(url="attachment://neutral_normal_child.png"))

    @commands.command(name='market')
    @ensure_user_initialized
    async def market(self, ctx):
        embed = discord.Embed(title="**Black Market**", description="**Here's what you can buy:**", color=self.chao_cog.embed_color)
        custom_emoji = f'<:custom_emoji:{self.chao_cog.CUSTOM_EMOJI_ID}>'
        for i in range(len(self.chao_cog.fruits)):
            embed.add_field(name=f'**{self.chao_cog.fruits[i]["emoji"]} {self.chao_cog.fruits[i]["name"]}**', value=f'**{custom_emoji} x {self.chao_cog.fruit_prices}**', inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='give_rings')
    @ensure_user_initialized
    async def give_rings(self, ctx):
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.chao_cog.load_inventory(file_path)
        rings = inventory_df.iloc[-1]['rings'] + 1000
        self.chao_cog.save_inventory(file_path, inventory_df, {'rings': rings, **{fruit['name']: int(inventory_df.iloc[-1].get(fruit['name'], 0)) for fruit in self.chao_cog.fruits}})
        await self.chao_cog.send_embed(ctx, f"{ctx.author.mention} has been given 1000 rings! Your current rings: {rings}")

    @commands.command(name='buy')
    @ensure_user_initialized
    async def buy(self, ctx, *, item_quantity: str):
        try: *item_name_parts, quantity = item_quantity.rsplit(' ', 1); item_name, quantity = ' '.join(item_name_parts), int(quantity)
        except ValueError: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, please specify the item and quantity correctly. For example: `$buy garden fruit 10`")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df = self.chao_cog.load_inventory(file_path)
        rings, fruit = inventory_df.iloc[-1]['rings'], next((fruit_item for fruit_item in self.chao_cog.fruits if fruit_item['name'].lower() == item_name.lower()), None)
        if not fruit: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, the item '{item_name}' is not available in the market.")
        total_cost = self.chao_cog.fruit_prices * quantity
        if rings < total_cost: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you do not have enough rings to buy {quantity} '{fruit['name']}'. You need {total_cost} rings.")
        current_inventory = {'rings': rings - total_cost, **{fruit_item['name']: int(inventory_df.iloc[-1].get(fruit_item['name'], 0)) + (quantity if fruit_item == fruit else 0) for fruit_item in self.chao_cog.fruits}, 'Chao Egg': int(inventory_df.iloc[-1].get('Chao Egg', 0))}
        self.chao_cog.save_inventory(file_path, inventory_df, current_inventory)
        await self.chao_cog.send_embed(ctx, f"{ctx.author.mention} has purchased {quantity} '{fruit['name']}(s)' for {total_cost} rings! You now have {current_inventory['rings']} rings.")

    @commands.command(name='inventory')
    @ensure_user_initialized
    async def inventory(self, ctx):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inventory_df = self.chao_cog.load_inventory(self.chao_cog.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0)
        embed = discord.Embed(title="Your Inventory", description="Here's what you have:", color=self.chao_cog.embed_color).add_field(name='Rings', value=f'{int(inventory_df.iloc[-1]["rings"])}', inline=False).add_field(name='Last Updated', value=f'{inventory_df.iloc[-1]["date"]}', inline=False)
        [embed.add_field(name=f'{fruit["emoji"]} {fruit["name"]}', value=f'Quantity: {int(inventory_df.iloc[-1].get(fruit["name"], 0))}', inline=True) for fruit in self.chao_cog.fruits if fruit["name"] in inventory_df.columns and int(inventory_df.iloc[-1].get(fruit["name"], 0)) > 0]
        chao_egg_quantity = int(inventory_df.iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity > 0: embed.add_field(name='<:ChaoEgg:1176372485986455562> Chao Egg', value=f'Quantity: {chao_egg_quantity}', inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='restore')
    @ensure_user_initialized
    async def restore(self, ctx, *, args: str):
        parts = args.split()
        if len(parts) != 2 or parts[0].lower() != 'inventory':
            return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, please use the command in the format: $restore inventory YYYY-MM-DD")
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        try: restore_date = datetime.strptime(parts[1], "%Y-%m-%d").date()
        except ValueError: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, please provide the date in YYYY-MM-DD format.")
        inventory_df = self.chao_cog.load_inventory(file_path)
        if parts[1] not in inventory_df['date'].values:
            return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, no inventory data found for {parts[1]}.")
        restored_inventory, current_date_str = inventory_df[inventory_df['date'] == parts[1]].iloc[0].to_dict(), self.chao_cog.current_date.strftime("%Y-%m-%d")
        restored_inventory['date'] = current_date_str
        pd.concat([inventory_df[inventory_df['date'] != current_date_str], pd.DataFrame([restored_inventory])], ignore_index=True).to_parquet(file_path, index=False)
        await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, your inventory has been restored to the state from {parts[1]}.")

    @commands.command(name='give_egg')
    @ensure_user_initialized
    async def give_egg(self, ctx):
        guild_id, user_id, file_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'user_data', 'inventory.parquet')
        inventory_df, chao_egg_quantity = self.chao_cog.load_inventory(file_path), int(self.chao_cog.load_inventory(file_path).iloc[-1].get('Chao Egg', 0))
        if chao_egg_quantity >= 1: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you already have a Chao Egg! Hatch it first before receiving another one.")
        self.chao_cog.save_inventory(file_path, inventory_df, {'Chao Egg': chao_egg_quantity + 1, 'rings': int(inventory_df.iloc[-1]['rings']), **{fruit['name']: int(inventory_df.iloc[-1].get(fruit['name'], 0)) for fruit in self.chao_cog.fruits}})
        await self.chao_cog.send_embed(ctx, f"{ctx.author.mention} has received a Chao Egg! You now have {chao_egg_quantity + 1} Chao Egg(s).")

    @commands.command(name='stats')
    @ensure_user_initialized
    async def stats(self, ctx, *, chao_name: str):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        chao_dir, chao_stats_path = self.chao_cog.get_path(guild_id, user_id, 'chao_data', chao_name), os.path.join(self.chao_cog.get_path(guild_id, user_id, 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path): return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")
        chao_df = pd.read_parquet(chao_stats_path).fillna(0)
        chao_to_view, chao_type = chao_df.iloc[0].to_dict(), self.chao_cog.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)

        # Correct type display if it's "Stamina"
        chao_type_display = "Normal" if chao_type == "Stamina" else chao_type

        chao_df.to_parquet(chao_stats_path, index=False)
        embed = discord.Embed(color=discord.Color.blue()).set_author(name=f"{chao_name}'s Stats", icon_url="attachment://Stats.png")
        alignment_label = "Hero" if chao_to_view.get('alignment', 0) >= 5 else "Dark" if chao_to_view.get('alignment', 0) <= -5 else "Neutral"
        self.chao_cog.paste_image(self.chao_cog.TEMPLATE_PATH, self.chao_cog.OVERLAY_PATH, os.path.join(chao_dir, f'{chao_name}_stats.png'), self.chao_cog.TICK_POSITIONS, chao_to_view["power_ticks"], chao_to_view["swim_ticks"], chao_to_view["stamina_ticks"], chao_to_view["fly_ticks"], chao_to_view["run_ticks"], chao_to_view["mind_ticks"], chao_to_view["power_level"], chao_to_view["swim_level"], chao_to_view["stamina_level"], chao_to_view["fly_level"], chao_to_view["run_level"], chao_to_view["mind_level"], chao_to_view.get("swim_exp", 0), chao_to_view.get("fly_exp", 0), chao_to_view.get("run_exp", 0), chao_to_view.get("power_exp", 0), chao_to_view.get("mind_exp", 0), chao_to_view.get("stamina_exp", 0))
        embed.add_field(name="Type", value=chao_type_display, inline=True).add_field(name="Alignment", value=alignment_label, inline=True).set_thumbnail(url="attachment://chao_thumbnail.png").set_image(url=f"attachment://output_image.png").set_footer(text="Page 1 / ?")
        await ctx.send(files=[discord.File(os.path.join(chao_dir, f'{chao_name}_stats.png'), "output_image.png"), discord.File(self.chao_cog.ICON_PATH), discord.File(os.path.join(chao_dir, f'{chao_name}_thumbnail.png'), "chao_thumbnail.png")], embed=embed)

    @commands.command(name='feed')
    @ensure_user_initialized
    async def feed(self, ctx, chao_name: str, *, fruit_name: str):
        guild_id, user_id, chao_dir_path, chao_stats_path = str(ctx.guild.id), str(ctx.author.id), self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'chao_data', chao_name), os.path.join(self.chao_cog.get_path(str(ctx.guild.id), str(ctx.author.id), 'chao_data', chao_name), f'{chao_name}_stats.parquet')
        if not os.path.exists(chao_stats_path): return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you do not have a Chao named {chao_name}.")
        chao_df, inventory_df, fruit = pd.read_parquet(chao_stats_path).fillna(0), self.chao_cog.load_inventory(self.chao_cog.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')).fillna(0), next((fruit_item for fruit_item in self.chao_cog.fruits if fruit_item['name'].lower() == fruit_name.lower()), None)
        if not fruit or fruit['name'] not in inventory_df.columns or int(inventory_df.iloc[-1].get(fruit['name'], 0)) <= 0: return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, you do not have any {fruit_name} to feed your Chao.")
        
        alignment = chao_df.at[0, 'alignment']
        evolved = chao_df.at[0, 'evolved']
        
        if evolved and alignment >= 5 and fruit['name'].lower() == 'dark fruit':
            return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, evolved Hero Chao cannot eat Dark Fruit.")
        if evolved and alignment <= -5 and fruit['name'].lower() == 'hero fruit':
            return await self.chao_cog.send_embed(ctx, f"{ctx.author.mention}, evolved Dark Chao cannot eat Hero Fruit.")

        inventory_df.at[inventory_df.index[-1], fruit['name']] -= 1
        stat_key = f"{FRUIT_STATS[fruit['name']]}_ticks"
        chao_df.at[0, stat_key] = chao_df.get(stat_key, pd.Series([0])).iloc[0] + random.randint(FRUIT_TICKS_MIN, FRUIT_TICKS_MAX)
        if not chao_df.at[0, 'evolved']:
            chao_df.at[0, 'alignment'] = min(5, chao_df.at[0, 'alignment'] + 1) if fruit_name.lower() == 'hero fruit' else max(-5, chao_df.at[0, 'alignment'] - 1) if fruit_name.lower() == 'dark fruit' else chao_df.at[0, 'alignment']
        if chao_df.at[0, stat_key] >= 10: chao_df.at[0, stat_key] %= 10; stat_level, stat_exp, stat_grade = f"{stat_key.rsplit('_', 1)[0]}_level", f"{stat_key.rsplit('_', 1)[0]}_exp", f"{stat_key.rsplit('_', 1)[0]}_grade"; chao_df.at[0, stat_level] += 1; chao_df.at[0, stat_exp] += self.chao_cog.calculate_exp_gain(chao_df.at[0, stat_grade]); chao_type = self.chao_cog.update_chao_type_and_thumbnail(guild_id, user_id, chao_name, chao_df)
        else: stat_level, chao_type = f"{stat_key.rsplit('_', 1)[0]}_level", chao_df.iloc[0]['Type']
        alignment_label = "Hero" if chao_df.at[0, 'alignment'] == 5 else "Dark" if chao_df.at[0, 'alignment'] == -5 else "Neutral"

        # Update the thumbnail if the alignment is Dark or Hero
        if alignment_label == "Dark":
            alignment_thumbnail = "../assets/chao/dark_normal_child.png"
        elif alignment_label == "Hero":
            alignment_thumbnail = "../assets/chao/hero_normal_child.png"
        else:
            alignment_thumbnail = None

        if alignment_thumbnail:
            output_thumbnail = os.path.join(chao_dir_path, f"{chao_name}_thumbnail.png")
            self.chao_cog.combine_images(self.chao_cog.BACKGROUND_PATH, alignment_thumbnail, output_thumbnail)

        self.chao_cog.save_inventory(self.chao_cog.get_path(guild_id, user_id, 'user_data', 'inventory.parquet'), inventory_df, inventory_df.iloc[-1].to_dict())
        chao_df.to_parquet(chao_stats_path, index=False)
        chao_type_display = "Normal" if chao_type == "Stamina" else chao_type
        await self.chao_cog.send_embed(ctx, f"{chao_name} ate {fruit_name}!\n{chao_name}'s {stat_key.split('_')[0].capitalize()} stat has increased!\nTicks: {chao_df.at[0, stat_key]}/10\nLevel: {chao_df.at[0, stat_level]} (Type: {chao_type_display})\nAlignment: {alignment_label}")

async def setup(bot): await bot.add_cog(Commands(bot))
