from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.state import TravelMode


class RouteRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Natural language description of the trip",
        examples=["I'm in Lima Centro, I need to go to Miraflores, Barranco and Surco"],
    )
    travel_mode: TravelMode = Field(default="driving", description="How the route will be travelled")


class StopResponse(BaseModel):
    name: str
    address: Optional[str] = None
    lat: float
    lng: float


class RouteStepResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_location: str = Field(alias="from")
    to_location: str = Field(alias="to")
    distance: str
    time: str
    distance_km: float
    duration_min: int


class RouteResponse(BaseModel):
    origin: str
    optimized_order: list[str]
    stops: list[StopResponse]
    return_to_origin: bool
    travel_mode: TravelMode
    total_distance_km: float
    estimated_time_min: int
    steps: list[RouteStepResponse]
    route_polyline: Optional[str] = None
    google_maps_url: str = ""


class ErrorResponse(BaseModel):
    detail: str
