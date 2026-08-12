from pathlib import Path

from lane_forecast.data import add_transit_days, load_shipments

DEMO = Path(__file__).parent.parent / "examples" / "demo.csv"


def test_demo_file_is_small():
    assert DEMO.stat().st_size < 1_000_000


def test_demo_file_loads_and_has_censored_rows():
    frame = add_transit_days(load_shipments(DEMO))
    assert len(frame) > 100
    assert frame["censored"].any(), "demo data must exercise the censoring path"
    assert not frame["censored"].all()
