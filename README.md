# demo-api

> API mínima en Python que sirve de sujeto de pruebas a la plataforma:
> se construye en CI, se publica en GHCR y se despliega por GitOps.

## Estado

**Fase 3 en curso.** App funcional, 11 tests en verde.

## Endpoints

| Ruta | Devuelve | Propósito |
|---|---|---|
| `/` | `{status, version, service}` | Identidad del pod: qué servicio es y qué versión corre |
| `/livez` | `{status: "ok"}` | **Liveness.** No consulta dependencias: un fallo de la BD reiniciaría el pod en bucle |
| `/readyz` | `{status: "ok"}` | **Readiness.** Aquí irá la comprobación de la BD; si falla → `503` y el pod sale del Service sin reiniciarse |
| `/metrics` | Texto Prometheus | Scrapeado por Prometheus |
| `/docs` | Swagger UI | Documentación autogenerada por FastAPI |

## Stack

- Python 3.12 · FastAPI + uvicorn
- `prometheus-client` para métricas
- pytest + httpx (solo desarrollo)
- Docker multi-stage, usuario non-root (fase 4)

## Cómo reproducirlo

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload

## Imagen de contenedor

<!-- TODO: por que multi-stage y por que non-root. -->

## CI/CD

<!-- TODO: que hace el pipeline y por que NO despliega (ver ADR de GitOps). -->
