"""SYNTHETIC calendar for offline testing only. Never a substitute for the real fetch."""
import json
import random
from datetime import date, timedelta

from common import ROOT

random.seed(7)
end = date.today()
days = []
for i in range(364, -1, -1):
    d = end - timedelta(days=i)
    busy = 0.15 if d.weekday() >= 5 else 0.7
    n = random.choice([0, 0, 1, 2, 3, 5, 8, 12]) if random.random() < busy else 0
    lvl = 0 if n == 0 else 1 if n <= 2 else 2 if n <= 4 else 3 if n <= 8 else 4
    days.append({"date": d.isoformat(), "level": lvl, "count": n})
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "contributions.json").write_text(
    json.dumps({"user": "SAMPLE", "sample": True, "days": days}, indent=1))
print("wrote SYNTHETIC data/contributions.json")
