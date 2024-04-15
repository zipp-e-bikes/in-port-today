from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import requests

from .constants import WEATHERURL
from .exceptions import WeatherError

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Literal, TypedDict

    # see https://openweathermap.org/weather-conditions#Weather-Condition-Codes-2
    WeatherConditions = Literal[
        "Thunderstorm",
        "Drizzle",
        "Rain",
        "Snow",
        "Mist",
        "Smoke",
        "Haze",
        "Dust",
        "Fog",
        "Sand",
        "Dust",
        "Ash",
        "Squall",
        "Tornado",
        "Clear",
        "Clouds",
    ]
    WeatherIcons = Literal[
        "01d.png",
        "01n.png",
        "02d.png",
        "02n.png",
        "03d.png",
        "03n.png",
        "04d.png",
        "04n.png",
        "09d.png",
        "09n.png",
        "10d.png",
        "10n.png",
        "11d.png",
        "11n.png",
        "13d.png",
        "13n.png",
        "50d.png",
        "50n.png",
    ]

    class Weather(TypedDict):
        low: list[int | None]
        high: list[int | None]
        conditions: list[list[WeatherConditions] | None]
        icons: list[list[WeatherIcons] | None]


def get_weather() -> dict[date, Weather]:
    print(f"Fetching weather from {WEATHERURL}")

    response = requests.get(WEATHERURL)

    # check if the response was successful
    if response.status_code != 200:
        raise WeatherError(f"Failed to retrieve the json: {WEATHERURL}")

    data = response.json()

    if not (snapshots := data.get("list")):
        raise WeatherError(f"Failed to get weather data: {WEATHERURL}")

    utc = ZoneInfo("UTC")
    cst = ZoneInfo("America/Chicago")

    calendar: dict[date, Weather] = {}
    for snapshot in snapshots:
        weatherstamp = datetime.fromtimestamp(snapshot["dt"])  # timestamp in UTC
        utcstamp = weatherstamp.replace(tzinfo=utc)
        cststamp = utcstamp.astimezone(cst)
        date = cststamp.date()

        index = int(cststamp.hour / 3)

        weather = calendar.setdefault(
            date,
            {
                "low": [None] * 8,
                "high": [None] * 8,
                "conditions": [None] * 8,
                "icons": [None] * 8,
            },
        )

        weather.setdefault("low", [])[index] = snapshot["main"]["temp_min"]
        weather.setdefault("high", [])[index] = snapshot["main"]["temp_max"]
        weather.setdefault("conditions", [])[index] = [
            conditions["main"] for conditions in snapshot["weather"]
        ]
        weather.setdefault("icons", [])[index] = [
            conditions["icon"] for conditions in snapshot["weather"]
        ]

    return calendar


def write_weather(year: int, month: int, output: Path) -> None:
    from . import json

    year_month = f"{year}-{month:02}"
    path = output / f"{year_month}.json"

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        weather = json.loads(path.read_text())
    except FileNotFoundError:
        # FileNotFoundError: path doesn't exist yet
        weather = {}

    path.write_text(json.dumps({**weather, **get_weather()}))
    print(f"Wrote weather to {path}")
