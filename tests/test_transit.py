import pandas as pd
import pytest

from lane_forecast.data import add_transit_days, filter_lane


def _frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in ("departure", "arrival"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    return frame


def test_completed_shipment_transit_days():
    frame = add_transit_days(_frame([
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": "2026-01-01", "arrival": "2026-01-24"},
    ]))
    assert frame.loc[0, "transit_days"] == 23.0
    assert not frame.loc[0, "censored"]


def test_in_flight_shipment_is_censored_at_as_of():
    frame = add_transit_days(
        _frame([
            {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
             "departure": "2026-01-01", "arrival": None},
        ]),
        as_of=pd.Timestamp("2026-01-15"),
    )
    assert frame.loc[0, "transit_days"] == 14.0
    assert frame.loc[0, "censored"]


def test_as_of_defaults_to_latest_date_in_data():
    frame = add_transit_days(_frame([
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-01", "arrival": "2026-01-20"},
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-10", "arrival": None},
    ]))
    assert frame.loc[1, "transit_days"] == 10.0
    assert frame.loc[1, "censored"]


def test_missing_arrival_column_means_all_censored():
    frame = add_transit_days(
        _frame([{"origin": "A", "destination": "B", "carrier": "X",
                 "departure": "2026-01-01"}]),
        as_of=pd.Timestamp("2026-01-11"),
    )
    assert frame["censored"].all()


def test_filter_lane_selects_origin_and_destination():
    frame = _frame([
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": "2026-01-01", "arrival": "2026-01-24"},
        {"origin": "CNSHA", "destination": "DEHAM", "carrier": "MAEU",
         "departure": "2026-01-01", "arrival": "2026-01-26"},
    ])
    assert len(filter_lane(frame, "CNSHA", "NLRTM")) == 1


def test_filter_lane_is_case_insensitive():
    frame = _frame([
        {"origin": "cnsha", "destination": "nlrtm", "carrier": "MAEU",
         "departure": "2026-01-01", "arrival": "2026-01-24"},
    ])
    assert len(filter_lane(frame, "CNSHA", "NLRTM")) == 1


def test_filter_lane_with_carrier():
    frame = _frame([
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
         "departure": "2026-01-01", "arrival": "2026-01-24"},
        {"origin": "CNSHA", "destination": "NLRTM", "carrier": "MSCU",
         "departure": "2026-01-01", "arrival": "2026-01-30"},
    ])
    assert len(filter_lane(frame, "CNSHA", "NLRTM", carrier="MSCU")) == 1
