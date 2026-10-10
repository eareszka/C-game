"""Writes 94_trochus.txt: the Trochus, or Rota (the medieval bestiaries, the
Indian Ocean): a huge wheel-shaped sea creature with a crest and spines
standing up out of the water; they travel in great shoals near shore, and
though timid, a trochus spins, draws itself in, dives deep and comes
rolling back up to the surface. A great upright wheel of a creature: a
round shell-pale body like a coiled shell, a red crest frilled all round
its rim, long bone spines standing out from the rim like spokes, a dark
eye at its hub, half sunk in a ring of churned white water. Big tier, 8
directions (a wheel: seen edge-on from the front, a full circle from the
side), five frames: the wheel turning -- frame 2 spinning hard, its spines
drawn in tight (contracting).

One rough 3D skeleton (pose_view sizes the wheel's face to the view),
turned to each view (enemy_shapes.skeleton); plain lit-edge shading (the
rough-sprite rules).

Each frame is hand-drawn whole with the pixel plugin in 94_views.aseprite
(exported to 94_views.png); this script only lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 96, 64
PAL = {'K': '000000', 'S': 'f0b890', 's': 'd7a175', 'o': '8d6b4f', 'R': 'ec8476', 'r': 'b6433d', 'T': 'e8e0c0', 'C': '3e91cc', 'c': '84a7e9', 'w': 'dcf0ff', 'E': '2850a0'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '94_views.png'), PAL, VW, VH, frames=5)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
