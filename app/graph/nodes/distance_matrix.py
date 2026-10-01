"""Node 3: travel distance and time between every pair of stops."""
from app.errors import RouteError
from app.models.state import GraphState
from app.services.google_maps import GoogleMapsService


def distance_matrix_node(state: GraphState) -> dict:
    distances, durations = GoogleMapsService().distance_matrix(state.locations, mode=state.travel_mode)

    # Every stop has to be reachable from every other one, otherwise the
    # optimiser could pick an impossible order.
    for i, row in enumerate(distances):
        for j, value in enumerate(row):
            if i != j and value is None:
                a, b = state.locations[i].name, state.locations[j].name
                raise RouteError(f'There is no {state.travel_mode} route between "{a}" and "{b}".')

    return {"distance_matrix": distances, "duration_matrix": durations}
