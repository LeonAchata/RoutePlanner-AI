from typing import Literal, Optional

from pydantic import BaseModel, Field

TravelMode = Literal["driving", "walking", "bicycling"]


class Location(BaseModel):
    name: str
    address: Optional[str] = None
    lat: float
    lng: float


class RouteStep(BaseModel):
    from_location: str
    to_location: str
    distance_km: float
    duration_min: int


class GraphState(BaseModel):
    """State shared by every node in the graph.

    Nodes never mutate this object; they return a dict with the fields they
    want to update and LangGraph merges it.
    """

    # Input
    user_input: str
    travel_mode: TravelMode = "driving"

    # parse
    origin: Optional[str] = None
    destinations: list[str] = Field(default_factory=list)
    return_to_origin: bool = False

    # geocode (index 0 is always the origin)
    locations: list[Location] = Field(default_factory=list)

    # distance_matrix: kilometres and minutes, None where no route exists
    distance_matrix: list[list[Optional[float]]] = Field(default_factory=list)
    duration_matrix: list[list[Optional[float]]] = Field(default_factory=list)

    # optimize: indexes into `locations`, ends with 0 on round trips
    optimized_order: list[int] = Field(default_factory=list)

    # directions
    route_steps: list[RouteStep] = Field(default_factory=list)
    route_polyline: Optional[str] = None

    # format
    total_distance_km: float = 0.0
    total_duration_min: int = 0
    google_maps_url: str = ""

    # Error handling: any node can set these and the graph stops early.
    error: Optional[str] = None
    error_status: int = 400
