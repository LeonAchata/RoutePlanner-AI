from pydantic import BaseModel, Field

class RouteRequest(BaseModel):
    query: str = Field(
        ..., 
        description="Texto natural describiendo la ruta",
        examples=["Estoy en Lima, quiero ir a Miraflores, Barranco y Surco"]
    )

class RouteStepResponse(BaseModel):
    from_location: str = Field(alias="from")
    to_location: str = Field(alias="to")
    distance: str
    time: str

class RouteResponse(BaseModel):
    origin: str
    optimized_order: list[str]
    total_distance_km: float
    estimated_time_min: int
    steps: list[RouteStepResponse]
    google_maps_url: str = ""

    class Config:
        populate_by_name = True