import random
from discord.ext import commands

class FortuneTeller(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_chao_name(self):
        """Generate a random name for a Chao"""
        # List of potential Chao names
        chao_names = ["Sparkle", "Bubbles", "Twilight", "Star", "Rainbow", "Sunny", "Moonbeam", "Glimmer", "Whisper", "Misty"]
        return random.choice(chao_names)

async def setup(bot):
    await bot.add_cog(FortuneTeller(bot))
    print("Fortune Teller cog loaded")
