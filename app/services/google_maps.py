"""
Servicio completo para interactuar con Google Maps APIs
"""
import googlemaps
from typing import List, Tuple, Optional, Dict, Any
from app.config import get_settings
from app.models.state import Location


class GoogleMapsService:
    """Cliente para todas las APIs de Google Maps"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = googlemaps.Client(key=self.settings.google_maps_api_key)
    
    def geocode(self, address: str) -> Location:
        """
        Convierte dirección en coordenadas usando Geocoding API
        
        Args:
            address: Dirección o nombre de lugar
            
        Returns:
            Location con coordenadas y dirección formateada
            
        Raises:
            ValueError: Si no se puede geocodificar
        """
        try:
            result = self.client.geocode(
                address,
                language=self.settings.geocoding_language,
                region=self.settings.default_country
            )
            
            if not result:
                raise ValueError(f"No se encontraron resultados para: {address}")
            
            location_data = result[0]
            geometry = location_data['geometry']['location']
            
            return Location(
                name=address,
                address=location_data['formatted_address'],
                lat=geometry['lat'],
                lng=geometry['lng']
            )
            
        except googlemaps.exceptions.ApiError as e:
            raise ValueError(f"Error en Geocoding API: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error geocodificando '{address}': {str(e)}")
    
    def get_distance_matrix(
        self, 
        origins: List[Location], 
        destinations: List[Location],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Obtiene matriz de distancias y duraciones usando Distance Matrix API
        
        Args:
            origins: Lista de ubicaciones origen
            destinations: Lista de ubicaciones destino
            mode: Modo de transporte (driving, walking, bicycling, transit)
            
        Returns:
            Respuesta completa de la API
        """
        origin_coords = [(loc.lat, loc.lng) for loc in origins]
        dest_coords = [(loc.lat, loc.lng) for loc in destinations]
        
        try:
            result = self.client.distance_matrix(
                origins=origin_coords,
                destinations=dest_coords,
                mode=mode,
                language=self.settings.geocoding_language,
                units="metric"
            )
            
            return result
            
        except googlemaps.exceptions.ApiError as e:
            raise ValueError(f"Error en Distance Matrix API: {str(e)}")
    
    def get_directions(
        self,
        origin: Tuple[float, float],
        destination: Tuple[float, float],
        mode: str = "driving",
        alternatives: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Obtiene direcciones detalladas usando Directions API
        
        Args:
            origin: Tupla (lat, lng) del origen
            destination: Tupla (lat, lng) del destino
            mode: Modo de transporte
            alternatives: Si debe devolver rutas alternativas
            
        Returns:
            Lista de rutas con pasos detallados
        """
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode,
                alternatives=alternatives,
                language=self.settings.geocoding_language,
                units="metric"
            )
            
            return result
            
        except googlemaps.exceptions.ApiError as e:
            raise ValueError(f"Error en Directions API: {str(e)}")
    
    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Obtiene detalles de un lugar usando Places API
        
        Args:
            place_id: ID del lugar en Google
            
        Returns:
            Detalles completos del lugar
        """
        try:
            result = self.client.place(
                place_id=place_id,
                language=self.settings.geocoding_language
            )
            
            return result
            
        except googlemaps.exceptions.ApiError as e:
            raise ValueError(f"Error en Places API: {str(e)}")
    
    def search_places(self, query: str, location: Optional[Tuple[float, float]] = None) -> List[Dict[str, Any]]:
        """
        Busca lugares usando Places API (Text Search)
        
        Args:
            query: Texto de búsqueda
            location: Coordenadas para centrar búsqueda (opcional)
            
        Returns:
            Lista de lugares encontrados
        """
        try:
            result = self.client.places(
                query=query,
                location=location,
                language=self.settings.geocoding_language
            )
            
            return result.get('results', [])
            
        except googlemaps.exceptions.ApiError as e:
            raise ValueError(f"Error en Places API: {str(e)}")