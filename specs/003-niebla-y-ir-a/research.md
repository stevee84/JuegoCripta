# Alternativas evaluadas: niebla de guerra e «ir a»

Material para la sección §5.3 del Documento de Decisiones (§7.1: «alternativas consideradas»).

## 1. Cómo representar lo que el jugador sabe

**Decisión**: dos tablas propias indexadas por id —salas exploradas y salas avistadas— más una
tabla de puertas observadas. Lo desconocido **no se almacena**.

**Por qué**: §5.3 pide tres cosas a la vez y esta forma las cumple sin trucos. Consultar el estado
de una sala o de una puerta es O(1), y son las consultas más frecuentes del juego: ocurren en cada
dibujo de la vista, en cada paso del viaje y en cada actualización por antorcha. Revelar `k` salas
son `k` inserciones, así que explorar cuesta en proporción a lo revelado y no al tamaño del mapa
conocido. Y cada revelación es un cambio pequeño e independiente, que es lo que hace barato
registrarlo y deshacerlo.

**Alternativas**:

| Alternativa | Por qué se descartó |
|---|---|
| Una marca de estado en cada sala del mapa real | Mezcla el conocimiento del jugador con el esqueleto, que §3.3 separa expresamente. Además la línea de tiempo necesita reconstruir el conocimiento de un instante pasado sin tocar el mapa. |
| Una lista de salas exploradas | Consultar si una sala está explorada pasaría a recorrer la lista, justo lo que §5.3 señala como operación frecuente y lo que el Principio II prohíbe. |
| Guardar también las desconocidas, con su estado | Hace que explorar y consultar dependan del tamaño del mapa completo en vez de lo descubierto, y rompe el requisito de proporcionalidad. |
| Una copia del mapa recortada al conocimiento | Habría que rehacerla en cada revelación y copiar completo para el retroceso, que es lo que el Principio VII prohíbe. |

## 2. Cómo calcular el camino del viaje

**Decisión**: reutilizar el buscador de caminos de la capacidad 001, entregándole una vista
construida solo con el conocimiento del jugador.

**Por qué**: el buscador ya existe, ya recibe una vista de solo lectura con `contiene_sala` y
`salidas_transitables`, ya minimiza la suma de costos y ya desempata por la vecina de menor id,
que es exactamente lo que §3.4 pide para «ir a». Escribir un segundo buscador sería duplicar un
problema resuelto y arriesgarse a que los dos desempaten distinto.

La separación la garantiza la vista, no la disciplina: el buscador no recibe el mapa real, así que
no puede observar lo que el jugador no sabe aunque el código cambiara.

**Alternativas**: un buscador propio para «ir a». Se descartó por duplicación. §5.3 pide
justificar si se comparte implementación con la búsqueda del cazador o si conviene separarlas: se
comparte, y lo que se separa es **el dato**, no el algoritmo.

## 3. Qué hacer con las salas avistadas en el viaje

**Decisión**: una sala avistada no es destino válido **ni paso intermedio**.

**Por qué**: §3.4 dice que «ir a» lleva a una sala explorada, y del lado de una avistada el jugador
no conoce ni sus salidas ni sus costos, así que no podría calcular nada a través de ella. Acordado
con 001 al cerrar el contrato de rutas.

## 4. Si guardar la ruta del viaje

**Decisión**: no se guarda. Cada paso vuelve a pedir el siguiente con el conocimiento vigente.

**Por qué**: §3.4 exige recalcular antes de cada paso, y así el caso de la puerta que se creía
abierta se resuelve solo, sin tratarlo como excepción: al llegar a la sala el jugador observa el
estado real, su mapa se corrige y el cálculo siguiente ya la evita.

**Alternativa**: calcular la ruta entera y seguirla validando cada paso. Es lo que el contrato con
001 descarta expresamente —«no seguiríamos una ruta guardada sin validar cada paso»— y obliga a
mantener coherente una respuesta que puede haber caducado.
