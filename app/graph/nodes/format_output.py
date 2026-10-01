"""Node 6: totals and a shareable Google Maps link."""
from urllib.parse import urlencode

from app.models.state import GraphState

# Google Maps URLs accept at most 9 waypoints. Past that Google silently drops
# stops, so it is better to return no link than a wrong one.
MAX_URL_WAYPOINTS = 9


def build_google_maps_url(points: list[str], travel_mode: str) -> str:
    if len(points) < 2 or len(points) - 2 > MAX_URL_WAYPOINTS:
        return ""
    params = {
        "api": "1",
        "origin": points[0],
        "destination": points[-1],
        "travelmode": travel_mode,
    }
    waypoints = points[1:-1]
    if waypoints:
        params["waypoints"] = "|".join(waypoints)
    return "https://www.google.com/maps/dir/?" + urlencode(params)


def format_output_node(state: GraphState) -> dict:
    stops = [state.locations[i] for i in state.optimized_order]
    # Coordinates are unambiguous; place names like "Surco" are not.
    points = [f"{s.lat},{s.lng}" for s in stops]

    return {
        "total_distance_km": round(sum(s.distance_km for s in state.route_steps), 2),
        "total_duration_min": sum(s.duration_min for s in state.route_steps),
        "google_maps_url": build_google_maps_url(points, state.travel_mode),
    }
