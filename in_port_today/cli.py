from datetime import date
from pathlib import Path

import click
from dateutil.relativedelta import relativedelta

from . import __version__
from .constants import TODAY


@click.group()
@click.version_option(__version__)
@click.help_option("-h", "--help")
def main() -> None:
    pass


@main.command()
@click.option("--output", default="data/cruises", type=Path)
@click.option("--year", default=TODAY.year, type=int)
@click.option("--month", default=TODAY.month, type=str)
@click.version_option(__version__)
@click.help_option("-h", "--help")
def cruises(output: Path, year: int, month: str) -> None:
    from .cruises import write_schedule

    if ".." in month:
        # 0..2 -> current, next, following
        start, stop = month.split("..")
        for increment in range(int(start), int(stop) + 1):
            today = date(year, TODAY.month, 1) + relativedelta(months=increment)
            write_schedule(today.year, today.month, output)
    elif month.startswith(("+", "-")):
        # +1 -> next
        # -1 -> prior
        today = date(year, TODAY.month, 1) + relativedelta(months=int(month))
        write_schedule(today.year, today.month, output)
    else:
        # 1 -> January
        write_schedule(year, int(month), output)


@main.command()
@click.option("--output", default="data/weather", type=Path)
@click.version_option(__version__)
@click.help_option("-h", "--help")
def weather(output: Path) -> None:
    from .weather import write_weather

    write_weather(TODAY.year, TODAY.month, output)


if __name__ == "__main__":
    main()
