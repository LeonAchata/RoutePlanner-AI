import pytest

from app.formatting import clean_location_name, format_distance, format_duration
from app.graph.nodes.format_output import build_google_maps_url


@pytest.mark.parametrize(
    "minutes, expected",
    [(0, "0 min"), (45, "45 min"), (60, "1h"), (150, "2h 30min"), (59.6, "1h")],
)
def test_format_duration(minutes, expected):
    assert format_duration(minutes) == expected


@pytest.mark.parametrize("km, expected", [(0.35, "350 m"), (1, "1.0 km"), (12.345, "12.3 km")])
def test_format_distance(km, expected):
    assert format_distance(km) == expected


def test_clean_location_name_keeps_casing():
    assert clean_location_name("  McDonald's   Av.  Larco ,") == "McDonald's Av. Larco"


def test_google_maps_url_encodes_waypoints():
    url = build_google_maps_url(["-12.1,-77.0", "-12.2,-77.1", "-12.3,-77.2"], "driving")
    assert url.startswith("https://www.google.com/maps/dir/?api=1")
    assert "waypoints=-12.2%2C-77.1" in url
    assert "travelmode=driving" in url


def test_google_maps_url_skipped_when_too_many_waypoints():
    points = [f"{i},{i}" for i in range(12)]
    assert build_google_maps_url(points, "driving") == ""
