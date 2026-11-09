---

description: "Tareas ejecutables para Terreno y cazador"
---

# Tasks: Terreno y cazador

**Input**: artefactos de `specs/001-terreno-y-cazador/` y constitución 1.0.0.

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/propuesta-steven-rutas-datos.md` y `contracts/propuesta-joshua-cambios-reversibles.md`.

**Estado**: planificación solamente. El análisis del Prompt 39 y esta remediación documental ya ocurrieron fuera de las tareas de implementación. Todas las tareas de implementación, pruebas y verificación permanecen sin marcar; ninguna cobertura descrita aquí se considera ejecutada.

**Organización**: las fases 3–6 corresponden a las cuatro historias de usuario. Las dependencias de Steven/Joshua y las tareas conjuntas se distinguen en el texto de cada tarea para no asignar a Sofía cambios ajenos.

**Recuento tras remediación**: 76 tareas (T001–T076), sin reutilizar IDs; 22 oportunidades `[P]` reales. Historias: US1=9, US2=12, US3=12, US4=17. Las 26 restantes cubren setup, fundamento, integraciones y cierre documental.

## Formato: `[ID] [P?] [Story?] Descripción`

- **[P]**: puede ejecutarse en paralelo porque usa archivos distintos y no depende de una tarea incompleta de la misma fase.
- **[US1]…[US4]**: historia de usuario atendida.
- **Sofía**: tarea propia de implementación, prueba o documentación.
- **Dependencia (Steven/Joshua)**: entrega ajena que Sofía verifica, no implementa.
- **Conjunta**: requiere acuerdo o ejecución coordinada antes de integrar.

## Capacidades existentes que se reutilizan

- `logica/acciones.py`: `calcular_intervalo()` ya implementa `max(1, costo*100//velocidad)` y conserva costos base.
- `logica/motor_juego.py`, `logica/agenda_eventos.py` y `logica/mutaciones.py`: reprogramación con secuencia nueva, transacción abierta y cambios reversibles ya existen.
- `estructuras/monticulo_minimo.py` y `estructuras/tabla_hash.py`: estructuras propias disponibles; no se crea otro montículo ni otra tabla.
- `tests/test_dto/test_sala_copia_serializacion.py`: ya cubre `deepcopy`/`pickle`, alias Sala↔actor e índices de enemigos; solo se amplía para campos/cambios nuevos.
- `benchmarks/benchmark_ciclo_real_integrante1.py`, `benchmarks/benchmark_agenda_integrante1.py` y `benchmarks/integrante3.py`: se adaptan y conectan; no se sustituyen.

---

## Phase 1: Setup — puertas contractuales y análisis previo

**Purpose**: cerrar o verificar dependencias antes de crear contratos de hecho. Estas tareas no autorizan a Sofía a modificar entregas de compañeros.

- [ ] T001 Sofía — después de aplicar las correcciones documentales del Prompt 39, reejecutar `/speckit.analyze` sobre `.specify/memory/constitution.md` y `specs/001-terreno-y-cazador/{spec.md,plan.md,tasks.md}` como revisión posterior independiente; resultado verificable: el nuevo informe no mezcla análisis de solo lectura con remediación ni autoriza implementación (FR-001–FR-018, PR-001–PR-006).
- [ ] T002 Conjunta Sofía/Steven — acordar únicamente las firmas Python, protocolo y representación exacta de la operación de siguiente paso, conservando la semántica ya aceptada —paso único, origen=destino con costo 0 sin paso y ausencia de ruta distinguible— sin introducir `ATACAR`/`ESPERAR`; registrar nombres y tipos reales en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md` (FR-007–FR-014, PR-004, PR-006).
- [ ] T003 Dependencia (Steven) — publicar su entrega de costo/rango estrictos, default 100 solo por ausencia, identificación de sentidos por origen/destino, detección de salidas múltiples ambiguas y costos simétricos; registrar hash y archivos concretos publicados en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`. Esta tarea no asigna a Steven ni a Sofía DTO/inicialización compartidos y mantiene pendiente la política de una salida sin inversa (FR-001, FR-002, FR-009, FR-011, FR-017, FR-018).
- [ ] T004 Dependencia (Steven) — publicar la vista de mapa conocido solo de salas exploradas con las capacidades acordadas, recálculo por paso y prueba de independencia; registrar hash/rutas concretas en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`. Bloquea solo integración 001/003, no el cazador (FR-013, FR-014, PR-004, PR-006).
- [ ] T005 Dependencia integrada (Joshua), revisión conjunta — verificar cruzadamente en `Sofia@3df43c63c68a33f692148b737c12b0c0a4208569` que `logica/cambios.py`, `logica/historial_reversible.py`, `tests/test_logica/test_cambios_linea.py` y `tests/test_logica/test_historial_linea.py` contienen y conservan `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, `fotografiar_para_rehacer(inverso, estado)` y `vincular_linea`; distinguir esta interfaz base ya disponible de la clase completa `LineaTiempo`, todavía no integrada localmente, y no copiar ni modificar código de Joshua (FR-014–FR-016, PR-004).
- [ ] T006 Dependencia coordinada (Steven/Joshua) — publicar persistencia de costo/rango/mapa conocido y línea de tiempo con campos, compatibilidad, archivos y versión reales; registrar el hash verificado en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md` y `specs/001-terreno-y-cazador/contracts/propuesta-joshua-cambios-reversibles.md`. Steven asume esta entrega coordinada, pero v9 sigue siendo el único formato comprobado hasta entonces (FR-001, FR-009, FR-016, FR-018).

**Checkpoint**: los acuerdos semánticos no equivalen a entregas. La precondición de disponibilidad local de T005 ya existe, pero su revisión cruzada de proceso sigue abierta. T002–T006 pueden seguir abiertas mientras avanza trabajo no bloqueado; cada tarea posterior declara si necesita código local, publicación remota o solo el acuerdo.

---

## Phase 2: Foundational — índice de mapa compartido

**Purpose**: eliminar búsquedas lineales frecuentes sin alterar firmas, orden, identidad ni enlace de salas. Steven solicitó expresamente que Sofía implemente el índice de su `MapaCripta`; `plan.md` identifica los consumidores reales. La condición histórica de componente compartido exige compatibilidad, no una nueva reasignación. Bloquea US2–US4; US1 solo depende de este índice donde el motor busca destinos.

- [ ] T007 [P] Sofía — ampliar `tests/test_logica/test_mapa_cripta.py` con pruebas de índice ID→instancia, `contiene_sala`, orden estable de `obtener_salas()`, sustitución en la misma posición y revinculación de referencias entrantes; resultado verificable: lista e índice siempre señalan a la misma `Sala` y los IDs no enteros se rechazan (FR-011, FR-013, FR-018, PR-001, PR-002).
- [ ] T008 Sofía — implementar en `logica/mapa_cripta.py` un `TablaHashImpl` ID→sala conservando `_salas`, actualizarlo en altas/sustituciones y hacer O(1) esperado `obtener_sala`/`contiene_sala`; al sustituir, invalidar `_enlaces_listos` y revincular antes de exponer vecinos (FR-011, FR-013, FR-018, PR-001, PR-002).
- [ ] T009 Sofía — ampliar `tests/test_restricciones_enunciado.py` para comprobar que el índice de `MapaCripta` es `TablaHashImpl` y que las rutas de producción nuevas siguen sin `dict`, `set`, `heapq`, `bisect`, `collections`, ordenamientos o bibliotecas de grafos prohibidos (FR-011, FR-018, PR-001–PR-004).

**Checkpoint**: el mapa conserva firmas y recorrido determinista, y ofrece acceso frecuente esperado O(1), sin duplicar `MonticuloMinimo` ni `TablaHashImpl`. La política no confirmada de una salida sin inversa no bloquea este índice ni sus pruebas/benchmarks estructurales.

---

## Phase 3: User Story 1 — Transitar por terreno con costo (Priority: P1) 🎯 MVP

**Goal**: todo actor usa el costo validado de la salida solo al moverse; el resto de acciones y la reprogramación heredada permanecen iguales.

**Independent Test**: con dos salas y actores de distintas velocidades, comprobar costo ausente/presente/mínimo, intervalo, rechazo sin cambios y costos heredados sin activar cazadores.

**Blocked by**: T003 para datos validados; T006 únicamente para persistir/reanudar estos campos, no para desarrollar la historia con fuente fresca.

### Tests for User Story 1

- [ ] T010 [P] [US1] Sofía — crear `tests/test_datos/test_terreno_cazador_datos.py` para verificar la futura entrega de Steven: AC-001 usa 100 solo si `costo` falta, AC-019 rechaza valores presentes inválidos y AC-020 identifica por origen/destino costos contradictorios y multiplicidad ambigua; no afirmar rechazo de una salida sin inversa hasta aclararlo (FR-001, FR-002, FR-017, FR-018).
- [ ] T011 [P] [US1] Sofía — crear `tests/test_logica/test_terreno_movimiento.py` con AC-002 y AC-B06 para jugador, errante y rastreador: el movimiento cobra la salida atravesada y programa `max(1, costo_salida*100//velocidad)` (FR-003, FR-005, FR-018).
- [ ] T012 [P] [US1] Sofía — crear `tests/test_logica/test_terreno_compatibilidad.py` con AC-003 y rechazos de movimiento: atacar/esperar/usar/equipar/recoger/soltar/abrir conservan costo, y un rechazo deja reloj, actor, puertas, agenda e historial idénticos (FR-004, FR-005, FR-017, FR-018).
- [ ] T013 [P] [US1] Sofía — ampliar `tests/test_logica/test_velocidad.py` con AC-B07 para una salida costosa y ambos tipos de actor, verificando tiempo restante proporcional, identidad del evento, secuencia estrictamente nueva y reversión exacta (FR-003, FR-006, FR-016, FR-018).
- [ ] T014 [P] [US1] Sofía — ampliar `tests/test_contrato_api_real.py` con una carga offline de al menos dos criptas que compruebe que los costos provienen de fixtures/servicio, no de constantes de una cripta, y que resolubilidad no cambia al variar solo pesos válidos (FR-001–FR-003, FR-018).
- [ ] T015 [P] [US1] Sofía — ampliar `tests/test_integracion_sofia.py` para comparar dos ejecuciones del mismo movimiento ponderado y exigir el mismo `ResultadoAccion.costo`, reloj, evento y registro observable (FR-003, FR-015, FR-018).

### Implementation for User Story 1

- [ ] T016 [US1] Sofía — modificar `logica/motor_juego.py` para que `_aplicar_accion(MOVER)` del jugador devuelva el costo de la `Puerta` atravesada y use el `calcular_intervalo` existente, sin cambiar `costo_base` de otras acciones; resultado verificable: T011/T012 pasan (FR-003, FR-004, FR-017, FR-018).
- [ ] T017 [US1] Sofía — modificar `logica/motor_juego.py` para que `_turno_enemigo` conserve la puerta concreta seleccionada y programe movimientos errante/rastreador con su costo, manteniendo ataque/espera y demás conductas heredadas; resultado verificable: cada movimiento enemigo cobra exactamente una salida (FR-003–FR-005, FR-012, FR-018).
- [ ] T064 [US1] Sofía — después de T003/T016/T017, ejecutar `tests/test_datos/test_terreno_cazador_datos.py`, `tests/test_logica/test_terreno_movimiento.py`, `tests/test_logica/test_terreno_compatibilidad.py`, `tests/test_logica/test_velocidad.py`, `tests/test_contrato_api_real.py` y `tests/test_integracion_sofia.py`, y registrar el resultado real en `specs/001-terreno-y-cazador/quickstart.md`; escribirlas antes no equivale a poder cerrarlas antes de la entrega local de Steven (FR-001–FR-006, FR-017, FR-018).

**Checkpoint**: US1 solo se considera cerrada cuando T064 pasa con la entrega de datos disponible localmente; guardado conjunto, buscador y 004 pueden seguir pendientes.

---

## Phase 4: User Story 2 — Persecución observable del cazador (Priority: P1)

**Goal**: el cazador ataca en la misma sala; en otro caso espera o mueve un único paso por la ruta abierta mínima dentro de rango con desempate estable.

**Independent Test**: usar grafos pequeños sintéticos y un oráculo exhaustivo independiente para comparar acción, costo total, primera vecina y costo del paso, sin contenido remoto ni niebla.

**Blocked by**: T002 para materializar resultado/firma; T003 para `rango`; T007–T009 para acceso por ID. No depende de T004 ni de la vista de «ir a».

### Tests for User Story 2

- [ ] T018 [P] [US2] Sofía — ampliar `tests/test_datos/test_terreno_cazador_datos.py` con AC-021: `rango` cumple literalmente “entero mayor o igual que 0”; ausencia, negativo, booleano, texto o fracción rechazan la ficha identificándola y sin default (FR-009, FR-017, FR-018).
- [ ] T019 [P] [US2] Sofía — crear `tests/test_logica/test_rutas_ponderadas.py` con oráculo de rutas simples para AC-B01, AC-B02, AC-005, AC-B03, AC-B04 y AC-022, permutando el orden incidental de salidas y verificando mínimo `(costo_total, primera_vecina_id)` (FR-008–FR-011, FR-013, FR-015).
- [ ] T020 [P] [US2] Sofía — crear `tests/test_logica/test_cazador_ponderado.py` con AC-004 y AC-023 para probar que compartir sala produce `ATACAR` antes del buscador incluso con rango 0 y salidas abiertas (FR-007, FR-009, FR-018).
- [ ] T021 [P] [US2] Sofía — crear `tests/test_logica/test_cazador_integracion.py` con AC-006 y AC-007: mueve solo la primera salida, cobra esa salida y decide igual con contenidos remotos descargados distintos (FR-010, FR-012, FR-013, FR-018).
- [ ] T022 [P] [US2] Sofía — crear `tests/test_logica/test_contrato_rutas_ponderadas.py` después de T002 para probar las firmas acordadas, IDs enteros estrictos, origen=destino, ausencia de ruta, límite inclusivo y ausencia de mutaciones/descargas (FR-008–FR-011, FR-013, FR-017).
- [ ] T023 [P] [US2] Sofía — ampliar `tests/test_logica/test_comportamiento_enemigos.py` para asegurar que guardianes, errantes y rastreadores conservan decisiones anteriores mientras el nuevo comportamiento `cazador` permanece separado (FR-004, FR-005, FR-018).

### Implementation for User Story 2

- [ ] T024 [US2] Sofía — crear en `logica/rutas_ponderadas.py` las entradas inmutables y el resultado exacto acordado en T002, ordenados por `(distancia, primera_vecina_id, sala_id)` y sin exponer una ruta completa; resultado verificable: empates no dependen del descubrimiento (FR-010, FR-011, FR-015).
- [ ] T025 [US2] Sofía — implementar en `logica/rutas_ponderadas.py` la búsqueda individual limitada por rango con `MonticuloMinimo` y `TablaHashImpl`, entradas duplicadas sin decrease-key, descarte de obsoletas y liberación de frontera; resultado verificable: no inserta distancia mayor al límite y coincide con T019 (FR-008–FR-011, FR-013, PR-002).
- [ ] T026 [US2] Sofía — implementar en `logica/rutas_ponderadas.py` la vista del cazador sobre esqueleto completo, costos reales y puertas actualmente abiertas, sin consultar contenido descargado ni mapa conocido (FR-009–FR-014).
- [ ] T027 [US2] Sofía — integrar `comportamiento == "cazador"` en `logica/comportamiento_enemigos.py`: atacar antes de buscar, esperar costo 100 sin ruta/dentro de límite falso y devolver solo `MOVER` con la primera vecina cuando corresponda (FR-007–FR-013, FR-018).
- [ ] T028 [US2] Sofía — integrar en `logica/motor_juego.py` la ejecución del paso del cazador usando identidad de sala/enemigo, helpers reversibles existentes y costo de la puerta elegida; resultado verificable: no abre puertas y T020/T021 pasan (FR-007, FR-010, FR-012, FR-013, FR-016–FR-018).
- [ ] T029 [US2] Sofía — ejecutar y corregir únicamente la integración propia en `tests/test_logica/test_rutas_ponderadas.py`, `tests/test_logica/test_cazador_ponderado.py` y `tests/test_logica/test_cazador_integracion.py` hasta que US2 pase de forma independiente, sin presentar T004/T006 como resueltas (FR-007–FR-018, PR-006).

**Checkpoint**: US2 ofrece persecución correcta desde cero; no requiere reutilización, vista de «ir a», persistencia nueva ni interfaces históricas futuras.

---

## Phase 5: User Story 3 — Decisiones vigentes, deterministas y reversibles (Priority: P1)

**Goal**: toda decisión equivale al cálculo desde cero sobre estado vigente y los cambios de terreno/cazador se deshacen sin romper alias ni determinismo.

**Independent Test**: alterar puertas, jugador, velocidad y otros actores entre turnos; comparar con cálculo desde cero; retroceder un intervalo y repetir la continuación.

**Blocked by**: US2; T005 solo para pruebas de historia/deshacer temporal; T006 solo para `pickle` del paquete conjunto. Con recálculo sin estado retenido no hay invalidación productiva que implementar.

### Tests for User Story 3

- [ ] T030 [P] [US3] Sofía — crear `tests/test_logica/test_cazador_vigencia.py` con AC-B05, AC-008, AC-016, AC-017 y AC-018, comparando cada decisión posterior con una invocación independiente desde cero y sin exigir invalidaciones idénticas para cambios irrelevantes (FR-006, FR-013, FR-014, PR-006).
- [ ] T031 [US3] Sofía — después de T030/T032–T039, ejecutar `tests/test_logica/test_cazador_vigencia.py`, `tests/test_logica/test_cazador_determinismo.py`, `tests/test_logica/test_terreno_cazador_retroceso.py`, `tests/test_logica/test_terreno_cazador_copia.py` y `tests/test_logica/test_rutas_sin_estado_retenido.py` hasta que pasen con recálculo desde cero, registrando el resultado en `specs/001-terreno-y-cazador/quickstart.md`; AC-009 experimental se cubre después en T065 sin dependencia circular con US4 (FR-006, FR-013–FR-018, PR-006).
- [ ] T032 [P] [US3] Sofía — crear `tests/test_logica/test_cazador_determinismo.py` con AC-010: dos estados con misma cripta/versiones/semilla/acciones y orden incidental permutado producen decisiones, tiempos, secuencias y `partida.log` idénticos (FR-011, FR-015, FR-018).
- [ ] T033 [P] [US3] Sofía — crear `tests/test_logica/test_terreno_cazador_retroceso.py` con AC-011: mover/esperar/atacar/cerrar/reprogramar dentro del intervalo, usar pergamino, restaurar sala/vida/reloj/agenda/puertas salvo la excepción de pergaminos y repetir continuación determinista (FR-006, FR-014–FR-016, FR-018).
- [ ] T034 [P] [US3] Sofía — ampliar `tests/test_dto/test_sala_copia_serializacion.py` solo para los campos canónicos nuevos `Puerta.costo`, rango materializado y coherencia lista/índice de `MapaCripta` tras `deepcopy`/`pickle`, reutilizando las comprobaciones existentes de cantidad/orden/IDs, índices de enemigos y alias sin duplicar su lógica (FR-001, FR-009, FR-011, FR-016, FR-018).
- [ ] T035 [P] [US3] Sofía — crear `tests/test_logica/test_terreno_cazador_copia.py` para `copy.deepcopy((estado, transacciones))`: cada cambio nuevo apunta a la entidad copiada, no al estado vivo, y ningún objeto copiado alcanza motor, servicio o caché (FR-014–FR-016, FR-018).
- [ ] T036 [P] [US3] Sofía — crear `tests/test_logica/test_rutas_sin_estado_retenido.py` para verificar que cada consulta productiva libera montículo/tablas, que estado/transacciones no alcanzan auxiliares y que decisiones tras `RETROCEDER`, `iniciar` o `historia` se recalculan sin depender de ganchos de caché (FR-014–FR-016, PR-003, PR-006).

### Implementation for User Story 3

- [ ] T037 [US3] Sofía — asegurar en `logica/rutas_ponderadas.py` que la vía productiva de recálculo crea y libera auxiliares dentro de cada consulta y no expone instantáneas, generaciones ni cachés; las alternativas compartida/reutilizada viven solo en `benchmarks/terreno_cazador_integrante1.py` (FR-013–FR-016, PR-003, PR-006).
- [ ] T038 [US3] Sofía — auditar `logica/motor_juego.py` para que `RETROCEDER`, `iniciar` e `historia` no incorporen ganchos de invalidación innecesarios mientras no exista estado de ruta retenido; resultado verificable: la siguiente decisión usa una consulta nueva y no hay observadores de atributos (FR-014–FR-016).
- [ ] T039 [US3] Sofía — auditar y ajustar en `logica/motor_juego.py` todas las mutaciones nuevas de cazador mediante `atributo`, `agregar`, `quitar_identidad`, `registrar` y registro de agenda dentro de la transacción abierta; resultado verificable: abortar/deshacer no deja cambios parciales (FR-016–FR-018).
- [ ] T040 [US3] Conjunta Sofía/Joshua — después de T005, **escribir** en `tests/test_integracion_001_004.py` pruebas de `deshacer_mientras`, inversos en `finally`, `fotografiar_para_rehacer` para cada cambio nuevo e `historia` sin ejecutar rutas; su ejecución satisfactoria se cierra únicamente en T056 (FR-014–FR-016, PR-004, PR-006).
- [ ] T041 [US3] Conjunta Sofía/Steven/Joshua — después de definir T006, **escribir** `tests/test_datos/test_guardado_terreno_cazador.py` para ida/vuelta del formato conjunto, alias, costo/rango/mapa conocido y ausencia de resultados de ruta; no asumir versión y reservar la ejecución satisfactoria para T055 (FR-001, FR-009, FR-014–FR-016, FR-018).

**Checkpoint**: T031 cierra el núcleo de US3 con recálculo; T040/T041 solo escriben integraciones y T055/T056 las ejecutan cuando las entregas están disponibles localmente.

---

## Phase 6: User Story 4 — Evidencia de escala y carga nueva (Priority: P2)

**Goal**: `--bench` demuestra corrección y costo completo de rutas/ciclo/agenda con sintéticos, y separa la validación oficial todavía bloqueada.

**Independent Test**: ejecutar `main.py --bench` offline y comprobar filas, alternativas, equivalencia previa, semillas, calentamiento, repeticiones, carga, unidad, trabajo y percentiles requeridos.

**Blocked by**: US1–US3 para medir rutas y ciclo de producción; el benchmark independiente del mapa requiere T008, no costo/rango ni la política no confirmada de salidas sin inversa. La referencia oficial pendiente bloquea solo T051.

### Tests for User Story 4

- [ ] T042 [US4] Sofía — crear `tests/test_bench_terreno_cazador.py` con un oráculo exhaustivo para grafos pequeños y relajación completa independiente para matrices mayores, fallando antes de cronometrar ante divergencias de acción, alcance/rango, costo total, primera vecina o costo del paso (PR-002–PR-004, PR-006).
- [ ] T043 [US4] Sofía — después de T042, ampliar el mismo `tests/test_bench_terreno_cazador.py` para exigir filas de AC-012, AC-014 y AC-015 y el **esquema/salida de AC-013** —identificador de ciclo real, origen sintético/oficial, carga, unidad y muestras— sin exigir aún resultados oficiales; incluir seis operaciones de agenda y costo completo (PR-001–PR-006).

### Implementation for User Story 4

- [ ] T044 [US4] Sofía — crear `benchmarks/terreno_cazador_integrante1.py` con generadores sintéticos deterministas, oráculos independientes e instrumentación de fijadas `F`, descubiertas `D`, salidas `E`, inserciones `P`, frontera `Q`, obsoletas, limpieza y memoria (PR-002–PR-004, PR-006).
- [ ] T045 [US4] Sofía — implementar en `benchmarks/terreno_cazador_integrante1.py` AC-012 comparando la misma región dentro de rango mientras crece solo el exterior; resultado verificable: el informe separa trabajo regional de `V/E` total y no afirma complejidad solo por tiempo (PR-002, PR-004, PR-006).
- [ ] T046 [US4] Sofía — implementar **solo en** `benchmarks/terreno_cazador_integrante1.py` AC-014 con individual/compartida, uno/decenas, rango pequeño/grande, recálculo/reutilización y puertas estables/inestables, incluyendo construcción, consulta, invalidación y limpieza; ninguna clase experimental pasa a producción (PR-003, PR-004, PR-006).
- [ ] T047 [US4] Sofía — implementar en `benchmarks/terreno_cazador_integrante1.py` AC-015 para insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates con cientos de eventos, comparando `AgendaEventos` con una **lista lineal manual local al benchmark** que busca/retira por recorrido; no modificar ni reimplementar la agenda productiva (PR-004, PR-005, PR-006).
- [ ] T048 [P] [US4] Sofía — adaptar `benchmarks/benchmark_ciclo_real_integrante1.py` para ciclos con decenas de cazadores y costos variables, manteniendo carga/copia fuera y acción, agenda y rutas dentro; incluir invalidación/limpieza únicamente en la variante experimental que retenga estado y etiquetar sintético frente a referencia oficial (PR-001, PR-003, PR-004, PR-006).
- [ ] T049 [US4] Conjunta Sofía/propietario de `main.py` — después de T044–T048/T073–T075, acordar y ejecutar la integración mínima en `main.py` para registrar una sola vez los proveedores de rutas de 001, `benchmarks/mapa_cripta_integrante1.py` y el adaptador del ciclo real, preservando proveedores existentes; la tarea no autoriza a Sofía a editar unilateralmente este punto compartido (PR-001–PR-006).
- [ ] T050 [US4] Sofía — después de T049/T073–T075, ejecutar los benchmarks sintéticos mediante `main.py --bench` y guardar evidencia reproducible en `benchmarks/resultados_terreno_cazador_integrante1.json` con filas separadas de mapa/rutas/agenda/ciclo, entorno, semilla, calentamiento, repeticiones, mediana, p95/máximo, carga, unidad, trabajo y alternativa, sin presentarla como referencia oficial (PR-002–PR-006).
- [ ] T051 [US4] Sofía — cuando se publique la referencia oficial, ejecutar AC-013 con decenas de cazadores y registrar en `benchmarks/resultados_terreno_cazador_referencia.json` cada ciclo `<20 ms`; mantener esta tarea bloqueada sin bloquear T042–T050 (PR-001, PR-004, PR-006).
- [ ] T065 [US4] Sofía — después de T046, ejecutar AC-009 en `tests/test_bench_terreno_cazador.py` comparando recálculo y reutilización **benchmark-local** en acción, primera vecina y costo para puertas estables/inestables; resultado verificable: no hay dependencia de US3 hacia una alternativa creada en US4 (FR-013, FR-014, PR-003, PR-006).
- [ ] T072 [P] [US4] Sofía — crear `tests/test_bench_mapa_cripta.py` para exigir que `main.py --bench` incluya filas separadas de construcción del índice, búsqueda por ID y vinculación de salidas, con varios tamaños y cargas equivalentes; antes de aceptar tiempos, comprobar mismos IDs/orden, mismos resultados de aciertos y ausencias, y que cada `Puerta.destino_sala` sea la instancia canónica correspondiente (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [ ] T073 [US4] Sofía — después de T008, crear `benchmarks/mapa_cripta_integrante1.py` con generadores deterministas de varios tamaños/densidades y una fila exclusiva para construir `_salas` más el índice propio, separando generación del fixture, construcción medida y memoria; la alternativa lineal permanece local al benchmark y recibe exactamente las mismas instancias en el mismo orden (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [ ] T074 [US4] Sofía — después de T073, añadir en `benchmarks/mapa_cripta_integrante1.py` búsqueda por ID del índice frente a recorrido lineal benchmark-local, con secuencias equivalentes de aciertos al inicio/medio/final y ausencias para varios tamaños; validar identidad/ausencia y la secuencia completa de resultados antes de cronometrar únicamente las consultas (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [ ] T075 [US4] Sofía — después de T073, añadir en `benchmarks/mapa_cripta_integrante1.py` vinculación de salidas antes/lineal frente a después/indexada sobre grafos equivalentes de varios `V/E`, cronometrando la vinculación aparte de construcción y consultas; antes de comparar tiempos, verificar orden de salas/puertas, destinos, alias e identidad canónica de todas las referencias (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).

**Checkpoint**: sintéticos y conexión a `--bench` pueden completarse antes de la referencia; ninguna alternativa se adopta por intuición.

---

## Phase 7: Integraciones coordinadas no bloqueantes para el MVP

**Purpose**: completar fronteras con 003/004 y guardado sin convertir trabajo ajeno en tarea de Sofía.

- [ ] T052 Conjunta Sofía/Steven/003 — después de T002/T004, crear `tests/test_integracion_ir_a_001_003.py` para dos estados reales con el mismo mapa conocido, paso único, recálculo tras cada cambio de origen/destino/conocimiento, origen=destino y sin ruta distintos; resultado verificable: nunca consulta estado oculto (FR-011, FR-013–FR-015, PR-004, PR-006).
- [ ] T053 Sofía — después de T002/T004, exponer en `logica/rutas_ponderadas.py` la firma acordada para que «ir a» calcule un siguiente paso desde la vista de Steven, manteniendo recálculo individual como implementación suficiente y sin añadir reglas de ataque/espera (FR-010, FR-011, FR-013–FR-015, PR-004, PR-006).
- [ ] T054 Conjunta Sofía/003 — añadir al proveedor `benchmarks/terreno_cazador_integrante1.py` la medición completa de un paso de «ir a» frente a 5 ms, primero con sintéticos y finalmente con el mapa conocido oficial; incluir preparación auxiliar necesaria y equivalencia antes del tiempo (FR-013–FR-015, PR-003, PR-004, PR-006).
- [ ] T055 Conjunta Steven/Joshua con verificación de Sofía — después de T006 y usando `tests/test_datos/test_guardado_terreno_cazador.py` escrita en T041, **ejecutar** la ida/vuelta contra `datos/guardado_binario.py` y `service/restaurador_partida.py` publicados, comprobando costo/rango/mapa conocido, paquete histórico, alias y ausencia de resultados de ruta; Sofía no implementa campos ajenos (FR-001, FR-009, FR-016, FR-018).
- [ ] T056 Conjunta Sofía/Joshua — después de T005/T040 y de integrar por el flujo del equipo la clase completa `LineaTiempo`, **ejecutar** `tests/test_integracion_001_004.py` sobre puntos de control, estado vivo e inversos en `finally`, comprobando que cada cambio nuevo ofrece fotografía y que 004 nunca llama al cazador; la interfaz base local por sí sola no cierra esta ejecución (FR-014–FR-016, PR-004, PR-006).
- [ ] T057 Sofía — después de T046/T065, documentar en `specs/001-terreno-y-cazador/research.md` la decisión real de estrategia del **cazador** —individual, compartida o adaptativa— con equivalencia y costo completo; si se adopta estado retenido, actualizar primero plan/tasks con tareas productivas concretas, y si no, no crear caché (FR-013, FR-014, PR-003, PR-006).
- [ ] T066 Conjunta Sofía/003 — después de T054, documentar separadamente en `specs/001-terreno-y-cazador/research.md` la decisión de reutilización para **«ir a»** frente a 5 ms; cumplir con recálculo cierra la decisión sin caché, y cualquier adopción exige primero nuevas tareas con propietario/archivos acordados (FR-013–FR-015, PR-003, PR-004, PR-006).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: cerrar trazabilidad, restricciones, evidencia real y regresión completa sin confundir planificación con ejecución.

- [ ] T058 [P] Sofía — ejecutar `.venv/Scripts/python.exe -m pytest -q tests/test_restricciones_enunciado.py` y corregir infracciones únicamente en los archivos propios señalados; resultado verificable: estructuras/rutas de producción cumplen la constitución (FR-011, FR-018, PR-001–PR-006).
- [ ] T059 Sofía — auditar la matriz AC→FR/PR→tareas→pruebas de `specs/001-terreno-y-cazador/tasks.md` contra los 30 escenarios de `spec.md`, corregir cualquier hueco y confirmar los siete AC-B explícitos (FR-001–FR-018, PR-001–PR-006).
- [ ] T060 Sofía — ejecutar con `.venv/Scripts/python.exe` todas las pruebas previstas de US1–US4 y las integraciones no bloqueadas, registrando aprobadas/omitidas/fixtures/en línea por separado en `specs/001-terreno-y-cazador/quickstart.md` (FR-001–FR-018, PR-001–PR-006).
- [ ] T061 Sofía — ejecutar `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` y resolver regresiones propias hasta conservar toda la suite; registrar conteo real sin reutilizar una línea base anterior en `specs/001-terreno-y-cazador/quickstart.md` (FR-004, FR-005, FR-015–FR-018, PR-006).
- [ ] T062 Sofía — ejecutar `main.py --bench`, revisar que las filas de 001 —incluidas construcción/búsqueda/vinculación del mapa— estén conectadas una sola vez y documentar resultados sintéticos frente a límites sin afirmar PR-001 oficial en `specs/001-terreno-y-cazador/quickstart.md` (PR-001–PR-006).
- [ ] T063 Sofía — actualizar `specs/001-terreno-y-cazador/plan.md` y `specs/001-terreno-y-cazador/research.md` con resultados reales, estrategia final, costo completo, restricciones revisadas y bloqueos que sigan abiertos; no marcar acuerdos/pruebas ausentes ni reservar una versión de guardado (FR-001–FR-018, PR-001–PR-006).
- [ ] T067 Sofía — escribir en `DECISIONES.md` la sección §5.1 con problema, alternativas individual/compartida/adaptativa, decisión medida, complejidad, evidencia de `--bench`, límites, enlaces a spec/plan y divergencia frente al plan original (FR-007–FR-015, PR-002–PR-004, PR-006).
- [ ] T068 Sofía — escribir en `DECISIONES.md` la sección §5.2 con recálculo frente a reutilización, puertas estables/inestables, eventos relevantes, decisión medida, costo de invalidación/limpieza si aplica, límites y enlaces (FR-014, PR-003, PR-004, PR-006).
- [ ] T069 Sofía — escribir en `DECISIONES.md` la parte de agenda de §5.6 con las seis operaciones, carga nueva, alternativa lineal benchmark-local, datos antes/después y conclusión aunque la decisión de Parte I se conserve (PR-005, PR-006).
- [ ] T070 Sofía — actualizar conjuntamente la sección Parte II de `README.md` con comandos de aceptación de 001, `main.py --bench`, ubicación de JSON sintético/oficial, entorno y cómo distinguir pruebas escritas, ejecutadas, omitidas y bloqueadas; coordinar el archivo compartido sin sobrescribir entradas ajenas (FR-018, PR-001–PR-006).
- [ ] T071 [US4] Sofía — ejecutar `tests/test_bench_terreno_cazador.py`, `tests/test_bench_mapa_cripta.py` y las filas sintéticas completas después de T043–T050/T065/T072–T075, registrar el cierre real de US4 y dejar AC-013 oficial explícitamente bloqueado por T051 si la referencia no está publicada (PR-001–PR-006).
- [ ] T076 [US4] Sofía — después de T050/T071, crear en `DECISIONES.md` una subsección propia titulada **«Índice por ID de MapaCripta (evidencia complementaria de 001)»**, separada de §5.4 Resolubilidad, con resultados de construcción, búsqueda por ID y vinculación antes/después, tamaños/cargas, alternativa lineal benchmark-local, identidad comprobada, complejidad observada y divergencias frente a la hipótesis previa; añadir desde la revisión de decisiones de §5.6 un enlace explícito a esa subsección, sin reescribir §5.4, reatribuir el componente ni modificar decisiones de 002 (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).

---

## Matriz de cobertura AC → FR/PR → tareas → pruebas previstas

| AC | FR/PR | Tareas principales | Prueba prevista |
|---|---|---|---|
| AC-001 | FR-001, FR-002 | T003, T010, T016–T017 | `tests/test_datos/test_terreno_cazador_datos.py`, `tests/test_logica/test_terreno_movimiento.py` |
| AC-002 | FR-003 | T011, T016–T017 | `tests/test_logica/test_terreno_movimiento.py` |
| AC-003 | FR-004, FR-005 | T012, T016–T017 | `tests/test_logica/test_terreno_compatibilidad.py` |
| AC-B06 | FR-003 | T011, T016–T017 | `tests/test_logica/test_terreno_movimiento.py` |
| AC-B07 | FR-006 | T013 | `tests/test_logica/test_velocidad.py` |
| AC-019 | FR-001 | T003, T010 | `tests/test_datos/test_terreno_cazador_datos.py` |
| AC-020 | FR-002 | T003, T010 | `tests/test_datos/test_terreno_cazador_datos.py` |
| AC-004 | FR-007 | T020, T027–T029 | `tests/test_logica/test_cazador_ponderado.py` |
| AC-B01 | FR-008 | T019, T025, T027–T029 | `tests/test_logica/test_rutas_ponderadas.py` |
| AC-B02 | FR-008, FR-009 | T018–T019, T025, T027–T029 | `tests/test_logica/test_rutas_ponderadas.py` |
| AC-005 | FR-009, FR-010 | T019, T024–T029 | `tests/test_logica/test_rutas_ponderadas.py` |
| AC-B03 | FR-009, FR-010 | T019, T024–T025 | `tests/test_logica/test_rutas_ponderadas.py` |
| AC-B04 | FR-011 | T007–T009, T019, T024–T025 | `tests/test_logica/test_mapa_cripta.py`, `tests/test_logica/test_rutas_ponderadas.py` |
| AC-006 | FR-010, FR-012 | T021, T024–T029 | `tests/test_logica/test_cazador_integracion.py` |
| AC-007 | FR-013 | T021, T026–T029 | `tests/test_logica/test_cazador_integracion.py` |
| AC-021 | FR-009 | T003, T018 | `tests/test_datos/test_terreno_cazador_datos.py` |
| AC-022 | FR-008, FR-009 | T019, T025, T027–T029 | `tests/test_logica/test_rutas_ponderadas.py` |
| AC-023 | FR-007, FR-009 | T018, T020, T027–T029 | `tests/test_logica/test_cazador_ponderado.py` |
| AC-B05 | FR-014 | T030, T036–T039 | `tests/test_logica/test_cazador_vigencia.py`, `tests/test_logica/test_rutas_sin_estado_retenido.py` |
| AC-008 | FR-014 | T030, T037–T039 | `tests/test_logica/test_cazador_vigencia.py` |
| AC-009 | FR-013, FR-014 | T046, T065 | `tests/test_bench_terreno_cazador.py`, alternativa benchmark-local |
| AC-010 | FR-011, FR-015 | T032, T037–T039 | `tests/test_logica/test_cazador_determinismo.py` |
| AC-011 | FR-016 | T033, T035, T039–T041, T055–T056 | `tests/test_logica/test_terreno_cazador_retroceso.py`, `tests/test_integracion_001_004.py` |
| AC-016 | FR-014 | T030, T036–T039 | `tests/test_logica/test_cazador_vigencia.py`, `tests/test_logica/test_rutas_sin_estado_retenido.py` |
| AC-017 | FR-006, FR-014 | T013, T030, T036–T039 | `tests/test_logica/test_velocidad.py`, `tests/test_logica/test_cazador_vigencia.py` |
| AC-018 | FR-014 | T030, T037–T039 | `tests/test_logica/test_cazador_vigencia.py` |
| AC-012 | PR-002 | T042, T044–T045, T050 | `tests/test_bench_terreno_cazador.py`, fila AC-012 de `--bench` |
| AC-013 | PR-001 | T043, T048–T051, T071 | `tests/test_bench_terreno_cazador.py` comprueba esquema/salida; ejecución oficial pendiente de T051 |
| AC-014 | PR-003, PR-004 | T042–T046, T049–T050, T065 | `tests/test_bench_terreno_cazador.py`, fila AC-014 y equivalencia AC-009 |
| AC-015 | PR-005 | T043, T047, T049–T050, T069 | `tests/test_bench_terreno_cazador.py`, seis filas de agenda de `--bench` y decisión §5.6 |

**Cobertura adicional**: FR-017 se verifica en T010/T012/T022/T039; FR-018 en cierres T064/T029/T031, regresión T061 y mapa T072–T076; PR-006 en oráculos/benchmarks T042–T050/T065/T071–T075. La documentación oficial se cierra en T067–T070/T076. Los siete casos del Apéndice B son AC-B01…AC-B07 y aparecen explícitamente en la matriz.

### Cobertura constitucional adicional

| Verificación | Principio | Tareas | Evidencia prevista |
|---|---|---|---|
| Índice propio preserva firmas, orden e identidad | II, VIII | T007–T009 | `tests/test_logica/test_mapa_cripta.py`, prueba AST y regresiones consumidoras |
| Acceso por ID frente a recorrido lineal | II, IX | T072–T074, T049–T050, T071, T076 | fila `mapa_busqueda_id` conectada a `main.py --bench` y subsección propia enlazada desde §5.6 |
| Vinculación antes/lineal frente a después/indexada | II, VIII, IX | T072–T073, T075, T049–T050, T071, T076 | fila `mapa_vinculacion_salidas`, igualdad de referencias antes de medir |
| Construcción del índice separada de consultas/vinculación | II, IX | T072–T073, T049–T050, T071, T076 | fila `mapa_construccion_indice`, carga y memoria separadas |

---

## Dependencies & Execution Order

### Puertas bloqueantes precisas

| Puerta | Se cierra con | Bloquea | No bloquea |
|---|---|---|---|
| G1 — firma/representación del buscador | T002 | T022, T024, T052–T054 | semántica terminal ya acordada, US1, índice y pruebas sintéticas |
| G2 — costo/rango/simetría publicados e integrados | T003 | cierre de T010/T018, T016–T017, T027–T029 y T064 | escritura previa de oráculos/tests y algoritmo desacoplado |
| G3 — vista de mapa conocido | T004 | T052–T054 | cazador, porque usa su vista real independiente |
| G4a — revisión cruzada de interfaz Joshua ya integrada | T005 | T040 y precondición de T056 | disponibilidad local de interfaz base, `deepcopy` y recálculo |
| G4b — `LineaTiempo` completa integrada localmente | integración por flujo del equipo de la entrega publicada | ejecución T056 | escritura contractual T040 e interfaz base ya local |
| G5 — persistencia/versionado publicados | T006 | T041, T055 | desarrollo desde fuente fresca y benchmarks sintéticos |
| G6 — referencia oficial | publicación externa | T051 y validación oficial final de T054 | T042–T050, T072–T075, pruebas funcionales y medición sintética |

### Phase Dependencies

- **Phase 1**: T001 es la revisión posterior de la remediación ya aplicada y debe completarse antes de código. T002–T006 pueden avanzar en paralelo con trabajo que no bloqueen.
- **Phase 2**: después de T001; T008 depende de T007 y T009 verifica T008.
- **US1 (Phase 3)**: las pruebas pueden escribirse antes, pero T016–T017/T064 dependen de T003 integrado; usan el índice de Phase 2 para destinos frecuentes.
- **US2 (Phase 4)**: depende de T002, T003 y Phase 2; integra sobre US1 para cobrar el paso.
- **US3 (Phase 5)**: depende de US2; T031 cierra el núcleo propio. T040 depende además de T005 y T041 de T006, pero solo escriben pruebas.
- **US4 (Phase 6)**: oráculos pueden escribirse tras T001; mediciones de rutas/ciclo dependen de US1–US3. T072 puede escribirse tras T001 y T073–T075 dependen de T008, no de costo/rango ni de la salida sin inversa. T043 sigue a T042; T065 sigue a T046; T049/T050 integran también el mapa; T051 espera la referencia oficial. US3 no depende de US4.
- **Phase 7**: T052–T054 dependen de T002/T004; T055 de T006/T041; T056 de T005/T040 y de G4b; T057 de T046/T065 y T066 de T054.
- **Phase 8**: T058 puede ejecutarse al terminar código; T059–T063/T071 cierran pruebas y evidencia; T067–T070/T076 documentan únicamente resultados ya medidos.

### User Story Dependencies

- **US1 (P1)**: incremento funcional independiente con datos validados de Steven.
- **US2 (P1)**: depende de costo/rango e índice; no depende de 003, 004 ni persistencia nueva.
- **US3 (P1)**: depende de US2 para observar/deshacer decisiones; su núcleo usa retroceso actual.
- **US4 (P2)**: depende de los incrementos que mide, pero los generadores y oráculos pueden prepararse antes.

### Parallel Opportunities

- Tras T001, T002–T006 son coordinaciones independientes entre propietarios distintos.
- T007 y los tests de datos/oráculos que no consuman implementación pueden escribirse en paralelo en archivos distintos.
- En US1, T010–T015 son paralelas; T016–T017 son secuenciales porque modifican `logica/motor_juego.py`.
- En US2, T018–T023 son paralelas después de sus puertas; T024–T028 son secuenciales por dependencias y archivos compartidos.
- En US3, T030/T032–T036 son paralelas; T037–T039 son secuenciales y T040/T041 esperan entregas externas distintas.
- En US4, T042 precede a T043 porque comparten archivo; T048 y T072 sí pueden avanzar en paralelo en archivos distintos. T044–T047 comparten proveedor y se ejecutan secuencialmente; T073–T075 comparten el proveedor de mapa y T074/T075 esperan T073; T065 espera T046.

---

## Parallel Examples

### User Story 1

```text
T010: tests/test_datos/test_terreno_cazador_datos.py
T011: tests/test_logica/test_terreno_movimiento.py
T012: tests/test_logica/test_terreno_compatibilidad.py
T013: tests/test_logica/test_velocidad.py
T014: tests/test_contrato_api_real.py
T015: tests/test_integracion_sofia.py
```

### User Story 2

```text
T018: tests/test_datos/test_terreno_cazador_datos.py
T019: tests/test_logica/test_rutas_ponderadas.py
T020: tests/test_logica/test_cazador_ponderado.py
T021: tests/test_logica/test_cazador_integracion.py
T022: tests/test_logica/test_contrato_rutas_ponderadas.py
T023: tests/test_logica/test_comportamiento_enemigos.py
```

### User Story 3

```text
T030: tests/test_logica/test_cazador_vigencia.py
T032: tests/test_logica/test_cazador_determinismo.py
T033: tests/test_logica/test_terreno_cazador_retroceso.py
T034: tests/test_dto/test_sala_copia_serializacion.py
T035: tests/test_logica/test_terreno_cazador_copia.py
T036: tests/test_logica/test_rutas_sin_estado_retenido.py
```

### User Story 4

```text
T042 -> T043: tests/test_bench_terreno_cazador.py (secuenciales)
T048: benchmarks/benchmark_ciclo_real_integrante1.py
T072: tests/test_bench_mapa_cripta.py
```

---

## Implementation Strategy

### MVP First — US1

1. Completar la revisión posterior T001 y obtener/integrar T003.
2. Completar Phase 2 sin cambiar firmas, orden ni identidad del mapa; la política pendiente de salidas sin inversa no bloquea estas pruebas independientes.
3. Escribir T010–T015 antes de T016–T017.
4. Validar US1 de forma independiente con fuente offline en T064; pruebas escritas no equivalen a cierre.
5. No esperar T002/T004/T005/T006 para demostrar movimiento ponderado fresco.

### Incremental Delivery

1. **US1**: terreno ponderado para todos los movimientos.
2. **US2**: cazador correcto desde cero; esta es la capacidad principal completa.
3. **US3**: vigencia, determinismo, retroceso y copia con recálculo sin estado retenido.
4. **US4**: evidencia sintética conectada de mapa, rutas, ciclo y agenda; referencia oficial cuando se publique.
5. **Integraciones**: 003/004/guardado según cada contrato, sin bloquear incrementos independientes.

### Regla para reutilización

La ruta de producción recalcula cada paso. T046/T065 deciden por separado la estrategia del cazador en T057; T054 decide reutilización de «ir a» en T066. Las alternativas permanecen en benchmarks. Cumplir §3.4 y 5 ms mediante recálculo cierra «ir a» sin caché, generaciones ni invalidación productiva.

---

## Notes

- Cada tarea cita archivo(s), resultado verificable y FR/PR.
- Las 22 marcas `[P]` se limitan a archivos distintos y dependencias satisfechas; T042→T043 es expresamente secuencial.
- Las tareas de Steven/Joshua se verifican como dependencias; no autorizan a Sofía a modificar sus documentos o código sin coordinación.
- Las pruebas de `Sala` existentes se reutilizan; no se crea otra regresión para lo ya cubierto.
- La publicación de la referencia oficial bloquea T051, no el resto del desarrollo.
- Ejecutar `/speckit.analyze` después de generar este archivo y antes de `/speckit.implement` es obligatorio.
