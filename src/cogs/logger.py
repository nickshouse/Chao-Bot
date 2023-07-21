import logging
from discord.ext import commands

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.WARNING)
        handler = logging.FileHandler(filename='./log.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)

    @commands.Cog.listener()
    async def on_message(self, message):
        self.logger.info(f"Message from {message.author}: {message.content}")

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('Bot is ready.')

async def setup(bot):
    await bot.add_cog(Logger(bot))
    print("Logger cog loaded")
