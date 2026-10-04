"""Writes 42_nykur.txt: the Nykur of Iceland -- the water horse, a fine
dapple-grey horse waiting by lakes and the sea, tempting people to ride it,
then galloping into the water and drowning them; it gives itself away by its
hooves, which face backwards.

A dapple-grey horse (pale rings dappling it), its mane and long tail dark,
wet and tangled with green waterweed, cold pale eyes, and slate hooves
turned backwards, their toes pointing to the rear. Medium tier: three
frames, each one hand-drawn whole with the pixel plugin in 42_views.aseprite
(exported to 42_views.png): row 0 at rest, row 1 it tosses its head, the
mane swinging out, row 2 it lowers its head, beckoning a rider. Laid out as
one 3D skeleton turned to each view (enemy_shapes.skeleton); legs, body, neck
and head are one seamless shape (a skeleton group), outlined only round the
outside and where one part stands clearly in front of another; the legs
come out from under the body (drawn behind it where they overlap), and from
behind the tail hangs over the hind legs. This script only
lays them out for the build."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
from enemy_shapes import drawn_frames, write, source_path

VW, VH = 56, 50
PAL = {'K': '000000', 'G': 'a8acb0', 'g': '70747c', 'L': 'd0d4d8', 'M': '3c4448', 'm': '242c30',
       'V': '4c7c4c', 'k': '2c2c30', 'E': '9cf0f0', 'N': '5c6068'}

def main():
    V = drawn_frames(os.path.join(os.path.dirname(os.path.abspath(__file__)), '42_views.png'), PAL, VW, VH)
    write(source_path(__file__), PAL, '#POSE\nframes\n', V)

if __name__ == '__main__':
    main()
