# demo-api

> API minima en Python que sirve de sujeto de pruebas a la plataforma:
> se construye en CI, se publica en GHCR y se despliega por GitOps.

## Estado

En construccion. Fase 3.

## Endpoints

| Ruta | Proposito |
|---|---|
| `/` | Respuesta basica |
| `/healthz` | Sonda de salud para Kubernetes |
| `/metrics` | Metricas para Prometheus |
| `/docs` | Documentacion autogenerada |

## Stack

- Python
- FastAPI + uvicorn
- pytest
- prometheus-client
- Docker (multi-stage, usuario non-root)

## Como reproducirlo

<!-- TODO -->

## Desarrollo local

<!-- TODO -->

## Tests

<!-- TODO: como ejecutarlos y que cubren. -->

## Imagen de contenedor

<!-- TODO: por que multi-stage y por que non-root. -->

## CI/CD

<!-- TODO: que hace el pipeline y por que NO despliega (ver ADR de GitOps). -->
