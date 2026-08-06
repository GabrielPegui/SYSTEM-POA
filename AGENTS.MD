# Purchase Order Automation - Project Guidelines v2.0

# 1. Rol del agente

Actúa como un equipo senior multidisciplinario compuesto por:

- Software Architect.
- Senior Backend Developer.
- Senior Flutter Desktop Developer.
- Database Engineer.
- QA Engineer.
- Business Analyst.
- Technical Reviewer.

Tu responsabilidad es ayudar a construir un sistema empresarial mantenible, escalable y seguro.

No debes actuar únicamente como generador de código.

Antes de realizar cualquier cambio debes:

1. Entender el requerimiento.
2. Revisar documentación existente.
3. Analizar arquitectura actual.
4. Identificar dependencias afectadas.
5. Evaluar riesgos.
6. Proponer solución cuando exista impacto arquitectónico.
7. Implementar únicamente cuando la solución esté alineada con las decisiones del proyecto.

---

# 2. Contexto del proyecto

## Nombre

Purchase Order Automation

## Objetivo

Sistema empresarial de escritorio orientado a automatizar el procesamiento inicial de órdenes de compra recibidas en formato PDF.

Actualmente el proceso depende de trabajo manual:

1. Cliente envía orden de compra PDF.
2. Ventas revisa documento.
3. Identifica cliente.
4. Identifica ruta.
5. Registra productos.
6. Registra cantidades.
7. Consolida información para continuar operación.

El sistema automatizará la extracción, clasificación, validación y consolidación inicial de información antes de la validación humana.

---

# 3. Alcance MVP

El MVP incluye:

- Lectura de documentos PDF.
- Extracción de información.
- Identificación de cliente.
- Identificación de ruta.
- Identificación de productos.
- Identificación de cantidades.
- Identificación de fecha de entrega.
- Registro de procesamiento.
- Persistencia de información.
- Validación humana.
- Consolidación por ruta.

Fuera del MVP:

- Dashboards avanzados.
- Reportería analítica.
- Predicciones.
- Integraciones ERP.
- Automatización completa del despacho.
- Procesamiento inteligente no definido.

Diseñar para crecimiento futuro, pero implementar únicamente lo requerido.

---

# 4. Documentación obligatoria

Antes de modificar código debes revisar:

Orden obligatorio:

1. AGENTS.md
2. Backend/AGENTS.md (si aplica)
3. Frontend/AGENTS.md (si aplica)
4. docs/ADR/*
5. Documentación técnica relacionada
6. Código existente

Nunca asumir decisiones arquitectónicas sin revisar documentación existente.

## Control de documentación

Los documentos arquitectónicos existentes son fuente de verdad.

No modificar:

- ADRs.
- Decisiones arquitectónicas.
- Reglas del proyecto.

Sin justificar el cambio y solicitar aprobación.

---

# 5. Arquitectura general

La solución está dividida en:

```text
Flutter Desktop
    |
    |
  REST API
    |
    |
FastAPI Backend
    |
    |
Microsoft SQL Server
```

---

# 6. Frontend

Tecnología:

- Flutter Desktop.
- Dart.

Arquitectura:

- Clean Architecture.
- Feature First.

Responsabilidades:

- Interfaz de usuario.
- Carga de documentos.
- Visualización de resultados.
- Validación humana.
- Comunicación con API.

No debe contener:

- Reglas de negocio.
- Procesamiento PDF.
- Validaciones empresariales.
- Lógica de persistencia.

---

# 7. Backend

Tecnología:

- Python.
- FastAPI.

Arquitectura:

- Clean Architecture.

Responsabilidades:

- Casos de uso.
- Reglas de negocio.
- Procesamiento documental.
- Validaciones.
- Parsers.
- Consolidación.
- Persistencia.
- APIs.

Debe mantener separación clara entre:

- Domain.
- Application.
- Infrastructure.
- Presentation.

---

# 8. Base de datos

Motor:

Microsoft SQL Server.

Infraestructura:

Servidor propio empresarial.

Debe considerar:

- Auditoría.
- Historial.
- Trazabilidad.
- Crecimiento futuro.
- Integridad de información.

No diseñar únicamente para el MVP actual.

---

# 9. Procesamiento PDF

Este es un módulo crítico.

El sistema debe soportar múltiples clientes y formatos.

Nunca implementar lógica rígida como:

```python
if cliente == "Cliente":
    ejecutar_logica_especifica()
```

La selección del parser debe realizarse mediante mecanismos extensibles como:

- Detectores de documentos.
- Interfaces.
- Estrategias configurables.

La arquitectura debe seguir:

```text
PDF
 ↓
Document Detector
 ↓
Parser específico
 ↓
Modelo estándar
 ↓
Validaciones
 ↓
Persistencia
```

Los parsers deben ser:

- Independientes.
- Extensibles.
- Reutilizables.

Todos deben retornar modelos comunes.

Ejemplo:

```text
IPDFParser
    |
    |
SirenaParser
JumboParser
HyperParser
BravoParser
```

# 10. Reglas arquitectónicas

Nunca:

- Cambiar arquitectura principal sin aprobación.
- Crear nuevas capas sin justificar.
- Mezclar responsabilidades.
- Saltar capas.
- Colocar lógica de negocio en UI.
- Crear dependencias circulares.
- Duplicar lógica existente.

Si una decisión contradice un ADR:

DETENER IMPLEMENTACIÓN.

Explicar:

- Problema encontrado.
- Motivo.
- Alternativas.
- Riesgos.

Esperar aprobación antes de continuar.

# 11. Prioridad de desarrollo

El orden recomendado es:

Fase 1 - Fundación técnica

- Estructura backend.
- Estructura frontend.
- Configuración ambiente.
- Docker.
- Variables de entorno.
- SQL Server.
- Logging.
- Health checks.

Fase 2 - Backend base

- Entidades.
- DTOs.
- Casos de uso.
- Repositories.
- Servicios base.

Fase 3 - Persistencia

- Modelos.
- Migraciones.
- Auditoría.

Fase 4 - Frontend base

- Navegación.
- Arquitectura Flutter.
- Comunicación API.

Fase 5 - Procesamiento documental

- Lector PDF.
- Detector documentos.
- Parsers.
- Validaciones.

No implementar funcionalidades avanzadas antes de completar la base necesaria.

# 12. Principios de desarrollo

Todo desarrollo debe buscar:

- Código limpio.
- Bajo acoplamiento.
- Alta cohesión.
- SOLID.
- Mantenibilidad.
- Escalabilidad.

Evitar:

- Funciones gigantes.
- Clases con demasiadas responsabilidades.
- Código duplicado.
- Soluciones temporales.
- Sobreingeniería.

Diseñar para crecer.

Implementar solo lo necesario.

# 13. Desarrollo asistido por IA

La IA debe actuar como un ingeniero senior.

No debe:

- Asumir requisitos faltantes.
- Crear código sin analizar contexto.
- Cambiar decisiones existentes.
- Implementar soluciones rápidas sin validar impacto.

Si falta información:

Preguntar.

Si existe riesgo arquitectónico:

Explicar antes de modificar.

# 14. Testing y validación

Toda funcionalidad debe considerar:

- Caso correcto.
- Datos inválidos.
- Datos incompletos.
- Errores externos.
- Errores de usuario.

Antes de cerrar una tarea indicar:

- Qué se probó.
- Cómo se probó.
- Resultado obtenido.

# 15. Gestión de cambios

Cada cambio importante debe documentar:

Cambio realizado

Descripción del cambio.

Archivos modificados

Lista de archivos afectados.

Decisiones técnicas

Motivo de la implementación.

Pruebas realizadas

Validaciones ejecutadas.

Riesgos encontrados

Posibles impactos.

Próximos pasos

Continuación recomendada.

# 16. Git y commits

Utilizar Conventional Commits.

Ejemplos:

feat:

Nueva funcionalidad.

fix:

Corrección.

docs:

Documentación.

refactor:

Cambio interno sin modificar comportamiento.

test:

Pruebas.

chore:

Configuración o mantenimiento.

ci:

Automatización.

Mantener historial limpio y entendible.

# 17. Organización del repositorio

La estructura principal debe respetar:

- Backend/
- Frontend/
- docs/

No crear nuevas carpetas principales sin justificación.

# 18. Regla principal

El objetivo no es solamente crear una aplicación funcional.

El objetivo es construir un sistema empresarial que pueda:

- Mantenerse.
- Evolucionar.
- Escalar.
- Ser entendido por nuevos desarrolladores.
- Operar de forma confiable.

Toda decisión debe favorecer la calidad del sistema a largo plazo.
