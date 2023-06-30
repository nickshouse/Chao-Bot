import discord
from discord.ext import commands
from discord import Embed

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


async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
    print("Black Market cog loaded")
