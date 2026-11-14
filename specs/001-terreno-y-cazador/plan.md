# Implementation Plan: Terreno y cazador

**Branch**: `Sofia` | **Created**: 2026-11-07 | **Updated**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Especificación confirmada en `specs/001-terreno-y-cazador/spec.md`.

## Summary

La capacidad incorpora costos de salida a todos los movimientos y añade decisiones de cazador mediante rutas ponderadas deterministas. `5000d1f` ya integra validación/persistencia v10 de costo/rango y simetría entre sentidos existentes; G1 fija `proximo_paso(...) -> ResultadoRuta` y el equipo acepta sentidos únicos. La **decisión medida** (T046/T048/T057, `research.md` R-13 y `DECISIONES.md` §5.1) conserva una búsqueda individual limitada por rango, con un montículo mínimo y tablas hash propios creados de forma perezosa; cálculo compartido y reutilización permanecen exclusivamente en `--bench`. La producción no retiene resultados de ruta. Las mediciones sintéticas de rutas, ciclo, agenda y mapa están conservadas, pero su conexión completa a `main.py --bench` sigue pendiente de T049/T050; la referencia oficial de PR-001 no se ha publicado. Mapa conocido, `LineaTiempo` completa y persistencia conjunta restante siguen pendientes.

## Technical Context

**Language/Version**: soporte mínimo Python 3.11. La suite local validada tras integrar `origin/Steve` usó el entorno del proyecto `.venv` con Python 3.12.10; los intérpretes generales instalados fuera de `.venv` no describen ese entorno.

**Primary Dependencies**: biblioteca estándar, `requests` y `pygame` ya existentes. Sin dependencias nuevas. En producción se reutilizan `TablaHashImpl`, `MonticuloMinimo`, `IndiceOrdenado`, `ListaDobleImpl`, `AgendaEventos` y el mecanismo de `CambioReversible` propios.

**Storage**: esqueleto y catálogo procedentes de `FuenteDatos`; `GuardadoBinario.VERSION = 10` y `partida.log`. V10 serializa `Puerta.costo` y rango; todavía no constituye la entrega conjunta completa de mapa conocido y línea de tiempo. Los resultados de ruta son exclusivamente memoria derivada y no se persisten.

**Testing**: `pytest`, incluida la suite heredada escrita con `unittest`; fixtures sintéticos deterministas, paquete offline y pruebas separadas contra el servicio cuando correspondan. T060 registró la validación local por etapas y la suite final (`1287 passed, 1 skipped, 4 subtests passed`); la omisión es T040 hasta G4b/T056. Las seis pruebas ejecutadas contra la copia temporal de Joshua no se presentan como pruebas locales.

**Target Platform**: aplicación de escritorio/CLI local en Windows; scripts de spec-kit ejecutados mediante PowerShell desde el puente WSL/Windows. Los modos `--bench` y `--replay` no instancian la vista.

**Project Type**: aplicación Python MVC con simulación por eventos, CLI y vista Pygame.

**Performance Goals**: ciclo completo entre decisiones del jugador `< 20 ms` en la referencia oficial con decenas de cazadores (`PR-001`); trabajo de rango pequeño acotado por su región (`PR-002`); construcción/consulta/vinculación del mapa medidas por separado frente a la base lineal; matriz de comparaciones y agenda bajo carga nueva (`PR-003`–`PR-006`); medición conjunta con 003 del costo completo de una decisión de «ir a» frente a 5 ms, todavía sin evidencia.

**Constraints**: determinismo; estructuras propias; sin `dict`/`set` como índice o caché; sin `heapq`, `bisect`, `collections`, `sorted()`, `list.sort()` ni bibliotecas de grafos/rutas en producción; sin red, disco, renderizado o preparación de fixtures dentro de intervalos que no los evalúen; sí se incluye dentro del tiempo toda preparación auxiliar necesaria por consulta o ciclo.

**Scale/Scope**: esqueleto completo en memoria, costos positivos, cientos de eventos pendientes, decenas de cazadores activos y rangos pequeños o grandes. La carga exacta de la referencia oficial sigue sujeta a la publicación prevista por el enunciado; no se inventa.

**Evidencia del checkout y ramas consultada el 2026-11-08**:

| Estado | Hash | Disponible |
|---|---|---|
| checkout local `Sofia` | `5000d1fe8af268987206827e4c524c05bd599357` | integra costo/rango, simetría de sentidos existentes y guardado v10 de esos campos; conserva interfaz base de Joshua; sin vista conocida/`LineaTiempo` completa |
| base de Steven integrada | `5000d1fe8af268987206827e4c524c05bd599357` | G2 disponible localmente; validación comunicada `1204 passed, 4 subtests passed`, no ejecutada en esta revisión |
| punta actual publicada `origin/joshua` | `b039b8b871d40984aa0e4bd74e8dd57b85e6224a` | contiene la clase completa `LineaTiempo` de `d055563` y su creación al iniciar; no es ancestro del checkout local y esa entrega completa sigue pendiente de integrar |

Los acuerdos comunicados no se clasifican como código disponible. La interfaz base de Joshua sí es código local por estar en `HEAD`; una publicación posterior en otra rama, como `LineaTiempo`, no lo es.

## Constitution Check

*GATE de diseño: se comprueba ausencia de contradicciones constitucionales; acuerdos, implementación, pruebas específicas y mediciones conservan su estado pendiente explícito.*

| Principio | Estado después de revisar el merge |
|---|---|
| I. Estructuras propias | **Comprobado en el diseño**. Rutas e índices se limitan a estructuras propias; el montículo actual permite insertar y extraer, pero no actualizar prioridad. Las alternativas de biblioteca solo aparecen en `--bench`. |
| II. Acceso por identificador | **Comprobado en producción y en benchmark**. `MapaCripta` conserva `_salas` y añade `_salas_por_id` con `TablaHashImpl`; T007–T009 y T072–T075 cerraron construcción, consultas y vinculación frente a la alternativa lineal benchmark-local. |
| III. Determinismo | **Comprobado en diseño e implementación**. La etiqueta ordena por costo y primera vecina; el ID de sala estabiliza trabajo ya empatado. T032 verificó dos estados equivalentes con orden incidental permutado, decisiones, tiempos, secuencias y `partida.log` idénticos. |
| IV. Separación MVC | **Comprobado en la frontera actual**. `--bench` y `--verificar` salen antes de crear la vista; rutas productivas permanecen en lógica y las alternativas de reutilización en benchmarks. |
| V. Datos desde el servicio | **G2 integrada**. `5000d1f` valida costo/rango, default 100 solo por ausencia y simetría entre sentidos existentes tras `vincular_salidas()`; acepta sentidos únicos. |
| VI. Presupuesto de solicitudes | **Comprobado en el diseño**. La ruta consumirá el esqueleto ya reunido por `InicializadorPartida`; no añade consultas ni contenido remoto. |
| VII. Estado reversible | **Interfaz base local; integración conjunta pendiente**. `deshacer_mientras`, `rehacer`, `fotografiar_para_rehacer` y `vincular_linea` están en `HEAD`. La clase completa `LineaTiempo`, el guardado y las pruebas conjuntas de cambios nuevos de 001 siguen pendientes. Sin reutilización productiva no existen cachés que invalidar. |
| VIII. Contratos estables | **Fronteras explícitas**. Steven conserva DTO/inicialización/guardado; Sofía conserva mapa, rutas y vista del cazador. G1 fija firma/resultado sin asignar la vista conocida de 003. |
| IX. Rendimiento medido | **Medición sintética disponible; conexión completa pendiente**. T044–T048/T065/T073–T075 conservan rutas, ciclo, agenda y mapa con equivalencia previa y trabajo separado. `main.py --bench` ya registra el proveedor del mapa, pero rutas, agenda y ciclo siguen pendientes de T049/T050; la referencia oficial de PR-001 no está publicada. |
| X. Especificación y trazabilidad | **Enmienda confirmada**. FR-002 acepta sentidos únicos y compara costos solo cuando ambos existen; se registra antes del código. |
| XI. Pruebas | **Cobertura propia ejecutada con una dependencia omitida**. T060 registró `1287 passed, 1 skipped, 4 subtests passed`; la única omisión es `tests/test_integracion_001_004.py` hasta G4b/T056. [quickstart.md](quickstart.md) separa esta corrida local de las seis pruebas ejecutadas contra una copia temporal de Joshua. |

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
├── sala.py                         # costo en la salida (integrado en 5000d1f)
└── actor.py                        # rango del cazador (integrado en 5000d1f)
datos/
├── decodificador_datos.py          # salidas externas/internas y fichas; validación v10 integrada
└── guardado_binario.py             # formato actual v10; costo/rango integrados
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
├── cambios.py                      # local: deshacer temporal, rehacer y extensión de fotografía de 004
└── historial_reversible.py         # local: retroceso y vincular_linea; LineaTiempo completa aún no integrada
benchmarks/
├── terreno_cazador_integrante1.py  # proveedor de rutas/agenda; T049 pendiente de conectar
├── benchmark_ciclo_real_integrante1.py  # ciclo real; T049/T050 pendientes de conectar
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
| Benchmark separado de construcción, consulta por ID y vinculación frente a base lineal | FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006 |
| Recálculo sin estado retenido; invalidación solo si una decisión posterior adopta reutilización | FR-014–FR-016 |
| Matriz de rutas, invalidación, ciclo completo y agenda | PR-001–PR-006 |
| Oráculo independiente y cobertura por identificador | FR-001–FR-018, PR-001–PR-006 |

## Design

### 1. Datos y validación en el límite

- Steven implementará en su frontera de datos que cada salida presente `costo` entero estricto `>= 1`. Solo si el campo está ausente usa 100; `bool`, texto, fracción, cero o negativo presentes se rechazan y nunca se sustituyen (`FR-001`).
- Después de `mapa.vincular_salidas()`, la validación identifica sentidos por `(origen_id, destino_id)`, compara costos y detecta como ambigua la multiplicidad entre el mismo par en vez de emparejar por posición. Una diferencia entre dos sentidos existentes rechaza la cripta antes de invocar a 002 (`FR-002`). Una salida sin inversa es válida y no crea otra conexión.
- Steven implementará que una ficha con `comportamiento == "cazador"` exija `rango` con `type(rango) is int` y `rango >= 0`; ausencia, booleano, cadena, fracción o negativo rechazan la ficha de forma descriptiva (`FR-009`).
- Los IDs de sala continúan bajo `validar_id_sala`; no se convierten (`FR-011`).
- `DecodificadorDatos.convertir_sala()` conserva costo en sus caminos de API y reconstrucción.
- `_adaptar_contenido_externo()` valida/materializa `rango` para cazadores y `convertir_contenido()` lo reconstruye.
- `InicializadorPartida._construir()` reúne páginas, detecta IDs repetidos, vincula salidas y valida multiplicidad/simetría antes de 002.
- `verificador_resolubilidad.verificar()` consume apertura, llave y destino, no costos. Steven confirmó que los pesos no cambian la alcanzabilidad; 001 no modifica la regla de 002.
- Steven conserva DTO/inicializador/guardado; Sofía implementa rutas/vista del cazador con la firma acordada.

**Persistencia vigente**: `GuardadoBinario.VERSION` es 10 en `5000d1f` y serializa costo/rango. Mapa conocido y línea de tiempo completa aún requieren coordinación Steven/Joshua. Los resultados de ruta no se persisten.

### 2. Índice de salas sin perder orden ni identidad

`MapaCripta` mantiene `_salas` como lista de referencias en orden de llegada y añadirá un `TablaHashImpl` por ID. Steven solicitó expresamente a Sofía esta optimización después de que su medición de 002 identificara la búsqueda lineal como causa del costo no lineal. La solicitud acuerda el cambio sobre un componente de Sofía; no transfiere a Sofía DTO, inicialización, persistencia ni archivos de Steven. No se encontró un acuerdo explícito contradictorio: §5.4 de `DECISIONES.md`, que permanece dedicado a Resolubilidad, registró históricamente el cuello de botella y la necesidad de acordar el cambio, no una prohibición. La evidencia nueva del índice irá a una subsección propia y solo se enlazará desde la revisión de decisiones de §5.6. El merge no adelantó el índice: `obtener_sala()` y `vincular_salidas()` siguen recorriendo la lista. `obtener_salas()` conservará el orden y copiará únicamente referencias; `obtener_sala()` consultará el índice sin cambiar su firma.

Para un ID nuevo, `agregar_sala()` añade al final y actualizará la tabla en O(1) esperado y amortizado. Para sustituir un ID existente, se recorrerá `_salas` hasta hallar su posición, se reemplazará allí y se actualizará el índice: O(`V`) y mismo orden, sin añadir un segundo índice para una operación infrecuente. Como el código actual ya usa `_enlaces_listos`, si el mapa estaba vinculado la sustitución debe dejarlo pendiente y, antes de exponer vecinos otra vez, `vincular_salidas()` debe resolver todas las `Puerta.destino_sala` desde sus IDs. El costo esperado completo es O(`V+E`) y el peor caso O(`V·E`) si cada consulta hash degenera.

No se usa el orden interno de la tabla hash para recorrer ni desempatar. Así, un rehash no cambia la simulación y las referencias de `Puerta.destino_sala` siguen apuntando a las instancias presentes en la lista (`FR-011`, `FR-013`, `FR-015`, `FR-018`). La comparación completa está en [research.md](research.md).

**Consumidores reales identificados por búsqueda de imports y llamadas**:

| Contrato de `MapaCripta` | Consumidores de producción comprobados | Compatibilidad que debe conservarse |
|---|---|---|
| construcción, `agregar_sala`, `vincular_salidas` | `main.py`, `service/inicializador_partida.py`, `service/restaurador_partida.py`, `service/partida_service.py` | mismas firmas; sustitución en la misma posición; enlace a las instancias canónicas |
| `obtener_sala` en simulación/verificación | `logica/motor_juego.py`, `logica/verificador_resolubilidad.py`, `logica/registro_rastro.py`, `logica/gestor_efectos.py` | mismo `Sala` por identidad o `None`; rechazo heredado de IDs inválidos |
| consultas desde servicios/datos | `service/juego_service.py`, `service/cargador_contenido.py`, `datos/decodificador_datos.py` | sin cambiar carga gradual, incorporación de contenido ni referencias |
| recorrido `obtener_salas` | `datos/guardado_binario.py`, motor, servicios, `vista/presentacion_juego.py`, `vista/vista_pygame.py` | lista nueva con las mismas referencias y orden de llegada |
| mediciones y regresiones | `benchmarks/integrante2.py`, `benchmarks/bench_ampliado.py`, `benchmarks/benchmark_ciclo_real_integrante1.py`, `benchmarks/linea_tiempo.py` y pruebas de lógica/servicio/datos | resultados e identidad iguales antes de comparar rendimiento |

T007–T009 protegen ese contrato. T072–T075 medirán por separado: (a) construir lista+índice; (b) consultar IDs frente a recorrido lineal; y (c) vincular las mismas salidas con resolución lineal frente a indexada. Los fixtures se generan fuera del intervalo; cada alternativa recibe mismos IDs, orden, instancias y carga, y la igualdad/identidad se comprueba antes de cronometrar.

### 3. Ruta ponderada de producción (decisión medida)

La interfaz interna recibe una vista de grafo, origen, objetivo y límite. La implementación de producción ejecuta una búsqueda individual desde el cazador y:

1. Crea de forma perezosa un `MonticuloMinimo` propio y tablas propias de mejores etiquetas y salas fijadas; no inicializa arreglos de tamaño total. El montículo actual ofrece `insertar`, `extraer_minimo`, `ver_minimo` y eliminación de una referencia conocida, pero no actualización de prioridad.
2. Etiqueta cada estado con `(distancia, primera_vecina_id, sala_id)`. Para una salida inicial, `primera_vecina_id` es su destino; en relajaciones posteriores se conserva.
3. Cada mejora inserta una entrada inmutable nueva. Al extraer se descarta una entrada que ya no coincida con la mejor etiqueta o cuya sala ya esté fijada; no se atribuye al montículo una actualización de prioridad inexistente.
4. Compara primero distancia y luego primera vecina. El `sala_id` solo hace determinista el orden de trabajo cuando el resultado observable ya está empatado.
5. No inserta candidatos cuya distancia supere el rango. Con costos positivos ninguna continuación puede volver a entrar; solo se expanden salas fijadas dentro del límite.
6. No devuelve una ruta completa: produce únicamente el siguiente paso y los metadatos mínimos acordados en T002. La firma es `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta`, con `alcanzable`, `costo_total`, `primera_vecina_id` y `costo_primera_salida`; «sin ruta» y «ya en destino» siguen siendo estados distintos.
7. El comportamiento del cazador comprueba antes si comparte sala para `ATACAR`; si el buscador no encuentra ruta dentro del límite, decide `ESPERAR`; si obtiene un paso, decide `MOVER` y cobra esa salida (`FR-007`–`FR-012`). Atacar y esperar no son resultados elegidos por el buscador.

**Prueba del desempate**: cada ruta desde el origen hereda el ID de su primera vecina. Para una sala, la etiqueta conserva el par mínimo `(costo_total, primera_vecina_id)`. Como todos los costos son positivos, todo predecesor de una ruta mínima al objetivo se fija antes que el objetivo; además, las etiquetas de igual costo con menor primera vecina salen antes del montículo. Por tanto, antes de fijar el objetivo ya se consideró toda ruta que pudiera igualar su costo con una primera vecina menor. El resultado coincide con escoger el menor `v` que cumple `costo(u,v) + dist(v,jugador) = d`, sin depender del orden de descubrimiento (`FR-011`).

La alternativa compartida hace una búsqueda inversa desde el jugador y luego cada cazador elige el mínimo `(costo(u,v)+dist(v), v.id)`. Se midió en T046/T048: fue más rápida en las cargas sintéticas, pero no se adopta como producción; la decisión medida está en `research.md` R-13 y `DECISIONES.md` §5.1. Puede recorrer una región grande por un único rango máximo (`PR-002`, `PR-003`).

Para «ir a», Steven confirmó una vista que solo contiene salas exploradas y enumera, desde ellas, puertas recordadas abiertas hacia otras salas exploradas. También aceptó recalcular cada paso con origen, destino y conocimiento vigentes, representar origen=destino como costo total 0 sin paso y distinguir ausencia de ruta. La firma y los tipos quedaron cerrados en T002; la integración de la vista de 003 sigue pendiente de T004.

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
| Decisión individual | lo anterior + sala y rango del cazador | se recalcula en cada turno (decisión medida, R-13) | contenido descargado, niebla |
| Paso de «ir a» acordado | origen, destino y mapa conocido vigentes | se recalcula en cada paso (T002; integración T004 pendiente) | estado real oculto fuera de la vista |
| Lote de cazadores | conjunto de cazadores vivos/activos | activación, muerte, retroceso que cambie ese conjunto | movimiento de un actor que no participa |
| Próxima acción | reloj, velocidad y evento del actor | inicio/fin de efecto de velocidad; retroceso | rutas y puertas si el evento ya fue programado |

La apertura y el cierre automático cambian el grafo transitable. El movimiento del jugador cambia el objetivo. El movimiento de un cazador cambia solo su origen; una distancia inversa al mismo objetivo podría seguir sirviendo. La velocidad no forma parte del costo de ruta y no invalida distancias; sí reprograma el evento con secuencia nueva (`FR-006`). La muerte/movimiento de otros actores no bloquea salidas, por lo que no invalida distancias, aunque la muerte cambia qué cazadores participan.

La producción recalcula y libera todos los auxiliares al terminar cada consulta. No conserva cachés, instantáneas ni generaciones entre decisiones; por tanto, `RETROCEDER`, `MotorJuego.iniciar` e `historia` no necesitan ganchos de invalidación de rutas.

Las instantáneas compartidas existen solo en `benchmarks/`. Si la evidencia lleva a adoptar reutilización, antes de tocar producción se actualizarán plan y tareas con propietario y claves concretos. Solo entonces deberán quedar fuera de `EstadoPartida` y transacciones, e invalidarse después de retroceso exitoso y al iniciar/cargar, nunca por una consulta `historia` que restaura el estado en `finally`.

En el código actual, `RestauradorPartida.restaurar_para_reanudar()` crea un estado nuevo, reconstruye agenda y referencias e inicia un historial vacío; ninguna caché de rutas se persiste. `MotorJuego.iniciar` es el punto común que recibe tanto estados nuevos como restaurados.

La producción recalcula cada decisión. Para «ir a», la integración aceptada también calcula individualmente desde cero en cada paso. Cualquier reutilización futura exige una decisión separada, equivalencia observable y medición completa antes de añadir tareas de producción; T046/T048 midieron la alternativa, pero no se adoptó (R-13).

### 6. Movimiento, agenda y reversión

- `ResultadoAccion.costo` de `MOVER` se obtiene de la salida atravesada tanto para jugador como para enemigos. `ATACAR`, `ESPERAR`, `USAR`, `EQUIPAR`, `RECOGER`, `SOLTAR` y `ABRIR` siguen usando `costo_base` heredado (`FR-003`–`FR-005`, `FR-012`).
- `calcular_intervalo` sigue siendo la única fórmula común. El motor no modifica el costo de una acción ya no relacionada con movimiento.
- `AgendaEventos.reprogramar` cancela y reinserta el mismo evento con tiempo nuevo y secuencia nueva; el cambio de velocidad conserva la fórmula proporcional y registra todos los cambios para poder deshacerlos (`FR-006`).
- Movimiento de cazadores registra retiro/inserción de listas, `sala_actual`, ataques/vida, agenda, reloj y secuencias mediante `logica.mutaciones` (`atributo`, `agregar`, `quitar_identidad`, `registrar`) y los cambios/registro automático de agenda, siempre dentro de la transacción abierta. No se crea un observador general de atributos.
- La interfaz disponible **en el checkout local** incluye `CambioReversible.deshacer(estado)`, `TransaccionAccion.registrar/revertir`, `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, la extensión `fotografiar_para_rehacer(inverso, estado)`, `HistorialReversible.deshacer_ultimo(estado) -> bool` y `vincular_linea`. Llegó mediante `972af542…` y `927d886…`, ambos ancestros de `Sofia@3df43c6…`. La clase completa `LineaTiempo` contenida en la punta posterior `origin/joshua@b039b8b…` no está local; tampoco están el guardado coordinado ni las pruebas conjuntas con cambios todavía inexistentes de 001.
- Todo cambio nuevo de 001 debe sobrevivir a `copy.deepcopy((estado, transacciones))` conservando referencias hacia las entidades copiadas, y al `pickle` conjunto de estado vivo/línea propuesto por 004. Por ello contiene solo valores y referencias canónicas incluidas en el paquete, nunca motor, servicio de rutas, cachés, callbacks o recursos externos.
- Las rutas, etiquetas, montículos de consulta e instantáneas no son estado del juego y no entran en `HistorialReversible` (`FR-016`).
- Una acción rechazada se valida antes de mutar o aborta su transacción, y no deja datos derivados presentados como válidos (`FR-017`).
- El contrato de 004 acepta condicionadamente esta frontera: FR-016 basta si todo estado observable se registra en la transacción. T034/T035 comprobaron `deepcopy`/`pickle` de los cambios locales y T040 redactó la integración; la ejecución conjunta con `LineaTiempo` completa sigue pendiente en T056.

### 7. Medición conectada a `--bench`

La conexión actual de `main.py --bench` importa `benchmarks.integrante2.PROVEEDORES`, concatena `benchmarks.bench_ampliado.PROVEEDORES` y entrega la tupla a `benchmarks.integrante3.ejecutar`. Ese ejecutor añade además `_medir_agenda_existente` y `_medir_ciclo_existente`. La integración conjunta acordada añadirá la tupla de 001 una sola vez; Sofía no edita unilateralmente `main.py`, no reemplaza proveedores de compañeros ni registra simultáneamente tupla y agregador.

Cada fila conservada de 001 informa semilla, entorno, calentamiento, repeticiones, carga, unidad, mediana, p95/máximo cuando corresponde, trabajo contado y alternativa. Los proveedores de 001 amplían la fila o usan adaptadores propios para los percentiles exigidos, sin cambiar el significado de las filas ajenas. Antes de cronometrar comprueban con un oráculo independiente la igualdad de acción, alcanzabilidad, costo total, primera vecina y costo del paso. Trabajo y orden interno pueden diferir y se miden aparte (`PR-004`, `PR-006`).

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

**Mapa e índice** (Constitución II, `PR-001`, `PR-002`, `PR-004`, `PR-006`): `benchmarks/mapa_cripta_integrante1.py` aportará filas separadas para construcción del índice, consultas por ID y vinculación de salidas. Usará varios tamaños y densidades equivalentes; comparará consultas y vinculación con una representación/recorrido lineal permitido solo dentro del benchmark. Generación del fixture, construcción, consultas y vinculación tendrán intervalos distintos. Antes de tiempos se comprobarán IDs, ausencias, orden de salas/puertas y que cada destino sea exactamente la instancia canónica. T049 conectará el proveedor una sola vez a `main.py --bench`; T050/T071 registrarán y validarán la evidencia y T076 creará una subsección documental propia, separada de §5.4 y enlazada desde la revisión de §5.6.

La evidencia decidirá si: (a) permanece la búsqueda individual; (b) se usa compartida solo con múltiples cazadores y estado estable; o (c) se adopta una estrategia adaptativa con umbral medido. No se fijará un umbral por intuición.

### 8. Estrategia de pruebas

[quickstart.md](quickstart.md) contiene una fila por cada AC, incluidos AC-B01–AC-B07. Las pruebas de rutas pequeñas usan enumeración exhaustiva de rutas simples y las matrices mayores una relajación completa independiente. Comparan decisión y costos observables; trabajo, frontera y orden interno se instrumentan aparte.

La reversión captura el estado canónico antes del intervalo, ejecuta acciones/cazadores/puertas/velocidad, retrocede y compara todos los campos reversibles, aplicando la excepción de pergaminos de FR-016. Después ejecuta las mismas acciones desde el mismo estado posterior al retroceso en dos partidas y compara registros. La línea base histórica fue `1071 passed`; la corrida posterior comunicada tras integrar la interfaz base de Joshua fue `1101 passed`, sin fallos ni omisiones. Esta revisión documental no ejecutó ninguna de las dos; la regresión debe conservarse al añadir la cobertura específica de 001.

## Ownership and Integration Boundaries

### Archivos de Sofía

- `logica/mapa_cripta.py`, `logica/rutas_ponderadas.py`, `logica/comportamiento_enemigos.py`, `logica/acciones.py`, `logica/motor_juego.py`.
- Steven solicitó expresamente a Sofía implementar el índice de `MapaCripta`; se conservan firmas, orden e identidad para los consumidores enumerados en §2. La calificación histórica de «componente compartido» obliga a conservar/coordinar el contrato, no prohíbe modificar un componente propio ya acordado.
- Mediciones de 001 bajo `benchmarks/` y pruebas de terreno/cazador bajo `tests/`.
- Propuesta de registro en `main.py` únicamente mediante una integración conjunta acordada; no es archivo propio de Sofía.

### Puntos de integración pendientes

- **Steven**: `5000d1f` integra costo/rango, simetría de sentidos existentes y persistencia v10 de esos campos; acepta sentidos únicos. Aceptó la firma `proximo_paso(...) -> ResultadoRuta` y asignó rutas/vista del cazador a Sofía. La vista conocida de 003 y la persistencia conjunta completa siguen abiertas: [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md).
- **Joshua**: la interfaz base introducida por `972af542…` y el enlace de historial de `927d886…` están integrados en `Sofia@3df43c6…`: deshacer/rehacer temporal, fotografía y `vincular_linea`. T005 cerró la revisión cruzada de esa interfaz y T040 redactó las pruebas contra el protocolo remoto. La clase completa `LineaTiempo`, el guardado coordinado y la ejecución local T056 siguen pendientes: [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md).
- **Spec 002**: la versión integrada resolvió las dos observaciones revisadas: un fallo al obtener ubicaciones deja la cripta sin verificar y bloquea el inicio salvo `--forzar` (`FR-011`, `FR-019`), y retiró la divulgación de contenido de rutas frente a la niebla. Solo se permite identificar al enemigo que custodia una llave, excepción exigida para ubicarla. 001 no modifica ese spec ni su recorrido; el índice conserva orden e identidad y los costos no alteran la resolubilidad. Como hallazgo de implementación, `InicializadorPartida._verificar()` captura `CriptaAPIError` y `ValueError`, mientras `convertir_llaves()` puede producir `TypeError` ante un ID de sala de tipo inválido; ese borde no se corrige desde 001.
- **Spec 004**: reconstruye hacia atrás desde el punto de control siguiente, deshaciendo como máximo K transacciones y rehaciendo con inversos en `finally`. Re-simular hacia adelante existe solo como alternativa de `--bench`. Su FR-022 necesita costos y cazadores canónicos, pero no cachés de ruta. No se modifica `specs/004-linea-de-tiempo`.

## Phase 0 Output

[research.md](research.md) fija las alternativas, la decisión medida (R-13) y el diseño de producción. FR-002 fue enmendada documentalmente antes del código para aceptar salidas sin inversa y comparar solo pares existentes. G1/G2 y T005 están cerradas; permanecen abiertas la vista conocida (T004), `LineaTiempo` completa y persistencia (T006), la conexión `--bench` (T049/T050) y la referencia oficial (T051).

## Phase 1 Outputs

- [data-model.md](data-model.md): entidades canónicas, derivadas, validaciones y transiciones.
- [contracts/propuesta-steven-rutas-datos.md](contracts/propuesta-steven-rutas-datos.md): resultado cerrado en T002 y estrategia de reutilización del cazador cerrada en T057; vista conocida y guardado siguen pendientes.
- [contracts/propuesta-joshua-cambios-reversibles.md](contracts/propuesta-joshua-cambios-reversibles.md): interfaz base y revisión cruzada disponibles localmente; T040 está redactada, mientras `LineaTiempo` completa, ejecución T056 y guardado siguen pendientes.
- [quickstart.md](quickstart.md): guía futura de validación, matriz completa de escenarios y `--bench`.

## Post-Design Constitution Check

**Puerta de diseño satisfecha con condiciones abiertas**. G1/G2, T005 y la interfaz base reversible están disponibles. No están locales la vista conocida ni la clase completa `LineaTiempo`; la persistencia conjunta restante y la medición de 5 ms con 003 siguen pendientes. T049 registra hoy solo el proveedor de mapa, no rutas/agenda/ciclo.

## Risks and Pending Agreements Before Tasks

1. **Integración de datos con Steven**: G1/G2 cerradas en `5000d1f`; costo/rango, firma/resultado, archivos de Sofía y política de sentidos únicos están confirmados. Falta la vista conocida de 003.
2. **Contrato de «ir a» con Steven/003**: firma, recálculo y casos terminales están confirmados; bloquean la integración la entrega de la vista de 003 y evidencia conjunta de 5 ms.
3. **Integración histórica con Joshua**: la interfaz base y `vincular_linea` están disponibles localmente; T005 cerró la revisión cruzada. `LineaTiempo` completa, cada fotografía de cambios nuevos de 001, las pruebas conjuntas y el guardado siguen abiertos. No hay invalidación de rutas mientras producción recalcule sin retener estado.
4. **Referencia oficial**: la carga exacta puede ser publicada o enmendada. Hasta entonces los sintéticos preparan la matriz, pero no demuestran `PR-001`.
5. **Elección de estrategia**: individual es la decisión medida (R-13). Compartida/adaptativa o cualquier reutilización de «ir a» solo se seleccionará con resultados de costo completo, equivalencia y tareas productivas; la referencia oficial sigue pendiente.
6. **Persistencia coordinada**: v10 de costo/rango está integrada; mapa conocido y línea completa aún requieren campos, compatibilidad y prueba conjunta.
7. **Componentes compartidos**: el diseño no exige ampliar `MonticuloMinimo`. El registro en `main.py` requiere tarea conjunta y no autoriza edición unilateral.

## Complexity Tracking

No aplica: el plan no introduce violaciones constitucionales.
