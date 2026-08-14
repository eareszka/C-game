"""Highlight pixels that differ between two same-sized renders, in red, on a
dimmed copy of the first image. Quick visual diff for A/B testing a
generation change against a fixed seed and window.

    python tools/diff_pair.py a.png b.png out.png
"""
import sys
import numpy as np
from PIL import Image

a = np.array(Image.open(sys.argv[1]).convert('RGB')).astype(np.int32)
b = np.array(Image.open(sys.argv[2]).convert('RGB')).astype(np.int32)
diff = np.any(a != b, axis=2)
print('changed pixels:', int(diff.sum()), '/', diff.size, '(%.2f%%)' % (100 * diff.sum() / diff.size))

base = (a * 0.5).astype(np.uint8)
out = base.copy()
out[diff] = [255, 0, 0]
Image.fromarray(out).save(sys.argv[3])
print('wrote', sys.argv[3])
