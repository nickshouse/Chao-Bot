from PIL import Image

def paste_image(template_path, overlay_path, output_path, position):
    template = Image.open(template_path)
    overlay = Image.open(overlay_path)

    # Ensure the overlay image has an alpha channel
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # Now the alpha channel can be used as the mask
    template.paste(overlay, position, overlay)

    template.save(output_path)

# Paths to the images
template_path = '../assets/stats_template.png'
overlay_path = '../assets/tick_filled.png'
output_path = './output_image.png'

# Position where the overlay image should be pasted onto the template
position = (100, 200)    # Replace x and y with the coordinates where you want to paste the overlay

# Call the function
paste_image(template_path, overlay_path, output_path, position)
