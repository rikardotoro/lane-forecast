from pathlib import Path

import pandas as pd
import pytest

from lane_forecast.data import detect_columns, load_shipments
from lane_forecast.errors import InvalidDataError, MissingColumnError


def test_detects_canonical_names():
    cols = ["origin", "destination", "carrier", "departure", "arrival"]
    assert detect_columns(cols)["origin"] == "origin"


def test_detects_common_aliases():
    cols = ["POL", "POD", "Shipping Line", "ATD", "ATA"]
    mapping = detect_columns(cols)
    assert mapping["origin"] == "POL"
    assert mapping["destination"] == "POD"
    assert mapping["carrier"] == "Shipping Line"
    assert mapping["departure"] == "ATD"
    assert mapping["arrival"] == "ATA"


def test_override_beats_detection():
    cols = ["POL", "POD", "carrier", "ATD", "ATA", "gate_out"]
    mapping = detect_columns(cols, overrides={"departure": "gate_out"})
    assert mapping["departure"] == "gate_out"


def test_missing_required_column_names_the_column():
    cols = ["origin", "destination", "carrier"]
    with pytest.raises(MissingColumnError, match="departure"):
        detect_columns(cols)


def test_optional_columns_absent_is_fine():
    cols = ["origin", "destination", "carrier", "departure"]
    mapping = detect_columns(cols)
    assert "arrival" not in mapping


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "s.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_load_returns_canonical_columns(tmp_path):
    path = _write(tmp_path, [
        {"POL": "CNSHA", "POD": "NLRTM", "Shipping Line": "MAEU",
         "ATD": "2026-01-05", "ATA": "2026-01-28"},
    ])
    frame = load_shipments(path)
    assert list(frame.columns[:5]) == ["origin", "destination", "carrier", "departure", "arrival"]
    assert frame.loc[0, "departure"] == pd.Timestamp("2026-01-05")


def test_unparseable_date_names_the_row(tmp_path):
    path = _write(tmp_path, [
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": "not-a-date", "arrival": "2026-01-28"},
    ])
    with pytest.raises(InvalidDataError, match="row 0"):
        load_shipments(path)


def test_arrival_before_departure_is_rejected(tmp_path):
    path = _write(tmp_path, [
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": "2026-02-01", "arrival": "2026-01-28"},
    ])
    with pytest.raises(InvalidDataError, match="row 0"):
        load_shipments(path)
