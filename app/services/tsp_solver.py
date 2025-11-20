"""
Servicio para resolver el problema del viajante (TSP)
Usa heurística Nearest Neighbor y optimización 2-opt
"""
from typing import List, Tuple
import numpy as np


class TSPSolver:
    """Resuelve TSP para rutas pequeñas (<20 nodos)"""
    
    def __init__(self, distance_matrix: List[List[float]]):
        """
        Args:
            distance_matrix: Matriz NxN de distancias entre ubicaciones
        """
        self.matrix = np.array(distance_matrix)
        self.n = len(distance_matrix)
    
    def solve(self, return_to_start: bool = False) -> Tuple[List[int], float]:
        """
        Encuentra la ruta óptima usando heurística + 2-opt
        
        Args:
            return_to_start: Si debe volver al punto inicial
            
        Returns:
            (ruta_ordenada, distancia_total)
        """
        if self.n <= 2:
            route = list(range(self.n))
            if return_to_start and self.n == 2:
                route.append(0)
            return route, self._calculate_route_distance(route)
        
        # Heurística: Nearest Neighbor desde el nodo 0
        route = self._nearest_neighbor()
        
        # Optimización: 2-opt
        route = self._two_opt(route)
        
        # Si debe volver al inicio, agregar el nodo 0 al final
        if return_to_start:
            route.append(0)
        
        total_distance = self._calculate_route_distance(route)
        
        return route, total_distance
    
    def _nearest_neighbor(self) -> List[int]:
        """Heurística del vecino más cercano"""
        unvisited = set(range(1, self.n))  # Comenzamos desde 0
        route = [0]
        current = 0
        
        while unvisited:
            # Encontrar el más cercano no visitado
            nearest = min(unvisited, key=lambda x: self.matrix[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        return route
    
    def _two_opt(self, route: List[int], max_iterations: int = 1000) -> List[int]:
        """
        Optimización 2-opt: intercambia pares de aristas para mejorar la ruta
        """
        best_route = route.copy()
        best_distance = self._calculate_route_distance(best_route)
        improved = True
        iteration = 0
        
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route)):
                    if j - i == 1:
                        continue
                    
                    # Crear nueva ruta invirtiendo el segmento
                    new_route = route[:i] + route[i:j][::-1] + route[j:]
                    new_distance = self._calculate_route_distance(new_route)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        route = new_route
                        improved = True
                        break
                
                if improved:
                    break
        
        return best_route
    
    def _calculate_route_distance(self, route: List[int]) -> float:
        """Calcula la distancia total de una ruta"""
        total = 0.0
        for i in range(len(route) - 1):
            total += self.matrix[route[i]][route[i + 1]]
        return total


def solve_tsp_ortools(
    distance_matrix: List[List[float]], 
    return_to_start: bool = False
) -> Tuple[List[int], float]:
    """
    Alternativa usando OR-Tools (más preciso para problemas grandes)
    Requiere: pip install ortools
    """
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp
    except ImportError:
        # Fallback a heurística propia
        solver = TSPSolver(distance_matrix)
        return solver.solve(return_to_start)
    
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix), 
        1,  # Un solo vehículo
        0   # Depot (inicio)
    )
    routing = pywrapcp.RoutingModel(manager)
    
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(distance_matrix[from_node][to_node] * 1000)  # Convertir a metros
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    solution = routing.SolveWithParameters(search_parameters)
    
    if solution:
        route = []
        index = routing.Start(0)
        total_distance = 0
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            route.append(node)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            total_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
        
        if return_to_start:
            route.append(0)
        
        return route, total_distance / 1000.0  # Convertir de vuelta a km
    
    # Si no hay solución, usar heurística
    solver = TSPSolver(distance_matrix)
    return solver.solve(return_to_start)