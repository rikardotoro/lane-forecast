import numpy as np
import pandas as pd

from lane_forecast.diagnostics import (
    carrier_eta_bias,
    is_bimodal,
    peak_season_share,
    transshipment_split,
)


def _frame(rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    for column in ("departure", "arrival", "carrier_eta"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column])
    frame["censored"] = frame.get("arrival", pd.Series(pd.NaT)).isna()
    frame["transit_days"] = (frame["arrival"] - frame["departure"]).dt.days.astype(float)
    return frame


def test_carrier_eta_bias_is_positive_when_late():
    frame = _frame([
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-01", "arrival": "2026-01-25",
         "carrier_eta": "2026-01-21"},
    ])
    assert carrier_eta_bias(frame) == 4.0


def test_carrier_eta_bias_is_none_without_the_column():
    frame = _frame([
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-01", "arrival": "2026-01-25"},
    ])
    assert carrier_eta_bias(frame) is None


def test_transshipment_split_counts_groups():
    frame = _frame([
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-01", "arrival": "2026-01-25", "transshipment": True},
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-02", "arrival": "2026-01-20", "transshipment": False},
    ])
    assert transshipment_split(frame) == {"direct": 1, "transshipment": 1}


def test_unimodal_is_not_flagged():
    rng = np.random.default_rng(3)
    assert not is_bimodal(rng.normal(24.0, 2.0, size=1000))


def test_bimodal_is_flagged():
    rng = np.random.default_rng(3)
    durations = np.concatenate([
        rng.normal(22.0, 1.0, size=500),
        rng.normal(40.0, 1.0, size=500),
    ])
    assert is_bimodal(durations)


def test_peak_season_share_counts_chinese_new_year_departures():
    frame = _frame([
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-01-25", "arrival": "2026-02-20"},
        {"origin": "A", "destination": "B", "carrier": "X",
         "departure": "2026-06-01", "arrival": "2026-06-24"},
    ])
    assert peak_season_share(frame) == 0.5
