"""Compose existing sailor pixels and mirrored fishing tackle; no generation service.

Writes two 600 ms cels and an editable, lossless RGBA Aseprite source.
"""
from pathlib import Path
import json
import struct
import zlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sailor = Image.open(ROOT / 'assets/npcs/sailor.png').convert('RGBA').crop((0, 40, 14, 60))
tackle = Image.open(ROOT / 'assets/npcs/fisher_fishing.png').convert('RGBA')
sheet = Image.new('RGBA', (80, 28))
for frame in range(2):
    cel = Image.new('RGBA', (40, 28))
    cel.paste(sailor, (26, 8))
    west = tackle.crop((frame * 40, 0, frame * 40 + 40, 28)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    cel.paste(west.crop((0, 0, 26, 28)), (0, 0))
    # Bridge the old tackle hand to the sailor's sleeve. Only transparent
    # pixels are filled: the original sailor and tackle pixels stay intact.
    black, skin, cuff, blue = (0, 0, 0, 255), (215, 161, 117, 255), (232, 224, 192, 255), (40, 80, 160, 255)
    for x in range(25, 31):
        for y, color in ((20 + frame, black), (21 + frame, skin if x < 27 else cuff if x == 27 else blue), (22 + frame, black)):
            if cel.getpixel((x, y))[3] == 0:
                cel.putpixel((x, y), color)
    for y in range(20):
        for x in range(14):
            pixel = sailor.getpixel((x, y))
            if pixel[3]:
                assert cel.getpixel((x + 26, y + 8)) == pixel
    assert cel.crop((26, 24, 40, 28)).tobytes() == sailor.crop((0, 16, 14, 20)).tobytes()
    sheet.paste(cel, (frame * 40, 0))
sheet.save(ROOT / 'assets/npcs/sailor_fisher_fishing.png')


def chunk(kind, data):
    return struct.pack('<IH', len(data) + 6, kind) + data


frames = []
for index in range(2):
    chunks = []
    if index == 0:
        name = b'Sailor fishing west'
        chunks.append(chunk(0x2004, struct.pack('<HHHHHHB', 1, 0, 0, 0, 0, 0, 255)
                            + b'\0' * 3 + struct.pack('<H', len(name)) + name))
    cel = sheet.crop((index * 40, 0, index * 40 + 40, 28))
    chunks.append(chunk(0x2005, struct.pack('<HhhBHh', 0, 0, 0, 255, 2, 0)
                        + b'\0' * 5 + struct.pack('<HH', 40, 28) + zlib.compress(cel.tobytes())))
    data = b''.join(chunks)
    frames.append(struct.pack('<IHHHHI', 16 + len(data), 0xF1FA, len(chunks), 600, 0, 0) + data)
header = struct.pack('<IHHHHHIH', 128 + sum(map(len, frames)), 0xA5E0, 2, 40, 28, 32, 1, 600)
header += b'\0' * 8 + bytes([0]) + b'\0' * 3 + struct.pack('<HBBhhHH', 0, 1, 1, 0, 0, 0, 0)
(ROOT / 'art/npcs/sailor_fisher_fishing.aseprite').write_bytes(header.ljust(128, b'\0') + b''.join(frames))
(ROOT / 'assets/npcs/sailor_fisher_fishing.json').write_text(json.dumps({
    'frame_width': 40, 'frame_height': 28, 'frames': 2, 'duration_ms': 600,
    'sprite_offset': {'x': -26, 'y': -8}, 'facing': 'west',
    'source': 'art/npcs/sailor_fisher_fishing.aseprite',
}, indent=2) + '\n')
print('Wrote sailor fishing PNG, JSON and editable Aseprite source; planted feet verified.')
