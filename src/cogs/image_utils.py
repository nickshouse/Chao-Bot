import os
from PIL import Image
from discord.ext import commands

class ImageUtils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Set the assets directory relative to this file
        self.assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../assets')
        self.TICK_SPACING = 105
        self.LEVEL_POSITION_OFFSET = (826, -106)
        self.LEVEL_SPACING = 60
        self.EXP_POSITIONS = {
            stat: [(183 + i * 60, y) for i in range(4)]
            for stat, y in zip(
                ['swim', 'fly', 'run', 'power', 'mind', 'stamina'],
                [302, 576, 868, 1161, 1454, 1732]
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

    def paste_image(
            self, template_path, overlay_path, output_path,
            tick_positions, *stats):
        with Image.open(template_path) as template, \
                Image.open(overlay_path) as overlay:
            overlay = overlay.convert("RGBA")
            # Paste EXP numbers
            for stat, exp in zip(
                    ["swim", "fly", "run", "power", "mind", "stamina"],
                    stats[-6:]):
                exp_str = f"{int(exp):04d}"
                for pos, digit in zip(
                        self.EXP_POSITIONS[stat], exp_str):
                    template.paste(
                        self.num_images[digit], pos, self.num_images[digit])
            # Paste ticks
            for pos, ticks in zip(tick_positions, stats[:6]):
                for i in range(int(ticks)):
                    tick_pos = (pos[0] + i * self.TICK_SPACING, pos[1])
                    template.paste(overlay, tick_pos, overlay)
            # Paste levels
            for pos, level in zip(tick_positions, stats[6:12]):
                tens = int(level) // 10
                ones = int(level) % 10
                x_offset, y_offset = self.LEVEL_POSITION_OFFSET
                template.paste(
                    self.num_images[str(tens)],
                    (pos[0] + x_offset, pos[1] + y_offset),
                    self.num_images[str(tens)])
                template.paste(
                    self.num_images[str(ones)],
                    (pos[0] + x_offset + self.LEVEL_SPACING,
                     pos[1] + y_offset),
                    self.num_images[str(ones)])
            template.save(output_path)

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
