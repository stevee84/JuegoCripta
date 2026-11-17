# Captura del servicio del 17/11/2026

Snapshot de lo que el API publica **hoy**, tomado con
`python -m tests.fixtures.capturar_api tests/fixtures/api_actual`.

Convive con `api_real/`, que es la captura anterior, en vez de reemplazarla. No se puede
fusionar las dos: **el catálogo cambió las estadísticas de las fichas**, y el contenido
capturado de `cripta-01` tiene enemigos cuya vida supera el máximo que declara el catálogo
nuevo, así que mezclarlos hace fallar la decodificación. Una captura es coherente consigo
misma o no sirve.

Qué trae esta que la otra no:

- **`cripta-05` «Cripta sellada»**, 24 salas, **sin solución a propósito**: la llave de hierro
  y la negra se encierran mutuamente. Es el caso de §3.5 con datos reales.
- **`cripta-06` «Cripta de referencia»**, **300 salas en 6 páginas**. Es la cripta que §6.1
  anticipaba. Con ella se descubrió que copiar el mapa agotaba la recursión de Python a partir
  de unas 180 salas.
- Cinco fichas nuevas en el catálogo: `ent_carcelero_errante`, `ent_espectro_acechador`,
  `ent_sabueso_oseo`, `itm_llave_hierro` e `itm_llave_plata`.
- **Ya no existe `cripta-01`**: el servicio devuelve 404. En `api_real/` se conserva porque 21
  archivos de prueba la usan y su captura sigue siendo coherente con el catálogo de entonces.
