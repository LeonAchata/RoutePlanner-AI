"""
Nodo 3: Calcula la matriz de distancias entre todas las ubicaciones
"""
from app.models.state import GraphState
from app.services.google_maps import GoogleMapsService


def distance_matrix_node(state: GraphState) -> GraphState:
    """
    Obtiene matriz de distancias y duraciones usando Google Distance Matrix API
    """
    
    if not state.locations:
        state.error = "No hay ubicaciones geocodificadas"
        return state
    
    google_service = GoogleMapsService()
    
    try:
        # Obtener matriz completa
        result = google_service.get_distance_matrix(
            origins=state.locations,
            destinations=state.locations
        )
        
        # Verificar que la respuesta sea válida
        if result['status'] != 'OK':
            state.error = f"Error en Distance Matrix API: {result['status']}"
            return state
        
        # Extraer distancias y duraciones
        n = len(state.locations)
        distance_matrix = []
        duration_matrix = []
        
        for i in range(n):
            distance_row = []
            duration_row = []
            
            for j in range(n):
                element = result['rows'][i]['elements'][j]
                
                if element['status'] != 'OK':
                    # Si no hay ruta, usar un valor muy grande
                    distance_row.append(999999.0)
                    duration_row.append(999999)
                else:
                    # Distancia en kilómetros
                    distance_km = element['distance']['value'] / 1000.0
                    distance_row.append(distance_km)
                    
                    # Duración en minutos
                    duration_min = element['duration']['value'] // 60
                    duration_row.append(duration_min)
            
            distance_matrix.append(distance_row)
            duration_matrix.append(duration_row)
        
        state.distance_matrix = distance_matrix
        state.duration_matrix = duration_matrix
        
        # Calcular estadísticas para logging
        total_distances = sum(sum(row) for row in distance_matrix)
        avg_distance = total_distances / (n * n) if n > 0 else 0
        
        state.messages.append({
            "role": "system",
            "content": f"✅ Matriz calculada: {n}x{n} ubicaciones, distancia promedio: {avg_distance:.1f} km"
        })
        
    except Exception as e:
        state.error = f"Error calculando matriz de distancias: {str(e)}"
    
    return state