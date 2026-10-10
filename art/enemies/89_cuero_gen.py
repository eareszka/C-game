"""Writes 89_cuero.txt: the Cuero (Mapuche and Chilote, the lakes of southern
Chile): a lake monster like a stretched cowhide -- flat, round, hairy-edged,
its rim set with eyes and with sharp hooked claws -- that lies spread on the
water and wraps itself around anyone who swims or wades, dragging them
under. A broad round hide, pale hairy cowhide on top with dark patches,
humped up in the middle, its rim curling and rippling, a ring of staring
eyes along the near edge and hooked claws hanging from the rim, seen from a
little above. Big tier, 8 directions (the round hide looks alike all round,
the eyes follow you), five frames: the rim rippling -- frame 2 the hide
heaving up in the middle, the claws flared out to wrap.

One rough 3D skeleton, pitched to be seen from a little above (pose_view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 89_views.aseprite
(exported to 89_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'W': 'e8e0c0', 'w': 'b2966a', 'b': '785830', 'h': '463422', 'T': 'fcfcfc', 'R': 'b6433d', 'C': '3e91cc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '89_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
