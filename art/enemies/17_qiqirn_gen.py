"""Writes 17_qiqirn.txt: the Qiqirn -- "a huge dog of Inuit folklore",
"hairless except for its mouth, feet, and ear and tail tips".

Bare, wrinkled pink-grey skin with pale fur only on the muzzle, paws, ear tips
and tail tip. The five views are hand-drawn with the pixel plugin in
17_views.aseprite (exported to 17_views.png); front and back are exact mirror
images. This script adds the idle animation: it breathes (the shared
transform), paws planted."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import views_reader, write, source_path
from build_enemy import poses

VW, VH = 40, 32
PAL = {'K': '000000', 'S': 'f0b890', 's': 'd7a175', 'd': '8d6b4f', 'W': 'fcfcfc', 'L': 'c6ccda', 'P': 'ec8476'}
ORDER = ('D', 'DR', 'R', 'UR', 'U')
BREATH_ROW = 14   # mid-chest in every view, clear of the belly outline: rows above it rise / sink

grab = views_reader(os.path.join(os.path.dirname(os.path.abspath(__file__)), '17_views.png'), PAL)
VIEWS = {k: ['.' + r + '.' for r in grab(i * VW, 0, VW, VH)] for i, k in enumerate(ORDER)}   # 1 px margin each side

def main():
    V = {}
    for suffix, n in (('', 0), ('@1', 1), ('@2', 2)):
        V.update({view + suffix: poses(VIEWS[view], BREATH_ROW)[n] for view in ORDER})
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
