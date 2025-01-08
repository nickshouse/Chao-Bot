# image_utils.py

import os
from PIL import Image
from discord.ext import commands
from typing import Dict, Tuple  # Added import for type annotations

class ImageUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Set the assets directory relative to this file
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../assets')
        self.TICK_SPACING = 105
        self.LEVEL_POSITION_OFFSET = (826, -106)
        self.LEVEL_SPACING = 60
        # Adjusted EXP_POSITIONS to remove the "mind" stat and shift "stamina" up
        self.EXP_POSITIONS = {
            stat: [(183 + i * 60, y) for i in range(4)]
            for stat, y in zip(
                ['swim', 'fly', 'run', 'power', 'stamina'],
                [302, 576, 868, 1161, 1454]
            )
        }
        self.num_images = {
            str(i): Image.open(
                os.path.join(self.assets_dir, f"resized/{i}.png")
            )
            for i in range(10)
        }

    def combine_images_with_face(
            self, background_path, chao_image_path, eyes_image_path,
            mouth_image_path, output_path):
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
            self, template_path, overlay_path, output_path,
            tick_positions, power_ticks, swim_ticks, fly_ticks, run_ticks, stamina_ticks,
            power_level, swim_level, fly_level, run_level, stamina_level,
            power_exp, swim_exp, fly_exp, run_exp, stamina_exp):
        """
        Generate the Page 1 stats image with ticks, levels, and EXP values for Chao stats.
        This function modifies the template image and saves the final image at the output path.
        """
        # Open the template and overlay images
        with Image.open(template_path) as template, \
                Image.open(overlay_path).convert("RGBA") as overlay:

            # Paste Ticks
            for pos, ticks in zip(tick_positions, [power_ticks, swim_ticks, fly_ticks, run_ticks, stamina_ticks]):
                for i in range(int(ticks)):
                    tick_pos = (pos[0] + i * self.TICK_SPACING, pos[1])
                    template.paste(overlay, tick_pos, overlay)

            # Paste Levels
            for pos, level in zip(tick_positions, [power_level, swim_level, fly_level, run_level, stamina_level]):
                level = int(level)  # Ensure the level is an integer
                tens = level // 10  # Extract tens digit
                ones = level % 10   # Extract ones digit
                x_offset, y_offset = self.LEVEL_POSITION_OFFSET

                # Paste tens digit
                template.paste(
                    self.num_images.get(str(tens), self.num_images['0']),
                    (pos[0] + x_offset, pos[1] + y_offset),
                    self.num_images.get(str(tens), self.num_images['0'])
                )
                # Paste ones digit
                template.paste(
                    self.num_images.get(str(ones), self.num_images['0']),
                    (pos[0] + x_offset + self.LEVEL_SPACING, pos[1] + y_offset),
                    self.num_images.get(str(ones), self.num_images['0'])
                )

            # Paste EXP
            for stat, exp in zip(["swim", "fly", "run", "power", "stamina"], 
                                [swim_exp, fly_exp, run_exp, power_exp, stamina_exp]):
                exp_str = f"{int(exp):04d}"  # Convert EXP to a zero-padded 4-digit string
                for pos, digit in zip(self.EXP_POSITIONS[stat], exp_str):
                    template.paste(
                        self.num_images.get(digit, self.num_images['0']),
                        pos,
                        self.num_images.get(digit, self.num_images['0'])
                    )

            # Save the Final Image
            template.save(output_path)

    def paste_page2_image(
            self, template_path, overlay_path, output_path,
            stats_positions: Dict[str, Tuple[int, int]],
            stats_values: Dict[str, int]):
        """
        Paste multiple stats ticks for Page 2 and display the percentages for all Page 2 stats.
        Includes: Belly, Happiness, Illness, Energy, and HP.
        Ensures alignment by pasting 'blank.png' for 1 and 2-digit numbers.
        """
        # Updated path for number images
        number_images_dir = r"C:\Users\You\Documents\GitHub\Chao-Bot\assets\resized"
        num_images = {
            str(i): Image.open(os.path.join(number_images_dir, f"{i}.png"))
            for i in range(10)
        }
        blank_image = Image.open(os.path.join(number_images_dir, "blank.png"))

        # Coordinates for percentage display
        percentage_coords = {
            "belly": (1044, 214),
            "happiness": (1044, 490),
            "illness": (1044, 782),
            "energy": (1044, 1073),
            "hp": (1044, 1370)
        }

        with Image.open(template_path) as template, \
                Image.open(overlay_path).convert("RGBA") as overlay:

            # Paste tick marks for each stat
            for stat, position in stats_positions.items():
                ticks = stats_values.get(stat, 0)
                for i in range(int(ticks)):
                    tick_pos = (position[0] + i * self.TICK_SPACING, position[1])
                    template.paste(overlay, tick_pos, overlay)

            # Function to calculate and paste percentages
            def paste_percentage(stat_name, percentage, coords):
                x_base, y_base = coords
                hundreds = percentage // 100
                tens = (percentage % 100) // 10
                ones = percentage % 10

                # Handle alignment for 0% (1-digit number: paste 2 blanks and '0')
                if percentage == 0:
                    template.paste(blank_image, (x_base, y_base), blank_image)
                    x_base += self.LEVEL_SPACING
                    template.paste(blank_image, (x_base, y_base), blank_image)
                    x_base += self.LEVEL_SPACING
                    template.paste(num_images.get("0"), (x_base, y_base), num_images.get("0"))
                    return

                # Handle alignment for 1-digit numbers (paste 2 blanks first)
                if hundreds == 0 and tens == 0:
                    template.paste(blank_image, (x_base, y_base), blank_image)
                    x_base += self.LEVEL_SPACING
                    template.paste(blank_image, (x_base, y_base), blank_image)
                    x_base += self.LEVEL_SPACING

                # Handle alignment for 2-digit numbers (paste 1 blank first)
                elif hundreds == 0:
                    template.paste(blank_image, (x_base, y_base), blank_image)
                    x_base += self.LEVEL_SPACING

                # Paste hundreds place if it exists
                if hundreds > 0:
                    template.paste(
                        num_images.get(str(hundreds), num_images['0']),
                        (x_base, y_base),
                        num_images.get(str(hundreds), num_images['0'])
                    )
                    x_base += self.LEVEL_SPACING

                # Paste tens place
                template.paste(
                    num_images.get(str(tens), num_images['0']),
                    (x_base, y_base),
                    num_images.get(str(tens), num_images['0'])
                )
                x_base += self.LEVEL_SPACING

                # Paste ones place
                template.paste(
                    num_images.get(str(ones), num_images['0']),
                    (x_base, y_base),
                    num_images.get(str(ones), num_images['0'])
                )


            # Calculate and paste percentages for all stats
            for stat, coords in percentage_coords.items():
                ticks = stats_values.get(stat, 0)
                percentage = int((ticks / 10) * 100)  # Convert ticks to percentage
                paste_percentage(stat, percentage, coords)

            # Save the updated image
            template.save(output_path)


    def paste_black_market_prices_page1(
        self, template_path: str, output_path: str, fruit_prices: Dict[str, int]
    ):
        """
        Generate the Black Market Page 1 image dynamically by pasting prices
        directly onto the provided template and saving the result to `output_path`.
        """
        fruit_coords = {
            "Round Fruit":   (1220, 220),
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

                # Paste each digit of the price
                for digit in digits_str:
                    digit_img = self.num_images.get(digit, self.num_images['0'])
                    template.paste(digit_img, (x_current, y), digit_img)
                    x_current += spacing

            # Save the updated image to the specified output path
            template.save(output_path, format="PNG")

    def paste_black_market_prices_page2(
        self, template_path: str, output_path: str, fruit_prices: Dict[str, int]
    ):
        """
        Generate the Black Market Page 2 image dynamically by pasting prices
        directly onto the provided template and saving the result to `output_path`.
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

                # Paste each digit of the price
                for digit in digits_str:
                    digit_img = self.num_images.get(digit, self.num_images['0'])
                    template.paste(digit_img, (x_current, y), digit_img)
                    x_current += spacing

            # Save the updated image to the specified output path
            template.save(output_path, format="PNG")


    def change_image_hue(
            self, image_path, output_path, hue, saturation):
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
