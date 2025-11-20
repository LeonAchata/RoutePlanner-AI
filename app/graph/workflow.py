"""
Definición del grafo de LangGraph para el agente de rutas
"""
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from app.models.state import GraphState
from app.graph.nodes.parse_input import parse_input_node
from app.graph.nodes.geocode import geocode_node
from app.graph.nodes.distance_matrix import distance_matrix_node
from app.graph.nodes.optimize_route import optimize_route_node
from app.graph.nodes.get_directions import get_directions_node
from app.graph.nodes.format_output import format_output_node


def _has_error(state: GraphState) -> bool:
	return bool(state.error)


def build_workflow() -> StateGraph:
	graph = StateGraph(GraphState)

	# Registrar nodos
	graph.add_node("parse", parse_input_node)
	graph.add_node("geocode", geocode_node)
	graph.add_node("distance_matrix", distance_matrix_node)
	graph.add_node("optimize", optimize_route_node)
	graph.add_node("directions", get_directions_node)
	graph.add_node("format", format_output_node)

	# Flujo principal
	graph.add_edge(START, "parse")
	graph.add_edge("parse", "geocode")
	graph.add_edge("geocode", "distance_matrix")
	graph.add_edge("distance_matrix", "optimize")
	graph.add_edge("optimize", "directions")
	graph.add_edge("directions", "format")
	graph.add_edge("format", END)

	# Compilar
	return graph


def run_workflow(user_input: str) -> GraphState:
	"""
	Helper síncrono para ejecutar el grafo completo y devolver el estado final
	"""
	state = GraphState(user_input=user_input)
	graph = build_workflow().compile()
	final_state: GraphState = graph.invoke(state)
	return final_state
