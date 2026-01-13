from PIL import Image, ImageDraw, ImageFont

from pathlib import Path
import io

font_path = Path(__file__).parent / "SourceHanSans.otf"

def generate_image(bg_file: str, text = "", font_size = 250, text_color = "black", stroke=""):

    img_path = Path(__file__).parent / bg_file
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    image_width, image_height = img.size

    x = (image_width - text_width) / 2
    y = (image_height - text_height) / 2 - font_size / 4

    draw.text((x, y), text, fill=text_color, font=font, stroke_fill=stroke, stroke_width=10)
    return img