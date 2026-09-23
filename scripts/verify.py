"""Assert every SVG is valid, self-contained, and geometrically inside its panel."""
import re
import sys
import xml.etree.ElementTree as ET

from common import BAR_H, ROOT, MONO_W

NAMES = ["ascii-portrait.svg", "info-card.svg", "contrib-heatmap.svg"]
SVG = "{http://www.w3.org/2000/svg}"
problems = []


def bad(name, msg):
    problems.append(f"{name}: {msg}")


def num(el, attr, default=0.0):
    v = el.get(attr)
    return float(v) if v not in (None, "") else default


def check(path):
    name = str(path.relative_to(ROOT))
    raw = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return bad(name, f"invalid XML: {e}")

    # ---- self-contained
    if re.search(r"<script", raw, re.I):
        bad(name, "contains <script>")
    if re.search(r"@import|<foreignObject|<image|<use|<iframe", raw, re.I):
        bad(name, "contains @import / foreignObject / image / use / iframe")
    for el in root.iter():
        for k, v in el.attrib.items():
            if k.startswith("on"):
                bad(name, f"event handler attribute {k}")
            if re.search(r"https?://", v):
                bad(name, f"external reference in {k}={v[:60]}")
            if "href" in k and not v.startswith("#"):
                bad(name, f"non-local href {v[:60]}")
    for m in re.finditer(r"url\(([^)]*)\)", raw):
        if not m.group(1).startswith("#"):
            bad(name, f"non-local url({m.group(1)})")
    if re.search(r"https?://", raw.replace("http://www.w3.org/2000/svg", "")):
        bad(name, "http(s) URL present in markup")

    # ---- geometry
    vb = [float(x) for x in root.get("viewBox").split()]
    W, H = vb[2], vb[3]
    if (num(root, "width"), num(root, "height")) != (W, H):
        bad(name, "width/height differ from viewBox")
    panel = next(e for e in root.iter(SVG + "rect") if e.get("id") == "panel")
    px0, py0 = num(panel, "x"), num(panel, "y")
    px1, py1 = px0 + num(panel, "width"), py0 + num(panel, "height")
    tol = 0.01
    counts = {"text": 0, "rect": 0, "circle": 0}

    def inside(x0, y0, x1, y1, what):
        if x0 < px0 - tol or y0 < py0 - tol or x1 > px1 + tol or y1 > py1 + tol:
            bad(name, f"{what} escapes panel: ({x0:.1f},{y0:.1f})-({x1:.1f},{y1:.1f}) "
                      f"vs panel ({px0},{py0})-({px1:.1f},{py1:.1f})")

    def walk(el, fs):
        tag = el.tag.replace(SVG, "")
        fs = num(el, "font-size", fs)
        if tag in ("title", "style"):
            return
        if tag == "text":
            counts["text"] += 1
            s = "".join(el.itertext())
            x, y = num(el, "x"), num(el, "y")
            w = num(el, "textLength", len(s) * fs * MONO_W)
            if "textLength" not in el.attrib:
                bad(name, f"text without textLength: {s[:20]!r}")
            inside(x, y - 0.8 * fs, x + w, y + 0.25 * fs, f"text {s[:24]!r}")
            return
        if tag == "rect" and el.get("id") != "panel":
            counts["rect"] += 1
            x, y, w, h = (num(el, a) for a in ("x", "y", "width", "height"))
            anim = el.find(SVG + "animate")                      # clip reveals grow to a final width
            if anim is not None and anim.get("attributeName") == "width":
                w = max(w, float(anim.get("to")))
            inside(x, y, x + w, y + h, "rect")
        elif tag == "circle":
            counts["circle"] += 1
            cx, cy, r = num(el, "cx"), num(el, "cy"), num(el, "r")
            inside(cx - r, cy - r, cx + r, cy + r, "circle")
        for c in el:
            walk(c, fs)

    walk(root, 12)
    if name.endswith("ascii-portrait.svg"):            # glyph rows only; the title bar is chrome
        rows = [t for t in root.iter(SVG + "text") if num(t, "y") > BAR_H + 1]
        if not rows:
            bad(name, "no glyph rows found")
        if any(" " in "".join(t.itertext()) for t in rows):
            bad(name, "portrait glyph <text> contains a space (whitespace-collapse wobble)")
    print(f"ok  {name:34s} {W:g}x{H:g}  text={counts['text']} rect={counts['rect']} circle={counts['circle']}")


def main():
    paths = [ROOT / n for n in NAMES] + [ROOT / "preview" / n for n in NAMES]
    for p in paths:
        if p.exists():
            check(p)
    readme = (ROOT / "README.md").read_text()
    if "style=" in readme:
        bad("README.md", "inline style (GitHub strips it)")
    if re.search(r"<h[12]", readme):
        bad("README.md", "h1/h2 draws a full-width rule; use h3")
    wf = (ROOT / ".github/workflows/heatmap.yml").read_text()
    for needle in ("contents: write", "[skip ci]", "pip install requests beautifulsoup4"):
        if needle not in wf:
            bad("heatmap.yml", f"missing {needle!r}")
    if problems:
        print("\nFAILED:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print("\nall checks passed")


if __name__ == "__main__":
    main()
