import os
from pathlib import Path
from PIL import Image
from discord.ext import commands
from typing import Dict, Tuple

from config import ASSETS_DIR  # <-- Make sure you have this in config.py

class ImageUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Remove manual path assembly; use ASSETS_DIR from config
        self.assets_dir = Path(ASSETS_DIR)

        # Directory for digit images, "blank.png", etc.
        self.resized_dir = self.assets_dir / "resized"

        self.TICK_SPACING = 105
        self.LEVEL_POSITION_OFFSET = (826, -106)
        self.LEVEL_SPACING = 60

        # Adjusted EXP_POSITIONS
        self.EXP_POSITIONS = {
            stat: [(183 + i * 60, y) for i in range(4)]
            for stat, y in zip(
                ['swim', 'fly', 'run', 'power', 'stamina'],
                [302, 576, 868, 1161, 1454]
            )
        }

        # Pre-load digit images 0-9 from the "resized" folder
        self.num_images = {
            str(i): Image.open(self.resized_dir / f"{i}.png") for i in range(10)
        }

    def combine_images_with_face(
            self,
            background_path: str,
            chao_image_path: str,
            eyes_image_path: str,
            mouth_image_path: str,
            output_path: str
    ):
        with Image.open(background_path).convert("RGBA") as background, \
             Image.open(chao_image_path).convert("RGBA") as chao_img, \
             Image.open(eyes_image_path).convert("RGBA") as eyes_img, \
             Image.open(mouth_image_path).convert("RGBA") as mouth_img:

            # Resize images
            chao_img = chao_img.resize((70, 70), Image.LANCZOS)
            background = background.resize((70, 70), Image.LANCZOS)
            eyes_img = eyes_img.resize((70, 70), Image.LANCZOS)
            mouth_img = mouth_img.resize((70, 70), Image.LANCZOS)

            # Composite the images
            chao_with_eyes = Image.alpha_composite(chao_img, eyes_img)
            chao_with_face = Image.alpha_composite(chao_with_eyes, mouth_img)
            final_image = Image.alpha_composite(background, chao_with_face)
            final_image.save(output_path)

    def paste_page1_image(
            self,
            template_path: str,
            overlay_path: str,
            output_path: str,
            tick_positions: list,
            power_ticks: int, swim_ticks: int, fly_ticks: int, run_ticks: int, stamina_ticks: int,
            power_level: int, swim_level: int, fly_level: int, run_level: int, stamina_level: int,
            power_exp: int, swim_exp: int, fly_exp: int, run_exp: int, stamina_exp: int
    ):
        """
        Generate the Page 1 stats image with ticks, levels, and EXP values for Chao stats.
        """
        with Image.open(template_path) as template, \
             Image.open(overlay_path).convert("RGBA") as overlay:

            # ---- Paste Ticks ----
            for pos, ticks in zip(
                tick_positions,
                [power_ticks, swim_ticks, fly_ticks, run_ticks, stamina_ticks]
            ):
                for i in range(int(ticks)):
                    tick_pos = (pos[0] + i * self.TICK_SPACING, pos[1])
                    template.paste(overlay, tick_pos, overlay)

            # ---- Paste Levels ----
            for pos, level in zip(
                tick_positions,
                [power_level, swim_level, fly_level, run_level, stamina_level]
            ):
                level = int(level)
                tens = level // 10
                ones = level % 10
                x_offset, y_offset = self.LEVEL_POSITION_OFFSET

                # Tens digit
                tens_img = self.num_images.get(str(tens), self.num_images['0'])
                template.paste(tens_img, (pos[0] + x_offset, pos[1] + y_offset), tens_img)

                # Ones digit
                ones_img = self.num_images.get(str(ones), self.num_images['0'])
                template.paste(
                    ones_img,
                    (pos[0] + x_offset + self.LEVEL_SPACING, pos[1] + y_offset),
                    ones_img
                )

            # ---- Paste EXP ----
            for stat, exp_val in zip(
                ["swim", "fly", "run", "power", "stamina"],
                [swim_exp, fly_exp, run_exp, power_exp, stamina_exp]
            ):
                exp_str = f"{int(exp_val):04d}"  # zero-padded 4 digits
                for pos, digit in zip(self.EXP_POSITIONS[stat], exp_str):
                    digit_img = self.num_images.get(digit, self.num_images['0'])
                    template.paste(digit_img, pos, digit_img)

            template.save(output_path)

    def paste_page2_image(
            self,
            template_path: str,
            overlay_path: str,
            output_path: str,
            stats_positions: Dict[str, Tuple[int, int]],
            stats_values: Dict[str, int]
    ):
        """
        Paste multiple stats ticks for Page 2 (belly, happiness, illness, energy, hp),
        plus numeric percentages.
        """
        # Instead of a hard-coded path, use our pre-loaded digit images in self.num_images
        # We'll also need a 'blank.png' from the same "resized" directory:
        blank_image_path = self.resized_dir / "blank.png"
        blank_image = Image.open(blank_image_path) if blank_image_path.exists() else None

        # Coordinates for the percentage display
        percentage_coords = {
            "belly": (1044, 214),
            "happiness": (1044, 490),
            "illness": (1044, 782),
            "energy": (1044, 1073),
            "hp": (1044, 1370)
        }

        with Image.open(template_path) as template, \
             Image.open(overlay_path).convert("RGBA") as overlay:

            # ---- Paste tick marks ----
            for stat, position in stats_positions.items():
                ticks = stats_values.get(stat, 0)
                for i in range(int(ticks)):
                    tick_pos = (position[0] + i * self.TICK_SPACING, position[1])
                    template.paste(overlay, tick_pos, overlay)

            def paste_percentage(percentage: int, coords: Tuple[int, int]):
                x_base, y_base = coords
                if not blank_image:
                    # if blank_image is missing, fallback logic
                    pass

                # Break into digits
                hundreds = percentage // 100
                tens = (percentage % 100) // 10
                ones = percentage % 10

                # If exactly 0, show "0" after two blank spaces
                if percentage == 0:
                    for _ in range(2):
                        if blank_image:
                            template.paste(blank_image, (x_base, y_base), blank_image)
                        x_base += self.LEVEL_SPACING
                    digit_0 = self.num_images.get("0")
                    template.paste(digit_0, (x_base, y_base), digit_0)
                    return

                # If 1 or 2 digit number, paste blank(s) first
                if hundreds == 0:
                    if tens == 0:
                        # 1-digit
                        for _ in range(2):
                            if blank_image:
                                template.paste(blank_image, (x_base, y_base), blank_image)
                            x_base += self.LEVEL_SPACING
                    else:
                        # 2-digit
                        if blank_image:
                            template.paste(blank_image, (x_base, y_base), blank_image)
                        x_base += self.LEVEL_SPACING
                else:
                    # 3-digit
                    digit_img = self.num_images.get(str(hundreds), self.num_images['0'])
                    template.paste(digit_img, (x_base, y_base), digit_img)
                    x_base += self.LEVEL_SPACING

                # Tens digit
                digit_img = self.num_images.get(str(tens), self.num_images['0'])
                template.paste(digit_img, (x_base, y_base), digit_img)
                x_base += self.LEVEL_SPACING

                # Ones digit
                digit_img = self.num_images.get(str(ones), self.num_images['0'])
                template.paste(digit_img, (x_base, y_base), digit_img)

            # Calculate/paste percentages
            for stat, coords in percentage_coords.items():
                ticks = stats_values.get(stat, 0)
                # Example formula for converting ticks to percent
                percentage = int((ticks / 10) * 100)
                paste_percentage(percentage, coords)

            template.save(output_path)

    def paste_black_market_prices_page1(
        self,
        template_path: str,
        output_path: str,
        fruit_prices: Dict[str, int]
    ):
        """
        Dynamically paste fruit prices onto a template for Black Market (Page 1).
        """
        fruit_coords = {
            "Round Fruit":    (1220, 220),
            "Triangle Fruit": (1220, 375),
            "Square Fruit":   (1220, 530),
            "Hero Fruit":     (1220, 675),
            "Dark Fruit":     (1220, 835),
            "Strong Fruit":   (1220, 990),
            "Tasty Fruit":    (1220, 1140),
            "Heart Fruit":    (1220, 1280),
            "Chao Fruit":     (1220, 1430),
        }

        with Image.open(template_path).convert("RGBA") as template:
            for fruit_name, (x, y) in fruit_coords.items():
                price = fruit_prices.get(fruit_name, 0)
                digits_str = str(price)
                spacing = 60
                x_current = x

                for digit in digits_str:
                    digit_img = self.num_images.get(digit, self.num_images['0'])
                    template.paste(digit_img, (x_current, y), digit_img)
                    x_current += spacing

            template.save(output_path, format="PNG")

    def paste_black_market_prices_page2(
        self,
        template_path: str,
        output_path: str,
        fruit_prices: Dict[str, int]
    ):
        """
        Dynamically paste fruit prices onto a template for Black Market (Page 2).
        """
        fruit_coords = {
            "Orange Fruit":  (1220, 220),
            "Yellow Fruit":  (1220, 375),
            "Green Fruit":   (1220, 530),
            "Red Fruit":     (1220, 675),
            "Blue Fruit":    (1220, 835),
            "Pink Fruit":    (1220, 990),
            "Purple Fruit":  (1220, 1140),
        }

        with Image.open(template_path).convert("RGBA") as template:
            for fruit_name, (x, y) in fruit_coords.items():
                price = fruit_prices.get(fruit_name, 0)
                digits_str = str(price)
                spacing = 60
                x_current = x

                for digit in digits_str:
                    digit_img = self.num_images.get(digit, self.num_images['0'])
                    template.paste(digit_img, (x_current, y), digit_img)
                    x_current += spacing

            template.save(output_path, format="PNG")

    def change_image_hue(self, image_path: str, output_path: str, hue: int, saturation: float):
        """
        Adjust the hue/saturation of an image.
        """
        img = Image.open(image_path).convert('RGB')
        hsv_img = img.convert('HSV')
        h, s, v = hsv_img.split()
        h = h.point(lambda p: hue)
        s = s.point(lambda p: int(p * saturation))
        hsv_img = Image.merge('HSV', (h, s, v))
        rgb_img = hsv_img.convert('RGB')
        rgb_img.save(output_path)

async def setup(bot):
    await bot.add_cog(ImageUtils(bot))
