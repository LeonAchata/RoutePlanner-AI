"""
Nodo 2: Geocodifica todas las ubicaciones (origen + destinos)
"""
from app.models.state import GraphState, Location
from app.services.google_maps import GoogleMapsService


def geocode_node(state: GraphState) -> GraphState:
    """
    Convierte todas las direcciones de texto en coordenadas geográficas
    usando Google Geocoding API
    """
    
    # Verificar que tengamos datos del nodo anterior
    if not state.origin:
        state.error = "No se pudo identificar el origen"
        return state
    
    if not state.destinations:
        state.error = "No se identificaron destinos"
        return state
    
    google_service = GoogleMapsService()
    
    try:
        # Lista de todas las ubicaciones a geocodificar
        all_locations = [state.origin] + state.destinations
        geocoded_locations: list[Location] = []
        
        for location_name in all_locations:
            try:
                location = google_service.geocode(location_name)
                geocoded_locations.append(location)
                
                state.messages.append({
                    "role": "system",
                    "content": f"✅ Geocodificado: {location.name} → {location.address}"
                })
                
            except ValueError as e:
                state.error = f"No se pudo geocodificar '{location_name}': {str(e)}"
                return state
        
        state.locations = geocoded_locations
        
        state.messages.append({
            "role": "system",
            "content": f"✅ Total geocodificado: {len(geocoded_locations)} ubicaciones"
        })
        
    except Exception as e:
        state.error = f"Error en geocodificación: {str(e)}"
    
    return state