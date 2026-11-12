# ---------- Etapa 1: builder ----------
FROM python:3.12-slim AS builder
WORKDIR /build

# Crea un virtualenv y instala dependencias dentro
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Etapa 2: runtime ----------
FROM python:3.12-slim
WORKDIR /usr/local/app

# Copia SOLO el venv ya instalado desde builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Usuario no root
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-log-init --create-home app

COPY --chown=10001:10001 app/ ./app

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/livez')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]