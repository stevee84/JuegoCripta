# Feature Specification: Línea de tiempo y puntos de control

**Feature Branch**: `joshua` (spec-kit 1.2.3 no crea rama; la especificación vive en la rama del integrante responsable)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Línea de tiempo y puntos de control de Cripta (enunciado de la Parte II, §3.6, §5.5, §6.1, §7.3 y Apéndice B): consultar sin modificar la partida el estado en cualquier instante pasado t o antes de la acción #k, con puntos de control como máximo cada K acciones (--checkpoint-cada K), reproducción sin vista con --replay partida.log --hasta t, recorte de la línea al usar un pergamino, persistencia en el guardado y mediciones en --bench. Texto completo registrado como Prompt 28 en PROMPTS_LLM.md."

## Conceptos

- **Acción del jugador**: una decisión del jugador aceptada por el juego (mover, atacar, abrir, recoger, soltar, usar, equipar, esperar, usar un pergamino). Las acciones rechazadas no son acciones de la línea de tiempo.
- **Instante t**: un valor del reloj virtual de la partida, entero mayor o igual que 0.
- **Estado en el instante t**: el estado después de ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla.
- **Estado antes de la acción #k**: el estado justo antes de que el jugador tome su acción número k, contando desde 1 las acciones que siguen en la línea de tiempo. #1 es el estado inicial de la partida.
- **Línea de tiempo**: la historia de la partida tal como quedó, desde el instante 0 hasta el reloj actual. Las acciones revertidas con un pergamino no forman parte de ella.
- **Punto de control**: una copia completa del estado de la partida tomada en un momento de la línea de tiempo.
- **K**: la cantidad máxima de acciones del jugador entre dos puntos de control consecutivos.
- **Resumen de estado**: lo que muestra una consulta de la línea de tiempo (FR-004).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el estado en un instante pasado (Priority: P1)

Durante la partida, el jugador escribe `historia <t>` para ver cómo estaba la partida en el instante t: dónde estaba, cuánta vida tenía, qué llevaba y qué enemigos había en su sala. La partida sigue exactamente igual después de la consulta.

**Why this priority**: es la capacidad central de la línea de tiempo (§3.6) y la que fija el límite de rendimiento de §6.1.

**Independent Test**: jugar una partida corta con eventos conocidos, consultar varios instantes y comparar cada resumen con el estado que se observó en ese instante al jugar.

**Acceptance Scenarios**:

1. **Given** una partida con reloj actual 1 200, **When** el jugador consulta `historia 1500`, **Then** la consulta se rechaza con un mensaje que indica que el instante es posterior al reloj actual, y la partida no cambia. *(Apéndice B)*
2. **Given** una partida donde en el instante 400 ocurren varios eventos (por ejemplo, un ataque enemigo y el vencimiento de un efecto), **When** el jugador consulta `historia 400`, **Then** el resumen muestra el estado después de todos los eventos de ese instante. *(Apéndice B)*
3. **Given** una partida en curso, **When** el jugador consulta `historia <t>` con cualquier t válido, **Then** el reloj virtual no avanza, partida.log no recibe ningún registro nuevo, el historial del pergamino de retroceso queda igual y la siguiente acción del jugador produce el mismo resultado que sin la consulta. *(Apéndice B)*
4. **Given** una partida en la que a t le corresponde una decisión del jugador, **When** el jugador consulta `historia <t>`, **Then** el resumen muestra el estado justo antes de esa decisión.
5. **Given** una partida en curso, **When** el jugador consulta `historia 0`, **Then** el resumen muestra el estado inicial de la partida.
6. **Given** una partida en curso, **When** el jugador consulta `historia` con un instante que no es un entero mayor o igual que 0, **Then** la consulta se rechaza con un mensaje y sin efectos.

---

### User Story 2 - Consultar el estado antes de la acción número k (Priority: P1)

El jugador escribe `historia #k` para ver el estado justo antes de su acción número k, sin tener que conocer el instante exacto.

**Why this priority**: es la otra forma de consulta que exige §3.6 y la que usan las pruebas de rendimiento con miles de acciones.

**Independent Test**: jugar una secuencia de acciones conocida, consultar `#1`, una `#k` intermedia y la última, y comparar con los estados observados antes de cada acción.

**Acceptance Scenarios**:

1. **Given** una partida con al menos una acción, **When** el jugador consulta `historia #1`, **Then** el resumen muestra el estado inicial de la partida.
2. **Given** una partida con n acciones del jugador en la línea de tiempo, **When** el jugador consulta `historia #(n+1)`, **Then** el resumen muestra el estado actual, en el que el jugador está por decidir.
3. **Given** una partida con n acciones, **When** el jugador consulta `historia #0` o `historia #(n+2)`, **Then** la consulta se rechaza con un mensaje que indica el rango válido, sin efectos.
4. **Given** una partida con miles de acciones, **When** el jugador consulta cualquier `historia #k`, **Then** el resumen coincide con el estado que tenía la partida justo antes de la acción k.

---

### User Story 3 - La línea se recorta al usar un pergamino (Priority: P2)

El jugador usa un pergamino de retroceso. Las acciones revertidas desaparecen de la línea de tiempo, como si nunca hubieran ocurrido.

**Why this priority**: sin esta regla la línea de tiempo describiría una partida que ya no existe (§3.6).

**Independent Test**: jugar acciones, usar un pergamino y comprobar que ninguna consulta muestra estados de las acciones revertidas.

**Acceptance Scenarios**:

1. **Given** una partida donde el jugador hizo acciones y luego usó un pergamino que revirtió la última, **When** el jugador consulta la línea de tiempo, **Then** ninguna consulta muestra el estado producido por la acción revertida. *(Apéndice B)*
2. **Given** una partida con reloj 900 en la que un pergamino revierte una acción y el reloj vuelve a 700, **When** el jugador consulta `historia 800`, **Then** la consulta se rechaza porque 800 es posterior al reloj actual.
3. **Given** una partida con n acciones en la que un pergamino revierte la última, **When** el jugador consulta `historia #n`, **Then** se muestra el estado actual (la línea ahora tiene n−1 acciones), con el pergamino ya consumido; y `historia #(n+1)` se rechaza por fuera de rango.
4. **Given** una partida larga, **When** el jugador usa un pergamino, **Then** el recorte de la línea de tiempo no depende de la longitud total de la partida (FR-013).

---

### User Story 4 - Reproducir una partida hasta un instante sin vista (Priority: P2)

Quien revisa el proyecto ejecuta `--replay partida.log --hasta <t>` y obtiene el resumen del estado en t, sin abrir la interfaz.

**Why this priority**: permite verificar la línea de tiempo de forma automática y reproducible (§3.6, constitución IV).

**Independent Test**: con un partida.log conocido, ejecutar el replay hasta varios instantes y comparar con `historia <t>` en la partida original.

**Acceptance Scenarios**:

1. **Given** un partida.log válido, **When** se ejecuta `--replay partida.log --hasta t` con t dentro de la partida, **Then** se imprime el mismo resumen que mostraría `historia t` en esa partida, sin instanciar la vista.
2. **Given** un partida.log de una partida que terminó en el instante 3 000, **When** se ejecuta `--replay partida.log --hasta 5000`, **Then** se imprime el estado final e indica que la partida terminó antes del instante pedido. *(Apéndice B)*
3. **Given** un partida.log válido, **When** se ejecuta `--replay partida.log` sin `--hasta`, **Then** el comportamiento es el mismo de la Parte I.
4. **Given** un partida.log con versión de cripta o catálogo incompatible, **When** se ejecuta `--replay partida.log --hasta t`, **Then** se rechaza igual que en la Parte I.

---

### User Story 5 - Guardar y cargar sin perder la línea de tiempo (Priority: P3)

El jugador guarda la partida y la carga más tarde. Puede seguir consultando cualquier instante desde el inicio.

**Why this priority**: lo exige §3.6 (persistencia), pero depende de que las consultas ya funcionen.

**Independent Test**: jugar, consultar varios instantes, guardar, cargar y repetir las mismas consultas.

**Acceptance Scenarios**:

1. **Given** una partida con línea de tiempo, **When** el jugador guarda, carga y consulta `historia <t>` o `historia #k`, **Then** cada resumen coincide con el que se obtenía antes de guardar.
2. **Given** una partida guardada con `--checkpoint-cada 50`, **When** se carga con `--checkpoint-cada 100`, **Then** se conserva K = 50, se informa que se ignora el valor pedido y las consultas dan el mismo resultado que antes de guardar.
3. **Given** un archivo de partida guardado por la Parte I, **When** el jugador intenta cargarlo, **Then** el juego informa que el formato es incompatible o lo migra de forma explícita y lo informa; nunca lo carga en silencio. *(Apéndice B)*

---

### User Story 6 - Ajustar la frecuencia de puntos de control (Priority: P3)

El desarrollador inicia el juego, el replay o el modo de medición con `--checkpoint-cada K` para elegir cada cuántas acciones del jugador se toma un punto de control, y mide su efecto en memoria y tiempo.

**Why this priority**: es el parámetro que el grupo debe justificar con mediciones (§5.5), pero el juego funciona con el valor por defecto.

**Independent Test**: ejecutar la misma partida con varios valores de K y comprobar que las consultas dan el mismo resultado con todos.

**Acceptance Scenarios**:

1. **Given** el juego iniciado con `--checkpoint-cada 1`, **When** el jugador consulta cualquier instante, **Then** el resultado es el mismo que con el K por defecto.
2. **Given** el juego iniciado con `--checkpoint-cada 0`, `-3` o un valor no entero, **When** arranca, **Then** se rechaza el valor con un mensaje y no se inicia.
3. **Given** dos ejecuciones de la misma partida con K distintos, **When** se consultan los mismos instantes, **Then** los resúmenes son idénticos.

---

### Edge Cases

- Consulta en el instante 0 o antes de la primera acción: muestra el estado inicial.
- Consulta exactamente en el reloj actual: muestra el estado actual.
- Varios eventos con el mismo tiempo: el resumen refleja todos, respetando el desempate por secuencia de la agenda.
- Instante entre dos eventos: muestra el estado después del último evento con tiempo menor o igual que t.
- K = 1 (un punto de control por acción) y K mayor que la cantidad de acciones de la partida (solo el punto de control inicial).
- Varios pergaminos seguidos: cada uno recorta la línea de tiempo.
- Partida terminada por victoria o muerte: la línea de tiempo se sigue pudiendo consultar (ver Assumptions).
- Acción que produce muchos cambios (por ejemplo, una con muchos eventos entre dos decisiones): cuenta como una sola acción para K.
- Consulta sin partida iniciada: se rechaza.

## Requirements *(mandatory)*

### Functional Requirements

**Consulta de la línea de tiempo**

- **FR-001**: El juego MUST permitir consultar `historia <t>`, que muestra el estado después de ejecutar todos los eventos con tiempo menor o igual que t; si a t le corresponde una decisión del jugador, el estado justo antes de tomarla.
- **FR-002**: Cuando varios eventos ocurren en el mismo instante t, `historia <t>` MUST mostrar el estado después de todos ellos.
- **FR-003**: El juego MUST permitir consultar `historia #k`, que muestra el estado justo antes de la acción número k del jugador. La numeración empieza en 1, cuenta solo las acciones aceptadas que siguen en la línea de tiempo, y #(n+1), con n la cantidad de acciones, es el estado actual.
- **FR-004**: El resumen de una consulta MUST mostrar como mínimo: reloj, sala del jugador, vida y estadísticas del jugador, inventario, efectos activos, enemigos de la sala del jugador con su vida, y el mapa conocido por el jugador en ese momento.
- **FR-005**: Una consulta MUST NOT consumir tiempo virtual, contar como acción del jugador, registrarse en partida.log ni alterar el estado del juego, el historial del pergamino de retroceso o el estado del generador aleatorio.
- **FR-006**: El juego MUST rechazar con un mensaje, y sin efectos, `historia <t>` con t mayor que el reloj actual.
- **FR-007**: El juego MUST rechazar con un mensaje, y sin efectos, un t que no sea un entero mayor o igual que 0, un #k fuera del rango 1..n+1 y cualquier consulta sin partida iniciada.
- **FR-008**: La interfaz MUST ofrecer los comandos `historia <t>` e `historia #k` y mostrar el resumen de FR-004 (§7.3).

**Reproducción sin interacción**

- **FR-009**: `--replay partida.log --hasta <t>` MUST reproducir la partida hasta el instante t e imprimir el mismo resumen de FR-004, sin instanciar la vista.
- **FR-010**: Si t es posterior al final de la partida registrada, `--replay … --hasta t` MUST imprimir el estado final e indicar que la partida terminó antes del instante pedido.
- **FR-011**: Sin `--hasta`, `--replay` MUST comportarse como en la Parte I, incluido el rechazo de logs con versiones incompatibles.

**Interacción con el pergamino de retroceso**

- **FR-012**: Las acciones revertidas con un pergamino MUST dejar de existir en la línea de tiempo: ninguna consulta posterior muestra estados producidos por ellas. El uso del pergamino no cuenta como acción #k: después de usarlo, la cantidad de acciones de la línea de tiempo baja en la cantidad de acciones revertidas. El consumo del pergamino sí forma parte de la historia tal como quedó: las consultas del instante al que vuelve el reloj, o posteriores, muestran el pergamino ya consumido; las anteriores, cuando el jugador todavía lo tenía, lo muestran en el inventario.
- **FR-013**: El recorte de la línea de tiempo al usar un pergamino MUST costar en proporción a las acciones revertidas (como máximo 5), no a la longitud total de la partida.
- **FR-014**: El pergamino de retroceso MUST seguir limitado a 5 acciones; la línea de tiempo no cambia ese límite.

**Puntos de control y reconstrucción**

- **FR-015**: El juego MUST aceptar `--checkpoint-cada K`, con K entero mayor o igual que 1, en la partida interactiva, en `--replay` y en `--bench`; cualquier otro valor se rechaza al arrancar con un mensaje.
- **FR-016**: Sin `--checkpoint-cada`, el juego MUST usar un K por defecto, elegido por el grupo y justificado con las mediciones de FR-024.
- **FR-017**: El juego MUST guardar como máximo un punto de control cada K acciones del jugador. Fuera de los puntos de control, MUST almacenar solo la información necesaria para reconstruir los cambios.
- **FR-018**: Responder cualquier consulta MUST requerir aplicar o deshacer cambios de, como máximo, K acciones del jugador.
- **FR-019**: Ubicar el punto de control más cercano al instante o a la acción pedidos MUST costar menos que recorrer todos los puntos de control de la partida.
- **FR-020**: Si la reconstrucción re-simula hacia adelante desde un punto de control, ese punto de control MUST incluir el estado del generador aleatorio, y la re-simulación MUST producir exactamente el mismo estado que la partida original.
- **FR-021**: La memoria usada por la línea de tiempo MUST crecer con la cantidad de cambios ocurridos más un punto de control cada K acciones, y nunca con «acciones por tamaño del estado».
- **FR-022**: La línea de tiempo MUST reconstruir todo el estado de la partida, incluido el que agregan otras capacidades: costos de salidas y cazadores (spec 001) y conocimiento del jugador y mapa conocido (spec 003).
- **FR-023**: El resultado de cualquier consulta MUST ser el mismo para cualquier valor válido de K.

**Medición**

- **FR-024**: `--bench` MUST medir memoria y tiempo de consulta de la línea de tiempo con al menos tres valores de K y con la alternativa sin puntos de control, en partidas sintéticas deterministas por semilla, y comparar la reconstrucción hacia adelante con la reconstrucción hacia atrás.
- **FR-025**: `--bench` MUST medir un uso del pergamino de retroceso de punta a punta (reloj, agenda, rastro, puertas, trampas e inventario) frente a la alternativa de copia completa del estado, con la carga nueva de la Parte II (§5.6).
- **FR-026**: `--bench` MUST medir una reproducción completa de partida.log y el rechazo de un log con versión incompatible (§5.6).
- **FR-027**: `--bench` MUST medir la vista ordenada del inventario por peso, valor y nombre sin alterar el orden real del inventario, y el rechazo de recoger al llegar al máximo de inventario (§5.6).

**Persistencia**

- **FR-028**: Guardar y cargar la partida MUST conservar la línea de tiempo completa: después de cargar, toda consulta da el mismo resultado que antes de guardar.
- **FR-029**: Como contrato con el guardado de partida, sin fijar su formato, el archivo MUST conservar: los puntos de control, la información de cambios necesaria para reconstruir cualquier instante desde el inicio, el valor de K con que se tomaron, el número de acción y el reloj de cada punto de control, y el estado del generador aleatorio si la reconstrucción re-simula.
- **FR-030**: Al cargar una partida guardada con un K distinto del configurado con `--checkpoint-cada`, el juego MUST conservar el K con que se guardó la partida, usarlo también en las acciones posteriores e informar al jugador que se ignora el valor pedido.
- **FR-031**: Un archivo de partida de la Parte I MUST reportarse como incompatible o migrarse de forma explícita, informándolo; nunca se carga en silencio.

### Key Entities

- **Acción del jugador en la línea de tiempo**: número de acción, instante en que se tomó y los cambios de estado que produjo, incluidos los eventos hasta la siguiente decisión.
- **Punto de control**: copia completa del estado en un momento de la línea, con su número de acción, su reloj y, si hace falta, el estado del generador aleatorio.
- **Resumen de estado**: el contenido de FR-004 para un instante o una acción.
- **Consulta**: un instante t o un número de acción #k, más su resultado o su motivo de rechazo.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `historia <t>` e `historia #k` responden en menos de 50 ms en una partida de al menos 5 000 acciones del jugador con el K por defecto, medido en el equipo local sin red ni renderizado (§6.1).
- **SC-002**: En el 100 % de las consultas de las pruebas, el resumen coincide con el estado que tenía la partida en ese instante o antes de esa acción.
- **SC-003**: Después de cualquier cantidad de consultas, la partida continúa de forma idéntica a una partida sin consultas: mismo partida.log, mismo reloj y mismos resultados.
- **SC-004**: `--bench` reporta memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control, y con esos datos se justifica el K por defecto en el Documento de Decisiones.
- **SC-005**: En `--bench`, al duplicar la cantidad de acciones con K fijo, la memoria de la línea de tiempo crece en proporción a los cambios registrados, no a «acciones por tamaño del estado».
- **SC-006**: Los 6 casos de línea de tiempo del Apéndice B (US1-1, US1-2, US1-3, US3-1, US4-2 y US5-3) tienen una prueba automatizada o un partida.log que los ejercita, y cada prueba cita su FR.

## Assumptions

- El K por defecto se fija en el plan con las mediciones de FR-024; esta especificación no lo fija.
- La línea de tiempo se puede consultar con la partida terminada (victoria o muerte), porque consultar no modifica la partida.
- El resumen de `--replay --hasta` es el mismo contenido que el de `historia`, impreso como texto.
- Una acción del jugador incluye todos los eventos del reloj hasta su siguiente decisión, igual que el pergamino de retroceso de la Parte I.
- El instante t se interpreta en las mismas unidades del reloj virtual que el resto del juego.
- Dependencias: la spec 001 (Sofía) y la spec 003 (Steven) deben registrar sus cambios de estado de forma reversible para que FR-022 se pueda cumplir; el guardado de partida (Steven) debe incluir lo que pide FR-029.
- Fuera de alcance: cambiar el límite de 5 acciones del pergamino y usar la línea de tiempo para volver a jugar desde un instante pasado.
