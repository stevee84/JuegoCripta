# Adaptación de joshua para el futuro merge

## Alcance y referencias

Trabajo sobre `joshua`, partiendo del commit del usuario `89dc16b`.
Referencia comparada: `origin/Steve` en `018ed3e`, que contiene `origin/Sofia`.
El árbol estaba limpio al empezar. No se ejecutó merge, commit, push,
checkout de rama ni cambio del índice. Los cambios quedan para revisión.
El worktree del ensayo anterior no se utilizó ni modificó en esta adaptación.

La autorización actual permite adaptar módulos compartidos dentro de joshua.
No se modificaron las ramas de los compañeros. Se revisaron los archivos por
separado; no se copió la rama completa ni la implementación de tabla hash de Steve.

## Diferencias reducidas

De los 25 archivos que dieron conflicto en el ensayo anterior, 11 ahora
tienen exactamente el mismo contenido que origin/Steve:

- `datos/almacen_persistente.py`, `cliente_api.py`, `decodificador_datos.py`,
  `fuente_offline.py`.
- `dto/actor.py`, `evento.py`, `sala.py`.
- `logica/agenda_eventos.py`, `comportamiento_enemigos.py`, `reglas_combate.py`.
- `service/repositorio_catalogo.py`.

También se alineó `datos/presupuesto_solicitudes.py`, necesario para los
consumidores compartidos. Estos módulos eran esqueletos o versiones parciales
en joshua. Se conservó el contenido remoto revisado, incluso dos espacios
finales preexistentes que `git diff --check` señala en agenda y comportamiento.

Esto reduce diferencias de contenido. No constituye una nueva medición de
conflictos de merge: no se ejecutó ninguno. Quedan diferencias intencionales
en los otros 14 archivos de la lista anterior:

- Seis implementaciones de Joshua: bitácora, cambios, historial, inventario,
  ordenamiento y servicio de inventario. No deben reemplazarse por los
  esqueletos de origin/Steve.
- Ocho adaptaciones compartidas: estado, guardado, caché, mapa, rastro,
  precarga, motor y efectos. Sus correcciones deben conservarse al integrar.

También se verificó que las ocho implementaciones propias de Joshua
(las seis anteriores, lista doble y cola circular) conservan su contenido
respecto al HEAD de inicio, normalizando únicamente finales de línea.

## Contratos reconciliados

| Módulo | Adaptación en joshua |
| --- | --- |
| CacheCatalogo | Conserva el nodo devuelto por insertar; usa valor/anterior/siguiente y nodos reales para mover/eliminar. LRU recorre desde el último omitiendo fijados. |
| Índice de caché | Arreglo ordenado y búsqueda binaria manual; entradas con atributos y fijaciones en arreglo. Sin bisect, dict o set como índice. Conserva fijar antes de insertar y liberación idempotente. |
| MapaCripta | Arreglo de salas y búsqueda lineal. Reemplazar un ID no duplica salas. Nuevo obtener_salas devuelve una copia de las referencias. |
| EstadoPartida | cripta_id opcional; conserva la llamada anterior con semilla. |
| GuardadoBinario | Recorre estado.mapa.obtener_salas y escribe offsets desde un arreglo de pares. Mantiene cabecera, registros e índice de versión 1. Acepta también los datos de entrada antiguos con salas. |
| RegistroRastro | Arreglo de pares; actualizar conserva solo el último tiempo de cada sala. |
| PlanificadorPrecarga | Usa obtener_salas; cargadas y visitados son arreglos sin hash. Conserva BFS, profundidad y lotes de diez. |
| MotorJuego | Al morir un actor, cancela sus eventos mediante agenda.cancelar_por_actor, sin acceder a estado.enemigos. |
| GestorEfectos | Comprueba duración antes de aplicar daño o acceder al objetivo. |

Los diccionarios que permanecen en estos módulos representan fichas JSON,
resultados de acciones y datos de entrada/salida serializables; no sustituyen
los índices o estructuras evaluadas. La tabla hash antigua y su stub ya
existían y no se modificaron ni conectaron al juego.

## Pruebas

Se incorporaron las suites de datos, simulación y servicios correspondientes
a los módulos de origin/Steve. Se conservaron todas las pruebas anteriores
de joshua. No se incorporó el archivo remoto de estrés global, que incluye
pruebas de la implementación hash retirada del alcance; tampoco se importó
esa implementación para satisfacerlas.

Adaptaciones de las pruebas traídas:

- Caché usa ListaDobleImpl, sin stub.
- Precarga usa MapaCripta real; los arreglos reemplazan el acceso al set privado.
- Las dos pruebas de muerte comprueban ambas notificaciones, sus actores y
  su cantidad. La expectativa anterior dependía de resultado[0], aunque no
  existe un contrato de ese orden. Se conservan las comprobaciones de derrota.

Los cinco diagnósticos originales ahora forman parte del descubrimiento
normal de pytest mediante `test_contratos_compartidos.py`. También se añadieron
pruebas de identidad de nodos, fijaciones, 500 inserciones con desalojos,
enlaces, rastro, mapa, cabecera binaria y precarga con catálogo offline,
repositorio, presupuesto, almacén y caché reales.

Comando desde la raíz:

```powershell
./.venv/Scripts/python.exe -m pytest -q --tb=short
```

Resultado final: **262 pasan, 0 fallan**. Dependencias: las de requirements.txt.
Las pruebas HTTP simulan respuestas; no se verificó el servidor remoto.
La suite incluye imports, estructuras manuales, recoger/soltar y reversión
de orden/cursor; no demuestra una partida completa terminada.

## Qué falta coordinar

- Revisar con los compañeros los contratos nuevos de recorrido del mapa y
  cripta_id; las ramas de ellos conservan los errores originales hasta que
  acuerden incorporar estas correcciones.
- Guardado versión 1 devuelve datos, no reconstruye EstadoPartida completo.
  No conserva todavía inventario, cursor, agenda, historial ni estado del azar.
  Tampoco se abordó la robustez general frente a archivos malformados.
- El motor sigue devolviendo descripciones, no cambios reversibles de combate;
  falta coordinación de transacciones, pergaminos y acciones irreversibles.
- Equipar, usar y coordinación completa de controlador/servicios siguen pendientes.
- No se garantiza cero conflictos futuros. El usuario hará el merge cuando
  decida; las pruebas deberán repetirse si Steve cambia o si la resolución
  final del merge produce contenido distinto al probado aquí.
