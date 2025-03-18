import os
import json
import discord
from discord.ui import View, Button
from config import MARKET_PERSISTENT_VIEWS_FILE

class MarketView(View):
    def __init__(self, embed: discord.Embed, icon_path: str, thumbnail_path: str,
                 page_1_path: str, page_2_path: str, black_market_cog, total_pages=3, current_page: int = None,
                 state_file: str = MARKET_PERSISTENT_VIEWS_FILE):
        super().__init__(timeout=None)
        self.embed = embed
        self.icon_path = icon_path
        self.thumbnail_path = thumbnail_path
        self.page_1_path = page_1_path
        self.page_2_path = page_2_path
        self.black_market_cog = black_market_cog
        self.total_pages = total_pages
        self.state_file = state_file

        # Load persistent state if available; otherwise, default to page 1.
        self.current_page = current_page if current_page is not None else self.load_state(default_page=1)

        self.add_navigation_buttons()

    @staticmethod
    def _read_json(file_path: str, default: dict = None) -> dict:
        default = default or {}
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    @staticmethod
    def _write_json(file_path: str, data: dict):
        with open(file_path, "w") as f:
            json.dump(data, f)

    def save_state(self):
        """Save the current page to the persistent state file."""
        data = self._read_json(self.state_file)
        key = f"{self.black_market_cog.bot.user.id}_{self.black_market_cog.__class__.__name__}"
        data[key] = {"current_page": self.current_page}
        self._write_json(self.state_file, data)

    def load_state(self, default_page: int = 1) -> int:
        data = self._read_json(self.state_file)
        key = f"{self.black_market_cog.bot.user.id}_{self.black_market_cog.__class__.__name__}"
        return data.get(key, {}).get("current_page", default_page)

    def add_navigation_buttons(self):
        self.clear_items()
        self.add_item(self.create_button("⬅️", "previous_page", f"{self.black_market_cog.bot.user.id}_prev"))
        self.add_item(self.create_button("➡️", "next_page", f"{self.black_market_cog.bot.user.id}_next"))
        self.add_item(self.create_button("🔄", "refresh_view", f"{self.black_market_cog.bot.user.id}_refresh"))

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def previous_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page - 1 if self.current_page > 1 else self.total_pages
        self.save_state()
        await self.update_market(interaction)

    async def next_page(self, interaction: discord.Interaction):
        self.current_page = self.current_page + 1 if self.current_page < self.total_pages else 1
        self.save_state()
        await self.update_market(interaction)

    async def refresh_view(self, interaction: discord.Interaction):
        await self.update_market(interaction)

    async def update_market(self, interaction: discord.Interaction):
        """
        Updates the market page display based on the current page.
        """
        fruit_prices = self.black_market_cog.load_fruit_prices()

        page_1_output_path = self.page_1_path
        page_2_output_path = self.page_2_path

        attachments = [
            discord.File(self.icon_path, filename="Black_Market.png"),
            discord.File(self.thumbnail_path, filename="black_market.png"),
        ]
        image_filename = None

        try:
            if self.current_page == 1:
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
                self.embed.clear_fields()
                self.embed.set_image(url=None)
                page_3_items = [
                    "Swim Fruit", "Fly Fruit", "Run Fruit",
                    "Power Fruit", "Garden Nut", "Strange Mushroom"
                ]
                cost_text = "\n".join(
                    f"- **{item}** ({fruit_prices[item]} rings)" for item in page_3_items
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

    def save_persistent_view(self, view_data: dict):
        """Save persistent view data to the persistent JSON file."""
        data = self._read_json(MARKET_PERSISTENT_VIEWS_FILE)
        key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data.get('market_id', 'default')}"
        data[key] = view_data
        self._write_json(MARKET_PERSISTENT_VIEWS_FILE, data)

    @classmethod
    def load_all_persistent_views(cls, bot: discord.ext.commands.Bot) -> None:
        """Loads all persistent MarketView instances from the JSON file and registers them with the bot."""
        data = cls._read_json(MARKET_PERSISTENT_VIEWS_FILE)
        for view_data in data.values():
            # We require the keys for guild_id, user_id, current_page, and total_pages.
            required_keys = {"guild_id", "user_id", "current_page", "total_pages"}
            if not required_keys.issubset(view_data.keys()):
                continue
            cog = bot.get_cog("BlackMarket")
            if not cog:
                continue
            view = cls.from_data(view_data, cog)
            bot.add_view(view)

    @classmethod
    def from_data(cls, view_data: dict, cog) -> "MarketView":
        return cls(
            embed=discord.Embed(),  # Optionally, reconstruct or create a new embed.
            icon_path=getattr(cog, "BLACK_MARKET_ICON_PATH", ""),
            thumbnail_path=getattr(cog, "BLACK_MARKET_THUMBNAIL_PATH", ""),
            page_1_path=getattr(cog, "BLACK_MARKET_FRUITS_PAGE_1_PATH", ""),
            page_2_path=getattr(cog, "BLACK_MARKET_FRUITS_PAGE_2_PATH", ""),
            black_market_cog=cog,
            total_pages=view_data["total_pages"],
            current_page=view_data.get("current_page", 1),
            state_file=MARKET_PERSISTENT_VIEWS_FILE
        )

    @staticmethod
    def _write_json(file_path: str, data: dict):
        with open(file_path, "w") as f:
            json.dump(data, f)
