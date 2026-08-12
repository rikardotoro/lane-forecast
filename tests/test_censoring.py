import numpy as np
import pytest

from lane_forecast.quantiles import empirical_quantiles, km_quantiles, km_survival


def test_survival_starts_at_one_and_decreases():
    durations = np.array([10.0, 12.0, 14.0, 16.0])
    observed = np.array([True, True, True, True])
    times, survival = km_survival(durations, observed)
    assert survival[0] < 1.0
    assert np.all(np.diff(survival) <= 0)
    assert times[0] == 10.0


def test_with_no_censoring_km_matches_empirical():
    rng = np.random.default_rng(7)
    durations = rng.gamma(shape=8.0, scale=3.0, size=400)
    observed = np.ones(durations.size, dtype=bool)
    km = km_quantiles(durations, observed, levels=(0.5,))
    emp = empirical_quantiles(durations, levels=(0.5,))
    assert km[0.5] == pytest.approx(emp[0.5], rel=0.05)


def test_censored_rows_push_p80_above_the_naive_estimate():
    """The core claim: dropping in-flight shipments makes you look faster."""
    rng = np.random.default_rng(11)
    arrived = rng.gamma(shape=8.0, scale=2.5, size=200)
    # 60 shipments still at sea, already past the arrived median
    in_flight = np.full(60, float(np.median(arrived)) + 5.0)

    durations = np.concatenate([arrived, in_flight])
    observed = np.concatenate([
        np.ones(arrived.size, dtype=bool),
        np.zeros(in_flight.size, dtype=bool),
    ])

    naive = empirical_quantiles(arrived, levels=(0.8,))[0.8]
    corrected = km_quantiles(durations, observed, levels=(0.8,))[0.8]

    assert corrected > naive


def test_all_censored_refuses_to_estimate():
    durations = np.full(50, 10.0)
    observed = np.zeros(50, dtype=bool)
    result = km_quantiles(durations, observed, levels=(0.5,))
    assert result[0.5] is None


def test_unreachable_quantile_returns_none():
    # Everything censored beyond the last arrival: the curve never reaches 0.2
    durations = np.concatenate([np.full(10, 5.0), np.full(90, 40.0)])
    observed = np.concatenate([np.ones(10, dtype=bool), np.zeros(90, dtype=bool)])
    assert km_quantiles(durations, observed, levels=(0.8,), min_observations=10)[0.8] is None
