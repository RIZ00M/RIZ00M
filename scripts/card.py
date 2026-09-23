"""info-card.svg: a neofetch-style panel, lines fading in on a stagger.
Deliberately contains NO GitHub statistics; the heatmap covers those."""
import sys

import config
from common import (ACCENT, BAR_H, BORDER, DOTS, GREEN, INK, MUTED, MONO_W, close_svg,
                    fade, f, open_svg, text, write)

W = 420
PAD = 20
FS = 13
LINE = 24
KEY_CHARS = 9
VAL_X = PAD + (KEY_CHARS + 1) * FS * MONO_W
MAX_VAL = int((W - PAD - VAL_X) // (FS * MONO_W))       # longest value that still fits


def build():
    for k, v in config.CARD:
        if len(v) > MAX_VAL:
            sys.exit(f"card value too long ({len(v)} > {MAX_VAL}): {v!r}")
        if len(k) > KEY_CHARS:
            sys.exit(f"card key too long ({len(k)} > {KEY_CHARS}): {k!r}")

    items, t = [], 0.3                                   # (markup, begin)
    y = BAR_H + 32

    items.append((text(PAD, y, "$ neofetch", FS, MUTED), t)); t += 0.35
    y += LINE + 4
    user = f"{config.HANDLE}@github"
    items.append((text(PAD, y, user, FS + 1, GREEN, 700), t)); t += 0.2
    y += 10
    items.append((f'<rect x="{PAD}" y="{f(y)}" width="{f(len(user) * (FS + 1) * MONO_W)}" '
                  f'height="1" fill="{BORDER}"/>', t)); t += 0.2
    y += LINE - 4

    for k, v in config.CARD:
        markup = (text(PAD, y, k, FS, ACCENT, 700) if k else "") + text(VAL_X, y, v, FS, INK)
        items.append((markup, t)); t += 0.22
        y += LINE

    y += 6
    sw = "".join(f'<rect x="{f(PAD + i * 26)}" y="{f(y)}" width="22" height="10" rx="2" fill="{c}"/>'
                 for i, c in enumerate(["#484f58", "#f85149", "#3fb950", "#d29922",
                                        "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]))
    items.append((sw, t))
    H = y + 10 + PAD

    body = "".join(fade(m, b) for m, b in items)
    return open_svg(W, H, f"{config.HANDLE}@github: ~/about", "About card") + body + close_svg()


if __name__ == "__main__":
    write("info-card.svg", build())
