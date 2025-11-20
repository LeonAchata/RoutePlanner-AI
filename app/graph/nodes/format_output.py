"""
Nodo 6: Formatea la salida final (último nodo antes de END)
"""
from app.models.state import GraphState


def format_output_node(state: GraphState) -> GraphState:
    """
    Nodo final: valida y formatea la salida
    Asegura que todos los datos necesarios estén presentes
    """
    
    try:
        # Validaciones finales
        if not state.optimized_locations:
            state.error = "No se generó ruta optimizada"
            return state
        
        if not state.route_steps:
            state.error = "No se generaron pasos de la ruta"
            return state
        
        # Validar consistencia
        expected_steps = len(state.optimized_locations) - 1
        if len(state.route_steps) != expected_steps:
            state.messages.append({
                "role": "system",
                "content": f"⚠️ Inconsistencia: {len(state.route_steps)} steps vs {expected_steps} esperados"
            })
        
        # Recalcular totales por si acaso (redundancia)
        recalculated_distance = sum(step.distance_km for step in state.route_steps)
        recalculated_duration = sum(step.duration_min for step in state.route_steps)
        
        # Si hay diferencia significativa, actualizar
        if abs(recalculated_distance - state.total_distance_km) > 0.5:
            state.total_distance_km = round(recalculated_distance, 2)
        
        if abs(recalculated_duration - state.total_duration_min) > 2:
            state.total_duration_min = recalculated_duration
        
        # Mensaje de éxito
        state.messages.append({
            "role": "system",
            "content": f"✅ Ruta completada: {len(state.optimized_locations)} ubicaciones, "
                      f"{state.total_distance_km} km, {state.total_duration_min} min"
        })
        
        # Generar resumen legible
        summary_parts = []
        summary_parts.append(f"🗺️ Ruta óptima calculada:")
        summary_parts.append(f"📍 Inicio: {state.origin}")
        summary_parts.append(f"🎯 Destinos visitados: {len(state.destinations)}")
        summary_parts.append(f"📏 Distancia total: {state.total_distance_km} km")
        summary_parts.append(f"⏱️ Tiempo estimado: {state.total_duration_min} min ({state.total_duration_min // 60}h {state.total_duration_min % 60}min)")
        summary_parts.append(f"\n🛣️ Orden de visita:")
        
        for i, location in enumerate(state.optimized_locations, 1):
            summary_parts.append(f"  {i}. {location}")
        
        state.messages.append({
            "role": "assistant",
            "content": "\n".join(summary_parts)
        })
        
        # Generar URL de Google Maps con paradas
        import urllib.parse
        
        locs = state.optimized_locations
        if locs and len(locs) > 1:
            origin = urllib.parse.quote(locs[0])
            destination = urllib.parse.quote(locs[-1])
            waypoints = "|".join([urllib.parse.quote(loc) for loc in locs[1:-1]]) if len(locs) > 2 else ""
            base = "https://www.google.com/maps/dir/?api=1"
            url = f"{base}&origin={origin}&destination={destination}"
            if waypoints:
                url += f"&waypoints={waypoints}"
            url += "&travelmode=driving"
            state.google_maps_url = url
        else:
            state.google_maps_url = ""
        
    except Exception as e:
        state.error = f"Error formateando salida: {str(e)}"
    
    return state