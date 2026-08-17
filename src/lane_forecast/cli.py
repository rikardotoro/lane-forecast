import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from lane_forecast.data import add_transit_days, load_shipments
from lane_forecast.errors import LaneForecastError
from lane_forecast.report import analyse, render, to_dict

app = typer.Typer(add_completion=False, help="Book against the percentile that holds.")
console = Console()

EXAMPLES = Path(__file__).parent / "examples"
DEMO = EXAMPLES / "demo.csv"

@app.command()
def main(
    data: Annotated[Path | None, typer.Option(help="Shipment history CSV.")] = None,
    demo: Annotated[bool, typer.Option(help="Use the bundled example data.")] = False,
    lane: Annotated[str | None, typer.Option(help="ORIGIN-DEST, e.g. CNSHA-NLRTM.")] = None,
    origin: Annotated[str | None, typer.Option()] = None,
    dest: Annotated[str | None, typer.Option()] = None,
    carrier: Annotated[str | None, typer.Option()] = None,
    service_level: Annotated[float, typer.Option(help="Target reliability.")] = 0.8,
    min_shipments: Annotated[int, typer.Option()] = 30,
    map_: Annotated[list[str] | None, typer.Option("--map", help="canonical=column")] = None,
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    path = DEMO if demo else data
    if path is None:
        raise typer.BadParameter("provide --data PATH or --demo")

    if lane:
        origin, _, dest = lane.partition("-")
    if demo and not (origin or dest):
        origin, dest = "CNSHA", "USA"
    if not origin or not dest:
        raise typer.BadParameter("provide --lane ORIGIN-DEST or --origin and --dest")

    overrides = dict(item.split("=", 1) for item in (map_ or []))

    try:
        frame = add_transit_days(load_shipments(path, overrides or None))
        available = (frame["origin"] + "-" + frame["destination"]).str.upper().unique()
        if f"{origin.upper()}-{dest.upper()}" not in available:
            console.print(f"[red]No shipments for {origin}-{dest}.[/red]")
            console.print("Available lanes: " + ", ".join(sorted(available)[:20]))
            raise typer.Exit(code=1)

        analysis = analyse(frame, origin, dest, carrier, service_level, min_shipments)
    except LaneForecastError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    if as_json:
        print(json.dumps(to_dict(analysis), indent=2))
    else:
        render(analysis)

if __name__ == "__main__":
    app()
