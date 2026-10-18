"""Add a north-facing watering can using only the original gardener palette."""
from PIL import Image, ImageDraw
image = Image.open("assets/npcs/gardener.png").convert("RGBA").crop((0, 20, 14, 40))
draw = ImageDraw.Draw(image)
draw.rectangle((0, 11, 4, 15), fill=(0, 0, 0, 255))
draw.rectangle((1, 12, 3, 14), fill=(35, 84, 54, 255))
draw.line((1, 12, 0, 10), fill=(148, 112, 61, 255))
draw.rectangle((2, 11, 3, 11), fill=(148, 112, 61, 255))
draw.point((4, 13), fill=(240, 184, 144, 255))
image.save("assets/npcs/gardener_water.png")
