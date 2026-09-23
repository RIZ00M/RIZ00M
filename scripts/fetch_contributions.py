import json
import os
import sys
from datetime import date, timedelta

import requests

import config
from common import ROOT

OUT = ROOT / "data" / "contributions.json"

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
          }
        }
      }
    }
  }
}
"""

LEVELS = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}


def main():
    token = os.environ.get("GH_TOKEN")

    if not token:
        sys.exit("GH_TOKEN is missing")

    today = date.today()
    start = today - timedelta(days=365)

    variables = {
        "login": config.USERNAME,
        "from": f"{start}T00:00:00Z",
        "to": f"{today + timedelta(days=1)}T00:00:00Z",
    }

    response = requests.post(
        "https://api.github.com/graphql",
        json={
            "query": QUERY,
            "variables": variables,
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
        timeout=30,
    )

    response.raise_for_status()
    result = response.json()

    if "errors" in result:
        sys.exit(f"GitHub GraphQL error: {result['errors']}")

    user = result["data"]["user"]

    if user is None:
        sys.exit(f"GitHub user not found: {config.USERNAME}")

    calendar = user["contributionsCollection"]["contributionCalendar"]

    days = []

    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            days.append({
                "date": day["date"],
                "level": LEVELS[day["contributionLevel"]],
                "count": day["contributionCount"],
            })

    days.sort(key=lambda d: d["date"])

    if not days:
        sys.exit("GitHub returned no contribution days.")

    OUT.parent.mkdir(exist_ok=True)

    OUT.write_text(
        json.dumps(
            {
                "user": config.USERNAME,
                "sample": False,
                "fetched": date.today().isoformat(),
                "days": days,
            },
            indent=1,
        )
    )

    print(
        f"{len(days)} days, "
        f"{calendar['totalContributions']} contributions -> "
        f"{OUT.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
