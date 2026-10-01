"""LangGraph pipeline: parse -> geocode -> distance_matrix -> optimize -> directions -> format.

Any node can fail. Failures are stored on the state and the graph jumps
straight to END, so later nodes never run on incomplete data.
"""
import logging
from functools import lru_cache, wraps
from typing import Callable

from langgraph.graph import END, START, StateGraph

from app.errors import RouteError
from app.graph.nodes.distance_matrix import distance_matrix_node
from app.graph.nodes.format_output import format_output_node
from app.graph.nodes.geocode import geocode_node
from app.graph.nodes.get_directions import get_directions_node
from app.graph.nodes.optimize_route import optimize_route_node
from app.graph.nodes.parse_input import parse_input_node
from app.models.state import GraphState, TravelMode

logger = logging.getLogger(__name__)

PIPELINE: list[tuple[str, Callable[[GraphState], dict]]] = [
    ("parse", parse_input_node),
    ("geocode", geocode_node),
    ("distance_matrix", distance_matrix_node),
    ("optimize", optimize_route_node),
    ("directions", get_directions_node),
    ("format", format_output_node),
]


def _guarded(name: str, node: Callable[[GraphState], dict]) -> Callable[[GraphState], dict]:
    """Turn exceptions raised inside a node into an error on the state."""

    @wraps(node)
    def run(state: GraphState) -> dict:
        try:
            return node(state)
        except RouteError as exc:
            logger.info("Node %s stopped the route: %s", name, exc.message)
            return {"error": exc.message, "error_status": exc.status_code}
        except Exception:
            logger.exception("Node %s crashed", name)
            return {"error": "Something went wrong while planning the route.", "error_status": 500}

    return run


def _next_or_end(next_node: str) -> Callable[[GraphState], str]:
    def route(state: GraphState) -> str:
        return END if state.error else next_node

    return route


def build_workflow() -> StateGraph:
    graph = StateGraph(GraphState)
    for name, node in PIPELINE:
        graph.add_node(name, _guarded(name, node))

    graph.add_edge(START, PIPELINE[0][0])
    for (current, _), (following, _) in zip(PIPELINE, PIPELINE[1:]):
        graph.add_conditional_edges(current, _next_or_end(following), [following, END])
    graph.add_edge(PIPELINE[-1][0], END)
    return graph


@lru_cache
def compiled_workflow():
    return build_workflow().compile()


def run_workflow(user_input: str, travel_mode: TravelMode = "driving") -> GraphState:
    initial = GraphState(user_input=user_input, travel_mode=travel_mode)
    result = compiled_workflow().invoke(initial)
    return GraphState.model_validate(result)
