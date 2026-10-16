# Incumplimientos de los enunciados

Este documento recopila únicamente los faltantes o incumplimientos detectados durante la revisión del proyecto.

## Antes de comenzar: acceso al API

### Manejo incompleto de excepciones de red

- **Requisito:** usar un tiempo de espera explícito y reportar los errores de red con contexto, sin permitir que una excepción de red termine el programa sin explicación.
- **Ubicación:** `datos/cliente_api.py`, método `ClienteAPI._solicitar()` (líneas 49-60).
- **Incumplimiento:** el cliente convierte `Timeout` y `ConnectionError` en `CriptaAPIError`, pero no captura las demás excepciones derivadas de `requests.exceptions.RequestException`. Por ejemplo, `ChunkedEncodingError` (respuesta interrumpida o truncada), `ContentDecodingError` y `TooManyRedirects` salen del cliente sin normalizar. El controlador tampoco captura estas excepciones específicas, por lo que pueden interrumpir la ejecución en lugar de producir un error contextual controlado.
- **Comprobación realizada:** al simular `requests.exceptions.ChunkedEncodingError`, `ClienteAPI.listar_criptas()` propagó directamente `ChunkedEncodingError` y no `CriptaAPIError`.
- **Pendiente sugerido:** después de los manejadores específicos, capturar `requests.exceptions.RequestException` y convertirla en `CriptaAPIError`, incluyendo el método, la URL y el detalle original. Agregar una prueba que confirme que una excepción de red distinta de timeout/conexión no escapa del cliente.

## 1. Propósito del proyecto

### Evidencia empírica incompleta para decisiones centrales

- **Requisito:** las estructuras de datos elegidas deben estar implementadas y su elección debe justificarse con mediciones propias; que el programa funcione o que solo se indique su complejidad teórica no es suficiente.
- **Incumplimiento:** existe evidencia reproducible para inventario/lista doble, historial, bitácora/cola circular, ordenamientos, replay y agenda, pero no para todas las decisiones centrales que ya usa la aplicación. En particular, el modo oficial `python main.py --bench` no mide búsquedas de caché, recuperación de fichas desalojadas ni operaciones de guardado/carga. Tampoco se encontró una medición que sustente el índice ordenado de la caché o el uso de `TablaHashImpl` en `CatalogoPartida`.
- **Comprobación realizada:** se ejecutó `python3 main.py --bench`; generó 463 filas, pero sus tipos de medición se limitan a agenda, bitácora, historial, inventario, ordenamiento, replay y ciclo de simulación. No produjo mediciones de caché, recuperación de fichas, tabla hash ni guardado/carga.
- **Evidencia del propio proyecto:** `docs/README_integrante3.md` (líneas 82-83 y 227-228) reconoce explícitamente que faltan proveedores de benchmarks para caché, recuperación de fichas y guardado/carga. `docs/comparacion_binario_json.md` contiene resultados de persistencia, pero no se encontró el script que los genera ni están integrados en `--bench`, por lo que no son reproducibles desde el proyecto actual.
- **Pendiente sugerido:** incorporar esos subsistemas a `--bench`, guardar resultados reproducibles y relacionarlos en la documentación con cada estructura elegida y al menos una alternativa pertinente. Incluir entorno, tamaños, repeticiones, método de medición y una conclusión coherente con los datos.

## 3. El servicio web

El incumplimiento «Manejo incompleto de excepciones de red», documentado en «Antes de comenzar: acceso al API», también incumple §3.1 porque algunas excepciones de `requests` pueden terminar la operación sin convertirse en un mensaje contextual del cliente.

### La espera de una respuesta 429 no siempre respeta `reintentar_en`

- **Requisito:** ante una respuesta HTTP 429, esperar el tiempo indicado por `reintentar_en` y volver a intentar la solicitud sin que el programa se caiga.
- **Ubicación:** `datos/cliente_api.py`, método `ClienteAPI._solicitar()` (líneas 70-85), especialmente `_MAX_ESPERA = 30` y la aplicación de `min(..., self._MAX_ESPERA)`.
- **Incumplimiento:** el cliente limita la espera a 30 segundos. Si el servicio indica, por ejemplo, `reintentar_en: 45`, el programa espera solo 30 segundos antes de reintentar, en vez del tiempo indicado por el servidor.
- **Comprobación realizada:** se simuló una respuesta 429 con `reintentar_en: 45`, seguida de una respuesta 200. La llamada a `time.sleep` recibió `30`, no `45`. Además, `tests/test_datos/test_cliente_api.py::TestError429::test_espera_maxima_30` codifica expresamente este comportamiento usando `reintentar_en: 999` y esperando una pausa de 30 segundos.
- **Pendiente sugerido:** validar que `reintentar_en` sea un número no negativo y esperar ese valor, sin sustituirlo por un máximo local distinto. Mantener un límite de reintentos puede producir un error controlado si el 429 persiste, pero cada reintento efectuado debe respetar la espera indicada.

### Los fallos HTTP del catálogo pueden perder su contexto

- **Requisito:** cualquier código HTTP distinto de 200 y 429 debe reportarse con un mensaje comprensible que incluya la operación que falló.
- **Ubicación:** `service/repositorio_catalogo.py`, métodos `RepositorioCatalogo._resolver_desde_red()` (líneas 59-73) y `RepositorioCatalogo.resolver_lote()` (líneas 111-127).
- **Incumplimiento:** ambos métodos capturan `Exception` y descartan el error sin reportarlo. Aunque `ClienteAPI` construya un `CriptaAPIError` con código, método y URL, el repositorio puede convertirlo silenciosamente en `None` o en un resultado incompleto. Durante el arranque, esto termina manifestándose como una ficha ausente, sin conservar la operación HTTP que falló.
- **Comprobación realizada:** se hizo que `obtener_catalogo()` lanzara `CriptaAPIError("Error 503 en operación GET https://ejemplo.invalid/catalogo")`; `RepositorioCatalogo.resolver("ficha-ausente")` devolvió `None` y no propagó ni reportó el error contextual.
- **Pendiente sugerido:** capturar únicamente los errores para los que exista una recuperación real. Si no hay una copia válida en memoria o disco que permita resolver todas las fichas solicitadas, propagar un error contextual que conserve el código y la operación HTTP originales.

## 3.4 Características del servicio que condicionan el diseño

### El presupuesto no se reinicia en todas las partidas nuevas

- **Requisito:** `presupuesto_solicitudes` pertenece a la cripta y debe respetarse de forma independiente en cada partida.
- **Ubicación:** `controller/controlador_juego.py`, métodos `ControladorJuego._preparar_nueva_partida()` (líneas 233-239) y `ControladorJuego.procesar_comando()` en la rama `cripta` (líneas 326-336); `service/inicializador_partida.py`, función `establecer_presupuesto()` (líneas 85-94).
- **Incumplimiento:** el contador se sustituye por uno nuevo únicamente al volver explícitamente al menú o cuando la partida anterior ya terminó. La rama que inicia una cripta permite hacerlo con `anterior is None` —por ejemplo, después de un arranque fallido— o reemplazar una partida activa cuyo historial aún esté vacío, pero en esos caminos no llama a `_preparar_nueva_partida()`. `establecer_presupuesto()` cambia el límite leído de la nueva cripta, pero conserva `_intentos`; por tanto, solicitudes de un intento o una partida anterior pueden descontarse del presupuesto de la nueva.
- **Comprobación realizada:** se siguieron ambas rutas del controlador y se verificó que `PresupuestoSolicitudes.establecer_limite()` solo asigna `_limite` y no reinicia `_intentos`. Las pruebas existentes cubren el reinicio mediante una llamada explícita a `_preparar_nueva_partida()`, pero no los caminos anteriores.
- **Pendiente sugerido:** centralizar el comienzo de una partida en una operación que cree su contador de presupuesto antes de realizar las solicitudes que deban pertenecer a ella. Aplicarla también al reintentar después de una inicialización fallida y al reemplazar una partida todavía sin acciones, sin vaciar la caché global compartida entre criptas.

## 4.6 Pergaminos de retroceso e historial reversible

### Los cambios posicionales pueden fallar después de un traslado irreversible de pergamino

- **Requisito:** deshacer debe restaurar completamente el estado anterior a la última acción, mientras que recoger, soltar y consumir pergaminos debe quedar excluido del estado reversible.
- **Ubicación:** `logica/cambios.py`, clase `CambioLista`, especialmente `deshacer()` (líneas 264-273); `logica/reglas_combate.py`, método `ReglasCombate.procesar_muerte()` (línea 44); y `logica/motor_juego.py`, exclusión de pergaminos al recoger o soltar (líneas 502-524).
- **Incumplimiento:** `CambioLista` identifica una inserción reversible únicamente por el índice numérico que tenía al registrarse y la deshace mediante `lista.pop(posicion)`. Un traslado posterior de pergamino se excluye correctamente del historial, pero puede desplazar los índices de esa misma lista. Al retroceder después la acción anterior, el índice guardado puede estar fuera de rango o señalar otro elemento. En consecuencia, el historial no siempre puede restaurar el resto del estado mientras conserva irreversible el traslado del pergamino.
- **Comprobación realizada:** se preparó una sala cuyo suelo contenía un pergamino, seguida de un enemigo con un objeto de botín. El jugador tenía otro pergamino. (1) Matar al enemigo agregó el botín después del pergamino y registró esa posición. (2) Recoger el pergamino del suelo desplazó el botín, sin registrar el traslado por tratarse de un pergamino. (3) El primer retroceso consumió ese pergamino y deshizo correctamente su acción de recogida, dejándolo consumido. (4) Al consumir el segundo pergamino para deshacer el ataque, `CambioLista.deshacer()` intentó ejecutar `pop(1)` sobre el suelo `[botín]` y produjo `IndexError: pop index out of range`. El enemigo y su botín no regresaron al estado anterior y la transacción permaneció parcialmente procesada.
- **Riesgo adicional:** `TransaccionAccion.revertir()` elimina cada registro inmediatamente después de aplicarlo. Si un inverso posterior falla, los inversos anteriores ya ejecutados no se recuperan y sus registros ya no están en la transacción, por lo que el estado puede quedar parcialmente retrocedido.
- **Cobertura existente:** las 130 pruebas dirigidas de historial, cambios, pergaminos, agenda, efectos, trampas e inventario pasan, pero no incluyen una modificación irreversible de pergamino que desplace un elemento administrado por `CambioLista` de una acción anterior.
- **Pendiente sugerido:** no identificar elementos mutables solo por un índice histórico. Guardar la identidad del elemento y referencias u órdenes estables de vecinos, como ya se hace en los cambios especializados del inventario y del suelo, y validar todas las inversas antes de modificar la transacción. El retroceso debe ser atómico o conservar suficientes registros para restaurar lo ya deshecho si una inversa inesperada falla.

## 4.7 El rastro del jugador

### El procesamiento de varios rastreadores puede crecer cuadráticamente

- **Requisito:** con varios rastreadores, el trabajo total por ciclo no debe crecer más que linealmente con la cantidad de enemigos que realmente actúan.
- **Ubicación:** `logica/motor_juego.py`, método `MotorJuego._turno_enemigo()` (líneas 577-607), especialmente la comprobación de pertenencia de las líneas 579-581 y el recorrido para retirar un enemigo de su sala de las líneas 595-600; `dto/sala.py`, atributo `Sala.enemigos` (línea 28).
- **Incumplimiento:** antes de tomar la decisión de cada enemigo, `_turno_enemigo()` ejecuta `any(...)` sobre toda la lista `sala.enemigos` para comprobar que la instancia pertenece a ella. Si `n` rastreadores de una sala actúan en un ciclo, estas búsquedas realizan en conjunto `1 + 2 + ... + n = O(n²)` visitas según sus posiciones. Cuando un rastreador se mueve, además se vuelve a recorrer la lista para localizarlo y `pop()` desplaza los elementos posteriores, ambos O(n), reforzando el crecimiento cuadrático.
- **Comprobación realizada:** se instrumentó la iteración de `Sala.enemigos` y se ejecutó un turno de cada rastreador activo, sin puertas para aislar el costo de validación. Con 10, 100 y 300 rastreadores se observaron respectivamente 55, 5.050 y 45.150 visitas a elementos, exactamente `n(n+1)/2`. La decisión de rastro en sí no recorrió el mapa ni el historial.
- **Cobertura existente:** las 81 pruebas dirigidas de rastro, mapa, comportamiento e integración pasan. Comprueban vecindad local, caducidad, desempate y reversión, pero no miden el trabajo agregado de muchos enemigos actuando en el mismo ciclo.
- **Pendiente sugerido:** representar la pertenencia de enemigos con un índice por identidad o ID y una colección que permita retirar un nodo conocido en O(1), por ejemplo una tabla hash `id_actor → nodo` combinada con una lista doble para conservar el orden estable. Así la validación, extracción y traslado dejan de recorrer todos los enemigos; el trabajo propio de las decisiones pasa a ser proporcional a los actores que actúan y a la suma de sus cantidades de salidas.

## 4.9 Ordenamiento

### El índice del archivo de guardado usa el ordenamiento prohibido de Python

- **Requisito:** los índices del archivo de guardado son uno de los contextos evaluados y no se permite utilizar `list.sort()` ni `sorted()` para esos ordenamientos.
- **Ubicación:** `datos/guardado_binario.py`, método `GuardadoBinario._guardar()`, especialmente la construcción y ordenamiento de `offsets_salas` (líneas 141-151).
- **Incumplimiento:** después de reunir los pares `(id_sala, offset)`, el guardado ejecuta directamente `offsets_salas.sort(...)`. Por tanto, el índice utilizado luego para búsqueda binaria no se ordena con ninguno de los dos algoritmos propios ni con la selección adaptativa requerida.
- **Comprobación realizada:** la búsqueda global de `sorted(` y `.sort(` en la implementación encontró el uso de producción de la línea 148. Los demás usos aparecieron en pruebas, benchmarks o en el descubrimiento de archivos offline, pero este corresponde exactamente al contexto «índices del archivo de guardado» nombrado en §4.9. Las 91 pruebas dirigidas de ordenamiento, puntajes, inventario, guardado y catálogo pasan porque verifican resultados y formato, no la prohibición del algoritmo de biblioteca.
- **Pendiente sugerido:** ordenar `offsets_salas` mediante `OrdenadorAdaptativo().ordenar(...)` con el ID de sala como criterio antes de escribir el índice. Agregar una prueba de integración que sustituya o prohíba `list.sort()`/`sorted()` en esta ruta y confirme que el índice sigue ordenado y permite la búsqueda binaria.

## 4.10 Guardado binario de la partida

### La comparación contra JSON no es reproducible desde el proyecto

- **Requisito:** comparar el tamaño en disco y el tiempo de carga del mismo estado guardado en el formato binario propio y en JSON.
- **Ubicación:** `docs/comparacion_binario_json.md`; modo `--bench` de `main.py` y contenido del directorio `benchmarks/`.
- **Incumplimiento:** el documento publica tamaños y tiempos para ambos formatos, pero el proyecto no contiene el programa que genera el estado medido, lo serializa de las dos maneras y ejecuta las 500 iteraciones indicadas. Tampoco incluye archivos de resultados crudos. Por ello no puede repetirse ni comprobarse que las dos mediciones correspondan exactamente al mismo estado. Este caso ya forma parte del incumplimiento general «Evidencia empírica incompleta para decisiones centrales» registrado en §1.
- **Comprobación realizada:** se buscaron proveedores de benchmark, serializadores JSON comparables y referencias a `comparacion_binario_json`; solo se encontró la tabla Markdown. Los únicos programas bajo `benchmarks/` corresponden a integrante 1 y a `integrante3.py`, y `python3 main.py --bench` no mide guardado ni carga. El propio `docs/README_integrante3.md` (líneas 227-228) indica que todavía deben aportarse los benchmarks de guardado/carga.
- **Pendiente sugerido:** agregar un benchmark ejecutable que construya una partida determinista, materialice ese mismo estado lógico en binario y JSON, registre los bytes de ambos archivos y mida por separado carga completa y recuperación de una sala. Debe informar entorno, repeticiones, calentamiento y resultados crudos o exportables, e integrarse en `--bench`.

## 4.11 Bitácora de partida y reproducción

### El registro de acciones es opcional y las partidas normales pueden quedar sin bitácora

- **Requisito:** cada acción del jugador debe registrarse en un archivo de texto de solo anexado, para que la reproducción sea el mecanismo principal de reporte y repetición de errores.
- **Ubicación:** `service/juego_service.py`, atributos iniciales `_ruta_registro = None` y método `iniciar_partida()` (líneas 33 y 128-130), método `_cerrar_accion()` (líneas 590-606) y método `iniciar_registro()` (líneas 614-647); `controller/controlador_juego.py`, comando opcional `registro RUTA` (líneas 313-320 y 337-341).
- **Incumplimiento:** una partida recién iniciada no crea ni conecta ningún log. `_cerrar_accion()` solo anexa cuando `_ruta_registro` ya fue configurada mediante el comando técnico `registro RUTA`, que el jugador debe ejecutar antes de la primera acción. Si no lo hace, las acciones se ejecutan normalmente y no queda archivo reproducible. La vista gráfica tampoco ofrece ese comando dentro de su interacción habitual, aunque utiliza el mismo servicio con el registro desactivado por defecto.
- **Comprobación realizada:** se inició una partida nueva mediante `JuegoService`, se ejecutó exitosamente un ataque y se comprobó que `tiene_registro()` seguía devolviendo `False` y que no se había creado ningún archivo `.log`. La búsqueda de llamadas de producción a `iniciar_registro()` encontró únicamente la rama explícita `registro` del controlador; las demás llamadas pertenecen a pruebas.
- **Cobertura existente:** las 114 pruebas dirigidas de registro, replay, inicialización y conexión aprobaron. Verifican correctamente el comportamiento cuando el registro se activa de forma explícita, pero no exigen que toda partida jugable lo active automáticamente.
- **Pendiente sugerido:** crear y conectar automáticamente un log con nombre único al publicar cada partida nueva reproducible, antes de aceptar la primera acción, tanto en consola como en la vista gráfica. El comando podría permitir elegir anticipadamente la ruta, pero no debería ser necesario para obtener la bitácora obligatoria. Si no puede crearse el archivo, debe bloquearse el comienzo o informarse claramente que no se puede garantizar el registro, en vez de continuar silenciosamente sin replay.

## 5.1 Presupuesto de red por cripta

El incumplimiento «El presupuesto no se reinicia en todas las partidas nuevas», documentado en §3.4, también incumple este punto: determinadas rutas que comienzan o reintentan una cripta conservan intentos de la partida anterior, por lo que el máximo deja de aplicarse independientemente a cada partida.

### El modo offline no reporta las solicitudes y el presupuesto declarado

- **Requisito:** las lecturas locales deben contar como cero solicitudes de red y, al finalizar la partida, el programa debe reportar solicitudes realizadas y `presupuesto_solicitudes`.
- **Ubicación:** `service/inicializador_partida.py`, funciones `establecer_presupuesto()` y `crear_repositorio()` (líneas 75-94); `service/juego_service.py`, método `obtener_metricas()` (líneas 401-413); `datos/fuente_offline.py`, clase `FuenteOffline`.
- **Incumplimiento:** `establecer_presupuesto()` retorna inmediatamente si la fuente no es `ClienteAPI`. `FuenteOffline` tampoco conserva un contador o el límite leído de `generales.json`. En consecuencia, `obtener_metricas()` omite por completo la sección `presupuesto` en modo offline, en lugar de reportar cero solicitudes frente al presupuesto declarado por la cripta. Las lecturas locales no se cuentan —lo cual es correcto—, pero tampoco se presenta la métrica obligatoria.
- **Comprobación realizada:** se inició `cripta-01` desde `tests/fixtures/api_real` mediante `FuenteOffline`. Sus datos generales declaran `presupuesto_solicitudes = 9`, pero `servicio.obtener_metricas()` no contenía la clave `presupuesto`; solo publicó caché y partida.
- **Pendiente sugerido:** mantener métricas de presupuesto separadas del transporte. Al preparar una cripta offline, registrar su límite declarado y exponer `intentos = 0`, `limite = presupuesto_solicitudes` y `restantes = limite`, sin convertir lecturas de archivos en solicitudes.

### Los aciertos y fallos de caché reportados se acumulan entre partidas

- **Requisito:** al finalizar la partida se deben reportar sus aciertos y fallos de caché, junto con las solicitudes y el presupuesto de esa partida.
- **Ubicación:** `logica/cache_catalogo.py`, contadores `_aciertos` y `_fallos` y método `metricas()` (líneas 40-44 y 122-135); `controller/controlador_juego.py`, métodos `_preparar_nueva_partida()` y `lineas_metricas()` (líneas 177-196 y 233-238).
- **Incumplimiento:** la caché se conserva deliberadamente entre partidas para aprovechar datos calientes, pero sus contadores no se reinician ni se toma una línea base al comenzar una nueva. El reporte final muestra los totales acumulados de toda la vida de esa instancia de caché, no los aciertos y fallos producidos por la partida que acaba de terminar. Esto impide comparar correctamente una partida fría con una caliente y atribuir sus solicitudes a sus propios resultados.
- **Comprobación realizada:** al iniciar dos veces `cripta-01` con el mismo servicio y la misma caché, la primera partida dejó `0` aciertos y `11` fallos. La segunda realizó 11 consultas resueltas en memoria y ningún fallo nuevo, pero `obtener_metricas()` reportó `11` aciertos y `11` fallos (`22` totales), en vez de las métricas propias de la segunda partida: `11` y `0`.
- **Pendiente sugerido:** conservar la caché caliente, pero guardar una línea base de sus contadores al comenzar cada partida y reportar diferencias al finalizar. Alternativamente, reiniciar solo los contadores, nunca el contenido ni el orden LRU.

## 5.3 Modo de medición

### `--bench` omite caché, recuperación de fichas liberadas y guardado/carga

- **Requisito:** la bandera `--bench` debe ejecutar cargas sintéticas y reportar tiempos por subsistema; como mínimo debe medir agenda, búsquedas de caché, recuperación de fichas liberadas, inventario, historial de retroceso, ordenamientos y las operaciones de guardado/carga documentadas.
- **Ubicación:** `main.py`, rama `config.bench` (líneas 35-39); `benchmarks/integrante3.py`, función `ejecutar()`; `docs/README_integrante3.md` (líneas 78-83 y 227-228). Este faltante ya forma parte del incumplimiento general «Evidencia empírica incompleta para decisiones centrales» registrado en §1.
- **Incumplimiento:** el ejecutor común incluye agenda, inventario, historial y ordenamientos, además de bitácora, replay y un ciclo de simulación, pero no contiene proveedores para:
  - buscar fichas presentes y ausentes en `CacheCatalogo`;
  - expulsar una ficha y recuperarla desde `AlmacenPersistente`, diferenciándola de una solicitud de red;
  - guardar y cargar el estado binario, incluida la recuperación directa de una sala;
  - comparar esas operaciones de persistencia con el JSON usado como alternativa documentada.
- **Comprobación realizada:** se ejecutó `python3 main.py --bench` y se analizaron sus 463 filas. Los únicos nombres de medición fueron `agenda_extraer_eventos`, operaciones de inventario, historial y ordenamiento, bitácora, parser de replay, alternativa de lista y ciclo de simulación. No apareció ningún nombre relacionado con `cache`, `ficha`, `liberada`, `guardado` o `carga`. Las cuatro pruebas actuales del ejecutor de benchmarks aprobaron, pero solo exigen los proveedores ya conectados.
- **Evidencia del proyecto:** `docs/README_integrante3.md` reconoce expresamente que faltan los proveedores de caché, recuperación de fichas y guardado/carga. `docs/comparacion_binario_json.md` publica cifras de persistencia, pero no está integrado en `--bench` ni tiene un generador reproducible dentro del proyecto.
- **Pendiente sugerido:** añadir proveedores reproducibles a `benchmarks/integrante3.py` para los tres grupos ausentes. Deben preparar los datos fuera del intervalo cronometrado, usar varios tamaños y repeticiones, comprobar el resultado de cada operación y etiquetar por separado acierto/fallo de caché, recuperación desde disco/red, guardado, carga completa y lectura parcial de sala. Incorporar pruebas que exijan la presencia de todos los subsistemas mínimos en la salida de `--bench`.

## 7. Restricciones de implementación

El incumplimiento «El índice del archivo de guardado usa el ordenamiento prohibido de Python», documentado en §4.9, también incumple este punto: `offsets_salas.sort(...)` sustituye el algoritmo propio por una implementación de biblioteca en uno de los problemas evaluados. Los usos de `sorted()` en pruebas y como alternativa de benchmark no forman parte de la solución seleccionada.

### La carga y reconstrucción de salas utiliza diccionarios como índices propios

- **Requisito:** solo pueden leerse como tales los diccionarios recibidos desde JSON; no se permite crear `dict` como índice, tabla de búsqueda o estructura propia para resolver los problemas de §4.
- **Ubicación:** `datos/fuente_offline.py`, método `obtener_contenido()` (líneas 62-70); `datos/decodificador_datos.py`, métodos `_adaptar_contenido_externo()` y `convertir_contenido()` (líneas 86-175); `datos/guardado_binario.py`, método `cargar()` (líneas 598-609); `service/restaurador_partida.py`, método `_reconstruir_mapa()` (líneas 138-155).
- **Incumplimiento:** estas rutas crean diccionarios nuevos indexados por `id_sala`, no se limitan a leer objetos producidos por `response.json()`:
  - `FuenteOffline` construye `registros = {}`, inserta `registros[id_sala]` y luego recupera cada sala mediante `registros[s]`;
  - `DecodificadorDatos` construye `adaptado` o `resultado`, detecta IDs repetidos con pertenencia por clave y publica `contenido[id_sala]`;
  - la carga binaria construye `salas = {}` y almacena cada registro como `salas[id_sala]`;
  - el restaurador consulta después `contenido[id_sala]` para asociar cada sala con enemigos y objetos.
  Esos diccionarios funcionan explícitamente como tablas de búsqueda para contenido y reconstrucción, problemas evaluados en precarga/carga y guardado.
- **Comprobación realizada:** se siguieron las asignaciones y consultas anteriores en las rutas normales offline y de restauración. Las 100 pruebas dirigidas de fuente offline, decodificador, guardado, repositorio, restauración y estructuras aprobaron, pero verifican el resultado funcional y no prohíben estos índices de biblioteca.
- **Pendiente sugerido:** usar una estructura propia ya disponible —por ejemplo `TablaHashImpl` si se necesita acceso por ID— o listas de pares con búsqueda explícita cuando el volumen transitorio no justifique un índice. Los diccionarios originales del JSON pueden seguir leyéndose como registros, pero no deben reorganizarse en otro `dict` para indexarlos.

### La resolución y restauración de fichas crea tablas de búsqueda con `dict`

- **Requisito:** no se permite usar `dict` como índice, caché o tabla de búsqueda para las entidades del catálogo; la excepción para JSON no cubre estructuras nuevas creadas por la aplicación.
- **Ubicación:** `service/repositorio_catalogo.py`, método `resolver_lote()` y su `fallback_disco` (líneas 75-135); `service/juego_service.py`, método `_fichas_del_estado()` (líneas 185-213); `service/restaurador_partida.py`, método `_completar_v5()` (líneas 332-352); `datos/decodificador_datos.py`, método `_buscar_ficha()` (líneas 9-27).
- **Incumplimiento:** aunque la caché LRU principal y `CatalogoPartida` sí usan estructuras propias, otras rutas crean índices auxiliares prohibidos:
  - `fallback_disco[ficha_id]` conserva y recupera fichas persistidas incompatibles durante la resolución por lotes;
  - `_fichas_del_estado()` construye `fichas[ficha_id] = ficha` para validar un guardado;
  - `_completar_v5()` vuelve a construir `fichas = {}` y enlaza actores, objetos y trampas mediante acceso directo por ID;
  - `_buscar_ficha()` admite esos diccionarios y ejecuta `fichas[ficha_id]`.
  Son tablas creadas por el programa y usadas para resolver referencias del catálogo, no simples objetos JSON leídos del servidor.
- **Comprobación realizada:** `JuegoService.guardar_partida()` pasa el índice producido por `_fichas_del_estado()` a `RestauradorPartida.restaurar_para_reanudar()`; allí cada ID se resuelve y se vuelve a insertar en otro diccionario antes de asignarse mediante clave. La ruta de fallback del repositorio también usa pertenencia y acceso por clave sobre su diccionario auxiliar.
- **Pendiente sugerido:** reutilizar `CatalogoPartida`/`TablaHashImpl` durante validación y restauración, o mantener pares en listas y resolverlos explícitamente. El diccionario que representa una ficha individual puede mantenerse como registro JSON; lo prohibido aquí es el diccionario exterior `ID → ficha` usado como índice.

### Se usa `set` de biblioteca para detectar duplicados en rutas evaluadas

- **Requisito:** las estructuras empleadas para resolver los problemas de §4 deben ser propias; solo se autoriza expresamente `list` como almacenamiento contiguo de bajo nivel, no `set`.
- **Ubicación:** `service/juego_service.py`, método `conectar_inventario()` (línea 157); `service/restaurador_partida.py`, método `_vincular_eventos()` (línea 472).
- **Incumplimiento:** `len(set(ids))` valida unicidad de objetos del inventario y `len(set(efecto["eventos"]))` valida IDs de eventos al restaurar un guardado. En ambos casos se delega la detección de duplicados a la tabla hash de biblioteca dentro de operaciones de inventario, agenda y persistencia evaluadas.
- **Comprobación realizada:** la búsqueda global encontró solo esos dos usos de `set` en las rutas de modelo/servicio; los demás aparecen en pruebas, benchmarks o en Pygame para tareas de presentación. No se encontraron `heapq`, `bisect`, `deque`, `OrderedDict` ni colas de biblioteca en la implementación de las estructuras principales.
- **Pendiente sugerido:** realizar la validación mediante `TablaHashImpl` o, para colecciones pequeñas, con una lista auxiliar y comprobación explícita de pertenencia. Agregar una prueba estática que impida introducir `dict`, `set`, `heapq`, `bisect`, `deque`, `.sort()` o `sorted()` en las rutas evaluadas, con excepciones delimitadas para registros JSON y código de interfaz/benchmark.
