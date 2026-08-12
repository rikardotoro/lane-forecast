from lane_forecast import __version__
from lane_forecast.errors import LaneForecastError, MissingColumnError


def test_version_is_exposed():
    assert __version__ == "0.1.0"


def test_missing_column_error_is_a_lane_forecast_error():
    assert issubclass(MissingColumnError, LaneForecastError)
