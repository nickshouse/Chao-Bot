import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize bot with all intents
bot = commands.Bot(command_prefix='$', help_command=None, intents=discord.Intents.all())

# Global variable to store the restricted channel ID
restricted_channel_id = None

@bot.event
async def on_ready():
    """
    Event triggered when the bot is ready and connected to Discord.
    """
    for cog in ['cogs.image_utils', 'cogs.data_utils', 'cogs.chao', 'cogs.black_market', 'cogs.commands']:
        try:
            await bot.load_extension(cog)
            print(f'Loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')
    print(f'Connected as {bot.user.name}')


@bot.command(name="restrict")
@commands.has_permissions(administrator=True)  # Admin-only command
async def restrict(ctx, channel_id: int = None):
    """
    Restrict the bot to post messages only in a specific channel.
    If no channel ID is provided, it removes the restriction.
    """
    global restricted_channel_id

    if channel_id:
        # Validate the channel exists in the guild
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            await ctx.reply(f"Channel ID {channel_id} is not valid in this server.")
            return

        # Set the restricted channel ID
        restricted_channel_id = channel_id
        await ctx.reply(f"The bot is now restricted to post messages only in <#{channel_id}>.")
    else:
        # Remove the restriction
        restricted_channel_id = None
        await ctx.reply("The bot can now post messages in all channels.")


@bot.event
async def on_message(message):
    """
    Event triggered for every message the bot can see.
    Adds 10 rings to a user's inventory on each message and respects channel restrictions for bot replies.
    """
    global restricted_channel_id

    # Ignore bot messages and messages outside of guilds
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    guild_name = message.guild.name
    user = message.author

    # Access the DataUtils cog
    data_utils = bot.get_cog('DataUtils')
    if not data_utils:
        print("DataUtils cog is not loaded.")
        return

    # Add 10 rings to the user's inventory
    if data_utils.is_user_initialized(guild_id, guild_name, user):
        try:
            # Get the inventory file path
            inventory_path = data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')

            # Load the inventory
            inventory_df = data_utils.load_inventory(inventory_path)
            if inventory_df.empty:
                print(f"Inventory is empty for user {user.name}. Initializing...")
                current_inventory = {'rings': 0}  # Initialize with 0 rings if no inventory exists
            else:
                # Get the latest inventory
                current_inventory = inventory_df.iloc[-1].to_dict()

            # Add 10 rings
            current_inventory['rings'] = current_inventory.get('rings', 0) + 10

            # Save the updated inventory
            data_utils.save_inventory(inventory_path, inventory_df, current_inventory)

        except Exception as e:
            print(f"Error adding rings for {user.name}: {str(e)}")

    # If the bot is restricted, ignore messages outside the restricted channel for its replies
    if restricted_channel_id and message.channel.id != restricted_channel_id:
        return

    # Ensure other commands still work
    await bot.process_commands(message)


# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
