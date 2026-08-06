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

Actualmente se identificaron aproximadamente 9 tipos diferentes de formatos PDF.

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

Ejemplo:


OrderDTO

{
orderNumber,
customer,
deliveryDate,
items[]
}


Detalle:


OrderItemDTO

{
productCode,
description,
quantity
}


Esto permite que el resto del sistema sea independiente del formato original del documento.

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
- Todos los parsers deben devolver modelos estándar.
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