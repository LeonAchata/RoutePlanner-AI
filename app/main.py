from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.graph.workflow import run_workflow
from app.models.state import GraphState
from app.models.schemas import RouteRequest, RouteResponse, RouteStepResponse
from app.utils.helpers import format_distance, format_duration


settings = get_settings()

app = FastAPI(title=settings.app_name, debug=settings.debug)

# CORS (abierto por defecto; ajustar para producción)
app.add_middleware(
	CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/health")
def health():
    """
    Health check endpoint para Railway/Docker/monitoreo
    """
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0",
    }
@app.post("/api/route", response_model=RouteResponse)
def create_route(req: RouteRequest):
    result = run_workflow(req.query)

    # langgraph>=0.6 devuelve dict; convertir a GraphState
    if isinstance(result, dict):
        try:
            result = GraphState.model_validate(result)
        except Exception:
            # Como fallback, pasar el error si existe
            err = result.get("error") if isinstance(result, dict) else None
            raise HTTPException(status_code=400, detail=str(err or "Error interno"))

    if result.error:
        raise HTTPException(status_code=400, detail=result.error)

    # Construir respuesta
    steps: list[RouteStepResponse] = []
    for s in result.route_steps:
        steps.append(
            RouteStepResponse(
                **{
                    "from": s.from_location,
                    "to": s.to_location,
                    "distance": format_distance(s.distance_km),
                    "time": format_duration(s.duration_min),
                }
            )
        )

    resp = RouteResponse(
        origin=result.origin or (result.optimized_locations[0] if result.optimized_locations else ""),
        optimized_order=result.optimized_locations,
        total_distance_km=result.total_distance_km,
        estimated_time_min=result.total_duration_min,
        steps=steps,
        google_maps_url=result.google_maps_url,
    )
    return resp


@app.get("/api/info")
def api_info():
    """
    Información de la API para clientes
    """
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "calculate_route": "POST /api/route",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
        "description": "API para cálculo de rutas óptimas usando LangGraph y Google Maps",
    }


# Root info
@app.get("/")
def root():
    """
    Root endpoint - redirige a documentación
    """
    return {
        "name": settings.app_name,
        "message": "Agente de Rutas con IA - LangGraph + Google Maps",
        "docs": "/docs",
        "api_info": "/api/info",
        "health": "/health",
    }