---

description: "Tareas ejecutables para Terreno y cazador"
---

# Tasks: Terreno y cazador

**Input**: artefactos de `specs/001-terreno-y-cazador/` y constitución 1.0.0.

**Prerequisites**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/propuesta-steven-rutas-datos.md` y `contracts/propuesta-joshua-cambios-reversibles.md`.

**Estado**: implementación en curso: **75/76 tareas**. G1/G2, US1, US2, el núcleo de US3, la persistencia conjunta y el alcance sintético de US4 están cerrados; los cierres de T001–T050/T052–T076 constan con evidencia fechada. Queda una sola tarea sin marcar: T051. La referencia `cripta-06` ya está publicada y el mejor diagnóstico reproducible avanzó de cinco a nueve participantes, pero no demostró los 20 exigidos por AC-013/PR-001. La exploración se detuvo sin relajar el criterio (R-16/R-17, 18/11/2026).

**Organización**: las fases 3–6 corresponden a las cuatro historias de usuario. Las dependencias de Steven/Joshua y las tareas conjuntas se distinguen en el texto de cada tarea para no asignar a Sofía cambios ajenos. **Prioridad de avance acordada en la revisión de 2026-11-09 (B2)**: primero el índice de Phase 2 (T007–T009), después US1 y US2; US3 y US4 avanzan después según su bloqueo (G3, G4b/G5, G6), conservando todos los requisitos obligatorios y sin reordenar dependencias declaradas.

**Recuento actual**: 76 tareas (T001–T076), sin reutilizar IDs; 75 marcadas y 1 abierta; 22 oportunidades `[P]` reales. US1 y US2 están cerradas; el núcleo de US3, la persistencia conjunta, el cierre sintético de US4 y la integración de rendimiento de «ir a» están cerrados. AC-013/PR-001 continúa sin demostrar en T051: la presencia de 36 cazadores cargados no equivale a decenas participando en el ciclo.

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

- [x] T001 Sofía — después de aplicar las correcciones documentales del Prompt 39, reejecutar `/speckit.analyze` sobre `.specify/memory/constitution.md` y `specs/001-terreno-y-cazador/{spec.md,plan.md,tasks.md}` como revisión posterior independiente; resultado verificable: el nuevo informe no mezcla análisis de solo lectura con remediación ni autoriza implementación (FR-001–FR-018, PR-001–PR-006).

**Evidencia T001 (2026-11-10)**: `/speckit.analyze` se reejecutó en modo solo lectura sobre la constitución, `spec.md`, `plan.md` y `tasks.md`. El informe confirmó 30/30 AC, 18/18 FR y 6/6 PR trazados, los siete AC-B explícitos y ninguna violación constitucional crítica. Los huecos de pruebas corresponden a archivos planificados por tareas abiertas (T040, T041, T052), no a requisitos sin cobertura. Hallazgos de documentación: el recuento de `tasks.md` estaba desactualizado (33/43), `research.md` R-01 afirmaba que no había mediciones y el comentario de `plan.md` presentaba el proveedor de rutas como conectado a `--bench`. El recuento se corrigió en T059, R-01 en T057 y el comentario de `plan.md` con la revisión de resultados en T063. El informe no aplicó remediaciones ni autorizó implementación.
- [x] T002 Conjunta Sofía/Steven — acordar únicamente las firmas Python, protocolo y representación exacta de la operación de siguiente paso, conservando la semántica ya aceptada —paso único, origen=destino con costo 0 sin paso y ausencia de ruta distinguible— sin introducir `ATACAR`/`ESPERAR`; registrar nombres y tipos reales en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md` (FR-007–FR-014, PR-004, PR-006).
- [x] T003 Dependencia (Steven) — publicar su entrega de costo/rango estrictos, default 100 solo por ausencia, identificación de sentidos por origen/destino, detección de salidas múltiples ambiguas y costos simétricos cuando ambos sentidos existen; registrar hash y archivos concretos publicados en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`. La entrega acepta salidas sin inversa y conserva fuera de Sofía DTO/inicialización/guardado de Steven (FR-001, FR-002, FR-009, FR-011, FR-017, FR-018).
- [x] T004 Dependencia (Steven) — publicar la vista de mapa conocido solo de salas exploradas con las capacidades acordadas, recálculo por paso y prueba de independencia; registrar hash/rutas concretas en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md`. Bloquea solo integración 001/003, no el cazador (FR-013, FR-014, PR-004, PR-006).

**Evidencia T004 (2026-11-13)**: la integración `d86819d` contiene `1bc5c6220a4a12f471f4e118ffdf4bf7117f2467` y `7a36ebe18c7c30f0f4364a2fa6f119e60285396f`. `logica/mapa_conocido.py` publica `VistaMapaConocido` con `contiene_sala` limitado a salas exploradas y `salidas_transitables` limitado a puertas recordadas abiertas entre salas exploradas; no conserva referencia al mapa real. `logica/viaje.py` crea exclusivamente esa vista y recalcula al pedir cada paso. La independencia se comprobó con dos `EstadoPartida`/`MapaCripta` reales divergentes y el mismo conocimiento; después de prohibir toda consulta al mapa real ambos devolvieron el mismo paso. Pruebas focalizadas de mapa/viaje/rutas: **45 passed in 0.30s**; integración 001/003 y 001/004: **10 passed in 0.29s**.
- [x] T005 Dependencia integrada (Joshua), revisión conjunta — verificar cruzadamente en `Sofia@e89574de14df8a9e672ef0a62590630d37242f05` que `logica/cambios.py`, `logica/historial_reversible.py`, `tests/test_logica/test_cambios_linea.py` y `tests/test_logica/test_historial_linea.py` contienen y conservan `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, `fotografiar_para_rehacer(inverso, estado)` y `vincular_linea`; distinguir esta interfaz base ya disponible de la clase completa `LineaTiempo`, todavía no integrada localmente, y no copiar ni modificar código de Joshua (FR-014–FR-016, PR-004).
- [x] T006 Dependencia coordinada (Steven/Joshua) — publicar persistencia de costo/rango/mapa conocido y línea de tiempo con campos, compatibilidad, archivos y versión reales; registrar el hash verificado en `specs/001-terreno-y-cazador/contracts/propuesta-steven-rutas-datos.md` y `specs/001-terreno-y-cazador/contracts/propuesta-joshua-cambios-reversibles.md`. La propuesta histórica partía de v9; la entrega real verificada es v11 (FR-001, FR-009, FR-016, FR-018).

**Evidencia T006 (2026-11-15)**: Steven introdujo costo/rango en v10 con `5000d1fe8af268987206827e4c524c05bd599357`; Joshua publicó la serialización conjunta de estado y línea en `e002077bc4d6376e21308bcb4dd6a2c2a364e779`, integrada localmente por `d86819db3f1e5505105f4dc8f49d2c3202cf8925`; Steven añadió el conocimiento reversible en `719fc3492e35a94f81f48fe52773f2adb35e3f55` y entregó el formato conjunto v11 en `d1ad04867c94a2637024089c1625edb9cb296807`. `GuardadoBinario.VERSION` es 11: los registros de sala conservan `Puerta.costo` y `Enemigo.rango`, y los extras añaden longitud más bytes opacos de `LineaTiempo`; el `mapa_conocido` viaja dentro del estado vivo serializado por la línea. `JuegoService` importa ese paquete conservando sus referencias y `RestauradorPartida` valida/reconstruye el camino sin sección. El lector acepta exclusivamente v11; v9/v10 se rechazan como incompatibles sin reemplazar la partida vigente. Los contratos de Steven y Joshua registran hashes, archivos, representación y compatibilidad reales; la propuesta M3 de un único v10 queda identificada como antecedente, no como formato vigente.

**Evidencia T005 (2026-11-08)**: inspección local confirmó las cinco interfaces y que `logica/mutaciones.py` registra `CambioAtributo`, `CambioDato` y `CambioLista`, tipos cubiertos por la fotografía base; cualquier tipo nuevo de 001 debe implementar `fotografiar_para_rehacer` y falla antes de deshacer si no lo hace. `./.venv/Scripts/python.exe -m pytest -q tests/test_logica/test_cambios_linea.py tests/test_logica/test_historial_linea.py tests/test_logica/test_cambios.py tests/test_logica/test_historial_reversible.py tests/test_logica/test_cambio_soltar_objeto.py` terminó en `44 passed in 0.76s`. No existe `logica/linea_tiempo.py` en `HEAD`; G4b y T056 permanecen abiertos.

**Evidencia T002–T003 (2026-11-09)**: Steven aceptó `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta`; los campos observables, casos terminales e instrumentación están registrados en el contrato. `Sofia@5000d1f` integra costo/rango estrictos, simetría de sentidos existentes, aceptación de sentidos únicos y v10 para costo/rango. La validación `1204 passed, 4 subtests passed` fue comunicada por Sofía y no fue ejecutada en este bloque. G1/G2 quedan cerradas; T004, G4b y la persistencia conjunta completa siguen abiertas.

**Checkpoint histórico (2026-11-09)**: T002/T003/T005 estaban cerradas mientras T004, `LineaTiempo` y T006 seguían abiertas; no bloqueaban US1 ni el cazador sobre el esqueleto completo. T004/T006 y las integraciones posteriores ya se cerraron con evidencia propia.

---

## Phase 2: Foundational — índice de mapa compartido

**Purpose**: eliminar búsquedas lineales frecuentes sin alterar firmas, orden, identidad ni enlace de salas. Steven solicitó expresamente que Sofía implemente el índice de su `MapaCripta`; `plan.md` identifica los consumidores reales. La condición histórica de componente compartido exige compatibilidad, no una nueva reasignación. Bloquea US2–US4; US1 solo depende de este índice donde el motor busca destinos.

- [x] T007 [P] Sofía — ampliar `tests/test_logica/test_mapa_cripta.py` con pruebas de índice ID→instancia, `contiene_sala`, orden estable de `obtener_salas()`, sustitución en la misma posición y revinculación de referencias entrantes; resultado verificable: lista e índice siempre señalan a la misma `Sala` y los IDs no enteros se rechazan (FR-011, FR-013, FR-018, PR-001, PR-002).
- [x] T008 Sofía — implementar en `logica/mapa_cripta.py` un `TablaHashImpl` ID→sala conservando `_salas`, actualizarlo en altas/sustituciones y hacer O(1) esperado `obtener_sala`/`contiene_sala`; al sustituir, invalidar `_enlaces_listos` y revincular antes de exponer vecinos (FR-011, FR-013, FR-018, PR-001, PR-002).
- [x] T009 Sofía — ampliar `tests/test_restricciones_enunciado.py` para comprobar que el índice de `MapaCripta` es `TablaHashImpl` y que las rutas de producción nuevas siguen sin `dict`, `set`, `heapq`, `bisect`, `collections`, ordenamientos o bibliotecas de grafos prohibidos (FR-011, FR-018, PR-001–PR-004).

**Evidencia T007–T009 (2026-11-09)**: `MapaCripta` conserva `_salas` para el orden y añade `_salas_por_id: TablaHashImpl`; altas/sustituciones actualizan ambas representaciones, `obtener_sala`/`contiene_sala` validan IDs y consultan la tabla, y `vincular_salidas` resuelve por esa vía. Las pruebas cubren identidad, ausencias, orden, sustitución, revinculación y alias tras `deepcopy`/`pickle`. Resultado focalizado final de mapa/copia/restricciones: `67 passed, 2 subtests passed`; consumidores relevantes, copia/serialización y restricciones: `209 passed, 2 subtests passed`; suite completa final: `1109 passed, 2 subtests passed in 101.44s`. T072–T076 permanecen abiertas: no se ejecutaron benchmarks ni se documentó evidencia de rendimiento.

**Checkpoint**: el mapa conserva firmas y recorrido determinista, y ofrece acceso frecuente esperado O(1), sin duplicar `MonticuloMinimo` ni `TablaHashImpl`. Las salidas sin inversa están aceptadas y no alteran estos fixtures estructurales.

---

## Phase 3: User Story 1 — Transitar por terreno con costo (Priority: P1) 🎯 MVP

**Goal**: todo actor usa el costo validado de la salida solo al moverse; el resto de acciones y la reprogramación heredada permanecen iguales.

**Independent Test**: con dos salas y actores de distintas velocidades, comprobar costo ausente/presente/mínimo, intervalo, rechazo sin cambios y costos heredados sin activar cazadores.

**Dependencias**: G2/T003 se cerró en `5000d1f`; T006 cerró posteriormente la persistencia conjunta v11. Ninguna bloquea ya esta fase.

### Tests for User Story 1

- [x] T010 [P] [US1] Sofía — crear `tests/test_datos/test_terreno_cazador_datos.py` para verificar la entrega integrada de Steven: AC-001 usa 100 solo si `costo` falta, AC-019 rechaza valores presentes inválidos y AC-020 identifica por origen/destino costos contradictorios y multiplicidad ambigua; una salida sin inversa es válida (FR-001, FR-002, FR-017, FR-018).
- [x] T011 [P] [US1] Sofía — crear `tests/test_logica/test_terreno_movimiento.py` con AC-002 y AC-B06 para jugador, errante y rastreador: el movimiento cobra la salida atravesada y programa `max(1, costo_salida*100//velocidad)` (FR-003, FR-005, FR-018).
- [x] T012 [P] [US1] Sofía — crear `tests/test_logica/test_terreno_compatibilidad.py` con AC-003 y rechazos de movimiento: atacar/esperar/usar/equipar/recoger/soltar/abrir conservan costo, y un rechazo deja reloj, actor, puertas, agenda e historial idénticos (FR-004, FR-005, FR-017, FR-018).
- [x] T013 [P] [US1] Sofía — ampliar `tests/test_logica/test_velocidad.py` con AC-B07 para una salida costosa y ambos tipos de actor, verificando tiempo restante proporcional, identidad del evento, secuencia estrictamente nueva y reversión exacta (FR-003, FR-006, FR-016, FR-018).
- [x] T014 [P] [US1] Sofía — ampliar `tests/test_contrato_api_real.py` con una carga offline de al menos dos criptas que compruebe que los costos provienen de fixtures/servicio, no de constantes de una cripta, y que resolubilidad no cambia al variar solo pesos válidos (FR-001–FR-003, FR-018).
- [x] T015 [P] [US1] Sofía — ampliar `tests/test_integracion_sofia.py` para comparar dos ejecuciones del mismo movimiento ponderado y exigir el mismo `ResultadoAccion.costo`, reloj, evento y registro observable (FR-003, FR-015, FR-018).

**Evidencia preparatoria histórica T010–T015 (antes de `5000d1f`, 2026-11-09)**: en el checkout entonces revisado G2 continuaba abierta: `Puerta` y `DecodificadorDatos` no publicaban costo. Por ello T010, T011, T014 y T015 no se marcaron en esa ejecución. T012 verificó los siete costos heredados y rechazos atómicos; T013 verificó reprogramación y reversión. Foco de aquella ejecución: `26 passed, 2 subtests`; regresiones: `170 passed, 2 subtests in 1.17s`. El cierre actual se registra abajo.

### Implementation for User Story 1

- [x] T016 [US1] Sofía — modificar `logica/motor_juego.py` para que `_aplicar_accion(MOVER)` del jugador devuelva el costo de la `Puerta` atravesada y use el `calcular_intervalo` existente, sin cambiar `costo_base` de otras acciones; resultado verificable: T011/T012 pasan (FR-003, FR-004, FR-017, FR-018).
- [x] T017 [US1] Sofía — modificar `logica/motor_juego.py` para que `_turno_enemigo` conserve la puerta concreta seleccionada y programe movimientos errante/rastreador con su costo, manteniendo ataque/espera y demás conductas heredadas; resultado verificable: cada movimiento enemigo cobra exactamente una salida (FR-003–FR-005, FR-012, FR-018).
- [x] T064 [US1] Sofía — después de T003/T016/T017, ejecutar `tests/test_datos/test_terreno_cazador_datos.py`, `tests/test_logica/test_terreno_movimiento.py`, `tests/test_logica/test_terreno_compatibilidad.py`, `tests/test_logica/test_velocidad.py`, `tests/test_contrato_api_real.py` y `tests/test_integracion_sofia.py`, y registrar el resultado real en `specs/001-terreno-y-cazador/quickstart.md`; escribirlas antes no equivale a poder cerrarlas antes de la entrega local de Steven (FR-001–FR-006, FR-017, FR-018).

**Cierre US1 (2026-11-09)**: `MotorJuego` cobra `Puerta.costo` únicamente al mover jugador/errante/rastreador y conserva `costo_base` para las demás acciones. Las pruebas cubren default, validación, simetría condicional, sentido único, dos paquetes offline con pesos distintos, fórmula, rechazo atómico, reprogramación y repetición determinista. T064 terminó en **133 passed, 2 subtests passed in 4.71s**.

**Checkpoint**: US1 solo se considera cerrada cuando T064 pasa con la entrega de datos disponible localmente; guardado conjunto, buscador y 004 pueden seguir pendientes.

---

## Phase 4: User Story 2 — Persecución observable del cazador (Priority: P1)

**Goal**: el cazador ataca en la misma sala; en otro caso espera o mueve un único paso por la ruta abierta mínima dentro de rango con desempate estable.

**Independent Test**: usar grafos pequeños sintéticos y un oráculo exhaustivo independiente para comparar acción, costo total, primera vecina y costo del paso, sin contenido remoto ni niebla.

**Blocked by**: T002/T003/T007–T009 están cerradas. No depende de T004 ni de la vista de «ir a».

### Tests for User Story 2

- [x] T018 [P] [US2] Sofía — ampliar `tests/test_datos/test_terreno_cazador_datos.py` con AC-021: `rango` cumple literalmente “entero mayor o igual que 0”; ausencia, negativo, booleano, texto o fracción rechazan la ficha identificándola y sin default (FR-009, FR-017, FR-018).
- [x] T019 [P] [US2] Sofía — crear `tests/test_logica/test_rutas_ponderadas.py` con oráculo de rutas simples para AC-B01, AC-B02, AC-005, AC-B03, AC-B04 y AC-022, permutando el orden incidental de salidas y verificando mínimo `(costo_total, primera_vecina_id)` (FR-008–FR-011, FR-013, FR-015).
- [x] T020 [P] [US2] Sofía — crear `tests/test_logica/test_cazador_ponderado.py` con AC-004 y AC-023 para probar que compartir sala produce `ATACAR` antes del buscador incluso con rango 0 y salidas abiertas (FR-007, FR-009, FR-018).
- [x] T021 [P] [US2] Sofía — crear `tests/test_logica/test_cazador_integracion.py` con AC-006 y AC-007: mueve solo la primera salida, cobra esa salida y decide igual con contenidos remotos descargados distintos (FR-010, FR-012, FR-013, FR-018).
- [x] T022 [P] [US2] Sofía — crear `tests/test_logica/test_contrato_rutas_ponderadas.py` después de T002 para probar las firmas acordadas, IDs enteros estrictos, origen=destino, ausencia de ruta, límite inclusivo y ausencia de mutaciones/descargas (FR-008–FR-011, FR-013, FR-017).
- [x] T023 [P] [US2] Sofía — ampliar `tests/test_logica/test_comportamiento_enemigos.py` para asegurar que guardianes, errantes y rastreadores conservan decisiones anteriores mientras el nuevo comportamiento `cazador` permanece separado (FR-004, FR-005, FR-018).

**Evidencia preparatoria histórica T018–T023 (antes de G1/G2, 2026-11-09)**: T019 reutilizó el oráculo de T042 sin importar producción y cubrió costo, desempate, orden, cerradas, ciclos y rango. T023 protegió guardián/errante/rastreador, pero permaneció abierta porque aún no existía cazador productivo; T018/T020–T022 también quedaron bloqueadas entonces. Foco de aquella ejecución: `27 passed in 0.10s`; regresiones: `106 passed in 0.23s`. El cierre actual se registra abajo.

### Implementation for User Story 2

- [x] T024 [US2] Sofía — crear en `logica/rutas_ponderadas.py` las entradas inmutables y el resultado exacto acordado en T002, ordenados por `(distancia, primera_vecina_id, sala_id)` y sin exponer una ruta completa; resultado verificable: empates no dependen del descubrimiento (FR-010, FR-011, FR-015).
- [x] T025 [US2] Sofía — implementar en `logica/rutas_ponderadas.py` la búsqueda individual limitada por rango con `MonticuloMinimo` y `TablaHashImpl`, entradas duplicadas sin decrease-key, descarte de obsoletas y liberación de frontera; resultado verificable: no inserta distancia mayor al límite y coincide con T019 (FR-008–FR-011, FR-013, PR-002).
- [x] T026 [US2] Sofía — implementar en `logica/rutas_ponderadas.py` la vista del cazador sobre esqueleto completo, costos reales y puertas actualmente abiertas, sin consultar contenido descargado ni mapa conocido (FR-009–FR-014).
- [x] T027 [US2] Sofía — integrar `comportamiento == "cazador"` en `logica/comportamiento_enemigos.py`: atacar antes de buscar, esperar costo 100 sin ruta/dentro de límite falso y devolver solo `MOVER` con la primera vecina cuando corresponda (FR-007–FR-013, FR-018).
- [x] T028 [US2] Sofía — integrar en `logica/motor_juego.py` la ejecución del paso del cazador usando identidad de sala/enemigo, helpers reversibles existentes y costo de la puerta elegida; resultado verificable: no abre puertas y T020/T021 pasan (FR-007, FR-010, FR-012, FR-013, FR-016–FR-018).
- [x] T029 [US2] Sofía — ejecutar y corregir únicamente la integración propia en `tests/test_logica/test_rutas_ponderadas.py`, `tests/test_logica/test_cazador_ponderado.py` y `tests/test_logica/test_cazador_integracion.py` hasta que US2 pase de forma independiente, sin presentar T004/T006 como resueltas (FR-007–FR-018, PR-006).

**Cierre US2 (2026-11-09)**: `proximo_paso` usa entradas inmutables, `MonticuloMinimo`/`TablaHashImpl`, duplicados y descarte de obsoletas; valida IDs/límite, limita inserciones, limpia frontera y no retiene estado. La vista del cazador solo lee esqueleto/puertas/costos y contabiliza también puertas cerradas inspeccionadas sin transitarlas. Ataque, movimiento único y espera son excluyentes; el movimiento usa helpers reversibles. Foco T029 ampliado: **30 passed in 0.15s**; regresiones relacionadas: **505 passed, 4 subtests passed in 7.20s**.

**Checkpoint**: US2 ofrece persecución correcta desde cero; no requiere reutilización, vista de «ir a», persistencia nueva ni interfaces históricas futuras.

---

## Phase 5: User Story 3 — Decisiones vigentes, deterministas y reversibles (Priority: P1)

**Goal**: toda decisión equivale al cálculo desde cero sobre estado vigente y los cambios de terreno/cazador se deshacen sin romper alias ni determinismo.

**Independent Test**: alterar puertas, jugador, velocidad y otros actores entre turnos; comparar con cálculo desde cero; retroceder un intervalo y repetir la continuación.

**Dependencias**: US2, T005 y T006 están cerradas. T006 aporta el paquete conjunto v11; con recálculo sin estado retenido no hay invalidación productiva que implementar.

### Tests for User Story 3

- [x] T030 [P] [US3] Sofía — crear `tests/test_logica/test_cazador_vigencia.py` con AC-B05, AC-008, AC-016, AC-017 y AC-018, comparando cada decisión posterior con una invocación independiente desde cero y sin exigir invalidaciones idénticas para cambios irrelevantes (FR-006, FR-013, FR-014, PR-006).
- [x] T031 [US3] Sofía — después de T030/T032–T039, ejecutar `tests/test_logica/test_cazador_vigencia.py`, `tests/test_logica/test_cazador_determinismo.py`, `tests/test_logica/test_terreno_cazador_retroceso.py`, `tests/test_logica/test_terreno_cazador_copia.py` y `tests/test_logica/test_rutas_sin_estado_retenido.py` hasta que pasen con recálculo desde cero, registrando el resultado en `specs/001-terreno-y-cazador/quickstart.md`; AC-009 experimental se cubre después en T065 sin dependencia circular con US4 (FR-006, FR-013–FR-018, PR-006).
- [x] T032 [P] [US3] Sofía — crear `tests/test_logica/test_cazador_determinismo.py` con AC-010: dos estados con misma cripta/versiones/semilla/acciones y orden incidental permutado producen decisiones, tiempos, secuencias y `partida.log` idénticos (FR-011, FR-015, FR-018).
- [x] T033 [P] [US3] Sofía — crear `tests/test_logica/test_terreno_cazador_retroceso.py` con AC-011: mover/esperar/atacar/cerrar/reprogramar dentro del intervalo, usar pergamino, restaurar sala/vida/reloj/agenda/puertas salvo la excepción de pergaminos y repetir continuación determinista (FR-006, FR-014–FR-016, FR-018).
- [x] T034 [P] [US3] Sofía — ampliar `tests/test_dto/test_sala_copia_serializacion.py` solo para los campos canónicos nuevos `Puerta.costo`, rango materializado y coherencia lista/índice de `MapaCripta` tras `deepcopy`/`pickle`, reutilizando las comprobaciones existentes de cantidad/orden/IDs, índices de enemigos y alias sin duplicar su lógica (FR-001, FR-009, FR-011, FR-016, FR-018).
- [x] T035 [P] [US3] Sofía — crear `tests/test_logica/test_terreno_cazador_copia.py` para `copy.deepcopy((estado, transacciones))`: cada cambio nuevo apunta a la entidad copiada, no al estado vivo, y ningún objeto copiado alcanza motor, servicio o caché (FR-014–FR-016, FR-018).
- [x] T036 [P] [US3] Sofía — crear `tests/test_logica/test_rutas_sin_estado_retenido.py` para verificar que cada consulta productiva libera montículo/tablas, que estado/transacciones no alcanzan auxiliares y que decisiones tras `RETROCEDER`, `iniciar` o `historia` se recalculan sin depender de ganchos de caché (FR-014–FR-016, PR-003, PR-006).

### Implementation for User Story 3

- [x] T037 [US3] Sofía — asegurar en `logica/rutas_ponderadas.py` que la vía productiva de recálculo crea y libera auxiliares dentro de cada consulta y no expone instantáneas, generaciones ni cachés; las alternativas compartida/reutilizada viven solo en `benchmarks/terreno_cazador_integrante1.py` (FR-013–FR-016, PR-003, PR-006).
- [x] T038 [US3] Sofía — auditar `logica/motor_juego.py` para que `RETROCEDER`, `iniciar` e `historia` no incorporen ganchos de invalidación innecesarios mientras no exista estado de ruta retenido; resultado verificable: la siguiente decisión usa una consulta nueva y no hay observadores de atributos (FR-014–FR-016).
- [x] T039 [US3] Sofía — auditar y ajustar en `logica/motor_juego.py` todas las mutaciones nuevas de cazador mediante `atributo`, `agregar`, `quitar_identidad`, `registrar` y registro de agenda dentro de la transacción abierta; resultado verificable: abortar/deshacer no deja cambios parciales (FR-016–FR-018).

**Cierre del núcleo US3 (2026-11-09)**: T030 usa un oráculo por enumeración de rutas simples construido de nuevo para cada decisión y cubre apertura/cierre, cierre automático real, movimiento real del jugador, velocidad con reprogramación y movimiento/muerte de otro actor. T032 compara dos partidas con la misma semilla y acciones, empate exacto `(5, 2)`, orden de salas/salidas permutado y bytes idénticos de `partida.log`. T033 ejecuta en un intervalo real espera, dos movimientos, ataque, vencimiento de velocidad con reprogramación y cierre automático; `RETROCEDER` mediante pergamino restaura salas, actores, vida, reloj, agenda, secuencias, puertas y azar, excepto el pergamino y un cambio `registrar_solo_linea`, y la continuación se repite. También se induce un fallo después del movimiento para comprobar aborto sin mutación parcial. T034–T035 verifican costo/rango, índices y alias tras `deepcopy`/`pickle` conjuntos, sin motor, servicio, caché ni resultados de ruta alcanzables. T036–T038 prueban liberación por referencia débil de un montículo y dos tablas por consulta, recálculo tras retroceso, reinicio y enlace de estado deserializado, sin ganchos. La auditoría T039 no encontró asignaciones nuevas fuera de helpers; no fue necesario cambiar producción. Foco T031: **13 passed in 1.48s**; regresiones relacionadas: **493 passed, 4 subtests passed in 3.52s**; restricciones: **56 passed in 0.51s**; contrato offline: **41 passed in 5.06s**. `py_compile` y `git diff --check` pasaron. La clase completa `LineaTiempo` sigue ausente: T040/T056 permanecen abiertas; T041/T055 continúan bloqueadas por T006/G5.
- [x] T040 [US3] Conjunta Sofía/Joshua — después de T005, **escribir** en `tests/test_integracion_001_004.py` pruebas de `deshacer_mientras`, inversos en `finally`, `fotografiar_para_rehacer` para cada cambio nuevo e `historia` sin ejecutar rutas; conforme a la evidencia de 2026-11-09 (A2), las pruebas se redactan contra el protocolo publicado por Joshua en `origin/joshua@f4da930dbdbf951609894a1501bfca2c4ea9264a`: la firma `deshacer_mientras(estado, condicion, inversos: list)` no cambia, pero la condición se invoca como `condicion(estado, cambio)` e incluye la restauración de eventos posteriores al instante consultado (`_hasta` en `logica/linea_tiempo.py`); su ejecución satisfactoria se cierra únicamente en T056 (FR-014–FR-016, PR-004, PR-006).

**Evidencia T040 (2026-11-10)**: se redactó `tests/test_integracion_001_004.py` con seis pruebas propias, sin copiar código de Joshua: condición `(estado, cambio)`, inversos rehacidos en `finally`, `_hasta`, `historia` sin invocar `proximo_paso`, avisos `vincular_linea`/`recortar` y fotografía de los cambios de terreno/cazador (`CambioVida`, `CambioReloj`, `CambioPuerta`, `CambioDato`, `CambioLista` y `CambioAgenda`). En la rama `Sofia` el módulo se omite con `pytest.importorskip` porque `LineaTiempo` no está integrada (G4b). Contra una copia temporal de solo lectura de `origin/joshua@b769f35` —que contiene el protocolo publicado— las seis pruebas pasaron: **6 passed in 0.08s**. T040 se cierra como redacción; la ejecución satisfactoria y su cierre formal siguen en T056.
- [x] T041 [US3] Conjunta Sofía/Steven/Joshua — después de definir T006, revisar y conservar `tests/test_datos/test_guardado_terreno_cazador.py` para la ida/vuelta del formato conjunto real v11 con costo, rango, mapa conocido y línea de tiempo; distinguir la propuesta histórica M3 de un único v10 de la implementación entregada y reservar la ejecución satisfactoria para T055 (FR-001, FR-009, FR-014–FR-016, FR-018).

**Evidencia T041 (2026-11-15)**: el archivo existente, introducido por Steven en `e4a34e8eb6120d06a6d4b552b9652558860d4c9f` y ampliado en `76ba6b7029b87bcddc7667f066b368e4ca9dd3ed`, ya cubre sin duplicación: ida/vuelta conjunta de costo, rango, exploradas/avistadas y K de la línea; costo no sustituido por el default; rechazo explícito de v9/v10; alias cortos normalizados a sentidos canónicos; ausencia de `ResultadoRuta`, `SalidasTransitables`, `VistaMapaConocido` y `Viaje` en el archivo; y reconstrucción propia de costo/rango por `RestauradorPartida` cuando la sección de línea es vacía. La identidad canónica queda cubierta por las regresiones existentes de restauración y línea: destinos enlazados a las salas canónicas, actores a su sala, eventos a la misma puerta/trampa/efecto, botín compartido por identidad y `linea._estado is estado`. No se añadió otra prueba porque no quedó un requisito sin cobertura demostrable.

**Checkpoint**: T031 cerró el núcleo de US3 con recálculo; T040/T041 escribieron o revisaron las integraciones y T055/T056 las ejecutaron contra las entregas locales.

---

## Phase 6: User Story 4 — Evidencia de escala y carga nueva (Priority: P2)

**Goal**: `--bench` demuestra corrección y costo completo de rutas/ciclo/agenda con sintéticos, y separa la validación oficial todavía bloqueada.

**Independent Test**: ejecutar `main.py --bench` offline y comprobar filas, alternativas, equivalencia previa, semillas, calentamiento, repeticiones, carga, unidad, trabajo y percentiles requeridos.

**Blocked by**: US1–US3 para medir rutas y ciclo de producción; el benchmark independiente del mapa requiere T008, no costo/rango ni la política ya confirmada de aceptar salidas sin inversa. La carga de decenas aún no validada en la referencia publicada mantiene abierta solo T051.

### Tests for User Story 4

- [x] T042 [US4] Sofía — crear `tests/test_bench_terreno_cazador.py` con un oráculo exhaustivo para grafos pequeños y relajación completa independiente para matrices mayores, fallando antes de cronometrar ante divergencias de acción, alcance/rango, costo total, primera vecina o costo del paso (PR-002–PR-004, PR-006).
- [x] T043 [US4] Sofía — después de T042, ampliar el mismo `tests/test_bench_terreno_cazador.py` para exigir filas de AC-012, AC-014 y AC-015 y el **esquema/salida de AC-013** —identificador de ciclo real, origen sintético/oficial, carga, unidad y muestras— sin exigir aún resultados oficiales; incluir seis operaciones de agenda y costo completo (PR-001–PR-006).

**Evidencia T042 (2026-11-09)**: `tests/test_bench_terreno_cazador.py` define únicamente auxiliares locales de prueba, sin DTO ni firma productiva: enumeración exhaustiva de rutas simples para grafos pequeños y relajación completa de hasta `|V|-1` pases para una carga mayor. El esquema observable aislado distingue estado, acción de ruta, alcanzabilidad, rango, costo total, primera vecina y costo del primer paso; `TrabajoOraculo` mantiene rutas/expansiones/salidas/relajaciones/pases aparte y la equivalencia no exige contadores ni orden interno iguales. Se verificaron origen=destino, inaccesible, límite exacto, fuera de rango, ciclos, conexión cerrada, empate por ID numérico y todas las permutaciones de cuatro conexiones; cualquier divergencia observable falla antes del cronómetro. Ejecución focalizada: `17 passed in 0.05s`. G1 sigue abierta y T043 no se inició: no se declararon firma de producción, filas, percentiles, ciclo real, agenda ni integración.

### Implementation for User Story 4

- [x] T044 [US4] Sofía — crear `benchmarks/terreno_cazador_integrante1.py` con generadores sintéticos deterministas, oráculos independientes e instrumentación de fijadas `F`, descubiertas `D`, salidas `E`, inserciones `P`, frontera `Q`, obsoletas, limpieza y memoria (PR-002–PR-004, PR-006).
- [x] T045 [US4] Sofía — implementar en `benchmarks/terreno_cazador_integrante1.py` AC-012 comparando la misma región dentro de rango mientras crece solo el exterior; resultado verificable: el informe separa trabajo regional de `V/E` total y no afirma complejidad solo por tiempo (PR-002, PR-004, PR-006).
- [x] T046 [US4] Sofía — implementar **solo en** `benchmarks/terreno_cazador_integrante1.py` AC-014 con individual/compartida, uno/decenas, rango pequeño/grande, recálculo/reutilización y puertas estables/inestables, incluyendo construcción, consulta, invalidación y limpieza; ninguna clase experimental pasa a producción (PR-003, PR-004, PR-006).

**Evidencia T044–T046 (2026-11-09)**: `benchmarks/terreno_cazador_integrante1.py` publica `PROVEEDORES_RUTAS` con AC-012 y AC-014. La alternativa individual invoca `proximo_paso` productivo; las alternativas inversa compartida y reutilizada, incluida su generación explícita, existen solo en el benchmark. La inversa transforma cada salida dirigida `u → v` en una entrada de recorrido `v → u` y las pruebas confirman que no inventa sentidos ausentes. Antes de cada reloj, una relajación completa independiente compara `alcanzable`, costo total, primera vecina y costo del primer paso sin igualar contadores. AC-012 conserva una región alcanzable de cinco salas para 32/128/512 salas totales: producción mantuvo `F=5`, `D=5`, `E=6`, `P=5`, `Q=2`, mientras la construcción inversa reporta por separado el barrido del grafo total. AC-014 genera 24 combinaciones de alternativa, 1/20 cazadores, rango pequeño/grande y puertas estables/cambios frecuentes durante tres ciclos; separa mantenimiento, construcción inicial, reconstrucción, consultas recalculadas/iniciales/reutilizadas, invalidación, limpieza y total del lote. Cada fila conserva nueve muestras, mediana, p95 de rango más cercano, máximo/mínimo, entorno, semilla, carga, trabajo y memoria `tracemalloc` de otra corrida. `benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json` contiene **30 filas/270 muestras** y se etiqueta como sintético, no como PR-001. Pruebas de benchmark/conexión: **55 passed in 6.89s**; rutas relacionadas: **21 passed in 0.21s**; restricciones: **56 passed in 1.31s**; `py_compile` pasó. T049 permanece abierta: rutas se validaron mediante `benchmarks.integrante3.ejecutar(proveedores=PROVEEDORES_RUTAS)` sin editar el punto compartido.

**Evidencia T043 (2026-11-10)**: `tests/test_bench_terreno_cazador.py` exige ahora las filas AC-015 de `medir_agenda_ciclo` y el esquema AC-013 de `medir_ciclos_sinteticos`: identificador, alternativa, carga, unidad, muestras, clasificación separada, origen sintético, referencia oficial pendiente y memoria aparte. Conserva las pruebas AC-012/AC-014 previas. La ejecución focalizada conjunta terminó en **52 passed in 4.45s** e incluye una cripta real con catálogo vivo reconectado fuera del intervalo; los seis módulos de benchmark terminaron en **70 passed in 7.58s**.
- [x] T047 [US4] Sofía — implementar en `benchmarks/terreno_cazador_integrante1.py` AC-015 para insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates con cientos de eventos, comparando `AgendaEventos` con una **lista lineal manual local al benchmark** que busca/retira por recorrido; no modificar ni reimplementar la agenda productiva (PR-004, PR-005, PR-006).

**Evidencia T047 (2026-11-10)**: `medir_agenda_ciclo` repite las seis operaciones con 256/512/1024 eventos, tipos `EFECTO`, `CERRAR_PUERTA`, `ENEMIGO`, `JUGADOR_DISPONIBLE` y `VENCER_EFECTO`, 28 destinatarios cazador, puertas y demoras derivadas de costos variables. La equivalencia observable frente a `_AgendaLinealBenchmark` se valida antes de cada reloj. `benchmarks/resultados/agenda_ciclo001_t047_c1_r9_256-512-1024.json` conserva **36 filas/324 muestras**; en 1024 eventos las medianas agenda/lineal (ns por lote) fueron: insertar 4 955 600/20 079 700; extraer 4 648 900/17 355 000; cancelar ID 4 609 200/3 968 700; cancelar actor 776 000/466 700; reprogramar 10 086 000/24 937 600; empates 15 341 200/39 693 900. Las 24 muestras lineales `>=20 ms` pertenecen a insertar 256 eventos (6/9), reprogramar 256 (9/9) y resolver 1024 empates (9/9); se conservan sin reducir carga. El registro por `main.py --bench` sigue pendiente exclusivamente en T049.
- [x] T048 [P] [US4] Sofía — adaptar `benchmarks/benchmark_ciclo_real_integrante1.py` para ciclos con decenas de cazadores y costos variables, manteniendo carga/copia fuera y acción, agenda y rutas dentro; incluir invalidación/limpieza únicamente en la variante experimental que retenga estado y etiquetar sintético frente a referencia oficial (PR-001, PR-003, PR-004, PR-006).

**Evidencia T048 (2026-11-10)**: `medir_ciclos_sinteticos` ejecuta `MotorJuego.ejecutar_accion()` completo hasta la siguiente decisión sobre 32/64 salas, 1/28 cazadores reales, rango 300 o `10000+100·n`, costos dirigidos 100..130 y puertas estables/inestables. Compara recálculo productivo con una inversa retenida exclusiva del benchmark; construcción, consultas, invalidación, reconstrucción y limpieza quedan dentro del intervalo y PR-006 compara notificaciones, reloj, agenda, salas, enemigos, puertas y azar antes de medir. `benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json` conserva **32 filas/288 muestras**: 288 ciclos completos, 0 rechazados/muertes/victorias/terminales/incompletos/errores y las **9 muestras `>=20 ms`**. En 64 salas, 28 cazadores y rango grande, producción obtuvo con puerta estable mediana **20.5445 ms**, p95 **36.8259 ms** y 7/9 muestras `>=20 ms` (28 decisiones/notificaciones enemigas); con puerta inestable obtuvo 17.9640 ms, 33.2342 ms y 2/9 (24 decisiones/notificaciones y un cierre). Se conservaron sin reducir carga. La variante retenida estable obtuvo 3.1269 ms, dato experimental que no decide producción. `benchmarks/resultados/ciclo_real_criptas_disponibles.json` separa cuatro criptas reales locales (12/12 ciclos completos, medianas 0.102..0.225 ms) y declara `afirma_pr001=false`; no son la referencia oficial. T051/PR-001 permanecen abiertos por G6 y T049 por el registro compartido en `main.py`.
- [x] T049 [US4] Conjunta Sofía/propietario de `main.py` — después de T044–T048/T073–T075, acordar y ejecutar la integración mínima en `main.py` para registrar una sola vez los proveedores de rutas de 001, `benchmarks/mapa_cripta_integrante1.py` y el adaptador del ciclo real, preservando proveedores existentes; la tarea no autoriza a Sofía a editar unilateralmente este punto compartido (PR-001–PR-006).

**Evidencia T049 (2026-11-14)**: el acuerdo de propiedad del punto compartido consta en `4ea99fa1c62dd79faf841ea143bb7ff9b55cde94`, donde Steven registró el proveedor de mapa de 001 en `main.py --bench`, retiró la omisión asociada y dejó el conteo derivado para extensiones coordinadas. Con la autorización actual, el mismo bloque concatena ahora `PROVEEDORES_MAIN` de terreno/cazador y ciclo después de los 20 proveedores existentes, incluido `bench_linea.PROVEEDORES` de Joshua: **25 identidades únicas**, y cada uno de los cinco adaptadores aparece exactamente una vez. `tests/test_bloque3_conexiones.py` captura y compara la secuencia completa sin ejecutar las cargas; junto con `tests/test_bench_adaptadores_001.py` y la prueba focalizada de línea de tiempo terminó en **10 passed in 0.64s**. La validación previa de adaptadores/regresiones permanece en **60 passed in 19.98s**. T050 continúa abierta: falta la ejecución oficial y su artefacto.
- [x] T050 [US4] Sofía — después de T049/T073–T075, ejecutar los benchmarks sintéticos mediante `main.py --bench` y guardar evidencia reproducible en `benchmarks/resultados_terreno_cazador_integrante1.json` con filas separadas de mapa/rutas/agenda/ciclo, entorno, semilla, calentamiento, repeticiones, mediana, p95/máximo, carga, unidad, trabajo y alternativa, sin presentarla como referencia oficial (PR-002–PR-006).

**Preparación T050 (2026-11-14; tarea abierta)**: `benchmarks/extraer_resultados_terreno_cazador_integrante1.py` filtra desde el JSON completo únicamente los nombres y alternativas exactos de los tres módulos de 001, conserva filas/metadatos/muestras sin transformarlos y rechaza cobertura ausente, alternativas ausentes/ajenas, pérdida de muestras y claves lógicas duplicadas. `contracts/ejecucion-t050-powershell.md` separa stdout, stderr, PID, código de salida y evidencia filtrada. `tests/fixtures/benchmarks/main_bench_t050_minimo.json` representa el esquema real sin ejecutar cargas. Pruebas del extractor, adaptadores y registro: **17 passed in 0.34s**. No se ejecutó `main.py --bench`; T050 no se cierra hasta obtener y validar la corrida completa.

**Incidencia previa T050 (2026-11-14; resuelta por el cierre posterior)**: dos corridas completas generaron JSON válido con **916 filas**; la validación en memoria encontró las **194 filas esperadas de 001** (mapa 60, agenda 72, rutas 30, ciclo 32) y no detectó errores del extractor. Sin embargo, `Start-Process.ExitCode` fue `$null` en ambas: la primera quedó preservada con sufijo `sin_codigo_20261114T201819` y la segunda registró `CAPTURE_FAILED` (envoltorio 254). stderr quedó separado y contiene cinco avisos por ausencia del paquete offline de `cripta-01`. En ese punto no se generó el JSON filtrado oficial y T050 permaneció abierta.

**Continuación previa T050 (2026-11-14; resuelta por el cierre posterior)**: la invocación directa añadió indebidamente `$ErrorActionPreference = "Stop"`. Windows PowerShell 5.1 convirtió el primer aviso legítimo de stderr en `NativeCommandError`, interrumpió Python y no llegó a asignar ni escribir `$LASTEXITCODE`; stdout/stderr quedaron en 0 bytes y se preservaron con sufijo `interrumpido_nativecommanderror_20261114T203733`. No se inició otra corrida con ese mecanismo; las dos corridas completas anteriores permanecieron intactas.

**Evidencia T050 (2026-11-14; cierre)**: `benchmarks/ejecutar_t050_integrante1.py`, probado primero con procesos hijos de códigos 0 y 7 y rechazo de sobrescritura (**3 passed in 0.22s**), ejecutó los 25 proveedores sin cambiar parámetros y registró el `returncode` real de `main.py`: **0**. `benchmarks/resultados/main_bench_completo_t050.json` conserva **916 filas**, entorno Windows/Python 3.12.10, tamaños globales 8/16/32/64/128/512 y 15 repeticiones; stderr está separado y conserva cinco avisos por falta del paquete offline de `cripta-01`. El extractor oficial generó `benchmarks/resultados_terreno_cazador_integrante1.json` con **194 filas/2910 muestras**: mapa 60/900, agenda 72/1080, rutas 30/450 y ciclo 32/480. Las 194 claves lógicas son únicas, el filtrado coincide exactamente con el subconjunto original y conserva entorno/metadatos superiores. Rangos mediana/p95/máximo (ms): mapa 0.0013–13.6665/0.0017–27.0195/0.0017–27.0195; agenda 0.0474–39.4820/0.0550–71.1175/0.0550–71.1175; rutas 0.0307–27.7025/0.0393–51.9595/0.0393–51.9595; ciclo 0.1212–20.3797/0.1832–33.2902/0.1832–33.2902. El ciclo conserva 10 muestras de producción `>=20 ms`, `origen_carga=sintetico`, `referencia_oficial=pendiente_publicacion_g6` y `afirma_pr001=false`; no se presenta como cierre de PR-001. Pruebas focalizadas finales de ejecutor, extractor, adaptadores y registro: **20 passed in 0.43s**.

**Aclaración de vigencia T050 (2026-11-16)**: la ejecución y los JSON permanecen como evidencia histórica inalterada. Dentro de las 916 filas, seis `mapa_conocido_explorar_una_sala` midieron cero revelaciones, y seis `mapa_conocido_estado_sala` más sus seis alternativas `mapa_conocido_estado_recorriendo_alternativa` usaron lotes variables de `n` consultas; esas **18 filas/270 repeticiones** no son evidencia vigente de SC-002/SC-003. La corrección posterior pertenece a Steven (`1734a70`, `d59752d`) y está documentada en su respuesta. Las 194 filas/2910 muestras filtradas de 001 no contienen ninguna de esas series y conservan su alcance. T050 sigue cerrada como ejecución reproducible; T051 permanece abierta por PR-001.
- [ ] T051 [US4] Sofía — sobre la referencia publicada `cripta-06`, validar un recorrido real con decenas de cazadores activos y participantes, ejecutar AC-013 y registrar en `benchmarks/resultados_terreno_cazador_referencia.json` cada ciclo `<20 ms` solo si cumple todas las condiciones; conservar abierta sin bloquear T042–T050 mientras falte demostrar la carga (PR-001, PR-004, PR-006).

**Diagnóstico T051 (2026-11-17; no cierre)**: versión `f9ed9afa683d`, catálogo `4b9e75a42be5`, 300 salas, 75 enemigos, 36 cazadores (25 sabuesos/11 espectros), 0 activos iniciales. El recorrido de acciones válidas conservado en `benchmarks/recorridos/t051_cripta06.json` alcanza 1/3/5 participantes; ejecutan 1/3/6 decisiones por ciclo. Su continuación registra 86 acciones completas y una muerte, sin rechazos/errores. `benchmarks/resultados/t051_cripta06_actividad_real.json` conserva 30 muestras completas, 3 calentamientos, 100 decisiones de cazadores, 130 eventos, mediana/p95/máximo **0.2940/1.0614/1.3282 ms**, cero muestras `>=20 ms` e I/O nulo medido. No acredita decenas ni demuestra imposibilidad de otro recorrido; `afirma_pr001=false` y no se crea el JSON reservado a la validación oficial. Pruebas de benchmark/conexión/restricciones: **125 passed in 3.82s**. T048/T050 y el diagnóstico anterior quedan intactos; R-16 documenta reglas, distribución, metodología y límite vigente.

**Carga preparada de §6.1 (2026-11-18; tarea abierta)**: `benchmarks/carga_cazadores_cripta06.py` activa los 36 cazadores de `cripta-06` con vida alta del jugador. La búsqueda compartida baja los ciclos de 20 ms o más de 299/300 a 6/300 (jugador espera) y de 271/300 a 16/300 (jugador se mueve). No sustituye el recorrido legal ni cumple «cada ciclo <20 ms»: T051 sigue sin marcar y no se genera `benchmarks/resultados_terreno_cazador_referencia.json`.

**Cierre documental de la investigación T051 (2026-11-18; tarea abierta)**: los Prompts 79–83 elevaron el máximo histórico reproducible de cinco a nueve cazadores vivos, activos y participantes. `benchmarks/recorridos/diagnosticos/t051_prompt82_ocho_cazadores_parcial.json` conserva los checkpoints 58/95/135/167/250; `benchmarks/recorridos/diagnosticos/t051_prompt83_nueve_cazadores_parcial.json` reproduce 299 acciones legales desde el inicio y un ciclo completo con nueve IDs distintos, I/O nulo y **1,292416 ms preliminares**. Termina con 9 HP y cinco pociones; dos perseguidores quedan en la sala del jugador y otro en la adyacente, por lo que curarse o regresar a C2 concede ataques concurrentes y no se justificó ampliar la búsqueda. Ambos JSON declaran `parcial=true` y `afirma_t051=false`. Se detiene la exploración para priorizar estabilidad: no se demostraron los 20 participantes de AC-013/PR-001, no se genera `benchmarks/resultados_terreno_cazador_referencia.json` y T051 permanece sin marcar en **75/76**.
- [x] T065 [US4] Sofía — después de T046, ejecutar AC-009 en `tests/test_bench_terreno_cazador.py` comparando recálculo y reutilización **benchmark-local** en acción, primera vecina y costo para puertas estables/inestables; resultado verificable: no hay dependencia de US3 hacia una alternativa creada en US4 (FR-013, FR-014, PR-003, PR-006).
- [x] T072 [P] [US4] Sofía — crear `tests/test_bench_mapa_cripta.py` para exigir que `main.py --bench` incluya filas separadas de construcción del índice, búsqueda por ID y vinculación de salidas, con varios tamaños y cargas equivalentes; antes de aceptar tiempos, comprobar mismos IDs/orden, mismos resultados de aciertos y ausencias, y que cada `Puerta.destino_sala` sea la instancia canónica correspondiente (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [x] T073 [US4] Sofía — después de T008, crear `benchmarks/mapa_cripta_integrante1.py` con generadores deterministas de varios tamaños/densidades y una fila exclusiva para construir `_salas` más el índice propio, separando generación del fixture, construcción medida y memoria; la alternativa lineal permanece local al benchmark y recibe exactamente las mismas instancias en el mismo orden (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [x] T074 [US4] Sofía — después de T073, añadir en `benchmarks/mapa_cripta_integrante1.py` búsqueda por ID del índice frente a recorrido lineal benchmark-local, con secuencias equivalentes de aciertos al inicio/medio/final y ausencias para varios tamaños; validar identidad/ausencia y la secuencia completa de resultados antes de cronometrar únicamente las consultas (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).
- [x] T075 [US4] Sofía — después de T073, añadir en `benchmarks/mapa_cripta_integrante1.py` vinculación de salidas antes/lineal frente a después/indexada sobre grafos equivalentes de varios `V/E`, cronometrando la vinculación aparte de construcción y consultas; antes de comparar tiempos, verificar orden de salas/puertas, destinos, alias e identidad canónica de todas las referencias (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).

**Evidencia T072–T075 (2026-11-09)**: `benchmarks/mapa_cripta_integrante1.py` publica `PROVEEDORES` con construcción, consultas y vinculación separadas; usa semilla 1729, densidades 1/4, genera fixtures fuera del reloj, descarta un calentamiento e informa carga, entorno, repeticiones, unidad, mediana, p95, máximo, mínimo, muestras, trabajo y memoria de contenedores. Las alternativas lineales son privadas del benchmark y la equivalencia de IDs, orden, aciertos/ausencias, puertas, destinos y alias canónicos se valida antes del cronómetro. Ejecución conectada por `benchmarks.integrante3.ejecutar`: 32/128/512 salas, 9 repeticiones, 30 filas. Pruebas relevantes: `84 passed, 1 skipped, 2 subtests`; suite completa final: `1113 passed, 1 skipped, 2 subtests in 99.41s`. T073–T075 quedan cerradas. T072 sigue abierta: su prueba de esquema/equivalencia y la conexión por interfaz estándar pasan, pero la prueba de inclusión real en `main.py --bench` se omite explícitamente hasta la integración conjunta T049. T076 permanece abierta y no se afirma cumplimiento del ciclo de 20 ms.

**Evidencia T072 (2026-11-14; cierre)**: la prueba de integración atraviesa `main.main()` con configuración `--bench`, intercepta únicamente `benchmarks.integrante3.ejecutar` y confirma que la composición real contiene 25 proveedores únicos y exactamente una instancia del proveedor de mapa, sin ejecutar las 916 mediciones. Otra prueba de solo lectura valida `benchmarks/resultados/main_bench_completo_t050.json`: **60 filas/900 muestras**, tamaños 8/16/32/64/128/512, densidades 1/4, seis alternativas esperadas, 15 repeticiones/muestras por fila y 60 claves lógicas únicas. Para cada carga comprueba las mismas huellas de IDs/orden, resultados y enlaces, conteos equivalentes de altas/consultas/salidas e identidad de instancias/destinos canónicos. El módulo focalizado terminó en **6 passed**; no se repitió el benchmark completo.

**Checkpoint**: sintéticos y conexión a `--bench` pueden completarse antes de la referencia; ninguna alternativa se adopta por intuición.

---

## Phase 7: Integraciones coordinadas no bloqueantes para el MVP

**Purpose**: completar fronteras con 003/004 y guardado sin convertir trabajo ajeno en tarea de Sofía.

- [x] T052 Conjunta Sofía/Steven/003 — después de T002/T004, crear `tests/test_integracion_ir_a_001_003.py` para dos estados reales con el mismo mapa conocido, paso único, recálculo tras cada cambio de origen/destino/conocimiento, origen=destino y sin ruta distintos; resultado verificable: nunca consulta estado oculto (FR-011, FR-013–FR-015, PR-004, PR-006).

**Evidencia T052 (2026-11-13)**: `tests/test_integracion_ir_a_001_003.py` usa `EstadoPartida`, `MapaCripta`, `MapaConocido`, `VistaMapaConocido`, `Viaje` y `proximo_paso` reales con fixtures offline. Sus tres escenarios comprueban: dos estados reales divergentes con conocimiento equivalente y acceso al mapa real prohibido; paso único recalculado al cambiar origen, destino y conocimiento; y distinción observable entre origen=destino (`alcanzable=True`, costo 0, sin paso) y ausencia de ruta (`alcanzable=False`). Ejecución focalizada junto con T056: **10 passed in 0.29s**, sin omisiones.

- [x] T053 Sofía — después de T002/T004, exponer en `logica/rutas_ponderadas.py` la firma acordada para que «ir a» calcule un siguiente paso desde la vista de Steven, manteniendo recálculo individual como implementación suficiente y sin añadir reglas de ataque/espera (FR-010, FR-011, FR-013–FR-015, PR-004, PR-006).

**Evidencia T053 (2026-11-13)**: `21c234248d4f9b7bcdeb3c9c299e40498a2d131a` publica `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta`. El buscador solo exige `contiene_sala` y `salidas_transitables`, devuelve un paso/costo y no contiene reglas de ataque o espera. `1bc5c62` conecta `Viaje` mediante `VistaMapaConocido`; cada llamada a `siguiente_paso` invoca de nuevo `proximo_paso` con origen y conocimiento vigentes. No fue necesario modificar el algoritmo productivo. Pruebas focalizadas: **45 passed in 0.30s** y los tres escenarios nuevos de T052 incluidos en **10 passed in 0.29s**.
- [x] T054 Conjunta Sofía/003 — añadir al proveedor `benchmarks/terreno_cazador_integrante1.py` la medición completa de un paso de «ir a» frente a 5 ms, primero con sintéticos y finalmente con el mapa conocido oficial; incluir preparación auxiliar necesaria y equivalencia antes del tiempo (FR-013–FR-015, PR-003, PR-004, PR-006).

**Evidencia T054 (2026-11-14)**: la medición propia `medir_paso_ir_a_001` quedó separada de `benchmarks.integrante2.medir_paso_ir_a` y se añadió al adaptador de rutas de 001 ya registrado en `main.py --bench`, sin modificar el punto compartido. Usa `Viaje`, `MapaConocido` y `VistaMapaConocido` reales; incluye creación del viaje/vista, auxiliares de ruta, consulta y limpieza, y deja fuera solo la construcción del fixture. Antes del reloj compara recálculo e inversa experimental en siguiente sala, alcance, costo total, costo de primera salida y motivo. Los sintéticos de 32/128/512 salas cubren desempate, puerta recordada cerrada, ausencia de camino y cambio de conocimiento; la carga publicada usa el mapa conocido oficial disponible localmente, con conocimiento completo de las 50 salas de `cripta-04`, y el par alcanzable 46→41 (paso 45, costo 4000); no es la cripta de referencia de PR-001. `benchmarks/resultados/paso_ir_a_t054_c1_r15_32-128-512-publicado50.json` conserva **26 filas/390 muestras**, semilla 2609, un calentamiento, 15 repeticiones, mediana, p95, máximo, fases, trabajo y memoria separada. En el mapa publicado, recálculo obtuvo **0.4965/0.5136/0.5136 ms** de mediana/p95/máximo y **15/15** muestras `<5 ms`; la construcción fría experimental obtuvo 0.2510/0.3344/0.3344 ms y su consulta reutilizada 0.0036 ms de mediana. En sintéticos, producción cumplió todas las muestras hasta 128 salas y en dos casos baratos de 512; en 512 salas, desempate registró **9/15 muestras que cumplen y 6/15 que superan** el límite, y puerta cerrada **12/15 que cumplen y 3/15 que superan**. La evidencia no afirma PR-001 ni repite T050. Pruebas focalizadas: **38 passed in 3.78s**, integración funcional: **49 passed in 0.42s**, restricciones: **61 passed in 0.57s**.
- [x] T055 Conjunta Steven/Joshua con verificación de Sofía — después de T006 y usando `tests/test_datos/test_guardado_terreno_cazador.py` revisada en T041, **ejecutar** la ida/vuelta del formato real v11 contra `datos/guardado_binario.py`, `service/juego_service.py` y `service/restaurador_partida.py` publicados, comprobando costo/rango/mapa conocido, línea, versiones históricas incompatibles, identidad, alias y ausencia de resultados de ruta; Sofía no implementa campos ajenos (FR-001, FR-009, FR-016, FR-018).

**Evidencia T055 (2026-11-15)**: `tests/test_datos/test_guardado_terreno_cazador.py` terminó en **7 passed in 0.63s**. La ejecución conjunta de ese archivo con `test_mapa_conocido_persistido.py`, `test_guardado_linea.py`, `test_costo_y_rango.py`, `test_service/test_restaurador_partida.py`, `test_service/test_reanudacion_v5.py`, `test_logica/test_linea_tiempo.py`, `test_integracion_001_004.py` y `test_integracion_conocimiento_003_004.py` terminó en **144 passed in 12.09s**. Se verificaron una ida/vuelta v11 completa, costo/rango, conocimiento, consultas y K de la línea, referencias canónicas/alias, continuación después de cargar, rechazo de v9/v10 sin pérdida del estado vigente y ausencia de derivados de ruta en los bytes. No se modificó producción de Steven/Joshua ni el formato.
- [x] T056 Conjunta Sofía/Joshua — después de T005/T040 y de integrar por el flujo del equipo la clase completa `LineaTiempo`, **ejecutar** `tests/test_integracion_001_004.py` sobre puntos de control, estado vivo e inversos en `finally`, comprobando el protocolo de condición `condicion(estado, cambio)` de la punta remota de Joshua, la restauración de eventos posteriores al instante consultado, que cada cambio nuevo ofrece fotografía y que 004 nunca llama al cazador; la interfaz base local por sí sola no cierra esta ejecución (FR-014–FR-016, PR-004, PR-006).

**Evidencia T056 (2026-11-13)**: `d86819d` integra `LineaTiempo` y el gancho `rehacer(estado)` de `a305be635206029666a8bb877acbc44844cf26a8`. `tests/test_integracion_001_004.py` ya no se omite: cubre `condicion(estado, cambio)`, inversos restaurados en `finally`, `_hasta` para eventos posteriores, fotografía/rehacer de los cambios usados por 001, avisos de `vincular_linea`/`recortar`, prohibición de invocar al cazador y una consulta que cruza el punto K=2 y deja intacto el estado vivo. Ejecución focalizada actual: **7 pruebas de T056** dentro de **10 passed in 0.29s**, sin omisiones. Se acepta además la evidencia ejecutada desde PowerShell tras la integración: **79 pruebas específicas aprobadas** y suite completa de **1402 pruebas y 4 subtests aprobados**, sin fallos ni omisiones. Limitación documentada: los dobles mínimos de este archivo aíslan el protocolo; los puntos de control y partidas reales quedan cubiertos por las pruebas integradas de Joshua incluidas en las 79 específicas y en la suite completa.
- [x] T057 Sofía — después de T046/T065, documentar en `specs/001-terreno-y-cazador/research.md` la decisión real de estrategia del **cazador** —individual, compartida o adaptativa— con equivalencia y costo completo; si se adopta estado retenido, actualizar primero plan/tasks con tareas productivas concretas, y si no, no crear caché (FR-013, FR-014, PR-003, PR-006).

**Evidencia T057 (2026-11-10; revisada 2026-11-13)**: `research.md` añade **R-13 — Decisión real de estrategia del cazador (T057)** y actualiza la medición pendiente de R-01. La producción conserva el recálculo individual por cazador y por decisión, sin caché ni estado retenido; la inversa compartida y la reutilizada permanecen exclusivas del benchmark; la adaptativa no se adopta por falta de umbral medido. La revisión recuperó las nueve muestras T048 `>=20 ms`: siete estables y dos inestables, todas `completo` y de recálculo productivo; la retención equivalente tuvo cero. Esto favorece en tiempo a la retención sintética, no al recálculo. T057 permanece cerrada como decisión final del alcance productivo actual porque la evidencia no cubre la referencia oficial ni la política completa de invalidación de `FR-014`; no se inventa un umbral ni se crea caché. Se registran equivalencia, costo completo, trabajo retenido y la ausencia de contadores internos de ruta en producción.
- [x] T066 Conjunta Sofía/003 — después de T054, documentar separadamente en `specs/001-terreno-y-cazador/research.md` la decisión de reutilización para **«ir a»** frente a 5 ms; cumplir con recálculo cierra la decisión sin caché, y cualquier adopción exige primero nuevas tareas con propietario/archivos acordados (FR-013–FR-015, PR-003, PR-004, PR-006).

**Evidencia T066 (2026-11-14)**: `research.md` añade R-14, separada de la estrategia del cazador. La decisión mantiene recálculo productivo por paso y no crea caché: con el mapa conocido completo de la mayor cripta publicada, las 15 muestras productivas quedaron bajo 5 ms. La inversa experimental fue más rápida en la ruta larga publicada y en los sintéticos largos, pero su ventaja no es necesaria para el criterio actual; además, recálculo fue más rápido en rutas resueltas casi de inmediato y en ausencia de camino. Las nueve superaciones sintéticas de 512 salas (6/15 en desempate y 3/15 en puerta cerrada) se conservan como límite, no disparan adopción automática. Si una referencia futura las vuelve relevantes, primero se requieren tareas coordinadas con 003 para propiedad, generación/invalidez ante cambios de conocimiento, ciclo de vida, limpieza y validación tras retroceso/carga. La producción sigue usando exclusivamente el conocimiento del jugador.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: cerrar trazabilidad, restricciones, evidencia real y regresión completa sin confundir planificación con ejecución.

- [x] T058 [P] Sofía — ejecutar `.venv/Scripts/python.exe -m pytest -q tests/test_restricciones_enunciado.py` y corregir infracciones únicamente en los archivos propios señalados; resultado verificable: estructuras/rutas de producción cumplen la constitución (FR-011, FR-018, PR-001–PR-006).
- [x] T059 Sofía — auditar la matriz AC→FR/PR→tareas→pruebas de `specs/001-terreno-y-cazador/tasks.md` contra los 30 escenarios de `spec.md`, corregir cualquier hueco y confirmar los siete AC-B explícitos (FR-001–FR-018, PR-001–PR-006).

**Evidencia T059 (2026-11-10)**: la auditoría automatizada y manual confirmó **30/30 AC** en la matriz, **18/18 FR** y **6/6 PR** citados por tareas, y los **siete AC-B** (AC-B01…AC-B07) explícitos en `spec.md`, en la matriz y en las pruebas previstas. No aparecieron requisitos sin tarea ni tareas sin cita FR/PR. Los dos archivos de prueba referenciados y aún ausentes (`tests/test_datos/test_guardado_terreno_cazador.py` y `tests/test_integracion_ir_a_001_003.py`) corresponden a T041 y T052, que siguen abiertas por dependencias declaradas; no son huecos de la matriz. `tests/test_integracion_001_004.py` ya existe (T040, redactado y validado contra `origin/joshua`; su ejecución local se omite hasta G4b/T056). Se corrigió el recuento obsoleto de `tasks.md` (ahora 58 cerradas/18 abiertas tras T040) y no se alteró la cobertura de escenarios.
- [x] T060 Sofía — ejecutar con `.venv/Scripts/python.exe` todas las pruebas previstas de US1–US4 y las integraciones no bloqueadas, registrando aprobadas/omitidas/fixtures/en línea por separado en `specs/001-terreno-y-cazador/quickstart.md` (FR-001–FR-018, PR-001–PR-006).

**Evidencia T060 (2026-11-10)**: suite completa final, con T040 añadido, `pytest -q -rs --tb=short`: **1287 passed, 1 skipped, 4 subtests passed in 173.39s**. La omisión es el módulo `tests/test_integracion_001_004.py`, que espera G4b/T056. La misma suite antes de T040 dio **1287 passed, 0 skipped, 4 subtests passed in 188.09s**. Una corrida intermedia falló solo en `tests/test_bench_integrante2.py::test_el_costo_crece_de_forma_aproximadamente_lineal` (factor 3.8 frente a 3.0); esa prueba pasó 3/3 aislada y volvió a pasar en la corrida final, por lo que se registra como fluctuación de medición y no como regresión. Foco funcional US1–US4 e integraciones no bloqueadas: **159 passed, 2 subtests passed in 9.99s**. Módulos de benchmark y restricciones: **126 passed in 30.26s**. No se ejecutaron pruebas contra el servicio en línea; la corrida usó fixtures offline. La ejecución de `main.py --bench` con las filas de rutas/agenda/ciclo completas sigue pendiente de T049/T062. El detalle quedó registrado en `quickstart.md`.
- [x] T061 Sofía — ejecutar `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` y resolver regresiones propias hasta conservar toda la suite; registrar conteo real sin reutilizar una línea base anterior en `specs/001-terreno-y-cazador/quickstart.md` (FR-004, FR-005, FR-015–FR-018, PR-006).
- [x] T062 Sofía — ejecutar `main.py --bench`, revisar que las filas de 001 —incluidas construcción/búsqueda/vinculación del mapa— estén conectadas una sola vez y documentar resultados sintéticos frente a límites sin afirmar PR-001 oficial en `specs/001-terreno-y-cazador/quickstart.md` (PR-001–PR-006).

**Evidencia T062 (2026-11-14)**: se reutilizó la corrida oficial T050, ya ejecutada por `main.py --bench` con código 0, sin repetir los 25 proveedores. El extractor volvió a validar en memoria que el JSON completo de **916 filas** produce exactamente el artefacto conservado de **194 filas/2910 muestras**, con 194 claves lógicas únicas, 15 repeticiones por fila y grupos mapa 60/900, agenda 72/1080, rutas 30/450 y ciclo 32/480. La prueba puntual de `main.main()` confirmó la secuencia de **25 proveedores únicos** y una sola inclusión de cada adaptador de mapa, agenda, rutas y ciclo (**1 passed in 0.23s**). PR-002 conserva trabajo productivo constante `(F,D,E,P,Q)=(5,5,6,5,2)` al crecer de 32 a 128/512 salas; PR-003 cubre 24 combinaciones de 1/20 cazadores, rango pequeño/grande, puertas estables/inestables y tres alternativas; PR-004/PR-006 conservan equivalencia y metadatos; PR-005 cubre 36 filas de seis operaciones, 256/512/1024 eventos y dos alternativas. Como resultado descriptivo, las filas nuevas de agenda tienen 43/540 muestras `>=20 ms`, todas lineales, pero agenda no posee ese umbral. En ciclo sintético, producción tiene **10/240** muestras `>=20 ms` (8 estables y 2 inestables en 64 salas/28 cazadores/rango grande) y la retención experimental 0/240. Esto no demuestra ni refuta PR-001: la carga declara `referencia_oficial=pendiente_publicacion_g6` y `afirma_pr001=false`; T051 sigue bloqueada.
- [x] T063 Sofía — actualizar `specs/001-terreno-y-cazador/plan.md` y `specs/001-terreno-y-cazador/research.md` con resultados reales, estrategia final, costo completo, restricciones revisadas y bloqueos que sigan abiertos; no marcar acuerdos/pruebas ausentes ni reservar una versión de guardado (FR-001–FR-018, PR-001–PR-006).

**Evidencia T063 (2026-11-10; revisada 2026-11-13)**: `plan.md` actualiza el resumen, la tabla constitucional, el árbol de archivos, la sección de ruta ponderada, las dependencias, la salida de Phase 0, la puerta de diseño y los riesgos. La revisión final corrigió los estados obsoletos de determinismo/cobertura, el futuro de proveedores/oráculos y la separación T040/T056. `research.md` añade R-13, corrige R-01 y conserva la clasificación completa de las nueve muestras lentas. La estrategia final documentada para el alcance productivo actual es el recálculo individual; la alternativa compartida/reutilizada queda medida y temporalmente no adoptada, sin afirmar superioridad temporal del recálculo. Se registran costo completo, restricciones y bloqueos reales (T004, T006, T049/T050, T051, G4b/G6) sin marcarlos como resueltos. Esos bloqueos son contenido exigido por T063, no precondiciones de su revisión documental; las ejecuciones dependientes conservan sus propias tareas abiertas. No se reservó ni cambió la versión de guardado: `GuardadoBinario.VERSION` sigue en 10 y T006 continúa abierta.
- [x] T067 Sofía — escribir en `DECISIONES.md` la sección §5.1 con problema, alternativas individual/compartida/adaptativa, decisión medida, complejidad, evidencia de `--bench`, límites, enlaces a spec/plan y divergencia frente al plan original (FR-007–FR-015, PR-002–PR-004, PR-006).
- [x] T068 Sofía — escribir en `DECISIONES.md` la sección §5.2 con recálculo frente a reutilización, puertas estables/inestables, eventos relevantes, decisión medida, costo de invalidación/limpieza si aplica, límites y enlaces (FR-014, PR-003, PR-004, PR-006).
- [x] T069 Sofía — escribir en `DECISIONES.md` la parte de agenda de §5.6 con las seis operaciones, carga nueva, alternativa lineal benchmark-local, datos antes/después y conclusión aunque la decisión de Parte I se conserve (PR-005, PR-006).

**Evidencia preparatoria T067/T068/T069 (2026-11-10)**: `DECISIONES.md` incorporó §5.1, §5.2 y la subsección de agenda de §5.6, con enlaces a spec/plan, alternativas, decisión, complejidad, evidencia y límites. §5.2 documenta el recálculo productivo frente a la inversa retenida del benchmark, las puertas estables/inestables, los eventos relevantes y el trabajo de invalidación/reconstrucción; §5.6 conserva `AgendaEventos` y compara las seis operaciones con la lista lineal benchmark-local, incluidas las 24 muestras lineales `>=20 ms`. En ese punto T067 permaneció abierta porque su evidencia literal de `--bench` dependía de T049/T050. T068 y T069 se cerraron con evidencia sintética aislada; ninguna se presentó como referencia oficial ni como cierre de PR-001.

**Evidencia T067 (2026-11-14; cierre)**: §5.1 conserva el problema, los enlaces a spec/plan/research, las alternativas individual, inversa compartida, reutilizada y adaptativa, la decisión productiva sin estado retenido y el análisis esperado de tiempo/memoria. Añade separadamente la ejecución conectada T050 de **15 repeticiones** sin reemplazar las tablas originales de nueve: AC-012 conserva `(F,D,E,P,Q)=(5,5,6,5,2)` al crecer el exterior; AC-014 documenta mediana/p95/máximo para 20 cazadores; y el ciclo sintético conserva 8/15 muestras productivas `>=20 ms` con puertas estables y 2/15 inestables. La evidencia oficial de ejecución confirma el resultado desfavorable de que compartida/reutilizada fueron más rápidas en cargas altas, pero no autoriza producción sin política completa de invalidación, tareas acordadas y referencia oficial. T049/T050/T062/T071 respaldan conexión, unicidad y equivalencia; PR-001 permanece explícitamente no demostrado y bloqueado en T051.
- [x] T070 Sofía — actualizar conjuntamente la sección Parte II de `README.md` con comandos de aceptación de 001, `main.py --bench`, ubicación de JSON sintético/oficial, entorno y cómo distinguir pruebas escritas, ejecutadas, omitidas y bloqueadas; coordinar el archivo compartido sin sobrescribir entradas ajenas (FR-018, PR-001–PR-006).

**Evidencia T070 (2026-11-14)**: `README.md` añade únicamente la subsección **«Parte II — especificación 001: terreno y cazador»** dentro de Mediciones, sin reescribir instrucciones ni resultados de 002/003/004. Incluye comandos existentes para aceptación funcional, integraciones, benchmarks y conexión; el comando real `main.py --bench`; rutas del JSON completo, evidencia filtrada y código de salida; entorno Windows/Python 3.12.10, reloj, calentamiento y 15 repeticiones; y una tabla que distingue pruebas escritas, ejecutadas, omitidas y bloqueadas. Registra 916 filas totales, 194/2910 de 001, carácter sintético, 10/240 muestras productivas de ciclo `>=20 ms` y T051 como bloqueo de la referencia PR-001. No fue necesaria coordinación sobre contenido ajeno porque el cambio quedó aislado en una subsección nueva de 001.
- [x] T071 [US4] Sofía — ejecutar `tests/test_bench_terreno_cazador.py`, `tests/test_bench_mapa_cripta.py` y las filas sintéticas completas después de T043–T050/T065/T072–T075, registrar el cierre real de US4 y dejar AC-013 oficial explícitamente bloqueado por T051 si la referencia no está publicada (PR-001–PR-006).

**Evidencia T071 (2026-11-14)**: los dos módulos exigidos terminaron en **33 passed in 2.66s**; cubren oráculos, equivalencia previa al reloj, AC-009/AC-012/AC-014/AC-015, esquema AC-013, interfaz estándar, conexión real de mapa y sus 60 filas oficiales. La prueba focalizada de composición de `main.py --bench` añadió **1 passed in 0.23s** sin ejecutar cargas. La auditoría de los JSON existentes confirmó las filas sintéticas completas de T043–T050/T065/T072–T075, todas las alternativas/cargas esperadas, 15 muestras por fila, ausencia de duplicados y equivalencia observable en agenda, rutas y ciclo; el mapa conserva huellas equivalentes e identidad canónica. No faltó una ejecución específica y no se lanzó otro benchmark. El alcance sintético de US4 queda cerrado; AC-013/PR-001 permanece explícitamente bloqueado en T051 porque no existe la cripta oficial de referencia y las 10 muestras sintéticas productivas `>=20 ms` no pueden clasificarse como cumplimiento o incumplimiento oficial.
- [x] T076 [US4] Sofía — después de T050/T071, crear en `DECISIONES.md` una subsección propia titulada **«Índice por ID de MapaCripta (evidencia complementaria de 001)»**, separada de §5.4 Resolubilidad, con resultados de construcción, búsqueda por ID y vinculación antes/después, tamaños/cargas, alternativa lineal benchmark-local, identidad comprobada, complejidad observada y divergencias frente a la hipótesis previa; añadir desde la revisión de decisiones de §5.6 un enlace explícito a esa subsección, sin reescribir §5.4, reatribuir el componente ni modificar decisiones de 002 (FR-011, FR-013, FR-018, PR-001, PR-002, PR-004, PR-006).

**Evidencia documental preparatoria T076 (2026-11-09)**: `DECISIONES.md` conserva §5.4 sin cambios y añade desde §5.6 un enlace a la subsección independiente **«Índice por ID de MapaCripta (evidencia complementaria de 001)»**. Documenta problema/consumidores, lista estable más `TablaHashImpl`, alternativa lineal benchmark-local, complejidades de construcción/consulta/sustitución/vinculación, identidad previa al tiempo, entorno/cargas/unidades y los resultados conservados en ambos JSON. Registra sin explicación causal la muestra original de construcción de `33 018 900 ns` y la repetición posterior de 30 muestras. T076 permanece abierta porque T049/T050/T071 aún deben registrar el proveedor en `main.py --bench`, ejecutar/validar las filas conectadas y cerrar la evidencia; tampoco se presenta esta medición aislada como prueba del ciclo completo de 20 ms.

**Evidencia T076 (2026-11-14; cierre documental del índice)**: la subsección enlazada desde §5.6 conserva por separado la corrida original de 9 repeticiones y la repetición de 30, y añade las **60 filas/900 muestras oficiales de T050** con código 0, entorno, semilla 1729, un calentamiento, 15 repeticiones, tamaños 8/16/32/64/128/512, cargas 1/4, alternativas y tablas completas de mediana/p95/máximo para construcción, consulta y vinculación. La decisión mantiene lista estable más `TablaHashImpl`, la alternativa lineal exclusivamente benchmark-local y el análisis esperado/peor caso. Documenta que el índice no siempre gana en cargas pequeñas, mientras consulta/vinculación se separan al crecer `V` y construcción tiene medianas menores desde 128 salas; no atribuye causas a muestras extremas. §5.4 no se modificó, no se reatribuyeron componentes de 002 y no se afirma PR-001 ni el presupuesto del ciclo completo. T071 cerró posteriormente el alcance sintético de US4; T051 conserva la referencia oficial bloqueada.

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
| AC-014 | PR-003, PR-004, PR-006 | T042–T046, T049–T050, T065 | `tests/test_bench_terreno_cazador.py`, fila AC-014 y equivalencia AC-009 |
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
| G1 — firma/representación del buscador | **cerrada por T002** | ya no bloquea T022/T024 ni T052–T054 | US1, índice y pruebas sintéticas |
| G2 — costo/rango/simetría publicados e integrados | **cerrada por T003 en `5000d1f`** | ya no bloquea T010/T018, T016–T017, T027–T029 ni T064 | persistencia conjunta completada después por T006 |
| G3 — vista de mapa conocido | **cerrada por T004** | ya no bloquea T052–T054 | cazador, porque usa su vista real independiente |
| G4a — revisión cruzada de interfaz Joshua ya integrada | **cerrada por T005** | ya no bloquea T040; satisface una precondición de T056 | disponibilidad local de interfaz base, `deepcopy` y recálculo |
| G4b — `LineaTiempo` completa integrada localmente | **cerrada por la integración `d86819d` y la ejecución T056** | ya no bloquea tareas; T056 se ejecutó sin omisiones | evidencia histórica T040 e interfaz base ya local |
| G5 — persistencia/versionado publicados | **cerrada por T006 en v11 (`d1ad048`)** | ya no bloquea T041/T055, cerradas con ejecución real | desarrollo desde fuente fresca y benchmarks sintéticos |
| G6 — validación de referencia oficial | `cripta-06` publicada; falta escenario real con decenas o aclaración oficial (R-16) | T051 | T042–T054, T066, T072–T075, pruebas funcionales y medición con la mayor cripta publicada local |

### Phase Dependencies

- **Phase 1**: T001 es la revisión posterior de la remediación ya aplicada y debe completarse antes de código. T002–T006 pueden avanzar en paralelo con trabajo que no bloqueen.
- **Phase 2**: después de T001; T008 depende de T007 y T009 verifica T008.
- **US1 (Phase 3)**: las pruebas pueden escribirse antes, pero T016–T017/T064 dependen de T003 integrado; usan el índice de Phase 2 para destinos frecuentes.
- **US2 (Phase 4)**: depende de T002, T003 y Phase 2; integra sobre US1 para cobrar el paso.
- **US3 (Phase 5)**: depende de US2; T031 cerró el núcleo propio. T040 dependió de T005 y T041 de T006; ambas integraciones y sus ejecuciones T055/T056 están cerradas.
- **US4 (Phase 6)**: oráculos pueden escribirse tras T001; mediciones de rutas/ciclo dependen de US1–US3. T072 puede escribirse tras T001 y T073–T075 dependen de T008, no de costo/rango ni de la salida sin inversa. T043 sigue a T042; T065 sigue a T046; T049/T050 integran también el mapa; T051 espera demostrar la carga de decenas en la referencia publicada. US3 no depende de US4.
- **Phase 7**: T052–T054 se cerraron sobre T002/T004; T055 se cerró sobre T006/T041; T056 sobre T005/T040 y G4b; T057 sobre T046/T065 y T066 tras T054.
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
2. Completar Phase 2 sin cambiar firmas, orden ni identidad del mapa; la política confirmada de salidas sin inversa no bloquea estas pruebas independientes.
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

La ruta de producción recalcula cada paso. T046/T065 deciden por separado la estrategia del cazador en T057; T054 mide «ir a» y T066 cierra su decisión de reutilización. Las alternativas permanecen en benchmarks. El recálculo cumplió 5 ms con el mapa conocido completo de la mayor cripta publicada y cierra «ir a» sin caché, generaciones ni invalidación productiva; las superaciones sintéticas de 512 salas quedan documentadas como límite.

---

## Notes

- Cada tarea cita archivo(s), resultado verificable y FR/PR.
- Las 22 marcas `[P]` se limitan a archivos distintos y dependencias satisfechas; T042→T043 es expresamente secuencial.
- Las tareas de Steven/Joshua se verifican como dependencias; no autorizan a Sofía a modificar sus documentos o código sin coordinación.
- Las pruebas de `Sala` existentes se reutilizan; no se crea otra regresión para lo ya cubierto.
- La validación de decenas de cazadores en la referencia publicada mantiene abierta T051, no el resto del desarrollo; las notas fechadas anteriores conservan su contexto de referencia aún no publicada.
- Ejecutar `/speckit.analyze` después de generar este archivo y antes de `/speckit.implement` es obligatorio.
