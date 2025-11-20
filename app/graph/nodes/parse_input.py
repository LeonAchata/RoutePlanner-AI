"""
Nodo 1: Parseo del input del usuario con LLM
"""
from app.models.state import GraphState
from app.services.llm_service import LLMService
from app.utils.helpers import sanitize_location_name


def parse_input_node(state: GraphState) -> GraphState:
	"""
	Usa LLM para extraer origin, destinations y return_to_origin
	del texto natural del usuario
	"""
	if not state.user_input or not state.user_input.strip():
		state.error = "Entrada de usuario vacía"
		return state

	llm = LLMService()

	try:
		parsed = llm.parse_route_input(state.user_input)

		origin = sanitize_location_name(parsed.get("origin", "").strip())
		destinations = [
			sanitize_location_name(d)
			for d in parsed.get("destinations", [])
			if isinstance(d, str) and d.strip()
		]
		return_to_origin = bool(parsed.get("return_to_origin", False))

		# Si no hay origen explícito, usar el primero de la lista
		if not origin and destinations:
			origin = destinations[0]
			destinations = destinations[1:]

		if not origin:
			state.error = "No se pudo identificar el origen"
			return state

		if not destinations:
			state.error = "No se identificaron destinos"
			return state

		state.origin = origin
		state.destinations = destinations
		state.return_to_origin = return_to_origin

		state.messages.append({
			"role": "system",
			"content": f"✅ Parseo: origen='{origin}', destinos={len(destinations)}, volver={return_to_origin}"
		})

	except Exception as e:
		state.error = f"Error parseando entrada: {str(e)}"

	return state
