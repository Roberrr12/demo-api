import os
import time

from fastapi import FastAPI, Request
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app

APP_VERSION = os.getenv("APP_VERSION", "dev")
SERVICE = "demo-api"

app = FastAPI(version=APP_VERSION, title=SERVICE)


@app.get("/")
def general_info():
    return {"status": "ok", "version": APP_VERSION, "service": SERVICE}


@app.get("/livez")
def livez():
    return {"status": "ok"}


@app.get("/readyz")
def readyz():
    # Aquí irá la comprobación de la base de datos.
    # Si no está lista: raise HTTPException(status_code=503, detail="db not ready")
    return {"status": "ok"}


REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests.",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "path"],
)
ACTIVE_REQUESTS = Gauge(
    "http_active_requests", "Number of in-flight HTTP requests."
)

EXCLUDED_PATHS = {"/metrics", "/livez", "/readyz"}


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Salida temprana: no medir el scrape de Prometheus ni los probes
    if request.url.path.startswith("/metrics") or request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    ACTIVE_REQUESTS.inc()
    start = time.perf_counter()
    status = 500  # si call_next lanza excepción, se contabiliza como 5xx
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start
        # Plantilla de ruta (/items/{id}), no la URL real. Sin ruta (404) -> fallback fijo.
        route = request.scope.get("route")
        path = route.path if route else "unmatched"

        REQUEST_COUNT.labels(request.method, path, str(status)).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(duration)
        ACTIVE_REQUESTS.dec()


app.mount("/metrics", make_asgi_app())