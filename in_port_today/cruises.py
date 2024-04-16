from __future__ import annotations

from datetime import datetime, time
from typing import TYPE_CHECKING
from warnings import warn

import requests
from bs4 import BeautifulSoup

from .constants import CRUISEURL, USERAGENT
from .exceptions import CruiseScheduleError

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path
    from typing import TypedDict

    from bs4 import element

    class Ship(TypedDict):
        line: str
        ship: str
        arrival: str | None
        departure: str | None

    Schedule = dict[date, list[Ship]]


def parse_date(text: str) -> date:
    return datetime.strptime(text, "%d %B, %Y").date()


def parse_time(text: str) -> time:
    return time.fromisoformat(text)


def get_schedule(year_month: str) -> Schedule:
    url = CRUISEURL % year_month

    print(f"Fetching cruise schedule from {url}")

    response = requests.get(url, headers={"User-Agent": USERAGENT}, timeout=10)

    # Check if the request was successful
    if response.status_code != requests.codes.ok:
        raise CruiseScheduleError(f"Failed to retrieve the webpage: {url}")

    soup = BeautifulSoup(response.text, "html.parser")

    if not (dom := soup.select("table.portItemSchedule")):
        raise CruiseScheduleError(
            f"Failed to find schedule (table) within webpage: {url}"
        )
    if len(dom) != 1:
        raise CruiseScheduleError(f"Got multiple schedules within webpage: {url}")

    if not (dom := dom[0].select("tbody")):
        raise CruiseScheduleError(
            f"Failed to find schedule (tbody) within webpage: {url}"
        )
    table = dom[0]

    return _parse_schedule(table)


# <tr><td>DATE</td><td>SHIP</td><td>ARRIVAL</td><td>DEPARTURE</td></tr>
_NUM_TABLE_ROW_CELLS = 4
# <td><span>DATE</span><span>WEEKDAY</span></td>
_NUM_DATE_CELL_SPANS = 2
# <td><img><a></td>
_NUM_SHIP_CELL_IMGS = 1


def _parse_schedule(table: element.Tag) -> Schedule:
    schedule: Schedule = {}
    rows = table.select("tr")
    for row in rows:
        cells = row.select("td")

        if len(cells) != _NUM_TABLE_ROW_CELLS:
            warn(f"Unexpected number ({len(cells)}) of cells, skipping", stacklevel=1)
            continue

        if len(dom := cells[0].select("span")) != _NUM_DATE_CELL_SPANS:
            warn(f"Unexpected date format ({cells[0]}), skipping", stacklevel=1)
            continue
        date = parse_date(dom[0].text)

        if len(dom := cells[1].select("img")) != _NUM_SHIP_CELL_IMGS:
            warn(f"Unexpected cruise line format ({cells[1]}), skipping", stacklevel=1)
            continue
        line = dom[0].attrs["title"].removesuffix(" cruise line")

        ship = cells[1].text

        try:
            arrival = parse_time(cells[2].text).strftime("%H:%M")
        except ValueError:
            arrival = None

        try:
            departure = parse_time(cells[3].text).strftime("%H:%M")
        except ValueError:
            departure = None

        schedule.setdefault(date, []).append(
            {
                "line": line,
                "ship": ship,
                "arrival": arrival,
                "departure": departure,
            }
        )

    return schedule


def write_schedule(year: int, month: int, output: Path) -> None:
    from . import json

    year_month = f"{year}-{month:02}"
    path = output / f"{year_month}.json"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(get_schedule(year_month)) + "\n")
    print(f"Wrote cruise schedule to {path}")
