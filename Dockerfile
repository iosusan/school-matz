# Dockerfile
# ─────────────────────────────────────────────────────────────
# Build: python:3.10-slim — imagen base ligera (~130 MB)
# Compatible con amd64 y arm64 (Raspberry Pi 4/5)
# ─────────────────────────────────────────────────────────────
FROM python:3.10-slim

# Dependencias del sistema requeridas por Pillow y reportlab
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    libfreetype6-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar Poetry
RUN pip install --no-cache-dir poetry==2.3.2

# Copiar solo los ficheros de dependencias primero (cacheo eficiente de capas)
COPY pyproject.toml poetry.lock ./

# Instalar dependencias en el Python del sistema (sin venv dentro del contenedor)
RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

# Copiar el código de la aplicación
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Crear directorios de datos (los volúmenes Docker se montarán sobre ellos)
RUN mkdir -p data static/qr static/qr_usuarios

EXPOSE 8000

# PYTHONPATH necesario para que los módulos se importen como "backend.xxx"
ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
