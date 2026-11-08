# Contrato con Steven: archivo de partida v10

**Dueño de la implementación**: Steven (`datos/guardado_binario.py`). Joshua no modifica ese archivo.
**Requisitos**: FR-028, FR-029, FR-030 y FR-031 de la spec 004.

## Qué pide la línea de tiempo

1. `GuardadoBinario.VERSION` pasa de 9 a 10.
2. Una sección nueva al final del archivo: **longitud (entero de 4 u 8 bytes) + bytes**. El guardado
   no interpreta su contenido.
3. Al guardar, el guardado pide los bytes a la línea de tiempo del estado; al cargar, le entrega
   esos bytes para que se reconstruya. Interfaz propuesta, que implementa Joshua:

   ```text
   linea.exportar_bytes(estado) -> bytes
   LineaTiempo.importar_bytes(datos: bytes, estado) -> LineaTiempo
   ```

   Si el estado no tiene línea de tiempo (partida de prueba, por ejemplo), la sección se escribe con
   longitud 0 y al cargar se crea una línea nueva a partir del estado cargado.
4. Un archivo v9 o anterior se reporta como incompatible, con el mismo mecanismo que ya se usó de v8
   a v9. Ninguno se carga en silencio (FR-031).

## Qué contienen los bytes (responsabilidad de Joshua)

K, los instantes de decisión, los puntos de control y la cola de acciones posteriores al último punto
de control copiada junto con el estado en que se guardó (FR-029). Se serializa con `pickle`. El
estado del azar va dentro de los puntos de control porque forma parte del estado.

## Por confirmar con Steven

- Que el informe de resolubilidad (v9) y la línea de tiempo (v10) queden en una sola subida de
  versión si todavía no se publicó un archivo v9 de uso real.
- Si prefiere que Joshua escriba un primer borrador del cambio en `guardado_binario.py` para que él
  lo revise, o hacerlo él con este contrato.
