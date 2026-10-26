"""The organ pipe cactus, desert scenery: a cluster of stems from one root.

    python art/structures/props/desert/organ_pipe_design.py

32x32, two cells square. Laid out after a PixelLab draft
(pixellab-out/desert-organpipe/sprites/v3): the tallest stem behind in the
middle, shorter ones before it to either side, the shortest in front. Each
stem is a limb of its own (tools/prop_paint.py columns), parted from the one
behind by the black line, in the trees' greens.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'tools'))
from prop_paint import columns, save

STEMS = [            # x0, x1, top -- back to front
    (14, 18, 2),
    (10, 13, 7), (20, 23, 5),
    (5, 8, 13), (25, 28, 11),
    (11, 14, 17), (18, 21, 19),
]

if __name__ == '__main__':
    save(columns(32, 32, STEMS), os.path.join(HERE, 'organ_pipe.png'), 'foliage')
