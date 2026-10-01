"""End-to-end tests of the API with OpenAI and Google Maps replaced by fakes."""
import importlib

import pytest
from fastapi.testclient import TestClient

from app.errors import RouteError
from app.main import app
from app.models.state import Location
from app.services import google_maps, llm_service
from app.services.llm_service import ParsedRoute

PLACES = {
    "Lima Centro": (-12.0464, -77.0428),
    "San Isidro": (-12.0977, -77.0365),
    "Miraflores": (-12.1211, -77.0297),
    "Barranco": (-12.1490, -77.0215),
}
DEFAULT_PARSE = ParsedRoute(origin="Lima Centro", destinations=["Barranco", "San Isidro", "Miraflores"])


class FakeLLM:
    parsed = DEFAULT_PARSE

    def __init__(self, *args, **kwargs):
        pass

    def parse_route_input(self, text):
        return self.parsed


class FakeMaps:
    directions_fail = False

    def __init__(self, *args, **kwargs):
        pass

    def geocode(self, name):
        if name not in PLACES:
            raise RouteError(f'Could not find "{name}" on the map.')
        lat, lng = PLACES[name]
        return Location(name=name, address=f"{name}, Lima, Peru", lat=lat, lng=lng)

    def distance_matrix(self, locations, mode="driving"):
        # Distance proportional to the latitude difference, so the best open
        # route from Lima Centro simply heads south.
        km = [[abs(a.lat - b.lat) * 111 for b in locations] for a in locations]
        minutes = [[d * 3 for d in row] for row in km]
        return km, minutes

    def directions(self, stops, mode="driving"):
        if self.directions_fail:
            raise RouteError("boom", 502)
        legs = [
            {"distance": {"value": 1000 * (i + 1)}, "duration": {"value": 600 * (i + 1)}}
            for i in range(len(stops) - 1)
        ]
        return {"legs": legs, "overview_polyline": {"points": "abc"}}


@pytest.fixture
def client(monkeypatch):
    for name in ("parse_input", "geocode", "distance_matrix", "get_directions"):
        module = importlib.import_module(f"app.graph.nodes.{name}")
        if hasattr(module, "LLMService"):
            monkeypatch.setattr(module, "LLMService", FakeLLM)
        if hasattr(module, "GoogleMapsService"):
            monkeypatch.setattr(module, "GoogleMapsService", FakeMaps)
    monkeypatch.setattr(FakeMaps, "directions_fail", False)
    monkeypatch.setattr(FakeLLM, "parsed", DEFAULT_PARSE)
    return TestClient(app)


def post(client, query="from lima centro to barranco, san isidro and miraflores", **extra):
    return client.post("/api/route", json={"query": query, **extra})


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["missing_config"] == []


def test_frontend_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "<html" in res.text.lower()


def test_route_is_optimised(client):
    res = post(client)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["optimized_order"] == ["Lima Centro", "San Isidro", "Miraflores", "Barranco"]
    assert [s["from"] for s in body["steps"]] == ["Lima Centro", "San Isidro", "Miraflores"]
    assert body["total_distance_km"] == pytest.approx(6.0)
    assert body["estimated_time_min"] == 60
    assert body["route_polyline"] == "abc"
    assert body["google_maps_url"].startswith("https://www.google.com/maps/dir/")
    assert len(body["stops"]) == 4


def test_round_trip_ends_at_origin(client, monkeypatch):
    monkeypatch.setattr(
        FakeLLM, "parsed", ParsedRoute(origin="Lima Centro", destinations=["Barranco", "Miraflores"], return_to_origin=True)
    )
    body = post(client).json()
    assert body["optimized_order"][0] == body["optimized_order"][-1] == "Lima Centro"
    assert len(body["steps"]) == 3
    assert body["return_to_origin"] is True


def test_directions_failure_falls_back_to_matrix(client, monkeypatch):
    monkeypatch.setattr(FakeMaps, "directions_fail", True)
    body = post(client).json()
    assert body["route_polyline"] is None
    assert body["total_distance_km"] == pytest.approx((-12.0464 + 12.1490) * 111, abs=0.05)


def test_unknown_place_returns_422(client, monkeypatch):
    monkeypatch.setattr(FakeLLM, "parsed", ParsedRoute(origin="Lima Centro", destinations=["Atlantis"]))
    res = post(client)
    assert res.status_code == 422
    assert "Atlantis" in res.json()["detail"]


def test_origin_repeated_in_destinations_is_removed(client, monkeypatch):
    monkeypatch.setattr(FakeLLM, "parsed", ParsedRoute(origin="Lima Centro", destinations=["Barranco", "lima centro"]))
    body = post(client).json()
    assert body["optimized_order"] == ["Lima Centro", "Barranco"]


def test_no_destinations(client, monkeypatch):
    monkeypatch.setattr(FakeLLM, "parsed", ParsedRoute(origin="Lima Centro", destinations=[]))
    assert post(client, "hello there").status_code == 422


def test_request_validation(client):
    assert post(client, "").status_code == 422
    assert post(client, travel_mode="teleport").status_code == 422


def test_unexpected_crash_returns_500_without_leaking_details(client, monkeypatch):
    def explode(self, text):
        raise RuntimeError("secret internals")

    monkeypatch.setattr(FakeLLM, "parse_route_input", explode)
    res = post(client)
    assert res.status_code == 500
    assert "secret" not in res.json()["detail"]


def test_llm_output_is_validated():
    class Message:
        content = ""

    class Completions:
        @staticmethod
        def create(**kwargs):
            choice = type("Choice", (), {"message": Message})
            return type("Completion", (), {"choices": [choice]})

    class Client:
        chat = type("Chat", (), {"completions": Completions})

    service = llm_service.LLMService(client=Client)

    Message.content = '{"origin": null, "destinations": ["A", 3, " ", "B"], "return_to_origin": true}'
    parsed = service.parse_route_input("x")
    assert parsed.origin is None
    assert parsed.destinations == ["A", "B"]
    assert parsed.return_to_origin is True

    Message.content = "not json"
    with pytest.raises(RouteError):
        service.parse_route_input("x")


def test_distance_matrix_requests_are_chunked():
    calls = []

    class Client:
        def distance_matrix(self, origins, destinations, **kwargs):
            calls.append(len(origins) * len(destinations))
            element = {"status": "OK", "distance": {"value": 1000}, "duration": {"value": 60}}
            return {"status": "OK", "rows": [{"elements": [element] * len(destinations)} for _ in origins]}

    locations = [Location(name=str(i), lat=i, lng=i) for i in range(20)]
    km, minutes = google_maps.GoogleMapsService(client=Client()).distance_matrix(locations)
    assert len(km) == 20 and all(len(row) == 20 for row in km)
    assert max(calls) <= google_maps.MAX_MATRIX_ELEMENTS
    assert minutes[3][4] == 1.0
