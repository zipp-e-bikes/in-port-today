from __future__ import annotations

from datetime import datetime
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


def get_weather() -> dict[str, dict[str, Weather]]:
    print(f"Fetching weather from {WEATHERURL}")

    response = requests.get(WEATHERURL, timeout=10)

    # check if the response was successful
    if response.status_code != requests.codes.ok:
        raise WeatherError(f"Failed to retrieve the json: {WEATHERURL}")

    data = response.json()

    if not (snapshots := data.get("list")):
        raise WeatherError(f"Failed to get weather data: {WEATHERURL}")

    utc = ZoneInfo("UTC")
    cst = ZoneInfo("America/Chicago")

    calendar: dict[str, dict[str, Weather]] = {}
    for snapshot in snapshots:
        weatherstamp = datetime.fromtimestamp(snapshot["dt"])  # timestamp in UTC
        utcstamp = weatherstamp.replace(tzinfo=utc)
        cststamp = utcstamp.astimezone(cst)
        date = cststamp.date().isoformat()

        index = int(cststamp.hour / 3)

        weather = calendar.setdefault(
            cststamp.date().isoformat()[:7],
            {},
        ).setdefault(
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


def deepupdate(
    original: dict[str, Weather],
    update: dict[str, Weather],
) -> dict[str, Weather]:
    for date, weather in update.items():
        if date not in original:
            original[date] = weather
            continue

        for key, value in weather.items():
            original[date][key] = [
                update_value or original_value
                for update_value, original_value in zip(
                    value,
                    original[date][key],
                    strict=True,
                )
            ]

    return original


def write_weather(output: Path) -> None:
    from . import json

    for year_month, new_weather in get_weather().items():
        path = output / f"{year_month}.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            weather = json.loads(path.read_text())
        except FileNotFoundError:
            # FileNotFoundError: path doesn't exist yet
            weather = {}

        path.write_text(json.dumps(deepupdate(weather, new_weather)) + "\n")
        print(f"Wrote weather to {path}")
