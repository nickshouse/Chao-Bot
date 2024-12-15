# cogs/black_market.py

import os
import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import asyncio


class MarketView(View):
    def __init__(self, embed: discord.Embed, icon_path: str, thumbnail_path: str, page_1_path: str, page_2_path: str, total_pages=2):
        super().__init__(timeout=None)
        self.embed = embed
        self.icon_path = icon_path
        self.thumbnail_path = thumbnail_path
        self.page_1_path = page_1_path
        self.page_2_path = page_2_path
        self.current_page = 1  # Start at Page 1
        self.total_pages = total_pages

        # Replace text buttons with arrow emojis using the 'emoji' parameter
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
        # Cycle to the previous page
        self.current_page = self.current_page - 1 if self.current_page > 1 else self.total_pages
        await self.update_market(interaction, self.current_page)

    async def next_page(self, interaction: discord.Interaction):
        # Cycle to the next page
        self.current_page = self.current_page + 1 if self.current_page < self.total_pages else 1
        await self.update_market(interaction, self.current_page)

    async def update_market(self, interaction: discord.Interaction, page: int):
        if page == 1:
            image_filename = "black_market_fruits_page_1.png"
            image_path = self.page_1_path
        else:
            image_filename = "black_market_fruits_page_2.png"
            image_path = self.page_2_path

        # Update embed image and footer
        self.embed.set_image(url=f"attachment://{image_filename}")
        self.embed.set_footer(text=f"Page {page} / {self.total_pages}")

        try:
            await interaction.response.edit_message(
                embed=self.embed,
                view=self,
                attachments=[
                    discord.File(self.icon_path, filename="Black_Market.png"),
                    discord.File(self.thumbnail_path, filename="black_market.png"),
                    discord.File(image_path, filename=image_filename)
                ]
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

        # Load configuration or receive it from a shared config
        with open('config.json', 'r') as f:
            config = json.load(f)

        self.FORM_LEVELS = config['FORM_LEVELS']
        self.ALIGNMENTS = config['ALIGNMENTS']
        self.FRUIT_TICKS_RANGE = config['FRUIT_TICKS_RANGE']
        self.FRUIT_STATS = config['FRUIT_STATS']

        self.fruits = [
            "Garden Nut", "Hero Fruit", "Dark Fruit", "Round Fruit", "Triangle Fruit",
            "Heart Fruit", "Square Fruit", "Chao Fruit", "Power Fruit",
            "Run Fruit", "Swim Fruit", "Fly Fruit", "Tasty Fruit", "Strange Mushroom"
        ]
        self.fruit_prices = 15
        self.CUSTOM_EMOJI_ID = 1176313914464681984
        self.embed_color = discord.Color.blue()

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

        # If we have a saved message ID, recreate the MarketView and re-add it.
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
                embed.set_footer(text="Page 1 / 2")  # Initial footer

                view = MarketView(
                    embed=embed,
                    icon_path=self.BLACK_MARKET_ICON_PATH,
                    thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                    page_1_path=self.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                    page_2_path=self.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                    total_pages=2  # Specify total pages
                )
                self.bot.add_view(view, message_id=self.market_message_id)

    def send_embed(self, ctx, description, title="Chao Bot"):
        embed = discord.Embed(title=title, description=description, color=self.embed_color)
        return ctx.send(embed=embed)

    async def market(self, ctx, *, market_type: str = None):
        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        rings = int(current_inv.get('rings', 0))
        ring_emoji = f'<:custom_emoji:{self.CUSTOM_EMOJI_ID}>'

        if market_type and market_type.lower() == "fruits":
            icon_file = discord.File(self.BLACK_MARKET_ICON_PATH, filename="Black_Market.png")
            thumb_file = discord.File(self.BLACK_MARKET_THUMBNAIL_PATH, filename="black_market.png")
            page_1_file = discord.File(self.BLACK_MARKET_FRUITS_PAGE_1_PATH, filename="black_market_fruits_page_1.png")

            embed = discord.Embed(color=self.embed_color)
            embed.set_author(name="Black Market - Fruits", icon_url="attachment://Black_Market.png")
            embed.description = "Buy fruits to feed your Chao!"
            embed.add_field(name="Rings", value=f"{ring_emoji} x {rings}", inline=True)
            embed.set_thumbnail(url="attachment://black_market.png")
            embed.set_image(url="attachment://black_market_fruits_page_1.png")
            embed.set_footer(text="Page 1 / 2")  # Initial footer

            view = MarketView(
                embed=embed,
                icon_path=self.BLACK_MARKET_ICON_PATH,
                thumbnail_path=self.BLACK_MARKET_THUMBNAIL_PATH,
                page_1_path=self.BLACK_MARKET_FRUITS_PAGE_1_PATH,
                page_2_path=self.BLACK_MARKET_FRUITS_PAGE_2_PATH,
                total_pages=2  # Specify total pages
            )

            try:
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

        guild_id, user_id = str(ctx.guild.id), str(ctx.author.id)
        inv_path = self.data_utils.get_path(guild_id, user_id, 'user_data', 'inventory.parquet')
        inv_df = self.data_utils.load_inventory(inv_path)
        current_inv = inv_df.iloc[-1].to_dict() if not inv_df.empty else {'rings': 0}
        rings = current_inv.get('rings', 0)

        fruit = next((f for f in self.fruits if f.lower() == item_name.lower()), None)
        if not fruit:
            return await self.send_embed(ctx, f"{ctx.author.mention}, '{item_name}' is not sold here.")

        total_cost = self.fruit_prices * quantity
        if rings < total_cost:
            return await self.send_embed(ctx, f"{ctx.author.mention}, not enough rings ({total_cost} needed).")

        current_inv['rings'] = rings - total_cost
        current_inv[fruit] = current_inv.get(fruit, 0) + quantity
        self.data_utils.save_inventory(inv_path, inv_df, current_inv)
        await self.send_embed(ctx, f"{ctx.author.mention} bought {quantity}x {fruit} for {total_cost} rings! Now you have {current_inv['rings']} rings.")


async def setup(bot):
    await bot.add_cog(BlackMarket(bot))
