"""Node 4: choose the visiting order that minimises total travel time."""
from app.models.state import GraphState
from app.services import tsp_solver


def optimize_route_node(state: GraphState) -> dict:
    # Optimise on time rather than distance: a slightly longer route on an
    # avenue usually beats a shorter one through congested streets.
    order, _ = tsp_solver.solve(state.duration_matrix, return_to_start=state.return_to_origin)
    return {"optimized_order": order}
