"""Check exact sleeping-art edits against approved walking sheets."""
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
review = Image.new('RGBA', (56, 80))
for i, name in enumerate(('girl', 'fisher', 'sailor', 'woodcutter')):
    reference = Image.open(root / f'assets/npcs/{name}.png').convert('RGBA')
    sheet = Image.open(root / f'assets/npcs/{name}_sleep_simple.png').convert('RGBA')
    assert sheet.size == (56, 20)
    assert set(sheet.get_flattened_data()) <= set(reference.get_flattened_data())
    review.paste(sheet, (0, i*20))
    for side in range(2):
        eye = 5 if side == 0 else 9
        skin = reference.getpixel((4 if side == 0 else 10, 49+side*20))
        a = sheet.crop((side*28, 0, side*28+14, 20))
        b = sheet.crop((side*28+14, 0, side*28+28, 20))
        assert a.tobytes() != b.tobytes()
        allowed = {(eye,10), (eye,11), (4 if side == 0 else 10,12)}
        original = reference.crop((0,40+side*20,14,60+side*20))
        changed = {(x,y) for y in range(20) for x in range(14)
                   if a.getpixel((x,y)) != original.getpixel((x,y))}
        assert changed == allowed
        for frame in (a,b):
            assert frame.getpixel((eye,10)) == frame.getpixel((eye,11)) == skin
            assert frame.crop((0,0,14,14)).tobytes() == a.crop((0,0,14,14)).tobytes()
            assert frame.crop((0,16,14,20)).tobytes() == a.crop((0,16,14,20)).tobytes()
    print(f'{name}: hidden eyes, two frames per side, original palette, fixed head/feet verified')
review.resize((560,800),Image.Resampling.NEAREST).save(root/'build_tmp/npc_review/sleep_simple_review.png')
