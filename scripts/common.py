"""Shared panel chrome, colours and animation helpers for every generator.

Design rule: each SVG carries its OWN dark terminal background. An SVG loaded
through <img> cannot see GitHub's light/dark theme, so a transparent SVG with
light ink would vanish for half of all visitors.
"""
import os
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
STATIC = os.environ.get("STATIC") == "1"        # frozen frame for previewing
OUT_DIR = (ROOT / "preview") if STATIC else ROOT
OUT_DIR.mkdir(exist_ok=True)

BG, BORDER, TITLEBAR = "#0d1117", "#21262d", "#161b22"
INK, MUTED, ACCENT, GREEN = "#e6edf3", "#8b949e", "#58a6ff", "#3fb950"
DOTS = ("#ff5f56", "#ffbd2e", "#27c93f")
BAR_H = 32
# Faces that ship with operating systems; no webfonts, nothing remote.
FONT = ('ui-monospace, SFMono-Regular, Menlo, Consolas, "DejaVu Sans Mono", '
        '"Liberation Mono", "Courier New", monospace')
MONO_W = 0.6                                     # advance width / font-size


def esc(s):
    return escape(str(s))


def f(n):
    """Compact number formatting."""
    return f"{n:.2f}".rstrip("0").rstrip(".")


def text(x, y, s, size, fill=INK, weight=None):
    """A <text> whose width is pinned with textLength so it can't overflow."""
    w = len(s) * size * MONO_W
    wt = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{f(x)}" y="{f(y)}" font-size="{f(size)}" fill="{fill}"{wt} '
            f'textLength="{f(w)}" lengthAdjust="spacingAndGlyphs">{esc(s)}</text>')


def fade(inner, begin, dur=0.5):
    """Wrap markup so it fades in (SMIL). In STATIC mode it is simply visible."""
    if STATIC:
        return f"<g>{inner}</g>"
    return (f'<g opacity="0">{inner}<animate attributeName="opacity" from="0" to="1" '
            f'begin="{f(begin)}s" dur="{f(dur)}s" fill="freeze"/></g>')


def open_svg(w, h, title, label):
    dots = "".join(f'<circle cx="{18 + 14 * i}" cy="{BAR_H // 2 + 1}" r="4.5" fill="{c}"/>'
                   for i, c in enumerate(DOTS))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" '
        f'width="{f(w)}" height="{f(h)}" role="img" aria-label="{esc(label)}">'
        f'<title>{esc(label)}</title>'
        f'<style>text{{font-family:{FONT};white-space:pre}}</style>'
        f'<rect id="panel" x="0.5" y="0.5" width="{f(w - 1)}" height="{f(h - 1)}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<rect x="1" y="1" width="{f(w - 2)}" height="{BAR_H}" rx="7" fill="{TITLEBAR}"/>'
        f'<rect x="1" y="{BAR_H - 6}" width="{f(w - 2)}" height="7" fill="{TITLEBAR}"/>'
        f'<rect x="1" y="{BAR_H + 1}" width="{f(w - 2)}" height="1" fill="{BORDER}"/>'
        f'{dots}{text(64, BAR_H // 2 + 5, title, 12, MUTED)}'
    )


def close_svg():
    return "</svg>\n"


def write(name, svg):
    path = OUT_DIR / name
    path.write_text(svg, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}  ({len(svg) / 1024:.1f} KB)"
          + ("  [STATIC preview]" if STATIC else ""))
    return path
