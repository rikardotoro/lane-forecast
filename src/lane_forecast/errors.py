class LaneForecastError(Exception):
    """Base class for all lane-forecast errors."""


class MissingColumnError(LaneForecastError):
    """A required column could not be found or mapped."""


class InvalidDataError(LaneForecastError):
    """A row or value failed validation."""


class InsufficientDataError(LaneForecastError):
    """Not enough usable observations to estimate."""
