"""README.md: centred terminal layout. Panel widths are SOLVED from the rendered
SVG dimensions so both panels display at the same height. With a combined width
of TOTAL, each display width is TOTAL * aspect / (sum of both aspects).
Re-run whenever the card's row count changes (regenerate the card first)."""
import re

import config
from common import ROOT

TOTAL = 850


def size(name):
    head = (ROOT / name).read_text(encoding="utf-8")[:400]
    w, h = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', head).groups()
    return float(w), float(h)


def main():
    (pw, ph), (cw, ch) = size("ascii-portrait.svg"), size("info-card.svg")
    pa, ca = pw / ph, cw / ch
    w_p = round(TOTAL * pa / (pa + ca))
    w_c = TOTAL - w_p
    print(f"portrait aspect {pa:.3f} -> {w_p}px ({w_p / pa:.0f}px tall); "
          f"card aspect {ca:.3f} -> {w_c}px ({w_c / ca:.0f}px tall)")
    readme = f'''<div align="center">

<h3>{config.HANDLE}@github:~$</h3>

<img src="contrib-heatmap.svg" width="{TOTAL}" alt="Contribution heatmap for {config.USERNAME}">

<br>

<table>
<tr>
<td valign="top"><img src="ascii-portrait.svg" width="{w_p}" alt="ASCII portrait"></td>
<td valign="top"><img src="info-card.svg" width="{w_c}" alt="About {config.USERNAME}"></td>
</tr>
</table>

</div>
'''
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print("wrote README.md")


if __name__ == "__main__":
    main()
