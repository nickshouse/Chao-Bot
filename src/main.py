import os
import json
import re
import difflib
import time
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Global dictionary to store a sliding window of recent messages per user.
# Key: (guild_id, user.id) -> List of normalized messages (up to 5 recent ones)
recent_user_messages = {}

# Load environment variables
load_dotenv()

# Initialize bot with all intents
bot = commands.Bot(command_prefix='$', help_command=None, intents=discord.Intents.all())

# Path to store the restrict settings
RESTRICT_FILE = "restricted_channels.json"

# Load the restricted channels data
if os.path.exists(RESTRICT_FILE):
    with open(RESTRICT_FILE, "r") as f:
        restricted_channels = json.load(f)
else:
    restricted_channels = {}

@bot.event
async def on_ready():
    """
    Event triggered when the bot is ready and connected to Discord.
    """
    for cog in ['cogs.image_utils', 'cogs.data_utils', 'cogs.chao_helper', 
                'cogs.chao_decay', 'cogs.chao', 'cogs.black_market', 'cogs.commands']:
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
    guild_id = str(ctx.guild.id)

    if channel_id:
        # Validate the channel exists in the guild
        channel = ctx.guild.get_channel(channel_id)
        if not channel:
            await ctx.reply(f"Channel ID {channel_id} is not valid in this server.")
            return

        # Set the restricted channel ID
        restricted_channels[guild_id] = channel_id
        save_restricted_channels()
        await ctx.reply(f"The bot is now restricted to post messages only in <#{channel_id}>.")
    else:
        # Remove the restriction
        restricted_channels.pop(guild_id, None)
        save_restricted_channels()
        await ctx.reply("The bot can now post messages in all channels.")

@bot.event
async def on_message(message):
    """
    Event triggered for every message the bot can see.
    Ensures that messages are processed only if they are in the restricted channel, if set.
    """
    # Ignore bot messages and messages outside of guilds
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    channel_id = restricted_channels.get(guild_id)

    # If a restriction is set and the message is not in the allowed channel, process commands only
    if channel_id and message.channel.id != channel_id:
        add_rings_for_user(message)
        return

    add_rings_for_user(message)
    await bot.process_commands(message)

def save_restricted_channels():
    """
    Save the restricted channels data to a file.
    """
    with open(RESTRICT_FILE, "w") as f:
        json.dump(restricted_channels, f, indent=4)


# Waits for 3 messages to be sent, then checks the last 5 messages for similarity
def add_rings_for_user(message):
    """
    Award 5 rings for each non-spam message a user sends.
    
    This function uses a sliding window (last 5 messages) to detect repeated content.
    It normalizes each message (lowercase and removes non-alphanumeric characters) and,
    if the new message is over 90% similar to at least two previous messages, no rings are awarded.
    
    Additionally, messages that are less than 3 characters long are ignored.
    """
    guild_id = str(message.guild.id)
    guild_name = message.guild.name
    user = message.author

    # Access the DataUtils cog
    data_utils = bot.get_cog('DataUtils')
    if not data_utils:
        print("DataUtils cog is not loaded.")
        return

    # Check if the user is initialized in the Chao system
    if not data_utils.is_user_initialized(guild_id, guild_name, user):
        print(f"User {user.name} is not initialized in the Chao system.")
        return

    # Normalize the message: lowercase and remove non-alphanumeric characters
    normalized_message = re.sub(r'\W+', '', message.content.lower())

    # Ignore messages that are less than 3 characters after normalization.
    if len(normalized_message) < 3:
        print(f"Ignoring message from {user.name} because it is too short.")
        return

    user_key = (guild_id, user.id)
    recent_msgs = recent_user_messages.get(user_key, [])

    spam_count = 0
    comparisons = []  # List to hold tuples of (old_message, similarity_ratio)
    for old_msg in recent_msgs:
        similarity = difflib.SequenceMatcher(None, normalized_message, old_msg).ratio()
        comparisons.append((old_msg, similarity))
        if similarity > 0.9:
            spam_count += 1

    # If at least 2 similar messages are found, treat this as spam.
    if spam_count >= 2:
        for old_msg, similarity in comparisons:
            if similarity > 0.9:
                print(f"Detected spam: New message '{normalized_message}' is {similarity*100:.1f}% similar to '{old_msg}'")
        print(f"Detected spam pattern from {user.name} (similar count: {spam_count}). No rings awarded.")
        recent_msgs.append(normalized_message)
        recent_user_messages[user_key] = recent_msgs[-5:]
        return

    # Update the sliding window with the new normalized message.
    recent_msgs.append(normalized_message)
    recent_user_messages[user_key] = recent_msgs[-5:]

    try:
        # Get the inventory file path.
        inventory_path = data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')

        # Load the inventory.
        inventory_df = data_utils.load_inventory(inventory_path)
        if inventory_df.empty:
            print(f"Inventory is empty for user {user.name}. Initializing with 0 rings.")
            current_inventory = {'rings': 0}
        else:
            current_inventory = inventory_df.iloc[-1].to_dict()

        # Award 5 rings for this valid (non-spam) message.
        current_inventory['rings'] = current_inventory.get('rings', 0) + 5

        # Save the updated inventory.
        data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        print(f"Awarded 5 rings to {user.name} (Guild={guild_id}).")
    except Exception as e:
        print(f"Error adding rings for {user.name}: {str(e)}")


# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
