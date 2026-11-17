"""Where the goods' colours stand, read from screenshots (KGi-DISS-I046, gate G11).

The rule of the interface: a good's colour is drawn at full strength on white or on the good's own
tint, where it keeps 3:1 against the ground. Triangle's orange has 3.2:1 on white, so a slightly
darker ground (a grey panel, a stronger tint) already breaks the rule.

For every pixel in a good's exact colour, this finds the flat light colour that surrounds it (the
ground it stands on) and prints, per ground, how many screenshots and pixels it was found on and
the contrast of the good's colour against it. Exit status 1 if a ground gives less than --min.
A mark drawn fainter than its colour (an opacity below 1) has no pixel in the exact colour and is
not seen here: the style test (analysis/tests/test_market_ui_I046.py) forbids that.

    python tools/browser_run.py --shots DIR          # screenshots first (server must be up)
    python tools/mark_contrast.py DIR [--min 3.0]

Needs numpy and Pillow (not part of the server's runtime).
"""
import argparse
import collections
import glob
import os
import sys

import numpy as np
from PIL import Image

GOODS = dict(Square=(0x2a, 0x78, 0xd6), Triangle=(0xeb, 0x68, 0x34))
REACH = 6           # px around a pixel in which its ground is looked for (screenshots at 2x: 12)


def _lin(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    return 0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1]) + 0.0722 * _lin(rgb[2])


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _box(mask, r):
    """number of set pixels in the (2r+1)-square around every pixel"""
    c = np.pad(mask.astype(np.int32), ((r + 1, r), (r + 1, r))).cumsum(0).cumsum(1)
    n = 2 * r + 1
    return c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]


def grounds(path, reach=REACH):
    """{good: {ground colour: number of the good's pixels standing on it}} for one screenshot"""
    im = np.asarray(Image.open(path).convert('RGB')).astype(np.uint32)
    code = (im[..., 0] << 16) | (im[..., 1] << 8) | im[..., 2]
    values, counts = np.unique(code, return_counts=True)
    floor = max(400, int(0.0004 * code.size))
    flat = [(int(v), int(n)) for v, n in zip(values, counts) if n >= floor]
    flat = [v for v, _ in flat if luminance(((v >> 16) & 255, (v >> 8) & 255, v & 255)) >= 0.80]   # light surfaces only
    out = {}
    for good, rgb in GOODS.items():
        mark = code == ((rgb[0] << 16) | (rgb[1] << 8) | rgb[2])
        if not mark.any() or not flat:
            continue
        rows, cols = np.flatnonzero(mark.any(1)), np.flatnonzero(mark.any(0))           # work inside the marks' bounding box
        y0, y1 = max(0, rows[0] - reach), min(code.shape[0], rows[-1] + reach + 1)
        x0, x1 = max(0, cols[0] - reach), min(code.shape[1], cols[-1] + reach + 1)
        part, mark = code[y0:y1, x0:x1], mark[y0:y1, x0:x1]
        near = np.stack([_box(part == v, reach)[mark] for v in flat])        # candidates x marked pixels
        best, most = near.argmax(0), near.max(0)
        tally = collections.Counter(flat[int(i)] for i, m in zip(best, most) if m >= 4)   # inside a shape: no ground in reach
        out[good] = {((v >> 16) & 255, (v >> 8) & 255, v & 255): n for v, n in tally.items()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('shots', help='directory of screenshots written by browser_run.py --shots')
    ap.add_argument('--min', type=float, default=3.0, help='least contrast a good\'s colour may have against its ground')
    ap.add_argument('--least', type=int, default=30, help='pixels of a good on a ground, in one screenshot, below which it is ignored')
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.shots, '*.png')))
    if not files:
        sys.exit(f'no screenshots in {a.shots}')
    found = collections.defaultdict(lambda: dict(files=set(), pixels=0))
    for f in files:
        width = Image.open(f).width
        reach = REACH * (2 if width in (780, 750, 640) else 1)      # the phone sessions are photographed at 2x
        for good, by_ground in grounds(f, reach).items():
            for ground, n in by_ground.items():
                if n >= a.least:
                    found[(good, ground)]['files'].add(os.path.basename(f))
                    found[(good, ground)]['pixels'] += n
    bad = 0
    print(f'{len(files)} screenshots; a good\'s colour against each ground it stands on (least allowed {a.min}):')
    for (good, ground), v in sorted(found.items(), key=lambda x: (x[0][0], -x[1]['pixels'])):
        c = contrast(GOODS[good], ground)
        low = c < a.min
        bad += low
        eg = sorted(v['files'])[0]
        print(f"  {good:<8} on #{ground[0]:02x}{ground[1]:02x}{ground[2]:02x}  {c:5.2f}:1  {len(v['files']):>3} screenshots  {v['pixels']:>8} px  "
              f"{'BELOW  e.g. ' + eg if low else ''}")
    print('MARK CONTRAST', 'FAIL' if bad else 'PASS')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
