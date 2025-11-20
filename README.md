
# AgenteRutas-IA — Agente de Rutas con IA

Agente que convierte una descripción en lenguaje natural en una ruta optimizada usando LangGraph, OpenAI y Google Maps. Incluye un frontend simple con un botón para calcular rutas desde la interfaz.

Principales características

- Entrada en lenguaje natural para describir origen y destinos
- Backend en FastAPI con endpoints claros y documentados (/docs)
- Optimización de rutas (TSP) y cálculo de distancias/tiempos con Google Maps
- Frontend minimalista listo: botón de rutas que llama a la API y muestra resultados
- Salida JSON estructurada con pasos, distancias y tiempos

Requisitos

- Python 3.10+
- Claves: GOOGLE_MAPS_API_KEY y OPENAI_API_KEY

Instalación y ejecución rápida

1) Crear y activar entorno (Windows PowerShell):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Copiar variables de entorno (editar según tu entorno):

```powershell
copy .env.example .env
# Edita .env y agrega OPENAI_API_KEY y GOOGLE_MAPS_API_KEY
```

3) Iniciar backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

Frontend

- Abre `frontend/index.html` en un navegador local o usa la ruta estática si sirves archivos desde el backend.
- En la interfaz hay un campo de texto para la consulta y un botón ("Calcular ruta" / "Botón de rutas") que envía la petición a `POST /api/route` y muestra el resultado.

Endpoints principales

- POST /api/route  — Calcula la ruta optimizada (payload: { "query": "texto" })
- GET /health      — Health check
- GET /api/info    — Información básica de la API
- /docs            — Documentación automática de FastAPI

Ejemplo mínimo

Request:

```json
{ "query": "Estoy en Lima, quiero visitar Miraflores y Barranco y regresar" }
```

Respuesta (resumen):

{
  "origin": "Lima",
  "optimized_order": ["Lima","Miraflores","Barranco"],
  "total_distance_km": 12.5,
  "estimated_time_min": 35,
  "steps": [ ... ]
}

Notas de despliegue y seguridad

- No subir claves en repositorios públicos. Usa variables de entorno en CI/CD.
- Ajusta CORS y límites de petición para producción.
- Revisa cuotas de Google Maps y políticas de facturación.

Tecnologías

- Python, FastAPI, Pydantic
- LangGraph para orquestación del flujo
- OpenAI (LLM) para parsing de entrada
- Google Maps Platform (Geocoding, Distance Matrix, Directions)
- OR-Tools / heurísticas para TSP

Contacto

Proyecto preparado y funcional; revisa `app/main.py` y `frontend/index.html` para detalles de integración.
