"""
Nodo 4: Optimiza el orden de visita usando TSP
"""
from app.models.state import GraphState
from app.services.tsp_solver import TSPSolver, solve_tsp_ortools


def optimize_route_node(state: GraphState) -> GraphState:
    """
    Calcula el orden óptimo de visita para minimizar distancia total
    usando algoritmos TSP
    """
    
    if not state.distance_matrix:
        state.error = "No hay matriz de distancias disponible"
        return state
    
    try:
        # Decidir qué solver usar según el tamaño del problema
        n = len(state.distance_matrix)
        
        if n > 15:
            # Para problemas grandes, usar OR-Tools (más robusto)
            optimized_indices, total_distance = solve_tsp_ortools(
                state.distance_matrix,
                return_to_start=state.return_to_origin
            )
        else:
            # Para problemas pequeños, usar heurística propia
            solver = TSPSolver(state.distance_matrix)
            optimized_indices, total_distance = solver.solve(
                return_to_start=state.return_to_origin
            )
        
        # Guardar orden optimizado
        state.optimized_order = optimized_indices
        
        # Convertir índices a nombres de ubicaciones
        optimized_names = [
            state.locations[idx].name 
            for idx in optimized_indices
        ]
        state.optimized_locations = optimized_names
        
        # Calcular distancia y tiempo total
        if state.return_to_origin and optimized_indices[-1] != 0:
            # Si debe volver y no está en la ruta, agregar manualmente
            total_distance += state.distance_matrix[optimized_indices[-1]][0]
        
        state.total_distance_km = round(total_distance, 2)
        
        # Calcular tiempo total aproximado
        total_duration = 0
        for i in range(len(optimized_indices) - 1):
            from_idx = optimized_indices[i]
            to_idx = optimized_indices[i + 1]
            total_duration += state.duration_matrix[from_idx][to_idx]
        
        state.total_duration_min = total_duration
        
        # Logging
        route_str = " → ".join(optimized_names)
        state.messages.append({
            "role": "system",
            "content": f"✅ Ruta optimizada: {route_str}"
        })
        state.messages.append({
            "role": "system",
            "content": f"📊 Distancia total: {state.total_distance_km} km, Tiempo: {state.total_duration_min} min"
        })
        
    except Exception as e:
        state.error = f"Error optimizando ruta: {str(e)}"
    
    return state