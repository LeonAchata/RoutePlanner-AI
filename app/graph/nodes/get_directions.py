"""
Nodo 5: Obtiene direcciones detalladas para cada tramo de la ruta
"""
from app.models.state import GraphState, RouteStep
from app.services.google_maps import GoogleMapsService


def get_directions_node(state: GraphState) -> GraphState:
    """
    Obtiene direcciones paso a paso usando Google Directions API
    para cada segmento de la ruta optimizada
    """
    
    if not state.optimized_order:
        state.error = "No hay ruta optimizada disponible"
        return state
    
    google_service = GoogleMapsService()
    route_steps: list[RouteStep] = []
    
    try:
        # Iterar sobre cada par consecutivo en la ruta
        for i in range(len(state.optimized_order) - 1):
            from_idx = state.optimized_order[i]
            to_idx = state.optimized_order[i + 1]
            
            from_location = state.locations[from_idx]
            to_location = state.locations[to_idx]
            
            # Obtener direcciones para este tramo
            directions = google_service.get_directions(
                origin=(from_location.lat, from_location.lng),
                destination=(to_location.lat, to_location.lng)
            )
            
            if not directions:
                # Si no hay direcciones, usar datos de la matriz
                distance_km = state.distance_matrix[from_idx][to_idx]
                duration_min = state.duration_matrix[from_idx][to_idx]
                polyline = None
            else:
                # Extraer información de la primera ruta
                leg = directions[0]['legs'][0]
                distance_km = leg['distance']['value'] / 1000.0
                duration_min = leg['duration']['value'] // 60
                polyline = directions[0]['overview_polyline']['points']
            
            # Crear step
            step = RouteStep(
                from_location=from_location.name,
                to_location=to_location.name,
                distance_km=round(distance_km, 2),
                duration_min=duration_min,
                polyline=polyline
            )
            
            route_steps.append(step)
        
        state.route_steps = route_steps
        
        state.messages.append({
            "role": "system",
            "content": f"✅ Direcciones obtenidas: {len(route_steps)} tramos"
        })
        
    except Exception as e:
        # Si falla Directions API, construir steps básicos desde la matriz
        state.messages.append({
            "role": "system",
            "content": f"⚠️ Usando datos de matriz (Directions API falló): {str(e)}"
        })
        
        for i in range(len(state.optimized_order) - 1):
            from_idx = state.optimized_order[i]
            to_idx = state.optimized_order[i + 1]
            
            step = RouteStep(
                from_location=state.locations[from_idx].name,
                to_location=state.locations[to_idx].name,
                distance_km=round(state.distance_matrix[from_idx][to_idx], 2),
                duration_min=state.duration_matrix[from_idx][to_idx],
                polyline=None
            )
            route_steps.append(step)
        
        state.route_steps = route_steps
    
    return state