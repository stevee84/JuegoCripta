# Especificación: Verificación de resolubilidad de una cripta

**Directorio de la especificación**: `specs/002-resolubilidad`

**Creada**: 2026-11-05

**Estado**: Borrador

**Entrada**: Descripción del usuario: "Verificación de resolubilidad de una cripta. Antes de que empiece una partida, el programa debe determinar si esa cripta se puede ganar, y explicarlo cuando no."

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Saber antes de jugar si la cripta se puede ganar (Prioridad: P1)

Un jugador elige una cripta. Antes de que la partida empiece, el programa determina si esa
cripta se puede ganar: si existe alguna manera de conseguir la llave de salida y llegar a la
sala de salida. El jugador ve el resultado en una línea y, si la cripta no tiene solución, la
partida no empieza. Así nadie invierte una hora en una mazmorra imposible.

**Por qué esta prioridad**: es el valor central de la capacidad. Sin esto, ninguna de las demás
historias tiene sentido, y el servicio publica criptas sin solución a propósito.

**Prueba independiente**: se verifica una cripta con solución y otra sin ella, y se comprueba
que la primera deja empezar la partida y la segunda no.

**Escenarios de aceptación**:

1. **Dado** una cripta donde la llave de salida se puede conseguir y la sala de salida se puede
   alcanzar por una puerta que exige esa llave, **cuando** el jugador la elige, **entonces** la
   partida empieza y el jugador ve que la cripta tiene solución y con cuántas llaves.
2. **Dado** una cripta sin solución, **cuando** el jugador la elige sin pedir forzarla,
   **entonces** la partida no empieza y se muestra el informe de por qué.
3. **Dado** una cripta sin solución, **cuando** el jugador pide expresamente forzarla,
   **entonces** la partida empieza igual, después de mostrar el informe.
4. **Dado** una cripta con solución, **cuando** termina la verificación, **entonces** el
   programa informa un orden de obtención de llaves en el que cada llave aparece después de
   todas las que hacen falta para alcanzarla.
5. **Dado** una misma cripta con varios órdenes de obtención válidos, **cuando** se verifica dos
   veces, **entonces** las dos veces se obtiene exactamente el mismo orden.

---

### Historia 2 — Entender por qué una cripta no se puede ganar (Prioridad: P2)

Cuando una cripta no tiene solución, el jugador o quien la diseñó necesita saber qué falta: qué
llaves no se pueden conseguir, qué puertas cerradas están frenando el avance y qué llave pide
cada una, y dónde está cada una de esas llaves. Con eso se entiende el problema sin tener que
recorrer la cripta a mano.

**Por qué esta prioridad**: sin el informe, el programa solo dice "no se puede" y el jugador se
queda igual. Es la diferencia entre un diagnóstico y un rechazo.

**Prueba independiente**: se verifica una cripta sin solución y se comprueba que el informe
nombra las llaves que no se pueden conseguir, las puertas que frenan el avance con la llave que
pide cada una, y la ubicación de cada una de esas llaves.

**Escenarios de aceptación**:

1. **Dado** una cripta sin solución, **cuando** se consulta el informe, **entonces** aparece la
   lista de llaves que no se pueden conseguir.
2. **Dado** una cripta sin solución, **cuando** se consulta el informe, **entonces** aparecen las
   puertas cerradas que limitan la zona a la que el jugador sí puede llegar, cada una con la
   llave que exige.
3. **Dado** una cripta sin solución, **cuando** se consulta el informe, **entonces** para cada
   llave que no se puede conseguir se indica dónde se encuentra.
4. **Dado** una llave que suelta un enemigo que se desplaza por la cripta, **cuando** se verifica,
   **entonces** esa llave se ubica en la sala donde el enemigo empieza, no donde pueda estar
   después.

---

### Historia 3 — Detectar llaves encerradas por sí mismas (Prioridad: P3)

El caso más difícil de ver a simple vista: una llave guardada detrás de una puerta que solo ella
abre, o una cadena de llaves donde cada una está detrás de la siguiente. Nadie puede empezar esa
cadena. El informe debe señalar exactamente qué llaves forman el círculo.

**Por qué esta prioridad**: sin esto, el informe de la Historia 2 diría "esta llave no se puede
conseguir" para cada llave de la cadena, sin explicar que el problema es el círculo entre ellas.
Es la diferencia entre listar síntomas y nombrar la causa.

**Prueba independiente**: se verifica una cripta donde la llave de salida está detrás de la única
puerta que ella misma abre, y se comprueba que el informe nombra esa situación y las llaves que
la forman.

**Escenarios de aceptación**:

1. **Dado** una cripta donde la llave de salida está detrás de la única puerta que ella misma
   abre, **cuando** se verifica, **entonces** la cripta no tiene solución y el informe señala el
   círculo.
2. **Dado** una cripta donde una llave A está detrás de una puerta que exige B, y B detrás de una
   puerta que exige A, **cuando** se verifica, **entonces** el informe nombra las dos llaves como
   el círculo que impide empezar.
3. **Dado** una cripta con un círculo de llaves, **cuando** se verifica dos veces, **entonces**
   las dos veces se señala el mismo círculo.

---

### Historia 4 — Verificar una cripta sin abrir el juego (Prioridad: P3)

Quien prepara una partida, prueba el programa o revisa varias criptas necesita verificar una
cripta sin abrir la interfaz del juego: pedir la verificación, ver el resultado y seguir.

**Por qué esta prioridad**: hace que la capacidad se pueda probar y demostrar sin jugar, y
permite revisar criptas en serie. Útil, pero el juego funciona sin ella.

**Prueba independiente**: se pide la verificación de una cripta sin iniciar partida y se obtiene
el mismo resultado que se obtendría al empezarla.

**Escenarios de aceptación**:

1. **Dado** el nombre de una cripta, **cuando** se pide únicamente su verificación, **entonces**
   se obtiene el resultado y el informe sin que se abra la interfaz del juego ni se pida ninguna
   acción al jugador.
2. **Dado** que el programa funciona sin conexión con datos guardados localmente, **cuando** se
   verifica una cripta, **entonces** el resultado es el mismo que con el servicio en línea.

---

---

### Historia 5 — Saber qué me espera en la ruta antes de ir (Prioridad: P3)

Que una cripta tenga solución no significa que el jugador sobreviva el camino. Una ruta puede
pasar por salas con enemigos y trampas que suman más daño del que aguanta su vida si va directo,
mientras que el equipo y las pociones repartidos por esas mismas salas la vuelven superable. El
jugador necesita ver eso antes de salir, no descubrirlo muriendo.

**Por qué esta prioridad**: no cambia el veredicto ni es obligatoria para ganar, pero es la
diferencia entre "esta cripta tiene solución" y "esta cripta tiene solución y así es como se
sobrevive". Se apoya en datos que ya están disponibles, sin pedir nada más.

**Prueba independiente**: se verifica una cripta con solución cuya ruta mínima expone al jugador a
más daño del que aguanta su vida, y se comprueba que el informe lo advierte, que señala el equipo
del camino, y que la cripta sigue declarada con solución.

**Escenarios de aceptación**:

1. **Dado** una cripta con solución cuya ruta propuesta pasa por salas con enemigos, **cuando** se
   consulta el informe, **entonces** aparecen esas salas con el daño por golpe de cada enemigo y la
   vida del jugador.
2. **Dado** la misma cripta, **cuando** se consulta el informe, **entonces** aparecen el equipo y
   las pociones que hay en las salas de la ruta.
3. **Dado** una cripta con solución cuya ruta suma más daño del que aguanta la vida del jugador,
   **cuando** se verifica, **entonces** la cripta sigue declarada **con solución** y la partida
   empieza: la advertencia no altera el veredicto.
4. **Dado** una cripta con solución, **cuando** se construye la advertencia y después empieza la
   partida, **entonces** recorrer las salas de esa ruta no vuelve a pedir sus datos: los que la
   advertencia necesitó quedaron disponibles para la partida.
5. **Dado** una ruta en la que los datos de algunas salas no se pueden obtener, **cuando** se
   consulta la advertencia, **entonces** describe las demás e indica cuántas quedaron sin
   describir.

### Casos límite

- **La cripta no tiene ninguna puerta cerrada ni ninguna llave**: tiene solución si se puede
  llegar a la sala de salida, y el orden de obtención de llaves queda vacío.
- **La sala de salida es la sala inicial**: se resuelve con las mismas reglas, sin tratarlo como
  un caso aparte.
- **Una llave aparece en varias salas**: basta con que una de ellas se pueda alcanzar.
- **Una llave que el esqueleto nunca pide**: no afecta al resultado, pero no debe desaparecer del
  informe si no se puede conseguir.
- **Una puerta exige una llave que no existe en ninguna parte de la cripta**: la cripta no tiene
  solución si esa puerta hace falta, y el informe debe decir que la llave no está en ningún lado.
- **El esqueleto declara una puerta hacia una sala que no existe**: se informa como dato inválido
  de la cripta, no como cripta sin solución.
- **Ninguna puerta hacia la sala de salida exige la llave de salida**: la cripta no tiene solución,
  aunque se pueda caminar hasta esa sala (FR-004).
- **No se puede obtener la ubicación de las llaves**: ver FR-016.
- **Los datos de una sala de la ruta no se pueden obtener**: la advertencia describe las demás y
  dice cuántas quedaron fuera (FR-021).
- **La ruta propuesta no tiene ningún enemigo ni trampa**: la advertencia lo dice en vez de quedar
  en blanco.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **FR-001**: El programa DEBE determinar, antes de que una partida empiece, si la cripta elegida
  se puede ganar.
- **FR-002**: La verificación DEBE suponer que el jugador atraviesa cualquier salida abierta y
  cualquier salida cerrada cuya llave ya consiguió; que las llaves no se gastan; que todo enemigo
  puede ser derrotado; y que ni las trampas ni los cierres automáticos impiden el paso, porque una
  puerta siempre puede volver a abrirse con la misma llave.
- **FR-003**: Una llave que suelta un enemigo DEBE considerarse obtenible en la sala donde ese
  enemigo empieza, sin importar que el enemigo pueda desplazarse durante la partida.
- **FR-004**: Una cripta tiene solución si, partiendo de la sala inicial y bajo los supuestos de
  FR-002, el jugador puede conseguir la llave de salida y llegar a la sala de salida atravesando
  una puerta que exige esa llave. Se exige atravesar esa puerta: alcanzar la sala de salida por
  otra puerta que no pide la llave de salida no cuenta como ganar.
- **FR-005**: Cuando la cripta tiene solución, el programa DEBE informar un orden de obtención de
  llaves en el que cada llave aparezca después de todas las llaves que hacen falta para alcanzarla.
- **FR-006**: Cuando existan varios órdenes de obtención válidos, el programa DEBE elegir siempre
  el mismo: dos verificaciones de la misma cripta DEBEN producir un resultado idéntico.
- **FR-007**: Cuando la cripta no tiene solución, el informe DEBE enumerar las llaves que no se
  pueden conseguir.
- **FR-008**: Cuando la cripta no tiene solución, el informe DEBE enumerar la **frontera
  bloqueada** —las puertas cerradas adyacentes a la región alcanzable— indicando para cada una la
  llave que exige.
- **FR-009**: Para cada llave que no se puede conseguir, el informe DEBE indicar dónde se
  encuentra.
- **FR-010**: Cuando una llave esté encerrada detrás de puertas que solo ella abre, de forma
  directa o mediante una cadena de llaves, el informe DEBE señalar esa cadena nombrando las
  llaves que la forman.
- **FR-011**: Una cripta sin solución NO DEBE iniciar partida, salvo que se pida expresamente
  forzar el inicio.
- **FR-012**: El programa DEBE ofrecer una forma de verificar una cripta sin abrir la interfaz
  del juego ni pedir acciones al jugador.
- **FR-013**: Al iniciar una partida, el jugador DEBE ver una línea con el resultado: que la
  cripta tiene solución y con cuántas llaves, o el aviso de que no la tiene.
- **FR-014**: Durante la partida, el jugador DEBE poder consultar el informe completo de la
  verificación.
- **FR-015**: La verificación DEBE dar el mismo resultado usando el servicio en línea o los datos
  guardados localmente para jugar sin conexión.
- **FR-016**: La verificación DEBE usar los mismos datos de la cripta que la partida necesita
  después, de modo que iniciar una partida verificada no exija volver a pedirlos. [NEEDS
  CLARIFICATION: si no se puede obtener la ubicación de las llaves porque el servicio falla o el
  dato no está, ¿la partida no inicia, inicia avisando que no se pudo verificar, o se trata como
  cripta sin solución?]
- **FR-017**: El informe DEBE poder leerse sin conocer la cripta de antemano: cada llave, puerta
  y sala que mencione DEBE identificarse de forma que el jugador pueda ubicarla.
- **FR-018**: El informe completo —la frontera bloqueada y las dependencias entre llaves— DEBE
  quedar disponible tras una sola verificación, sin tener que repetirla por cada llave.
- **FR-019**: Cuando la cripta tiene solución, el informe DEBE añadir una advertencia de la ruta
  propuesta, que indique las salas de esa ruta con enemigos o trampas, el daño por golpe de cada
  enemigo y el daño de cada trampa frente a la vida del jugador, y el equipo y las pociones que
  hay en esas salas. Esta advertencia es informativa: NO DEBE cambiar el resultado de la
  verificación ni impedir que la partida empiece.
- **FR-020**: La advertencia de ruta DEBE construirse con los datos de las salas de esa ruta.
  Obtenerlos no añade costo al total de la partida, porque son los mismos datos que el jugador
  necesitará al recorrerla y quedan disponibles para el resto de la partida: solo se adelantan.
- **FR-021**: Si los datos de alguna sala de la ruta no se pueden obtener, la advertencia DEBE
  describir las demás e indicar cuántas quedaron sin describir, en lugar de fallar o de quedar
  vacía.

### Entidades principales

- **Cripta**: la mazmorra que se verifica. Tiene una sala inicial, una sala de salida y una llave
  de salida.
- **Sala**: cada lugar de la cripta. Se conecta con otras mediante salidas.
- **Salida**: conexión entre dos salas. Puede estar abierta o cerrada; si está cerrada, exige una
  llave concreta.
- **Llave**: objeto que abre las salidas que la exigen. Está en una sala, o la suelta un enemigo
  que empieza en una sala. No se gasta al usarla.
- **Orden de obtención**: secuencia de llaves que demuestra que la cripta tiene solución; cada
  llave aparece después de las que hacen falta para alcanzarla.
- **Frontera bloqueada**: las puertas cerradas adyacentes a la región que el jugador sí puede
  alcanzar. Es lo que delimita hasta dónde llega y qué llave le falta para seguir.
- **Informe de verificación**: resultado legible de la verificación. Si la cripta no tiene
  solución, reúne las llaves inalcanzables, la frontera bloqueada con la llave de cada puerta, la
  ubicación de esas llaves y las cadenas de llaves encerradas entre sí.
- **Advertencia de ruta**: parte del informe que acompaña a una cripta con solución. Describe lo
  que el jugador encontrará en las salas de la ruta propuesta —enemigos, trampas, equipo y
  pociones— frente a su vida inicial. No participa del veredicto.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-001**: La verificación de la cripta publicada más grande termina en menos de 200 ms.
- **SC-002**: Al crecer la cripta, el tiempo de verificación crece de forma aproximadamente
  proporcional a la suma de salas, salidas y llaves: duplicar ese total no más que duplica el
  tiempo, dentro del margen de medición.
- **SC-003**: Verificar dos veces la misma cripta produce un resultado idéntico, incluido el
  orden de obtención de llaves y, cuando corresponda, la cadena de llaves encerradas.
- **SC-004**: Iniciar una partida en una cripta ya verificada no consume ninguna consulta
  adicional al servicio respecto de iniciarla sin verificar.
- **SC-005**: Ante cualquier cripta sin solución, el informe permite identificar al menos una
  llave inalcanzable o una cadena de llaves encerradas: nunca se rechaza una cripta sin explicar
  el motivo.
- **SC-006**: Los cuatro casos obligatorios del enunciado (llave de salida tras su propia puerta,
  llave soltada por un enemigo que se desplaza, varios órdenes válidos, y cripta sin solución sin
  forzar) tienen cada uno una prueba automática que los ejercita.
- **SC-007**: Una medición compara el costo de la verificación contra el de repetir el recorrido
  completo de la cripta por cada llave, sobre criptas generadas con muchas llaves encadenadas y
  reproducibles a partir de una semilla.

## Supuestos

- El esqueleto de la cripta, que incluye todas las salas, sus salidas, cuáles están cerradas y
  qué llave exige cada una, ya se descarga completo al elegir una cripta. La verificación usa ese
  dato y no necesita recorrer la cripta jugando.
- La sala inicial, la sala de salida y la llave de salida vienen declaradas en los datos
  generales de la cripta.
- La ubicación de las llaves se obtiene del servicio en una consulta aparte, que cuenta dentro del
  presupuesto de solicitudes de la cripta. Por cada llave indica la sala donde está y, cuando la
  suelta un enemigo, cuál es esa instancia de enemigo; en ese caso la sala es donde ese enemigo
  inicia. Esa respuesta se puede guardar localmente y sigue siendo válida mientras coincida la
  versión de la cripta.
- La consulta de llaves identifica al enemigo que guarda una llave por su instancia concreta, no
  por su tipo. Las estadísticas de ese enemigo solo están disponibles junto con los datos de su
  sala, así que la advertencia de ruta depende de tener esos datos (FR-020, FR-021).
- Los datos de una sala, una vez obtenidos, quedan disponibles durante el resto de la partida: lo
  que la verificación trae no se vuelve a pedir al recorrerla. Hoy esa reutilización dura lo que
  dura la partida; el esqueleto y el contenido no sobreviven al cierre del programa, solo las
  fichas del catálogo.
- La vida, el ataque y la defensa iniciales del jugador vienen en los datos generales de la cripta,
  así que la advertencia de ruta puede compararlos sin pedir nada más.
- Un enemigo no impide atravesar una sala ni salir de ella: puede herir al jugador, pero nunca
  bloquea el paso. Por eso los enemigos no afectan al resultado de la verificación, solo a la
  advertencia de ruta.
- La verificación no simula el combate, el tiempo ni el azar: solo responde si existe alguna
  manera de ganar bajo los supuestos de FR-002.
- Si una cripta sin solución se fuerza, el jugador asume que puede no poder terminarla; el
  programa no cambia ninguna regla del juego para compensarlo.
- El servicio publica criptas sin solución a propósito, y la cripta usada en la revisión será
  desconocida de antemano.
