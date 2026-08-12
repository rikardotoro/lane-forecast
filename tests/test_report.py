import pandas as pd

from lane_forecast.data import add_transit_days
from lane_forecast.report import analyse, to_dict


def _frame(n_arrived: int, n_flight: int) -> pd.DataFrame:
    rows = []
    for index in range(n_arrived):
        rows.append({
            "origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
            "departure": pd.Timestamp("2026-01-01") + pd.Timedelta(days=index),
            "arrival": pd.Timestamp("2026-01-24") + pd.Timedelta(days=index),
        })
    for index in range(n_flight):
        rows.append({
            "origin": "CNSHA", "destination": "NLRTM", "carrier": "MAEU",
            "departure": pd.Timestamp("2026-03-01") + pd.Timedelta(days=index),
            "arrival": pd.NaT,
        })
    return add_transit_days(pd.DataFrame(rows), as_of=pd.Timestamp("2026-04-01"))


def test_analysis_counts_censored_rows():
    analysis = analyse(_frame(40, 10), "CNSHA", "NLRTM", None, 0.8, 30)
    assert analysis.n_total == 50
    assert analysis.n_censored == 10


def test_to_dict_is_json_serialisable():
    import json

    analysis = analyse(_frame(40, 10), "CNSHA", "NLRTM", None, 0.8, 30)
    json.dumps(to_dict(analysis))  # must not raise
