import discord
from discord.ext import commands
import logging
from datetime import datetime

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.setup_logger()

    def setup_logger(self):
        self.log_file = 'log.md'
        # Open log file and write the initial date header if file is empty
        with open(self.log_file, 'a+') as file:
            file.seek(0)
            if not file.read(1):  # Check if file is empty
                file.write(f"# {datetime.now().strftime('%B %d, %Y')}\n\n")

    def log(self, message_type, ctx, description):
        # Manually format the log entry
        log_entry = (
            f"<div style=\"background-color: #000000; color: {'red' if message_type == 'ERROR' else 'white'}; "
            f"border: 4px solid #ccc; padding: 16px; font-family: 'Roboto Mono Medium', monospace; display: inline-block;\">\n"
            f"    === {message_type} ===<br><br>\n"
            f"    Server: {ctx.guild} ({ctx.guild.id}) <br>\n"
            f"    User: {ctx.author} ({ctx.author.display_name}) ({ctx.author.id}) <br>\n"
            f"    Command: {ctx.message.content} <br>\n"
            f"    Description: {description} <br><br>\n"
            f"    {datetime.now().strftime('%I:%M:%S %p')}\n"
            f"</div><br><br>\n\n"
        )

        # Write the log entry to the file
        with open(self.log_file, 'a') as file:
            file.write(log_entry)

    @commands.Cog.listener()
    async def on_command(self, ctx):
        # Example of logging an INFO message
        self.log("INFO", ctx, "Example description of what happened.")

    # Add more listeners or methods for different types of logs

async def setup(bot):
    await bot.add_cog(Logger(bot))
    print("Logger cog loaded")
