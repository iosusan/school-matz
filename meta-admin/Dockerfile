FROM python:3.10-slim

# Copiar el binario docker CLI y el plugin compose para poder lanzar
# "docker compose" desde el contenedor.
# Requiere que el socket /var/run/docker.sock esté montado en el contenedor.
COPY --from=docker:27-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:27-cli /usr/local/libexec/docker/cli-plugins/docker-compose \
                           /usr/local/libexec/docker/cli-plugins/docker-compose

WORKDIR /app

RUN pip install --no-cache-dir poetry==2.3.2

COPY pyproject.toml ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --only main

COPY backend/ ./backend/
COPY services/ ./services/
COPY frontend/ ./frontend/

RUN mkdir -p data

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
