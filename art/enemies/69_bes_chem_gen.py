"""Writes 69_bes_chem.txt: the Bes Chem -- "bird spirit" of the Malaysian
jungle, which lives on big branches that touch one another and scatters
whoever passes beneath with tiny poisonous feathers that leave them thin
forever. Drawn after the user's reference.

A towering bird that is nearly all body: a great egg of brown feathers
mottled with dark dashes, a folded wing at each side, no neck; a bare pink
head leaning out over its front with two huge glowing yellow eyes and a long
drooping pink nose; and in its front a huge gaping mouth, dark purple inside,
ringed with long white fangs. Thin pink bird's legs on clawed bird's feet, a
short stubby tail angled down. Hunched over, creepily: the body bent forward
from the hips into a humped back, the head hanging low out in front. The eyes
and the mouth are fixed flat shapes laid where they sit, the same from every
side -- the claw feet too, three toes and three dark hooked claws each -- the mouth cut into the chest, never past the body's outline, ringed
with a dark feathered lip. Medium tier: three frames, each one
hand-drawn whole with the pixel plugin in 69_views.aseprite (exported to
69_views.png): row 0 at rest, row 1 the mouth gapes wide, fangs bared, the
body swelling, row 2 it eases shut. Laid out as one 3D skeleton turned to
each view (enemy_shapes.skeleton). This script only lays them out for the
build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 46, 52
PAL = {'K': '000000', 'F': '815423', 'f': '583518', 'L': 'c18a39', 'P': 'f0b890', 'p': 'd7a175',
       'E': 'f0e880', 'e': 'f0bc3c', 'M': '5e486a', 'm': '361f42', 'W': 'fcfcfc'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '69_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
