# cogs/black_market.py

import os
import discord
from discord.ext import commands
from discord.ui import View, Button
import json


class MarketView(View):
    def __init__(self, embed: discord.Embed, icon_path: str, thumbnail_path: str,
                 page_1_path: str, page_2_path: str, black_market_cog, total_pages=3, state_file="market_state.json"):
        super().__init__(timeout=None)
        self.embed = embed
        self.icon_path = icon_path
        self.thumbnail_path = thumbnail_path
        self.page_1_path = page_1_path
        self.page_2_path = page_2_path
        self.black_market_cog = black_market_cog
        self.total_pages = total_pages
        self.state_file = state_file

        # Load or initialize state
        self.current_page = self.load_state()

        self.add_item(self.previous_button())
        self.add_item(self.next_button())

    def save_state(self):
        """Save the current page to a file."""
        state = {"current_page": self.current_page}
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        except Exception as e:
            print(f"[MarketView] Failed to save state: {e}")

    def load_state(self):
        """Load the current page from a file, ensuring it is within valid bounds."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                    page = state.get("current_page", 1)
                    if 1 <= page <= self.total_pages:
                        return page
            except Exception as e:
                print(f"[MarketView] Failed to load state: {e}")
        return 1

    def previous_button(self) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji="⬅️", custom_id="market_previous")
        button.callback = self.previous_page
        return button

    def next_button(self) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji="➡️", custom_id="market_next")
        button.callback = self.next_page
        return button

    async def previous_page(self, interaction: discord.Interaction):
        """Navigate to the previous page and update the state."""
        self.current_page = self.current_page - 1 if self.current_page > 1 else self.total_pages
        self.save_state()
        await self.update_market(interaction)

    async def next_page(self, interaction: discord.Interaction):
        """Navigate to the next page and update the state."""
        self.current_page = self.current_page + 1 if self.current_page < self.total_pages else 1
        self.save_state()
        await self.update_market(interaction)

    async def update_market(self, interaction: discord.Interaction):
        """
        Updates the market page display based on the current page.
        """
        fruit_prices = self.black_market_cog.load_fruit_prices()

        page_1_output_path = self.page_1_path
        page_2_output_path = self.page_2_path

        # Common attachments: the icon + thumbnail
        attachments = [
            discord.File(self.icon_path, filename="Black_Market.png"),
            discord.File(self.thumbnail_path, filename="black_market.png"),
        ]
        image_filename = None

        try:
            if self.current_page == 1:
                # Page 1 logic
                self.black_market_cog.image_utils.paste_black_market_prices_page1(
                    self.black_market_cog.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                    page_1_output_path,
                    fruit_prices
                )
                image_filename = "black_market_fruits_page_1.png"
                attachments.append(discord.File(page_1_output_path, filename=image_filename))

                self.embed.clear_fields()
                self.embed.description = "Buy somethin' will ya?"
                self.embed.add_field(name="Shop Type", value="Fruits", inline=True)
                self.embed.set_image(url=f"attachment://{image_filename}")
                self.embed.set_footer(text=f"Page {self.current_page} / {self.total_pages}")

            elif self.current_page == 2:
                # Page 2 logic
                self.black_market_cog.image_utils.paste_black_market_prices_page2(
                    self.black_market_cog.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                    page_2_output_path,
                    fruit_prices
                )
                image_filename = "black_market_fruits_page_2.png"
                attachments.append(discord.File(page_2_output_path, filename=image_filename))

                self.embed.clear_fields()
                self.embed.description = "These ones are a bit more expensive:"
                self.embed.add_field(name="Shop Type", value="Fruits", inline=True)
                self.embed.set_image(url=f"attachment://{image_filename}")
                self.embed.set_footer(text=f"Page {self.current_page} / {self.total_pages}")

            else:
                # Page 3 logic with synced prices
                self.embed.clear_fields()
                self.embed.set_image(url=None)

                # Dynamic prices for Page 3 items
                page_3_items = [
                    "Swim Fruit", "Fly Fruit", "Run Fruit",
                    "Power Fruit", "Garden Nut", "Strange Mushroom"
                ]
                cost_text = "\n".join(
                    f"- **{item}** ({fruit_prices[item]} rings)"
                    for item in page_3_items
                )

                self.embed.description = (
                    "Main items for unique Chao evolution:\n\n"
                    "**Shop Type**\nFruits\n\n"
                    f"{cost_text}\n"
                )
                self.embed.set_footer(text=f"Page {self.current_page} / {self.total_pages} | Graphics Pending...")

            await interaction.response.edit_message(
                embed=self.embed,
                view=self,
                attachments=attachments
            )

        except Exception as e:
            print(f"[MarketView] Error on page {self.current_page}: {e}")
            await interaction.response.send_message(
                "An error occurred while updating the market page.", ephemeral=True
            )


class BlackMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.yellow()
        self.image_utils = self.data_utils = None
        self.market_message_id = None

        self.prices_file = "fruit_prices.json"
        self.default_prices = {
            "Round Fruit": 25, "Triangle Fruit": 25, "Square Fruit": 25,
            "Hero Fruit": 10, "Dark Fruit": 10, "Strong Fruit": 25,
            "Tasty Fruit": 30, "Heart Fruit": 30, "Chao Fruit": 55,
            "Orange Fruit": 35, "Yellow Fruit": 50, "Green Fruit": 50,
            "Red Fruit": 60, "Blue Fruit": 40, "Pink Fruit": 55, "Purple Fruit": 45,
            "Swim Fruit": 15, "Fly Fruit": 15, "Run Fruit": 15, "Power Fruit": 15,
            "Garden Nut": 10, "Strange Mushroom": 10
        }

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
        """
        Opens the black market. Defaults to fruits market if no type is specified.
        """
        try:
            # Default to fruits market
            page_1_output_path = "black_market_fruits_page_1_temp.png"
            page_2_output_path = "black_market_fruits_page_2_temp.png"

            # Generate images for the fruit market
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

            # Create embed
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

            # Create the view for navigation
            view = MarketView(
                embed=embed,
                icon_path=self.BLACK_MARKET_ICON_PATH,
                thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                page_1_path=page_1_output_path,
                page_2_path=page_2_output_path,
                black_market_cog=self,
                total_pages=3
            )

            # Send the market embed and view
            await interaction.response.send_message(
                files=[icon_file, thumb_file, page_1_file],
                embed=embed,
                view=view
            )
            msg = await interaction.original_response()

            # Save the message ID for the market view
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

        # Create an embed with the black market thumbnail
        description = (
            f"{interaction.user.mention} bought {quantity}x {actual_item_name} for {price} rings!\n"
            f"You now have {current_inv['rings']} rings."
        )
        embed = discord.Embed(title="Chao Bot", description=description, color=self.embed_color)
        embed.set_thumbnail(url="attachment://black_market.png")
        thumb_file = discord.File(self.BLACK_MARKET_THUMBNAIL_PATH, filename="black_market.png")
        await interaction.response.send_message(embed=embed, file=thumb_file)


    async def cog_unload(self):
        temp_files = ["black_market_fruits_page_1_temp.png", "black_market_fruits_page_2_temp.png"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
