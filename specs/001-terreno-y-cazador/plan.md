# Implementation Plan: Terreno y cazador

**Branch**: `Sofia` | **Date**: 2026-11-07 | **Spec**: [spec.md](spec.md)

**Input**: Especificación confirmada en `specs/001-terreno-y-cazador/spec.md`.

## Summary

La capacidad incorporará costos de salida a todos los movimientos, validará los datos de terreno y cazadores, y añadirá decisiones de cazador mediante rutas ponderadas deterministas. La elección provisional es una búsqueda individual limitada por rango, con un montículo mínimo y tablas hash propios creados de forma perezosa; el cálculo inverso compartido hacia el jugador se conserva como alternativa medible y no se habilitará por una hipótesis no medida. El mapa mantendrá su lista ordenada de referencias y añadirá un índice propio por ID. Los cálculos de ruta serán datos derivados: no formarán parte del estado reversible y se descartarán ante cambios relevantes o reconstrucciones históricas.

## Technical Context

**Language/Version**: Python 3.11 o superior; el entorno disponible informa Python 3.14.x.

**Primary Dependencies**: biblioteca estándar, `requests` y `pygame` ya existentes. Sin dependencias nuevas. En producción se reutilizan `TablaHashImpl`, `MonticuloMinimo`, `IndiceOrdenado`, `ListaDobleImpl`, `AgendaEventos` y el mecanismo de `CambioReversible` propios.

**Storage**: esqueleto y catálogo procedentes de `FuenteDatos`; guardado binario versionado y `partida.log` heredados. Los resultados de ruta son exclusivamente memoria derivada y no se persisten.

**Testing**: `pytest`, incluida la suite heredada escrita con `unittest`; fixtures sintéticos deterministas, paquete offline y pruebas separadas contra el servicio cuando correspondan.

**Target Platform**: aplicación de escritorio/CLI local en Windows; scripts de spec-kit ejecutados mediante PowerShell desde el puente WSL/Windows. Los modos `--bench` y `--replay` no instancian la vista.

**Project Type**: aplicación Python MVC con simulación por eventos, CLI y vista Pygame.

**Performance Goals**: ciclo completo entre decisiones del jugador `< 20 ms` en la referencia oficial con decenas de cazadores (`PR-001`); trabajo de rango pequeño acotado por su región (`PR-002`); matriz de comparaciones y agenda bajo carga nueva (`PR-003`–`PR-006`).

**Constraints**: determinismo; estructuras propias; sin `dict`/`set` como índice o caché; sin `heapq`, `bisect`, `collections`, `sorted()`, `list.sort()` ni bibliotecas de grafos/rutas en producción; sin red, disco, renderizado o preparación de fixtures dentro de intervalos que no los evalúen; sí se incluye dentro del tiempo toda preparación auxiliar necesaria por consulta o ciclo.

**Scale/Scope**: esqueleto completo en memoria, costos positivos, cientos de eventos pendientes, decenas de cazadores activos y rangos pequeños o grandes. La carga exacta de la referencia oficial sigue sujeta a la publicación prevista por el enunciado; no se inventa.

## Constitution Check

*GATE: aprobado antes de Phase 0 y revalidado después de Phase 1.*

| Principio | Resultado y evidencia del plan |
|---|---|
| I. Estructuras propias | **PASS**. Rutas, índices y agenda usan estructuras propias. Alternativas de biblioteca solo pueden vivir dentro de `--bench`. |
| II. Acceso por identificador | **PASS**. `MapaCripta` conservará la lista de recorrido y añadirá `TablaHashImpl` para sala por ID; no habrá búsqueda lineal por sala en turnos o rutas. |
| III. Determinismo | **PASS**. La clave de ruta incluye costo y primera vecina; el ID de sala rompe empates sin depender del descubrimiento. La agenda conserva tiempo y secuencia nueva al reprogramar. |
| IV. Separación MVC | **PASS**. Reglas, rutas e invalidación quedan en modelo/lógica; `--bench` usa el punto de entrada sin vista. |
| V. Datos desde el servicio | **PASS**. Costos y rangos se validan al adaptar los datos; no se codifican valores de una cripta. |
| VI. Presupuesto de solicitudes | **PASS**. La ruta usa el esqueleto ya descargado y nunca consulta red o contenido remoto. |
| VII. Estado reversible | **PASS**. Movimiento, puertas, agenda, vida y reloj continúan como cambios pequeños; resultados derivados se invalidan y no se copian ni historizan. |
| VIII. Contratos estables | **PASS condicionado a acuerdo**. No se cambian archivos de Steven/Joshua en esta fase; las propuestas están en `contracts/` y deben aprobarse antes de tareas de integración. |
| IX. Rendimiento medido | **PASS**. Toda selección provisional conserva alternativa y matriz de `--bench`; no se afirma rendimiento sin resultados. |
| X. Especificación y trazabilidad | **PASS**. Las decisiones siguientes citan FR/PR y no añaden reglas. |
| XI. Pruebas | **PASS**. [quickstart.md](quickstart.md) propone cobertura de los 30 escenarios, oráculo independiente y regresión completa. |

No hay violaciones que requieran justificación en Complexity Tracking.

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

`MapaCripta` mantiene `_salas` como lista de referencias en orden de llegada y añade un `TablaHashImpl` por ID. `obtener_salas()` conserva el orden y copia únicamente referencias. `obtener_sala()` consulta el índice. `agregar_sala()` actualiza lista e índice como una sola operación; una sustitución conserva la posición de la entrada. `vincular_salidas()` resuelve destinos por el índice, de modo que pasa de búsquedas lineales repetidas a costo esperado proporcional a salas más salidas.

No se usa el orden interno de la tabla hash para recorrer ni desempatar. Así, un rehash no cambia la simulación y las referencias de `Puerta.destino_sala` siguen apuntando a las instancias presentes en la lista (`FR-011`, `FR-013`, `FR-015`, `FR-018`). La comparación completa está en [research.md](research.md).

### 3. Ruta ponderada provisional

La interfaz interna recibe una vista de grafo, origen, objetivo y límite. La implementación provisional ejecuta una búsqueda individual desde el cazador y:

1. Crea de forma perezosa un montículo propio y tablas propias de etiquetas; no inicializa arreglos de tamaño total.
2. Etiqueta cada estado con `(distancia, primera_vecina_id, sala_id)`. Para una salida inicial, `primera_vecina_id` es su destino; en relajaciones posteriores se conserva.
3. Compara primero distancia y luego primera vecina. El `sala_id` solo hace determinista el orden de trabajo cuando el resultado observable ya está empatado.
4. Deja de expandir cuando la menor distancia pendiente supera el rango o cuando el objetivo queda fijado.
5. Devuelve ataque fuera del buscador si origen y objetivo coinciden; si no hay resultado dentro del límite, el comportamiento espera con costo 100; si lo hay, mueve un paso y entrega el costo de esa salida (`FR-007`–`FR-012`).

**Prueba del desempate**: cada ruta desde el origen hereda el ID de su primera vecina. Para una sala, la etiqueta conserva el par mínimo `(costo_total, primera_vecina_id)`. Como todos los costos son positivos, todo predecesor de una ruta mínima al objetivo se fija antes que el objetivo; además, las etiquetas de igual costo con menor primera vecina salen antes del montículo. Por tanto, antes de fijar el objetivo ya se consideró toda ruta que pudiera igualar su costo con una primera vecina menor. El resultado coincide con escoger el menor `v` que cumple `costo(u,v) + dist(v,jugador) = d`, sin depender del orden de descubrimiento (`FR-011`).

La alternativa compartida hace una búsqueda inversa desde el jugador y luego cada cazador elige el mínimo `(costo(u,v)+dist(v), v.id)`. Es potencialmente favorable con muchos cazadores y objetivo/puertas estables, pero puede recorrer una región grande por un único rango máximo. Se medirá; no es aún un resultado ni un contrato de producción (`PR-002`, `PR-003`).

### 4. Costo completo y complejidad

Variables:

- `V`, `E`: salas y salidas dirigidas del esqueleto completo.
- `V_R`, `E_R`: salas fijadas y salidas examinadas por una consulta limitada al rango.
- `H`: cazadores activos que deciden en el ciclo.
- `V_L`, `E_L`: región recorrida por el cálculo compartido hasta el límite agregado.
- `N`: eventos pendientes en agenda; `K_a`: eventos pendientes de un actor.
- `C`: cambios canónicos registrados en un intervalo reversible.

| Operación | Tiempo esperado/amortizado | Peor caso | Memoria adicional |
|---|---|---|---|
| Construir índice de mapa | O(`V`) esperado total; inserción O(1) esperada y amortizada por rehash | O(`V²`) con colisiones patológicas y rehashes | O(`V`) |
| Obtener sala | O(1) esperado | O(`V`) por colisiones | O(1) |
| Vincular salidas | O(`V+E`) esperado | O(`V·E`) si cada consulta hash degenera | O(1) además del índice |
| Ruta individual completa | O((`V_R+E_R`) log `V_R`) esperado, incluida creación, inserciones, búsqueda y descarte | O((`V_R+E_R`)·`V_R` + `V_R` log `V_R`) con hash degenerado | O(`V_R`) |
| `H` rutas individuales | suma de los costos de sus regiones; cota O(`H(V+E)log V`) | suma de los peores casos individuales | O(max `V_R`) si se liberan entre consultas |
| Cálculo compartido | O((`V_L+E_L`) log `V_L` + suma de grados de los `H` cazadores) esperado | término hash degenerado análogo | O(`V_L`) |
| Invalidar una instantánea por generación | O(1) para desacoplarla; la reclamación/limpieza se reporta y mide | O(`V_L`) si se limpia de inmediato | O(`V_L`) hasta reclamación |
| Revertir intervalo | O(`C`) más costos de sus inversos | depende de los cambios concretos, nunca del estado completo por diseño | O(`C`) registrado |
| Agenda por ID | O(log `N`) actual | O(log `N`) por AVL/montículo balanceado | O(`N`) total |
| Agenda por actor | O(log `N` + `K_a`) para localizar; cancelación total O(`K_a log N`) | igual bajo AVL balanceado | O(`K_a`) para referencias devueltas |

En `--bench`, “preparación fuera del cronómetro” significa únicamente generar/cargar el fixture común. La construcción de montículo/tablas por consulta, la selección de vecinos, las validaciones requeridas, la limpieza, la invalidación y el despacho del ciclo permanecen dentro de la medición correspondiente (`PR-004`).

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

Un nuevo proveedor se registrará en la misma cadena que hoy ejecuta `main.py --bench`. Cada fila informará semilla, entorno, calentamiento, repeticiones, carga, unidad, mediana, p95/máximo cuando corresponda, trabajo contado y alternativa. Antes de cronometrar se comprobará la igualdad con un oráculo independiente; una divergencia produce fallo de corrección, no una fila rápida (`PR-004`, `PR-006`).

**Rutas e invalidación** (`PR-002`, `PR-003`):

- `H = 1` y decenas de cazadores sobre la misma semilla.
- rangos pequeños y grandes, manteniendo una región pequeña idéntica mientras crece el exterior;
- búsqueda individual frente a inversa compartida;
- recálculo siempre frente a reutilización por generación;
- puertas estables frente a aperturas/cierres frecuentes;
- tiempo de consulta, ciclo completo, salas fijadas, salidas examinadas, tamaño máximo del montículo, memoria auxiliar e invalidación/limpieza.

**Ciclo real** (`PR-001`): se reutilizará `benchmarks/benchmark_ciclo_real_integrante1.py`, extendiendo su carga para la referencia oficial con decenas de cazadores. El intervalo abarca la acción del jugador y todos los eventos hasta su siguiente decisión, incluidos creación y limpieza de auxiliares de rutas; excluye solo carga de fuente, copia/reinicio de muestra, red, disco, renderizado e impresión. Los sintéticos no sustituyen la referencia oficial.

**Agenda** (`PR-005`): con flujos deterministas de al menos cientos de eventos se miden por separado insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates. La alternativa comparable usa listas lineales/manuales solo dentro de benchmarks. Además se mide un ciclo mixto de punta a punta con costos variables y cazadores. Se reporta antes/después de la agenda existente aunque la decisión se conserve.

La evidencia decidirá si: (a) permanece la búsqueda individual; (b) se usa compartida solo con múltiples cazadores y estado estable; o (c) se adopta una estrategia adaptativa con umbral medido. No se fijará un umbral por intuición.

### 8. Estrategia de pruebas

[quickstart.md](quickstart.md) contiene una fila por cada AC, incluidos AC-B01–AC-B07. Las pruebas de rutas pequeñas usarán enumeración exhaustiva de rutas simples como referencia independiente; las matrices mayores usarán una relajación completa separada de la implementación de producción. Ambas comparan tipo de acción, primera vecina, costo y trabajo, no el orden interno del algoritmo.

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

[research.md](research.md) resuelve las alternativas de ruta, desempate, índice, invalidación, reversión, benchmark y oráculo. No quedan incógnitas técnicas abiertas en esta fase.

## Phase 1 Outputs

- [data-model.md](data-model.md): entidades canónicas, derivadas, validaciones y transiciones.
- [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md): propuesta pendiente sobre datos y reutilización de rutas con mapa conocido.
- [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md): propuesta pendiente sobre cambios e invalidación histórica.
- [quickstart.md](quickstart.md): guía futura de validación, matriz completa de escenarios y `--bench`.

## Post-Design Constitution Check

**PASS**. El diseño final de Phase 1 mantiene estructuras propias, acceso esperado O(1) por sala, determinismo independiente del descubrimiento, separación MVC, datos externos, reversión por cambios, contratos explícitamente pendientes, mediciones conectadas a `--bench`, trazabilidad y pruebas. No propone dependencias prohibidas ni modifica reglas del spec.

## Risks and Pending Agreements Before Tasks

1. **Contrato de datos con Steven**: acordar quién añade y valida `costo`/`rango`, cómo se informa simetría contradictoria y cómo se conserva en guardado. Bloquea tareas de decodificación, no el diseño de rutas.
2. **Contrato de «ir a» con Steven**: aprobar la vista de grafo restringida al mapa conocido para impedir que 003 filtre el esqueleto completo.
3. **Contrato histórico con Joshua**: acordar representación de cambios de 001 y el punto de invalidación de derivados tras retroceso/reconstrucción.
4. **Referencia oficial**: la carga exacta puede ser publicada o enmendada. Hasta entonces los sintéticos preparan la matriz, pero no demuestran `PR-001`.
5. **Elección de estrategia**: individual es provisional. Compartida/adaptativa solo se seleccionará con resultados de costo completo y equivalencia.
6. **Componente compartido**: ampliar `MonticuloMinimo` o `main.py` requiere revisar consumidores y conservar firmas; si no hace falta ampliar el montículo, se reutiliza sin cambios.

## Complexity Tracking

No aplica: el plan no introduce violaciones constitucionales.
