from dataclasses import asdict, dataclass

import pandas as pd
from rich.console import Console
from rich.table import Table

from lane_forecast import diagnostics
from lane_forecast.data import filter_lane
from lane_forecast.quantiles import DEFAULT_LEVELS, empirical_quantiles, km_quantiles


@dataclass
class Analysis:
    origin: str
    destination: str
    carrier: str | None
    n_total: int
    n_censored: int
    naive: dict[float, float]
    corrected: dict[float, float | None]
    service_level: float
    carrier_bias: float | None
    split: dict[str, int] | None
    bimodal: bool
    peak_share: float


def analyse(
    frame: pd.DataFrame,
    origin: str,
    destination: str,
    carrier: str | None,
    service_level: float,
    min_shipments: int,
) -> Analysis:
    lane = filter_lane(frame, origin, destination, carrier)
    completed = lane[~lane["censored"]]
    levels = tuple(sorted(set(DEFAULT_LEVELS) | {service_level}))

    return Analysis(
        origin=origin.upper(),
        destination=destination.upper(),
        carrier=carrier,
        n_total=len(lane),
        n_censored=int(lane["censored"].sum()),
        naive=empirical_quantiles(
            completed["transit_days"].to_numpy(), levels, min_shipments
        ),
        corrected=km_quantiles(
            lane["transit_days"].to_numpy(),
            (~lane["censored"]).to_numpy(),
            levels,
            min_shipments,
        ),
        service_level=service_level,
        carrier_bias=diagnostics.carrier_eta_bias(lane),
        split=diagnostics.transshipment_split(lane),
        bimodal=diagnostics.is_bimodal(completed["transit_days"].to_numpy()),
        peak_share=diagnostics.peak_season_share(lane),
    )


def to_dict(analysis: Analysis) -> dict:
    payload = asdict(analysis)
    payload["naive"] = {str(k): v for k, v in analysis.naive.items()}
    payload["corrected"] = {str(k): v for k, v in analysis.corrected.items()}
    return payload


def render(analysis: Analysis) -> None:
    console = Console()
    lane = f"{analysis.origin} to {analysis.destination}"
    if analysis.carrier:
        lane += f" via {analysis.carrier}"

    table = Table(title=f"Transit days — {lane}")
    table.add_column("Percentile")
    table.add_column("Completed only", justify="right")
    table.add_column("Including in-transit", justify="right")

    for level in sorted(analysis.naive):
        corrected = analysis.corrected.get(level)
        table.add_row(
            f"P{int(level * 100)}",
            f"{analysis.naive[level]:.1f}",
            "—" if corrected is None else f"{corrected:.1f}",
        )

    console.print(table)

    target = analysis.corrected.get(analysis.service_level)
    if target is not None:
        console.print(
            f"\n[bold]Plan for day {target:.0f}[/bold] to be right "
            f"{analysis.service_level:.0%} of the time."
        )

    console.print(
        f"\n{analysis.n_total} shipments, of which {analysis.n_censored} still in transit."
    )
    if analysis.carrier_bias is not None:
        console.print(f"Carrier ETA runs {analysis.carrier_bias:+.1f} days optimistic.")
    if analysis.split:
        console.print(
            f"Split: {analysis.split['direct']} direct, "
            f"{analysis.split['transshipment']} transshipment "
            "— consider analysing these separately."
        )
    if analysis.bimodal:
        console.print(
            "[yellow]Two clusters detected[/yellow] — likely rolled cargo. "
            "A single percentile hides this."
        )
    if analysis.peak_share > 0:
        console.print(
            f"{analysis.peak_share:.0%} of departures fall in a peak-season window."
        )
