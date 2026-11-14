---

description: "Tareas de la capacidad 003-niebla-y-ir-a"
---

# Tareas: Niebla de guerra y viaje automático «ir a»

**Entrada**: documentos de diseño en `specs/003-niebla-y-ir-a/`

**Requisitos previos**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Pruebas**: incluidas. El spec las pide en `SC-007` y el Principio XI de la constitución las
exige.

**Organización**: por historia de usuario, para que cada una se implemente y se pruebe sola.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: puede ir en paralelo (archivo distinto, sin depender de tareas incompletas)
- **[US1]…[US5]**: a qué historia pertenece
- Cada tarea lleva la ruta exacta y los `FR` que cumple (§2.5)

## Rutas del proyecto

El proyecto no usa `src/`. Las capas son `contratos/`, `datos/`, `dto/`, `logica/`, `service/`,
`controller/`, `vista/`, `estructuras/`, `benchmarks/` y `tests/`, en la raíz del repositorio.

---

## Fase 1: Preparación

**Propósito**: tener criptas de prueba con la topología que esta capacidad necesita, antes de
tocar código.

- [ ] T001 [P] Crear el paquete `tests/fixtures/niebla/cripta-rutas/` con una cripta donde existan
      dos caminos de igual costo total entre dos salas, para ejercitar el desempate por menor id
      (`FR-012`), con la estructura que `FuenteOffline` ya sabe leer
- [ ] T002 [P] Crear el paquete `tests/fixtures/niebla/cripta-cierre/` con una puerta de cierre
      automático en el camino, para ejercitar la memoria de puertas desactualizada (`FR-006`,
      `FR-014`)
- [ ] T003 [P] Crear el paquete `tests/fixtures/niebla/cripta-antorcha/` con una sala de muchas
      vecinas, algunas tras puertas cerradas, para ejercitar la antorcha (`FR-024`)

---

## Fase 2: Base (bloquea todo lo demás)

**Propósito**: el conocimiento del jugador tiene que existir y vivir en el estado antes de que
nada pueda consultarlo.

**Crítico**: ninguna historia puede empezar hasta que esta fase esté completa.

- [ ] T004 Crear `logica/mapa_conocido.py` con la estructura del conocimiento: salas exploradas,
      salas avistadas y puertas observadas, cada una en una `TablaHashImpl` indexada por id. Lo
      desconocido NO se almacena: una sala desconocida simplemente no está en ninguna tabla
      (`FR-001` a `FR-004`). Prohibidos `set`, `heapq`, `collections` y `sorted()` (§6.2)
- [ ] T005 Implementar en `logica/mapa_conocido.py` las consultas de estado de una sala y de
      estado recordado de una puerta, en O(1) promedio, porque ocurren en cada dibujo de la vista
      y en cada paso del viaje (`FR-001`, `FR-006`, `SC-002`)
- [ ] T006 Implementar en `logica/mapa_conocido.py` la revelación al entrar a una sala: la sala
      pasa a explorada con su nombre, sus salidas y sus costos, y sus vecinas pasan a avistadas.
      El costo DEBE ser proporcional a las salidas de esa sala, no al tamaño del mapa conocido
      (`FR-002`, `FR-003`, `SC-003`)
- [ ] T007 Implementar en `logica/mapa_conocido.py` la observación de puertas: estando en una
      sala, el estado de cada puerta que la conecta se registra tal como está en ese momento, y
      sobrescribe la observación anterior (`FR-006`)
- [ ] T008 Añadir el mapa conocido a `dto/estado_partida.py`, con la sala inicial ya explorada
      desde el instante cero (`FR-005`)
- [ ] T009 Conectar la revelación al movimiento en `logica/motor_juego.py`: entrar a una sala
      actualiza el conocimiento antes de que nada lo consulte (`FR-002`, `FR-006`)
- [ ] T010 [P] Escribir en `tests/test_logica/test_mapa_conocido.py` las pruebas de los tres
      estados, de la sala inicial explorada y de que una sala desconocida no aparece de ninguna
      forma (`FR-001` a `FR-005`)

**Punto de control**: el jugador tiene un mapa propio que avanza al moverse. Las historias pueden
empezar.

---

## Fase 3: Historia 1 — El jugador solo ve lo que ha descubierto (P1) — MVP

**Meta**: que la vista deje de mostrar la cripta entera y muestre solo el conocimiento.

**Prueba independiente**: al empezar una partida solo se conoce la sala inicial y lo que hay
detrás de sus salidas; tras moverse, esa vecina se conoce por completo.

### Pruebas de la Historia 1

- [ ] T011 [P] [US1] Escribir en `tests/test_logica/test_mapa_conocido.py` la prueba de que una
      sala avistada revela únicamente su existencia: ni nombre, ni salidas, ni contenido
      (`FR-003`)
- [ ] T012 [P] [US1] Escribir la prueba de la memoria de puertas desactualizada con
      `cripta-cierre`: una puerta observada abierta sigue figurando abierta tras cerrarse sola, y
      se corrige al volver a observarla (`FR-006`)
- [ ] T013 [P] [US1] Escribir en `tests/test_logica/test_mapa_conocido.py` la prueba de que
      revelar las mismas salas sobre un mapa conocido mucho mayor no cuesta proporcionalmente más
      (`SC-003`)

### Implementación de la Historia 1

- [ ] T014 [US1] Exponer el mapa conocido desde `service/juego_service.py` como dato, para que la
      interfaz lo pinte sin recibir el esqueleto completo (`FR-007`)
- [ ] T015 [US1] Dar al mapa conocido una forma legible para la interfaz —salas exploradas con sus
      salidas y estado recordado, y la lista de avistadas— según
      [contracts/cli-ir-a.md](./contracts/cli-ir-a.md) (`FR-008`)
- [ ] T016 [US1] **Depende de Joshua** (`controller/` y `vista/` son suyos según
      `REPARTO_PARTE2.md`): añadir el comando que muestra el mapa conocido, y dejar de pintar las
      salas que el jugador no conoce. §7.3 lo exige en la interfaz mínima (`FR-007`, `FR-008`)

**Punto de control**: la niebla funciona y se puede probar sola.

---

## Fase 4: Historia 2 — Viajar a una sala ya explorada (P1)

**Meta**: «ir a» lleva al jugador por el camino más barato que él conoce, paso a paso.

**Prueba independiente**: tras explorar un recorrido, pedir ir a una sala visitada lleva al
jugador allí con movimientos ordinarios, sin usar nada que no conozca.

### Pruebas de la Historia 2

- [ ] T017 [P] [US2] Escribir en `tests/test_logica/test_viaje.py` la prueba de contrato de la
      vista conocida con los casos de
      [contracts/vista-conocida.md](./contracts/vista-conocida.md): sala explorada sí, avistada
      no, desconocida no, salida recordada abierta hacia explorada sí, hacia avistada no, y
      recordada cerrada no (`FR-011`)
- [ ] T018 [P] [US2] Escribir la prueba del desempate por menor id con `cripta-rutas`, y de que
      dos ejecuciones iguales dan el mismo recorrido (`FR-012`, `SC-006`)
- [ ] T019 [P] [US2] Escribir la prueba de que pedir ir a una sala avistada, desconocida o
      inexistente se rechaza indicando el motivo (`FR-010`)
- [ ] T020 [P] [US2] Escribir la prueba de que el viaje no abre puertas aunque el jugador tenga la
      llave (`FR-015`)
- [ ] T021 [P] [US2] Escribir la prueba de `SC-005`: dos estados reales distintos que produzcan el
      mismo mapa conocido producen el mismo viaje. Es la garantía de separación que acordó 001
- [ ] T022 [P] [US2] Escribir la prueba de que pedir ir a la sala actual termina de inmediato sin
      consumir pasos ni tiempo (`FR-009`)

### Implementación de la Historia 2

- [ ] T023 [US2] Implementar en `logica/mapa_conocido.py` la vista que consume el buscador de 001:
      `contiene_sala` responde solo por salas exploradas, y `salidas_transitables` devuelve solo
      las salidas recordadas abiertas hacia salas exploradas, con el costo conocido
      (`FR-011`, contrato en [contracts/vista-conocida.md](./contracts/vista-conocida.md))
- [ ] T024 [US2] Crear `logica/viaje.py` que pide un paso al buscador de `logica/rutas_ponderadas.py`
      con esa vista, lo ejecuta como acción ordinaria y vuelve a pedir el siguiente. NO guarda la
      ruta: §3.4 exige recalcular antes de cada paso (`FR-009`, `FR-013`, `FR-014`)
- [ ] T025 [US2] Rechazar en `logica/viaje.py` los destinos que no son salas exploradas, con un
      motivo legible (`FR-010`)
- [ ] T026 [US2] Hacer que cada paso sea una acción completa del jugador en `logica/viaje.py`:
      consume tiempo según el costo de la salida y deja correr los eventos del reloj entre paso y
      paso (`FR-013`)
- [ ] T027 [US2] Impedir en `logica/viaje.py` que el viaje abra puertas, aunque el jugador tenga
      la llave (`FR-015`)
- [ ] T028 [US2] Exponer el viaje desde `service/juego_service.py` como dato: el motivo de parada
      y la sala donde quedó (`FR-019`)

**Punto de control**: las Historias 1 y 2 funcionan por separado.

---

## Fase 5: Historia 3 — Entender por qué se detuvo el viaje (P2)

**Meta**: cada parada tiene un motivo y el jugador lo ve.

**Prueba independiente**: se provoca cada condición de parada y el motivo informado es el
correcto.

### Pruebas de la Historia 3

- [ ] T029 [P] [US3] Escribir en `tests/test_logica/test_viaje.py` la prueba de las cuatro
      condiciones de parada: llegó, hay enemigos, recibió daño y no hay camino conocido
      (`FR-016`)
- [ ] T030 [P] [US3] Escribir la prueba del enemigo **dormido**, que es el caso obligatorio de
      §3.4: también detiene el viaje (`FR-016`)
- [ ] T031 [P] [US3] Escribir la prueba de que el viaje **sí** empieza cuando el jugador ya está
      en una sala con enemigos, porque la parada se dispara al entrar (`FR-017`)
- [ ] T032 [P] [US3] Escribir la prueba de que el daño recibido entre dos pasos, sin que el
      jugador se mueva, también detiene el viaje (`FR-018`)
- [ ] T033 [P] [US3] Escribir con `cripta-cierre` la prueba del caso obligatorio de §3.4: una
      puerta que el mapa recordaba abierta y en realidad se cerró NO detiene el viaje; el mapa se
      corrige al llegar y el cálculo siguiente la evita (`FR-014`)

### Implementación de la Historia 3

- [ ] T034 [US3] Implementar en `logica/viaje.py` las cuatro condiciones de parada, cada una con
      su motivo distinguible (`FR-016`, `FR-019`)
- [ ] T035 [US3] Implementar en `logica/viaje.py` que estar ya en una sala con enemigos no impide
      empezar el viaje (`FR-017`)
- [ ] T036 [US3] Detectar en `logica/viaje.py` el daño recibido entre dos pasos, no solo al
      moverse (`FR-018`)
- [ ] T037 [US3] Anotar en la bitácora cada paso como un movimiento individual, y la orden de ir a
      como un comentario, en `logica/viaje.py` (`FR-020`)
- [ ] T038 [US3] **Depende de Joshua**: añadir el comando «ir a» y mostrar el motivo de parada,
      consumiendo lo que expone T028. §7.3 lo exige en la interfaz mínima (`FR-019`)

**Punto de control**: las tres primeras historias funcionan por separado.

---

## Fase 6: Historia 4 — El conocimiento es parte de la partida (P2)

**Meta**: el mapa conocido se revierte con el pergamino, se guarda y se reconstruye.

**Prueba independiente**: se explora, se guarda, se reanuda y el mapa es el mismo; se retrocede un
paso y vuelve al estado anterior.

### Pruebas de la Historia 4

- [ ] T039 [P] [US4] Escribir en `tests/test_logica/test_mapa_conocido.py` la prueba del caso
      obligatorio de §3.4: usar el pergamino durante un viaje revierte **solo el último paso**, y
      el mapa conocido vuelve al estado anterior a ese paso, sin las salas que reveló (`FR-021`)
- [ ] T040 [P] [US4] Escribir en `tests/test_datos/test_mapa_conocido_persistido.py` la prueba de
      que el mapa conocido sobrevive a guardar, cerrar y reanudar, y de que un archivo de la
      versión anterior se reporta incompatible (`FR-022`)
- [ ] T041 [P] [US4] Escribir la prueba de que registrar y deshacer una revelación cuestan un
      tiempo que no crece con el tamaño del mapa conocido (`SC-004`)

### Implementación de la Historia 4

- [ ] T042 [US4] Registrar cada revelación en `logica/mapa_conocido.py` como un cambio reversible,
      heredando del contrato que ya existe en `logica/cambios.py` **sin modificar ese archivo**,
      que es de otro integrante (Principio VIII). Sin copias completas del mapa (Principio VII)
      (`FR-021`, `FR-022`, `SC-004`)
- [ ] T043 [US4] Subir `GuardadoBinario.VERSION` de 10 a 11 en `datos/guardado_binario.py` y
      escribir el mapa conocido en el archivo de partida (`FR-022`)
- [ ] T044 [US4] Reconstruir el mapa conocido al reanudar en `service/restaurador_partida.py`, y
      hacer que un archivo de la versión 10 se reporte como incompatible en lugar de cargarse a
      medias (`FR-022`)
- [ ] T045 [US4] Comprobar que la línea de tiempo reconstruye el mapa conocido de un instante
      pasado, sin alterar el actual (`FR-022`)

**Punto de control**: el conocimiento sobrevive al retroceso, al guardado y a la consulta de un
instante pasado.

---

## Fase 7: Historia 5 — La antorcha ilumina lo que hay alrededor (P3)

**Meta**: con la antorcha encendida, entrar a una sala revela también sus vecinas.

**Prueba independiente**: entrar con la antorcha encendida deja las vecinas exploradas; con la
antorcha apagada, solo avistadas.

### Pruebas de la Historia 5

- [ ] T046 [P] [US5] Escribir con `cripta-antorcha` la prueba del caso obligatorio de §3.4: con la
      antorcha encendida las vecinas quedan exploradas por cualquier salida, abierta o cerrada, y
      no se activa ninguno de sus enemigos ni trampas (`FR-023`, `FR-024`)
- [ ] T047 [P] [US5] Escribir la prueba de que una vecina revelada por la antorcha conoce su
      nombre y sus salidas pero no su contenido, y de que es un destino válido de «ir a»
      (`FR-024`, `FR-010`)
- [ ] T048 [P] [US5] Escribir la prueba de que con la antorcha apagada las vecinas quedan solo
      avistadas (`FR-003`)

### Implementación de la Historia 5

- [ ] T049 [US5] Implementar en `logica/mapa_conocido.py` la revelación por antorcha: al entrar a
      una sala con la antorcha encendida, todas sus vecinas pasan a exploradas, a través de
      cualquier salida, esté abierta o cerrada (`FR-023`)
- [ ] T050 [US5] Comprobar que esa revelación no toca el contenido de las vecinas ni activa sus
      enemigos ni sus trampas (`FR-024`)

**Punto de control**: las cinco historias funcionan por separado.

---

## Fase 8: Cierre y asuntos transversales

- [ ] T051 Añadir a `benchmarks/integrante2.py` la medición del mapa conocido frente a una
      alternativa que recorre el mapa para responder lo mismo, con criptas sintéticas
      deterministas por semilla (`SC-008`, §5.3, §6.3)
- [ ] T052 Medir el paso de «ir a» con el mapa conocido completo de la cripta de referencia y
      comprobar que queda por debajo de 5 ms, separando la preparación del intervalo cronometrado
      y con calentamiento y repeticiones (`SC-001`, §6.1)
- [ ] T053 Comprobar que `SC-002` y `SC-003` se cumplen con datos: las consultas no crecen con el
      mapa conocido y explorar cuesta en proporción a lo revelado
- [ ] T054 Conectar las mediciones nuevas a `--bench`, porque un benchmark que ningún punto de
      entrada ejecuta no cuenta como evidencia (Principio IX)
- [ ] T055 [P] Comprobar que `tests/test_restricciones_enunciado.py` sigue en verde sobre el
      código nuevo: sin `heapq`, `set`, `collections`, bibliotecas de grafos ni `sorted()` (§6.2)
- [ ] T056 Ejecutar la validación de punta a punta de [quickstart.md](./quickstart.md), los diez
      pasos
- [ ] T057 Registrar en `PROMPTS_LLM.md`, en la sección «Steven Moya Porras — Parte II», los
      comandos de spec-kit usados en esta capacidad (§2.6)
- [ ] T058 Escribir en `DECISIONES.md` la sección §5.3 con el formato de §7.1 —problema,
      alternativas consideradas, decisión, análisis de complejidad, evidencia empírica y límites
      conocidos—, enlazando a [spec.md](./spec.md) y [plan.md](./plan.md), e indicando si la
      decisión final coincide con la del plan. Debe responder lo que §5.3 pregunta: si se comparte
      implementación con la búsqueda del cazador o si conviene separarlas. Las alternativas están
      en [research.md](./research.md) y la evidencia sale de T051 a T053
- [ ] T059 Actualizar `README.md` con los comandos nuevos de esta capacidad y de la 002
      (`--verificar`, `--forzar`, ver el mapa conocido e «ir a»), que §7.2 exige

---

## Dependencias y orden

### Entre fases

- **Fase 1 (Preparación)**: sin dependencias, puede empezar ya
- **Fase 2 (Base)**: depende de la Fase 1 y **bloquea todas las historias**
- **Fases 3 a 7 (Historias)**: todas dependen de la Fase 2
- **Fase 8 (Cierre)**: depende de las historias que se quieran entregar

### Entre historias

- **US1 (P1)**: arranca al cerrar la Fase 2. No depende de ninguna otra historia
- **US2 (P1)**: necesita el conocimiento de la Fase 2 y el buscador de 001, que ya existe en
  `logica/rutas_ponderadas.py`
- **US3 (P2)**: necesita el viaje de US2
- **US4 (P2)**: necesita el conocimiento de la Fase 2; se puede hacer en paralelo con US2 y US3
- **US5 (P3)**: necesita la revelación de la Fase 2; independiente de US2, US3 y US4

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar antes de implementar
- El conocimiento antes de la vista que lo consulta; la vista antes del viaje que la usa

### Qué puede ir en paralelo

- T001 a T003: tres fixtures, archivos distintos
- Las pruebas de cada historia entre sí: T011–T013, T017–T022, T029–T033, T039–T041, T046–T048
- US4 y US5 pueden repartirse una vez cerrada la Fase 2

---

## Estrategia de entrega

### Mínimo entregable: Fases 1, 2 y 3

Con eso el jugador deja de ver lo que no ha descubierto, que es el núcleo de §3.3. La niebla sola
ya es una capacidad entregable.

### Entrega incremental

1. Fases 1 y 2 → el jugador tiene un mapa propio
2. + US1 → deja de ver lo que no conoce (mínimo entregable)
3. + US2 → puede viajar a una sala explorada
4. + US3 → entiende por qué se detuvo
5. + US4 → el conocimiento se revierte y se guarda
6. + US5 → la antorcha revela las vecinas
7. + Fase 8 → mediciones, Documento de Decisiones y README

### Reparto

Esta capacidad es de un solo integrante, con dos excepciones.

**T016 y T038 no son de este integrante.** Tocan `controller/` y `vista/`, que según
`REPARTO_PARTE2.md` son de Joshua. Están aquí porque `FR-007`, `FR-008` y `FR-019` no se cumplen
sin ellas y §7.3 las exige en la interfaz mínima, pero el trabajo es suyo. La frontera es la misma
que se usó en 002: el servicio entrega el mapa conocido y el resultado del viaje **como datos**
(T014, T015, T028) y la interfaz los pinta.

**T043 toca el formato de guardado**, que es compartido. Conviene avisar antes de hacerlo para que
la línea de tiempo entre en el mismo salto de versión, en vez de provocar un v12.

---

## Notas

- `[P]` = archivos distintos, sin dependencias entre sí
- Cada tarea cita sus `FR`, que es lo que §2.5 pide para la trazabilidad de la defensa
- Confirmar que cada prueba falla antes de implementar lo que la hace pasar
- Un commit por tarea o por grupo con sentido
- T042 hereda del contrato de cambios reversibles **sin modificar** el archivo de otro integrante;
  si eso no bastara, hay que acordarlo antes (Principio VIII)
- No se escribe un segundo buscador de caminos: T023 construye la vista y T024 usa el buscador de
  001 que ya existe
