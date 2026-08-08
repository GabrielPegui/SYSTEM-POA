# purchase-order-automation

Sistema empresarial de escritorio para automatizar el procesamiento inicial de órdenes de compra recibidas en PDF.

## Stack

- **Frontend**: Flutter Desktop (Clean Architecture + Feature First) — `Frontend/`
- **Backend**: FastAPI / Python (Clean Architecture) — `Backend/`
- **Base de datos**: Microsoft SQL Server

## Estructura

```
Backend/
├── app/
│   ├── core/           # Config, logging, utilidades transversales
│   ├── api/            # Endpoints y schemas HTTP
│   ├── domain/         # Entidades, interfaces y reglas de negocio
│   ├── application/    # Casos de uso y servicios de aplicación
│   ├── infrastructure/ # Repositorios, parsers PDF, servicios externos
│   ├── database/       # Conexión SQL Server y migraciones
│   └── tests/
├── Dockerfile
└── requirements.txt

Frontend/
└── lib/
    ├── core/           # Config, network, errors, theme, router...
    └── features/       # Feature First (order_processing, validation, history, ...)

docs/                   # ADRs y documentación técnica (fuente de verdad)
docker-compose.yml      # Ambiente de desarrollo (SQL Server + backend)
```

## Inicio rápido (desarrollo)

1. Copiar `.env.example` a `.env` y ajustar credenciales.
2. Levantar infraestructura: `docker compose up -d mssql`.
3. Crear la base y aplicar migraciones (desde `Backend/`):
   ```
   python -m app.database.create_database
   alembic upgrade head
   ```
4. Backend disponible en `http://localhost:8000` (docs en `/docs`, health en `/health`).
5. Frontend: `cd Frontend && flutter run -d windows`.

## Documentación de referencia

- `AGENTS.md` (raíz, `Backend/`, `Frontend/`).
- `docs/ADR_001_arquitectura.md`, `docs/ADR_002_parser_strategy.md`, `docs/ADR_003_database.md`.
