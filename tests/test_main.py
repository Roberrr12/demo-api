"""Tests de demo-api (fase 3).

Cada test verifica una expectativa definida ANTES de escribir el código.
Si uno falla, es que la app no cumple el contrato -- no que el test esté mal.
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main
from app.main import REQUEST_COUNT, app  # noqa: F401  (app se usa en cliente)

cliente = TestClient(app)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def valor_counter(method: str, path: str, status: str) -> float:
    """Valor actual del contador para esa combinación de labels.

    Se lee ANTES y DESPUÉS y se comparan diferencias, porque el contador
    es global: sobrevive de un test al siguiente. Si se comparara contra
    un valor absoluto, el resultado dependería del orden de ejecución.
    """
    hijo = REQUEST_COUNT.labels(method=method, path=path, status=status)
    for muestra in hijo.collect()[0].samples:
        if muestra.name.endswith("_total"):
            return muestra.value
    return 0.0


def rutas_contabilizadas() -> set:
    """Todas las rutas que tienen al menos una serie en el contador."""
    rutas = set()
    for metrica in REQUEST_COUNT.collect():
        for muestra in metrica.samples:
            if muestra.name.endswith("_total"):
                rutas.add(muestra.labels.get("path"))
    return rutas


# --------------------------------------------------------------------------
# 1. /  -> 200 y las tres claves
# --------------------------------------------------------------------------

def test_raiz_devuelve_200_y_los_tres_campos():
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200

    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["version"] == main.APP_VERSION
    assert cuerpo["service"] == "demo-api"


# --------------------------------------------------------------------------
# 2. La versión se refleja y se lee de la variable de entorno
# --------------------------------------------------------------------------

def test_version_se_refleja_en_la_respuesta(monkeypatch):
    """/ devuelve lo que valga APP_VERSION, no un literal fijo."""
    monkeypatch.setattr(main, "APP_VERSION", "abc123")
    assert cliente.get("/").json()["version"] == "abc123"


def test_version_se_lee_de_la_variable_de_entorno(monkeypatch):
    """La versión entra por entorno: así el CI inyecta el SHA del commit."""
    monkeypatch.setenv("APP_VERSION", "sha-abc123")
    assert main.leer_version() == "sha-abc123"


def test_version_tiene_fallback_si_no_hay_entorno(monkeypatch):
    """Sin APP_VERSION definida, la app arranca igual (no revienta)."""
    monkeypatch.delenv("APP_VERSION", raising=False)
    assert main.leer_version() == "dev"


# --------------------------------------------------------------------------
# 3 y 4. Probes
# --------------------------------------------------------------------------

def test_livez_responde_200():
    respuesta = cliente.get("/livez")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_readyz_responde_200():
    respuesta = cliente.get("/readyz")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


# --------------------------------------------------------------------------
# 5. /metrics -> 200 y formato Prometheus
# --------------------------------------------------------------------------

def test_metrics_responde_200_con_formato_prometheus():
    respuesta = cliente.get("/metrics")
    assert respuesta.status_code == 200

    # "text/plain" es el formato de exposición de Prometheus.
    # Prometheus RECHAZA el scrape si el Content-Type no es este.
    assert "text/plain" in respuesta.headers["content-type"]

    # Y el cuerpo tiene que llevar la métrica que declaramos.
    assert "http_requests_total" in respuesta.text


# --------------------------------------------------------------------------
# 6. EL TEST QUE CIERRA LA FASE: el contador sube de verdad
# --------------------------------------------------------------------------

def test_el_contador_sube_exactamente_uno_tras_una_peticion():
    antes = valor_counter("GET", "/", "200")

    assert cliente.get("/").status_code == 200

    despues = valor_counter("GET", "/", "200")
    assert despues - antes == 1


# --------------------------------------------------------------------------
# 7. /metrics y los probes NO se cuentan a sí mismos (salida temprana)
# --------------------------------------------------------------------------

def test_metrics_y_probes_no_se_contabilizan():
    cliente.get("/metrics")
    cliente.get("/metrics")
    cliente.get("/livez")
    cliente.get("/readyz")

    rutas = rutas_contabilizadas()

    assert "/metrics" not in rutas
    assert "/livez" not in rutas
    assert "/readyz" not in rutas


# --------------------------------------------------------------------------
# 8. La Gauge vuelve a cero (verifica que el 'finally' decrementa)
# --------------------------------------------------------------------------

def test_la_gauge_vuelve_a_cero_despues_de_la_peticion():
    from app.main import ACTIVE_REQUESTS

    cliente.get("/")
    for metrica in ACTIVE_REQUESTS.collect():
        for muestra in metrica.samples:
            if muestra.name == "http_active_requests":
                assert muestra.value == 0


# --------------------------------------------------------------------------
# 9. El detalle fino del middleware: una excepción cuenta como 500
# --------------------------------------------------------------------------

def test_excepcion_se_contabiliza_como_500():
    from app.main import metrics_middleware

    app_test = FastAPI()
    app_test.middleware("http")(metrics_middleware)

    @app_test.get("/boom")
    def boom():
        raise RuntimeError("explota")

    # raise_server_exceptions=False -> queremos el 500, no la excepción.
    cliente_test = TestClient(app_test, raise_server_exceptions=False)

    antes = valor_counter("GET", "/boom", "500")
    respuesta = cliente_test.get("/boom")
    despues = valor_counter("GET", "/boom", "500")

    assert respuesta.status_code == 500
    assert despues - antes == 1