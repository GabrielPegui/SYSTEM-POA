# ADR-001 - Arquitectura General del Sistema

## Estado

Aceptado

## Fecha

[8-6-2026]

## Contexto

El proyecto Purchase Order Automation requiere desarrollar un sistema empresarial para automatizar el procesamiento de órdenes de compra recibidas en formato PDF.

El sistema debe:

- Leer documentos PDF de diferentes clientes.
- Extraer información variable según el formato del documento.
- Identificar clientes, productos, cantidades y fechas de entrega.
- Asignar rutas automáticamente.
- Consolidar información.
- Permitir validación humana antes de continuar el proceso operativo.

Debido a la naturaleza del sistema, se requiere una arquitectura que permita:

- Mantenimiento a largo plazo.
- Crecimiento futuro.
- Separación clara de responsabilidades.
- Facilidad para incorporar nuevos formatos de documentos.
- Bajo acoplamiento entre componentes.

---

# Decisión

Se implementará una arquitectura separada en tres componentes principales:

## Frontend

Aplicación Desktop desarrollada con Flutter.

Responsabilidades:

- Interfaz de usuario.
- Carga de archivos PDF.
- Visualización de resultados.
- Validación por parte de Ventas.
- Consulta de información procesada.

El frontend no contendrá lógica de negocio.

---

## Backend

API desarrollada con FastAPI.

Responsabilidades:

- Procesamiento de órdenes.
- Lectura y análisis de documentos.
- Gestión de parsers.
- Reglas de negocio.
- Validaciones.
- Consolidación.
- Comunicación con base de datos.

El backend será el responsable principal de la lógica del sistema.

---

## Base de datos

Microsoft SQL Server.

Responsabilidades:

- Persistencia de información.
- Historial de procesamiento.
- Auditoría.
- Trazabilidad.
- Información operacional.

La base de datos estará alojada en infraestructura propia de la empresa.

---

# Patrón arquitectónico seleccionado

Se utilizará Clean Architecture.

La separación interna del backend será:
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

## Core

Contiene configuraciones transversales:

- Variables de ambiente.
- Configuración del sistema.
- Logging.
- Seguridad.
- Utilidades compartidas.


## API

Capa de presentación HTTP.

Responsable de:

- Endpoints.
- Request schemas.
- Response schemas.
- Manejo HTTP.

No contiene reglas de negocio.


## Application

Contiene:

- Casos de uso.
- Orquestación del flujo.
- Servicios de aplicación.


## Domain

Contiene:

- Entidades.
- Value Objects.
- Interfaces.
- Reglas de negocio.

No depende de ninguna capa externa.


## Infrastructure

Contiene implementaciones concretas:

- Repositorios SQL Server.
- Lectores PDF.
- Servicios externos.


## Database

Contiene:

- Configuración de conexión.
- Migraciones.
- Scripts versionados.

# Principios arquitectónicos

El sistema seguirá los siguientes principios:

- Separación de responsabilidades.
- Bajo acoplamiento.
- Alta cohesión.
- Dependencias dirigidas hacia el dominio.
- Independencia entre frontend, backend y persistencia.