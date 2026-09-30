# Preparación de joshua para integrar Steve

> Informe histórico del primer ensayo. La adaptación posterior autorizada
> exclusivamente en joshua está en [adaptacion_joshua_actual.md](adaptacion_joshua_actual.md).
> Los cinco diagnósticos que aquí figuraban pendientes ya pasan en joshua.

Revisión del 29 de septiembre de 2026.

## Referencias y alcance

- Rama de trabajo: `joshua`, HEAD `8c3197e80689998f13f2124a40f8188fb3cd36d5`.
- `origin/Steve`: `018ed3e27d1c5c7b6a650a3fe4946bcde3429ebf`.
- `origin/Sofia`: `d9bd77d2348124caaf77d1f8ea5ce2dc45aa3401`.
- `git fetch origin` completado. `git merge-base --is-ancestor origin/Sofia origin/Steve`
  devolvió 0: Steve contiene Sofia.
- El árbol de trabajo estaba limpio. Se leyó `EQUIPO.md`; no se encontraron
  archivos AGENTS.md en el repositorio ni en sus directorios ascendentes.
- No se hicieron commits, push ni merge en las ramas del equipo.

## Correcciones de Joshua

`logica/servicio_inventario.py` devuelve los cambios reversibles mediante
`ResultadoAccion.cambios`, sin cambiar la llamada existente a recoger o soltar.
Soltar usa `retirar_actual_con_registro()` y construye `CambioSoltarObjeto`
antes de modificar la ubicación. Así conserva nodo, vecinos y selección.

`logica/cambios.py` incorpora `CambioRecogerObjeto`: conserva la posición
original en el suelo, la ubicación y el cursor previo; al deshacer retira
la inserción y restaura esos datos. Es idempotente. Los cambios se deshacen
en orden inverso mediante la transacción ya existente, sin copiar inventarios.
La restauración supone que se revierten primero las acciones posteriores;
no admite mutaciones arbitrarias fuera del historial.

Se añadió el parámetro opcional `reversible=False` para que el coordinador
excluya movimientos de pergaminos. `ObjetoInstancia` solo conoce el ID de
ficha, no su categoría: no se inventó una clasificación basada en el nombre.
El coordinador deberá consultar el catálogo y aplicar esta opción. También
debe definir cómo conservar movimientos irreversibles al retroceder acciones
anteriores; el juego todavía no implementa esa coordinación.

`tests/test_logica/test_integracion_inventario.py` añade ocho casos con
Inventario, ListaDobleImpl, ServicioInventario, Sala, EstadoPartida,
CambioReloj e HistorialReversible reales. Comprueban extremos y posición
intermedia, retiros sucesivos, recoger después de soltar, suelo, identidad
del cursor, inventario vacío, acciones rechazadas y exclusión del retroceso.

No se modificaron las estructuras manuales, contratos de compañeros ni
pruebas existentes. No se añadieron índices dict/set ni ordenamientos de biblioteca.

## Ensayo separado y conflictos de Git

Worktree con HEAD separado:
`C:/Users/joshu/AppData/Local/Temp/JuegoCripta-integracion-20260929`.
Se ejecutó allí `git merge --no-commit --no-ff origin/Steve`.
El índice del ensayo conserva los conflictos para inspección; los archivos
de trabajo se prepararon para ejecutar las pruebas. No hay commit de integración.

Git detectó 25 archivos con conflictos add/add, varios asociados a
rename/delete por la migración de `modelo` y `adaptadores`.
Resolución de contenido usada únicamente para el ensayo, tras comparar ambos lados:

| Archivos | Criterio |
| --- | --- |
| `logica/bitacora_pantalla.py`, `cambios.py`, `historial_reversible.py`, `inventario.py`, `ordenamiento.py`, `servicio_inventario.py` | Conservar implementaciones de Joshua frente a esqueletos de Steve; incluir las correcciones locales. |
| `datos/almacen_persistente.py`, `cliente_api.py`, `decodificador_datos.py`, `fuente_offline.py`, `guardado_binario.py` | Implementaciones del integrante 2 frente a esqueletos de Joshua. |
| `dto/actor.py`, `estado_partida.py`, `sala.py` | Solo difieren por comentarios de autoría; conservarlos en el ensayo. |
| `dto/evento.py` | Conservar `datos=None` de Sofia, requerido por los efectos; mantiene llamadas de cinco argumentos. |
| `logica/agenda_eventos.py` | Conservar `cancelar_por_actor` y `tiene_eventos`; mantener el montículo manual. |
| `logica/cache_catalogo.py`, `comportamiento_enemigos.py`, `gestor_efectos.py`, `mapa_cripta.py`, `motor_juego.py`, `registro_rastro.py`, `reglas_combate.py` | Implementaciones del bloque remoto frente a esqueletos locales. Sus defectos no se corrigieron silenciosamente. |
| `service/planificador_precarga.py`, `repositorio_catalogo.py` | Implementaciones del integrante 2 frente a esqueletos locales. |

Las listas, cola y pruebas de Joshua se conservaron en el resultado combinado.
No se copió Steve sobre joshua ni se usó una estrategia global ours/theirs.
La corrección funcional no elimina estos conflictos históricos de Git.

La búsqueda de imports antiguos no encontró imports activos de `modelo`,
`adaptadores`, `controlador`, `puertos` o `contratos.accion` en joshua.
La suite combinada tampoco presentó errores de importación.

## Pruebas y resultados

Python 3.11.9; entorno `.venv` creado con `requirements.txt` (pytest y requests).
Se usó el mismo intérprete para las copias temporales.

| Ejecución | Resultado |
| --- | --- |
| `joshua` original, copia de HEAD | 149 pasan |
| `joshua` con correcciones y pruebas nuevas | 157 pasan |
| `origin/Steve` original, copia aislada | 148 pasan, 3 fallan |
| Integración temporal con correcciones de Joshua | 280 pasan, 3 fallan |
| Diagnósticos adicionales con clases reales en la integración | 5 fallan, reproducen pendientes de compañeros |
| `git diff --check` en joshua | Sin problemas |

Comando en cada directorio: `<ruta-absoluta-a-.venv/Scripts/python.exe> -m pytest -q`.
Copias de referencia: `%TEMP%/JuegoCripta-joshua-base-20260929` y
`%TEMP%/JuegoCripta-steve-20260929`.

Los cinco diagnósticos están en `docs/diagnostico_steve.py`. Se ejecutan
explícitamente desde el worktree con `python -m pytest -q docs/diagnostico_steve.py`.
Se mantienen fuera del descubrimiento normal de joshua porque requieren
implementaciones que allí siguen siendo esqueletos. No tienen mocks,
xfail ni expectativas de que una excepción signifique éxito.

## Pendientes de compañeros

### Integrante 2: caché y persistencia

- **CacheCatalogo / ListaDobleImpl:** insertar devuelve un NodoDoble;
  la caché ignora ese retorno, guarda un dict como si fuera nodo y lo pasa
  a mover_al_frente. Falla con `AttributeError`. Debe indexar el nodo
  devuelto, acceder a `nodo.valor` y pasar nodos a mover/quitar.
  Para desalojar debe partir de `lista.ultimo` y recorrer `anterior`,
  omitiendo entradas fijadas. `_datos` pertenece al stub, no a la lista real.
  Las pruebas actuales de caché y estrés usan ListaDobleSimple y ocultan
  ambas incompatibilidades. Cambiarlas a ListaDobleImpl una vez adaptada la caché.
- La caché también usa `set` para fijados y `bisect` para buscar: debe acordarse
  una entrada con atributos y un arreglo ordenado con búsqueda binaria manual,
  sin sustituir el índice por dict/set. La lista de Joshua no necesita cambiar
  su contrato para aceptar valores en operaciones que reciben nodos.
- **GuardadoBinario / EstadoPartida / MapaCripta:** guardar accede a
  `estado.salas` y `estado.cripta_id`, ausentes en EstadoPartida.
  El mapa ofrece `obtener_sala`, pero no un recorrido público de todas las salas.
  Acordar ese recorrido y el ID de cripta sin duplicar un índice hash en el estado.
  Las pruebas actuales usan `_FakeEstado`, por eso no detectan el problema.
- El formato actual tiene MAGIC `CRPT`, versión 1, cabecera `<4sH32sqIIII`,
  registros de jugador/salas e índice de IDs de 32 bytes más offset de 4 bytes.
  `cargar()` devuelve datos en diccionarios, no un EstadoPartida reconstruido.
  No guarda inventario/cursor, agenda, efectos, historial ni estado actual del azar.
  Acordar reconstrucción y cobertura antes de prometer continuar una partida.
  La versión leída tampoco se valida y `leer_sala` necesita robustecer el manejo
  de índices truncados. Estos últimos puntos son hallazgos de lectura del código.

### Bloque de Sofia incluido en Steve: simulación

- **Muerte:** el motor ejecuta `estado.enemigos.pop(...)`; ese atributo no existe.
  Debe llamar `estado.agenda.cancelar_por_actor(actor_id)`, que ya está implementado,
  preservando eventos de otros actores. El diagnóstico programa dos eventos del
  enemigo y uno del jugador para comprobarlo.
- **Efectos vencidos:** comprobar duración antes de usar objetivo o aplicar daño.
  Actualmente un efecto de duración 0 puede lanzar AttributeError si no tiene
  objetivo, o dañar nuevamente a un objetivo válido. Un fallo ya aparece en Steve;
  el diagnóstico adicional demuestra el daño indebido con un actor real.
- **Combate:** dos pruebas esperan la derrota en `resultado[0]`, pero la primera
  notificación es CANCELAR_EVENTOS_ACTOR. No hay contrato que exija la derrota
  primero. Corresponde comprobar las dos notificaciones y sus actores, además
  de estadísticas/estado, sin depender de esa posición. No se alteraron esas pruebas.
- **Historial:** los resultados de combate/movimiento son descripciones en dict,
  no objetos CambioReversible. No se pueden registrar directamente en
  TransaccionAccion: hay que capturar los valores previos y crear cambios que
  implementen deshacer. Coordinar motor y controlador antes de integrar retroceso
  de combate, muerte, agenda y efectos. Las pruebas nuevas cubren inventario/reloj,
  no afirman que todo el motor sea reversible.

### Restricción sin tablas hash

Persisten índices dict en MapaCripta (`_salas`), RegistroRastro (`_presencias`)
y offsets de GuardadoBinario, además de set en PlanificadorPrecarga (`_cargadas`)
y la caché (`_fijados`). Corresponde a sus responsables reemplazarlos por las
estructuras acordadas. La tabla hash y sus pruebas antiguas todavía están en
el repositorio; se debe coordinar su retirada, no asumir que siguen siendo requisito.
Los dict que representan respuestas JSON, fichas o registros de datos son un
caso distinto de usarlos como índices. `sorted` en una expectativa de prueba
no sustituye por sí mismo el algoritmo de producción.

## Estado para revisión

Las correcciones de Joshua están listas para revisar y hacer commit/push.
La integración completa sigue bloqueada por los contratos y fallos descritos;
no debe presentarse como una integración aprobada ni como el juego terminado.
Equipar/usar, controlador y servicios de coordinación siguen pendientes en
el proyecto. El ensayo temporal se conserva para inspección, sin finalizarlo.
