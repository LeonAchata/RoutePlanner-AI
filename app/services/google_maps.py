"""Thin wrapper around the Google Maps Geocoding, Distance Matrix and Directions APIs."""
import logging
from functools import lru_cache
from typing import Any, Optional

import googlemaps
from googlemaps.exceptions import ApiError, HTTPError, Timeout, TransportError

from app.config import get_settings
from app.errors import RouteError, UpstreamError
from app.models.state import Location

logger = logging.getLogger(__name__)

# Distance Matrix limits per request (standard plan).
MAX_MATRIX_ELEMENTS = 100
MAX_MATRIX_SIDE = 25

LatLng = tuple[float, float]


@lru_cache
def _client() -> googlemaps.Client:
    settings = get_settings()
    return googlemaps.Client(
        key=settings.google_maps_api_key,
        timeout=settings.maps_timeout_seconds,
        retry_timeout=2 * settings.maps_timeout_seconds,
    )


def _translate(exc: Exception, api: str) -> RouteError:
    """Map googlemaps exceptions to something we can show the user."""
    if isinstance(exc, ApiError):
        if exc.status == "REQUEST_DENIED":
            logger.error("%s denied the request: %s", api, exc.message)
            return UpstreamError(f"Google {api} denied the request. Check that the API is enabled for this key.")
        if exc.status == "OVER_QUERY_LIMIT":
            return UpstreamError(f"Google {api} quota exceeded. Try again later.")
        if exc.status == "MAX_ELEMENTS_EXCEEDED":
            return RouteError("Too many stops for a single request.")
        return UpstreamError(f"Google {api} returned {exc.status}.")
    if isinstance(exc, (Timeout, TransportError, HTTPError)):
        return UpstreamError(f"Could not reach Google {api}.")
    return UpstreamError(f"Unexpected error from Google {api}.")


class GoogleMapsService:
    # Shared across instances. Only used with the default client so tests that
    # inject a fake client never see results from a previous test.
    _geocode_cache: dict[tuple[str, str, str], Location] = {}
    _GEOCODE_CACHE_SIZE = 512

    def __init__(self, client: Optional[googlemaps.Client] = None):
        self.settings = get_settings()
        self._use_cache = client is None
        self.client = client or _client()

    def geocode(self, query: str) -> Location:
        """Resolve a place name or address to coordinates.

        Results are cached per process because delivery addresses and
        districts repeat a lot between requests.
        """
        key = (" ".join(query.lower().split()), self.settings.geocoding_language, self.settings.default_country)
        cached = self._geocode_cache.get(key) if self._use_cache else None
        if cached is not None:
            return cached.model_copy(update={"name": query})

        location = self._geocode_uncached(query)
        if self._use_cache:
            if len(self._geocode_cache) >= self._GEOCODE_CACHE_SIZE:
                self._geocode_cache.pop(next(iter(self._geocode_cache)))
            self._geocode_cache[key] = location
        return location

    def _geocode_uncached(self, query: str) -> Location:
        try:
            results = self.client.geocode(
                query,
                language=self.settings.geocoding_language,
                region=self.settings.default_country.lower(),
            )
        except Exception as exc:  # googlemaps raises several unrelated types
            raise _translate(exc, "Geocoding") from exc

        if not results:
            raise RouteError(f'Could not find "{query}" on the map. Try adding the district or city.')

        top = results[0]
        point = top["geometry"]["location"]
        return Location(
            name=query,
            address=top.get("formatted_address"),
            lat=point["lat"],
            lng=point["lng"],
        )

    def distance_matrix(
        self, locations: list[Location], mode: str = "driving"
    ) -> tuple[list[list[Optional[float]]], list[list[Optional[float]]]]:
        """Return (km, minutes) NxN matrices. Cells are None when there is no route.

        Large matrices are split into several requests so no single call goes
        over the per-request element limit.
        """
        n = len(locations)
        if n > MAX_MATRIX_SIDE:
            raise RouteError(f"At most {MAX_MATRIX_SIDE} stops are supported.")

        coords: list[LatLng] = [(loc.lat, loc.lng) for loc in locations]
        distances: list[list[Optional[float]]] = []
        durations: list[list[Optional[float]]] = []
        rows_per_call = max(1, MAX_MATRIX_ELEMENTS // n)

        for start in range(0, n, rows_per_call):
            origins = coords[start:start + rows_per_call]
            try:
                result = self.client.distance_matrix(
                    origins=origins,
                    destinations=coords,
                    mode=mode,
                    units="metric",
                    language=self.settings.geocoding_language,
                )
            except Exception as exc:
                raise _translate(exc, "Distance Matrix") from exc

            if result.get("status") != "OK":
                raise UpstreamError(f"Google Distance Matrix returned {result.get('status')}.")

            for row in result["rows"]:
                dist_row: list[Optional[float]] = []
                dur_row: list[Optional[float]] = []
                for element in row["elements"]:
                    if element.get("status") == "OK":
                        dist_row.append(element["distance"]["value"] / 1000.0)
                        dur_row.append(element["duration"]["value"] / 60.0)
                    else:
                        dist_row.append(None)
                        dur_row.append(None)
                distances.append(dist_row)
                durations.append(dur_row)

        return distances, durations

    def directions(self, stops: list[Location], mode: str = "driving") -> Optional[dict[str, Any]]:
        """Fetch the full route through `stops` in the given order with one request.

        Returns the first route or None if Google could not build one.
        """
        if len(stops) < 2:
            return None
        coords = [(s.lat, s.lng) for s in stops]
        try:
            routes = self.client.directions(
                origin=coords[0],
                destination=coords[-1],
                waypoints=coords[1:-1] or None,
                optimize_waypoints=False,
                mode=mode,
                units="metric",
                language=self.settings.geocoding_language,
            )
        except Exception as exc:
            raise _translate(exc, "Directions") from exc
        return routes[0] if routes else None

