"""Node 5: real per-leg distances, times and the polyline for the chosen order."""
import logging

from app.errors import RouteError
from app.models.state import GraphState, RouteStep
from app.services.google_maps import GoogleMapsService

logger = logging.getLogger(__name__)


def get_directions_node(state: GraphState) -> dict:
    stops = [state.locations[i] for i in state.optimized_order]

    route = None
    try:
        route = GoogleMapsService().directions(stops, mode=state.travel_mode)
    except RouteError as exc:
        # Directions only adds detail; the matrix already has what we need.
        logger.warning("Directions failed, using matrix values: %s", exc.message)

    legs = route["legs"] if route else []
    steps = []
    for k, (a, b) in enumerate(zip(state.optimized_order, state.optimized_order[1:])):
        if len(legs) == len(stops) - 1:
            distance_km = legs[k]["distance"]["value"] / 1000.0
            duration_min = legs[k]["duration"]["value"] / 60.0
        else:
            distance_km = state.distance_matrix[a][b]
            duration_min = state.duration_matrix[a][b]
        steps.append(
            RouteStep(
                from_location=state.locations[a].name,
                to_location=state.locations[b].name,
                distance_km=round(distance_km, 2),
                duration_min=round(duration_min),
            )
        )

    polyline = route.get("overview_polyline", {}).get("points") if route else None
    return {"route_steps": steps, "route_polyline": polyline}
