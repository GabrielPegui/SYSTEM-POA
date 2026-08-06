# ADR-003 - Database Strategy

## Estado

Aceptado

## Fecha

2026-08-06

## Contexto

El sistema Purchase Order Automation requiere almacenar información relacionada con:

- Órdenes de compra procesadas.
- Clientes.
- Rutas.
- Productos.
- Detalles de pedidos.
- Historial de procesamiento.
- Errores encontrados.
- Validaciones realizadas.

Actualmente la empresa cuenta con infraestructura propia y utilizará su servidor interno para alojar la base de datos.

El motor definido por la empresa es:

Microsoft SQL Server.

La solución debe garantizar:

- Persistencia confiable.
- Auditoría.
- Trazabilidad.
- Historial operativo.
- Capacidad de crecimiento futuro.

---

# Decisión

Se utilizará Microsoft SQL Server como motor principal de base de datos del sistema.

La base de datos estará alojada en la infraestructura existente de la empresa.

El backend FastAPI será el único componente autorizado para comunicarse directamente con la base de datos.

El flujo será:

Flutter Desktop

↓

API FastAPI

↓

Application Layer

↓

Infrastructure Layer

↓

Microsoft SQL Server

---

# Principios de diseño

La base de datos debe diseñarse considerando:

## Trazabilidad

El sistema debe permitir conocer:

- Qué orden fue procesada.
- Cuándo fue procesada.
- Quién realizó la validación.
- Qué resultado tuvo el procesamiento.

---

## Auditoría

Los cambios importantes deben conservar información histórica.

Ejemplos:

- Procesamiento exitoso.
- Error de lectura.
- Validación manual.
- Rechazo de información.

---

## Integridad de datos

La información almacenada debe mantener consistencia entre:

- Cliente.
- Ruta.
- Producto.
- Orden.
- Detalle de pedido.

---

# Modelo conceptual inicial

Las entidades principales serán:

## Customer

Representa los clientes que generan órdenes de compra.

Campos esperados:

- Id.
- Nombre.
- Ruta asociada.
- Estado.

---

## Route

Representa las rutas utilizadas para distribución.

Campos esperados:

- Id.
- Nombre.
- Estado.

Relación:

Una ruta puede tener múltiples clientes.

---

## Product

Representa el catálogo de productos.

Campos esperados:

- Id.
- Código.
- EAN.
- Descripción.
- Estado.

---

## Order

Representa una orden de compra procesada.

Debe almacenar:

- Número de orden.
- Cliente.
- Ruta.
- Fecha de orden.
- Fecha de entrega.
- Fecha de procesamiento.
- Estado.

Estados posibles:

- Procesada.
- Pendiente validación.
- Validada.
- Error.

---

## Order Item

Representa los productos dentro de una orden.

Debe almacenar:

- Orden relacionada.
- Producto.
- Cantidad.

---

## Processing History

Permite auditoría del procesamiento documental.

Debe almacenar:

- Archivo procesado.
- Fecha procesamiento.
- Resultado.
- Error encontrado.
- Mensaje técnico.

---

# Separación de modelos

No se expondrán directamente las tablas de base de datos mediante la API.

La separación será:

Database Model

↓

Domain Entity

↓

Response DTO

↓

Frontend


Esto evita acoplamiento entre base de datos y aplicación.

---

# Migraciones y cambios de esquema

Toda modificación estructural de base de datos debe:

1. Analizar impacto.
2. Documentar el cambio.
3. Validar compatibilidad con backend.
4. Probar antes de aplicar en ambiente productivo.

No realizar cambios directos sin control.

---

# Ambiente de desarrollo

Durante desarrollo se utilizará Docker cuando sea necesario para:

- Levantar ambientes locales.
- Realizar pruebas.
- Mantener consistencia entre desarrolladores.

La configuración productiva utilizará la infraestructura SQL Server existente de la empresa.

---

# Alternativas consideradas

## SQLite local

Descartada como base principal.

Motivos:

- No permite centralización de información.
- Dificulta auditoría compartida.
- Limitada para múltiples usuarios.

Puede utilizarse únicamente para pruebas locales si fuese necesario.

---

## PostgreSQL

Descartada.

Motivo:

La empresa ya posee infraestructura Microsoft SQL Server y se busca aprovechar recursos existentes.

---

## Microsoft SQL Server

Aceptada.

Motivos:

- Tecnología existente en la empresa.
- Infraestructura disponible.
- Soporte empresarial.
- Integración futura con ecosistema Microsoft.
- Capacidad suficiente para el MVP y crecimiento.

---

# Impacto

Beneficios:

- Aprovechamiento de infraestructura existente.
- Menor costo operativo.
- Mayor control de información.
- Auditoría completa.
- Preparación para futuras fases.

Consideraciones:

- Requiere correcta configuración de acceso.
- Requiere manejo seguro de credenciales.
- Requiere coordinación con infraestructura de la empresa.

---

# Reglas futuras

Cualquier cambio relacionado con:

- Nuevas entidades.
- Modificación de tablas.
- Relaciones.
- Índices.
- Migraciones.

Debe evaluarse considerando impacto en:

- Backend.
- API.
- Frontend.
- Datos existentes.

La base de datos debe evolucionar de forma controlada.