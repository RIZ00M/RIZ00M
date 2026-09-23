"""ascii-portrait.svg: monochrome ASCII art that types itself in row by row, then freezes.

MODE=logo  (default) colour-keys a flat background. Right for emblems/logos.
MODE=photo uses rembg for the cut-out and head-width framing. Right for faces.
"""
import os
import re
import sys

import cv2
import numpy as np
from PIL import Image

import config
from common import (BAR_H, INK, ROOT, STATIC, close_svg, f, open_svg, text, write, esc)

MODE = os.environ.get("MODE", "logo")

# POLARITY: panel is dark, ink is light, so the ramp runs dark -> bright.
# A black pixel picks the space (vanishes into the panel); bright picks '@'.
RAMP = " .`:-=+*csS#%@"

COLS = int(os.environ.get("COLS", 88))
CW, CH = 6.0, 11.5            # glyph cell (px): terminal cells are ~1:2, so rows < cols
PAD = 16
ROW_DELAY, ROW_DUR = 0.07, 0.35   # stagger between rows / time to type one row

# Levels curve (black point, white point, gamma). Photos crush harder so
# clothing falls to pure black; logos are already high-contrast.
LEVELS = dict(logo=(25, 215, 0.9), photo=(70, 225, 1.1))[MODE]


# ---------------------------------------------------------------- cut-out
def cutout(im):
    """Return (rgb float32 HxWx3, alpha float32 HxW in 0..1)."""
    rgb = np.asarray(im.convert("RGB")).astype(np.float32)
    if MODE == "photo":
        from rembg import remove                      # only needed for photos
        alpha = np.asarray(remove(im.convert("RGB")))[..., 3].astype(np.float32) / 255
        return rgb, alpha
    h, w = rgb.shape[:2]
    corners = np.concatenate([rgb[:12, :12].reshape(-1, 3), rgb[:12, -12:].reshape(-1, 3),
                              rgb[-12:, :12].reshape(-1, 3), rgb[-12:, -12:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    dist = np.linalg.norm(rgb - bg, axis=2)
    return rgb, np.clip((dist - 25) / 40, 0, 1)


# ---------------------------------------------------------------- framing
def frame_box(alpha):
    """Crop box (x0, y0, x1, y1) measured from the ALPHA SILHOUETTE only.

    Never from the graded image: dark hair carries almost no brightness, so
    hunting for bright pixels crops the top of the head off.
    """
    mask = alpha > 0.5
    ys, xs = np.where(mask)
    top, bottom, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    H, W = alpha.shape

    if MODE == "photo":
        # Head width = MEDIAN row width over the upper ~60% of the silhouette.
        # The maximum would catch a shoulder and leave the face adrift.
        upper = range(top, top + int((bottom - top) * 0.6))
        widths = [np.count_nonzero(mask[r]) for r in upper if mask[r].any()]
        head_w = float(np.median(widths))
        cx = np.mean([xs[ys == r].mean() for r in upper if mask[r].any()])
        crop_w = head_w * 2.3
        y0 = top - 0.08 * crop_w
        crop_h = crop_w * 1.1                          # slightly taller than wide
        x0, x1, y1 = cx - crop_w / 2, cx + crop_w / 2, y0 + crop_h
    else:
        pad = 0.04 * max(right - left, bottom - top)
        x0, x1, y0, y1 = left - pad, right + pad, top - pad, bottom + pad

    return (int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1)))


# ---------------------------------------------------------------- grading
def grade(rgb_u8, alpha):
    gray = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2GRAY)
    # CLAHE: a flatly-lit subject otherwise converts to one undifferentiated blob.
    gray = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    lo, hi, gamma = LEVELS
    g = np.clip((gray.astype(np.float32) - lo) / (hi - lo), 0, 1) ** gamma
    return g * alpha                                   # background -> pure black


def to_rows(gray01):
    idx = np.rint(gray01 * (len(RAMP) - 1)).astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


# ---------------------------------------------------------------- svg
def build(rows):
    n, cols = len(rows), len(rows[0])
    W = cols * CW + 2 * PAD
    H = BAR_H + 2 * PAD + n * CH
    gw = cols * CW
    defs, body = [], []
    for i, row in enumerate(rows):
        # WHITESPACE: renderers collapse space runs inside <text>, so the row
        # wobbles. Emit no spaces: each run of non-space glyphs gets its own
        # absolute x and a textLength, so alignment holds in any monospace face.
        runs = [m for m in re.finditer(r"\S+", row)]
        if not runs:
            continue
        top = BAR_H + PAD + i * CH
        base = top + CH * 0.8
        glyphs = "".join(
            f'<text x="{f(PAD + m.start() * CW)}" y="{f(base)}" '
            f'textLength="{f(len(m.group()) * CW)}" lengthAdjust="spacingAndGlyphs">'
            f'{esc(m.group())}</text>' for m in runs)
        if STATIC:
            body.append(glyphs)
        else:
            b = i * ROW_DELAY
            defs.append(
                f'<clipPath id="r{i}"><rect x="{f(PAD)}" y="{f(top)}" width="0" height="{f(CH)}">'
                f'<animate attributeName="width" from="0" to="{f(gw)}" begin="{f(b)}s" '
                f'dur="{f(ROW_DUR)}s" fill="freeze"/></rect></clipPath>')
            body.append(f'<g clip-path="url(#r{i})">{glyphs}</g>')

    head = open_svg(W, H, f"{config.HANDLE}@github: ~/portrait", "ASCII portrait")
    style = f'<g font-size="{f(CH * 0.9)}" fill="{INK}">'         # ONE colour, on purpose
    return (head + f"<defs>{''.join(defs)}</defs>" + style + "".join(body) + "</g>" + close_svg())


def main():
    src = ROOT / config.PORTRAIT_SRC
    im = Image.open(src)
    rgb, alpha = cutout(im)
    x0, y0, x1, y1 = frame_box(alpha)
    rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    ar = (y1 - y0) / (x1 - x0)
    rows_n = max(1, round(COLS * ar * CW / CH))
    S = 4                                              # grade at 4x, then area-average down
    big = (COLS * S, rows_n * S)
    rgb_b = cv2.resize(rgb.astype(np.uint8), big, interpolation=cv2.INTER_AREA)
    a_b = cv2.resize(alpha, big, interpolation=cv2.INTER_AREA)
    g = cv2.resize(grade(rgb_b, a_b), (COLS, rows_n), interpolation=cv2.INTER_AREA)
    rows = to_rows(g)
    if os.environ.get("SHOW"):
        print("\n".join(rows))
    write("ascii-portrait.svg", build(rows))
    print(f"grid {COLS}x{rows_n}, crop {x1 - x0}x{y1 - y0}px from silhouette, mode={MODE}")


if __name__ == "__main__":
    main()
