import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.config import get_settings
from app.formatting import format_distance, format_duration
from app.graph.workflow import run_workflow
from app.models.schemas import (
    ErrorResponse,
    RouteRequest,
    RouteResponse,
    RouteStepResponse,
    StopResponse,
)

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Plan the fastest order to visit several places from a plain-language description.",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["meta"])
def health():
    missing = settings.missing_keys()
    return {
        "status": "ok" if not missing else "degraded",
        "version": __version__,
        "missing_config": missing,
    }


@app.post(
    "/api/route",
    response_model=RouteResponse,
    tags=["routes"],
    responses={
        422: {"model": ErrorResponse, "description": "The description could not be turned into a route"},
        502: {"model": ErrorResponse, "description": "OpenAI or Google Maps failed"},
        503: {"model": ErrorResponse, "description": "The server is missing API keys"},
    },
)
def create_route(req: RouteRequest) -> RouteResponse:
    missing = settings.missing_keys()
    if missing:
        raise HTTPException(status_code=503, detail=f"Server is not configured: missing {', '.join(missing)}.")

    result = run_workflow(req.query, req.travel_mode)
    if result.error:
        raise HTTPException(status_code=result.error_status, detail=result.error)

    stops = [result.locations[i] for i in result.optimized_order]
    return RouteResponse(
        origin=result.origin or stops[0].name,
        optimized_order=[s.name for s in stops],
        stops=[StopResponse(**s.model_dump()) for s in stops],
        return_to_origin=result.return_to_origin,
        travel_mode=result.travel_mode,
        total_distance_km=result.total_distance_km,
        estimated_time_min=result.total_duration_min,
        steps=[
            RouteStepResponse(
                from_location=step.from_location,
                to_location=step.to_location,
                distance=format_distance(step.distance_km),
                time=format_duration(step.duration_min),
                distance_km=step.distance_km,
                duration_min=step.duration_min,
            )
            for step in result.route_steps
        ],
        route_polyline=result.route_polyline,
        google_maps_url=result.google_maps_url,
    )


# The web UI lives at "/". Mounted last so it never shadows the API routes.
if FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
