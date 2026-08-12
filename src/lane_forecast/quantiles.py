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
