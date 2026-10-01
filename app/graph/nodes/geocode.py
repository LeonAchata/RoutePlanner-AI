"""Node 2: resolve every place name to coordinates."""
from concurrent.futures import ThreadPoolExecutor

from app.errors import RouteError
from app.models.state import GraphState
from app.services.google_maps import GoogleMapsService

MAX_PARALLEL_REQUESTS = 5


def geocode_node(state: GraphState) -> dict:
    service = GoogleMapsService()
    names = [state.origin] + state.destinations

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as pool:
        locations = list(pool.map(service.geocode, names))

    # Two names that land on the same point (e.g. "Lima" and "Cercado de Lima")
    # would produce a zero-length leg and confuse the user.
    seen: dict[tuple[float, float], str] = {}
    for loc in locations:
        key = (round(loc.lat, 5), round(loc.lng, 5))
        if key in seen:
            raise RouteError(
                f'"{seen[key]}" and "{loc.name}" point to the same place on the map. '
                "Add more detail to one of them."
            )
        seen[key] = loc.name

    return {"locations": locations}
