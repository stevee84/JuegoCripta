# Contrato con Steven: archivo de partida v10

**Dueño de la implementación**: Steven (`datos/guardado_binario.py`). Joshua no modifica ese archivo.
**Requisitos**: FR-028, FR-029, FR-030 y FR-031 de la spec 004.

## Qué pide la línea de tiempo

1. `GuardadoBinario.VERSION` pasa de 9 a 10.
2. Una sección nueva al final del archivo: **longitud (entero de 4 u 8 bytes) + bytes**. El guardado
   no interpreta su contenido.
3. Al guardar, el guardado pide los bytes a la línea de tiempo; al cargar, se los entrega y **usa como
   estado de la partida el que devuelve la línea**. El resto del archivo se sigue leyendo para validar
   cabecera, versión y compatibilidad. Interfaz propuesta, que implementa Joshua:

   ```text
   linea.exportar_bytes(estado) -> bytes
   LineaTiempo.importar_bytes(datos: bytes) -> (estado, linea)
   linea.aviso_k(k_pedido) -> str | None   # FR-030: texto para avisar si se pidió otro K
   ```

   Implementado en `logica/linea_tiempo.py` (T032 y T033). La caché (`cache_inicial`), el
   catálogo vivo (`catalogo_inicial`), el cargador de contenido y la fuente de datos **no viajan**
   en los bytes: pueden tener el cliente de red. Al cargar quedan en `None` y quien restaura la
   partida los vuelve a conectar, como ya hace hoy el guardado. Los enlaces del historial y del
   inventario con la línea se reconectan dentro de `importar_bytes`.

   Si el estado no tiene línea de tiempo (partida de prueba, por ejemplo), la sección se escribe con
   longitud 0; al cargar se usa el estado que arma el guardado y se crea una línea nueva a partir de él.
4. Un archivo v9 o anterior se reporta como incompatible, con el mismo mecanismo que ya se usó de v8
   a v9. Ninguno se carga en silencio (FR-031).

## Por qué el estado vivo sale de la línea

La cola de la línea (las acciones posteriores al último punto de control) guarda cambios que apuntan
a objetos del estado vivo. Si al cargar se usara el estado que arma el guardado, esos cambios
apuntarían a otros objetos y no se podrían deshacer. Serializar el estado vivo y la línea en una
sola operación conserva las referencias y evita un punto de control extra, que el enunciado prohíbe
(«no más de una cada K acciones», §3.6). Esto se corrigió después de `/speckit-analyze` (hallazgo C2).

## Qué contienen los bytes (responsabilidad de Joshua)

El estado vivo, K, los instantes de decisión, los puntos de control y la cola (FR-029). Se serializa
con `pickle`. El estado del azar va dentro del estado.

## Por confirmar con Steven

- Que acepta que, cuando la sección existe, el estado cargado sea el de la línea.
- Si el informe de resolubilidad (v9) y la línea de tiempo (v10) pueden quedar en una sola subida de
  versión, en caso de que todavía no circule ningún archivo v9 de uso real.
- Si prefiere que Joshua escriba un primer borrador del cambio en `guardado_binario.py` para que él
  lo revise, o hacerlo él con este contrato.
