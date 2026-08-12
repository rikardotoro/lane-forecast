import numpy as np
import pytest

from lane_forecast.errors import InsufficientDataError
from lane_forecast.quantiles import DEFAULT_LEVELS, empirical_quantiles


def test_quantiles_of_a_known_sequence():
    durations = np.arange(1, 101, dtype=float)  # 1..100
    result = empirical_quantiles(durations, levels=(0.5,))
    assert result[0.5] == pytest.approx(50.5)


def test_default_levels_are_returned():
    durations = np.arange(1, 101, dtype=float)
    assert set(empirical_quantiles(durations)) == set(DEFAULT_LEVELS)


def test_p80_is_at_least_p50():
    rng = np.random.default_rng(42)
    durations = rng.gamma(shape=8.0, scale=3.0, size=500)
    result = empirical_quantiles(durations)
    assert result[0.80] >= result[0.50]


def test_too_few_observations_raises():
    with pytest.raises(InsufficientDataError, match="30"):
        empirical_quantiles(np.arange(1, 10, dtype=float))


def test_min_observations_can_be_lowered():
    result = empirical_quantiles(np.arange(1, 10, dtype=float), min_observations=5)
    assert result[0.50] == pytest.approx(5.0)
