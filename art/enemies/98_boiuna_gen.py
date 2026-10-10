"""Writes 98_boiuna.txt: the Boiuna (the Amazon): a gigantic black snake said to
reach two hundred metres, with widely spaced eyes that glow like
searchlights, lower canines jutting up like horns and a dizzying stench;
it hides in holes under the rivers, leaves a huge V-shaped wake, traps
boats with a magnetic pull and steals people's shadows. A colossal black
serpent rearing its head and forebody out of the river, a broad flat head
with two glowing searchlight eyes set far apart, two lower fangs jutting up
past its snout like horns, its loops breaking the water behind, a great V
of white wake spreading out behind it, seen from a little above. Giant
tier, 8 directions, eight frames: swaying, the loops rolling -- frames 3-4
the head reared back, jaws gaping, the eyes blazing.

One rough 3D skeleton, the river seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 98_views.aseprite
(exported to 98_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 128, 80
PAL = {'K': '000000', 'B': '235436', 'b': '142e1f', 'k': '0e2016', 'C': '3e91cc', 'c': '84a7e9', 'w': 'dcf0ff', 'Y': 'fae488', 'T': 'e8e0c0', 'm': '531b1c', 'P': '29633e'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '98_views.png'), PAL, VW, VH, frames=8)
    write(source_path(__file__), PAL, '#POSE\nframes\n#ROWS\n1\n', V)

if __name__ == '__main__':
    main()
