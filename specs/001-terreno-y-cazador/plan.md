# Implementation Plan: Terreno y cazador

**Branch**: `Sofia` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Especificación confirmada en `specs/001-terreno-y-cazador/spec.md`.

## Summary

La capacidad incorporará costos de salida a todos los movimientos, validará los datos de terreno y cazadores, y añadirá decisiones de cazador mediante rutas ponderadas deterministas. La elección provisional es una búsqueda individual limitada por rango, con un montículo mínimo y tablas hash propios creados de forma perezosa; el cálculo inverso compartido hacia el jugador se conserva como alternativa medible y no se habilitará por una hipótesis no medida. El mapa mantendrá su lista ordenada de referencias y añadirá un índice propio por ID. Los cálculos de ruta serán datos derivados: no formarán parte del estado reversible y se descartarán ante cambios relevantes o reconstrucciones históricas.

## Technical Context

**Language/Version**: soporte mínimo Python 3.11. La suite local previamente validada usó el entorno del proyecto `.venv` con Python 3.12.10; los intérpretes generales instalados fuera de `.venv` no se toman como evidencia del entorno del proyecto.

**Primary Dependencies**: biblioteca estándar, `requests` y `pygame` ya existentes. Sin dependencias nuevas. En producción se reutilizan `TablaHashImpl`, `MonticuloMinimo`, `IndiceOrdenado`, `ListaDobleImpl`, `AgendaEventos` y el mecanismo de `CambioReversible` propios.

**Storage**: esqueleto y catálogo procedentes de `FuenteDatos`; guardado binario versionado y `partida.log` heredados. Los resultados de ruta son exclusivamente memoria derivada y no se persisten.

**Testing**: `pytest`, incluida la suite heredada escrita con `unittest`; fixtures sintéticos deterministas, paquete offline y pruebas separadas contra el servicio cuando correspondan.

**Target Platform**: aplicación de escritorio/CLI local en Windows; scripts de spec-kit ejecutados mediante PowerShell desde el puente WSL/Windows. Los modos `--bench` y `--replay` no instancian la vista.

**Project Type**: aplicación Python MVC con simulación por eventos, CLI y vista Pygame.

**Performance Goals**: ciclo completo entre decisiones del jugador `< 20 ms` en la referencia oficial con decenas de cazadores (`PR-001`); trabajo de rango pequeño acotado por su región (`PR-002`); matriz de comparaciones y agenda bajo carga nueva (`PR-003`–`PR-006`).

**Constraints**: determinismo; estructuras propias; sin `dict`/`set` como índice o caché; sin `heapq`, `bisect`, `collections`, `sorted()`, `list.sort()` ni bibliotecas de grafos/rutas en producción; sin red, disco, renderizado o preparación de fixtures dentro de intervalos que no los evalúen; sí se incluye dentro del tiempo toda preparación auxiliar necesaria por consulta o ciclo.

**Scale/Scope**: esqueleto completo en memoria, costos positivos, cientos de eventos pendientes, decenas de cazadores activos y rangos pequeños o grandes. La carga exacta de la referencia oficial sigue sujeta a la publicación prevista por el enunciado; no se inventa.

## Constitution Check

*GATE de diseño: se comprueba ausencia de contradicciones constitucionales; acuerdos, implementación, pruebas y mediciones conservan su estado pendiente explícito.*

| Principio | Estado de la revisión del plan |
|---|---|
| I. Estructuras propias | **Comprobado en el diseño**. Rutas e índices se limitan a estructuras propias; se verificó que el montículo actual permite insertar y extraer, pero no actualizar prioridad. Las alternativas de biblioteca solo aparecen en `--bench`. La comprobación de código queda para implementación/análisis. |
| II. Acceso por identificador | **Comprobado en el diseño**. `MapaCripta` conservará la lista y añadirá `TablaHashImpl` para consultas frecuentes; la sustitución infrecuente seguirá siendo lineal y queda costada expresamente. |
| III. Determinismo | **Comprobado en el diseño**. La etiqueta ordena por costo y primera vecina; el ID de sala solo estabiliza trabajo ya empatado. La agenda heredada asigna secuencia nueva al reprogramar. Falta probar la implementación. |
| IV. Separación MVC | **Comprobado en el diseño**. Rutas e invalidación quedan en lógica y `--bench` no requiere vista. Falta verificarlo sobre el código nuevo. |
| V. Datos desde el servicio | **Pendiente de acuerdo con Steven**. El plan no codifica datos concretos, pero responsabilidad, ubicación y persistencia de la validación de costo/rango siguen propuestas. |
| VI. Presupuesto de solicitudes | **Comprobado en el diseño**. La búsqueda consume el esqueleto ya cargado y no incorpora solicitudes. |
| VII. Estado reversible | **Pendiente de acuerdo con Joshua**. La separación canónico/derivado está definida; el punto de invalidación posterior a reconstrucción aún debe acordarse. |
| VIII. Contratos estables | **Pendiente de acuerdo**. Las dos propuestas de `contracts/` no son contratos aceptados y bloquean las tareas de integración correspondientes. |
| IX. Rendimiento medido | **Decisión provisional pendiente de medición**. Individual limitada es el punto de partida; compartida/adaptativa y cualquier umbral dependen de `--bench`. No hay resultado empírico en esta fase. |
| X. Especificación y trazabilidad | **Comprobado en los artefactos**. Las decisiones citan FR/PR y no cambian las reglas del spec. |
| XI. Pruebas | **Cobertura planificada, no ejecutada**. [quickstart.md](quickstart.md) asigna los 30 escenarios y oráculos, pero esta fase no crea ni ejecuta pruebas nuevas. |

La puerta de planificación no detecta una violación constitucional en el diseño. Esto no equivale a dar por cerrados los acuerdos de integración, las pruebas ni la evidencia de rendimiento indicados arriba.

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-y-cazador/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── propuesta-steven-rutas-datos.md
    └── propuesta-joshua-cambios-reversibles.md
```

`tasks.md` no se crea en esta fase.

### Source Code (repository root)

```text
dto/
├── sala.py                         # integración pendiente: costo en la salida
└── actor.py                        # integración pendiente: rango del cazador
datos/
└── decodificador_datos.py          # integración pendiente con Steven: validación estricta
estructuras/
├── tabla_hash.py                   # índice esperado O(1)
└── monticulo_minimo.py             # prioridad propia reutilizable
logica/
├── mapa_cripta.py                  # lista estable + índice propio por ID
├── rutas_ponderadas.py             # nuevo, propiedad de Sofía
├── comportamiento_enemigos.py      # decisión del cazador
├── acciones.py                     # intervalo común; sin cambiar otros costos
├── motor_juego.py                  # costo de la salida y ejecución reversible
├── agenda_eventos.py               # reprogramación y agenda medida
├── cambios.py                      # cambios canónicos pequeños
└── historial_reversible.py         # integración pendiente con Joshua
benchmarks/
├── terreno_cazador_integrante1.py  # nuevo proveedor conectado a --bench
├── benchmark_ciclo_real_integrante1.py
└── benchmark_agenda_integrante1.py
tests/
├── test_datos/                     # validación costo/rango, tras acuerdo con Steven
├── test_estructuras/               # montículo/índice si se amplían contratos
├── test_logica/                    # rutas, movimiento, cazador, reversión
└── test_bench_terreno_cazador.py   # presencia y coherencia de mediciones
main.py                             # punto de integración del proveedor --bench
```

**Structure Decision**: se conserva el proyecto único y sus capas existentes. `logica/rutas_ponderadas.py` aislará el problema evaluado y recibirá una vista de grafo; no conocerá la vista, la red, el contenido descargado ni el mapa conocido de Steven. La adaptación de datos y la línea de tiempo solo se tocarán después de acordar los contratos propuestos.

## Requirement-to-Decision Traceability

| Decisión | Requisitos atendidos |
|---|---|
| Validación estricta de costo, simetría y rango en el borde de datos | FR-001, FR-002, FR-009, FR-011, FR-017 |
| Costo de la salida como costo de resultado solo para `MOVER` | FR-003, FR-004, FR-005, FR-012, FR-018 |
| Reprogramación proporcional mediante la agenda existente | FR-006, FR-015, FR-016 |
| Búsqueda individual ponderada y limitada por rango | FR-007, FR-008, FR-009, FR-010, FR-013, PR-002 |
| Etiqueta lexicográfica por primera vecina | FR-011, FR-015 |
| Índice propio de salas conservando la lista | FR-011, FR-013, FR-018, PR-001, PR-002 |
| Cálculos derivados no reversibles e invalidación explícita | FR-014–FR-016 |
| Matriz de rutas, invalidación, ciclo completo y agenda | PR-001–PR-006 |
| Oráculo independiente y cobertura por identificador | FR-001–FR-018, PR-001–PR-006 |

## Design

### 1. Datos y validación en el límite

- El adaptador de esqueleto produce cada salida con `costo` entero estricto `>= 1`; si el campo no existe usa 100. `bool` se rechaza porque se valida con `type(valor) is int`, no con `isinstance` (`FR-001`).
- Una validación del esqueleto completo comprueba la igualdad de los dos sentidos antes de iniciar la partida. Ante diferencia identifica la salida y ambos valores y rechaza la cripta (`FR-002`). No corrige ni convierte.
- Una ficha con `comportamiento == "cazador"` exige `rango` con `type(rango) is int` y `rango >= 0`; ausencia, booleano, cadena, fracción o negativo rechazan la ficha de forma descriptiva (`FR-009`).
- Los IDs de sala continúan bajo `validar_id_sala`; no se convierten (`FR-011`).
- Esta fase documenta el contrato con Steven; no adjudica como aceptada la ubicación final de estas validaciones.

### 2. Índice de salas sin perder orden ni identidad

`MapaCripta` mantiene `_salas` como lista de referencias en orden de llegada y añade un `TablaHashImpl` por ID. `obtener_salas()` conserva el orden y copia únicamente referencias. `obtener_sala()` consulta el índice. Para un ID nuevo, `agregar_sala()` añade al final y actualiza la tabla en O(1) esperado y amortizado. Para sustituir un ID existente, la tabla detecta la existencia, pero se recorre `_salas` hasta hallar su posición, se reemplaza allí y se actualiza el índice: esa parte cuesta O(`V`) y conserva el orden sin añadir un segundo índice para una operación infrecuente.

Si las salidas ya estaban vinculadas, la sustitución ejecuta antes de exponer de nuevo el mapa un pase de revinculación: cada `Puerta.destino_sala` se resuelve otra vez desde `destino_sala_id`. Así todas las referencias entrantes que apuntaban a la instancia sustituida pasan a la nueva, y también se resuelven las salidas de la nueva sala. El costo esperado completo de sustituir es O(`V+E`); con búsquedas hash degeneradas, el peor caso del pase es O(`V·E`). Durante la carga inicial, cuando `_enlaces_listos` todavía es falso, las sustituciones solo marcan el mapa pendiente y se realiza un único pase al finalizar. `vincular_salidas()` pasa de búsquedas lineales repetidas a O(`V+E`) esperado.

No se usa el orden interno de la tabla hash para recorrer ni desempatar. Así, un rehash no cambia la simulación y las referencias de `Puerta.destino_sala` siguen apuntando a las instancias presentes en la lista (`FR-011`, `FR-013`, `FR-015`, `FR-018`). La comparación completa está en [research.md](research.md).

### 3. Ruta ponderada provisional

La interfaz interna recibe una vista de grafo, origen, objetivo y límite. La implementación provisional ejecuta una búsqueda individual desde el cazador y:

1. Crea de forma perezosa un `MonticuloMinimo` propio y tablas propias de mejores etiquetas y salas fijadas; no inicializa arreglos de tamaño total. Se comprobó que el montículo actual ofrece `insertar`, `extraer_minimo`, `ver_minimo` y eliminación de una referencia conocida, pero no ofrece actualización de prioridad.
2. Etiqueta cada estado con `(distancia, primera_vecina_id, sala_id)`. Para una salida inicial, `primera_vecina_id` es su destino; en relajaciones posteriores se conserva.
3. Cada mejora de la mejor etiqueta de una sala inserta una entrada inmutable nueva; no modifica ni elimina la entrada anterior. Al extraer, una entrada se descarta si no coincide con la mejor etiqueta actual de esa sala o si la sala ya está fijada. Por tanto, puede haber varias entradas almacenadas por sala y no se atribuye al montículo una operación de actualización que no existe.
4. Compara primero distancia y luego primera vecina. El `sala_id` solo hace determinista el orden de trabajo cuando el resultado observable ya está empatado.
5. No inserta candidatos cuya distancia ya supere el rango: como todos los costos son positivos, ninguna continuación puede volver a quedar dentro. Como defensa adicional, no expande una entrada válida mayor que el rango. La búsqueda termina cuando se fija el objetivo o se agota la frontera pertinente.
6. Devuelve ataque fuera del buscador si origen y objetivo coinciden; si no hay resultado dentro del límite, el comportamiento espera con costo 100; si lo hay, mueve un paso y entrega el costo de esa salida (`FR-007`–`FR-012`).

**Prueba del desempate**: cada ruta desde el origen hereda el ID de su primera vecina. Para una sala, la etiqueta conserva el par mínimo `(costo_total, primera_vecina_id)`. Como todos los costos son positivos, todo predecesor de una ruta mínima al objetivo se fija antes que el objetivo; además, las etiquetas de igual costo con menor primera vecina salen antes del montículo. Por tanto, antes de fijar el objetivo ya se consideró toda ruta que pudiera igualar su costo con una primera vecina menor. El resultado coincide con escoger el menor `v` que cumple `costo(u,v) + dist(v,jugador) = d`, sin depender del orden de descubrimiento (`FR-011`).

La alternativa compartida hace una búsqueda inversa desde el jugador y luego cada cazador elige el mínimo `(costo(u,v)+dist(v), v.id)`. Es potencialmente favorable con muchos cazadores y objetivo/puertas estables, pero puede recorrer una región grande por un único rango máximo. Se medirá; no es aún un resultado ni un contrato de producción (`PR-002`, `PR-003`).

### 4. Costo completo y complejidad

Variables:

- `V`, `E`: salas y salidas dirigidas del esqueleto completo.
- `F_R`: salas fijadas: entradas vigentes extraídas cuya distancia quedó definitiva y no supera el rango.
- `D_R`: salas distintas descubiertas: tienen o tuvieron una mejor etiqueta con distancia dentro del rango; incluye fijadas y salas aún en frontera.
- `E_R`: salidas examinadas al expandir las `F_R` salas fijadas, transitables o cerradas; solo las transitables pueden producir una mejora.
- `P_R`: entradas insertadas en el montículo, incluidas mejoras duplicadas; `P_R <= E_R + 1`.
- `Q_R`: máximo de entradas simultáneamente almacenadas en la frontera; incluye vigentes y obsoletas, y `Q_R <= P_R`.
- `Q_fin`: entradas que quedan almacenadas cuando se fija temprano el objetivo y deben liberarse al cerrar la consulta.
- `H`: cazadores activos que deciden en el ciclo.
- `F_L`, `D_L`, `E_L`, `P_L`, `Q_L`, `Q_fin_L`: magnitudes análogas del cálculo compartido hasta el límite agregado.
- `N`: eventos pendientes en agenda; `K_a`: eventos pendientes de un actor.
- `C`: cambios canónicos registrados en un intervalo reversible.

| Operación | Tiempo esperado/amortizado | Peor caso | Memoria adicional |
|---|---|---|---|
| Construir índice de mapa | O(`V`) esperado total; inserción O(1) esperada y amortizada por rehash | O(`V²`) con colisiones patológicas y rehashes | O(`V`) |
| Obtener sala | O(1) esperado | O(`V`) por colisiones | O(1) |
| Vincular salidas | O(`V+E`) esperado | O(`V·E`) si cada consulta hash degenera | O(1) además del índice |
| Sustituir sala y revincular | O(`V+E`) esperado: búsqueda lineal de posición y pase de referencias | O(`V·E`) con hash degenerado durante la revinculación | O(1) adicional |
| Ruta individual completa con duplicados | O(`E_R + P_R log max(2,Q_R) + Q_fin`) esperado, incluida creación, extracciones vigentes/obsoletas y limpieza | O((`E_R+P_R`)·`D_R` + `P_R log P_R` + `Q_fin`) con hash degenerado | O(`D_R+Q_R`), peor O(`D_R+E_R`) |
| `H` rutas individuales secuenciales | suma de los costos anteriores; no se expresa solo con `F_R` porque duplicados y descubiertas también cuestan | suma de los peores casos individuales | O(max(`D_R+Q_R`)) si cada consulta se libera antes de la siguiente |
| Cálculo compartido con duplicados | O(`E_L + P_L log max(2,Q_L) + Q_fin_L` + selección de vecinos de `H`) esperado | término hash degenerado análogo | O(`D_L+Q_L`) |
| Invalidar una instantánea por generación | O(1) para desacoplarla; la reclamación/limpieza se reporta y mide | O(`D_L+Q_L`) si se limpia de inmediato | O(`D_L+Q_L`) hasta reclamación |
| Revertir intervalo | O(`C`) más costos de sus inversos | depende de los cambios concretos, nunca del estado completo por diseño | O(`C`) registrado |
| Agenda por ID | O(log `N`) actual | O(log `N`) por AVL/montículo balanceado | O(`N`) total |
| Agenda por actor | O(log `N` + `K_a`) para localizar; cancelación total O(`K_a log N`) | igual bajo AVL balanceado | O(`K_a`) para referencias devueltas |

En `--bench`, “preparación fuera del cronómetro” significa únicamente generar/cargar el fixture común. La construcción de montículo/tablas por consulta, las `P_R` inserciones, las extracciones obsoletas, la selección de vecinos, las validaciones requeridas, la liberación de `Q_fin`, la invalidación y el despacho del ciclo permanecen dentro de la medición correspondiente (`PR-004`). El límite evita explorar fuera de la región pertinente porque no almacena etiquetas con costo superior al rango y solo examina salidas de salas fijadas dentro de él; aun así, `D_R`, `P_R` y `Q_R` pueden superar `F_R` y se cuentan por separado.

### 5. Dependencias e invalidación

| Información | Depende de | Invalida | No invalida por sí solo |
|---|---|---|---|
| Esqueleto/costos | versión de cripta y datos validados | nueva versión/nueva partida | contenido descargado |
| Distancias compartidas | esqueleto, costos, puertas abiertas, sala objetivo | abrir/cerrar puerta, cierre automático, mover jugador, nueva versión | velocidad; mover o morir otro actor |
| Decisión individual | lo anterior + sala y rango del cazador | se recalcula en cada turno provisionalmente | contenido descargado, niebla |
| Lote de cazadores | conjunto de cazadores vivos/activos | activación, muerte, retroceso que cambie ese conjunto | movimiento de un actor que no participa |
| Próxima acción | reloj, velocidad y evento del actor | inicio/fin de efecto de velocidad; retroceso | rutas y puertas si el evento ya fue programado |

La apertura y el cierre automático cambian el grafo transitable. El movimiento del jugador cambia el objetivo. El movimiento de un cazador cambia solo su origen; una distancia inversa al mismo objetivo podría seguir sirviendo. La velocidad no forma parte del costo de ruta y no invalida distancias; sí reprograma el evento con secuencia nueva (`FR-006`). La muerte/movimiento de otros actores no bloquea salidas, por lo que no invalida distancias, aunque la muerte cambia qué cazadores participan. Después de cualquier retroceso o reconstrucción histórica se descartan todos los cálculos derivados antes de la próxima decisión; se prioriza un recálculo seguro frente a intentar invertir una caché (`FR-014`–`FR-016`).

La producción provisional recalcula cada decisión. Cualquier reutilización futura exige clave de versión/generación y comparación automática contra cálculo desde cero antes de habilitarse.

### 6. Movimiento, agenda y reversión

- `ResultadoAccion.costo` de `MOVER` se obtiene de la salida atravesada tanto para jugador como para enemigos. `ATACAR`, `ESPERAR`, `USAR`, `EQUIPAR`, `RECOGER`, `SOLTAR` y `ABRIR` siguen usando `costo_base` heredado (`FR-003`–`FR-005`, `FR-012`).
- `calcular_intervalo` sigue siendo la única fórmula común. El motor no modifica el costo de una acción ya no relacionada con movimiento.
- `AgendaEventos.reprogramar` cancela y reinserta el mismo evento con tiempo nuevo y secuencia nueva; el cambio de velocidad conserva la fórmula proporcional y registra todos los cambios para poder deshacerlos (`FR-006`).
- Movimiento de cazadores registra retiro/inserción de las listas de sala, `sala_actual`, ataques/vida, agenda, reloj y secuencias mediante cambios pequeños. Las rutas, etiquetas, montículos de consulta e instantáneas no son estado del juego y no entran en `HistorialReversible` (`FR-016`).
- Una acción rechazada se valida antes de mutar o aborta su transacción, y no deja datos derivados presentados como válidos (`FR-017`).
- El acuerdo pendiente con Joshua define una notificación para descartar derivados después de retroceso o reconstrucción, sin copias completas y sin imponer el diseño interno de su línea de tiempo.

### 7. Medición conectada a `--bench`

Un nuevo proveedor se registrará en la misma cadena que hoy ejecuta `main.py --bench`. Cada fila informará semilla, entorno, calentamiento, repeticiones, carga, unidad, mediana, p95/máximo cuando corresponda, trabajo contado y alternativa. Antes de cronometrar se comprobará con un oráculo independiente la igualdad de la decisión observable: acción, alcanzabilidad, costo total, primera vecina y costo del paso. El orden interno y la cantidad de trabajo pueden diferir; se reportan como mediciones separadas y no como igualdad exigida por el oráculo. Una divergencia observable produce fallo de corrección, no una fila rápida (`PR-004`, `PR-006`).

**Rutas e invalidación** (`PR-002`, `PR-003`):

- `H = 1` y decenas de cazadores sobre la misma semilla.
- rangos pequeños y grandes, manteniendo una región pequeña idéntica mientras crece el exterior;
- búsqueda individual frente a inversa compartida;
- recálculo siempre frente a reutilización por generación;
- puertas estables frente a aperturas/cierres frecuentes;
- tiempo de consulta, ciclo completo, `F` fijadas, `D` descubiertas, `E` salidas examinadas, `P` inserciones totales, `Q` frontera máxima, extracciones obsoletas, memoria auxiliar e invalidación/limpieza.

**Ciclo real** (`PR-001`): se reutilizará `benchmarks/benchmark_ciclo_real_integrante1.py`, extendiendo su carga para la referencia oficial con decenas de cazadores. El intervalo abarca la acción del jugador y todos los eventos hasta su siguiente decisión, incluidos creación y limpieza de auxiliares de rutas; excluye solo carga de fuente, copia/reinicio de muestra, red, disco, renderizado e impresión. Los sintéticos no sustituyen la referencia oficial.

**Agenda** (`PR-005`): con flujos deterministas de al menos cientos de eventos se miden por separado insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates. La alternativa comparable usa listas lineales/manuales solo dentro de benchmarks. Además se mide un ciclo mixto de punta a punta con costos variables y cazadores. Se reporta antes/después de la agenda existente aunque la decisión se conserve.

La evidencia decidirá si: (a) permanece la búsqueda individual; (b) se usa compartida solo con múltiples cazadores y estado estable; o (c) se adopta una estrategia adaptativa con umbral medido. No se fijará un umbral por intuición.

### 8. Estrategia de pruebas

[quickstart.md](quickstart.md) contiene una fila por cada AC, incluidos AC-B01–AC-B07. Las pruebas de rutas pequeñas usarán enumeración exhaustiva de rutas simples como referencia independiente; las matrices mayores usarán una relajación completa separada de la implementación de producción. Ambas comparan acción, alcanzabilidad, primera vecina, costo total y costo del paso. El trabajo, la frontera y el orden interno pueden diferir y se evalúan por instrumentación separada.

La reversión captura el estado canónico antes del intervalo, ejecuta acciones/cazadores/puertas/velocidad, retrocede y compara todos los campos reversibles, aplicando la excepción de pergaminos de FR-016. Después ejecuta las mismas acciones desde el mismo estado posterior al retroceso en dos partidas y compara registros. La suite completa y `tests/test_restricciones_enunciado.py` deben permanecer verdes.

## Ownership and Integration Boundaries

### Archivos de Sofía

- `logica/mapa_cripta.py`, `logica/rutas_ponderadas.py`, `logica/comportamiento_enemigos.py`, `logica/acciones.py`, `logica/motor_juego.py`.
- Mediciones de 001 bajo `benchmarks/` y pruebas de terreno/cazador bajo `tests/`.
- Cambios mínimos en `main.py` únicamente para registrar el proveedor de `--bench`, coordinados por ser punto compartido.

### Puntos de integración pendientes

- **Steven**: adaptación estricta de `costo` y `rango`, DTO compartidos, persistencia/versión y vista del mapa conocido para «ir a». Propuesta: [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md). No se considera aceptada hasta revisión conjunta.
- **Joshua**: publicación de cambios canónicos para línea de tiempo y descarte de cálculos derivados después de retroceso/reconstrucción. Propuesta: [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md). No se considera aceptada hasta revisión conjunta.
- **Spec 002**: la resolubilidad consume el mismo esqueleto y referencias de sala; el índice no altera su orden ni identidad. No se modifica `specs/002-resolubilidad`.
- **Spec 004**: su FR-022 necesita reconstruir costos y cazadores como estado canónico, pero no instantáneas de ruta. No se modifica `specs/004-linea-de-tiempo`.

## Phase 0 Output

[research.md](research.md) fija el mecanismo de prioridades, las cotas y las alternativas de ruta, desempate, índice, invalidación, reversión, benchmark y oráculo. No quedan ambigüedades normativas del spec; sí permanecen acuerdos de integración y decisiones provisionales condicionadas por mediciones, enumerados abajo.

## Phase 1 Outputs

- [data-model.md](data-model.md): entidades canónicas, derivadas, validaciones y transiciones.
- [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md): propuesta pendiente sobre datos y reutilización de rutas con mapa conocido.
- [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md): propuesta pendiente sobre cambios e invalidación histórica.
- [quickstart.md](quickstart.md): guía futura de validación, matriz completa de escenarios y `--bench`.

## Post-Design Constitution Check

**Puerta de diseño satisfecha con condiciones abiertas**. Los artefactos no proponen dependencias prohibidas ni cambian reglas del spec, y definen estructuras propias, acceso frecuente esperado O(1), determinismo, separación MVC y trazabilidad. Permanecen pendientes los acuerdos con Steven/Joshua, la ejecución de pruebas y la evidencia de `--bench`; por ello no se presentan como comprobaciones ya completadas ni como resultados de rendimiento.

## Risks and Pending Agreements Before Tasks

1. **Contrato de datos con Steven**: acordar quién añade y valida `costo`/`rango`, cómo se informa simetría contradictoria y cómo se conserva en guardado. Bloquea tareas de decodificación, no el diseño de rutas.
2. **Contrato de «ir a» con Steven**: aprobar la vista de grafo restringida al mapa conocido para impedir que 003 filtre el esqueleto completo.
3. **Contrato histórico con Joshua**: acordar representación de cambios de 001 y el punto de invalidación de derivados tras retroceso/reconstrucción.
4. **Referencia oficial**: la carga exacta puede ser publicada o enmendada. Hasta entonces los sintéticos preparan la matriz, pero no demuestran `PR-001`.
5. **Elección de estrategia**: individual es provisional. Compartida/adaptativa solo se seleccionará con resultados de costo completo y equivalencia.
6. **Componente compartido**: `MonticuloMinimo` se reutiliza únicamente con `insertar`, `extraer_minimo` y lectura del mínimo ya existentes; el diseño no exige actualización de prioridad. Cualquier otro cambio al montículo o a `main.py` requiere revisar consumidores y conservar firmas.

## Complexity Tracking

No aplica: el plan no introduce violaciones constitucionales.
