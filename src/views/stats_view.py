# views/stats_view.py

import os, json, asyncio
import discord
from discord.ui import View, Button
from discord.ext import commands
from typing import List, Tuple, Dict
from config import PAGE1_TICK_POSITIONS, PAGE2_TICK_POSITIONS, PERSISTENT_VIEWS_FILE

class StatsView(View):
    def __init__(
        self,
        bot: commands.Bot,
        chao_name: str,
        guild_id: str,
        user_id: str,
        page1_tick_positions: List[Tuple[int, int]],
        page2_tick_positions: Dict[str, Tuple[int, int]],
        exp_positions: Dict[str, List[Tuple[int, int]]],
        num_images: Dict[str, discord.File],
        level_position_offset: Tuple[int, int],
        level_spacing: int,
        tick_spacing: int,
        chao_type_display: str,
        alignment_label: str,
        template_path: str,
        template_page_2_path: str,
        overlay_path: str,
        icon_path: str,
        image_utils,
        data_utils,
        total_pages: int = 2,
        current_page: int = 1,
        state_file: str = PERSISTENT_VIEWS_FILE
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.chao_name = chao_name
        self.guild_id = guild_id
        self.user_id = user_id
        self.page1_tick_positions = page1_tick_positions
        self.page2_tick_positions = page2_tick_positions
        self.exp_positions = exp_positions
        self.num_images = num_images
        self.level_position_offset = level_position_offset
        self.level_spacing = level_spacing
        self.tick_spacing = tick_spacing
        self.chao_type_display = chao_type_display
        self.alignment_label = alignment_label
        self.template_path = template_path
        self.template_page_2_path = template_page_2_path
        self.overlay_path = overlay_path
        self.icon_path = icon_path
        self.image_utils = image_utils
        self.data_utils = data_utils
        self.total_pages = total_pages
        self.current_page = current_page
        self.state_file = state_file
        self.save_state()
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
        data = StatsView._read_json(self.state_file)
        key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
        data[key] = {
            "chao_name": self.chao_name,
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "chao_type_display": self.chao_type_display or "Unknown",
            "alignment_label": self.alignment_label or "Neutral",
            "total_pages": self.total_pages,
            "current_page": self.current_page,
            # You can save additional information here if needed.
        }
        StatsView._write_json(self.state_file, data)

    def load_state(self, default_page: int = 1) -> int:
        data = StatsView._read_json(self.state_file)
        key = f"{self.guild_id}_{self.user_id}_{self.chao_name}"
        return data.get(key, {}).get("current_page", default_page)

    def add_navigation_buttons(self):
        self.clear_items()
        # Add previous button
        self.add_item(self.create_button("⬅️", "previous_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_prev"))
        # Add next button
        self.add_item(self.create_button("➡️", "next_page", f"{self.guild_id}_{self.user_id}_{self.chao_name}_next"))
        # Add refresh button
        self.add_item(self.create_button("🔄", "refresh_view", f"{self.guild_id}_{self.user_id}_{self.chao_name}_refresh"))

    def create_button(self, emoji: str, callback_name: str, custom_id: str) -> Button:
        button = Button(style=discord.ButtonStyle.primary, emoji=emoji, custom_id=custom_id)
        button.callback = getattr(self, callback_name)
        return button

    async def change_page(self, interaction: discord.Interaction, delta: int):
        new_page = self.current_page + delta
        if new_page < 1:
            new_page = self.total_pages
        elif new_page > self.total_pages:
            new_page = 1
        self.current_page = new_page
        self.save_state()
        await self.update_stats(interaction)

    async def previous_page(self, interaction: discord.Interaction):
        await self.change_page(interaction, -1)

    async def next_page(self, interaction: discord.Interaction):
        await self.change_page(interaction, 1)

    async def refresh_view(self, interaction: discord.Interaction):
        # Refresh button callback simply updates the view.
        await self.update_stats(interaction)

    async def _send(self, interaction: discord.Interaction, **kwargs):
        """
        Helper to send a response if one hasn't been sent yet;
        otherwise, sends a followup.
        """
        if not interaction.response.is_done():
            await interaction.response.send_message(**kwargs)
        else:
            await interaction.followup.send(**kwargs)

    async def update_stats(self, interaction: discord.Interaction):
        guild = self.bot.get_guild(int(self.guild_id))
        if not guild:
            return await self._send(interaction, content="Error: Could not find the guild.", ephemeral=True)
        member = guild.get_member(int(self.user_id))
        if not member:
            return await self._send(interaction, content="Error: Could not find the user in this guild.", ephemeral=True)

        chao_dir = self.data_utils.get_path(self.guild_id, guild.name, member, 'chao_data', self.chao_name)
        chao_stats_path = os.path.join(chao_dir, f'{self.chao_name}_stats.parquet')
        chao_df = self.data_utils.load_chao_stats(chao_stats_path)
        if chao_df.empty:
            return await self._send(interaction, content="No stats data available for this Chao.", ephemeral=True)
        chao_to_view = chao_df.iloc[-1].to_dict()
        image_path = os.path.join(chao_dir, f'{self.chao_name}_stats_page_{self.current_page}.png')

        if self.current_page == 1:
            stats = ['power', 'swim', 'fly', 'run', 'stamina']
            await asyncio.to_thread(
                self.image_utils.paste_page1_image,
                self.template_path,
                self.overlay_path,
                image_path,
                self.page1_tick_positions,
                *[chao_to_view.get(f"{stat}_ticks", 0) for stat in stats],
                *[chao_to_view.get(f"{stat}_level", 0) for stat in stats],
                *[chao_to_view.get(f"{stat}_exp", 0) for stat in stats]
            )
        else:
            stats_values = {stat: chao_to_view.get(f"{stat}_ticks", 0) for stat in self.page2_tick_positions}
            await asyncio.to_thread(
                self.image_utils.paste_page2_image,
                self.template_page_2_path,
                self.overlay_path,
                image_path,
                self.page2_tick_positions,
                stats_values
            )

        embed = discord.Embed(color=discord.Color.blue())
        embed.set_author(name=f"{self.chao_name}'s Stats", icon_url="attachment://Stats.png")
        embed.add_field(name="Type", value=self.chao_type_display, inline=True)
        embed.add_field(name="Alignment", value=self.alignment_label, inline=True)
        embed.set_thumbnail(url="attachment://chao_thumbnail.png")
        embed.set_image(url="attachment://stats_page.png")
        embed.set_footer(text=f"Page {self.current_page} / {self.total_pages}")

        await interaction.response.edit_message(
            embed=embed,
            attachments=[
                discord.File(image_path, "stats_page.png"),
                discord.File(self.icon_path, filename="Stats.png"),
                discord.File(os.path.join(chao_dir, f'{self.chao_name}_thumbnail.png'), "chao_thumbnail.png"),
            ],
            view=self
        )

    @classmethod
    def from_data(cls, view_data: Dict, cog) -> "StatsView":
        return cls(
            bot=cog.bot,
            chao_name=view_data["chao_name"],
            guild_id=view_data["guild_id"],
            user_id=view_data["user_id"],
            page1_tick_positions=getattr(cog, "PAGE1_TICK_POSITIONS", PAGE1_TICK_POSITIONS),
            page2_tick_positions=getattr(cog, "PAGE2_TICK_POSITIONS", PAGE2_TICK_POSITIONS),
            exp_positions=getattr(cog.image_utils, "EXP_POSITIONS", {}),
            num_images=getattr(cog.image_utils, "num_images", {}),
            level_position_offset=getattr(cog.image_utils, "LEVEL_POSITION_OFFSET", (0, 0)),
            level_spacing=getattr(cog.image_utils, "LEVEL_SPACING", 0),
            tick_spacing=getattr(cog.image_utils, "TICK_SPACING", 0),
            chao_type_display=view_data["chao_type_display"],
            alignment_label=view_data["alignment_label"],
            template_path=getattr(cog, "TEMPLATE_PATH", ""),
            template_page_2_path=getattr(cog, "TEMPLATE_PAGE_2_PATH", ""),
            overlay_path=getattr(cog, "OVERLAY_PATH", ""),
            icon_path=getattr(cog, "ICON_PATH", ""),
            image_utils=cog.image_utils,
            data_utils=cog.data_utils,
            total_pages=view_data["total_pages"],
            current_page=view_data.get("current_page", 1),
            state_file=PERSISTENT_VIEWS_FILE
        )

    def save_persistent_view(self, view_data: Dict):
        data = StatsView._read_json(PERSISTENT_VIEWS_FILE)
        key = f"{view_data['guild_id']}_{view_data['user_id']}_{view_data['chao_name']}"
        data[key] = view_data
        StatsView._write_json(PERSISTENT_VIEWS_FILE, data)

    @classmethod
    def load_all_persistent_views(cls, bot: commands.Bot) -> None:
        """Loads all persistent StatsView instances from the JSON file and registers them with the bot."""
        data = cls._read_json(PERSISTENT_VIEWS_FILE)
        for view_data in data.values():
            # Ensure required keys exist
            required_keys = {"chao_name", "guild_id", "user_id", "chao_type_display", "alignment_label", "total_pages", "current_page"}
            if not required_keys.issubset(view_data.keys()):
                continue
            # Create a view instance using from_data.
            # Adjust the cog name below to match the cog that owns the stats view (e.g. "ChaoLifecycle").
            cog = bot.get_cog("ChaoLifecycle")
            if not cog:
                continue
            view = cls.from_data(view_data, cog)
            bot.add_view(view)

    def load_persistent_views(self):
        """Instance method to load the current view state (if needed)."""
        self.current_page = self.load_state()

# To load persistent StatsView instances on bot startup, call:
# StatsView.load_all_persistent_views(bot)
