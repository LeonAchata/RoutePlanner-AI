"""
Funciones utilitarias para el proyecto
"""
from typing import List, Tuple
import math


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calcula la distancia en kilómetros entre dos coordenadas usando la fórmula de Haversine
    
    Args:
        coord1: Tupla (lat, lng) del primer punto
        coord2: Tupla (lat, lng) del segundo punto
        
    Returns:
        Distancia en kilómetros
    """
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    # Radio de la Tierra en kilómetros
    R = 6371.0
    
    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def format_duration(minutes: int) -> str:
    """
    Formatea duración en minutos a string legible
    
    Args:
        minutes: Duración en minutos
        
    Returns:
        String formateado (ej: "2h 30min" o "45 min")
    """
    if minutes < 60:
        return f"{minutes} min"
    
    hours = minutes // 60
    mins = minutes % 60
    
    if mins == 0:
        return f"{hours}h"
    
    return f"{hours}h {mins}min"


def format_distance(km: float) -> str:
    """
    Formatea distancia en kilómetros a string legible
    
    Args:
        km: Distancia en kilómetros
        
    Returns:
        String formateado
    """
    if km < 1:
        meters = int(km * 1000)
        return f"{meters} m"
    
    return f"{km:.1f} km"


def validate_coordinates(lat: float, lng: float) -> bool:
    """
    Valida que las coordenadas sean válidas
    
    Args:
        lat: Latitud
        lng: Longitud
        
    Returns:
        True si son válidas
    """
    return -90 <= lat <= 90 and -180 <= lng <= 180


def calculate_bounding_box(coordinates: List[Tuple[float, float]]) -> dict:
    """
    Calcula el bounding box de un conjunto de coordenadas
    
    Args:
        coordinates: Lista de tuplas (lat, lng)
        
    Returns:
        Dict con north, south, east, west
    """
    if not coordinates:
        return {}
    
    lats = [coord[0] for coord in coordinates]
    lngs = [coord[1] for coord in coordinates]
    
    return {
        "north": max(lats),
        "south": min(lats),
        "east": max(lngs),
        "west": min(lngs)
    }


def estimate_fuel_cost(
    distance_km: float, 
    fuel_price_per_liter: float = 4.5,
    consumption_per_100km: float = 8.0
) -> float:
    """
    Estima el costo de combustible para una distancia dada
    
    Args:
        distance_km: Distancia en kilómetros
        fuel_price_per_liter: Precio del combustible por litro (default: 4.5 soles)
        consumption_per_100km: Consumo en litros cada 100km (default: 8.0)
        
    Returns:
        Costo estimado en soles
    """
    liters_needed = (distance_km / 100) * consumption_per_100km
    total_cost = liters_needed * fuel_price_per_liter
    return round(total_cost, 2)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Divide una lista en chunks de tamaño específico
    
    Args:
        lst: Lista a dividir
        chunk_size: Tamaño de cada chunk
        
    Returns:
        Lista de chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def sanitize_location_name(name: str) -> str:
    """
    Limpia y normaliza nombres de ubicaciones
    
    Args:
        name: Nombre de ubicación
        
    Returns:
        Nombre limpio
    """
    # Eliminar espacios extra
    name = " ".join(name.split())
    
    # Capitalizar correctamente
    name = name.title()
    
    return name.strip()