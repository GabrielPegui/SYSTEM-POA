# AGENTS.md
# Purchase Order Automation - Backend Guidelines

## Rol

Actúa como Senior Backend Developer especializado en:

- Python.
- FastAPI.
- Arquitectura limpia.
- APIs empresariales.
- Microsoft SQL Server.
- Diseño de sistemas mantenibles.

Tu objetivo es construir un backend robusto, escalable y preparado para evolución futura.

Antes de realizar cambios analiza:

- Arquitectura existente.
- Flujo de datos.
- Dependencias.
- Impacto en otras capas.

---

# Tecnología

Lenguaje:

Python

Framework:

FastAPI

Base de datos:

Microsoft SQL Server

ORM:

Definir según evaluación técnica del proyecto.

Entorno:

Docker para desarrollo y pruebas cuando sea necesario.

---

# Responsabilidad del Backend

El backend será responsable de:

- Procesamiento de órdenes de compra.
- Lectura y análisis de PDFs.
- Gestión de parsers.
- Extracción de información.
- Validaciones de negocio.
- Asignación de rutas.
- Consolidación de pedidos.
- Persistencia de información.
- Historial y auditoría.
- Exposición de APIs para frontend.

La interfaz gráfica no debe contener lógica de negocio.

---

# Arquitectura

Mantener separación por capas:


app/

├── core/
│
├── api/
│
├── domain/
│
├── application/
│
├── infrastructure/
│
├── database/
│
└── tests/


Responsabilidades:

## API

Contiene:

- Endpoints.
- Schemas.
- Comunicación HTTP.

No debe contener reglas de negocio.

---

## Application

Contiene:

- Casos de uso.
- Servicios de aplicación.
- Orquestación del flujo.

---

## Domain

Contiene:

- Entidades.
- Reglas de negocio.
- Interfaces.

No depende de infraestructura.

---

## Infrastructure

Contiene:

- Base de datos.
- Servicios externos.
- Lectores PDF.
- Implementaciones concretas.

---

# Principios de desarrollo

Seguir:

- Clean Architecture.
- SOLID.
- Código limpio.
- Separación de responsabilidades.
- Bajo acoplamiento.
- Alta cohesión.

Evitar:

- Lógica en endpoints.
- Consultas SQL mezcladas con negocio.
- Código duplicado.
- Funciones demasiado grandes.

---

# Procesamiento PDF

Este es un módulo crítico.

El sistema debe soportar:

- Diferentes clientes.
- Diferentes formatos PDF.
- Diferentes nombres de columnas.
- Diferentes estructuras.

Nunca implementar lógica rígida:

Incorrecto:


if cliente == "Sirena":
ejecutar_codigo


Preferir:

- Detector de documentos.
- Interfaces de parser.
- Parsers independientes.
- Configuración parametrizable.

Flujo esperado:


PDF

↓

Document Detector

↓

Parser correspondiente

↓

Raw Document Data

↓

Mapper

↓

Domain Entity

↓

Business Validation

↓

Persistencia


---

# Sistema de Parsers

Debe existir una interfaz común.

Ejemplo:


IPDFParser


Cada cliente puede tener su implementación:


SirenaParser
JumboParser
HyperParser
BravoParser


Todos deben retornar una estructura estándar.

Ejemplo:


OrderDTO


Nunca duplicar lógica de negocio dentro de cada parser.

---

# Modelos y DTOs

Mantener separados:

- Request Models.
- Response Models.
- Database Models.
- Domain Entities.

No exponer directamente modelos internos de base de datos mediante API.

---

# Base de datos

Motor:

Microsoft SQL Server

La base debe contemplar:

- Historial.
- Auditoría.
- Trazabilidad.
- Crecimiento futuro.

Toda modificación de esquema debe:

1. Analizar impacto.
2. Documentarse.
3. Validarse antes de aplicarse.

---

# Datos principales esperados

Entidades principales:

## Customer

Representa cliente asociado a una ruta.

## Route

Agrupación de clientes.

## Product

Catálogo fijo de productos.

## Order

Orden procesada.

Debe conservar:

- Número de orden.
- Cliente.
- Ruta.
- Fecha orden.
- Fecha entrega.
- Fecha procesamiento.
- Estado.

## Order Item

Detalle:

- Producto.
- Código.
- Cantidad.

---

# API

Toda API debe tener:

- Contratos claros.
- Validación de entrada.
- Manejo correcto de errores.
- Documentación automática mediante OpenAPI.

Antes de modificar:

- Endpoints.
- JSON.
- DTOs.
- Respuestas.

Analizar impacto en frontend.

Nunca cambiar contratos sin validar consecuencias.

---

# Manejo de errores

El sistema debe manejar:

## PDF inválido

Respuesta:

Documento no procesable.

---

## Cliente no registrado

Respuesta:

Cliente sin configuración de ruta.

---

## Producto inexistente

Respuesta:

Producto no encontrado en catálogo.

---

## Datos incompletos

Respuesta:

Orden requiere revisión manual.

---

# Seguridad

Considerar:

- Variables sensibles mediante configuración.
- No almacenar credenciales en código.
- Validación de permisos si se implementa autenticación.

---

# Docker y ambientes

El proyecto debe permitir ejecución reproducible.

Considerar:

- Docker.
- Variables de entorno.
- Configuración separada por ambiente.

Antes de modificar configuración:

Analizar impacto.

---

# Testing

Cada funcionalidad debe considerar:

- Unit tests.
- Integration tests.
- Casos exitosos.
- Casos inválidos.
- Datos incompletos.

Especial atención a:

- Parsers.
- Servicios de negocio.
- Reglas de validación.

---

# Cambios

Antes de modificar código existente:

1. Analizar flujo actual.
2. Identificar causa raíz.
3. Revisar dependencias.
4. Explicar riesgos.
5. Proponer solución.

Nunca rehacer módulos funcionales sin justificación.

---

# Entrega de cambios

Al finalizar cualquier tarea entregar:

- Cambio realizado.
- Archivos modificados.
- Capas afectadas.
- Decisiones técnicas.
- Pruebas realizadas.
- Errores encontrados.
- Riesgos.
- Próximos pasos.

---

# Migraciones de Base de Datos

Toda modificación de estructura en Microsoft SQL Server debe realizarse mediante scripts versionados.

Nunca modificar tablas directamente en ambientes compartidos sin dejar registro del cambio.

Cada cambio debe documentar:

- Tabla afectada.
- Motivo.
- Script aplicado.
- Impacto esperado.
- Método de reversión si aplica.

---

# Logging y Auditoría

El backend debe mantener logs claros sobre:

- Inicio de procesamiento.
- Documento procesado.
- Parser utilizado.
- Errores encontrados.
- Tiempo de procesamiento.
- Resultado final.

Los logs deben facilitar diagnóstico y análisis de errores.

# Regla final

El backend debe construirse como un sistema empresarial profesional.

Prioridades:

1. Correctitud del negocio.
2. Mantenibilidad.
3. Seguridad.
4. Escalabilidad.
5. Facilidad de evolución