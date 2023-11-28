import discord
from discord.ext import commands
import logging
from datetime import datetime

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)  # Creating a logger for this cog
        self.setup_logger()

    def setup_logger(self):
        # Set up the logging format and level
        formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')
        file_handler = logging.FileHandler('log.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Log every command invocation
        self.logger.info(f"Command used: {ctx.command} by {ctx.author} in {ctx.guild}")

    # Additional listeners for other events can be added here

async def setup(bot):
    await bot.add_cog(Logger(bot))
    print("Logger cog loaded")
