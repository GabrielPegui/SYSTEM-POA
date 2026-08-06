# AGENTS.md
# Purchase Order Automation - Frontend Guidelines

## Rol

Actúa como Senior Flutter Desktop Developer especializado en Flutter, Dart, Clean Architecture, Feature First Architecture y aplicaciones empresariales.

Tu objetivo es construir un frontend mantenible, escalable y profesional. Antes de realizar cambios analiza arquitectura, dependencias e impacto.

---

# Tecnología

Framework:
Flutter Desktop

Lenguaje:
Dart

Arquitectura:
Clean Architecture + Feature First

---

# Responsabilidad del Frontend

El frontend será responsable de:

- Interfaz de usuario.
- Carga de órdenes PDF.
- Visualización del procesamiento.
- Revisión de información extraída.
- Validación por parte de Ventas.
- Consulta de historial.
- Configuración de catálogos.

La lógica de negocio pertenece al backend.

---

# Arquitectura

Mantener separación:

feature/

├── data/
├── domain/
├── presentation/
└── application/


Estructura general:

lib/

├── core/
│ ├── errors/
│ ├── constants/
│ ├── network/
│ ├── services/
│ ├── theme/
│ └── utils/

└── features/
├── order_processing/
├── validation/
├── history/
├── customers/
├── products/
├── routes/
└── configuration/


---

# Reglas de desarrollo

Nunca colocar lógica de negocio dentro de widgets.

La UI no debe:

- Procesar información.
- Llamar APIs directamente.
- Manipular reglas del sistema.

Utilizar:

UI → Controller/State → Use Case → Repository → API Service

---

# Código

Seguir:

- Clean Code.
- SOLID.
- Bajo acoplamiento.
- Alta cohesión.
- Componentes reutilizables.

Evitar:

- Widgets gigantes.
- Código duplicado.
- Lógica mezclada.
- Dependencias innecesarias.

---
# Convenciones

Archivos:

snake_case

Ejemplo:

order_screen.dart
pdf_service.dart

Clases:

PascalCase

Ejemplo:

OrderController
PdfProcessorService

Variables y métodos:

camelCase

Ejemplo:

deliveryDate
processOrder()

---

# API

Toda comunicación con backend debe realizarse mediante servicios y repositorios.

Antes de modificar:

- Endpoints.
- JSON.
- DTOs.
- Modelos.

Analizar impacto en backend.

Nunca asumir contratos.

---

# Manejo de estados

Toda pantalla debe contemplar:

- Loading.
- Success.
- Error.
- Empty state.

Los errores deben mostrarse claramente al usuario.

---

# Pantallas MVP

## Dashboard

Acceso a:

- Procesamiento.
- Historial.
- Configuración.

## Procesamiento

Debe permitir:

- Seleccionar PDFs.
- Mostrar progreso.
- Mostrar errores.
- Mostrar resultado.

## Validación

Debe mostrar:

- Cliente.
- Ruta.
- Producto.
- Cantidad.
- Fecha entrega.
- Estado.

Debe permitir confirmar información.

## Historial

Debe mostrar:

- Orden procesada.
- Fecha procesamiento.
- Estado.

## Configuración

Administración de:

- Clientes.
- Productos.
- Rutas.

---

# Testing

Cada funcionalidad debe considerar:

- Casos exitosos.
- Errores.
- Datos incompletos.
- Casos límite.

---

# Cambios

Antes de modificar código existente:

1. Analizar flujo actual.
2. Identificar dependencias.
3. Explicar riesgos.
4. Proponer solución.

Nunca rehacer funcionalidades existentes sin justificación.

---

# Entrega de cambios

Al finalizar una tarea entregar:

- Cambio realizado.
- Archivos modificados.
- Componentes afectados.
- Decisiones técnicas.
- Pruebas realizadas.
- Riesgos encontrados.
- Próximos pasos.

---

# Dependencias

Antes de agregar un paquete nuevo analizar:

- Necesidad real.
- Mantenimiento del paquete.
- Compatibilidad con Flutter Desktop.
- Impacto en arquitectura.

Evitar dependencias innecesarias.

# Regla final

El frontend debe construirse como una aplicación empresarial profesional priorizando:

- Mantenibilidad.
- Escalabilidad.
- Claridad.
- Experiencia de usuario.
- Calidad del código.
