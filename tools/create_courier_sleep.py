"""Local couch-sleep cels, preserving the existing courier sprite and palette."""
from PIL import Image
source = Image.open("assets/npcs/courier.png").convert("RGBA")
profile = source.crop((0, 40, 14, 60))
skin = profile.getpixel((4, 9))
profile.putpixel((5, 10), skin)
profile.putpixel((4, 11), (0, 0, 0, 255))
profile.putpixel((4, 12), skin)
sheet = Image.new("RGBA", (56, 20))
for i in range(4):
    frame = profile.copy()
    if i % 2:
        frame.putpixel((3, 14), (0, 0, 0, 255))
        frame.putpixel((4, 14), profile.getpixel((5, 14)))
    if i >= 2:
        frame = frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    sheet.paste(frame, (i * 14, 0))
sheet.save("assets/npcs/courier_sleep_simple.png")
