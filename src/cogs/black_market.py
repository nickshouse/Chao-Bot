import os
import discord
from discord.ext import commands
from discord.ui import View, Button
import json



class MarketView(View):
    def __init__(self, embed: discord.Embed, icon_path: str, thumbnail_path: str, page_1_path: str, page_2_path: str, black_market_cog, total_pages=2):
        super().__init__(timeout=None)
        self.embed = embed
        self.icon_path = icon_path
        self.thumbnail_path = thumbnail_path
        self.page_1_path = page_1_path
        self.page_2_path = page_2_path
        self.black_market_cog = black_market_cog  # Store the BlackMarket cog reference
        self.current_page = 1  # Start at Page 1
        self.total_pages = total_pages

        self.add_item(self.previous_button())
        self.add_item(self.next_button())

    def previous_button(self) -> Button:
        button = Button(
            style=discord.ButtonStyle.primary,
            emoji="⬅️",  # Left arrow emoji
            custom_id="market_previous"
        )
        button.callback = self.previous_page
        return button

    def next_button(self) -> Button:
        button = Button(
            style=discord.ButtonStyle.primary,
            emoji="➡️",  # Right arrow emoji
            custom_id="market_next"
        )
        button.callback = self.next_page
        return button

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page - 1 if self.current_page > 1 else self.total_pages
        await self.update_market(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page + 1 if self.current_page < self.total_pages else 1
        await self.update_market(interaction)

    async def update_market(self, interaction: discord.Interaction):
        # Load updated fruit prices
        fruit_prices = self.black_market_cog.load_fruit_prices()

        # Temporary file paths
        page_1_output_path = "black_market_fruits_page_1_temp.png"
        page_2_output_path = "black_market_fruits_page_2_temp.png"

        # Regenerate the corresponding page with updated prices
        try:
            if self.current_page == 1:
                self.black_market_cog.image_utils.paste_black_market_prices_page1(
                    self.black_market_cog.BLACK_MARKET_FRUITS_PAGE_1_PATH, page_1_output_path, fruit_prices
                )
                image_path = page_1_output_path
            else:
                self.black_market_cog.image_utils.paste_black_market_prices_page2(
                    self.black_market_cog.BLACK_MARKET_FRUITS_PAGE_2_PATH, page_2_output_path, fruit_prices
                )
                image_path = page_2_output_path

            # Update embed
            image_filename = f"black_market_fruits_page_{self.current_page}.png"
            self.embed.set_image(url=f"attachment://{image_filename}")
            self.embed.set_footer(text=f"Page {self.current_page} / {self.total_pages}")

            # Send updated message
            await interaction.response.edit_message(
                embed=self.embed,
                view=self,
                attachments=[
                    discord.File(self.icon_path, filename="Black_Market.png"),
                    discord.File(self.thumbnail_path, filename="black_market.png"),
                    discord.File(image_path, filename=image_filename),
                ],
            )
        except Exception as e:
            print(f"[MarketView] Failed to edit message: {e}")
            await interaction.response.send_message("An error occurred while updating the market page.", ephemeral=True)


class BlackMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embed_color = discord.Color.blue()
        self.image_utils = self.data_utils = None
        self.market_message_id = None

        self.prices_file = "fruit_prices.json"

        self.default_prices = {
            "Round Fruit": 15, "Triangle Fruit": 15, "Square Fruit": 15,
            "Hero Fruit": 15, "Dark Fruit": 15, "Strong Fruit": 15,
            "Tasty Fruit": 15, "Heart Fruit": 15, "Chao Fruit": 15,
            "Orange Fruit": 15, "Yellow Fruit": 15, "Green Fruit": 15,
            "Red Fruit": 15, "Blue Fruit": 15, "Pink Fruit": 15, "Purple Fruit": 15
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
        self.BLACK_MARKET_THUMBNAIL_PATH = os.path.join(self.assets_dir, 'graphics/thumbnails/black_market.png')
        self.BLACK_MARKET_FRUITS_PAGE_1_PATH = os.path.join(self.assets_dir, 'graphics/cards/black_market_fruits_page_1.png')
        self.BLACK_MARKET_FRUITS_PAGE_2_PATH = os.path.join(self.assets_dir, 'graphics/cards/black_market_fruits_page_2.png')
        self.BLACK_MARKET_ICON_PATH = os.path.join(self.assets_dir, 'graphics/icons/Black_Market.png')

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
                embed.set_footer(text="Page 1 / 2")

                view = MarketView(
                    embed=embed,
                    icon_path=self.BLACK_MARKET_ICON_PATH,
                    thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                    page_1_path=self.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                    page_2_path=self.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                    black_market_cog=self,
                    total_pages=2
                )
                self.bot.add_view(view, message_id=self.market_message_id)

    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)



    async def market(self, ctx, *, market_type: str = None):
        guild_id, guild_name, user = str(ctx.guild.id), ctx.guild.name, ctx.author
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')

        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        rings = int(current_inv.get('rings', 0))
        ring_emoji = f'<:custom_emoji:1176313914464681984>'  # Updated to provided emoji ID

        if market_type and market_type.lower() == "fruits":
            # Generate updated images as temporary files
            page_1_output_path = "black_market_fruits_page_1_temp.png"
            page_2_output_path = "black_market_fruits_page_2_temp.png"

            try:
                # Ensure files are created successfully
                self.image_utils.paste_black_market_prices_page1(
                    self.BLACK_MARKET_FRUITS_PAGE_1_PATH, page_1_output_path, self.fruit_prices
                )
                self.image_utils.paste_black_market_prices_page2(
                    self.BLACK_MARKET_FRUITS_PAGE_2_PATH, page_2_output_path, self.fruit_prices
                )

                # Prepare attachments
                icon_file = discord.File(self.BLACK_MARKET_ICON_PATH, filename="Black_Market.png")
                thumb_file = discord.File(self.BLACK_MARKET_THUMBNAIL_PATH, filename="black_market.png")
                page_1_file = discord.File(page_1_output_path, filename="black_market_fruits_page_1.png")

                embed = discord.Embed(color=self.embed_color)
                embed.set_author(name="Black Market - Fruits", icon_url="attachment://Black_Market.png")
                embed.description = "Buy fruits to feed your Chao!"
                embed.add_field(name="Rings", value=f"{ring_emoji} x {rings}", inline=True)
                embed.set_thumbnail(url="attachment://black_market.png")
                embed.set_image(url="attachment://black_market_fruits_page_1.png")
                embed.set_footer(text="Page 1 / 2")

                view = MarketView(
                    embed=embed,
                    icon_path=self.BLACK_MARKET_ICON_PATH,
                    thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                    page_1_path=page_1_output_path,  # Include page_1_path
                    page_2_path=page_2_output_path,  # Include page_2_path
                    black_market_cog=self,
                    total_pages=2
                )

                # Send the message
                msg = await ctx.send(files=[icon_file, thumb_file, page_1_file], embed=embed, view=view)
                with open("market_message_id.txt", "w") as f:
                    f.write(str(msg.id))
                self.market_message_id = msg.id
                self.bot.add_view(view, message_id=msg.id)

            except Exception as e:
                print(f"[market] Failed to send market message: {e}")
                await ctx.send("An error occurred while opening the market.")
        else:
            await self.send_embed(ctx, "Please specify a valid market type. For example: `$market fruits`")


    async def buy(self, ctx, *, item_quantity: str):
        try:
            *item_parts, quantity = item_quantity.rsplit(' ', 1)
            item_name, quantity = ' '.join(item_parts), int(quantity)
        except ValueError:
            return await self.send_embed(ctx, f"{ctx.author.mention}, use `$buy [item] [quantity]`.")

        guild_id, guild_name, user = str(ctx.guild.id), ctx.guild.name, ctx.author
        inv_path = self.data_utils.get_path(guild_id, guild_name, user, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        rings = current_inv.get('rings', 0)

        if item_name not in self.fruit_prices:
            return await self.send_embed(ctx, f"{ctx.author.mention}, '{item_name}' is not sold here.")

        price = self.fruit_prices[item_name] * quantity
        if rings < price:
            return await self.send_embed(ctx, f"{ctx.author.mention}, not enough rings ({price} needed).")

        current_inv['rings'] = rings - price
        current_inv[item_name] = current_inv.get(item_name, 0) + quantity
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)
        await self.send_embed(ctx, f"{ctx.author.mention} bought {quantity}x {item_name} for {price} rings! Now you have {current_inv['rings']} rings.")
    
    async def cog_unload(self):
        # Cleanup temporary files
        temp_files = ["black_market_fruits_page_1_temp.png", "black_market_fruits_page_2_temp.png"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)


async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
