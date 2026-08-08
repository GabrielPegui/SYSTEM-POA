# Análisis de Datos — Catálogo Clientes y Productos

> Reporte del análisis de datos (pre-Sprint 2). Fuente: `docs/data/` (CSV) y `docs/samples/` (PDF, evidencia complementaria).
> No modifica código, entidades ni ADRs.

## 1. Resumen ejecutivo

- **Clientes** (`OUT_CLIENTES.csv`): 2.445 registros, 2.442 códigos únicos, 30 rutas. La regla *1 código de cliente = 1 ruta* se cumple salvo **1 excepción** (`CL001062`, en PPN000 y PPN403). El **RNC no es identificador único** (una razón social comparte un RNC con hasta 98 clientes y 19 rutas, ej. cadena Sirena).
- **Productos** (`OUT_PRODUCTO.xlsx.csv`): 3.692 registros, **76 códigos de producto únicos**. Catálogo consistente (ningún código con más de una descripción/categoría/ruta). El export solo contiene la ruta **PPN002** y 2 categorías (VIGAS, PANECILLOS), por lo que **la relación Producto↔Ruta no puede concluirse** con estos datos.
- **Cantidades**: los PDFs de muestra confirman que la **cantidad solicitada es entera** (columna Cantidad / Cant. / Ctd.pedido / N. cajas / Cantidad Pedida). Valores como `192.50`/`119.84` en `BOLIN 4012234.pdf` son **Precio/U** (monetario), no cantidad. → `quantity: int` **se mantiene**; los valores monetarios (`unit_price`, `total`) son `Decimal`; `uom`/presentación quedan para la capa de parsing.
- **PDF**: 2 de 9 muestras son **escaneadas sin texto** (requieren OCR).
- **Decisión Sprint 2: 🟡 AMBER.** El Domain Foundation queda mayormente validado; antes de diseñar la base de datos se requieren 5 confirmaciones de negocio.

## 2. Archivos analizados

| Archivo | Tipo | Tamaño | Registros | Columnas | Notas |
|---|---|---|---|---|---|
| `docs/data/OUT_CLIENTES.csv` | CSV | 36 col | 2.445 | 36 | UTF-8 BOM, coma, CRLF, **sin encabezados** |
| `docs/data/OUT_PRODUCTO.xlsx.csv` | CSV | 35 col | 3.692 | 35 | UTF-8 BOM, coma, CRLF, **sin encabezados** |
| `docs/samples/*.pdf` | 9 PDF | — | — | — | Evidencia complementaria (cantidades, identificación) |

Mapeo de columnas inferido (sin encabezados): clientes → ruta=col0, código=col1, RNC=col2, nombre=col3, dirección=col4; productos → ruta=col0, código=col1, descripción=col2, categoría=col3.

## 3. Clientes

- 2.445 registros, **2.442 códigos únicos** (`CL#####[-NNN]`). Sin filas duplicadas exactas.
- 2 códigos con más de una fila: `CL001642-002` (duplicado administrativo en misma ruta) y `CL001062` (**SURTIDORA BENERITO, 2 rutas**).
- RNC: presente en 2.348/2.445. Formatos inconsistentes: **9 (1.319), 11 (1.027), 12 (2)**, 2 con no-dígitos.
- Nombres: 232 con doble espacio, 44 con caracteres no-ASCII → normalización requerida para matching.
- Col24 = id interno secuencial (2.445 únicos), no es clave de negocio.

## 4. Rutas

- **30 rutas**: PPN000–PPN019 (sin PPN011), PPN301–304, PPN401–404, PPN501–502, PPN601. Formato `PPN###`.
- Estructura por familias (0xx, 3xx, 4xx, 5xx, 6xx) — probablemente agrupación territorial; el mayor es PPN601 (475 clientes).
- Todos los clientes tienen ruta; las 30 rutas tienen clientes.
- 🟢 La ruta es propiedad estable del cliente a nivel de cuenta.

## 5. Productos

- 3.692 registros, **76 códigos únicos** (8 dígitos, ej. `01010101`). Todos los registros son de la ruta **PPN002**.
- **Cada código se repite 49–51 veces** → artefacto de export administrativo (ids internos en col22 y timestamps en col33), **no** son productos de negocio distintos.
- Sin conflictos: 0 códigos con >1 descripción, >1 categoría o >1 ruta. Categorías en export: **PANECILLOS (2.703), VIGAS (989)**.
- col8 ≈ "unidades por caja/empaque" (45 valores distintos: 0, 6, 23, 25…). col33: 599 registros con `1900-01-01` (fecha nula de SQL Server).
- 🟡 Catálogo real más amplio que el export (solo 2 categorías y 1 ruta).

## 6. Relaciones

- **Customer → Route (1 cuenta = 1 ruta): 🟢 confirmado** con 1 excepción (`CL001062`).
- **Razón social (RNC) → muchas cuentas y muchas rutas**: RNC `101796822` (Sirena) = 98 clientes en 19 rutas; `124003091` (Mercadal) = 54 en 10 rutas; 52 RNC comparten >1 ruta; 17 nombres normalizados en >1 ruta. → El RNC **no identifica** la cuenta cliente.
- **Product → Route: 🔴 indeterminado.** El export tiene columna de ruta y está filtrado a PPN002 (sugiere catálogo por ruta), pero no permite confirmar cardinalidad. La observación de negocio ("no necesariamente todos los productos están disponibles en todas las rutas") apoya un catálogo por ruta.

## 7. Calidad de datos

- Sin duplicados exactos en ninguno de los 2 archivos.
- Códigos sin espacios; 0 filas huérfanas sin ruta.
- Problemas: RNC con formatos mixtos (9/11/12) y 2 no numéricos; 232 nombres con doble espacio; 44 nombres no-ASCII; export de productos con filas repetidas (artefacto interno); fecha nula representada como `1900-01-01`.

## 8. Identificadores (recomendación de clave natural)

- **Cliente**: código `CL#####[-NNN]` → clave natural. RNC = índice, no clave (no único).
- **Producto**: código 8 dígitos → clave natural. Ojo: en los PDFs el producto aparece con **códigos/EAN distintos** al catálogo (ej. `110000002260`, EAN `7460966301406`) → el matching PDF↔catálogo necesitará descripción/EAN, no el mismo código.
- **Ruta**: `PPN###` → clave natural. Familia (0xx/3xx/…) como atributo de agrupación.

## 9. Cantidades

- ✅ **Cantidad solicitada = entera** (verificado con coordenadas posicionales de los PDFs). Columna Cantidad / Cant. / Ctd.pedido / N. cajas / Cantidad Pedida.
- `BOLIN 4012234.pdf`: **Cantidad** = `20.00`, `10.00` (enteros); **Precio/U** = `192.50`, `119.84` (monetario); **Total** = `3,850.00` (= 20 × 192.50 ✓). El valor `192.50` **NO es cantidad**.
- `4000326734/4000326758.pdf`: **Cantidad** = `211.000`, `814.000`… (enteros con formato de 3 decimales); Precio = `82.00` (82 × 211 = 17,302.00 ✓). `Jumbo` = `27`, `2`, `12`, `8`, `11` (Pieza); `Bravo` = `180` (UN); `Plaza Lama` = `10.00`, `12.00`, `1.00`.
- **Unidad de medida presente**: PAQ, FDA, UND, UN, CAJ, PZA, Ar. Expresiones `(5 UND)`, `(20 UND)`, `180 UN / 6 UN`, `1 CAJ = 12 UND` = **presentación/conversión del producto**, no cantidad solicitada.
- **Conclusión**: `quantity: int` **se mantiene**. `unit_price` y `total` = `Decimal`. El parser debe identificar la columna de cantidad por su encabezado y nunca inferir que un decimal es cantidad por aparecer junto a una unidad.
- Fecha de entrega: presente en PDFs (ej. `28/07/2026`, `03/08/2026`) → validado.

## 10. Impacto en el Domain Foundation

- 🟢 **Confirmado**: `Customer` con 1 ruta (clave `CL…`), `Product` con código único consistente, `Route` con `PPN###`, orden con cliente + fecha entrega + items, `OrderItem` producto+cantidad, `quantity: int` **correcto sin cambios**.
- 🟡 **Pendiente de diseño (no MVP)**: `uom`, `unit_price`, `total`, `units_per_pack`, `pdf_code` → pertenecen a la capa de parsing / raw document data (ADR-002); se incorporan al dominio solo si el negocio lo requiere. Manejar excepción de multi-ruta (`CL001062`).
- 🔴 **Pendiente de negocio**: cardinalidad Product↔Route.

## 11. Recomendación Database Foundation

- Tablas propuestas: `routes` (`code` PK, familia), `customers` (`code` PK, `rnc`, `name`, `route_code` FK), `products` (`code` PK, descripción, categoría), `product_route` (si el catálogo es por ruta), `orders`, `order_items`.
- `RNC`: solo índice (no `UNIQUE`). Códigos de cliente/producto/ruta: claves naturales, no autoincrementales.
- Auditoría/historial en tablas de negocio (creado/modificado por usuario).

## 12. Implicaciones para el procesamiento PDF

- **2 de 9 muestras sin texto** (`20260803140205892.pdf`, `Orden de Compras BOLIN 2026.08.04-17.pdf`) → se requiere **OCR** o flujo alternativo en el parser.
- **Identificación de cliente**: nombre + (RNC como refuerzo, no único) y posiblemente dirección/ubicación para desambiguar cadenas (Sirena, Mercadal).
- **Identificación de producto**: por descripción/EAN, no por código interno (los códigos del PDF difieren del catálogo).
- **Cantidad**: identificar la columna por su encabezado (Cantidad / Cant. / Ctd.pedido / N. cajas) antes de extraer; normalizar separadores de miles solo en campos monetarios (`Precio/U` `192.50`, `Total` `3,850.00`).

## 13. Preguntas para Grupo Bolín

1. **¿El catálogo de productos es por ruta?** ¿Un producto puede pertenecer a varias rutas o a una sola? (Determina si se necesita la tabla `product_route`.)
2. **¿Existe un export completo de productos** (todas las rutas y categorías)? El actual solo trae PPN002 y VIGAS/PANECILLOS.
3. **`CL001062` (SURTIDORA BENERITO) en PPN000 y PPN403**: ¿caso real (1 cuenta, 2 rutas) o error de datos? ¿Cómo debe tratarse?
4. **¿Se requiere registrar `uom` y `units_per_pack` (presentación) en cada línea** (PAQ/FDA/UND, `1 CAJ = 12 UND`) para la consolidación por ruta, o basta con la cantidad entera? (Las cantidades son enteras; `192.50` es Precio/U.)
5. **¿Se acepta OCR** para los PDF escaneados, o todos los documentos operativos vienen con texto seleccionable?

## 14. Decisión: ¿listos para Sprint 2?

**🟡 AMBER — Listos para iniciar Sprint 2 (Database Foundation) con ajuste previo al dominio.**

- El Domain Foundation queda validado en sus reglas centrales (cliente↔ruta 1:1, producto con código único, orden/ítems). `quantity: int` **ya confirmado** — no requiere cambio de dominio.
- Se recomienda antes de modelar la BD: confirmar los puntos de negocio (claves: catálogo por ruta, y si `uom`/presentación son necesarios para la consolidación).
- Riesgo si no se confirma: diseño de `product_route`/esquema de cantidades erróneo → retrabajo en migraciones.

**Qué se probó**: extracción de ambos CSV con stdlib (Python 3.12), conteos y col-profile completos, análisis cruzado RNC/nombre↔rutas, y extracción de texto de los 9 PDFs de muestra.
**Cómo se probó**: scripts en `C:\Users\sae5\AppData\Local\Temp\opencode\` (`analyze_clientes.py`, `analyze_producto.py`, `analyze_cross.py`, `probe_pdf_scan.py`), venv `Backend\.venv`, `PYTHONIOENCODING=utf-8`.
**Resultado**: 2.445 clientes / 76 productos únicos, 30 rutas, regla cliente↔ruta confirmada con 1 excepción, relación producto↔ruta indeterminada, `quantity: int` confirmado (7 PDFs legibles; valores decimales observados = Precio/U, no cantidad).
