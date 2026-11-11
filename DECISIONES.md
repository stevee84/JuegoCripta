# Documento de Decisiones de Diseño — Parte II

Continúa el documento de la primera parte (`docs/decisiones_diseno.pdf`), con el mismo formato de
seis apartados: problema, alternativas consideradas, decisión, análisis de complejidad, evidencia
empírica y límites conocidos. Cada sección añade, como pide P2 §7.1, el enlace a la especificación
y al plan de spec-kit de los que proviene, y si la decisión final coincide con la del `plan.md`.

**Entorno de las mediciones.** Las de esta parte se tomaron en el equipo local con
`.venv/Scripts/python.exe`, mediana de repeticiones, con la preparación fuera del intervalo
cronometrado y las criptas sintéticas generadas de forma determinista por semilla (§6.3). Todas
salen de `--bench`: ningún número de aquí viene de un benchmark suelto (Principio IX).

---

## 5.4 Resolubilidad

**Especificación**: [specs/002-resolubilidad/spec.md](specs/002-resolubilidad/spec.md) ·
**Plan**: [specs/002-resolubilidad/plan.md](specs/002-resolubilidad/plan.md) ·
**Alternativas**: [specs/002-resolubilidad/research.md](specs/002-resolubilidad/research.md)

**¿Coincide con el plan original?** Sí en la estructura y el algoritmo. Cambió un detalle de
organización: el plan calculaba las dependencias entre llaves en una segunda pasada y la versión
entregada las obtiene del mismo recorrido. No lo motivó una medición sino una relectura de §5.4,
que pide que la frontera y las dependencias salgan «del mismo recorrido»; el cambio además quitó
una función y una estructura intermedia.

### 1. Problema

Antes de iniciar una partida hay que decidir si la cripta puede ganarse, y explicarlo cuando no.
El servicio publica criptas sin solución a propósito (§4.3) y en la revisión se usa una cripta
nueva, así que no sirve conocer las publicadas de antemano.

La dificultad no es recorrer la cripta: es que **obtener una llave puede volver alcanzable una
región entera**, de modo que el conjunto de salas accesibles crece a saltos. Además, cuando no
hay solución el informe debe nombrar la frontera bloqueada y las dependencias entre llaves, y
§5.4 exige que esa información salga del mismo recorrido, no de uno por cada llave.

La cripta más grande publicada tiene 50 salas; el límite es 200 ms (§6.1).

### 2. Alternativas consideradas

**Rehacer el recorrido completo cada vez que se obtiene una llave.** Es la que §5.4 nombra
expresamente como insuficiente. Cuesta `O(L·(V+E))`. Se conserva **dentro de `--bench`** como
término de comparación, que es el uso que §6.3 pide.

**Punto fijo sobre el conjunto de llaves** —repetir «¿qué alcanzo con lo que tengo?» hasta que no
cambie— es la anterior con otro nombre: cada iteración vuelve a recorrer todo.

**Precalcular, para cada sala, el conjunto de llaves necesarias para llegar.** El conjunto crece
de forma combinatoria y obliga a representar conjuntos de llaves, que es justo lo que `set` haría
y §6.2 prohíbe.

**Alcanzabilidad en el grafo producto (sala × llaves poseídas).** Correcto pero exponencial:
`V·2^L` estados. Inviable dentro de los 200 ms y desproporcionado para el problema.

Para el **orden de obtención** se evaluó ordenar por id de llave o por id de la sala que la
contiene. Las dos son deterministas y más simples de explicar, pero los ids no guardan relación
con la distancia, así que el informe podría listar primero una llave del fondo de la cripta y
después una de la entrada. Se descartaron por legibilidad, no por costo.

### 3. Decisión

Un **recorrido en anchura que se reanuda**. Parte de la sala inicial y avanza por las salidas
abiertas y por las cerradas cuya llave ya se obtuvo. Al encontrar una puerta cerrada cuya llave
falta, no la descarta: la **aparca** en una tabla indexada por esa llave. Cuando el recorrido
alcanza la sala donde está esa llave, reanuda desde todas las puertas que la esperaban.

Agotada la región alcanzable, **el mismo recorrido continúa** más allá de las puertas aparcadas,
cruzándolas aunque falte su llave y arrastrando cuál bloquea el paso. Al terminar, lo aparcado
*es* la frontera bloqueada y la llave que marca cada sala *es* la dependencia de las llaves que
hay allí. Buscar círculos es seguir esas flechas.

Estructuras, todas ya entregadas en la Parte I y ninguna de biblioteca:

| Dato | Estructura | Por qué |
|---|---|---|
| Salas vistas y qué llave las bloquea | `TablaHashImpl` | pertenencia y consulta por id en O(1); `set` está prohibido (§6.2) |
| Llaves obtenidas | `TablaHashImpl` | lo mismo, por id de llave |
| Puertas en espera de una llave | `TablaHashImpl` → lista | es la frontera bloqueada y el grafo de dependencias a la vez |
| Desempate dentro de un nivel | `MonticuloMinimo` | ordena sin `sorted()`, prohibido por §6.2 |

El orden de obtención es por cercanía a la sala inicial; a igual distancia, por menor id de sala;
dentro de una sala, por id de llave. Sale del propio recorrido, que ya avanza por niveles, y
reutiliza el patrón de `mas_cercanas` (`service/cargador_contenido.py`).

### 4. Análisis de complejidad

Con `V` salas, `E` salidas y `L` llaves:

- Cada sala entra una vez en la cola: `O(V)`.
- Cada salida se examina al visitar su sala y, si estaba aparcada, una segunda vez al liberarse su
  llave: `O(E)` en total, **no** `O(L·E)`.
- Cada llave se obtiene una vez y reanuda su lista de puertas una vez: `O(L + E)`.
- La continuación más allá de la frontera visita cada sala restante una vez: `O(V + E)`.
- Los círculos se buscan siguiendo una flecha por llave: `O(L)`.

El recorrido en sí es **`O(V + E + L)`**, frente a `O(L·(V+E))` de la alternativa ingenua. La
memoria es `O(V + E + L)`.

**Pero el costo observado no es lineal, y la causa está fuera de esta capacidad.**
`MapaCripta.obtener_sala` recorre el arreglo de salas —su propio comentario lo declara: «búsqueda
O(n), sin índice hash»—, así que cada consulta por id cuesta `O(V)` y el recorrido completo se
vuelve `O(V²)` en criptas grandes. Medido con un perfilador sobre una cripta de 641 salas, esa
función sola se lleva el 35 % del tiempo de verificación.

Sustituyéndola por un índice por id, con la misma tabla hash propia, el tiempo baja de 18,85 ms a
7,34 ms en 641 salas y el factor al duplicar el tamaño pasa de 2,9 a 2,1, que es lo que `SC-002`
pide. No se cambió aquí porque `MapaCripta` es un componente compartido y el Principio VIII exige
identificar a sus consumidores y acordar el cambio; además es justo la observación que el profesor
hizo sobre la primera parte y que el Principio II recoge. Queda reportado al grupo.

Esto **no** compromete el límite de §6.1: la cripta publicada más grande tiene 50 salas y se
verifica en 0,51 ms. El efecto solo aparece en las criptas sintéticas de cientos de salas que
genera el `--bench`.

### 5. Evidencia empírica

Verificación de las criptas publicadas, mediana de 5 repeticiones:

| CRIPTA | SALAS | MEDIANA | LÍMITE §6.1 |
|---|---|---|---|
| cripta-01 | 6 | 0,109 ms | 200 ms |
| cripta-02 | 20 | 0,216 ms | 200 ms |
| cripta-03 | 40 | 0,446 ms | 200 ms |
| cripta-04 | 50 | **0,509 ms** | 200 ms |

La más grande queda casi 400 veces por debajo del límite. El crecimiento es aproximadamente
lineal: de 20 a 40 salas el tiempo pasa de 0,216 a 0,446 ms, así que duplicar el tamaño no más
que duplica el tiempo (`SC-002`).

Recorrido incremental contra rehacerlo por cada llave, sobre criptas sintéticas de llaves
encadenadas, deterministas por semilla:

| SALAS | LLAVES | INCREMENTAL | POR LLAVE | VECES |
|---|---|---|---|---|
| 21 | 5 | 0,271 ms | 0,297 ms | 1,1× |
| 41 | 10 | 0,566 ms | 1,110 ms | 2,0× |
| 81 | 20 | 1,276 ms | 4,522 ms | 3,5× |
| 161 | 40 | 3,172 ms | 21,305 ms | **6,7×** |

La ventaja casi se duplica cada vez que se duplican las llaves, que es justo lo que separa
`O(V+E+L)` de `O(L·(V+E))`. Con pocas llaves la diferencia es menor, porque domina el costo fijo
del recorrido.

**Costo de red.** La verificación añade **una solicitud por partida**, la consulta de ubicación de
llaves (§4.2), que cuenta en el presupuesto (§4.3). El arranque pasó de 7 a 8 solicitudes; en
`cripta-01`, con `presupuesto_solicitudes` 9, el margen baja de 2 a 1. No se desperdicia: son los
mismos datos que la partida necesita después, así que iniciar una cripta ya verificada no vuelve
a pedir nada (`SC-004`).

### 6. Límites conocidos

- **La verificación no dice nada del combate.** §3.5 supone que todo enemigo puede ser derrotado,
  y se comprobó que eso deja fuera un modo de fallo real: `cripta-01` **tiene solución** y aun así
  mata al jugador que va directo por la llave de salida, porque la ruta pasa por dos ratas
  rastreadoras y una trampa mientras el equipo que la vuelve superable está repartido por esas
  mismas salas. Se consideró añadir una advertencia de ruta con esos datos y **se descartó**:
  habría revelado el contenido de salas no exploradas, que §3.3 reserva al conocimiento del
  jugador —ni la antorcha revela contenido— y habría contradicho la capacidad `003-niebla-y-ir-a`.
  Decidir si existe *alguna* secuencia de acciones que sobreviva es además una búsqueda en el
  espacio de estados (vida × inventario × posiciones × reloj × semilla), no un recorrido de grafo.
- **Un presupuesto muy justo podría no absorber la solicitud extra.** Hoy ninguna de las cuatro
  criptas publicadas está en ese caso, pero una cripta grande con presupuesto ajustado lo estaría.
- **Las dependencias entre llaves se modelan con una llave bloqueante por sala**, la primera que
  el recorrido encuentra. Alcanza para los círculos que §3.5 describe —una llave tras su propia
  puerta, o una cadena entre varias— pero no describe el caso en que llegar a una sala exige
  varias llaves por caminos distintos.
- **Las criptas sintéticas del `--bench` son cadenas regulares.** Validan el crecimiento, no
  cualquier topología; una cripta muy ramificada o con muchas puertas por sala podría comportarse
  distinto.
- **Los costos de §3.1 no participan del veredicto.** La alcanzabilidad es binaria, así que la
  verificación mira destino, apertura y llave requerida, nunca el peso de la salida. Se acordó
  con la capacidad 001, que introduce los costos, y hay una regresión que comprueba sobre las
  cuatro criptas publicadas y las de prueba que cambiar costos válidos no altera el veredicto,
  el orden de llaves, la frontera ni los círculos. La consecuencia es que esta capacidad **no**
  dice nada sobre la ruta más barata: eso es «ir a» (§3.4), en la capacidad 003.
- Las mediciones son de un solo equipo y no caracterizan otras máquinas.

**Trazabilidad**: `logica/verificador_resolubilidad.py`; `service/inicializador_partida.py`;
`datos/decodificador_datos.py` (`convertir_llaves`); `main.py` (`--verificar`);
`benchmarks/integrante2.py` (`medir_resolubilidad`, `medir_resolubilidad_cripta_real`);
`tests/test_logica/test_resolubilidad.py`; `tests/test_datos/test_contrato_llaves.py`.

---

## 5.5 Línea de tiempo y puntos de control

**Especificación**: [specs/004-linea-de-tiempo/spec.md](specs/004-linea-de-tiempo/spec.md) ·
**Plan**: [specs/004-linea-de-tiempo/plan.md](specs/004-linea-de-tiempo/plan.md) ·
**Alternativas y mediciones previas**: [specs/004-linea-de-tiempo/research.md](specs/004-linea-de-tiempo/research.md) ·
**Responsable**: Joshua Cabrera Bonilla

**¿Coincide con el plan original?** En el mecanismo, sí: reconstruir hacia atrás desde el punto de
control siguiente. Cambió en cuatro puntos, todos por mediciones o pruebas: (1) la primera versión
del plan copiaba el estado en cada consulta; `/speckit-analyze` lo marcó contra el principio VII y
se cambió a deshacer y rehacer en sitio; (2) el K por defecto pasó de 50 a 10 con la medición de
T001; (3) la copia del estado real exigió arreglar la serialización de las salas (Sofía, `f89b7b5`)
y de la lista doble, que se copiaba de forma recursiva; (4) el punto de control comparte el historial
del pergamino y las tuplas del azar en lugar de copiarlos, lo que bajó la copia de 71,5 a 19,1 ms.

### 1. Problema

`historia <t>` e `historia #k` deben mostrar el estado de la partida en cualquier instante pasado
sin modificarla (§3.6). Se permiten copias completas del estado, pero como máximo una cada K
acciones del jugador, y una consulta no puede aplicar ni deshacer cambios de más de K acciones
(§5.5). Ubicar el punto de control más cercano es frecuente y su costo importa en partidas largas.
Al usar un pergamino la línea debe recortarse sin recorrer la historia. El límite es 50 ms con al
menos 5 000 acciones y el K por defecto (§6.1).

### 2. Alternativas consideradas

| Alternativa | Resultado |
|---|---|
| Sin puntos de control: deshacer desde el estado actual | Viola «como máximo K». Medido: hasta 97 s por consulta con 5 000 acciones. |
| Una copia completa por acción (K = 1) | Viola la memoria de §5.5 («acciones por tamaño del estado»). |
| Copia de trabajo del punto de control en cada consulta | Choca con el principio VII. Medido en T001: de 8 a 14 veces más lenta que deshacer. |
| Re-simular hacia adelante desde el punto de control anterior | Llega al mismo estado (comprobado). Con el contenido de todas las salas cargado salió más rápida (10 ms frente a 44 ms con K = 10). Se descartó para producción porque ejecuta las reglas del motor en cada consulta y, con salas descargadas después del punto de control, necesitaría volver a pedir contenido al servicio (presupuesto de solicitudes, principio VI). Las copias tampoco llevan el catálogo de fichas. |
| **Hacia atrás desde el punto de control siguiente, deshaciendo y rehaciendo en sitio** | **Elegida.** |

### 3. Decisión

- **Instantes**: arreglo contiguo no decreciente con el reloj de cada decisión; el instante t se
  traduce a una acción con una búsqueda binaria propia (sin `bisect`).
- **Puntos de control**: arreglo contiguo; el de la acción j·K está en la posición j, así que se
  ubica por aritmética, ⌈(k − 1) / K⌉. Cada punto es una sola copia profunda del estado y de las
  transacciones de su ventana, hecha junta para que los cambios copiados apunten al estado copiado.
  Comparte en vez de copiar el historial del pergamino y las tuplas inmutables del azar.
- **Consulta**: deshace sobre el punto de control (o sobre el estado vivo si la acción está después
  del último punto) como máximo K transacciones, la última a medias si t cae entre dos decisiones;
  arma el resumen y rehace con los inversos en un `finally`. Nunca copia el estado.
- **Pergamino**: la línea quita lo revertido del final de sus arreglos y descarta los puntos
  posteriores. Recoger, soltar y consumir pergaminos se anotan como cambios «solo línea» para que el
  pasado los muestre bien.
- **K por defecto: 10** (`LineaTiempo.K_POR_DEFECTO`, configurable con `--checkpoint-cada`).
- **Persistencia**: pendiente del guardado de Steven (contrato `specs/004-linea-de-tiempo/contracts/guardado-v10.md`).

### 4. Análisis de complejidad

| Operación | Costo |
|---|---|
| Registrar una acción | O(1) amortizado, más una copia del estado cada K acciones |
| Ubicar el punto de control de #k | O(1) |
| Ubicar la acción de un instante t | O(log n) |
| `historia` | O(c · K) para deshacer y rehacer, con c cambios por acción, más armar el resumen |
| Recorte por pergamino | O(r), con r ≤ 5 acciones revertidas |
| Memoria | ⌈n / K⌉ copias del estado más los cambios de todas las acciones |

### 5. Evidencia empírica

Todo sale de `main.py --bench` (`benchmarks/linea_tiempo.py`, proveedor `medir_linea_tiempo`) y
queda guardado en `benchmarks/resultados/linea_tiempo_5000.json` (los cuatro K en una partida) y
`benchmarks/resultados/linea_tiempo_5000_k10.json` (K = 10 solo, en un proceso aparte). Carga:
5 000 acciones de `cripta-04` (50 salas), semilla 7, jugador con vida muy alta solo en la medición
para que la partida dure, lo que va activando enemigos de toda la cripta (unos 110 cambios por
acción). Es un peor caso.

| K | `historia`: mediana / p95 / máximo | Crear un punto (mediana) | Memoria de la línea | Máx. transacciones por consulta |
|---|---|---|---|---|
| **10 (solo)** | **16,3 / 59,7 / 82,7 ms** | **50,6 ms** | **647 MB** | 9 |
| 50 | 128,7 / 473,0 / 482,4 ms | 294 ms | 518 MB | 48 |
| 200 | 549,6 / 1 918 / 2 307 ms | 1 372 ms | 439 MB | 193 |
| sin puntos | 22,9 s / — / 97,2 s | — | 0,3 MB | 3 932 |

Las filas de 50 y 200 se midieron con las cuatro líneas en el mismo proceso (más de 1,5 GB), lo
que agrega pausas del sistema; por eso K = 10 se midió también por separado. Otras mediciones:
un retroceso de punta a punta cuesta 3,1 ms frente a 82,8 ms de copiar el estado; reconstruir hacia
atrás y re-simular llegan al mismo estado con los tres K; el replay rechaza un log de otra versión.

**Por qué K = 10.** Es el único de los tres que deja la mediana de `historia` muy por debajo de
50 ms (16 ms). Con K = 50 la mediana ya pasa los 100 ms. La memoria baja poco al subir K (de 647 a
439 MB), porque la mayor parte son los cambios de las acciones, que se guardan igual con cualquier K
(eso es lo que pide §5.5: crecer con los cambios); por eso subir K no compensa.

### 6. Límites conocidos

- **`historia` no cumple 50 ms en todos los casos** con esta carga: el p95 es 60 ms y el máximo
  83 ms. La mediana sí (16 ms). En una partida normal, con menos enemigos activos por acción, cada
  transacción es más chica y las consultas son más rápidas (T001: 5,6 ms de mediana con 600 acciones).
- **La acción que crea un punto de control pasa los 20 ms por ciclo** (unos 51 ms, una de cada 10
  acciones). Mejoras posibles, no implementadas: tomar el punto de control fuera del ciclo de la
  decisión, o una copia propia del estado más barata que `copy.deepcopy`.
- **Memoria alta en partidas muy largas** (unos 650 MB con 5 000 acciones en esta carga).
- **Guardar y cargar la línea** depende del guardado de Steven; mientras tanto, una partida cargada
  empieza sin línea de tiempo.
- **El mapa conocido** del resumen dice «no disponible» hasta que exista la spec 003.
- `pickle` ejecuta código al cargar un archivo malicioso; se acepta porque el archivo de partida es
  local y lo produce el propio juego.

**Archivos**: `logica/linea_tiempo.py`, `logica/cambios.py`, `logica/historial_reversible.py`,
`logica/servicio_inventario.py`, `logica/inventario.py`, `estructuras/lista_doble.py`,
`controller/resumen_historia.py`, `controller/ejecutor_replay.py`, `controller/controlador_juego.py`,
`benchmarks/linea_tiempo.py`.

---

## 5.6 Revisión de decisiones con la carga nueva

**Historial de retroceso (Joshua, spec 004, FR-025).** Con la carga nueva (cazadores, costos
variables y la línea de tiempo vinculada), un retroceso con pergamino de punta a punta (reloj, agenda,
rastro, puertas, trampas, inventario y azar) cuesta 3,1 ms de mediana, frente a 82,8 ms de guardar una
copia completa del estado por acción (`benchmarks/resultados/linea_tiempo_5000.json`, fila
`retroceso_punta_a_punta`). La decisión de la Parte I (cambios reversibles, sin copias) sigue siendo
adecuada. Cambió un detalle: la lista doble que usa el historial se copiaba de forma recursiva y
reventaba en partidas largas; ahora se copia y serializa de forma iterativa (ver §5.5).

La revisión de agenda correspondiente a §5.6 se completará por separado en T069. La evidencia
complementaria del mapa se documenta en [Índice por ID de MapaCripta (evidencia complementaria
de 001)](#índice-por-id-de-mapacripta-evidencia-complementaria-de-001). Esta referencia no cambia
la decisión de Resolubilidad de §5.4 ni atribuye a 001 el componente de 002.

### Índice por ID de MapaCripta (evidencia complementaria de 001)

**Especificación**: [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md) ·
**Plan**: [specs/001-terreno-y-cazador/plan.md](specs/001-terreno-y-cazador/plan.md) ·
**Diseño medido**: [benchmarks/mapa_cripta_integrante1.py](benchmarks/mapa_cripta_integrante1.py)

#### 1. Problema y consumidores

`MapaCripta` necesita conservar el orden de llegada de las salas, pero una lista sola obliga a
recorrer hasta `V` referencias para resolver cada ID. Esa búsqueda aparece en operaciones
frecuentes y, al vincular `E` salidas, puede repetirse una vez por puerta. El costo lineal no es
solo del verificador de Resolubilidad: también afecta, entre otros, inicialización y restauración
(`datos/decodificador_datos.py`, `service/inicializador_partida.py`,
`service/restaurador_partida.py`), simulación (`logica/motor_juego.py`,
`logica/registro_rastro.py`, `logica/gestor_efectos.py`), carga gradual, servicios, vista y pruebas
de identidad/serialización. El cambio debía preservar las firmas y la instancia canónica que esos
consumidores ya observaban.

#### 2. Decisión y alternativa

Se conserva `_salas` como lista de referencias para mantener orden estable, recorrido, guardado y
la sustitución de una sala en su misma posición. En paralelo, `_salas_por_id` usa la
`TablaHashImpl` propia para `obtener_sala` y `contiene_sala`. Altas y sustituciones actualizan las
dos representaciones; `vincular_salidas` consulta el índice y deja cada `Puerta.destino_sala`
apuntando a la instancia canónica. El orden de buckets de la tabla nunca define el orden del mapa.

La comparación usa `_MapaLinealBenchmark`, limitada a
`benchmarks/mapa_cripta_integrante1.py`: conserva únicamente una lista, busca y sustituye por
recorrido y resuelve cada destino de cada puerta con otra búsqueda lineal. Antes de cronometrar se
comprobaron los mismos IDs y orden, aciertos y ausencias idénticos, orden de puertas, destinos y
alias canónicos. La generación de salas/puertas quedó fuera; construcción, consultas y
vinculación tuvieron intervalos separados.

#### 3. Complejidad

Con `V` salas y `E` salidas dirigidas:

| Operación | Lista + `TablaHashImpl` | Peor caso hash | Alternativa lineal medida |
|---|---|---|---|
| Construir | `O(V)` esperado total; inserción `O(1)` esperada/amortizada | `O(V²)` por colisiones patológicas y rehashes | `O(V²)`, porque cada alta comprueba el ID por recorrido |
| Consultar/contener por ID | `O(1)` esperado | `O(V)` | `O(V)` |
| Sustituir una sala | `O(V)` para conservar exactamente la posición; índice esperado `O(1)` | `O(V)` | `O(V)` |
| Vincular todas las salidas | `O(V+E)` esperado | `O(V·E)` si cada consulta degenera | `O(V·E)` |
| Sustituir y revincular | `O(V+E)` esperado | `O(V·E)` | `O(V·E)` |

El índice añade `O(V)` memoria. `obtener_salas()` sigue copiando solo la lista de referencias y no
expone ni ordena la tabla.

#### 4. Entorno, cargas y resultados originales

La ejecución original se conserva en
[`benchmarks/resultados/mapa_cripta_original_c1_r9_32-128-512.json`](benchmarks/resultados/mapa_cripta_original_c1_r9_32-128-512.json).
Usó Python 3.12.10 sobre Windows 11 (`Intel64 Family 6 Model 154 Stepping 3`),
`perf_counter_ns`, semilla de fixture 1729, un calentamiento y nueve repeticiones. La unidad es
**ns por lote** y todas las muestras permanecen en el JSON. Con nueve muestras, p95 por
*nearest-rank* ocupa el rango 9 y coincide con el máximo.

**Construcción** — cada lote añade `V` salas; la densidad indica las puertas ya presentes en el
fixture, cuya generación no forma parte del intervalo:

| V | Salidas/sala | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|
| 32 | 1 | 32 800 | 35 400 | 22 100 | 23 600 |
| 32 | 4 | 37 900 | 40 100 | 17 900 | 18 700 |
| 128 | 1 | 236 500 | 322 500 | 255 900 | 309 700 |
| 128 | 4 | 150 200 | 169 100 | 238 100 | 258 500 |
| 512 | 1 | 675 400 | **33 018 900** | 3 887 900 | 4 211 300 |
| 512 | 4 | 602 900 | 629 200 | 3 613 600 | 4 164 000 |

**Consultas por ID** — cada patrón contiene aciertos al inicio, medio y final y dos ausencias, y se
repite `V` veces:

| V | Consultas/lote | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|
| 32 | 160 | 25 500 | 26 700 | 64 100 | 66 500 |
| 128 | 640 | 100 100 | 102 600 | 1 026 600 | 1 184 500 |
| 512 | 2 560 | 486 100 | 536 700 | 13 630 700 | 13 821 400 |

**Vinculación** — cada lote resuelve todas las salidas del grafo:

| V | Salidas/sala | E | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 1 | 32 | 7 100 | 11 100 | 15 700 | 19 200 |
| 32 | 4 | 128 | 21 300 | 21 800 | 42 800 | 45 000 |
| 128 | 1 | 128 | 29 100 | 37 900 | 181 500 | 193 000 |
| 128 | 4 | 512 | 117 400 | 322 100 | 656 300 | 979 900 |
| 512 | 1 | 512 | 151 100 | 211 500 | 2 541 000 | 3 081 200 |
| 512 | 4 | 2 048 | 376 700 | 433 800 | 9 146 900 | 10 785 800 |

La consulta indexada conserva un costo aproximadamente constante por consulta mientras el lote
crece; la lineal aumenta también con `V`. La vinculación muestra el mismo contraste entre resolver
`E` destinos por hash y hacer `E` recorridos. La construcción paga la estructura adicional y en
32 salas puede ser más lenta; desde 128/512 salas sus medianas son menores que las de la
alternativa lineal medida. Esto matiza la hipótesis histórica de §5.4: confirma el cuello de
botella en las primitivas de consulta/vinculación, pero no vuelve a medir ni atribuye a este
benchmark el cambio de 18,85 ms a 7,34 ms del verificador completo de 002.

#### 5. Muestra extrema y repetición conservada

La construcción indexada de 512 salas y una salida por sala tuvo en la corrida original una
muestra de **33 018 900 ns**, que por el tamaño de nueve muestras fue a la vez p95 y máximo; la
mediana del mismo lote fue 675 400 ns. La muestra se conserva y no se descarta ni se le asigna una
causa no comprobada.

La repetición posterior está en
[`benchmarks/resultados/mapa_cripta_repeticion_c5_r30_512.json`](benchmarks/resultados/mapa_cripta_repeticion_c5_r30_512.json).
Usó el mismo entorno, semilla 1729, tamaño 512 y densidades 1/4, con cinco calentamientos, treinta
repeticiones, todas las muestras conservadas y p95 *nearest-rank* en el rango 29:

| Operación (512 salas) | Densidad | Índice mediana/p95/máx. | Lineal mediana/p95/máx. |
|---|---:|---:|---:|
| Construcción | 1 | 639 950 / 685 600 / 718 600 | 4 484 950 / 4 737 100 / 4 995 200 |
| Construcción | 4 | 652 000 / 897 800 / 1 252 100 | 3 914 450 / 4 462 900 / 4 476 700 |
| Vinculación (`E=512`) | 1 | 218 200 / 1 093 100 / 1 636 300 | 2 394 800 / 2 738 700 / 2 827 800 |
| Vinculación (`E=2 048`) | 4 | 467 850 / 1 449 200 / 1 985 500 | 9 563 400 / 10 065 200 / 10 077 100 |
| Consulta (2 560) | — | 407 000 / 485 200 / 601 000 | 14 014 750 / 14 866 900 / 16 212 400 |

La muestra extrema original no se repitió en esas treinta mediciones de construcción; esta
observación no demuestra por qué apareció y no autoriza a borrar el dato original.

#### 6. Límites y estado de integración

- El proveedor publica `PROVEEDORES` y funciona mediante la interfaz de
  `benchmarks.integrante3.ejecutar`, pero todavía no está registrado en `main.py --bench`; esa
  integración conjunta corresponde a T049. Por eso estos números son evidencia aislada
  complementaria y no una medición final conectada de §5.6.
- Las mediciones validan construcción, consulta e identidad de vinculación; no miden un ciclo de
  juego completo, rutas de cazadores, agenda ni red/renderizado. No demuestran el presupuesto de
  20 ms de PR-001.
- Solo caracterizan el equipo y las cargas indicadas. El peor caso de la tabla hash sigue siendo
  lineal por colisiones, aunque no se observó esa degeneración en estos fixtures.
- T076 permanece abierta hasta que T049/T050/T071 conecten, ejecuten y validen las filas por
  `main.py --bench`; documentar la evidencia aislada no sustituye esas dependencias.

**Trazabilidad**: `logica/mapa_cripta.py`; `estructuras/tabla_hash.py`;
`benchmarks/mapa_cripta_integrante1.py`; `tests/test_bench_mapa_cripta.py`;
`specs/001-terreno-y-cazador/tasks.md` (T007–T009, T049–T050, T071–T076).
