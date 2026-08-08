# ADR-002 - Estrategia de Procesamiento y Parsers de Órdenes PDF

## Estado

Aceptado

## Fecha

[Completar fecha]

---

# Contexto

El sistema Purchase Order Automation debe procesar órdenes de compra recibidas en formato PDF provenientes de diferentes clientes.

Durante el análisis inicial se identificaron múltiples formatos documentales. Aunque todas las órdenes contienen información funcional similar:

- Cliente.
- Número de orden.
- Productos.
- Cantidades.
- Fecha de entrega.

La estructura del documento puede variar dependiendo del cliente:

- Diferentes nombres de columnas.
- Diferentes posiciones de información.
- Diferentes estructuras de tablas.
- Diferentes formatos de cantidad.
- Documentos con múltiples páginas.
- Productos distribuidos en varias líneas.

En el corpus actual de análisis se dispone de 9 PDFs de muestra:

- 7 contienen texto extraíble.
- 2 son PDFs escaneados/sin texto.

Los 7 PDFs legibles representan aproximadamente 5–6 estructuras documentales principales, que sirven como base para el MVP y el desarrollo inicial de parsers.

Esto no significa que en el futuro solo existan 5–6 formatos posibles. Nuevos clientes o variaciones pueden requerir estructuras adicionales; cada formato real se incorporará como un parser propio cuando aparezca.

No se debe crear artificialmente un parser por cada PDF del corpus; los parsers del MVP cubrirán las estructuras principales identificadas.

Cada cliente puede mantener una estructura propia aunque pertenezca al mismo flujo operativo del negocio.

---

# Problema identificado

Implementar una lectura basada únicamente en reglas fijas generaría un sistema difícil de mantener y escalar.

Ejemplo de una implementación incorrecta:


Si cliente = Cliente A
leer columna X

Si cliente = Cliente B
leer columna Y

Si cliente = Cliente C
leer columna Z


Este enfoque provocaría:

- Código duplicado.
- Alto acoplamiento.
- Dificultad para agregar nuevos clientes.
- Mayor riesgo de errores.
- Mayor costo de mantenimiento.

---

# Decisión

Se implementará una arquitectura basada en:

- Servicio de lectura PDF.
- Detector de documentos.
- Interfaz común de parser.
- Parsers independientes por formato de cliente.
- Modelo estándar de salida.

El objetivo es separar la interpretación del documento de las reglas de negocio del sistema.

---

# Flujo definido

El procesamiento seguirá el siguiente flujo:


PDF recibido

↓

PDF Reader

↓

Document Detector

↓

Parser específico

↓

Raw Document Data

↓

Mapper

↓

Order Entity

↓

Validaciones de negocio

↓

Persistencia


---

# Componentes principales

## PDF Reader

Responsabilidad:

Extraer información técnica del documento.

Funciones:

- Leer contenido PDF.
- Extraer texto.
- Detectar tablas.
- Mantener información estructural.
- Preparar información para análisis.

No debe contener lógica específica de clientes.

---

## Document Detector

Responsabilidad:

Determinar qué parser debe utilizarse.

Puede utilizar:

- Nombre del cliente.
- Palabras clave.
- Encabezados.
- Estructura del documento.
- Patrones identificados.

Ejemplo:

Entrada:


PDF


Resultado:


Cliente detectado:
Sirena

Parser:
SirenaParser


---

## Interfaz de Parser

Todos los parsers deberán implementar una interfaz común.

Ejemplo conceptual:


IPDFParser


Responsabilidad:

Transformar un documento específico en una estructura estándar utilizada por el sistema.

---

# Parsers específicos

Cada formato tendrá su propia implementación independiente.

Ejemplo:


Parsers

├── SirenaParser
├── HyperParser
├── BravoParser
├── JumboParser
└── ClienteParser


Cada parser será responsable únicamente de:

- Interpretar la estructura del documento.
- Ubicar campos.
- Extraer información.
- Transformar datos.

Los parsers no deben contener reglas de negocio.

---

# Modelo estándar de salida

Sin importar el formato recibido, todos los parsers deben entregar una estructura común.

El modelo concreto es `PurchaseOrderDocument` (ver `backend/app/domain/document_processing/purchase_order.py`), que representa el resultado normalizado de extracción:

```text
PurchaseOrderDocument {
  orderNumber,
  customerCode?,
  customerName?,
  routeCode?,
  orderDate?,
  deliveryDate?,
  items[]
}
```

Cada línea:

```text
PurchaseOrderItemDocument {
  description,
  quantity (int),
  pdfCode?,
  ean?,
  uom?,
  unitPrice (Decimal)?,
  total (Decimal)?,
  unitsPerPack?,
  lineNumber?
}
```

Reglas del modelo estándar:

- `quantity` es siempre un entero (`int`); los valores monetarios (`unit_price`, `total`) son siempre `Decimal`.
- Los campos opcionales (`?`) se llenan únicamente si la información existe en el PDF.
- `pdf_code` / `ean` son identificadores extraídos del documento y quedan como trazabilidad; **no** son claves del catálogo.
- El parser extrae; **no** realiza matching contra la base de datos, **no** decide qué `Product` del catálogo corresponde y **nunca** crea entidades.

Esto permite que el resto del sistema sea independiente del formato original del documento.

## Matching como paso separado (pre-Sprint 7)

La correspondencia entre una línea extraída y el catálogo es responsabilidad de un `ProductMatcher` (ver `backend/app/domain/interfaces/matching.py`), no del parser. El resultado es `MatchResult` y expresa tres estados:

- `MATCHED`: evidencia suficiente para elegir un producto del catálogo.
- `REVIEW_REQUIRED`: hay candidatos pero la confianza no es suficiente; requiere revisión humana.
- `NO_MATCH`: no se encontró candidato.

Regla de seguridad: **nunca** crear silenciosamente un producto/cliente/ruta porque el matching no fue concluyente. Un match dudoso termina en `REVIEW_REQUIRED`; la persistencia solo ocurre después de resolver correctamente la correspondencia.

---

# Manejo de variaciones documentales

Las diferencias entre clientes deberán resolverse dentro del parser correspondiente.

Ejemplos:

Cantidad:


Cantidad
Cant
N. Cajas


deben convertirse a:


quantity


Fecha:


Fecha Entrega
Fecha Vencimiento
Fecha de entrega


deben convertirse a:


deliveryDate


El sistema trabajará internamente con nombres y estructuras estándar.

---

# Regla fundamental de interpretación de datos

El parser debe identificar primero el **campo/columna y su significado**, y posteriormente interpretar el **valor**. Nunca debe inferir el significado de un número únicamente por su apariencia, formato decimal o proximidad a una unidad de medida.

Ejemplo conceptual:

```text
Cantidad = 20
UOM = PAQ
Precio/U = 192.50
Total = 3,850.00
```

En este caso:

- `20` = cantidad solicitada.
- `PAQ` = unidad de medida.
- `192.50` = precio unitario.
- `3,850.00` = total.

El hecho de que `192.50` sea decimal **no significa que sea una cantidad fraccionaria**. La decisión del tipo de campo (entero o decimal) depende del significado del campo, no de cómo aparece el valor en el documento.

Esta es una regla de diseño del parser: evita errores futuros en parsers nuevos y debe aplicarse en todas las implementaciones.

---

# Documentos no procesables

Si un documento no puede ser interpretado correctamente, el sistema debe:

- Registrar el error.
- Mantener trazabilidad.
- Indicar el motivo.
- Permitir revisión manual.

Ejemplo:


Orden requiere revisión manual:
Formato no reconocido


---

# Manejo de PDFs imagen

Durante el análisis inicial se identificaron algunos documentos enviados como imagen.

Decisión inicial:

El MVP priorizará PDFs con texto extraíble.

Los documentos imagen serán considerados como una extensión futura mediante:

- OCR.
- Procesamiento adicional de imágenes.

Estas excepciones no deben retrasar el desarrollo principal.

---

# Alternativas consideradas

## Alternativa 1 - Un único parser general

Descripción:

Crear un parser capaz de interpretar todos los formatos.

Motivo de rechazo:

Generaría:

- Código complejo.
- Muchas condiciones especiales.
- Difícil mantenimiento.
- Mayor probabilidad de errores.

---

## Alternativa 2 - Procesamiento manual asistido

Descripción:

Extraer parcialmente información y mantener intervención humana.

Motivo de rechazo:

No cumple completamente el objetivo de automatización del proceso.

---

## Alternativa 3 - Arquitectura basada en parsers independientes

Descripción:

Cada formato tiene su propio parser bajo una interfaz común.

Motivo de aceptación:

Permite:

- Escalabilidad.
- Mantenimiento sencillo.
- Pruebas independientes.
- Incorporación rápida de nuevos clientes.
- Aislamiento de errores.

---

# Consecuencias positivas

Esta decisión permite:

- Agregar nuevos clientes sin modificar la lógica principal.
- Aislar errores por formato documental.
- Realizar pruebas específicas por parser.
- Mantener el núcleo del sistema estable.
- Evolucionar hacia configuraciones más dinámicas en futuras versiones.

---

# Consecuencias negativas

La solución tendrá mayor cantidad de componentes:

- Más archivos.
- Mayor diseño inicial.
- Necesidad de mantener múltiples parsers.

Esta complejidad es aceptable debido a la variabilidad documental identificada.

---

# Reglas derivadas

A partir de esta decisión:

- Los parsers no contienen reglas comerciales.
- Todos los parsers deben devolver `PurchaseOrderDocument` (modelo estándar).
- Los parsers no realizan matching ni crean entidades del catálogo.
- La correspondencia con el catálogo es responsabilidad del `ProductMatcher` (`MatchResult`: MATCHED / REVIEW_REQUIRED / NO_MATCH).
- Nunca crear silenciosamente un producto/cliente/ruta cuando el matching no es concluyente; un match dudoso termina en `REVIEW_REQUIRED`.
- Nuevos formatos deben agregarse como nuevos parsers.
- No modificar parsers existentes para resolver formatos completamente diferentes.
- Toda nueva estrategia de lectura debe validarse antes de implementarse.

---

# Impacto en desarrollo

Esta decisión afecta:

- Diseño del backend.
- Organización de módulos.
- Pruebas automatizadas.
- Modelo de datos.
- Flujo de procesamiento de órdenes.

El sistema deberá diseñarse alrededor de esta estrategia para garantizar mantenibilidad y crecimiento futuro.