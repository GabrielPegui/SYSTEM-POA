# purchase_order_frontend

Cliente de escritorio (Flutter Desktop) del sistema **Purchase Order Automation**.

## Arquitectura

Clean Architecture + Feature First (ver `../Frontend/AGENTS.md`).

```
lib/
├── core/               # Transversal (config, network, errors, theme, router...)
│   ├── config/
│   ├── constants/
│   ├── errors/
│   ├── network/
│   ├── router/
│   ├── services/
│   ├── state/
│   ├── theme/
│   ├── utils/
│   └── widgets/
└── features/           # Feature First
    ├── order_processing/
    ├── validation/
    ├── history/
    ├── customers/
    ├── products/
    ├── routes/
    └── configuration/
```

Cada feature mantiene su separación interna `data/`, `domain/`, `presentation/`, `application/`.

## Dependencias

- `go_router`: navegación.
- `provider`: manejo de estado.
- `http`: comunicación con la API backend.

## Configuración

La URL base de la API se define en tiempo de compilación:

```bash
flutter run --dart-define=API_BASE_URL=http://localhost:8000
```

## Ejecución

```bash
flutter pub get
flutter run -d windows
```

## Tests

```bash
flutter test
flutter analyze
```
