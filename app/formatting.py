"""Small helpers for turning numbers into human readable strings."""


def format_duration(minutes: int) -> str:
    """45 -> "45 min", 150 -> "2h 30min", 120 -> "2h"."""
    minutes = max(0, int(round(minutes)))
    if minutes < 60:
        return f"{minutes} min"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h" if mins == 0 else f"{hours}h {mins}min"


def format_distance(km: float) -> str:
    """0.35 -> "350 m", 12.345 -> "12.3 km"."""
    if km < 1:
        return f"{int(round(km * 1000))} m"
    return f"{km:.1f} km"


def clean_location_name(name: str) -> str:
    """Collapse whitespace and strip stray punctuation around a place name.

    Casing is left alone on purpose: title-casing breaks names such as
    "McDonald's" or "Av. 28 de Julio".
    """
    return " ".join(name.split()).strip(" ,.;")
