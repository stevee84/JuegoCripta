# Especificación: Niebla de guerra y viaje automático «ir a»

**Directorio de la especificación**: `specs/003-niebla-y-ir-a`

**Creada**: 2026-11-11

**Estado**: Borrador

**Entrada**: Descripción del usuario: "Niebla de guerra y viaje automático «ir a». Que el jugador
deje de ver lo que no ha descubierto, y que pueda pedir que lo lleven automáticamente a una sala
que ya conoce."

## Clarifications

### Session 2026-11-11

- Q: Si el jugador ya está en una sala con enemigos cuando pide el viaje, ¿el viaje empieza? → A:
  Sí. §3.4 detiene el viaje cuando el jugador **entra** a una sala con enemigos, y quien ya está
  allí no entra. Además, pedir irse de una sala con un enemigo al lado es justo lo razonable:
  bloquearlo sería impedirle moverse cuando más lo necesita.
- Q: ¿El daño que llega entre dos pasos, sin que el jugador se mueva —un pulso de veneno, el
  ataque de un enemigo que lo alcanzó—, detiene el viaje? → A: Sí. La regla existe para devolverle
  el control cuando algo le pasa, y da igual si el daño llegó al moverse o estando quieto.

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — El jugador solo ve lo que ha descubierto (Prioridad: P1)

Hasta ahora el jugador veía la cripta entera desde el primer instante. A partir de aquí solo
conoce las salas en las que ha estado, intuye que hay algo detrás de las salidas que ha visto, y
no sabe nada del resto. Explorar deja de ser un trámite y pasa a ser el juego.

**Por qué esta prioridad**: es el fundamento. Sin un mapa propio del jugador no hay nada que
mostrar ni sobre lo que viajar, así que las demás historias se apoyan en esta.

**Prueba independiente**: se empieza una partida, se consulta lo que el jugador conoce y solo
aparece la sala inicial y lo que hay justo detrás de sus salidas; tras moverse a una vecina, esa
pasa a conocerse por completo.

**Escenarios de aceptación**:

1. **Dado** una partida recién empezada, **cuando** el jugador consulta su mapa, **entonces** la
   sala inicial figura como explorada y las salas que están detrás de sus salidas figuran como
   avistadas.
2. **Dado** una sala avistada, **cuando** el jugador entra en ella, **entonces** pasa a estar
   explorada y se conocen su nombre, sus salidas y el costo de cada una.
3. **Dado** una sala que no es la inicial ni destino de ninguna salida de una sala explorada,
   **cuando** el jugador consulta su mapa, **entonces** esa sala no aparece de ninguna forma.
4. **Dado** una sala avistada, **cuando** el jugador consulta su mapa, **entonces** lo único que
   sabe de ella es que existe: ni su nombre, ni sus salidas, ni su contenido.
5. **Dado** que el jugador estuvo en una sala y observó una puerta abierta, **cuando** esa puerta
   se cierra sola mientras él está en otra parte, **entonces** su mapa la sigue mostrando abierta,
   porque así fue su última observación.
6. **Dado** que el jugador vuelve a una sala que ya había explorado, **cuando** observa de nuevo
   sus puertas, **entonces** su mapa se actualiza con el estado que ve en ese momento.

---

### Historia 2 — Viajar automáticamente a una sala ya explorada (Prioridad: P1)

Volver sobre los propios pasos sala por sala es tedioso. El jugador pide ir a una sala que ya
exploró y el programa lo lleva, paso a paso, por el camino más barato que él mismo conoce.

**Por qué esta prioridad**: es la otra mitad de la capacidad y lo que §7.3 exige en la interfaz
mínima. Depende de la Historia 1, porque viaja sobre el conocimiento del jugador.

**Prueba independiente**: se explora un recorrido, se pide ir a una sala ya visitada y el jugador
llega por una secuencia de movimientos ordinarios, sin que el viaje use nada que el jugador no
conozca.

**Escenarios de aceptación**:

1. **Dado** una sala que el jugador ya exploró, **cuando** pide ir a ella, **entonces** se desplaza
   hasta allí mediante movimientos ordinarios, uno por paso.
2. **Dado** un viaje en curso, **cuando** se ejecuta cada paso, **entonces** ese paso consume
   tiempo según el costo de la salida y entre paso y paso ocurren los eventos del reloj con
   normalidad.
3. **Dado** una sala avistada pero no explorada, **cuando** el jugador pide ir a ella, **entonces**
   no se acepta como destino y se le dice por qué.
4. **Dado** dos caminos conocidos hasta el destino con el mismo costo total, **cuando** se calcula
   el viaje, **entonces** se elige el que da el primer paso hacia la sala de menor identificador, y
   dos ejecuciones iguales producen el mismo recorrido.
5. **Dado** una puerta cerrada en el camino y el jugador con la llave que la abre, **cuando**
   viaja, **entonces** el viaje no la abre: solo se mueve.
6. **Dado** que el jugador pide ir a la sala en la que ya está, **entonces** el viaje termina de
   inmediato sin consumir ningún paso ni tiempo.

---

### Historia 3 — Entender por qué se detuvo el viaje (Prioridad: P2)

Un viaje automático que se interrumpe sin explicación deja al jugador sin saber qué pasó ni dónde
quedó. Cada parada tiene un motivo y el jugador tiene que poder verlo.

**Por qué esta prioridad**: §7.3 lo pide expresamente —«ejecutar ir a y ver por qué se detuvo un
viaje»— y es lo que separa una función útil de una que desconcierta.

**Prueba independiente**: se provoca cada una de las condiciones de parada y se comprueba que el
viaje se detiene y que el motivo que se informa es el correcto.

**Escenarios de aceptación**:

1. **Dado** un viaje en curso, **cuando** el jugador llega al destino, **entonces** el viaje
   termina e informa que llegó.
2. **Dado** un viaje en curso, **cuando** el jugador entra a una sala que contiene enemigos, aunque
   estén dormidos, **entonces** el viaje se detiene allí e informa el motivo.
3. **Dado** un viaje en curso, **cuando** el jugador recibe daño, **entonces** el viaje se detiene
   e informa el motivo.
4. **Dado** un viaje en curso, **cuando** deja de existir un camino conocido hasta el destino,
   **entonces** el viaje se detiene e informa que ya no hay ruta.
5. **Dado** que el mapa del jugador recordaba abierta una puerta del camino que en realidad se
   cerró sola, **cuando** el jugador llega a la sala desde la que se observa, **entonces** su mapa
   se corrige y el siguiente cálculo busca otro camino, sin detener el viaje por eso.
6. **Dado** un viaje que se detuvo, **cuando** el jugador consulta qué pasó, **entonces** puede ver
   el motivo y en qué sala quedó.
7. **Dado** que el jugador ya está en una sala con enemigos, **cuando** pide ir a otra sala,
   **entonces** el viaje empieza igual: la parada se dispara al entrar a una sala con enemigos, y
   él no está entrando.
8. **Dado** un viaje en curso, **cuando** el jugador recibe daño entre dos pasos sin haberse
   movido, por un efecto o por un ataque que lo alcanzó, **entonces** el viaje se detiene igual que
   si el daño hubiera llegado al moverse.

---

### Historia 4 — El conocimiento es parte de la partida (Prioridad: P2)

Lo que el jugador ha descubierto no es un adorno de la pantalla: es parte de su partida. Tiene que
deshacerse con el pergamino, guardarse con el resto y poder reconstruirse al consultar un instante
pasado.

**Por qué esta prioridad**: sin esto, retroceder o reanudar dejaría al jugador con un mapa que no
corresponde al momento en que está, que es peor que no tener mapa.

**Prueba independiente**: se explora, se guarda, se reanuda y el mapa conocido es el mismo; se
retrocede un paso y el mapa vuelve a ser el de antes de ese paso.

**Escenarios de aceptación**:

1. **Dado** un viaje en curso, **cuando** el jugador usa el pergamino de retroceso, **entonces** se
   revierte únicamente el último paso, porque cada paso es una acción suya por separado.
2. **Dado** que el último paso reveló salas nuevas, **cuando** se retrocede ese paso, **entonces**
   el mapa conocido vuelve exactamente al estado anterior, sin esas salas.
3. **Dado** una partida con parte de la cripta explorada, **cuando** se guarda, se cierra el
   programa y se reanuda, **entonces** el mapa conocido es el mismo que antes de guardar.
4. **Dado** una partida en curso, **cuando** se consulta el estado en un instante pasado,
   **entonces** el mapa conocido que se muestra es el que el jugador tenía en ese instante, no el
   actual.

---

### Historia 5 — La antorcha ilumina lo que hay alrededor (Prioridad: P3)

Con la antorcha encendida, entrar a una sala revela también lo que la rodea, sin tener que pisarlo.
Da una ventaja real a quien la lleva encendida y le da sentido a cargarla.

**Por qué esta prioridad**: mejora la exploración pero el juego funciona sin ella, y depende de que
las Historias 1 y 2 estén en pie.

**Prueba independiente**: se entra a una sala con la antorcha encendida y las vecinas quedan
exploradas; se repite con la antorcha apagada y solo quedan avistadas.

**Escenarios de aceptación**:

1. **Dado** la antorcha encendida, **cuando** el jugador entra a una sala, **entonces** todas sus
   vecinas quedan exploradas, por cualquier salida, esté abierta o cerrada.
2. **Dado** una vecina explorada por la antorcha, **cuando** el jugador consulta su mapa,
   **entonces** conoce su nombre y sus salidas, pero no su contenido.
3. **Dado** una vecina con enemigos o trampas explorada por la antorcha, **cuando** se revela,
   **entonces** no se activa ninguno de ellos.
4. **Dado** la antorcha apagada, **cuando** el jugador entra a una sala, **entonces** sus vecinas
   quedan solo avistadas.
5. **Dado** una sala explorada gracias a la antorcha, **cuando** el jugador pide ir a ella,
   **entonces** es un destino válido como cualquier otra sala explorada.

### Casos límite

- **El jugador pide ir a una sala desconocida o inexistente**: no se acepta como destino, con el
  mismo trato que una sala avistada.
- **El jugador pide ir a una sala explorada que ya no es alcanzable con lo que conoce**: el viaje
  no empieza, o se detiene en cuanto se agota el camino, informando que no hay ruta.
- **El jugador ya está en una sala con enemigos y pide un viaje**: el viaje empieza igual; la parada se dispara al entrar a una sala con enemigos (FR-017).
- **El daño llega entre dos pasos** sin que el jugador se mueva, por un efecto o un ataque: detiene el viaje igual (FR-018).
- **Dos salidas de la misma sala llevan a la misma vecina**: no cambia nada; el destino se conoce
  igual y el viaje elige la más barata.
- **Una sala avistada se vuelve explorada**: deja de ser avistada; los dos estados se excluyen.
- **La antorcha se apaga a mitad de un viaje**: los pasos siguientes ya no revelan vecinas, y lo
  revelado antes se conserva.
- **El jugador retrocede un paso que no reveló nada**: el mapa conocido queda igual, sin error.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El programa DEBE mantener, por cada sala de la cripta y desde el punto de vista del
  jugador, uno de tres estados: explorada, avistada o desconocida.
- **FR-002**: Una sala está **explorada** cuando el jugador entró en ella al menos una vez. De una
  sala explorada el jugador conoce su nombre, sus salidas, el costo de cada salida y el estado de
  sus puertas en el momento de su última observación.
- **FR-003**: Una sala está **avistada** cuando no está explorada pero es el destino de una salida
  de una sala explorada. De una sala avistada el jugador solo sabe que existe.
- **FR-004**: Una sala está **desconocida** cuando no es ninguna de las anteriores, y el jugador no
  sabe nada de ella.
- **FR-005**: La sala inicial DEBE estar explorada desde el instante cero de la partida.
- **FR-006**: El jugador observa una puerta cuando está en cualquiera de las dos salas que conecta.
  Su mapa DEBE recordar el estado de cada puerta tal como estaba en su última observación, aunque
  haya cambiado después.
- **FR-007**: Todo lo que se muestra al jugador DEBE derivarse exclusivamente de su conocimiento.
  El esqueleto completo sigue disponible internamente para la precarga y para la verificación de la
  cripta, pero NO DEBE llegar a la vista.
- **FR-008**: La interfaz DEBE ofrecer una forma de ver el mapa conocido: las salas exploradas con
  sus salidas y las salas avistadas.
- **FR-009**: El jugador DEBE poder pedir que lo lleven a una sala, y el programa DEBE llevarlo
  mediante una secuencia de movimientos ordinarios.
- **FR-010**: Solo una sala **explorada** es un destino válido. Pedir ir a una sala avistada,
  desconocida o inexistente DEBE rechazarse indicando el motivo.
- **FR-011**: El camino DEBE calcularse únicamente con el conocimiento del jugador: solo salas
  exploradas y solo salidas que su mapa recuerda abiertas.
- **FR-012**: El camino DEBE minimizar la suma de los costos de las salidas. Entre caminos de igual
  costo, DEBE elegirse el que da el primer paso hacia la sala de menor identificador.
- **FR-013**: Cada paso del viaje DEBE ser una acción completa del jugador: consume tiempo según el
  costo de la salida, y entre un paso y el siguiente ocurren los eventos del reloj con normalidad.
- **FR-014**: El camino DEBE recalcularse antes de cada paso con el conocimiento vigente en ese
  momento, de modo que una puerta que resulte estar cerrada quede descartada en el cálculo
  siguiente.
- **FR-015**: El viaje NO DEBE abrir ninguna puerta, aunque el jugador tenga la llave que la abre.
- **FR-016**: El viaje DEBE detenerse cuando el jugador llega al destino, cuando **entra** a una
  sala que contiene enemigos —activos o dormidos—, cuando recibe daño, o cuando deja de existir un
  camino conocido hasta el destino.
- **FR-017**: Que el jugador ya esté en una sala con enemigos al pedir el viaje NO DEBE impedir que
  empiece: la condición de parada es entrar a una sala con enemigos, y quien ya está allí no entra.
  Pedir irse de una sala con un enemigo al lado es un uso legítimo del viaje.
- **FR-018**: El daño DEBE detener el viaje tanto si llega al moverse como si llega entre dos pasos
  sin que el jugador se mueva, por ejemplo un pulso de veneno o el ataque de un enemigo que lo
  alcanzó. La regla existe para devolverle el control cuando algo le pasa.
- **FR-019**: El jugador DEBE poder ver por qué se detuvo un viaje y en qué sala quedó.
- **FR-020**: Cada paso del viaje DEBE anotarse en la bitácora de la partida como un movimiento
  individual, y la orden de ir a DEBE anotarse además como un comentario.
- **FR-021**: El pergamino de retroceso DEBE revertir únicamente el último paso del viaje, porque
  cada paso es una acción del jugador por separado.
- **FR-022**: El conocimiento del jugador es estado del juego: DEBE revertirse con el pergamino,
  guardarse en el archivo de partida y poder reconstruirse al consultar un instante pasado.
- **FR-023**: Mientras la antorcha está encendida, entrar a una sala DEBE dejar exploradas todas
  sus vecinas, a través de cualquier salida, esté abierta o cerrada.
- **FR-024**: Explorar una sala por efecto de la antorcha DEBE revelar su nombre y sus salidas, NO
  DEBE revelar su contenido y NO DEBE activar sus enemigos ni sus trampas.

### Entidades principales

- **Mapa conocido**: lo que el jugador sabe de la cripta. Reúne el estado de cada sala desde su
  punto de vista y el estado recordado de cada puerta observada. Es estado de la partida: se
  guarda, se revierte y se reconstruye.
- **Estado de una sala para el jugador**: explorada, avistada o desconocida. Son excluyentes entre
  sí y solo avanzan hacia un conocimiento mayor.
- **Puerta recordada**: el estado de una puerta tal como el jugador lo observó la última vez, que
  puede diferir del estado real en ese momento.
- **Viaje**: la orden de ir a una sala explorada y la secuencia de pasos que la cumple. Termina con
  un motivo y una sala donde quedó el jugador.
- **Motivo de parada**: por qué terminó un viaje. Llegó al destino, encontró enemigos, recibió daño
  o se quedó sin camino conocido.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: Calcular un paso del viaje tarda menos de 5 ms con el mapa conocido completo de la
  cripta de referencia.
- **SC-002**: Consultar si una sala está explorada, avistada o desconocida, y consultar el estado
  recordado de una puerta, tardan un tiempo que no crece con el tamaño del mapa que el jugador ya
  conoce.
- **SC-003**: Explorar salas nuevas cuesta en proporción a las salas que se revelan, no al tamaño
  del mapa conocido: revelar las mismas salas sobre un mapa diez veces mayor no cuesta diez veces
  más.
- **SC-004**: Registrar un cambio del mapa conocido y deshacerlo cuestan un tiempo que no crece con
  el tamaño del mapa conocido.
- **SC-005**: Dos estados reales distintos de la cripta que produzcan el mismo mapa conocido
  producen exactamente el mismo viaje: el cálculo no observa nada fuera del conocimiento del
  jugador.
- **SC-006**: Pedir dos veces el mismo viaje desde el mismo estado produce exactamente el mismo
  recorrido.
- **SC-007**: Los seis casos obligatorios del enunciado —destino avistado, puerta recordada abierta
  que en realidad se cerró, enemigo dormido, empate de costos, retroceso de un paso y antorcha—
  tienen cada uno una prueba automática que los ejercita.
- **SC-008**: Una medición compara el costo de las consultas y de la exploración del mapa conocido
  contra al menos una alternativa descartada, sobre criptas reproducibles a partir de una semilla.

## Supuestos

- El esqueleto completo de la cripta, con el costo de cada salida, ya está disponible al empezar la
  partida y se sigue usando internamente para la precarga y para verificar si la cripta se puede
  ganar. Esta capacidad no cambia esa descarga: cambia lo que de ahí llega al jugador.
- Ya existe un buscador de caminos que, dado un mapa consultable, un origen y un destino, devuelve
  el primer paso del camino más barato y distingue los casos de origen igual a destino y de
  ausencia de camino. Esta capacidad le entrega un mapa construido solo con el conocimiento del
  jugador.
- El costo de una salida es el mismo en los dos sentidos y no cambia durante la partida, así que el
  costo que el jugador recuerda de una salida no puede quedar desactualizado; lo que sí puede
  quedar desactualizado es el estado de una puerta.
- Una sala explorada nunca vuelve a ser avistada ni desconocida: el conocimiento solo avanza,
  salvo que el pergamino o la línea de tiempo devuelvan la partida a un instante anterior.
- El jugador conoce las salidas de una sala explorada, incluidas las que llevan a salas que no ha
  pisado; por eso esas salas quedan avistadas.
- Las trampas y el contenido de las salas no forman parte del mapa conocido que esta capacidad
  define: lo que el jugador sabe del contenido se rige por las reglas de juego ya existentes.
