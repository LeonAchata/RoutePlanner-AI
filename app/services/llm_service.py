"""
Servicio para interactuar con LLMs (OpenAI)
"""
from openai import OpenAI
from app.config import get_settings
import json
from typing import Dict, Any, Optional


class LLMService:
    """Cliente para llamadas a modelos de lenguaje"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
    
    def parse_route_input(self, user_input: str) -> Dict[str, Any]:
        """
        Extrae información estructurada de un texto en lenguaje natural
        sobre una ruta deseada
        
        Args:
            user_input: Texto del usuario describiendo la ruta
            
        Returns:
            Dict con origin, destinations y return_to_origin
            
        Ejemplo:
            Input: "Estoy en Lima, quiero ir a Miraflores, Barranco y Surco"
            Output: {
                "origin": "Lima",
                "destinations": ["Miraflores", "Barranco", "Surco"],
                "return_to_origin": false
            }
        """
        
        system_prompt = """Eres un asistente especializado en extraer información de rutas.

Tu tarea es analizar texto en lenguaje natural y extraer:
1. origin: El punto de partida (string)
2. destinations: Lista de lugares a visitar (array de strings)
3. return_to_origin: Si menciona volver al punto inicial (boolean)

Reglas importantes:
- Respeta los nombres exactos de los lugares mencionados
- No inventes ubicaciones que no estén en el texto
- Si no hay origen explícito, usa el primer lugar mencionado
- Si dice "volver", "regresar", "retornar a casa/inicio", entonces return_to_origin es true
- Si no menciona volver, return_to_origin es false
- Devuelve SOLO JSON válido, sin explicaciones adicionales"""

        user_prompt = f"""Analiza este texto y extrae la información de ruta:

"{user_input}"

Responde con un JSON válido."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=self.settings.llm_temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            # Validación básica
            if "origin" not in parsed_data:
                raise ValueError("No se pudo identificar el origen")
            
            if "destinations" not in parsed_data or not isinstance(parsed_data["destinations"], list):
                raise ValueError("No se pudieron identificar los destinos")
            
            # Asegurar que return_to_origin sea boolean
            parsed_data["return_to_origin"] = bool(parsed_data.get("return_to_origin", False))
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parseando respuesta del LLM: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error llamando al LLM: {str(e)}")
    
    def suggest_optimization(
        self, 
        current_route: list[str], 
        context: Optional[str] = None
    ) -> str:
        """
        Sugiere mejoras u observaciones sobre una ruta calculada
        
        Args:
            current_route: Ruta actual ordenada
            context: Contexto adicional (distancias, tiempos, etc.)
            
        Returns:
            Sugerencia en texto natural
        """
        
        prompt = f"""Analiza esta ruta y sugiere observaciones útiles:

Ruta: {' → '.join(current_route)}
{f'Contexto: {context}' if context else ''}

Proporciona 2-3 observaciones breves y útiles sobre:
- Posibles optimizaciones
- Consideraciones de tiempo (hora pico, etc.)
- Alternativas de transporte si aplica

Sé conciso y práctico."""

        try:
            response = self.client.chat.completions.create(
                model=self.settings.llm_model,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": "Eres un asistente de planificación de rutas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"No se pudieron generar sugerencias: {str(e)}"