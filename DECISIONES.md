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

Total **`O(V + E + L)`**, frente a `O(L·(V+E))` de la alternativa ingenua. La memoria es
`O(V + E + L)`.

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
