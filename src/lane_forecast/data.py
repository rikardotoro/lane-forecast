import re
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from lane_forecast.errors import InvalidDataError, MissingColumnError

CANONICAL: dict[str, bool] = {
    "origin": True,
    "destination": True,
    "carrier": True,
    "departure": True,
    "arrival": False,
    "transshipment": False,
    "carrier_eta": False,
}

ALIASES: dict[str, tuple[str, ...]] = {
    "origin": ("origin", "originport", "pol", "portofloading", "from", "source"),
    "destination": ("destination", "destinationport", "pod", "portofdischarge", "to"),
    "carrier": ("carrier", "carriername", "shippingline", "line", "scac"),
    "departure": ("departure", "departuredate", "atd", "actualdeparture",
                  "shippeddate", "shippingdate", "orderdate"),
    "arrival": ("arrival", "arrivaldate", "ata", "actualarrival",
                "delivereddate", "deliverydate"),
    "transshipment": ("transshipment", "transhipment", "istransshipment", "ts"),
    "carrier_eta": ("carriereta", "eta", "estimatedarrival", "promiseddate",
                    "scheduleddelivery", "estimateddeliverydate"),
}

DATE_COLUMNS = ("departure", "arrival", "carrier_eta")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def detect_columns(
    columns: Sequence[str], overrides: dict[str, str] | None = None
) -> dict[str, str]:
    overrides = overrides or {}
    lookup = {_norm(c): c for c in columns}
    mapping: dict[str, str] = {}

    for canonical, required in CANONICAL.items():
        if canonical in overrides:
            source = overrides[canonical]
            if source not in columns:
                raise MissingColumnError(
                    f"--map {canonical}={source}: column {source!r} is not in the file"
                )
            mapping[canonical] = source
            continue

        for alias in ALIASES[canonical]:
            if alias in lookup:
                mapping[canonical] = lookup[alias]
                break
        else:
            if required:
                raise MissingColumnError(
                    f"required column {canonical!r} not found; "
                    f"tried {', '.join(ALIASES[canonical])}. "
                    f"Use --map {canonical}=<your column> to set it explicitly."
                )
    return mapping


def load_shipments(
    path: Path, overrides: dict[str, str] | None = None
) -> pd.DataFrame:
    raw = pd.read_csv(path)
    mapping = detect_columns(list(raw.columns), overrides)
    frame = raw[list(mapping.values())].copy()
    frame.columns = list(mapping.keys())

    for column in DATE_COLUMNS:
        if column not in frame.columns:
            continue
        parsed = pd.to_datetime(frame[column], errors="coerce")
        was_present = frame[column].notna()
        broke = was_present & parsed.isna()
        if broke.any():
            row = int(broke.idxmax())
            raise InvalidDataError(
                f"row {row}: could not parse {column} value {frame.loc[row, column]!r}"
            )
        frame[column] = parsed

    if "arrival" in frame.columns:
        backwards = frame["arrival"].notna() & (frame["arrival"] < frame["departure"])
        if backwards.any():
            row = int(backwards.idxmax())
            raise InvalidDataError(f"row {row}: arrival is before departure")

    ordered = [c for c in CANONICAL if c in frame.columns]
    return frame[ordered]
