import random
from discord.ext import commands
import os
import shutil

class FortuneTeller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_chao_name(self):
        """Generate a random name for a Chao"""
        # List of potential Chao names
        chao_names = ["Chaoko", "Chaolin", "Chow", "Chaoblin", "Count Chaocula", "Chaozil", "Chaos", "Chaoz"]
        return random.choice(chao_names)
    
    @commands.command()
    async def name(self, ctx, old_name, new_name):
        """Rename a user's Chao"""
        # Get all the user's Chao
        chao_list = await self.bot.cogs['Database'].get_chao(ctx.guild.id, ctx.author.id)

        # Check if new_name is already taken
        if any(chao['name'] == new_name for chao in chao_list):
            await ctx.send(f"The name {new_name} is already taken.")
            return

        # Find the Chao with the specified old name
        for chao in chao_list:
            if chao['name'] == old_name:
                chao['name'] = new_name  # Change the name

                # Rename the file
                old_filename = f"../database/{ctx.guild.id}/{ctx.author.id}/chao_data/{old_name}.parquet"
                new_filename = f"../database/{ctx.guild.id}/{ctx.author.id}/chao_data/{new_name}.parquet"

                # Use the lock for the old filename to perform the rename operation
                async with self.bot.cogs['Database'].locks[old_filename]:
                    if os.path.exists(old_filename):
                        shutil.move(old_filename, new_filename)

                await self.bot.cogs['Database'].store_chao(ctx.guild.id, ctx.author.id, chao)  # Store the updated Chao
                await ctx.send(f"{old_name} has been renamed to {new_name}!")
                break
        else:
            await ctx.send(f"You don't have a Chao named {old_name}.")



async def setup(bot):
    await bot.add_cog(FortuneTeller(bot))
    print("Fortune Teller cog loaded")
