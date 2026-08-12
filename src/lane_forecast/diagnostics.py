import numpy as np
import pandas as pd

# (start month, start day, end month, end day) — approximate, calendar-independent
PEAK_WINDOWS: tuple[tuple[int, int, int, int], ...] = (
    (1, 15, 2, 20),   # Chinese New Year shutdown and the rush before it
    (9, 28, 10, 8),   # Golden Week
)


def carrier_eta_bias(frame: pd.DataFrame) -> float | None:
    if "carrier_eta" not in frame.columns:
        return None
    completed = frame[~frame["censored"]]
    if completed.empty:
        return None
    promised = (completed["carrier_eta"] - completed["departure"]).dt.days
    return float((completed["transit_days"] - promised).mean())


def transshipment_split(frame: pd.DataFrame) -> dict[str, int] | None:
    if "transshipment" not in frame.columns:
        return None
    flags = frame["transshipment"].astype(bool)
    return {
        "direct": int((~flags).sum()),
        "transshipment": int(flags.sum()),
    }


def is_bimodal(
    durations: np.ndarray, bins: int = 20, trough_ratio: float = 0.6
) -> bool:
    durations = np.asarray(durations, dtype=float)
    durations = durations[~np.isnan(durations)]
    if durations.size < 2:
        return False

    counts, _ = np.histogram(durations, bins=bins)
    first = int(np.argmax(counts))

    best_second, best_trough = -1, 0
    for candidate in range(counts.size):
        if abs(candidate - first) < 2:
            continue
        low, high = sorted((first, candidate))
        trough = int(counts[low + 1:high].min())
        if counts[candidate] > best_second:
            best_second, best_trough = int(counts[candidate]), trough

    if best_second <= 0:
        return False
    smaller_peak = min(int(counts[first]), best_second)
    return best_trough < trough_ratio * smaller_peak


def peak_season_share(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    departures = frame["departure"]
    inside = pd.Series(False, index=frame.index)
    for start_month, start_day, end_month, end_day in PEAK_WINDOWS:
        after_start = (departures.dt.month > start_month) | (
            (departures.dt.month == start_month) & (departures.dt.day >= start_day)
        )
        before_end = (departures.dt.month < end_month) | (
            (departures.dt.month == end_month) & (departures.dt.day <= end_day)
        )
        inside |= after_start & before_end
    return float(inside.mean())
