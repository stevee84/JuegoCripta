# Feature Specification: Terreno y cazador

**Feature Branch**: `Sofia`

**Created**: 2026-11-07

**Status**: Clarified — reglas pendientes resueltas el 2026-11-07

**Input**: User description: "Crear la especificación 001-terreno-y-cazador de la Parte II de JuegoCripta, correspondiente a Sofía, sin crear ni cambiar de rama."

## Clarifications

### Session 2026-11-07

- Q: Cuando una salida declara un costo no entero, menor que 1 o contradictorio entre sus dos sentidos, ¿qué debe hacer el programa? → A: Rechazar la cripta con un error descriptivo que identifique la salida y los valores inválidos o contradictorios; no convertir ni reemplazar silenciosamente los datos. Esta es una política acordada ante datos inválidos, no una regla textual del PDF. La ausencia del campo conserva el valor predeterminado 100.
- Q: ¿Qué valores debe admitir el rango de un cazador y qué debe ocurrir si falta o es inválido? → A: Admitir un rango entero mayor o igual que 0. Rechazar valores ausentes, negativos, booleanos o no enteros con un error descriptivo que identifique la ficha; no convertir cadenas ni establecer un valor predeterminado. Esta es una política acordada para el dominio del rango, no una exigencia textual del PDF.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Transitar por terreno con costo (Priority: P1)

Como participante de una partida, quiero que el tiempo de movimiento refleje el costo de la salida y la velocidad del actor, para que el terreno afecte de forma consistente al jugador y a todos los enemigos sin alterar las demás acciones.

**Why this priority**: El costo variable de movimiento es la regla base sobre la que dependen el cazador y la carga temporal de toda la simulación.

**Independent Test**: Puede verificarse con actores de distintas velocidades que atraviesen salidas con costo presente, ausente y mínimo, observando el siguiente instante de acción y comprobando que las acciones no relacionadas con movimiento conservan sus reglas.

**Acceptance Scenarios**:

1. **AC-001 — Costo predeterminado y simétrico [FR-001, FR-002]**: **Given** una salida sin costo declarado que conecta dos salas, **When** cualquier actor la atraviesa en cualquiera de los dos sentidos, **Then** el costo usado es 100 en ambos sentidos.
2. **AC-002 — Intervalo de movimiento [FR-003]**: **Given** un actor con velocidad positiva que atraviesa una salida de costo válido, **When** termina el movimiento, **Then** su intervalo hasta la próxima acción es `max(1, costo_salida * 100 // velocidad)`.
3. **AC-003 — Acciones no modificadas [FR-004, FR-005]**: **Given** actores que atacan, esperan o realizan cualquier acción distinta de moverse, **When** se programa su siguiente acción, **Then** se conserva el costo y el comportamiento establecidos antes de esta capacidad.
4. **AC-B06 — Apéndice B: costo 1 y velocidad alta [FR-003]**: **Given** un actor de velocidad suficientemente alta para que la división entera de una salida de costo 1 produzca 0, **When** atraviesa la salida, **Then** el intervalo resultante es 1.
5. **AC-B07 — Apéndice B: cambio de velocidad en salida costosa [FR-006]**: **Given** un actor que ya atravesó una salida costosa y tiene una próxima acción programada, **When** su velocidad cambia en el instante `t`, **Then** el tiempo restante se reajusta a `max(1, (tiempo_siguiente - t) * velocidad_anterior // velocidad_nueva)`, la próxima acción queda en `t + tiempo_restante_reajustado` y la reprogramación asigna un número de secuencia nuevo para conservar el desempate determinista heredado.
6. **AC-019 — Costo presente inválido [FR-001]**: **Given** una salida cuyo costo presente es booleano, no entero o menor que 1, **When** se valida la cripta, **Then** se rechaza con un error descriptivo que identifica la salida y el valor inválido, sin convertirlo ni reemplazarlo silenciosamente.
7. **AC-020 — Costos contradictorios [FR-002]**: **Given** una salida para la que existen ambos sentidos y estos declaran costos distintos, **When** se valida la cripta, **Then** se rechaza con un error descriptivo que identifica la salida y ambos valores, sin elegir ni sustituir silenciosamente ninguno. La ausencia completa del sentido inverso es válida y no constituye por sí sola una contradicción.

---

### User Story 2 - Persecución observable del cazador (Priority: P1)

Como jugador, quiero que cada cazador ataque cuando me alcanza y, en otro caso, avance por una ruta abierta de costo mínimo dentro de su rango, para que su persecución sea predecible por las reglas y no por detalles internos.

**Why this priority**: Es el comportamiento principal de la capacidad y debe tener un resultado único para cada estado de la partida.

**Independent Test**: Puede verificarse con mapas pequeños de costos conocidos, variando rutas, rango y estado de puertas, y comparando la acción observada con la decisión definida por las reglas.

**Acceptance Scenarios**:

1. **AC-004 — Ataque prioritario [FR-007]**: **Given** un cazador y el jugador en la misma sala, aun cuando existan salidas abiertas, **When** llega el turno del cazador, **Then** ataca y no intenta moverse ni esperar.
2. **AC-B01 — Apéndice B: sin ruta abierta [FR-008]**: **Given** un cazador separado del jugador sin ninguna ruta formada únicamente por salidas abiertas, **When** decide su acción, **Then** espera con costo 100.
3. **AC-B02 — Apéndice B: ruta fuera de rango [FR-008, FR-009]**: **Given** que el costo mínimo `d` hasta el jugador es mayor que el rango del cazador, **When** decide su acción, **Then** espera con costo 100.
4. **AC-005 — Límite inclusivo del rango [FR-009, FR-010]**: **Given** que existe una ruta abierta de costo mínimo `d` y `d == rango`, **When** decide su acción, **Then** se mueve exactamente un paso por una ruta mínima y no espera por razón de rango.
5. **AC-B03 — Apéndice B: costo antes que cantidad de salas [FR-009, FR-010]**: **Given** una ruta con menos salas pero mayor costo y otra con más salas pero menor costo, ambas abiertas y dentro del rango, **When** el cazador decide, **Then** inicia la ruta de menor costo total.
6. **AC-B04 — Apéndice B: empate entre primeras vecinas [FR-011]**: **Given** dos o más vecinas con ID de sala entero que inician rutas abiertas con el mismo costo mínimo total, **When** el cazador decide, **Then** elige la vecina con el menor valor numérico de ID, sin convertir silenciosamente valores de otros tipos.
7. **AC-006 — Un solo paso y costo elegido [FR-010, FR-012]**: **Given** una ruta mínima de varias salidas dentro del rango, **When** actúa el cazador, **Then** atraviesa únicamente la primera salida y el costo de su acción es el costo de esa salida.
8. **AC-007 — Independencia del contenido descargado [FR-013]**: **Given** el mismo esqueleto, jugador y estado actual de puertas en dos partidas, pero distinto conjunto de contenidos de salas descargados, **When** el cazador decide, **Then** produce la misma acción en ambas partidas.
9. **AC-021 — Rango ausente o inválido [FR-009]**: **Given** una ficha de cazador cuyo rango está ausente, es negativo, booleano o no entero, **When** se valida la ficha, **Then** se rechaza con un error descriptivo que la identifica, sin convertir cadenas ni establecer un valor predeterminado.
10. **AC-022 — Rango cero en otra sala [FR-008, FR-009]**: **Given** un cazador de rango 0 en una sala distinta de la del jugador, **When** llega su turno, **Then** espera con costo 100 porque toda ruta abierta tiene costo positivo y queda fuera de su rango.
11. **AC-023 — Rango cero compartiendo sala [FR-007, FR-009]**: **Given** un cazador de rango 0 que comparte sala con el jugador, **When** llega su turno, **Then** ataca por la prioridad de ataque y no espera por razón de rango.

---

### User Story 3 - Decisiones vigentes, deterministas y reversibles (Priority: P1)

Como jugador y revisor, quiero que cada decisión del cazador corresponda al estado actual y pueda reproducirse o deshacerse sin divergencias, para confiar en cierres de puertas, repeticiones y pergaminos de retroceso.

**Why this priority**: Una optimización nunca puede cambiar el juego observable ni romper las garantías ya entregadas.

**Independent Test**: Puede verificarse repitiendo estados idénticos, alterando puertas o la posición del jugador entre turnos, y ejecutando y deshaciendo un intervalo completo para comparar el estado restaurado y la decisión posterior.

**Acceptance Scenarios**:

1. **AC-B05 — Apéndice B: puerta cerrada entre turnos [FR-014]**: **Given** una puerta perteneciente a la ruta mínima del turno anterior, **When** se cierra antes del siguiente turno del cazador, **Then** la nueva decisión coincide con calcular desde cero usando esa puerta cerrada.
2. **AC-008 — Jugador movido entre turnos [FR-014]**: **Given** que el jugador cambia de sala después de una decisión del cazador, **When** llega el siguiente turno del cazador, **Then** la decisión coincide con calcular desde cero hacia la sala actual del jugador.
3. **AC-009 — Estado actual completo [FR-013, FR-014]**: **Given** una combinación determinada de esqueleto y puertas actuales, **When** se comparan una decisión que reutiliza resultados y otra que calcula desde cero, **Then** ataque, espera o vecina elegida y costo de acción son idénticos.
4. **AC-010 — Repetición determinista [FR-011, FR-015]**: **Given** la misma cripta, versiones de datos, semilla y secuencia de acciones, **When** se ejecutan dos partidas, **Then** producen la misma secuencia observable de decisiones, tiempos y desempates de cazadores.
5. **AC-011 — Retroceso [FR-016]**: **Given** una acción del jugador seguida por movimientos, esperas o ataques de cazadores hasta la siguiente decisión del jugador, **When** un pergamino revierte ese intervalo, **Then** se restauran salas, vida, reloj, próximas acciones y estado de puertas afectados; la unidad usada queda consumida y la cantidad de pergaminos permanece fuera de la reversión; al continuar desde el estado restaurado, cada cazador vuelve a decidir como un cálculo desde cero sobre ese estado.
6. **AC-016 — Puerta abierta entre turnos [FR-014]**: **Given** que una puerta cerrada se abre después de una decisión del cazador, **When** llega su siguiente turno, **Then** la nueva acción coincide con calcular desde cero usando la puerta abierta, sin exigir que se descarte información que no afecte esa decisión.
7. **AC-017 — Velocidad modificada entre turnos [FR-006, FR-014]**: **Given** que cambia la velocidad de un actor entre dos decisiones del cazador, **When** llega el siguiente turno del cazador, **Then** los eventos se reprograman conforme a FR-006 y la decisión coincide con calcular desde cero sobre el estado vigente, sin presuponer que el cambio altera la ruta si no cambia sus datos relevantes.
8. **AC-018 — Movimiento o muerte de otro actor [FR-014]**: **Given** que otro actor se mueve o muere entre dos decisiones del cazador, **When** llega el siguiente turno del cazador, **Then** la acción coincide con calcular desde cero sobre el estado vigente; la comprobación determina por el resultado observable si ese cambio afecta la decisión, sin tratar movimiento y muerte como invalidaciones idénticas por defecto.

---

### User Story 4 - Evidencia de escala y carga nueva (Priority: P2)

Como equipo evaluado, queremos medir la persecución y la agenda bajo la carga nueva, para demostrar que el resultado correcto también cumple los límites y conocer cuándo conviene reutilizar o compartir trabajo.

**Why this priority**: La corrección define el juego; la evidencia de rendimiento determina si funciona bajo las condiciones de evaluación y si las decisiones anteriores siguen siendo adecuadas.

**Independent Test**: Puede verificarse ejecutando `--bench` con escenarios deterministas que cubran todas las comparaciones exigidas, sin red ni renderizado, y revisando tanto resultados equivalentes como tiempos y cantidad de trabajo.

**Acceptance Scenarios**:

1. **AC-012 — Rango pequeño [PR-002]**: **Given** dos criptas con la misma región dentro del rango de un cazador y distinta cantidad de salas exclusivamente fuera de esa región, **When** `--bench` mide una decisión equivalente, **Then** el trabajo reportado para hallar la decisión no crece proporcionalmente al tamaño total añadido fuera del rango.
2. **AC-013 — Ciclo con decenas de cazadores [PR-001]**: **Given** la cripta de referencia con decenas de cazadores activos, **When** `--bench` mide cada ciclo completo entre dos decisiones del jugador sin red ni renderizado, **Then** el ciclo tarda menos de 20 ms bajo las condiciones oficiales de referencia.
3. **AC-014 — Matriz de comparaciones [PR-003, PR-004]**: **Given** escenarios sintéticos deterministas, **When** `--bench` ejecuta las mediciones de ruta e invalidación, **Then** informa por separado uno frente a muchos cazadores, rango pequeño frente a grande, trabajo individual frente a compartido, reutilización frente a recálculo siempre y puertas estables frente a inestables, comprobando equivalencia observable antes de comparar tiempos.
4. **AC-015 — Revisión de agenda [PR-005]**: **Given** las mediciones de agenda de la primera parte, cientos de eventos y una carga equivalente con costos variables y cazadores activos, **When** `--bench` mide insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates frente a una alternativa comparable, **Then** reporta cada operación por separado, resultados antes/después y si los límites y decisiones previos siguen siendo adecuados.

### Edge Cases

- El costo ausente equivale a 100. Un costo presente no entero o menor que 1, o costos contradictorios entre ambos sentidos, hacen que se rechace la cripta con un error que identifique la salida y los valores; no se convierten ni reemplazan silenciosamente.
- Una salida puede existir en un solo sentido. Solo cuando existen ambos sentidos se exige que sus costos efectivos coincidan; la ausencia del inverso no se rechaza ni crea una salida implícita.
- `d == rango` permite movimiento; solo `d > rango` obliga a esperar por rango.
- Un rango entero igual a 0 es válido; un rango ausente, negativo, booleano o no entero hace que se rechace la ficha con un error descriptivo, sin conversión ni valor predeterminado.
- Todo costo válido es positivo, por lo que una salida de costo 1 nunca produce un intervalo menor que 1.
- Una puerta cerrada no forma parte de una ruta, aunque el cazador esté junto a ella; el cazador no la abre.
- Si el cazador comparte sala con el jugador, atacar tiene prioridad incluso si no existiría una ruta de salida.
- Si varias rutas mínimas comparten la misma primera vecina, la decisión observable sigue siendo esa única vecina.
- Descargar o no el contenido de salas remotas no modifica la decisión del cazador.
- Los cambios de puertas, posición del jugador y velocidad entre turnos se evalúan con sus valores vigentes al decidir o reprogramar.
- Un ID de sala que no sea un entero se rechaza como dato inválido; no se convierte silenciosamente para desempatar.
- El retroceso restaura el estado reversible del intervalo, pero no restaura pergaminos recogidos o soltados dentro de él y deja consumida la unidad usada para retroceder.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 — Dominio del costo**: Cada salida DEBE tener un costo entero mayor o igual que 1; un booleano NO es un costo entero válido. Si el dato está ausente, el costo efectivo DEBE ser 100. Como política acordada ante datos inválidos —no como regla textual del PDF—, un costo presente booleano, no entero o menor que 1 DEBE causar el rechazo de la cripta con un error descriptivo que identifique la salida y el valor, sin convertirlo ni reemplazarlo silenciosamente.
- **FR-002 — Simetría del costo cuando existen ambos sentidos**: Si el esqueleto declara los dos sentidos entre un par de salas, sus costos efectivos DEBEN ser iguales. Una salida sin sentido inverso es válida: NO se rechaza y NO crea una conexión implícita. Como política acordada ante datos inválidos —no como regla textual del PDF—, costos contradictorios entre dos sentidos existentes DEBEN causar el rechazo de la cripta con un error descriptivo que identifique la salida y ambos valores, sin convertirlos ni reemplazarlos silenciosamente.
- **FR-003 — Tiempo de movimiento**: Para todo actor, moverse DEBE programar el siguiente turno con `max(1, costo_salida * 100 // velocidad)` a partir del reloj vigente.
- **FR-004 — Costos restantes**: Atacar, esperar, usar, equipar, recoger, soltar, abrir y cualquier otra acción distinta de movimiento DEBEN conservar sus costos anteriores.
- **FR-005 — Conductas existentes**: Los comportamientos anteriores de enemigos DEBEN conservar sus reglas de decisión; cuando se muevan, únicamente cambia el costo temporal según la salida atravesada.
- **FR-006 — Cambio de velocidad**: Si cambia la velocidad de un actor con una próxima acción ya programada, el tiempo restante DEBE reajustarse con la regla heredada `max(1, restante * velocidad_anterior // velocidad_nueva)` y toda reprogramación DEBE asignar un número de secuencia nuevo para conservar el desempate determinista.
- **FR-007 — Prioridad de ataque**: En su turno, un cazador que comparte sala con el jugador DEBE atacar antes de considerar cualquier movimiento o espera.
- **FR-008 — Espera del cazador**: Un cazador que no comparte sala con el jugador DEBE esperar con costo 100 cuando no exista ruta abierta o cuando el costo mínimo `d` sea mayor que su rango.
- **FR-009 — Ruta y rango**: El costo `d` DEBE ser la suma de costos de las salidas abiertas de una ruta de costo mínimo desde el cazador hasta la sala actual del jugador; `d == rango` DEBE considerarse dentro del rango. El rango DEBE ser un entero mayor o igual que 0 en unidades de costo. Como política acordada —no como exigencia textual del PDF—, un rango ausente, negativo, booleano o no entero DEBE causar el rechazo de la ficha con un error descriptivo que la identifique; NO se convierten cadenas ni se establece un valor predeterminado.
- **FR-010 — Movimiento del cazador**: Cuando exista una ruta mínima dentro del rango, el cazador DEBE moverse exactamente un paso por una ruta mínima.
- **FR-011 — Desempate estable**: Todo ID de sala DEBE ser un entero conforme al contrato heredado. Entre primeras vecinas que permitan completar una ruta de costo `d`, el cazador DEBE elegir la de menor ID por comparación numérica. Un valor de otro tipo DEBE rechazarse como dato inválido y NO DEBE convertirse silenciosamente.
- **FR-012 — Costo del paso**: El movimiento del cazador DEBE usar como costo de acción el costo de la única salida atravesada en ese turno.
- **FR-013 — Conocimiento del cazador**: La decisión DEBE usar el esqueleto completo, sus costos y el estado actual de todas las puertas; DEBE ser independiente de la niebla del jugador y de qué contenidos de sala estén descargados. Un cazador NO DEBE abrir puertas cerradas.
- **FR-014 — Equivalencia vigente**: Cada decisión del cazador DEBE ser observablemente idéntica a calcular desde cero en ese instante. Cualquier reutilización DEBE respetar aperturas y cierres de puertas, cambios de sala del jugador, cambios de velocidad y movimientos o muertes de otros actores cuando alteren ataque, espera, primera vecina o costo. La especificación NO presupone que todos esos cambios invaliden la misma información; solo exige igualdad observable con el cálculo desde cero.
- **FR-015 — Determinismo**: La misma cripta, versiones, semilla y acciones DEBEN producir las mismas decisiones, tiempos y desempates de cazadores, sin depender de hora real, latencia de red ni orden incidental de datos.
- **FR-016 — Retroceso completo**: Todo cambio causado por terreno o cazadores dentro de un intervalo reversible DEBE poder deshacerse sin copias completas por acción, restaurando exactamente el estado reversible previo y permitiendo que la continuación vuelva a ser determinista. Conforme a la excepción heredada, la unidad usada para retroceder DEBE quedar consumida y la cantidad de pergaminos —incluidos los recogidos o soltados durante el intervalo— DEBE permanecer fuera de la reversión.
- **FR-017 — Rechazos sin efectos parciales**: Cualquier movimiento rechazado DEBE conservar reloj, actor, puertas, próximas acciones e historial sin cambios parciales.
- **FR-018 — Compatibilidad**: Las reglas y resultados existentes no modificados expresamente por esta especificación DEBEN seguir siendo observables como antes, incluida la activación de enemigos y el orden por tiempo y secuencia.

### Performance Requirements

- **PR-001 — Presupuesto del ciclo**: `--bench` DEBE comprobar que, en el equipo local y sin red ni renderizado, cada ciclo de eventos entre decisiones del jugador tarda menos de 20 ms en la cripta oficial de referencia con decenas de cazadores activos. La composición exacta de esa referencia queda sujeta a la publicación o enmienda prevista por §6.1.
- **PR-002 — Trabajo acotado por rango**: `--bench` DEBE demostrar que, para rango pequeño, el trabajo de decidir depende de la región alcanzable dentro del rango y no crece proporcionalmente al tamaño total de la cripta cuando solo se agregan salas fuera de esa región.
- **PR-003 — Comparaciones obligatorias**: `--bench` DEBE comparar: un cazador frente a muchos; rango pequeño frente a grande; trabajo individual frente a compartido; reutilización frente a recálculo siempre; y puertas estables frente a inestables.
- **PR-004 — Medición válida**: Cada comparación de `--bench` DEBE verificar primero igualdad de decisiones, usar escenarios deterministas por semilla, excluir preparación, red y renderizado del intervalo cronometrado, e informar calentamiento, repeticiones, carga, unidad y resultados.
- **PR-005 — Agenda bajo carga nueva**: `--bench` DEBE repetir las mediciones de agenda de la primera parte con cientos de eventos, costos variables y cazadores activos. DEBE medir por separado insertar, extraer, cancelar por ID, cancelar por actor, reprogramar y resolver empates frente a una alternativa comparable, conservar una base común y reportar antes/después aunque la decisión previa no cambie.
- **PR-006 — Cobertura de corrección medida**: Los escenarios de `--bench` DEBEN informar cualquier divergencia respecto del cálculo desde cero como fallo de corrección, no como mejora de tiempo.

### Key Entities

- **Salida**: Conexión transitable entre dos salas; tiene costo efectivo simétrico y un estado actual que determina si puede usarse.
- **Sala**: Lugar del esqueleto identificado exclusivamente por un entero; sus IDs se comparan numéricamente y no admiten conversiones silenciosas.
- **Actor**: Participante con sala, velocidad y próxima acción; incluye al jugador y a los distintos enemigos.
- **Cazador**: Enemigo con rango entero mayor o igual que 0 expresado en unidades de costo y una decisión ordenada entre atacar, esperar o moverse un paso; su ficha es inválida si el rango falta o no pertenece a ese dominio.
- **Decisión de cazador**: Resultado observable en un turno: tipo de acción, primera vecina cuando corresponda y costo temporal.
- **Estado de persecución**: Esqueleto completo, costos, puertas actuales, sala del jugador y sala del cazador relevantes en el instante de decidir.
- **Intervalo reversible**: Acción del jugador y eventos posteriores hasta su próxima decisión, cuyos cambios deben restaurarse juntos al usar retroceso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los siete casos de terreno y cazador del Apéndice B produce el resultado definido y queda enlazado a requisitos estables.
- **SC-002**: El 100 % de los escenarios de ataque prioritario, `d == rango`, independencia del contenido descargado y retroceso produce los resultados descritos en AC-004, AC-005, AC-007 y AC-011.
- **SC-003**: Para todos los escenarios de validación, una decisión con reutilización y la decisión desde cero coinciden en acción, primera vecina y costo.
- **SC-004**: Dos ejecuciones con iguales datos, versiones, semilla y acciones producen registros observables idénticos para terreno y cazadores.
- **SC-005**: En la carga oficial de referencia, se observan cero ciclos de eventos de 20 ms o más entre decisiones del jugador, medidos sin red ni renderizado.
- **SC-006**: Al ampliar una cripta únicamente con salas fuera del rango pequeño, la cantidad de salas y salidas consideradas para la decisión no crece proporcionalmente con la ampliación total.
- **SC-007**: El informe de `--bench` contiene el 100 % de las comparaciones de PR-003 y las seis operaciones de agenda de PR-005 con cientos de eventos y una alternativa comparable, con equivalencia de resultados comprobada.
- **SC-008**: Tras deshacer un intervalo con acciones de cazadores, el estado reversible coincide exactamente con el estado anterior, respetando la excepción de pergaminos de FR-016: la unidad usada queda consumida y la cantidad de pergaminos permanece fuera de la reversión. Partiendo del mismo estado posterior al retroceso, dos continuaciones con las mismas acciones posteriores producen la misma secuencia observable.

## Assumptions

- Todo lo establecido en la Parte I continúa vigente salvo modificación expresa de la Parte II; en particular, se heredan la fórmula de cambio de velocidad, la activación de enemigos, el combate, el orden temporal y los costos de acciones no modificadas.
- El esqueleto completo, los costos de salida y las fichas vigentes se obtienen de la fuente de datos compatible; no se codifican valores propios de una cripta.
- La versión de la cripta y la versión del catálogo determinan la vigencia de costos y datos del cazador.
- La niebla de guerra, el viaje automático, la resolubilidad, la línea de tiempo, la presentación visual y sus mediciones propias están fuera de esta especificación, salvo las dependencias explícitas necesarias para conocimiento del cazador, retroceso y repetición de agenda.
- La selección de mecanismos internos, estructuras, componentes y alternativas concretas pertenece a `plan.md`, no a esta especificación.

## Normative Source and Clarification Boundaries

**Explicit in the official PDF**:

- Reglas de costo, movimiento y cazador: Parte II §3.1–§3.2.
- Propiedades de escala y vigencia de decisiones: §5.1–§5.2.
- Repetición de mediciones de decisiones anteriores: §5.6.
- Límite y modo de medición: §6.1–§6.3.
- Los siete resultados AC-B01 a AC-B07: Apéndice B.
- La fórmula exacta de reajuste de velocidad se hereda de Parte I §2.3, referida expresamente por AC-B07.
- Parte I §2.3 establece que toda reprogramación asigna un número de secuencia nuevo.
- El contrato heredado publica y valida los IDs de sala como enteros; el desempate de §3.2 es, por tanto, numérico.
- Parte I §2.11 excluye la cantidad de pergaminos del estado reversible y deja consumida la unidad usada para retroceder.

**Agreed policy beyond the PDF's explicit text**:

- Los costos presentes inválidos o contradictorios entre dos sentidos existentes hacen que se rechace la cripta con un error descriptivo, sin conversión ni reemplazo silencioso; solo la ausencia del campo conserva el valor predeterminado 100. Una salida sin inversa es válida y no crea otro sentido (FR-001, FR-002; aclaraciones del 2026-11-07 y 2026-11-09).
- El rango admite enteros mayores o iguales que 0; un valor ausente, negativo, booleano o no entero hace que se rechace la ficha con un error descriptivo, sin conversión de cadenas ni valor predeterminado (FR-009; aclaración del 2026-11-07).

La carga exacta de la cripta oficial de referencia no se inventa: PR-001 se aplicará a la publicación o enmienda indicada por §6.1.
