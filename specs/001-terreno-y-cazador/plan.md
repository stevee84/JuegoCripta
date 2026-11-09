# Implementation Plan: Terreno y cazador

**Branch**: `Sofia` | **Created**: 2026-11-07 | **Updated**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Especificación confirmada en `specs/001-terreno-y-cazador/spec.md`.

## Summary

La capacidad incorporará costos de salida a todos los movimientos, validará los datos de terreno y cazadores, y añadirá decisiones de cazador mediante rutas ponderadas deterministas. Steven confirmó validación estricta de costo/rango, identificación de sentidos por origen/destino con detección de ambigüedad, vista de «ir a» limitada a salas exploradas, recálculo por paso y casos terminales distinguibles. La elección provisional es una búsqueda individual limitada por rango, con un montículo mínimo y tablas hash propios creados de forma perezosa; cálculo compartido y reutilización permanecen exclusivamente en `--bench` hasta una decisión con evidencia. La producción inicial no retiene resultados de ruta, por lo que no necesita caché, generaciones ni invalidación. El mapa mantendrá su lista ordenada de referencias y añadirá un índice propio por ID. Steven asume persistencia de costo/rango/mapa conocido coordinada con Joshua, pero firmas, archivos compartidos y versión implementada siguen pendientes.

## Technical Context

**Language/Version**: soporte mínimo Python 3.11. La suite local validada tras integrar `origin/Steve` usó el entorno del proyecto `.venv` con Python 3.12.10; los intérpretes generales instalados fuera de `.venv` no describen ese entorno.

**Primary Dependencies**: biblioteca estándar, `requests` y `pygame` ya existentes. Sin dependencias nuevas. En producción se reutilizan `TablaHashImpl`, `MonticuloMinimo`, `IndiceOrdenado`, `ListaDobleImpl`, `AgendaEventos` y el mecanismo de `CambioReversible` propios.

**Storage**: esqueleto y catálogo procedentes de `FuenteDatos`; `GuardadoBinario.VERSION = 9` y `partida.log`. V9 persiste, entre otros datos, el informe de resolubilidad de 002, pero todavía no serializa `Puerta.costo` ni el rango materializado del cazador. Los resultados de ruta son exclusivamente memoria derivada y no se persisten.

**Testing**: `pytest`, incluida la suite heredada escrita con `unittest`; fixtures sintéticos deterministas, paquete offline y pruebas separadas contra el servicio cuando correspondan. Línea base comunicada tras el merge: `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` → `1071 passed`, sin omisiones. Esa regresión satisfecha no sustituye las futuras pruebas de aceptación de 001.

**Target Platform**: aplicación de escritorio/CLI local en Windows; scripts de spec-kit ejecutados mediante PowerShell desde el puente WSL/Windows. Los modos `--bench` y `--replay` no instancian la vista.

**Project Type**: aplicación Python MVC con simulación por eventos, CLI y vista Pygame.

**Performance Goals**: ciclo completo entre decisiones del jugador `< 20 ms` en la referencia oficial con decenas de cazadores (`PR-001`); trabajo de rango pequeño acotado por su región (`PR-002`); matriz de comparaciones y agenda bajo carga nueva (`PR-003`–`PR-006`); medición conjunta con 003 del costo completo de una decisión de «ir a» frente a 5 ms, todavía sin evidencia.

**Constraints**: determinismo; estructuras propias; sin `dict`/`set` como índice o caché; sin `heapq`, `bisect`, `collections`, `sorted()`, `list.sort()` ni bibliotecas de grafos/rutas en producción; sin red, disco, renderizado o preparación de fixtures dentro de intervalos que no los evalúen; sí se incluye dentro del tiempo toda preparación auxiliar necesaria por consulta o ciclo.

**Scale/Scope**: esqueleto completo en memoria, costos positivos, cientos de eventos pendientes, decenas de cazadores activos y rangos pequeños o grandes. La carga exacta de la referencia oficial sigue sujeta a la publicación prevista por el enunciado; no se inventa.

**Evidencia de ramas consultada el 2026-11-08 (sin checkout ni merge)**:

| Estado | Hash | Disponible |
|---|---|---|
| checkout local `Sofia` | `f89b7b53722e92c1337fe57c7bebf5528c1ec53e` | interfaces destructivas actuales; v9; sin costo/rango/003 |
| publicado `Steve` | `757d747b461cdb755705ca5cdd90391090112782` | trabajo de 002; `GuardadoBinario.VERSION = 9`; no publica aún las entregas acordadas de 001/003 |
| publicado `joshua` | `112cd78ab85a5b0f9a580353e5824f4aeb517889` | contiene la implementación 004 de `972af5421d628171a4464709858275b100151c1e`: deshacer temporal, rehacer y `fotografiar_para_rehacer`; pendiente de integrar localmente |

Los acuerdos comunicados no se clasifican como código disponible. La publicación en otra rama tampoco se clasifica como disponibilidad local.

## Constitution Check

*GATE de diseño: se comprueba ausencia de contradicciones constitucionales; acuerdos, implementación, pruebas específicas y mediciones conservan su estado pendiente explícito.*

| Principio | Estado después de revisar el merge |
|---|---|
| I. Estructuras propias | **Comprobado en el diseño**. Rutas e índices se limitan a estructuras propias; el montículo actual permite insertar y extraer, pero no actualizar prioridad. Las alternativas de biblioteca solo aparecen en `--bench`. |
| II. Acceso por identificador | **Pendiente de 001**. El código integrado conserva `MapaCripta._salas` y búsquedas lineales; el índice propio por ID sigue siendo trabajo de 001. La sustitución infrecuente continuará costada por separado. |
| III. Determinismo | **Comprobado en el diseño**. La etiqueta ordena por costo y primera vecina; el ID de sala estabiliza trabajo ya empatado. Falta probar la implementación de 001. |
| IV. Separación MVC | **Comprobado en la frontera actual**. `--bench` y `--verificar` salen antes de crear la vista; rutas productivas permanecen en lógica y las alternativas de reutilización en benchmarks. |
| V. Datos desde el servicio | **Responsabilidad confirmada; implementación pendiente**. Steven implementará validación estricta de costo/rango, default 100 solo por ausencia y simetría tras `vincular_salidas()`. El código aún no incorpora esos campos. |
| VI. Presupuesto de solicitudes | **Comprobado en el diseño**. La ruta consumirá el esqueleto ya reunido por `InicializadorPartida`; no añade consultas ni contenido remoto. |
| VII. Estado reversible | **Aceptación condicionada; interfaz publicada fuera del checkout**. Las mutaciones canónicas de 001 usan transacciones. Joshua publicó deshacer/rehacer temporal y el gancho de fotografía, pero aún no están integrados localmente. Sin reutilización productiva no existen cachés que invalidar. |
| VIII. Contratos estables | **Acuerdos parciales con frontera explícita**. Steven acepta semántica de datos/vista/pasos y asume persistencia coordinada; firmas y archivos concretos siguen abiertos. Joshua publicó interfaces en su rama, no en `Sofia`. `main.py` y demás puntos compartidos requieren integración conjunta acordada. |
| IX. Rendimiento medido | **Decisión provisional pendiente de medición**. La vía común de proveedores existe, pero todavía no registra mediciones de rutas/invalidez de 001 ni las seis operaciones exigidas de agenda. |
| X. Especificación y trazabilidad | **Comprobado en los artefactos**. Los ajustes describen código existente sin cambiar reglas de `spec.md`. |
| XI. Pruebas | **Regresión actual satisfecha; cobertura 001 pendiente**. Se reportan `1071 passed` sin omisiones; [quickstart.md](quickstart.md) conserva la cobertura futura de los 30 escenarios de 001. |

La puerta de planificación no detecta una violación constitucional. Esto no cierra los contratos, la implementación ni la evidencia de rendimiento de 001.

## Project Structure

### Documentation (this feature)

```text
specs/001-terreno-y-cazador/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/
│   └── requirements.md
└── contracts/
    ├── propuesta-steven-rutas-datos.md
    └── propuesta-joshua-cambios-reversibles.md
```

`tasks.md` ya existe y fue corregido después del análisis del Prompt 39; sigue siendo planificación, no evidencia de implementación.

### Source Code (repository root)

```text
dto/
├── sala.py                         # integración pendiente: costo en la salida
└── actor.py                        # integración pendiente: rango del cazador
datos/
├── decodificador_datos.py          # salidas externas/internas y fichas; integración pendiente
└── guardado_binario.py             # formato actual v9; costo/rango aún ausentes
service/
├── inicializador_partida.py        # reúne esqueleto y verifica 002 antes del contenido
└── restaurador_partida.py          # reconstruye mapa/actores y publica historial vacío
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
├── cambios.py                      # local: interfaz destructiva; 004 remoto publica extensión temporal
└── historial_reversible.py         # interfaz local de retroceso; enlace futuro de 004 aún no publicado
benchmarks/
├── terreno_cazador_integrante1.py  # nuevo proveedor conectado a --bench
├── benchmark_ciclo_real_integrante1.py
└── benchmark_agenda_integrante1.py
tests/
├── test_datos/                     # validación costo/rango, tras acuerdo con Steven
├── test_estructuras/               # montículo/índice si se amplían contratos
├── test_logica/                    # rutas, movimiento, cazador, reversión
└── test_bench_terreno_cazador.py   # presencia y coherencia de mediciones
main.py                             # punto compartido: registro de 001 solo mediante integración conjunta
```

**Structure Decision**: se conserva el proyecto único y sus capas existentes. `logica/rutas_ponderadas.py` aislará el problema evaluado y recibirá una vista de grafo; no conocerá la vista, la red, el contenido descargado ni el mapa conocido de Steven. Steven puede planificar la validación y la vista ya confirmadas, pero la integración de la interfaz exacta y del guardado espera los acuerdos abiertos; la línea de tiempo no se modifica desde 001.

## Requirement-to-Decision Traceability

| Decisión | Requisitos atendidos |
|---|---|
| Validación estricta de costo, simetría y rango en el borde de datos | FR-001, FR-002, FR-009, FR-011, FR-017 |
| Costo de la salida como costo de resultado solo para `MOVER` | FR-003, FR-004, FR-005, FR-012, FR-018 |
| Reprogramación proporcional mediante la agenda existente | FR-006, FR-015, FR-016 |
| Búsqueda individual ponderada y limitada por rango | FR-007, FR-008, FR-009, FR-010, FR-013, PR-002 |
| Etiqueta lexicográfica por primera vecina | FR-011, FR-015 |
| Índice propio de salas conservando la lista | FR-011, FR-013, FR-018, PR-001, PR-002 |
| Recálculo sin estado retenido; invalidación solo si una decisión posterior adopta reutilización | FR-014–FR-016 |
| Matriz de rutas, invalidación, ciclo completo y agenda | PR-001–PR-006 |
| Oráculo independiente y cobertura por identificador | FR-001–FR-018, PR-001–PR-006 |

## Design

### 1. Datos y validación en el límite

- Steven implementará en su frontera de datos que cada salida presente `costo` entero estricto `>= 1`. Solo si el campo está ausente usa 100; `bool`, texto, fracción, cero o negativo presentes se rechazan y nunca se sustituyen (`FR-001`).
- Después de `mapa.vincular_salidas()`, la validación identifica sentidos por `(origen_id, destino_id)`, compara costos y detecta como ambigua la multiplicidad entre el mismo par en vez de emparejar por posición. Una diferencia identifica ambos sentidos y rechaza la cripta antes de invocar a 002 (`FR-002`). El PDF y la aclaración vigente no definen por sí solos si toda ausencia de inversa debe rechazarse; esa pregunta queda abierta y no se convierte en regla de implementación.
- Steven implementará que una ficha con `comportamiento == "cazador"` exija `rango` con `type(rango) is int` y `rango >= 0`; ausencia, booleano, cadena, fracción o negativo rechazan la ficha de forma descriptiva (`FR-009`).
- Los IDs de sala continúan bajo `validar_id_sala`; no se convierten (`FR-011`).
- `DecodificadorDatos.convertir_sala()` tiene dos caminos que deberán conservar el mismo dato: `salidas` para el API y `puertas` para registros reconstruidos. Hoy ambos construyen `Puerta` sin costo.
- `DecodificadorDatos._adaptar_contenido_externo()` ya resuelve la ficha antes de construir cada `Enemigo`; ese es un punto posible para validar/materializar `rango` cuando el comportamiento sea `cazador`. `convertir_contenido()` es el camino simétrico de reconstrucción.
- `InicializadorPartida._construir()` reúne todas las páginas, detecta IDs repetidos, vincula salidas y, antes de cargar contenido, llama a la verificación de 002. Steven propuso y Sofía acepta usar el recorrido inmediatamente posterior al enlace para la simetría; la implementación y sus pruebas siguen pendientes.
- `verificador_resolubilidad.verificar()` consume apertura, llave y destino, no costos. Steven confirmó que los pesos no cambian la alcanzabilidad; 001 no modifica la regla de 002.
- La responsabilidad conceptual está acordada, pero no la asignación de DTO/inicializador u otros archivos compartidos. La representación materializada y la firma también siguen abiertas.

**Persistencia vigente**: `GuardadoBinario.VERSION` sigue siendo 9 tanto localmente como en `Steve@757d747…`; el lector exige coincidencia exacta y todavía no serializa costo/rango. Steven asume implementar costo/rango/mapa conocido coordinado con Joshua y la línea, pero no se ha publicado una versión verificable ni se asignaron archivos concretos. Costo/rango serán canónicos; resultados de ruta no se persisten. La propuesta v10 de 004 no prueba una versión implementada ni permite reservarla desde 001.

### 2. Índice de salas sin perder orden ni identidad

`MapaCripta` mantiene `_salas` como lista de referencias en orden de llegada y añadirá un `TablaHashImpl` por ID. El merge no adelantó ese cambio: `obtener_sala()` y `vincular_salidas()` siguen recorriendo la lista. `obtener_salas()` conservará el orden y copiará únicamente referencias; `obtener_sala()` consultará el índice.

Para un ID nuevo, `agregar_sala()` añade al final y actualizará la tabla en O(1) esperado y amortizado. Para sustituir un ID existente, se recorrerá `_salas` hasta hallar su posición, se reemplazará allí y se actualizará el índice: O(`V`) y mismo orden, sin añadir un segundo índice para una operación infrecuente. Como el código actual ya usa `_enlaces_listos`, si el mapa estaba vinculado la sustitución debe dejarlo pendiente y, antes de exponer vecinos otra vez, `vincular_salidas()` debe resolver todas las `Puerta.destino_sala` desde sus IDs. El costo esperado completo es O(`V+E`) y el peor caso O(`V·E`) si cada consulta hash degenera.

No se usa el orden interno de la tabla hash para recorrer ni desempatar. Así, un rehash no cambia la simulación y las referencias de `Puerta.destino_sala` siguen apuntando a las instancias presentes en la lista (`FR-011`, `FR-013`, `FR-015`, `FR-018`). La comparación completa está en [research.md](research.md).

### 3. Ruta ponderada provisional

La interfaz interna recibe una vista de grafo, origen, objetivo y límite. La implementación provisional ejecuta una búsqueda individual desde el cazador y:

1. Crea de forma perezosa un `MonticuloMinimo` propio y tablas propias de mejores etiquetas y salas fijadas; no inicializa arreglos de tamaño total. El montículo actual ofrece `insertar`, `extraer_minimo`, `ver_minimo` y eliminación de una referencia conocida, pero no actualización de prioridad.
2. Etiqueta cada estado con `(distancia, primera_vecina_id, sala_id)`. Para una salida inicial, `primera_vecina_id` es su destino; en relajaciones posteriores se conserva.
3. Cada mejora inserta una entrada inmutable nueva. Al extraer se descarta una entrada que ya no coincida con la mejor etiqueta o cuya sala ya esté fijada; no se atribuye al montículo una actualización de prioridad inexistente.
4. Compara primero distancia y luego primera vecina. El `sala_id` solo hace determinista el orden de trabajo cuando el resultado observable ya está empatado.
5. No inserta candidatos cuya distancia supere el rango. Con costos positivos ninguna continuación puede volver a entrar; solo se expanden salas fijadas dentro del límite.
6. No devuelve una ruta completa: produce únicamente el siguiente paso y los metadatos mínimos que finalmente se acuerden. La firma y representación exactas continúan abiertas.
7. El comportamiento del cazador comprueba antes si comparte sala para `ATACAR`; si el buscador no encuentra ruta dentro del límite, decide `ESPERAR`; si obtiene un paso, decide `MOVER` y cobra esa salida (`FR-007`–`FR-012`). Atacar y esperar no son resultados elegidos por el buscador.

**Prueba del desempate**: cada ruta desde el origen hereda el ID de su primera vecina. Para una sala, la etiqueta conserva el par mínimo `(costo_total, primera_vecina_id)`. Como todos los costos son positivos, todo predecesor de una ruta mínima al objetivo se fija antes que el objetivo; además, las etiquetas de igual costo con menor primera vecina salen antes del montículo. Por tanto, antes de fijar el objetivo ya se consideró toda ruta que pudiera igualar su costo con una primera vecina menor. El resultado coincide con escoger el menor `v` que cumple `costo(u,v) + dist(v,jugador) = d`, sin depender del orden de descubrimiento (`FR-011`).

La alternativa compartida hace una búsqueda inversa desde el jugador y luego cada cazador elige el mínimo `(costo(u,v)+dist(v), v.id)`. Es potencialmente favorable con muchos cazadores y objetivo/puertas estables, pero puede recorrer una región grande por un único rango máximo. Se medirá; no es aún un resultado ni un contrato de producción (`PR-002`, `PR-003`).

Para «ir a», Steven confirmó una vista que solo contiene salas exploradas y enumera, desde ellas, puertas recordadas abiertas hacia otras salas exploradas. También aceptó recalcular cada paso con origen, destino y conocimiento vigentes, representar origen=destino como costo total 0 sin paso y distinguir ausencia de ruta. Siguen abiertos los nombres, firma Python y tipos de retorno.

### 4. Costo completo y complejidad

Variables:

- `V`, `E`: salas y salidas dirigidas del esqueleto completo.
- `F_R`: salas fijadas con distancia definitiva dentro del rango.
- `D_R`: salas distintas descubiertas; incluye fijadas y pendientes.
- `E_R`: salidas examinadas desde las `F_R` salas, abiertas o cerradas; solo las transitables pueden mejorar una etiqueta.
- `P_R`: entradas insertadas, incluidos duplicados; `P_R <= E_R + 1`.
- `Q_R`: máximo de entradas simultáneas en frontera, vigentes u obsoletas.
- `Q_fin`: entradas restantes que se liberan al cerrar anticipadamente la consulta.
- `H`: cazadores activos que deciden en el ciclo.
- `F_L`, `D_L`, `E_L`, `P_L`, `Q_L`, `Q_fin_L`: magnitudes análogas del cálculo compartido.
- `N`: eventos pendientes en agenda; `K_a`: eventos pendientes de un actor.
- `C`: cambios canónicos registrados en un intervalo reversible.

| Operación | Tiempo esperado/amortizado | Peor caso | Memoria adicional |
|---|---|---|---|
| Construir índice de mapa | O(`V`) esperado total; inserción O(1) esperada y amortizada por rehash | O(`V²`) con colisiones patológicas y rehashes | O(`V`) |
| Obtener sala | O(1) esperado | O(`V`) por colisiones | O(1) |
| Vincular salidas | O(`V+E`) esperado | O(`V·E`) si cada consulta hash degenera | O(1) además del índice |
| Sustituir sala y revincular | O(`V+E`) esperado | O(`V·E`) con hash degenerado | O(1) adicional |
| Ruta individual con duplicados | O(`E_R + P_R log max(2,Q_R) + Q_fin`) esperado | O((`E_R+P_R`)·`D_R` + `P_R log P_R` + `Q_fin`) con hash degenerado | O(`D_R+Q_R`), peor O(`D_R+E_R`) |
| `H` rutas individuales secuenciales | suma de los costos de sus regiones | suma de los peores casos individuales | O(max(`D_R+Q_R`)) al liberar entre consultas |
| Cálculo compartido con duplicados | O(`E_L + P_L log max(2,Q_L) + Q_fin_L` + selección de vecinos de `H`) esperado | término hash degenerado análogo | O(`D_L+Q_L`) |
| Invalidar una instantánea experimental por generación | O(1) para desacoplarla; solo `--bench` hasta decisión posterior | O(`D_L+Q_L`) si se limpia de inmediato | O(`D_L+Q_L`) hasta reclamación |
| Revertir intervalo | O(`C`) más costos de sus inversos | depende de los cambios concretos, nunca del estado completo por diseño | O(`C`) registrado |
| Agenda por ID | O(log `N`) actual | O(log `N`) por AVL/montículo balanceado | O(`N`) total |
| Agenda por actor | O(log `N` + `K_a`) para localizar; cancelación total O(`K_a log N`) | igual bajo AVL balanceado | O(`K_a`) para referencias devueltas |

En `--bench`, “preparación fuera del cronómetro” significa únicamente generar/cargar el fixture común. Construcción de auxiliares, `P_R` inserciones, extracciones obsoletas, selección, validaciones, liberación de `Q_fin`, invalidación y despacho permanecen dentro. El límite evita almacenar candidatos fuera del rango y examinar salidas desde salas no fijadas dentro de él; aun así `D_R`, `P_R` y `Q_R` se cuentan separadamente de `F_R` (`PR-004`).

### 5. Dependencias, ubicación e invalidación

| Información | Depende de | Invalida | No invalida por sí solo |
|---|---|---|---|
| Esqueleto/costos | versión de cripta y datos validados | nueva versión/nueva partida | contenido descargado |
| Distancias compartidas | esqueleto, costos, puertas abiertas, sala objetivo | abrir/cerrar puerta, cierre automático, mover jugador, nueva versión | velocidad; mover o morir otro actor |
| Decisión individual | lo anterior + sala y rango del cazador | se recalcula en cada turno provisionalmente | contenido descargado, niebla |
| Paso de «ir a» propuesto | origen, destino y mapa conocido vigentes | se recalcula en cada paso provisionalmente | estado real oculto fuera de la vista |
| Lote de cazadores | conjunto de cazadores vivos/activos | activación, muerte, retroceso que cambie ese conjunto | movimiento de un actor que no participa |
| Próxima acción | reloj, velocidad y evento del actor | inicio/fin de efecto de velocidad; retroceso | rutas y puertas si el evento ya fue programado |

La apertura y el cierre automático cambian el grafo transitable. El movimiento del jugador cambia el objetivo. El movimiento de un cazador cambia solo su origen; una distancia inversa al mismo objetivo podría seguir sirviendo. La velocidad no forma parte del costo de ruta y no invalida distancias; sí reprograma el evento con secuencia nueva (`FR-006`). La muerte/movimiento de otros actores no bloquea salidas, por lo que no invalida distancias, aunque la muerte cambia qué cazadores participan.

La producción provisional recalcula y libera todos los auxiliares al terminar cada consulta. No conserva cachés, instantáneas ni generaciones entre decisiones; por tanto, `RETROCEDER`, `MotorJuego.iniciar` e `historia` no necesitan ganchos de invalidación de rutas.

Las instantáneas compartidas existen solo en `benchmarks/`. Si la evidencia lleva a adoptar reutilización, antes de tocar producción se actualizarán plan y tareas con propietario y claves concretos. Solo entonces deberán quedar fuera de `EstadoPartida` y transacciones, e invalidarse después de retroceso exitoso y al iniciar/cargar, nunca por una consulta `historia` que restaura el estado en `finally`.

En el código actual, `RestauradorPartida.restaurar_para_reanudar()` crea un estado nuevo, reconstruye agenda y referencias e inicia un historial vacío; ninguna caché de rutas se persiste. `MotorJuego.iniciar` es el punto común que recibe tanto estados nuevos como restaurados.

La producción provisional recalcula cada decisión. Para «ir a», la integración aceptada también calcula individualmente desde cero en cada paso. Cualquier reutilización futura exige una decisión separada, equivalencia observable y medición completa antes de añadir tareas de producción.

### 6. Movimiento, agenda y reversión

- `ResultadoAccion.costo` de `MOVER` se obtiene de la salida atravesada tanto para jugador como para enemigos. `ATACAR`, `ESPERAR`, `USAR`, `EQUIPAR`, `RECOGER`, `SOLTAR` y `ABRIR` siguen usando `costo_base` heredado (`FR-003`–`FR-005`, `FR-012`).
- `calcular_intervalo` sigue siendo la única fórmula común. El motor no modifica el costo de una acción ya no relacionada con movimiento.
- `AgendaEventos.reprogramar` cancela y reinserta el mismo evento con tiempo nuevo y secuencia nueva; el cambio de velocidad conserva la fórmula proporcional y registra todos los cambios para poder deshacerlos (`FR-006`).
- Movimiento de cazadores registra retiro/inserción de listas, `sala_actual`, ataques/vida, agenda, reloj y secuencias mediante `logica.mutaciones` (`atributo`, `agregar`, `quitar_identidad`, `registrar`) y los cambios/registro automático de agenda, siempre dentro de la transacción abierta. No se crea un observador general de atributos.
- La interfaz disponible **en el checkout local** es `CambioReversible.deshacer(estado)`, `TransaccionAccion.registrar/revertir` e `HistorialReversible.deshacer_ultimo(estado) -> bool`; no existe allí `rehacer`. Joshua publicó remotamente `registrar_solo_linea`, `deshacer_mientras`, `rehacer` y `fotografiar_para_rehacer(inverso, estado)` en `972af542…`, visible en `joshua@112cd78…`. 001 no los considera disponibles hasta su integración local ni modifica el archivo de Joshua.
- Todo cambio nuevo de 001 debe sobrevivir a `copy.deepcopy((estado, transacciones))` conservando referencias hacia las entidades copiadas, y al `pickle` conjunto de estado vivo/línea propuesto por 004. Por ello contiene solo valores y referencias canónicas incluidas en el paquete, nunca motor, servicio de rutas, cachés, callbacks o recursos externos.
- Las rutas, etiquetas, montículos de consulta e instantáneas no son estado del juego y no entran en `HistorialReversible` (`FR-016`).
- Una acción rechazada se valida antes de mutar o aborta su transacción, y no deja datos derivados presentados como válidos (`FR-017`).
- El contrato de 004 acepta condicionadamente esta frontera: FR-016 basta si todo estado observable se registra en la transacción. Implementación, compatibilidad `deepcopy`/`pickle` y pruebas conjuntas siguen pendientes.

### 7. Medición conectada a `--bench`

La conexión actual de `main.py --bench` importa `benchmarks.integrante2.PROVEEDORES`, concatena `benchmarks.bench_ampliado.PROVEEDORES` y entrega la tupla a `benchmarks.integrante3.ejecutar`. Ese ejecutor añade además `_medir_agenda_existente` y `_medir_ciclo_existente`. La integración conjunta acordada añadirá la tupla de 001 una sola vez; Sofía no edita unilateralmente `main.py`, no reemplaza proveedores de compañeros ni registra simultáneamente tupla y agregador.

Cada fila de 001 informará semilla, entorno, calentamiento, repeticiones, carga, unidad, mediana, p95/máximo cuando corresponda, trabajo contado y alternativa. El helper genérico actual `benchmarks.integrante3.medir()` solo calcula mediana y mínimo; el proveedor de 001 deberá ampliar su fila o usar un adaptador propio para los percentiles exigidos, sin cambiar el significado de las filas ajenas. Antes de cronometrar se comprobará con un oráculo independiente la igualdad de acción, alcanzabilidad, costo total, primera vecina y costo del paso. Trabajo y orden interno pueden diferir y se miden aparte (`PR-004`, `PR-006`).

**Rutas e invalidación** (`PR-002`, `PR-003`):

- `H = 1` y decenas de cazadores sobre la misma semilla.
- rangos pequeños y grandes, manteniendo una región pequeña idéntica mientras crece el exterior;
- búsqueda individual frente a inversa compartida;
- recálculo siempre frente a reutilización por generación;
- puertas estables frente a aperturas/cierres frecuentes;
- tiempo de consulta, ciclo completo, fijadas `F`, descubiertas `D`, salidas `E`, inserciones `P`, frontera `Q`, obsoletas, memoria e invalidación/limpieza.

**Colaboración con 003**: medir cada decisión de «ir a» con origen, destino y conocimiento vigentes frente al límite de 5 ms. El intervalo incluye auxiliares requeridos por la consulta y, para reutilización, construcción, consulta, invalidación y limpieza. Antes de medir se compara con cálculo individual desde cero y se verifica que dos estados reales con el mismo mapa conocido den el mismo resultado. No existe todavía evidencia de cumplimiento.

**Ciclo real** (`PR-001`): `benchmarks/benchmark_ciclo_real_integrante1.py` existe, pero no está conectado por la ruta común: `_medir_ciclo_existente` ejecuta actualmente `prueba_rendimiento_sofia.py`. Se añadirá un adaptador/proveedor para el benchmark real y se extenderá su carga con decenas de cazadores. El intervalo abarca acción y eventos hasta la siguiente decisión, incluidos auxiliares de rutas; excluye carga de fuente, copia/reinicio, red, disco, renderizado e impresión.

**Agenda** (`PR-005`): la conexión actual solo adapta la extracción de `benchmark_agenda_integrante1.py`. 001 agregará, sin atribuirlas al proveedor actual, mediciones separadas de insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates, más el ciclo mixto con costos variables y cazadores.

La evidencia decidirá si: (a) permanece la búsqueda individual; (b) se usa compartida solo con múltiples cazadores y estado estable; o (c) se adopta una estrategia adaptativa con umbral medido. No se fijará un umbral por intuición.

### 8. Estrategia de pruebas

[quickstart.md](quickstart.md) contiene una fila por cada AC, incluidos AC-B01–AC-B07. Las pruebas de rutas pequeñas usarán enumeración exhaustiva de rutas simples y las matrices mayores una relajación completa independiente. Comparan decisión y costos observables; trabajo, frontera y orden interno se instrumentan aparte.

La reversión captura el estado canónico antes del intervalo, ejecuta acciones/cazadores/puertas/velocidad, retrocede y compara todos los campos reversibles, aplicando la excepción de pergaminos de FR-016. Después ejecuta las mismas acciones desde el mismo estado posterior al retroceso en dos partidas y compara registros. La línea base posterior al merge es `1071 passed` sin omisiones; debe conservarse al añadir la cobertura específica de 001.

## Ownership and Integration Boundaries

### Archivos de Sofía

- `logica/mapa_cripta.py`, `logica/rutas_ponderadas.py`, `logica/comportamiento_enemigos.py`, `logica/acciones.py`, `logica/motor_juego.py`.
- Mediciones de 001 bajo `benchmarks/` y pruebas de terreno/cazador bajo `tests/`.
- Propuesta de registro en `main.py` únicamente mediante una integración conjunta acordada; no es archivo propio de Sofía.

### Puntos de integración pendientes

- **Steven**: confirmó validación estricta, simetría identificada por origen/destino con detección de ambigüedad, vista de exploradas, recálculo por paso y casos terminales; asume persistencia coordinada. La punta `757d747…` aún no implementa esas entregas. Firmas, asignación de archivos y política de ausencia de inversa siguen abiertas: [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md).
- **Joshua**: mantiene la aceptación condicionada y publicó deshacer/rehacer temporal y el gancho `fotografiar_para_rehacer` en su rama (`112cd78…`, introducido por `972af542…`). No está integrado en `Sofia`; línea completa, enlace del historial y guardado coordinado siguen pendientes: [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md).
- **Spec 002**: la versión integrada resolvió las dos observaciones revisadas: un fallo al obtener ubicaciones deja la cripta sin verificar y bloquea el inicio salvo `--forzar` (`FR-011`, `FR-019`), y retiró la divulgación de contenido de rutas frente a la niebla. Solo se permite identificar al enemigo que custodia una llave, excepción exigida para ubicarla. 001 no modifica ese spec ni su recorrido; el índice conserva orden e identidad y los costos no alteran la resolubilidad. Como hallazgo de implementación, `InicializadorPartida._verificar()` captura `CriptaAPIError` y `ValueError`, mientras `convertir_llaves()` puede producir `TypeError` ante un ID de sala de tipo inválido; ese borde no se corrige desde 001.
- **Spec 004**: reconstruye hacia atrás desde el punto de control siguiente, deshaciendo como máximo K transacciones y rehaciendo con inversos en `finally`. Re-simular hacia adelante existe solo como alternativa de `--bench`. Su FR-022 necesita costos y cazadores canónicos, pero no cachés de ruta. No se modifica `specs/004-linea-de-tiempo`.

## Phase 0 Output

[research.md](research.md) fija las alternativas y el diseño provisional. No se propone cambiar `spec.md`: la política para una salida sin inversa no está definida y queda como pregunta contractual, sin rebajar FR-002. Permanecen por cerrar firmas/archivos, integración local de la interfaz publicada por Joshua, entrega coordinada de persistencia y decisiones condicionadas por medición.

## Phase 1 Outputs

- [data-model.md](data-model.md): entidades canónicas, derivadas, validaciones y transiciones.
- [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md): acuerdo parcial sobre datos/vista y propuesta pendiente sobre resultado, reutilización y guardado.
- [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md): acuerdo condicionado y evidencia de interfaz publicada remotamente, aún no integrada localmente.
- [quickstart.md](quickstart.md): guía futura de validación, matriz completa de escenarios y `--bench`.

## Post-Design Constitution Check

**Puerta de diseño satisfecha con condiciones abiertas**. Joshua publicó la interfaz temporal en otra rama, pero no está disponible localmente y no implementa aún la línea completa o el guardado coordinado. Steven confirmó semántica y responsabilidad, pero su punta consultada no publica costo/rango/003/persistencia. Tampoco existe evidencia de `--bench` para seleccionar estrategia ni de la medición de 5 ms con 003.

## Risks and Pending Agreements Before Tasks

1. **Integración de datos con Steven**: están confirmadas semántica e identificación por origen/destino; faltan implementación, asignación de archivos, representación y aclarar la salida sin inversa.
2. **Contrato de «ir a» con Steven/003**: vista, recálculo y casos terminales están confirmados; bloquean la integración la firma/representación, entrega de 003 y evidencia conjunta de 5 ms.
3. **Integración histórica con Joshua**: la interfaz base está publicada remotamente y pendiente de integración local. Cada cambio nuevo de 001 deberá ofrecer `fotografiar_para_rehacer` cuando corresponda y pasar pruebas conjuntas; el guardado sigue abierto. No hay invalidación de rutas mientras producción recalcule sin retener estado.
4. **Referencia oficial**: la carga exacta puede ser publicada o enmendada. Hasta entonces los sintéticos preparan la matriz, pero no demuestran `PR-001`.
5. **Elección de estrategia**: individual es provisional. Compartida/adaptativa o cualquier reutilización de «ir a» solo se seleccionará con resultados de costo completo y equivalencia.
6. **Persistencia coordinada**: Steven la asume coordinado con Joshua; deben publicar campos, compatibilidad, archivos y versión. V10 ni otra versión se reserva unilateralmente.
7. **Componentes compartidos**: el diseño no exige ampliar `MonticuloMinimo`. El registro en `main.py` requiere tarea conjunta y no autoriza edición unilateral.

## Complexity Tracking

No aplica: el plan no introduce violaciones constitucionales.
