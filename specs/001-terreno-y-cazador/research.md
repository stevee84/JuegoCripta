# Research: Terreno y cazador

Este documento registra decisiones de diseño provisionales. Las afirmaciones de rendimiento son hipótesis que `--bench` debe confirmar; no son resultados medidos.

## R-01 — Estrategia provisional de rutas

**Decision**: usar una búsqueda ponderada individual, desde cada cazador y limitada por su rango, como estrategia de producción inicial (`FR-007`–`FR-010`, `PR-002`). Para la integración propuesta con «ir a», calcular también cada siguiente paso de forma individual con origen, destino y conocimiento vigentes. Implementar la alternativa inversa compartida como comparación de `--bench`, no como optimización asumida.

**Rationale**: la búsqueda individual no inserta candidatos cuyo costo ya supere el rango y solo expande salas fijadas dentro de él. Como los costos son positivos, una ruta que ya excedió el rango no puede volver a entrar. Esto evita recorrer o inicializar el exterior, aunque dentro de la región pertinente deben contarse por separado salas fijadas, salas descubiertas y todas las entradas almacenadas en frontera. También reduce el riesgo de invalidación y ofrece una referencia de producción simple frente a la cual validar reutilización.

**Alternatives considered**:

- **Una búsqueda inversa completa desde el jugador**: amortiza trabajo entre decenas de cazadores, pero paga potencialmente `V+E` aunque un único cazador tenga rango pequeño.
- **Búsqueda inversa limitada al rango máximo activo**: puede compartir trabajo, pero un solo rango grande amplía la región para todos y requiere gestionar cazadores fuera de la región.
- **Estrategia adaptativa**: prometedora, pero el umbral depende de cantidad/distribución de cazadores, rangos y estabilidad de puertas. No se fija sin datos.

**Measurement completed (2026-11-14)**: T046/T065 y T048 midieron uno frente a muchos cazadores, rango pequeño/grande, individual/compartida/reutilizada y puertas estables/inestables. La alternativa compartida/reutilizada fue más rápida en la matriz sintética y pasó la equivalencia observable, pero producción conserva el recálculo individual porque adoptar estado retenido exige tareas productivas nuevas y validación del ciclo completo; la referencia oficial sigue sin publicarse. La decisión medida del cazador se registra en R-13. T054 midió separadamente «ir a» con `Viaje`/`VistaMapaConocido` reales y T066 cerró su decisión sin caché; los resultados y límites están en R-14.

## R-02 — Desempate independiente del descubrimiento

**Decision**: en búsqueda hacia adelante, propagar la etiqueta `(distancia, primera_vecina_id)` y priorizar lexicográficamente; usar `sala_id` solo como tercer componente determinista (`FR-011`, `FR-015`). En la alternativa inversa, calcular distancias y seleccionar al final el mínimo `(costo_salida + distancia_vecino, vecino_id)`.

**Rationale**: el primer componente obtiene el costo mínimo y el segundo codifica exactamente la regla observable. Con pesos positivos, un camino alternativo de igual costo llega a través de un predecesor con menor distancia, por lo que puede actualizar el objetivo antes de que este se fije. La prioridad por primera vecina impide que el orden de las puertas o de inserción decida el resultado.

**Alternatives considered**:

- **Aceptar el primer camino encontrado**: rechazado; depende del orden de descubrimiento.
- **Ordenar previamente todas las listas de vecinos**: insuficiente por sí solo y prohibiría apoyarse en `sorted()`/`.sort()`; una ruta descubierta después aún puede empatar con primera vecina menor.
- **Reconstruir un único predecesor al final**: insuficiente si los empates intermedios descartaron la primera vecina correcta.

## R-03 — Estructuras auxiliares propias y perezosas

**Decision**: reutilizar `MonticuloMinimo` con entradas inmutables duplicadas y `TablaHashImpl` para mejores etiquetas y salas fijadas. Se verificó que el montículo actual tiene `insertar`, `extraer_minimo`, `ver_minimo` y eliminación de una referencia conocida, pero no una operación para actualizar prioridad. Cada mejora inserta otra entrada; al extraer, se descarta si no coincide con la mejor etiqueta vigente o la sala ya fue fijada. El diseño no usa actualización en sitio ni atribuye decrease-key al montículo.

**Rationale**: cumple la constitución y evita inicializar `V` posiciones por cazador o mantener un handle mutable por sala. Si `D_R` es la cantidad de salas distintas descubiertas, `E_R` cuenta todas las salidas inspeccionadas —también las cerradas—, `P_R` las entradas insertadas y `Q_R` la frontera máxima, la memoria es O(`D_R+Q_R`), con peor caso O(`D_R+E_R`) porque cada relajación exitosa puede insertar un duplicado. El tiempo esperado completo es O(`E_R + P_R log max(2,Q_R) + Q_fin`), incluyendo salidas examinadas, inserciones/extracciones vigentes u obsoletas y limpieza de la frontera restante.

**Alternatives considered**:

- **Arreglo indexado por ID**: los IDs no garantizan densidad y su inicialización global viola el objetivo de rango pequeño.
- **`heapq`, `dict`, `set` o bibliotecas de rutas**: prohibidos en producción.
- **Una entrada por sala con actualización de prioridad**: requeriría una operación que el montículo actual no publica o un contrato nuevo de handles/eliminación y reinserción; se descarta para mantener el cambio mínimo y medir explícitamente los duplicados.
- **Explorar linealmente la menor distancia**: sirve como alternativa comparable/oráculo, pero cuesta O(`D_R²+E_R`) para las salas descubiertas y salidas examinadas.

## R-04 — Índice de `MapaCripta`

**Decision**: conservar `_salas` para recorrido determinista y referencias, y añadir `TablaHashImpl` ID→sala. Para un ID existente, localizar linealmente su posición O(`V`), sustituir allí, actualizar la tabla y revincular todas las salidas antes de volver a exponer un mapa ya vinculado. No se añade un índice de posiciones para optimizar una operación infrecuente. Las consultas del turno y las rutas nunca usan el recorrido lineal.

**Rationale**: `obtener_sala` actual es O(`V`) y `vincular_salidas` puede llegar a O(`EV`). La tabla ofrece O(1) esperado y amortizado por inserción, con O(`V`) peor caso por colisiones. La lista conserva el contrato observable de recorrido que un hash no garantiza. Sustituir conserva la posición, pero cuesta O(`V+E`) esperado por la búsqueda lineal y el pase que vuelve a resolver cada `destino_sala`; así las referencias entrantes dejan de apuntar a la instancia antigua. El peor caso de esa revinculación es O(`V·E`) si el hash degenera.

**Ownership and agreement**: `MapaCripta` es código de Sofía y Steven solicitó expresamente que Sofía implemente este índice después de identificar el recorrido lineal como cuello de botella de 002. La mención histórica de «componente compartido» exige conservar el contrato para sus consumidores, no impide modificar un componente propio cuando el cambio ya fue solicitado. No se encontró un acuerdo explícito contradictorio. Se conservan las firmas públicas, el orden de `obtener_salas()`, la identidad de cada `Sala`, la sustitución en la misma posición y los alias de `Puerta.destino_sala`.

**Measurement**: T072–T076 conectan a `--bench` tres intervalos independientes: construir lista+índice, consultar IDs y vincular salidas. Consultas y vinculación se comparan con recorridos lineales que viven solo en `benchmarks/mapa_cripta_integrante1.py`. Se usan varios tamaños/densidades y cargas equivalentes; antes de cronometrar se comparan IDs, ausencias, orden, destinos y la identidad exacta de las salas. La generación del fixture queda fuera y no se mezclan construcción, consulta y enlace en una sola cifra.

**Alternatives considered**:

- **Mantener solo lista lineal**: rechazado por Constitución II y por multiplicar el costo de cada búsqueda.
- **Reemplazar la lista por hash**: rechazado; perdería orden estable y contrato de referencias/recorrido.
- **Usar `dict`**: prohibido como índice.

## R-05 — Reutilización e invalidación

**Decision**: recalcular cada decisión en la primera versión y liberar sus auxiliares al terminar. En «ir a», cada paso vuelve a consultar con origen, destino y mapa conocido vigentes, semántica aceptada por Steven. No hay caché, generación o instantánea productiva que invalidar. Las instantáneas compartidas y la reutilización viven únicamente en `benchmarks/` hasta que una decisión posterior a las mediciones justifique planificar su adopción (`FR-014`, `FR-016`).

**Rationale**: calcular desde cero es la referencia normativa y minimiza el riesgo inicial. Exigir ahora generaciones e invalidación convertiría una alternativa no seleccionada en complejidad de producción. En el benchmark, una generación permite medir invalidación O(1) y memoria pendiente de reclamar. Si se adopta después, la caché deberá permanecer fuera del estado y 004 la dejará intacta durante `historia` porque restaura exactamente el estado vivo.

**Alternatives considered**:

- **Invertir cada mutación de la caché en el historial**: rechazado; mezcla estado derivado con canónico y aumenta `C` sin valor observable.
- **Añadir invalidación sin adoptar reutilización**: rechazado; no hay estado retenido que descartar.
- **No invalidar después de retroceso si una reutilización futura se adopta**: rechazado; una versión monotónica puede no representar el estado restaurado y conservar referencias obsoletas.
- **Invalidar al consultar `historia`**: rechazado; la consulta no decide rutas y restaura el estado vivo. Invalidar alteraría innecesariamente un derivado que 004 no alcanza.
- **Observadores de cada atributo canónico**: rechazados; duplican el registro reversible y acoplan 004 a las cachés. La ejecución normal usa dependencias específicas y las fronteras de retroceso/inicio-carga usan invalidación explícita.
- **Invalidación selectiva por puerta**: candidata futura; necesita índice puerta→resultados y medición de ahorro. No se justifica antes de comparar con recálculo.

## R-06 — Matriz de dependencias

**Decision**:

- puertas abiertas/cerradas y costos determinan distancias;
- sala del jugador determina el objetivo compartido;
- sala/rango del cazador determinan su consulta;
- velocidad determina tiempos de agenda, no distancias;
- movimiento/muerte de otros actores no bloquean rutas, pero cambian el lote de actores activos;
- contenido descargado y niebla no afectan al cazador (`FR-013`, `FR-014`).

**Rationale**: separa invalidación de rutas de reprogramación temporal y evita invalidar todo ante cambios irrelevantes, sin asumir que todas las mutaciones tienen el mismo efecto.

**Alternatives considered**: una generación global para cualquier cambio es correcta pero puede eliminar toda reutilización. Solo se planificará como fallback si la reutilización es habilitada por medición; no forma parte de la producción de recálculo.

## R-07 — Integración del costo de movimiento

**Decision**: mantener `calcular_intervalo(costo, velocidad)` y hacer que cada ejecución de `MOVER` entregue el costo de la salida realmente atravesada. Las demás acciones conservan `costo_base`; el cazador espera/ataca con las reglas heredadas (`FR-003`–`FR-005`, `FR-012`).

**Rationale**: existe una única fórmula para todos los actores y no se duplican reglas de velocidad. El resultado de acción ya es el punto que el motor usa para programar el siguiente turno.

**Alternatives considered**:

- **Cambiar la constante global `COSTO_MOVER`**: no representa salidas distintas.
- **Aplicar el costo solo al jugador o solo al cazador**: contradice FR-003/FR-005.
- **Modificar `costo_base` para recibir una puerta en todas las acciones**: ensancha innecesariamente un contrato compartido.

## R-08 — Estado reversible y línea de tiempo

**Decision**: registrar solo mutaciones canónicas mediante la transacción abierta y `logica.mutaciones`/cambios de agenda existentes; costos y rangos son datos inmutables de la versión cargada. La producción inicial no conserva cachés. Cada cambio nuevo debe ser compatible con el gancho local `fotografiar_para_rehacer(inverso, estado)`. Si una decisión futura adopta reutilización, sus puntos de invalidación se planificarán entonces; no invalidar por `historia`.

**Rationale**: `Sofia@3df43c63c68a33f692148b737c12b0c0a4208569` integra `972af5421d628171a4464709858275b100151c1e` y `927d8860639f3efa6260172d3e03cae61f74301b`: están locales `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, `fotografiar_para_rehacer` y `HistorialReversible.vincular_linea`. 001 consume esa interfaz y no copia ni modifica clases de Joshua. Añadir snapshots por decisión violaría Constitución VII. La excepción de pergaminos permanece en el servicio de inventario y no se replica en rutas.

**Estado observado (actualizado 2026-11-15)**: la interfaz base, el enlace del historial y `LineaTiempo` están locales; T005/T040/T056 verifican su protocolo. `5000d1f` introdujo guardado v10 de costo/rango y `d1ad048` entregó v11 con el bloque conjunto de línea/estado, incluido `mapa_conocido`. T006/T041/T055 verifican persistencia y restauración sin resultados de ruta retenidos.

**Compatibilidad exigida por 004**: cada cambio nuevo de 001 debe poder copiarse profundamente junto con el estado y su ventana de transacciones, conservando referencias hacia las entidades copiadas. También debe poder serializarse con el `pickle` conjunto de estado vivo y línea propuesto para el formato que finalmente acuerden Steven y Joshua. No puede retener motor, servicio de rutas, caché, callbacks ni recursos externos. Estas propiedades se prueban; no se dan por demostradas por el acuerdo documental.

**Alternatives considered**:

- **Guardar mapa/estado completo por turno**: prohibido.
- **Persistir cachés de ruta en checkpoints o hacerlas alcanzables desde cambios**: innecesario; no son observables, inflarían `deepcopy`/`pickle` y pueden reconstruirse.
- **Confiar en que una caché vieja “probablemente” sirve**: contradice FR-014.

## R-09 — Oráculos de corrección

**Decision**: para grafos pequeños, enumerar rutas simples de forma exhaustiva y escoger por `(costo, primera_vecina)`; para matrices de benchmark mayores, usar una relajación completa independiente sobre listas. Antes de medir, comparar únicamente la decisión observable: acción, alcanzabilidad/dentro de rango, costo total, primera vecina y costo del paso (`PR-004`, `PR-006`). El trabajo, orden de descubrimiento, cantidad de entradas y frontera pueden diferir; se instrumentan y comparan aparte, sin exigir igualdad con el oráculo.

**Rationale**: un oráculo con estructura y recorrido distintos detecta errores de frontera, parada anticipada y desempate que una segunda invocación del mismo algoritmo ocultaría.

**Alternatives considered**:

- **Comparar la implementación consigo misma**: no es independiente.
- **`networkx` como único oráculo**: permitido solo en benchmark, pero no verifica por sí solo el desempate específico y añade una dependencia innecesaria.
- **Logs dorados únicamente**: útiles para Apéndice B, pero no cubren combinaciones generadas.

## R-10 — Diseño de `--bench`

**Decision**: preparar una tupla propia de proveedores de 001 y coordinar con el propietario de `main.py` su registro único en la concatenación entregada a `benchmarks.integrante3.ejecutar`; conservar los proveedores actuales, conectar el ciclo real y medir rutas, reutilización experimental y las seis operaciones de agenda. El fixture común se prepara fuera; todo trabajo requerido por la operación/ciclo permanece dentro.

**Rationale**: la constitución exige una vía ejecutable y comparaciones; los scripts aislados no bastan. `main.py` ya concatena `PROVEEDORES_MAPA`, parte entregada de T049. Rutas/ciclo de 001 aún no están registrados; la agenda común no sustituye las seis operaciones de `PR-005`.

**Alternatives considered**:

- **Microbenchmarks aislados solamente**: no demuestran el ciclo de 20 ms.
- **Cronometrar carga HTTP**: mezcla latencia externa con simulación y contradice el alcance del límite.
- **Sacar creación de auxiliares de ruta del cronómetro**: oculta el costo que paga cada decisión.

## R-11 — Contratos entre integrantes

**Decision**: distinguir siempre checkout local, publicación remota y acuerdo comunicado. Registrar el acuerdo parcial con Steven y la aceptación condicionada de Joshua sin presentar otra rama como integrada ni un acuerdo como implementación.

**Rationale**: `Sofia@5000d1f` integra costo/rango estrictos, simetría entre sentidos existentes y persistencia v10 de esos campos. Steven aceptó `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta` con los cuatro observables acordados y asignó a Sofía rutas/vista del cazador; el equipo acepta sentidos sin inversa. La vista conocida y `LineaTiempo` están integradas; `d1ad048` entrega su persistencia conjunta v11 y T006/T041/T055 la verifican. La validación histórica `1204 passed, 4 subtests passed` fue comunicada sobre la base v10; la auditoría actual ejecutó separadamente 7 pruebas conjuntas y 144 regresiones relacionadas.

**Alternatives considered**: modificar directamente los archivos compartidos o asumir una firma. Ambas se rechazan porque crearían contratos de hecho sin revisión.

## R-12 — Frontera de «ir a» y resultado del buscador

**Decisión aceptada por Steven**: `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta`. El resultado inmutable publica `alcanzable`, `costo_total`, `primera_vecina_id` y `costo_primera_salida`, más métricas separadas. Devuelve un único siguiente paso, no una secuencia completa, y «ir a» recalcula antes de cada paso. `ATACAR` y `ESPERAR` quedan fuera. Origen igual a destino produce `alcanzable=True`, costo 0 y sin paso; ausencia de ruta/límite insuficiente produce `alcanzable=False` sin costo ni paso.

**Rationale**: decidir un paso por vez permite aplicar §3.4 con origen, destino y conocimiento actuales, y evita que una ruta calculada con puertas recordadas antiguas se trate como compromiso futuro. Separar el resultado geométrico de la acción impide introducir reglas de combate o espera en un servicio reutilizado por 003.

**Vista confirmada por Steven**: solo contiene salas exploradas y solo enumera, desde ellas, puertas recordadas abiertas hacia otras salas exploradas. Steven construirá la vista y una prueba futura donde estados reales distintos con el mismo mapa conocido producen el mismo resultado. La capacidad `contiene_sala`/`salidas_transitables` está aceptada, pero no sus firmas definitivas ni los archivos compartidos que cada integrante editará.

**Alternatives considered**:

- **Devolver la ruta completa**: rechazada como propuesta de Sofía porque puede quedar obsoleta antes del siguiente paso y ensancha el contrato.
- **Usar el mapa real y filtrar después**: rechazada; puede filtrar información oculta aun si la presentación final la omite.
- **Confundir origen=destino con sin ruta**: rechazada; son estados semánticamente distintos para 003.

## R-13 — Decisión real de estrategia del cazador (T057)

**Decision**: la producción conserva el **recálculo individual por cazador y por decisión**, sin caché, generación ni estado retenido. La inversa compartida y su variante reutilizada permanecen exclusivamente en `benchmarks/terreno_cazador_integrante1.py` y `benchmarks/benchmark_ciclo_real_integrante1.py`. La estrategia adaptativa no se adopta: no existe un umbral medido que justifique cambiar de estrategia según cantidad de cazadores, rango o estabilidad de puertas.

**Rationale**: el recálculo individual ya era la referencia normativa del plan y la única vía productiva implementada. La evidencia sintética **favorece en tiempo** a la inversa compartida/reutilizada en las cargas medidas; no demuestra que el recálculo sea más rápido. Se conserva el recálculo porque adoptar estado retenido exige (a) planificar tareas productivas concretas con propietario y archivos, (b) validar invalidación y limpieza frente a todos los cambios de `FR-014`, no solo las puertas de T048, y (c) repetir el ciclo completo con la referencia oficial. Nada de eso está acordado. La decisión es final para el alcance productivo actual —no crear caché ni cambiar producción—, pero no selecciona un umbral adaptativo ni descarta una adopción futura con evidencia y tareas nuevas.

**Equivalence evidence**:

- T046/T065 comparó las tres alternativas antes de cada reloj sobre el mismo fixture y exige igualdad de acción, alcanzabilidad, costo total, primera vecina y costo del primer paso. Todas las filas conservadas pasaron esa comprobación.
- T048 comparó el ciclo completo productivo con la retención experimental sobre la misma plantilla, acción `ESPERAR`, semilla 2609 y carga. La huella previa al cronómetro incluyó reloj, secuencia, agenda, salas, enemigos, puertas, jugador, azar, resultado y orden de notificaciones. Los 288 ciclos sintéticos clasificaron `completo`, sin rechazos, muertes, victorias, terminales, incompletos ni errores.
- Los contadores internos de la alternativa retenida no se comparan con producción (`PR-006`); solo se comparan los observables.

**Full-cost evidence** (medianas; no se comparan cocientes entre tablas porque las cargas difieren):

| Escenario | Individual productivo | Inversa compartida | Inversa reutilizada |
|---|---:|---:|---:|
| T046: 64 salas, 20 cazadores, rango 640, 3 ciclos, puertas estables | 26 813 300 ns/lote | 587 200 ns/lote | 301 700 ns/lote |
| T046: misma carga, cambios frecuentes de puertas | 18 713 300 ns/lote | 662 300 ns/lote | 586 800 ns/lote |

| T048: 64 salas, 28 cazadores, rango 16 400, un ciclo completo | Producción individual | Retención experimental |
|---|---:|---:|
| Puertas estables | 20.5445 ms de mediana; p95/máx. 36.8259 ms; 7/9 muestras `>=20 ms` | 3.1269 ms; p95/máx. 4.0276 ms; 0/9 |
| Puertas inestables | 17.9640 ms; p95/máx. 33.2342 ms; 2/9 | 2.6901 ms; p95/máx. 3.6784 ms; 0/9 |

**Clasificación recuperada de las nueve muestras `>=20 ms`:**

| Escenario / estrategia | Muestras lentas (índice: ms) | Carga | Mediana / p95 / máximo de la fila | Trabajo instrumentado por muestra |
|---|---|---|---|---|
| puertas estables / `ciclo_corriente_recalculo_produccion` | 1: 20.5445; 2: 20.4867; 4: 21.7241; 5: 22.2237; 6: 20.0708; 7: 21.0831; 8: 36.8259 | 64 salas, 28 cazadores activos, rango 16 400, `ESPERAR`, costos 100–130, 28 eventos enemigos | 20.5445 / 36.8259 / 36.8259 ms | 28 notificaciones, 28 eventos enemigos, 0 eventos de puerta, sin cierres |
| puertas inestables / `ciclo_corriente_recalculo_produccion` | 5: 33.2342; 6: 22.9758 | 64 salas, 28 cazadores activos, rango 16 400, `ESPERAR`, costos 100–130, 24 eventos enemigos y 1 evento de puerta | 17.9640 / 33.2342 / 33.2342 ms | 24 notificaciones, 24 eventos enemigos, 1 evento de puerta, cierre `p2-1` |

Las nueve muestras clasifican `completo`, con `exito=true`; ninguna pertenece a la estrategia retenida. La retención experimental incluye construcción, consultas, invalidación, reconstrucción y limpieza dentro del intervalo. En estable realizó 26 consultas, una construcción, ninguna invalidación y examinó 135 salidas; en inestable realizó 23 consultas, una construcción, una invalidación por `puertas`, una reconstrucción y examinó 267 salidas. Producción no expone contadores internos de ruta: sus filas solo reportan notificaciones y eventos observables y declaran `contadores_internos_comparados=false`. Por ello estas nueve duraciones no permiten atribuir la demora a una fase interna ni derivar un umbral adaptativo.

**Complexity**: el recálculo individual conserva el costo de R-01/R-03: `O(E_R + P_R log max(2,Q_R) + Q_fin)` esperado por cazador, con memoria `O(D_R+Q_R)` y peor caso `O(D_R+E_R)`. La inversa compartida paga una construcción `O(E_L + P_L log max(2,Q_L) + Q_fin_L)` y luego la selección de cada cazador; la reutilizada añade consultas y, cuando cambian las puertas, invalidación y reconstrucción. El benchmark mide esos componentes por separado; no se atribuye a la variante retenida un coste que no se haya cronometrado.

**Limits**:

- Son cargas sintéticas de un solo equipo; no son la referencia oficial de `PR-001` ni permiten afirmar cumplimiento o incumplimiento del límite de 20 ms.
- T046 usa 20 cazadores y tres ciclos por lote; T048 usa 28 cazadores y un ciclo completo por muestra. Sus medianas no son intercambiables ni justifican una comparación causal entre sí.
- La alternativa compartida/reutilizada no se adopta y no existe caché productiva. Cualquier adopción futura requiere actualizar primero `plan.md`/`tasks.md` con tareas productivas concretas, definir la invalidación y repetir la validación de ciclo completo.
- La estrategia adaptativa sigue sin umbral medido; no se implementó.
- T049/T050 conectaron y ejecutaron estas filas mediante `main.py --bench`: la evidencia oficial conserva 194 filas/2910 muestras de 001 dentro de un informe completo de 916 filas. Siguen siendo cargas sintéticas y no cierran PR-001 ni sustituyen la referencia oficial pendiente.

**Trazabilidad**: `logica/rutas_ponderadas.py`; `logica/comportamiento_enemigos.py`;
`benchmarks/terreno_cazador_integrante1.py`; `benchmarks/benchmark_ciclo_real_integrante1.py`;
`benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json`;
`benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json`;
`specs/001-terreno-y-cazador/tasks.md` (T046, T048, T057, T065).

## R-14 — Decisión de reutilización para «ir a» (T066)

**Decision**: conservar en producción el **recálculo completo en cada paso de «ir a»**, sin caché,
generación ni estado de ruta retenido. La inversa reutilizable permanece exclusivamente en
`benchmarks/terreno_cazador_integrante1.py`. Esta decisión es independiente de R-13: que el
cazador y «ir a» compartan el buscador no obliga a que compartan una política de reutilización.

**Rationale**: el criterio vigente exige menos de 5 ms con el mapa conocido completo de la cripta
de referencia. En la mayor cripta publicada disponible (`cripta-04`, 50 salas exploradas), el
recálculo productivo obtuvo 15/15 muestras bajo el límite, incluidas la creación real de `Viaje` y
`VistaMapaConocido` y los auxiliares que `proximo_paso` crea y libera. Por tanto, no hay una
necesidad de rendimiento que justifique introducir una caché productiva y sus obligaciones de
invalidez. La alternativa experimental demuestra que reutilizar es viable, no que sea necesario.

**Equivalence and knowledge evidence**:

- Antes de cada medición se compararon recálculo e inversa experimental en siguiente sala,
  alcanzabilidad, costo total, costo de la primera salida y motivo de parada.
- Los sintéticos comprueban empate por menor primera vecina, puerta recordada cerrada, ausencia de
  camino y un nuevo atajo que solo puede usarse después de pasar de avistado a explorado.
- Ambas alternativas reciben `VistaMapaConocido`; ninguna consulta el mapa real ni una sala no
  explorada. El mapa publicado se carga y explora fuera del intervalo; red y decodificación no se
  atribuyen al paso.
- La consulta reutilizada solo se considera válida mientras el conocimiento no cambia. Las filas
  de conocimiento actualizado construyen nuevamente sobre la vista vigente; no se reutiliza una
  instantánea anterior como si siguiera siendo válida.

**Measured full cost** (15 repeticiones, un calentamiento, ns convertidos a ms):

| Carga / estado | Recálculo mediana / p95 / máx. | Muestras que cumplen `<5 ms` | Inversa fría mediana / p95 / máx. | Consulta reutilizada mediana |
|---|---:|---:|---:|---:|
| 32, empate | 0.2895 / 0.4029 / 0.4029 | 15/15 | 0.1311 / 0.1835 / 0.1835 | 0.0079 |
| 32, puerta cerrada | 0.2744 / 0.2823 / 0.2823 | 15/15 | 0.1092 / 0.1176 / 0.1176 | 0.0055 |
| 32, conocimiento actualizado | 0.0554 / 0.0655 / 0.0655 | 15/15 | 0.1173 / 0.1319 / 0.1319 | 0.0076 |
| 32, sin camino | 0.0132 / 0.0152 / 0.0152 | 15/15 | 0.1070 / 0.1221 / 0.1221 | 0.0042 |
| 128, empate | 1.0906 / 1.5156 / 1.5156 | 15/15 | 0.4060 / 0.4298 / 0.4298 | 0.0065 |
| 128, puerta cerrada | 1.0958 / 1.4903 / 1.4903 | 15/15 | 0.4446 / 0.6648 / 0.6648 | 0.0058 |
| 128, conocimiento actualizado | 0.0555 / 0.0586 / 0.0586 | 15/15 | 0.4072 / 0.4496 / 0.4496 | 0.0071 |
| 128, sin camino | 0.0142 / 0.0181 / 0.0181 | 15/15 | 0.4152 / 0.4587 / 0.4587 | 0.0045 |
| 512, empate | 4.9585 / 12.4589 / 12.4589 | 9/15 | 1.6261 / 1.7028 / 1.7028 | 0.0066 |
| 512, puerta cerrada | 4.7594 / 5.6072 / 5.6072 | 12/15 | 1.8904 / 2.4974 / 2.4974 | 0.0068 |
| 512, conocimiento actualizado | 0.0635 / 0.0684 / 0.0684 | 15/15 | 2.0905 / 4.1043 / 4.1043 | 0.0094 |
| 512, sin camino | 0.0146 / 0.0176 / 0.0176 | 15/15 | 1.7512 / 2.1633 / 2.1633 | 0.0047 |
| `cripta-04`, 50, conocimiento completo | **0.4965 / 0.5136 / 0.5136** | **15/15** | 0.2510 / 0.3344 / 0.3344 | 0.0036 |

La inversa fría incluye crear `Viaje`/vista, construir sus tablas/listas/distancias, consultar y
limpiar; la consulta reutilizada se informa aparte y no se resta de ese costo. La memoria se mide
en una corrida `tracemalloc` separada. La columna de muestras que cumplen no cuenta las
superaciones: en 512 salas, desempate tiene 9/15 que cumplen y 6/15 que superan; puerta cerrada,
12/15 que cumplen y 3/15 que superan. En total, producción conservó 186/195 muestras sintéticas y
publicadas bajo 5 ms; las nueve superaciones pertenecen únicamente a esas dos cargas de 512 salas
(6 + 3). La alternativa experimental tuvo 195/195 muestras frías bajo el límite. Estos resultados
favorecen la inversa en recorridos largos, pero el recálculo fue más rápido cuando el nuevo atajo
resolvió el paso de inmediato o no había salida transitable; no existe un ganador universal.

**Complexity**: el recálculo conserva el costo de R-03 sobre el subgrafo conocido alcanzado,
`O(E_R + P_R log max(2,Q_R) + Q_fin)` esperado y memoria `O(D_R+Q_R)`. La inversa fría barre todas
las salidas conocidas, construye distancias al destino y paga su limpieza; una consulta estable
posterior inspecciona solo las salidas del origen, pero cualquier cambio relevante de conocimiento
obliga a invalidar o reconstruir antes de decidir.

**Limits and future coordination**:

- Las cargas de 512 salas son sintéticas y mayores que las criptas publicadas. Sus nueve muestras
  `>=5 ms` se conservan como límite real; no se redujo la carga ni se ajustó el umbral.
- El cumplimiento de 5 ms corresponde al mapa conocido completo de la cripta publicada de 50
  salas disponible localmente. No es una afirmación sobre PR-001, cuyo ciclo oficial es otro
  requisito y sigue bloqueado por T051.
- Si una referencia futura mayor o una topología nueva hace necesario retener estado, no se adopta
  automáticamente esta inversa. Primero deben acordarse con 003 tareas y archivos para propietario
  de la caché, generación/invalidez ante exploración y puertas recordadas, ciclo de vida y limpieza,
  y pruebas tras retroceso, historia, inicio y carga. Hasta entonces no existe caché productiva.

**Evidence**: `benchmarks/resultados/paso_ir_a_t054_c1_r15_32-128-512-publicado50.json` conserva
26 filas/390 muestras, entorno Windows/Python 3.12.10, semilla 2609, fases, trabajo, percentiles y
memoria. La medición es propia de 001 y no reemplaza ni modifica
`benchmarks.integrante2.medir_paso_ir_a`.

## R-15 — Vigencia metodológica de las filas de mapa conocido en T050

**Decision**: conservar sin cambios la ejecución T050 y sus JSON como registro histórico real y
reproducible, pero no usar como evidencia vigente de SC-002/SC-003 las filas producidas con la
metodología anterior de `benchmarks.integrante2.medir_mapa_conocido`. La validación corregida es la
publicada posteriormente por Steven en `1734a70` (SC-003) y `d59752d` (SC-002), documentada en
`specs/003-niebla-y-ir-a/contracts/respuesta-sofia-sc003.md` y `DECISIONES.md` §5.3.

**Alcance exacto dentro de las 916 filas de T050**:

| Medición histórica | Filas / repeticiones | `n` | Metodología anterior | Vigencia |
|---|---:|---|---|---|
| `mapa_conocido_explorar_una_sala` | 6 / 90 | 9, 16, 25, 64, 121, 484 | construía el conocimiento completo y volvía a explorar `salas // 2`; produjo cero revelaciones y objetivos de grado distinto | registro histórico; no demuestra SC-003 |
| `mapa_conocido_estado_sala` | 6 / 90 | 9, 16, 25, 64, 121, 484 | una pasada por todas las salas, por lo que `consultas_por_lote == n`; los lotes comparados no eran iguales | operación válida, pero esas filas no demuestran actualmente SC-002 |
| `mapa_conocido_estado_recorriendo_alternativa` | 6 / 90 | 9, 16, 25, 64, 121, 484 | alternativa emparejada con la misma cantidad variable de consultas | comparación histórica; tampoco es evidencia vigente de SC-002 |

Las dos métricas principales reúnen 12 filas/180 repeticiones; al incluir la alternativa necesaria
para la comparación de SC-002 son **18 filas/270 repeticiones** con metodología anterior. Las filas
históricas sí registran medianas y mínimos de 15 repeticiones, pero no el lote fijo comparable que
exige la revisión vigente. La corrección de Steven usa 2 000 consultas fijas y medianas para SC-002;
para SC-003 usa hasta ocho salas interiores separadas, comprueba revelaciones positivas equivalentes
antes del reloj, normaliza por revelación y compara medianas alternando el orden.

**Límites de la reclasificación**:

- No se reescriben ni eliminan `main_bench_completo_t050.json` ni sus resultados; la corrida y su
  código de salida 0 siguen demostrando que los 25 proveedores se ejecutaron y fueron capturados.
- Las 18 filas señaladas están en el informe completo, no en
  `resultados_terreno_cazador_integrante1.json`; las **194 filas/2910 muestras** propias de mapa,
  agenda, rutas y ciclo de 001 conservan íntegramente su alcance original.
- Los dos commits correctivos de Steven solo cambian las tres series identificadas. No se extrapola
  el hallazgo a las otras 898 filas de T050 ni se alteran decisiones sustentadas en otras cargas.
- T050 permanece cerrada como ejecución histórica. PR-001 no queda demostrado por ella y T051
  continúa abierta hasta que se publique la referencia oficial.

## R-16 — Auditoría de la referencia publicada y validación pendiente T051 (17/11/2026)

**Decisión vigente**: T051/AC-013/PR-001 permanece **abierta**. `cripta-06` ya está publicada;
el bloqueo actual es demostrar un ciclo con **decenas de cazadores realmente activos y
participantes**, no la ausencia del paquete. Esta actualización sustituye las menciones de
referencia pendiente en el estado vigente; las secciones anteriores conservan su contexto histórico.

### Datos reales y activación

La copia de `tests/fixtures/api_real/cripta-06/` tiene versión `f9ed9afa683d`, catálogo
`4b9e75a42be5`, **300 salas y 75 enemigos**. Hay 36 ratas rastreadoras, dos guardianes, un
carcelero errante y **36 cazadores**:

| Ficha | Cantidad | Rango de costo | Velocidad | Salas iniciales (un cazador por sala) |
|---|---:|---:|---:|---|
| `ent_sabueso_oseo` | 25 | 600 | 110 | 8, 11, 17, 19, 34, 41, 60, 98, 108, 134, 148, 151, 152, 163, 176, 190, 216, 230, 241, 251, 256, 268, 283, 289, 295 |
| `ent_espectro_acechador` | 11 | 2400 | 100 | 10, 31, 35, 68, 112, 123, 137, 177, 196, 249, 265 |

Las instancias publicadas no declaran activación inicial. El DTO comienza con `activo=False`;
la sala inicial 141 no tiene enemigos. Tras `MotorJuego.iniciar` hay **0 cazadores activos y 0
eventos pendientes**. Entrar en una sala activa sus enemigos vivos y programa su primer turno a
`reloj + max(1, 100*100//velocidad)` (90 para sabueso, 100 para espectro). Estar dentro del rango
no activa por sí solo a un enemigo. La activación persiste mientras siga vivo.

Cada evento `ENEMIGO` puede producir una decisión si el actor sigue activo, vivo y pertenece a su
sala. Compartir sala con el jugador vivo lleva a `ATACAR`; de lo contrario, un cazador consulta
`proximo_paso` sobre salidas abiertas y dirigidas, limitado por el costo acumulado de su rango.
Sin ruta dentro del rango decide `ESPERAR`, también reprograma turno y **no emite notificación**.
El movimiento paga el costo real de salida; ataque/espera cuestan 100. La agenda ordena por
tiempo/secuencia y se drena hasta la disponibilidad del jugador: un mismo cazador puede decidir
varias veces, o no tener un turno vencido en un intervalo corto.

El intervalo completo incluye validación/aplicación de la acción, presencia, activación y trampas
al entrar, agenda, decisiones y rutas, combate/mutaciones, historial y disponibilidad siguiente.
El motor también despacha `EFECTO`, `VENCER_EFECTO`, `TRAMPA`, `REARMAR_TRAMPA` y
`CERRAR_PUERTA`. `JUGADOR_DISPONIBLE` termina el ciclo; una muerte/victoria no se clasifica como
ciclo completo. No se confunden enemigos cargados, activos, actores participantes, decisiones,
eventos extraídos y avisos de presentación.

### Por qué el diagnóstico anterior no probaba PR-001

`_escenario_enemigos` elige el enemigo más cercano por puertas abiertas: desde 141 entra en 142,
que tiene una **rata**, no un cazador. `_escenario_efectos` usa una antorcha real de la sala inicial
y prepara su vencimiento. La repetición alternaba copias de esos dos estados; no exploraba las
300 salas ni acumulaba activaciones. La auditoría directa cuenta, respectivamente:

- un evento `ENEMIGO`, una decisión de rata y un aviso enemigo;
- un `VENCER_EFECTO`, ninguna decisión enemiga y ningún aviso enemigo;
- un `JUGADOR_DISPONIBLE` en cada caso y **0 decisiones de cazadores en ambos**.

En esos dos escenarios concretos no había decisiones de cazadores ocultas detrás de los 0–1
avisos. En general, sin embargo, `ESPERAR` demuestra por qué ese contador antiguo era insuficiente.
`t051_cripta06_diagnostico.json` se conserva intacto: sus 30 ciclos rápidos solo describen esa carga.

### Adaptación y recorrido reproducible

`benchmarks/benchmark_ciclo_real_integrante1.py` usa ahora el auxiliar propio
`benchmarks/auditoria_ciclo_referencia_integrante1.py`. Los contadores envuelven métodos de las
instancias del benchmark y siempre delegan al motor real; no sustituyen rutas ni decisiones.
Su costo está incluido en el tiempo total. La copia del estado inicial, inicialización y repetición
de acciones de preparación quedan fuera; se conserva el historial real del prefijo recorrido.
Los puntos de medición están fijados antes del cronómetro, sin elegir por sus tiempos.

El recorrido [publicado con el benchmark](../../benchmarks/recorridos/t051_cripta06.json) equipa
coraza/daga reales, recoge la llave de bronce, combate ratas y recoge/consume pociones reales.
No añade actores, estadísticas ni activaciones. Conserva **87 acciones: 86 ciclos completos y una
muerte final**, sin rechazos ni errores. Los puntos 11/37/55 parten de 1/3/5 cazadores activos.
Los cinco activados proceden de las salas 41, 123, 163, 265 y 283; corresponden a los IDs
`e-cripta-06-7`, `-6`, `-5`, `-9` y `-4`, respectivamente. El prefijo completo se reproduce antes
de cada muestra, para medir un estado alcanzado por el juego, sin reinicializar un estado avanzado
ni limpiar su historial/botín. La muerte posterior no se oculta ni se mezcla con las muestras completas.

Este recorrido **no consigue decenas**. Tampoco demuestra que todos los recorridos válidos de la
cripta sean incapaces de conseguirlas: queda pendiente encontrar y validar ese escenario o recibir
una aclaración/enmienda oficial. La presencia de 36 cazadores cargados no resuelve esa condición.

`cripta-05` es irresoluble: solo si la comprobación real confirma ese estado, el inicializador
local del benchmark reintenta con `forzar=True`. No se fuerza una verificación fallida/desconocida;
el inicio normal del juego sigue rechazando la cripta. La evidencia conserva el informe y el flag.

### Evidencia conservada y resultado

[Diagnóstico de actividad real](../../benchmarks/resultados/t051_cripta06_actividad_real.json):
Windows 11, Python 3.12.10, Intel64 Family 6 Model 154 Stepping 3, `perf_counter_ns`, semilla
20240517, caché 25, tres calentamientos y 30 muestras (10 por escenario):

| Activos / participantes distintos | Decisiones de cazadores / ciclo | Eventos totales / ciclo | Mediana / p95 / máximo (ms) |
|---|---:|---:|---|
| 1 / 1 | 1 | 2 | 0.1292 / 0.3592 / 0.3592 |
| 3 / 3 | 3 | 4 | 0.2862 / 0.7219 / 0.7219 |
| 5 / 5 | 6 | 7 | 0.6815 / 1.3282 / 1.3282 |

Cada fila de la tabla representa 10 intervalos; los eventos incluyen disponibilidad del jugador.
En el tercer escenario hay cinco movimientos y un ataque por ciclo: **6 decisiones no son 6
cazadores distintos**. Total medido: **100 decisiones de cazadores y 130 eventos**. Resumen de
las 30 muestras: mediana **0.2940 ms**, p95 **1.0614 ms**, máximo **1.3282 ms**, 30 ciclos completos,
0 rechazos/muertes/victorias/incompletos/errores, **0 ciclos `>=20 ms`**. Los tres calentamientos
también son completos. No hubo fallos de caché ni lecturas desde disco/fuente dentro de los relojes.

El JSON conserva todas las duraciones, comparación estricta `<20_000_000 ns`, versiones, carga
antes/después, IDs y decisiones/eventos ordenados, calentamientos, traza de preparación, auditoría
de los escenarios antiguos y SHA-256 de 56 archivos de datos y 55 archivos de código.
`resultado_requisito=BAJO_20MS_EN_CARGA_MEDIDA` y **`afirma_pr001=false`**: no se genera
`benchmarks/resultados_terreno_cazador_referencia.json`. El escritor rechaza sobrescribir archivos y
reserva ese nombre para una medición validada con al menos dos decenas de actores distintos por
ciclo, además del resto de condiciones. T048/T050 mantienen sus JSON, cifras y alcance históricos.

**Pruebas**: foco de ciclo/referencia, terreno, adaptadores, conexión y restricciones:
**125 passed in 3.82s** (64 focalizadas y 61 restricciones, sin omisiones). Se comprueba equivalencia
observable con/sin contadores, espera silenciosa, 20 ms exactos, rechazo de falsas conclusiones,
protección de evidencia y `cripta-05` con inicio normal rechazado y benchmark permitido.

## R-17 — Cierre documental de la exploración T051 (18/11/2026)

**Decisión**: detener los intentos exploratorios y mantener T051/AC-013/PR-001 **abierta**. Los
Prompts 79–83 mejoraron la evidencia reproducible desde los cinco participantes históricos hasta
nueve, pero no alcanzaron los 20 exigidos. No se relaja el mínimo, no se modifica producción y no se
genera `benchmarks/resultados_terreno_cazador_referencia.json`.

### Evidencia parcial reproducible

Los dos recorridos conservados cargan `cripta-06@f9ed9afa683d`, catálogo `4b9e75a42be5` y semilla
20240517, y ejecutan exclusivamente acciones legales mediante `MotorJuego.ejecutar_accion()` desde el
estado inicial:

| Diagnóstico | Acciones | Checkpoint final | Activos / participantes | Clasificación |
|---|---:|---|---:|---|
| `t051_prompt82_ocho_cazadores_parcial.json` | 250 | sala 71, 12 HP, 3 pociones | 8 / 8 | ciclo completo |
| `t051_prompt83_nueve_cazadores_parcial.json` | 299 | sala 109, 9 HP, 5 pociones | 9 / 9 | ciclo completo |

El parcial de ocho preserva los checkpoints reproducibles 58, 95, 135, 167 y 250. El de nueve añade
`e-cripta-06-39`, lo separa mediante el cierre automático 111–110 y mide como acción 299 un
`MOVER OESTE`. Los nueve IDs vivos y activos toman decisiones en el mismo ciclo; el intervalo procesa
nueve decisiones de cazador y la disponibilidad del jugador, no realiza I/O y registra
**1,292416 ms preliminares**. Esta duración describe únicamente la carga de nueve y no puede usarse
para afirmar PR-001.

### Límite observado y alcance de la conclusión

Después del ciclo, dos cazadores comparten sala con el jugador y un tercero queda en la sala
adyacente. El jugador conserva 9 HP: curarse o volver hacia C2 concede turnos de ataque concurrentes.
Ese bloqueo explica por qué no se amplió la exploración, pero **no demuestra imposibilidad global**.
La decisión es de entrega y estabilidad, no una enmienda del criterio. Los dos diagnósticos mantienen
`parcial=true` y `afirma_t051=false`; el resultado oficial sigue ausente y el avance de tareas se
mantiene en **75/76**, con T051 sin marcar.
