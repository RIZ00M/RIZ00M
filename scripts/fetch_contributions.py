"""Read the public contribution calendar: no token, no third-party service.

Day cells are <td data-date data-level id=...>. The exact count is NOT on the
cell; it lives in a separate <tool-tip for="<cell id>">, so we join by id.
Levels are 0-4. Writes data/contributions.json, and refuses to overwrite it
with an empty result if GitHub changes its markup.
"""
import json
import re
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

import config
from common import ROOT

URL = f"https://github.com/users/{config.USERNAME}/contributions"
OUT = ROOT / "data" / "contributions.json"


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    tips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.find_all("td", attrs={"data-date": True}):
        tip = tips.get(td.get("id"), "")
        m = re.match(r"(\d[\d,]*)\s+contribution", tip)      # "No contributions on ..." -> 0
        days.append({"date": td["data-date"],
                     "level": int(td.get("data-level", 0)),
                     "count": int(m.group(1).replace(",", "")) if m else 0})
    days.sort(key=lambda d: d["date"])
    return days


def main():
    r = requests.get(URL, headers={"User-Agent": "profile-readme-heatmap/1.0"}, timeout=30)
    r.raise_for_status()
    days = parse(r.text)
    if len(days) < 300:                       # a full calendar is ~365-371 cells
        sys.exit(f"only parsed {len(days)} day cells from {URL}; markup may have changed. "
                 "Leaving existing data untouched.")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"user": config.USERNAME, "sample": False,
                               "fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "days": days}, indent=1))
    print(f"{len(days)} days, {sum(d['count'] for d in days)} contributions -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
