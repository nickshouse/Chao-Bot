import os
import json
import re
import difflib
import time
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from views.stats_view import StatsView  # Import persistent stats view loader
from views.market_view import MarketView  # Import persistent market view loader

# Global dictionary to store a sliding window of recent messages per user.
# Key: (guild_id, user.id) -> List of normalized messages (up to 5 recent ones)
recent_user_messages = {}

# Load environment variables
load_dotenv()

# Initialize bot with all intents
bot = commands.Bot(command_prefix='/', help_command=None, intents=discord.Intents.all())

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
    # Load cogs
    for cog in [
        'cogs.image_utils',
        'cogs.data_utils',
        'cogs.chao_helper',
        'cogs.chao_decay',
        'cogs.chao',
        'cogs.black_market',
        'cogs.chao_lifecycle',
        'cogs.chao_admin',
        'cogs.commands'
    ]:
        try:
            await bot.load_extension(cog)
            print(f'Loaded {cog}')
        except Exception as e:
            print(f'Failed to load {cog}: {e}')

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

    # Load persistent StatsView instances so interactions remain active across restarts.
    StatsView.load_all_persistent_views(bot)
    print("Persistent stats views loaded.")

    # Load persistent MarketView instances so interactions remain active across restarts.
    MarketView.load_all_persistent_views(bot)
    print("Persistent market views loaded.")

    print(f'Connected as {bot.user.name}')


@bot.tree.command(name="restrict", description="Restrict the bot to a specific channel or remove restriction.")
@app_commands.describe(channel_id="Channel ID to restrict to. Omit to remove restriction.")
@app_commands.checks.has_permissions(administrator=True)
async def restrict_cmd(interaction: discord.Interaction, channel_id: int = None):
    """
    Restrict the bot to post messages only in a specific channel.
    If no channel ID is provided, it removes the restriction.
    """
    # We need a guild to exist
    if not interaction.guild:
        await interaction.response.send_message("This command can only be used in a server (guild).", ephemeral=True)
        return

    guild_id = str(interaction.guild.id)

    # If the user provided a channel ID, set or validate it
    if channel_id:
        # Validate the channel exists in the guild
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            await interaction.response.send_message(
                f"Channel ID {channel_id} is not valid in this server.",
                ephemeral=True
            )
            return

        # Set the restricted channel ID
        restricted_channels[guild_id] = channel_id
        save_restricted_channels()
        await interaction.response.send_message(
            f"The bot is now restricted to post messages only in <#{channel_id}>."
        )
    else:
        # Remove the restriction
        restricted_channels.pop(guild_id, None)
        save_restricted_channels()
        await interaction.response.send_message(
            "The bot can now post messages in all channels."
        )


@bot.event
async def on_message(message: discord.Message):
    """
    Event triggered for every message the bot can see.
    Ensures that messages are processed only if they are in the restricted channel, if set.
    Also handles awarding rings for non-spam messages.
    """
    # Ignore bot messages and messages outside of guilds
    if message.author.bot or not message.guild:
        return

    guild_id = str(message.guild.id)
    channel_id = restricted_channels.get(guild_id)

    # If a restriction is set and the message is not in the allowed channel, still add rings, but skip processing commands
    if channel_id and message.channel.id != channel_id:
        add_rings_for_user(message)
        return

    add_rings_for_user(message)

    # Process normal prefix-based commands if needed (not slash commands)
    await bot.process_commands(message)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    """
    Event triggered for every interaction (including slash commands and context menus).
    We'll award rings for slash commands to ensure the user can gain rings from using them.
    """
    # Only handle slash or context commands invoked by real users in a guild
    if (interaction.type == discord.InteractionType.application_command
        and not interaction.user.bot
        and interaction.guild):
        
        # If there's a restricted channel for this guild, we could optionally check 
        # if the user is using slash commands in that channel, etc.
        # We'll still award rings no matter what channel, but you can decide otherwise.
        add_rings_for_slash_command(interaction)

    # NOTICE: We do NOT call bot.process_application_commands(interaction) here
    # because that method doesn't exist in recent discord.py versions.
    # The library automatically handles slash command invocations.


def add_rings_for_slash_command(interaction: discord.Interaction):
    """
    Award rings for a slash (or context) command usage.
    We'll give them 5 rings for each slash command invoked, no spam check needed.
    """
    data_utils = bot.get_cog('DataUtils')
    if not data_utils:
        print("DataUtils cog is not loaded.")
        return

    guild = interaction.guild
    user = interaction.user
    guild_id = str(guild.id)
    guild_name = guild.name

    # Check if the user is initialized
    if not data_utils.is_user_initialized(guild_id, guild_name, user):
        print(f"User {user.name} is not initialized in the Chao system.")
        return

    try:
        inventory_path = data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inventory_df = data_utils.load_inventory(inventory_path)
        if inventory_df.empty:
            current_inventory = {'rings': 0}
        else:
            current_inventory = inventory_df.iloc[-1].to_dict()

        current_inventory['rings'] = current_inventory.get('rings', 0) + 5
        data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        print(f"Awarded 5 rings to {user.name} for slash command usage. (Guild={guild_id})")
    except Exception as e:
        print(f"Error adding slash command rings for {user.name}: {str(e)}")


def save_restricted_channels():
    """
    Save the restricted channels data to a file.
    """
    with open(RESTRICT_FILE, "w") as f:
        json.dump(restricted_channels, f, indent=4)


def add_rings_for_user(message: discord.Message):
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

    # Ignore messages that are less than 3 characters after normalization
    if len(normalized_message) < 3:
        print(f"Ignoring message from {user.name} because it is too short.")
        return

    user_key = (guild_id, user.id)
    recent_msgs = recent_user_messages.get(user_key, [])

    spam_count = 0
    comparisons = []
    for old_msg in recent_msgs:
        similarity = difflib.SequenceMatcher(None, normalized_message, old_msg).ratio()
        comparisons.append((old_msg, similarity))
        if similarity > 0.9:
            spam_count += 1

    # If at least 2 similar messages are found, treat this as spam
    if spam_count >= 2:
        for old_msg, similarity in comparisons:
            if similarity > 0.9:
                print(f"Detected spam: New message '{normalized_message}' is {similarity*100:.1f}% similar to '{old_msg}'")
        print(f"Detected spam pattern from {user.name} (similar count: {spam_count}). No rings awarded.")
        recent_msgs.append(normalized_message)
        recent_user_messages[user_key] = recent_msgs[-5:]
        return

    # Update the sliding window with the new normalized message
    recent_msgs.append(normalized_message)
    recent_user_messages[user_key] = recent_msgs[-5:]

    try:
        # Get the inventory file path
        inventory_path = data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')

        # Load the inventory
        inventory_df = data_utils.load_inventory(inventory_path)
        if inventory_df.empty:
            print(f"Inventory is empty for user {user.name}. Initializing with 0 rings.")
            current_inventory = {'rings': 0}
        else:
            current_inventory = inventory_df.iloc[-1].to_dict()

        # Award 5 rings for this valid (non-spam) message
        current_inventory['rings'] = current_inventory.get('rings', 0) + 5

        # Save the updated inventory
        data_utils.save_inventory(inventory_path, inventory_df, current_inventory)
        print(f"Awarded 5 rings to {user.name} (Guild={guild_id}).")
    except Exception as e:
        print(f"Error adding rings for {user.name}: {str(e)}")


# Run the bot
bot.run(os.getenv('DISCORD_TOKEN'))
