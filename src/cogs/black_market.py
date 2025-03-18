import os
import json
import discord
from discord.ext import commands
from discord.ui import View, Button
from views.market_view import MarketView  # Import MarketView from the views directory
from config import DEFAULT_PRICES  # Import the default prices from config.py

class BlackMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.yellow()
        self.image_utils = self.data_utils = None
        self.market_message_id = None

        self.prices_file = "fruit_prices.json"
        # Use the default prices imported from config.py
        self.default_prices = DEFAULT_PRICES

        self.fruit_prices = self.load_fruit_prices()

    def load_fruit_prices(self):
        if os.path.exists(self.prices_file):
            with open(self.prices_file, "r") as f:
                return json.load(f)
        return self.default_prices.copy()

    def save_fruit_prices(self):
        with open(self.prices_file, "w") as f:
            json.dump(self.fruit_prices, f)

    async def cog_load(self):
        self.image_utils = self.bot.get_cog('ImageUtils')
        self.data_utils = self.bot.get_cog('DataUtils')
        if not self.image_utils or not self.data_utils:
            raise Exception("ImageUtils or DataUtils cog not loaded.")

        self.assets_dir = self.image_utils.assets_dir
        self.BLACK_MARKET_THUMBNAIL_PATH = os.path.join(
            self.assets_dir, 'graphics/thumbnails/black_market.png')
        self.BLACK_MARKET_FRUITS_PAGE_1_PATH = os.path.join(
            self.assets_dir, 'graphics/cards/black_market_fruits_page_1.png')
        self.BLACK_MARKET_FRUITS_PAGE_2_PATH = os.path.join(
            self.assets_dir, 'graphics/cards/black_market_fruits_page_2.png')
        self.BLACK_MARKET_ICON_PATH = os.path.join(
            self.assets_dir, 'graphics/icons/Black_Market.png')

        # If you want to automatically reload the view for an existing message ID...
        if os.path.exists("market_message_id.txt"):
            with open("market_message_id.txt", "r") as f:
                market_message_id_str = f.read().strip()
            if market_message_id_str.isdigit():
                self.market_message_id = int(market_message_id_str)

                embed = discord.Embed(color=self.embed_color)
                embed.set_author(name="Black Market", icon_url="attachment://Black_Market.png")
                embed.description = "Buy somethin' will ya?"
                embed.add_field(name="Shop Type", value="Fruits", inline=True)
                embed.set_thumbnail(url="attachment://black_market.png")
                embed.set_image(url="attachment://black_market_fruits_page_1.png")
                embed.set_footer(text="Page 1 / 3")

                view = MarketView(
                    embed=embed,
                    icon_path=self.BLACK_MARKET_ICON_PATH,
                    thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                    page_1_path=self.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                    page_2_path=self.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                    black_market_cog=self,
                    total_pages=3
                )
                self.bot.add_view(view, message_id=self.market_message_id)

    def send_embed(self, interaction: discord.Interaction, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return interaction.response.send_message(embed=embed)

    async def market(self, interaction: discord.Interaction, *, market_type: str = None):
        try:
            page_1_output_path = "black_market_fruits_page_1_temp.png"
            page_2_output_path = "black_market_fruits_page_2_temp.png"

            self.image_utils.paste_black_market_prices_page1(
                self.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                page_1_output_path,
                self.fruit_prices
            )
            self.image_utils.paste_black_market_prices_page2(
                self.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                page_2_output_path,
                self.fruit_prices
            )

            icon_file = discord.File(self.BLACK_MARKET_ICON_PATH, filename="Black_Market.png")
            thumb_file = discord.File(self.BLACK_MARKET_THUMBNAIL_PATH, filename="black_market.png")
            page_1_file = discord.File(page_1_output_path, filename="black_market_fruits_page_1.png")

            embed = discord.Embed(color=self.embed_color)
            embed.set_author(name="Black Market", icon_url="attachment://Black_Market.png")
            embed.description = "Buy somethin' will ya?"
            embed.add_field(name="Shop Type", value="Fruits", inline=True)
            embed.set_thumbnail(url="attachment://black_market.png")
            embed.set_image(url="attachment://black_market_fruits_page_1.png")
            embed.set_footer(text="Page 1 / 3")

            view = MarketView(
                embed=embed,
                icon_path=self.BLACK_MARKET_ICON_PATH,
                thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                page_1_path=page_1_output_path,
                page_2_path=page_2_output_path,
                black_market_cog=self,
                total_pages=3
            )

            await interaction.response.send_message(
                files=[icon_file, thumb_file, page_1_file],
                embed=embed,
                view=view
            )
            msg = await interaction.original_response()

            with open("market_message_id.txt", "w") as f:
                f.write(str(msg.id))

            self.market_message_id = msg.id
            self.bot.add_view(view, message_id=msg.id)

        except Exception as e:
            print(f"[market] Failed to send market message: {e}")
            await interaction.response.send_message("An error occurred while opening the market.", ephemeral=True)

    async def buy(self, interaction: discord.Interaction, item: str, amount: int):
        item_name = item.strip()
        quantity = amount

        item_name_normalized = item_name.lower()
        fruit_prices_normalized = {key.lower(): key for key in self.fruit_prices}

        if item_name_normalized not in fruit_prices_normalized:
            available_items = ', '.join(self.fruit_prices.keys())
            return await self.send_embed(
                interaction,
                f"{interaction.user.mention}, '{item_name}' is not sold here. Available items: {available_items}."
            )

        actual_item_name = fruit_prices_normalized[item_name_normalized]

        guild_id, guild_name, user = str(interaction.guild.id), interaction.guild.name, interaction.user
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        rings = current_inv.get('rings', 0)

        price = self.fruit_prices[actual_item_name] * quantity
        if rings < price:
            return await self.send_embed(
                interaction,
                f"{interaction.user.mention}, not enough rings. You need {price} rings, but you only have {rings}."
            )

        current_inv['rings'] = rings - price
        current_inv[actual_item_name] = current_inv.get(actual_item_name, 0) + quantity
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)

        description = (
            f"{interaction.user.mention} bought {quantity}x {actual_item_name} for {price} rings!\n"
            f"You now have {current_inv['rings']} rings."
        )
        embed = discord.Embed(title="Chao Bot", description=description, color=self.embed_color)
        embed.set_thumbnail(url="attachment://black_market.png")
        thumb_file = discord.File(self.BLACK_MARKET_THUMBNAIL_PATH, filename="black_market.png")
        await interaction.response.send_message(embed=embed, file=thumb_file)

    async def buy_item_autocomplete(self, interaction: discord.Interaction, current: str):
        from discord import app_commands
        current = current or ""
        return [
            app_commands.Choice(name=fruit, value=fruit)
            for fruit in self.fruit_prices.keys() if current.lower() in fruit.lower()
        ]

    async def cog_unload(self):
        temp_files = ["black_market_fruits_page_1_temp.png", "black_market_fruits_page_2_temp.png"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
