# Alternativas evaluadas: verificación de resolubilidad

Material para la sección §5.4 del Documento de Decisiones (§7.1: «alternativas consideradas»).

## 1. Cómo recorrer la cripta cuando una llave abre toda una región

**Decisión**: un solo recorrido en anchura que aparca las puertas bloqueadas en una tabla
indexada por la llave que exigen, y las reanuda cuando esa llave aparece.

**Por qué**: §5.4 lo pide casi con esas palabras —«repetir el recorrido completo de la cripta cada
vez que se obtiene una llave no cumple el requisito»— y además exige que la frontera bloqueada y
las dependencias entre llaves salgan de ese mismo recorrido. Aparcar la puerta en lugar de
descartarla deja las dos cosas construidas sin trabajo extra: lo que quedó aparcado al terminar
**es** la frontera, y quién esperaba a quién **es** el grafo de dependencias.

**Alternativas**:

| Alternativa | Por qué se descartó |
|---|---|
| Rehacer el recorrido completo cada vez que se obtiene una llave | `O(L·(V+E))`. §5.4 la nombra expresamente como insuficiente. Se conserva **dentro de `--bench`** como término de comparación, que es el uso que §6.3 exige. |
| Punto fijo sobre el conjunto de llaves: repetir «¿qué alcanzo con lo que tengo?» hasta que no cambie | Es la anterior con otro nombre: cada iteración vuelve a recorrer todo. Mismo costo. |
| Precalcular, para cada sala, el conjunto de llaves necesarias para llegar | El conjunto crece de forma combinatoria y obliga a representar conjuntos de llaves, que es justo lo que `set` haría y §6.2 prohíbe. |
| Tratarlo como alcanzabilidad en un grafo producto (sala × llaves poseídas) | Correcto pero exponencial en llaves: `V·2^L` estados. Inviable dentro de los 200 ms y desproporcionado para el problema. |

### Una pasada o dos

La primera versión calculaba las dependencias entre llaves en una **segunda** pasada, separada
del recorrido principal. Dos pasadas lineales dan el mismo `O(V + E)` y cumplen lo que §5.4
prohíbe, que es un recorrido *por cada llave*. Pero §5.4 dice literalmente que la frontera
bloqueada y las dependencias deben salir «del mismo recorrido», así que se fusionaron: cuando la
región alcanzable se agota, el mismo bucle continúa más allá de las puertas aparcadas.

Fusionarlo no costó legibilidad, al contrario. Desapareció la función de dependencias y una sola
tabla `sala → llave que la bloquea` sustituyó a la de visitadas más el grafo de dependencias,
que antes se construía aparte. La detección de círculos pasó a ser seguir flechas ya anotadas.

## 2. Cómo fijar el orden de obtención de llaves

**Decisión**: por cercanía a la sala inicial; a igual distancia, menor id de sala; dentro de una
misma sala, por id de llave.

**Por qué**: `FR-006` y `SC-003` exigen que dos ejecuciones den el mismo orden, y el enunciado
permite cualquier orden válido mientras sea determinista. Este criterio sale gratis del propio
recorrido —que ya avanza por niveles— y reutiliza el patrón de `mas_cercanas`
(`service/cargador_contenido.py:53`), donde un `MonticuloMinimo` ordena cada nivel por id sin
llamar a `sorted()`, prohibido por §6.2. Además produce un orden parecido al que seguiría un
jugador, lo que hace el informe legible.

**Alternativas**: ordenar por id de llave, o por id de la sala que la contiene. Las dos son
deterministas y más simples de explicar, pero los ids no guardan relación con la distancia, así
que el informe podría listar primero una llave del fondo de la cripta y después una de la
entrada. Se descartaron por legibilidad, no por costo.

## 3. Cuántos círculos de llaves reportar

**Decisión**: todos, ordenados por la llave de menor id de cada uno.

**Por qué**: el grafo de dependencias ya está construido al terminar el recorrido, así que
encontrar todos los círculos cuesta lo mismo que encontrar el primero. Reportar uno solo obliga a
quien diseñó la cripta a corregir, volver a verificar y descubrir el siguiente, de a uno.

**Alternativa**: reportar solo el primero. Informe más corto y prueba más simple, pero oculta
trabajo pendiente.

## 4. Dónde vive la verificación

**Decisión**: `logica/verificador_resolubilidad.py`, lógica pura que recibe el mapa y la
ubicación de las llaves ya resueltos y devuelve el informe como dato.

**Por qué**: §3.5 exige que `--verificar` corra «sin instanciar la vista», y el Principio IV
separa las capas. Si el verificador no conoce la red ni la vista, se prueba con datos en memoria,
corre en el `--bench` sin montar una partida y la medición de los 200 ms no mezcla tiempo de red.

**Alternativa**: ponerlo en `service/`, junto a quien trae los datos. Habría acoplado el
algoritmo a la fuente y obligado a simular la red para medirlo.

## 5. Cómo llega la ubicación de las llaves sin conexión

**Decisión**: como un archivo más del paquete de datos, leído por el mismo contrato lógico que
usa la fuente de red (`FR-015`).

**Por qué**: P1 §3.4 exige que «el modelo no debe saber si los datos vinieron de HTTP o de
archivos». Un dato nuevo del servicio es un archivo nuevo del paquete.

**Alternativa**: deducir dónde está cada llave leyendo los objetos de cada sala, que sin conexión
ya están en disco. Sale gratis y funciona con el paquete actual, pero crea un segundo camino para
el mismo dato: si alguna vez discrepa del que devuelve el servicio, el resultado con red y sin red
deja de coincidir y `FR-015` se rompe en silencio.
