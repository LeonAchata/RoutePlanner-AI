FROM python:3.11-slim

# Metadata
LABEL maintainer="tu-email@example.com"
LABEL description="Agente Inteligente de Rutas con LangGraph y Google Maps"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar código de la aplicación
COPY ./app ./app
# Copiar frontend como carpeta pública (compatibilidad con estructura actual)
COPY ./frontend ./public
# Copiar script de inicio
COPY ./start.sh ./start.sh

# Hacer ejecutable el script
RUN chmod +x start.sh

# Crear usuario no-root
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puerto (Railway usa PORT variable)
EXPOSE 8001
ENV PORT=8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

# Comando de inicio (Railway/producción usa start.sh con $PORT dinámico)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]