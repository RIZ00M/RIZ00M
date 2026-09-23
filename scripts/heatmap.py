"""contrib-heatmap.svg: the real 53-week calendar, revealing diagonally,
with a Less->More legend and a stats footer."""
import json
from datetime import date, timedelta

from common import (BAR_H, BORDER, ROOT, INK, MUTED, MONO_W, close_svg, f, fade, open_svg,
                    STATIC, text, write)
import config

W = 850
PAD_L, PAD_R = 52, 24
COLS = 53
STEP = (W - PAD_L - PAD_R) / COLS
CELL = STEP - 3
LEVEL_FILL = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
DIAG = 0.03                   # seconds per (week + weekday) step
CELL_DUR = 0.3


def dow(d):                   # Sunday = 0, as on GitHub's calendar
    return (d.weekday() + 1) % 7


def days_str(n):
    return f"{n} day" if n == 1 else f"{n} days"


def stats(days):
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    cur, seq = 0, list(reversed(days))
    if seq and seq[0]["count"] == 0:       # today may simply not have happened yet
        seq = seq[1:]
    for d in seq:
        if d["count"] == 0:
            break
        cur += 1
    return total, longest, cur, best


def build(days):
    dates = [date.fromisoformat(d["date"]) for d in days]
    start = dates[0] - timedelta(days=dow(dates[0]))          # Sunday of the first week
    top = BAR_H + 1 + 14
    grid_y = top + 18
    body, last_begin = [], 0.0

    # month labels: first column where a month appears, skipping ones that would crowd
    seen, last_col = None, -9
    for d, dt in zip(days, dates):
        col = (dt - start).days // 7
        if dt.month != seen and dt.day <= 7 and col - last_col >= 3:
            body.append(text(PAD_L + col * STEP, top + 8, dt.strftime("%b"), 11, MUTED))
            last_col = col
        seen = dt.month
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(text(10, grid_y + row * STEP + CELL - 2, label, 11, MUTED))

    # cells: diagonal reveal from the top-left
    for d, dt in zip(days, dates):
        col, row = (dt - start).days // 7, dow(dt)
        rect = (f'<rect x="{f(PAD_L + col * STEP)}" y="{f(grid_y + row * STEP)}" '
                f'width="{f(CELL)}" height="{f(CELL)}" rx="2" fill="{LEVEL_FILL[d["level"]]}"')
        if STATIC:
            body.append(rect + "/>")
        else:
            b = (col + row) * DIAG
            last_begin = max(last_begin, b)
            body.append(rect + f' opacity="0"><animate attributeName="opacity" from="0" to="1" '
                        f'begin="{f(b)}s" dur="{CELL_DUR}s" fill="freeze"/></rect>')

    # legend, right-aligned to the grid's right edge
    ly = grid_y + 7 * STEP + 10
    lw = 4 * 11 * MONO_W
    sq = 5 * 11 + 4 * 3
    lx = W - PAD_R - (lw + 6 + sq + 6 + lw)
    legend = text(lx, ly + 9, "Less", 11, MUTED)
    legend += "".join(f'<rect x="{f(lx + lw + 6 + i * 14)}" y="{f(ly)}" width="11" height="11" '
                      f'rx="2" fill="{c}"/>' for i, c in enumerate(LEVEL_FILL))
    legend += text(lx + lw + 6 + sq + 6, ly + 9, "More", 11, MUTED)
    end = last_begin + CELL_DUR
    body.append(fade(legend, end))

    # stats footer
    total, longest, cur, best = stats(days)
    fy = ly + 11 + 16
    body.append(f'<rect x="{PAD_L}" y="{f(fy)}" width="{f(W - PAD_L - PAD_R)}" height="1" fill="{BORDER}"/>')
    col_w = (W - PAD_L - PAD_R) / 4
    cells = [(f"{total:,}", "contributions, last year"),
             (days_str(longest), "longest streak"),
             (days_str(cur), "current streak"),
             (f"{best['count']}", f"busiest day, {date.fromisoformat(best['date']).strftime('%b %-d')}")]
    foot = "".join(text(PAD_L + i * col_w, fy + 26, v, 15, INK, 700) +
                   text(PAD_L + i * col_w, fy + 43, lab, 11, MUTED)
                   for i, (v, lab) in enumerate(cells))
    body.append(fade(foot, end + 0.2))

    H = fy + 43 + 16
    return open_svg(W, H, f"{config.HANDLE}@github: ~/contributions", "Contribution heatmap") \
        + "".join(body) + close_svg()


def main():
    data = json.loads((ROOT / "data" / "contributions.json").read_text())
    if data.get("sample"):
        print("WARNING: rendering SYNTHETIC sample data, not your real contributions")
    write("contrib-heatmap.svg", build(data["days"]))


if __name__ == "__main__":
    main()
