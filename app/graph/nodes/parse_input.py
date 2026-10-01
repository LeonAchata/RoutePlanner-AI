"""Node 1: extract origin, destinations and round-trip intent from free text."""
from app.config import get_settings
from app.errors import RouteError
from app.formatting import clean_location_name
from app.models.state import GraphState
from app.services.llm_service import LLMService


def parse_input_node(state: GraphState) -> dict:
    text = state.user_input.strip()
    if not text:
        raise RouteError("Describe the trip you want to plan.")

    parsed = LLMService().parse_route_input(text)

    origin = clean_location_name(parsed.origin or "")
    destinations = []
    seen = {origin.lower()}
    for raw in parsed.destinations:
        name = clean_location_name(raw)
        # Drop blanks, repeats and the origin itself (the LLM sometimes lists
        # it again when the user says they will go back).
        if name and name.lower() not in seen:
            seen.add(name.lower())
            destinations.append(name)

    if not origin and destinations:
        origin, destinations = destinations[0], destinations[1:]

    if not origin:
        raise RouteError("Could not tell where the trip starts. Try something like \"From Miraflores, go to ...\".")
    if not destinations:
        raise RouteError("Could not find any places to visit in the description.")

    max_stops = get_settings().max_stops
    if len(destinations) + 1 > max_stops:
        raise RouteError(f"A route can have at most {max_stops} stops including the origin.")

    return {
        "origin": origin,
        "destinations": destinations,
        "return_to_origin": parsed.return_to_origin,
    }
