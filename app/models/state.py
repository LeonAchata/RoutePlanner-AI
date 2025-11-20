from typing import Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph import add_messages


class Location(BaseModel):
    name: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class RouteStep(BaseModel):
    from_location: str
    to_location: str
    distance_km: float
    duration_min: int
    polyline: Optional[str] = None


class GraphState(BaseModel):
    """Estado compartido entre todos los nodos del grafo"""

    # Input
    user_input: str

    # Parsed data
    origin: Optional[str] = None
    destinations: list[str] = Field(default_factory=list)
    return_to_origin: bool = False

    # Geocoded locations
    locations: list[Location] = Field(default_factory=list)

    # Distance matrix
    distance_matrix: list[list[float]] = Field(default_factory=list)
    duration_matrix: list[list[int]] = Field(default_factory=list)

    # Optimized route
    optimized_order: list[int] = Field(default_factory=list)
    optimized_locations: list[str] = Field(default_factory=list)

    # Final route details
    route_steps: list[RouteStep] = Field(default_factory=list)
    total_distance_km: float = 0.0
    total_duration_min: int = 0
    google_maps_url: str = ""

    # Messages for debugging (LangGraph message store)
    messages: Annotated[list, add_messages] = Field(default_factory=list)

    # Error handling
    error: Optional[str] = None