from collections.abc import Sequence

import numpy as np

from lane_forecast.errors import InsufficientDataError

DEFAULT_LEVELS: tuple[float, ...] = (0.10, 0.50, 0.80, 0.90)


def empirical_quantiles(
    durations: np.ndarray,
    levels: Sequence[float] = DEFAULT_LEVELS,
    min_observations: int = 30,
) -> dict[float, float]:
    durations = np.asarray(durations, dtype=float)
    durations = durations[~np.isnan(durations)]
    if durations.size < min_observations:
        raise InsufficientDataError(
            f"{durations.size} completed shipments is below the minimum of "
            f"{min_observations}; the estimate would not be trustworthy. "
            f"Lower it with --min-shipments if you accept that."
        )
    return {level: float(np.quantile(durations, level)) for level in levels}


def km_survival(
    durations: np.ndarray, observed: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    durations = np.asarray(durations, dtype=float)
    observed = np.asarray(observed, dtype=bool)

    event_times = np.unique(durations[observed])
    survival = np.empty(event_times.size, dtype=float)
    running = 1.0

    for index, time in enumerate(event_times):
        at_risk = int(np.count_nonzero(durations >= time))
        events = int(np.count_nonzero((durations == time) & observed))
        if at_risk > 0:
            running *= 1.0 - events / at_risk
        survival[index] = running

    return event_times, survival


def km_quantiles(
    durations: np.ndarray,
    observed: np.ndarray,
    levels: Sequence[float] = DEFAULT_LEVELS,
    min_observations: int = 30,
) -> dict[float, float | None]:
    durations = np.asarray(durations, dtype=float)
    observed = np.asarray(observed, dtype=bool)

    if durations.size < min_observations:
        raise InsufficientDataError(
            f"{durations.size} shipments is below the minimum of {min_observations}."
        )

    times, survival = km_survival(durations, observed)
    result: dict[float, float | None] = {}

    for level in levels:
        target = 1.0 - level
        reached = np.nonzero(survival <= target)[0]
        result[level] = float(times[reached[0]]) if reached.size else None

    return result
