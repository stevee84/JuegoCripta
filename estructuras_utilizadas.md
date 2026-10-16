# Estructuras de datos utilizadas

Este documento registra, para cada punto revisado del enunciado:

- la estructura de datos utilizada;
- dónde y cómo se utiliza;
- por qué resulta adecuada para el requisito;
- por qué se prefirió frente a otras estructuras pertinentes;
- y, cuando corresponda, la estructura sugerida para corregir una elección inadecuada.

Las secciones se agregarán con el mismo número de punto del enunciado.

## 4. Problemas de estructuras de datos a resolver

### 4.1 Qué ocurre a continuación

**Evaluación: estructura adecuada.**

#### Estructuras utilizadas

La agenda combina las siguientes estructuras:

1. **Montículo mínimo binario indexado** (`MonticuloMinimo`).
   - Está implementado sobre un arreglo de Python en `estructuras/monticulo_minimo.py`.
   - Cada `Evento` conserva su posición actual en `_indice_monticulo`.
   - La prioridad se compara como la tupla `(tiempo, secuencia)` en `dto/evento.py`.
2. **Tres índices AVL** (`IndiceOrdenado`) dentro de `logica/agenda_eventos.py`:
   - `_por_id`: localiza un evento por `id_evento`.
   - `_por_prioridad`: impide prioridades `(tiempo, secuencia)` duplicadas.
   - `_por_destinatario`: agrupa mediante claves `(destinatario_id, id_evento)` los eventos de cada actor.
3. **Lista de IDs por efecto** en el campo `efecto["eventos"]` de `logica/gestor_efectos.py`.
   - Permite cancelar únicamente los eventos pertenecientes a ese efecto.

#### Dónde y cómo se utilizan

- `AgendaEventos.ver_siguiente()` consulta la raíz del montículo en **O(1)**.
- `AgendaEventos.extraer_siguiente()` retira la raíz y reordena el montículo en **O(log n)**; no examina todos los eventos.
- Programar un evento lo inserta en el montículo y en los tres AVL, con costo total **O(log n)**.
- Cancelar por ID primero consulta `_por_id` y después elimina la referencia conocida del montículo mediante `_indice_monticulo`, todo en **O(log n)**.
- Al morir un actor, `AgendaEventos.cancelar_por_actor()` obtiene desde `_por_destinatario` solo sus `k` eventos en **O(log n + k)** y cancela cada uno en **O(log n)**. No recorre los eventos de otros actores.
- Un efecto conserva los IDs de sus propios eventos; su cancelación elimina solo esos eventos mediante el índice de la agenda.
- Una reprogramación cancela y vuelve a insertar el mismo evento en **O(log n)**, actualizando su tiempo y asignándole una secuencia nueva.
- Los intercambios del montículo actualizan siempre `_indice_monticulo`, por lo que una cancelación o reprogramación no necesita buscar linealmente la posición del evento.

#### Por qué es adecuada

- El montículo está especializado en la operación dominante: consultar y extraer repetidamente el evento mínimo.
- La comparación `(tiempo, secuencia)` produce el orden total determinista exigido, incluso cuando varios eventos comparten tiempo.
- Los índices complementan al montículo precisamente en sus operaciones débiles: búsqueda por ID, cancelación arbitraria y consulta por actor.
- La eliminación física evita que eventos de actores muertos o efectos cancelados permanezcan acumulados como entradas obsoletas.
- La solución mantiene costos logarítmicos con cientos de eventos y decenas de miles de operaciones. Como comprobación, `python3 -m benchmarks.benchmark_agenda_integrante1` extrajo 10 000 eventos en aproximadamente **0,145 s** en el entorno revisado. Además, las 36 pruebas dirigidas de montículo, agenda, velocidad, cancelación y reprogramación finalizaron correctamente.

#### Por qué no se utilizaron otras estructuras

- **Lista o arreglo sin ordenar:** insertar sería barato, pero encontrar cada mínimo costaría **O(n)**, contrario al requisito principal.
- **Lista o arreglo ordenado:** permitiría consultar un extremo en O(1), pero cada inserción o reprogramación podría desplazar **O(n)** elementos.
- **Cola FIFO:** ordenaría por llegada, no por `(tiempo, secuencia)`, y no admitiría correctamente eventos futuros con tiempos distintos.
- **Pila:** procesa en orden inverso de inserción y no representa una agenda temporal.
- **Solo un árbol AVL por prioridad:** sería una alternativa válida con operaciones O(log n), pero no ofrece la consulta O(1) del mínimo propia del montículo y seguiría necesitando índices adicionales para ID y destinatario.
- **Solo una tabla hash:** puede localizar IDs con costo promedio O(1), pero no permite obtener eficientemente el evento de menor prioridad ni consultar por rango de destinatario. Los AVL elegidos ofrecen además límite O(log n) en el peor caso.
- **Montículo con cancelación perezosa:** marcar eventos como inválidos simplifica la cancelación, pero deja entradas obsoletas. Una extracción podría tener que descartar muchas de ellas y la memoria crecería hasta limpiar el montículo. El montículo indexado garantiza eliminación física O(log n).

#### Sugerencia

No se requiere sustituir la estructura. Conviene conservar sincronizados el montículo y los tres índices mediante una única interfaz de agenda, como ya se hace, y mantener pruebas de invariantes para detectar cualquier divergencia entre ellos.

### 4.2 Traer el contenido antes de que haga falta

**Evaluación: parcialmente adecuada; la estructura prevista no está integrada y faltan estados de solicitud.**

#### Estructuras utilizadas actualmente

1. **Grafo mediante listas de adyacencia.**
   - `MapaCripta` guarda las salas en una lista `_salas`.
   - Cada `Sala` guarda sus conexiones en la lista `puertas` y cada `Puerta` mantiene una referencia `destino_sala` una vez vinculado el esqueleto.
   - Esta representación permite recorrer vecinos usando solo las puertas de la sala actual.
2. **Listas auxiliares para la carga inicial.**
   - `InicializadorPartida._construir()` reúne IDs de salas, registros recibidos y salas vistas en las listas `ids_salas`, `registros` y `vistas`.
   - Recorre `ids_salas` en segmentos de diez y solicita sincrónicamente el contenido de todas las salas antes de publicar la partida.
3. **Planificación BFS aislada.**
   - `PlanificadorPrecarga` contiene una búsqueda en anchura por niveles mediante las listas `frontera`, `siguiente`, `visitados` y `resultado`.
   - `_cargadas` es una lista de IDs usada para evitar solicitudes repetidas.
   - `solicitar_lote()` divide en segmentos de diez.
   - Esta clase solo aparece conectada en pruebas; no se utiliza desde `JuegoService`, `InicializadorPartida`, `ControladorJuego` ni el movimiento del motor.

#### Qué resuelve correctamente la implementación activa

- El grafo por adyacencia es adecuado para explotar el esqueleto completo y consultar vecindad sin una matriz de tamaño `salas_total²`.
- Las referencias `destino_sala` permiten recorrer vecinos locales sin buscar el mapa completo en cada paso.
- La carga inicial divide las solicitudes de contenido en lotes de hasta diez.
- Como toda la carga es síncrona y ocurre antes de entregar el estado al motor, el jugador no puede moverse mientras falte contenido. Por ello tampoco avanza el reloj virtual durante una espera de red.
- La incorporación sigue el orden determinista de los lotes y registros procesados por el inicializador.

#### Problemas de la estructura y su integración

1. **El planificador no forma parte de la ejecución real.** La aplicación no realiza una precarga gradual por cercanía: descarga el contenido de todas las salas durante cada inicialización. Esto evita pausas en puertas, pero desaprovecha la estrategia BFS implementada y puede consumir muchas solicitudes al iniciar criptas grandes.
2. **No existe una tabla de estados por sala.** No se representa explícitamente `NO_SOLICITADA`, `PENDIENTE`, `DISPONIBLE` o `FALLIDA`. Las listas vacías de una `Sala` tampoco permiten distinguir entre “contenido vacío” y “contenido todavía desconocido”.
3. **No se modelan respuestas pendientes.** No hay una estructura que asocie una sala con su solicitud en curso, ni una cola que determine el orden en que deben incorporarse respuestas concurrentes. La ejecución actual es determinista porque bloquea y procesa todo secuencialmente, pero no soportaría el caso pendiente exigido si se habilitara precarga en segundo plano.
4. **`_cargadas` y `visitados` son listas.** Comprobar `id in lista` cuesta O(n). En BFS se repite esa comprobación para cada arista; en el peor caso puede degradar el recorrido hacia O(V·E). También permite que la deduplicación de solicitudes empeore conforme crece la cripta.
5. **La búsqueda global de salas es lineal.** `MapaCripta.obtener_sala()` recorre `_salas`, por lo que localizar repetidamente IDs durante planificación cuesta O(V).
6. **La deduplicación no está ligada a la versión.** `_cargadas` solo contiene IDs y vive dentro de una instancia no integrada del planificador. La ruta activa no conserva un índice de contenido por `(cripta_id, version_cripta, sala_id)`. Se comprobó que iniciar dos veces `cripta-01` con la misma versión volvió a solicitar el lote `(1, 2, 3, 4, 5, 6)` completo en ambas ocasiones.

Las 45 pruebas dirigidas de inicialización, adaptación y `PlanificadorPrecarga` pasan, pero prueban por separado el cargador total y el planificador; no demuestran que este último participe en el flujo real de movimiento.

#### Por qué algunas alternativas no son adecuadas

- **Matriz de adyacencia:** permitiría comprobar una conexión en O(1), pero consumiría O(V²) memoria en criptas normalmente dispersas y no aporta ventaja al recorrer los pocos vecinos de una sala.
- **Solo una lista de IDs cargados:** es simple, pero tiene búsquedas O(n), no guarda la versión, no representa solicitudes pendientes y no asocia el ID con su contenido.
- **Solo una cola de solicitudes:** conserva orden, pero no evita duplicados ni permite consultar en O(1) si una sala ya está disponible o pendiente.
- **Precargar siempre toda la cripta:** garantiza disponibilidad y simplifica el determinismo, pero aumenta el tiempo inicial y puede desperdiciar presupuesto en salas lejanas que nunca se visitan.
- **Incorporar respuestas apenas llegan:** reduce latencia, pero hace que el estado dependa del orden real de la red y viola el determinismo.

#### Estructura sugerida

Se recomienda integrar una estructura compuesta:

1. **Grafo por listas de adyacencia**, conservando el modelo actual de puertas y referencias locales.
2. **Índice hash de salas por ID** además de la lista de recorrido del mapa. Así `obtener_sala(id)` pasa de O(V) a O(1) promedio sin perder el orden estable de publicación.
3. **Tabla hash de contenido y estado**, con clave `(cripta_id, version_cripta, sala_id)` y un registro que contenga:
   - estado `NO_SOLICITADA`, `PENDIENTE`, `DISPONIBLE` o `FALLIDA`;
   - contenido decodificado cuando esté disponible;
   - identificador y número de orden del lote que la solicitó.
4. **Conjunto de IDs planificados** para impedir que una sala disponible o pendiente vuelva a agregarse a otro lote.
5. **Cola FIFO de lotes**, cada uno con un máximo de diez salas. El BFS agrega vecinos por distancia y la cola conserva el orden determinista de solicitud.
6. **Índice de respuestas pendientes por número de lote.** Las respuestas pueden descargarse concurrentemente, pero deben quedar almacenadas temporalmente y aplicarse al modelo solo cuando corresponda el siguiente número de lote.

Antes de confirmar un movimiento, el servicio debe consultar la tabla: si el destino está `DISPONIBLE`, mueve al jugador; si está `PENDIENTE`, espera esa respuesta sin tocar el reloj virtual; si está ausente o falló, realiza una solicitud controlada y solo confirma el movimiento después de publicar el contenido. La clave con versión permite reutilizar contenido sin mezclar datos obsoletos.

### 4.3 Resolución de referencias del catálogo

**Evaluación: adecuada para el requisito funcional, con una mejora recomendable en la deduplicación inicial.**

#### Estructuras utilizadas

1. **Lista temporal de IDs únicos.**
   - `InicializadorPartida` descubre referencias en generales, puertas, enemigos, objetos, trampas y botines.
   - `_agregar_id()` evita duplicados mediante `ficha_id not in ids_fichas`.
   - Antes de consultar la red, los IDs se ordenan de forma determinista y se dividen en lotes de hasta diez.
2. **Tabla hash propia para el catálogo de la partida.**
   - `CatalogoPartida` utiliza `TablaHashImpl`, implementada con encadenamiento separado, factor de carga máximo de 0,75 y redimensionamiento automático.
   - La clave es el ID de catálogo y el valor es la única ficha compartida por todas las instancias de ese tipo durante la partida.
3. **Caché LRU compartida entre partidas.**
   - `CacheCatalogo` combina una lista doble con un arreglo ordenado.
   - La lista doble conserva el orden de uso reciente y permite mover un nodo al frente en O(1).
   - El arreglo ordenado relaciona `ficha_id` con el nodo de la lista mediante búsqueda binaria O(log c), donde `c` es la capacidad de la caché.
   - Otro arreglo ordenado registra las fichas fijadas y sus dueños para impedir que se desalojen mientras estén en uso.
4. **Almacenamiento persistente indexado por archivo.**
   - `AlmacenPersistente` guarda cada ficha en `<ficha_id>.json`, junto con la versión global del catálogo.
   - La ruta del archivo funciona como índice persistente directo por ID.
5. **Repositorio por niveles.**
   - `RepositorioCatalogo` consulta en orden: memoria → disco con versión vigente → red.
   - `resolver_lote()` reúne únicamente los faltantes y realiza una sola consulta de red para hasta diez IDs.

#### Dónde y cómo se resuelven las referencias

- El inicializador descubre primero todos los IDs conocidos y añade después los IDs de objetos declarados en `suelta` por las fichas de enemigos.
- Cada lote se resuelve por medio de `RepositorioCatalogo`, nunca mediante una solicitud individual por cada entidad en el flujo normal de inicialización.
- Las fichas resueltas se insertan en `CatalogoPartida` y el decodificador asigna esa misma referencia a cada `Enemigo`, `ObjetoInstancia` o `Trampa` correspondiente.
- La partida no se publica si falta una ficha requerida, por lo que una entidad real no se muestra ni se simula con una referencia sin resolver.
- La caché sobrevive al cambio de cripta cuando la versión global del catálogo coincide. Si la ficha no está en memoria, el repositorio intenta recuperarla del almacenamiento persistente vigente antes de gastar red.

#### Por qué las estructuras son adecuadas

- La tabla hash de `CatalogoPartida` ofrece resolución ID→ficha en O(1) promedio, operación repetida por la vista y la simulación.
- Guardar una sola ficha por ID evita duplicar estadísticas y garantiza que distintas instancias compartan los mismos datos técnicos.
- La combinación índice + lista doble implementa una política LRU sin buscar linealmente el nodo que debe actualizarse en cada acierto.
- El límite de capacidad evita que la caché en memoria crezca sin control, mientras que el disco conserva fichas reutilizables entre criptas.
- La versión global impide mezclar fichas persistidas de catálogos diferentes en la ruta utilizada por el inicializador.
- Ordenar los IDs antes de formar lotes hace determinista el orden de las consultas aunque las referencias se descubran desde distintas salas.

#### Comprobaciones realizadas

- Dos enemigos `e-201` y `e-202` de tipo `ent_rata_gigante` resultaron ser objetos actor distintos, pero `ratas[0].ficha is ratas[1].ficha` fue verdadero.
- Los IDs enviados durante la primera inicialización de `cripta-01` no se repitieron entre lotes.
- Al iniciar nuevamente la misma cripta con la misma caché y versión, no se realizó ningún lote adicional de catálogo.
- Las 52 pruebas dirigidas de repositorio, caché, tabla hash e integración del catálogo finalizaron correctamente.

#### Por qué no se utilizaron otras estructuras

- **Una lista simple como catálogo principal:** requeriría O(n) para resolver cada ID y repetiría ese costo cada vez que la vista o el modelo consulte una ficha.
- **Una ficha copiada dentro de cada instancia:** aumentaría la memoria y permitiría inconsistencias entre instancias del mismo tipo.
- **Solicitudes individuales por ID:** desperdiciarían presupuesto y latencia, pues consultar uno cuesta prácticamente lo mismo que consultar diez.
- **Una tabla hash sin política de desalojo:** daría búsquedas rápidas, pero crecería indefinidamente al compartir el catálogo entre criptas.
- **Una cola FIFO para desalojo:** expulsaría por antigüedad de inserción, aunque una ficha se utilice con frecuencia. LRU refleja mejor la reutilización reciente.
- **Solo una lista doble para LRU:** actualizar el orden sería O(1) después de localizar el nodo, pero encontrarlo por ID exigiría recorrer toda la lista.
- **Consultar siempre el disco:** evitaría red, pero añadiría I/O a cada resolución; la caché en memoria debe ser el primer nivel.

#### Mejora sugerida

La lista `ids_fichas` deduplica con búsquedas lineales. Con `u` IDs únicos y muchas referencias repetidas, el descubrimiento puede acercarse a O(u²). Se recomienda mantener simultáneamente:

- una **lista** para conservar un orden reproducible de descubrimiento; y
- una **tabla hash o conjunto** para decidir en O(1) promedio si el ID ya fue agregado.

También sería razonable reemplazar el arreglo ordenado de `CacheCatalogo` por una tabla hash ID→nodo si la capacidad dejara de ser pequeña. La implementación actual es aceptable con la capacidad predeterminada de 25: ofrece búsqueda O(log c), orden estable y una política LRU correcta; con capacidades grandes, sus inserciones y eliminaciones O(c) serían menos convenientes que la combinación clásica tabla hash + lista doble.

### 4.4 Reutilización y caché persistente

**Evaluación: la política LRU y el nivel persistente son apropiados, pero el límite de memoria no se cumple realmente. La estructura global necesita corrección.**

#### Estructuras utilizadas

1. **Caché LRU acotada (`CacheCatalogo`).**
   - Una lista doble mantiene las fichas desde la más reciente hasta la menos reciente.
   - Un arreglo ordenado `_arreglo` relaciona cada `ficha_id` con su nodo de la lista.
   - Un segundo arreglo ordenado `_fijados` relaciona cada ID con una lista de dueños que impiden su desalojo.
2. **Catálogo de partida no acotado (`CatalogoPartida`).**
   - Usa `TablaHashImpl` para conservar todas las fichas resueltas durante la inicialización.
   - Las entidades también guardan directamente el diccionario de ficha en su atributo `ficha`.
3. **Almacenamiento persistente por ID (`AlmacenPersistente`).**
   - Cada ficha se guarda en un JSON independiente con `{version, datos}`.
   - El nombre de archivo se deriva del ID, por lo que no se necesita recorrer todos los archivos para leer una ficha concreta.
4. **Registro de referencias en uso.**
   - `JuegoService` fija las fichas de enemigos vivos, objetos del suelo de la sala actual y trampas de la sala actual.
   - `ServicioInventario` fija las fichas de objetos en inventario, equipo e historial reversible.
   - Los dueños `general` y `en_uso` permiten que una ficha siga protegida hasta que todos sus usos la liberen.

#### Aspectos correctamente resueltos

- `--cache-size` llega desde `configuracion.py` hasta `CacheCatalogo`; el valor predeterminado es 25 y se rechazan valores no positivos.
- LRU es una política justificable: libera primero la ficha no fijada cuyo uso fue menos reciente, porque es una candidata razonable a tardar más en volver a necesitarse.
- Consultar una ficha actualiza su recencia moviendo el mismo nodo al frente de la lista doble.
- El desalojo recorre desde el extremo menos reciente y omite fichas fijadas.
- El repositorio consulta memoria, después disco vigente y por último red. Una ficha recuperada de red se escribe en disco antes de intentar insertarla en la caché.
- El almacenamiento de fichas sobrevive al proceso y se valida con la versión global del catálogo.
- Los guardados de partida incluyen las versiones de cripta y catálogo; antes de reanudar se comparan con los endpoints de versión sin descargar todo el catálogo.
- El guardado binario conserva esqueleto y contenido de la partida. Su reutilización se bloquea cuando no coincide la versión de la cripta.

#### Problema principal: el desalojo no libera la ficha del modelo

`CacheCatalogo._evictar()` elimina la entrada del arreglo y de la lista LRU, pero existen otras referencias fuertes:

- `CatalogoPartida._tabla` conserva todas las fichas resueltas, sin límite de capacidad.
- Cada enemigo, objeto y trampa conserva la ficha en su atributo `ficha`.
- `estado.catalogo_inicial` mantiene accesible el catálogo completo después de inicializar.

Por ello, una ficha desalojada del LRU continúa en memoria y puede seguir obteniéndose desde `CatalogoPartida` o desde una entidad. Volver a necesitarla no obliga a recuperarla del disco, como exige el punto.

**Comprobación realizada:** con una caché de capacidad 2 se insertaron las fichas `a`, `b` y `c` tanto en el LRU como en `CatalogoPartida`. Después del desalojo, `cache.obtener("a")` devolvió `None`, pero `catalogo.resolver("a")` todavía devolvió la ficha. La caché contenía 2 entradas y la tabla de la partida 3.

Esto también significa que `--cache-size` limita únicamente el índice LRU, no la cantidad real de fichas de catálogo mantenidas por el programa.

#### Otros costos y riesgos

- La operación frecuente de presencia usa búsqueda binaria O(log c), no O(1). Es razonable con `c=25`, pero `--cache-size` es configurable y el proyecto ya dispone de una tabla hash propia.
- Insertar o eliminar en `_arreglo` desplaza elementos y cuesta O(c).
- Buscar una víctima puede recorrer hacia atrás muchas fichas fijadas, hasta O(c).
- `AlmacenPersistente.guardar()` descarta silenciosamente errores de escritura. Si una ficha no llegó a persistirse y luego se desaloja de una caché corregida, volver a necesitarla produciría una solicitud de red, contrario a la garantía esperada.
- Como se indicó en 4.2, no existe una caché persistente independiente para esqueleto y contenido entre partidas; esos datos solo se conservan dentro de un archivo de partida guardada. Su persistencia es opcional en el enunciado, pero sería útil para evitar descargas repetidas.

Las 77 pruebas dirigidas de caché, repositorio, datos reales y reanudación pasan. Verifican el comportamiento interno del LRU, pero no detectan que otra estructura conserva la ficha después del desalojo.

#### Por qué LRU es preferible a otras políticas

- **FIFO:** libera la ficha más antigua aunque se consulte constantemente; no aprovecha la localidad temporal.
- **Desalojo aleatorio:** es simple, pero puede expulsar una ficha que acaba de usarse y no ofrece una justificación basada en el patrón de acceso.
- **LFU:** conserva las fichas históricamente frecuentes, pero necesita contadores y una estructura adicional para actualizar prioridades; además, puede retener fichas que fueron populares en una cripta anterior y ya no son útiles.
- **Caché sin límite:** evita recuperaciones, pero contradice directamente el tope configurable.
- **Solo almacenamiento persistente:** cumple supervivencia entre procesos, pero obliga a realizar I/O de disco en cada acceso.
- **Arreglo ordenado sin lista LRU:** localiza por ID, pero no mantiene eficientemente el orden de uso reciente.

#### Estructura sugerida

La caché debe convertirse en la autoridad única de fichas en memoria:

1. **Tabla hash ID→nodo LRU.** Reutilizar `TablaHashImpl` para obtener presencia y ficha en O(1) promedio.
2. **Lista doble LRU.** Conservarla para mover al frente, retirar la víctima y mantener la recencia en O(1).
3. **Tabla hash de fijaciones o contador de referencias.** Asociar cada ID con sus dueños activos; una entrada solo es desalojable cuando no tiene dueños.
4. **Entidades identificadas por ID.** Mantener siempre `tipo_ficha_id`, pero no una referencia permanente a una ficha desalojable. La ficha puede enlazarse mientras esté fijada o resolverse a través de un servicio de catálogo al mostrar/simular.
5. **Eliminar el almacén no acotado de `CatalogoPartida`.** Puede transformarse en una fachada del repositorio y la caché, en vez de otra tabla que posea todas las fichas.
6. **Escritura persistente confirmada.** Guardar de forma atómica y propagar el error; una ficha no debe considerarse recuperable desde disco hasta confirmar la escritura.

Al desalojar una ficha no fijada deben desaparecer todas sus referencias fuertes de memoria. Si después se solicita su ID, el repositorio la reconstruye desde el JSON de la versión vigente y la reinserta en el LRU sin usar red. Solo una ausencia real o una versión distinta debe llegar al cliente HTTP.

### 4.5 Inventario

**Evaluación: adecuada. La lista doble con cursor satisface las operaciones exigidas y las vistas ordenadas se construyen sin modificar el orden real.**

#### Estructuras utilizadas

1. **Lista doblemente enlazada (`ListaDobleImpl`).**
   - Cada `NodoDoble` conserva el objeto y referencias a los nodos anterior y siguiente.
   - `Inventario` usa la lista como orden real y mantiene referencias a sus extremos.
2. **Cursor directo al nodo seleccionado.**
   - `Inventario._cursor` no guarda un índice ni una copia del objeto: referencia directamente el nodo que el jugador está viendo.
   - Esto permite avanzar, retroceder, retirar o mover el objeto actual sin buscar su posición desde el inicio.
3. **Contador y capacidad máxima.**
   - `Inventario` mantiene `_cantidad` y `_capacidad`, esta última inicializada con `generales.inventario_max` por `InicializadorPartida`.
   - `esta_lleno()` compara ambos valores en O(1).
4. **Lista auxiliar para vistas ordenadas.**
   - `obtener_objetos()` copia las referencias a una lista de Python y `ServicioInventario.vista_ordenada()` ordena pares `(clave, objeto)` mediante `OrdenadorAdaptativo`.
   - Los criterios admitidos son peso, valor y nombre de la ficha.
   - Los nodos, sus enlaces y el cursor del inventario real no se reordenan.
5. **Registro de nodos para cambios reversibles.**
   - `RetiroInventario` conserva el mismo nodo, sus vecinos y su marca de orden.
   - Los cambios de recoger, soltar y equipar pueden restaurar el orden sin copiar el inventario completo.

#### Correspondencia con los requisitos

- **Recorrido en ambas direcciones:** `siguiente()` usa el enlace `siguiente` y `anterior()` usa `anterior`; ambos cuestan O(1). En los extremos se conserva la selección actual.
- **Soltar el objeto visible:** `retirar_actual_con_registro()` parte del nodo señalado por el cursor y `quitar_nodo()` actualiza directamente sus dos vecinos. La eliminación del inventario cuesta O(1) y no depende de que el objeto esté al inicio, en medio o al final. Añadirlo al suelo mediante `append()` es O(1) amortizado.
- **Equipar y mover al frente:** `mover_actual_al_frente()` reutiliza el mismo nodo, lo desconecta y lo enlaza como primero en O(1). El cursor continúa apuntando al objeto equipado.
- **Vista ordenada independiente:** la ordenación opera sobre una lista auxiliar. `OrdenadorAdaptativo` usa inserción estable para colecciones pequeñas o con pocos desplazamientos y cambia a mezcla estable para entradas grandes desordenadas; el peor caso general para entradas grandes es O(n log n). La vista no altera el orden real ni la posición actual.
- **Capacidad:** `recoger()` comprueba `esta_lleno()` antes de insertar o retirar el objeto del suelo. Cuando la cantidad alcanza `inventario_max`, devuelve un rechazo de costo cero y conserva el suelo, el inventario y el cursor. Soltar o consumir reduce `_cantidad` y vuelve a habilitar espacio.

La sincronización posterior de referencias de caché recorre los objetos del inventario y cuesta O(n), pero ese trabajo no busca el nodo que se soltó ni depende de su posición. La operación estructural exigida —retirar el objeto actualmente visible— permanece O(1).

#### Por qué la estructura es adecuada

La operación decisiva no es acceder por número de posición, sino operar sobre el elemento actualmente seleccionado. Como el cursor ya referencia el nodo, la lista doble ofrece:

- avance y retroceso O(1);
- eliminación del actual O(1);
- traslado del actual al frente O(1);
- conservación estable del resto del orden;
- restauración del mismo nodo entre sus vecinos sin reconstruir toda la colección.

Copiar referencias para una vista cuesta O(n) tiempo y espacio auxiliar, pero permite presentar cualquier criterio sin destruir el orden utilizado para navegación, equipamiento e historial.

#### Comprobaciones realizadas

- Las 86 pruebas dirigidas de inventario, lista doble, servicio, equipo, vistas e integración finalizaron correctamente.
- Las pruebas cubren navegación en ambos sentidos; retiro al inicio, en medio y al final; equipamiento del mismo nodo; vistas por peso, valor y nombre sin mutación; y rechazo de recolección con el inventario lleno.
- `benchmarks/integrante3.py` contiene mediciones reproducibles de inserción, recorrido, retiro del seleccionado y movimiento al frente, además de comparar el retiro con una lista de Python.

#### Alternativas descartadas

- **Arreglo o lista de Python como estructura principal:** permite acceso por índice O(1), pero retirar una posición arbitraria o moverla al frente desplaza hasta O(n) elementos. El costo dependería de la posición.
- **Lista simplemente enlazada:** avanzar es O(1), pero retroceder o localizar el predecesor para eliminar el nodo actual requeriría un recorrido O(n).
- **Pila:** facilita operar sobre el frente, pero no permite navegar libremente hacia adelante y atrás ni soltar cualquier elemento visible.
- **Cola doble:** optimiza sus extremos, no la eliminación de una posición interior seleccionada.
- **Árbol ordenado como orden real:** facilitaría una única vista ordenada, pero no podría representar simultáneamente peso, valor, nombre y el orden real modificado al equipar.
- **Tres índices ordenados permanentes:** acelerarían la presentación, pero consumirían más memoria y tendrían que sincronizarse en cada recoger, soltar, consumir, equipar o retroceder. Para un inventario acotado, ordenar una copia bajo demanda es más simple y seguro.

#### Sugerencia

No se requiere sustituir la estructura. Conviene mantener pruebas de invariantes que comprueben que `Inventario._cantidad` y `ListaDobleImpl.cantidad` no diverjan. Si `inventario_max` pudiera crecer mucho, podría añadirse una tabla hash `id_instancia → nodo` para seleccionar directamente por ID; no es necesaria para operar sobre el objeto que ya está siendo visto.

### 4.6 Pergaminos de retroceso e historial reversible

**Evaluación: parcialmente adecuada. El historial acotado y las transacciones de cambios inversos son apropiados, pero un cambio genérico basado solo en índices puede impedir un retroceso completo cuando intervienen pergaminos excluidos del historial.**

#### Estructuras utilizadas

1. **Lista doble de transacciones cerradas (`HistorialReversible`).**
   - La transacción más reciente se inserta al frente y la más antigua queda al final.
   - El historial mantiene como máximo cinco nodos. Al insertar el sexto, elimina directamente el último nodo.
   - Consultar, agregar la acción reciente, retirar la reciente y descartar la antigua cuestan O(1).
2. **Pila de cambios inversos por acción (`TransaccionAccion`).**
   - Cada transacción usa otra `ListaDobleImpl` y agrega el cambio más reciente al frente.
   - Al deshacer, consume los cambios desde ese mismo extremo, por lo que aplica primero la inversa de la última mutación.
   - Registrar cuesta O(1) y revertir cuesta O(k), donde `k` es la cantidad de mutaciones producidas por la acción y sus eventos posteriores.
3. **Objetos de cambio o comandos inversos.**
   - `CambioAtributo`, `CambioDato` y `CambioLista` guardan la referencia afectada y el valor, clave o posición mínimos necesarios.
   - Hay cambios especializados para agenda, azar, inventario, equipo, consumo, puertas y traslados de objetos.
   - `CambioAzar` conserva el estado interno del generador seudoaleatorio; no copia el estado del juego.
4. **Agenda reversible enlazada al mismo historial.**
   - `AgendaEventos` registra inserciones, extracciones, cancelaciones, reprogramaciones y cambios de secuencia mientras existe un intervalo abierto.
   - `CambioAgenda` conserva la referencia al evento y si la operación original lo insertó o retiró.
5. **Intervalo abierto durante la simulación automática.**
   - `MotorJuego.ejecutar_accion()` abre la transacción antes de aplicar la decisión y la cierra después de `avanzar_hasta_decision()`.
   - Por ello, los turnos enemigos, pulsos y vencimientos de efectos, cierres de puertas, rearmes de trampas y cambios de reloj ejecutados antes de la siguiente decisión pertenecen a la misma transacción.

#### Aspectos correctamente resueltos

- No se encontraron copias completas, `deepcopy`, serializaciones ni instantáneas de `EstadoPartida` en la implementación del historial.
- La memoria requerida es proporcional a los cambios de las últimas cinco acciones, no a cinco copias de todo el juego.
- Las mutaciones comunes se registran antes de ejecutarse mediante las funciones `atributo()`, `dato()`, `agregar()` y `quitar()`.
- El orden LIFO dentro de cada transacción permite recuperar valores previos aunque un mismo atributo haya cambiado varias veces durante el intervalo.
- Reloj, vida, ubicación, rastro, visitas, puertas, trampas, efectos, inventario, equipo, botín, estado final, contador de acciones, azar y agenda disponen de inversas utilizadas por el motor.
- La restauración de agenda vuelve a insertar el mismo objeto `Evento`, actualizando montículo e índices AVL mediante la interfaz de `AgendaEventos`.
- El límite de cinco acciones se aplica al cerrar cada intervalo; descartar la sexta más antigua no revierte sus efectos.
- `RETROCEDER` consume el pergamino antes de deshacer y no abre una transacción nueva. Si el retroceso termina correctamente, el nodo permanece fuera del inventario y su ubicación es `consumido`.
- Recoger y soltar pergaminos produce acciones con sus demás efectos reversibles, pero omite deliberadamente el cambio de cantidad/ubicación del pergamino. Esto permite que dos pergaminos consecutivos deshagan intervalos distintos sin reaparecer.

#### Problema de la estructura posicional genérica

`CambioLista` guarda `(lista, posicion, valor, insertado)`, pero para deshacer una inserción ejecuta solamente `lista.pop(posicion)`. La posición deja de ser una identidad estable cuando una operación irreversible modifica esa lista.

Se comprobó el siguiente caso:

1. El suelo contenía un pergamino.
2. Matar a un enemigo añadió su botín detrás del pergamino y registró la inserción en la posición 1.
3. Recoger el pergamino eliminó de forma irreversible el elemento anterior al botín, que pasó a la posición 0.
4. Un primer pergamino deshizo la recogida sin restaurar el pergamino, como exige el enunciado.
5. Al usar otro pergamino para deshacer el ataque, `CambioLista` intentó `pop(1)` sobre la lista `[botín]` y lanzó `IndexError`.

Además, `TransaccionAccion.revertir()` retira cada cambio de la pila inmediatamente después de aplicarlo. Si un cambio posterior falla, ya se aplicaron y eliminaron algunos inversos, por lo que la transacción no ofrece atomicidad ni puede reintentarse completa. Este incumplimiento también quedó registrado en `incumplimientos_enunciados.md`.

#### Comprobaciones realizadas

- Las 130 pruebas dirigidas de historial, cambios, pergaminos, agenda, efectos, trampas e inventario finalizaron correctamente.
- Cubren el límite de cinco, orden inverso, reloj, vida, azar, agenda e índices, inventario, botín, puertas, trampas, efectos, victoria/derrota y consumo permanente de pergaminos.
- El caso adicional anterior falla aunque toda la batería existente pase, porque combina una inserción reversible con un traslado irreversible que desplaza su índice.
- `benchmarks/integrante3.py` mide registro con límite de cinco y reversión de cambios, y compara el enfoque incremental con una alternativa de instantáneas mediante copia profunda.

#### Por qué las estructuras principales son adecuadas

- La lista doble exterior ofrece acceso O(1) tanto a la acción más reciente como a la más antigua. Esto encaja con deshacer por un extremo y descartar por el otro.
- La pila interior representa naturalmente el orden inverso de las mutaciones y evita ordenar cambios al retroceder.
- Los objetos de cambio almacenan deltas pequeños y referencias concretas; agregar nuevos tipos de mutación no exige copiar ni conocer toda la estructura de `EstadoPartida`.
- Mantener abierto un único intervalo durante la acción y la simulación automática establece explícitamente la frontera indicada por §2.11.

#### Alternativas descartadas

- **Instantánea completa por acción:** simplifica la restauración, pero está prohibida y su costo de memoria y copia depende del tamaño total del mapa, agenda e inventario.
- **Registrar solo las acciones y volver a simular:** exige reproducir desde un punto anterior, conservar más información, controlar toda fuente de azar y pagar el costo de muchas acciones para deshacer una sola.
- **Una pila global sin transacciones:** no permite identificar con seguridad cuáles cambios pertenecen a la última decisión y a sus eventos posteriores.
- **Lista de Python para las cinco transacciones:** con el elemento reciente al frente, insertar y retirar desplaza referencias; con el reciente al final, descartar el más antiguo desplaza referencias. El límite de cinco reduce el impacto práctico, pero la lista doble expresa mejor las operaciones requeridas.
- **Cola FIFO:** descarta correctamente lo antiguo, pero no ofrece por sí sola el orden LIFO necesario para deshacer la acción más reciente.
- **Guardar únicamente índices de listas:** ocupa poco, pero los índices no son estables frente a modificaciones irreversibles o intercaladas, como demuestra el fallo encontrado.

#### Estructura sugerida

Se recomienda conservar la lista doble exterior y las transacciones de inversos, corrigiendo dos aspectos:

1. **Cambios de colección con identidad estable.** Cada cambio debe guardar la identidad del elemento y referencias a vecinos estables o una marca de orden. Al deshacer una inserción debe localizar y validar la misma instancia, no ejecutar `pop()` sobre un índice histórico. Al restaurar una extracción debe calcular su lugar respecto de los vecinos que aún existan, como ya hacen los cambios especializados del inventario.
2. **Reversión validada y atómica.** Antes de aplicar el primer inverso, la transacción debe validar todos los cambios que puedan fallar. Como protección adicional, no debe destruir los registros hasta completar el retroceso, o debe poder reaplicar en orden directo los inversos ya ejecutados si uno falla.

Una alternativa válida para las colecciones con muchas mutaciones sería una lista doble con nodos estables e identidad propia. Para `Sala.objetos`, también puede mantenerse la lista actual junto con marcas de orden e índice por identidad; así se preserva la interfaz existente sin depender de posiciones que cambian cuando un pergamino queda fuera del historial.

### 4.7 El rastro del jugador

**Evaluación: parcialmente adecuada. La representación del rastro y la decisión local cumplen sus costos, pero la colección de enemigos hace que el trabajo agregado de varios rastreadores pueda ser O(n²).**

#### Estructuras utilizadas

1. **Grafo mediante listas de adyacencia.**
   - Cada `Sala` conserva sus salidas en la lista `puertas`.
   - Después de `MapaCripta.vincular_salidas()`, cada `Puerta` referencia directamente su `destino_sala`.
   - El rastreador itera únicamente las puertas de su sala actual y no busca rutas ni consulta el arreglo global de salas.
2. **Una marca temporal por sala.**
   - `Sala.ultimo_rastro` guarda el último instante del reloj virtual en el que estuvo el jugador.
   - `RegistroRastro.obtener_tiempo()` recibe directamente el objeto `Sala` desde la puerta y obtiene la marca en O(1).
   - Las actualizaciones usan `CambioAtributo`, por lo que el rastro participa en el historial reversible.
3. **Lista auxiliar de compatibilidad.**
   - Si `RegistroRastro` se utiliza sin un mapa, `_presencias` guarda pares `(id_sala, tiempo)` y los busca linealmente.
   - Esta ruta conserva una interfaz anterior, pero no interviene en la decisión normal del rastreador, que trabaja con salas enlazadas.
4. **Lista de enemigos por sala.**
   - `Sala.enemigos` es una lista de Python utilizada para iterar, validar pertenencia, retirar y agregar actores.
   - Esta colección es adecuada para mostrar o recorrer secuencialmente, pero no para comprobar y retirar repetidamente actores conocidos en O(1).

#### Costo de la decisión de rastro

`ComportamientoEnemigos._accion_rastreador()` recorre las `d` puertas de la sala actual. Por cada puerta realiza trabajo constante:

- comprueba si está abierta y tiene destino enlazado;
- lee `destino_sala.ultimo_rastro` en O(1);
- calcula la edad;
- compara frescura y, en empate, el ID numérico de la sala.

Por tanto, la decisión cuesta O(d), donde `d` es el número de salidas de esa sala. No depende de la cantidad total de salas, de la longitud del recorrido del jugador ni del número de rastros históricos. Las pruebas incluso sustituyen las búsquedas globales del mapa por funciones que fallan para demostrar que la decisión no las utiliza.

#### Política de caducidad

La implementación elige **caducidad perezosa al consultar**. Una marca solo es válida cuando:

`0 <= reloj_actual - ultimo_rastro < 400`

Esto descarta exactamente una antigüedad de 400, cualquier valor más antiguo y también rastros futuros. Si no hay vecino con marca vigente, el rastreador espera.

La decisión es adecuada porque solo existe un entero opcional por sala, no una entrada por visita. Conservar una marca vencida no hace crecer la memoria y comprobar su edad cuesta O(1), operación que ya debe realizarse al comparar vecinos. Eliminar activamente exigiría programar/cancelar un evento por actualización o recorrer periódicamente salas, aumentando la agenda y complicando el retroceso sin reducir el costo asintótico de la consulta.

#### Incumplimiento en el trabajo agregado

Aunque la decisión aislada es O(d), `MotorJuego._turno_enemigo()` primero valida la pertenencia mediante:

`any(e is enemigo for e in enemigo.sala_actual.enemigos)`

Esta búsqueda cuesta O(m), donde `m` es la cantidad de enemigos de la sala. Si los `n` rastreadores de esa colección actúan, el total de validaciones es O(n²). Los que se desplazan vuelven a buscar su posición y luego se eliminan de una lista de Python, que desplaza elementos.

**Comprobación realizada:** al instrumentar la lista y ejecutar un turno de cada rastreador se obtuvieron 55 visitas para 10 actores, 5.050 para 100 y 45.150 para 300, exactamente `n(n+1)/2`. Este incumplimiento también quedó registrado en `incumplimientos_enunciados.md`.

Las 81 pruebas dirigidas de registro de rastro, mapa, comportamiento e integración pasan, pero no incluyen una medición agregada con muchos rastreadores.

#### Por qué algunas alternativas no son adecuadas

- **Lista con todas las visitas del jugador:** permitiría reconstruir la ruta, pero la decisión podría depender de la longitud recorrida y la memoria crecería con cada acción.
- **Búsqueda global de salas con rastro:** costaría O(V) por rastreador aunque su sala tenga pocas salidas.
- **Búsqueda de caminos BFS o DFS:** contradice la regla de examinar únicamente vecinos y añade un costo O(V + E) innecesario.
- **Matriz de adyacencia:** permite comprobar una conexión en O(1), pero recorrer los vecinos exigiría revisar O(V) posiciones y consumir O(V²) memoria.
- **Eventos de expiración para cada rastro:** eliminan marcas viejas, pero aumentan la agenda, requieren cancelación al refrescar y agregan cambios al historial. No ahorran memoria porque ya existe una sola marca por sala.
- **Solo una tabla hash de enemigos:** ofrece pertenencia O(1) promedio, pero si se mantiene además una lista de Python sin coordinación, retirar del orden real continúa siendo O(m).

#### Estructura sugerida

Se recomienda conservar las puertas enlazadas, el timestamp por sala y la caducidad perezosa. Para los enemigos de cada sala conviene usar una estructura compuesta:

1. **Tabla hash `id_actor → nodo`**, para validar pertenencia y localizar al actor en O(1) promedio.
2. **Lista doble de enemigos**, para mantener un orden estable de recorrido y retirar o insertar un nodo conocido en O(1).

Con esta combinación, procesar `a` rastreadores cuesta O(a + Σdᵢ) para la lógica de pertenencia, traslado y decisión, donde `dᵢ` es el número de salidas examinado por cada actor. La agenda conserva aparte sus costos O(log n) ya analizados en §4.1.

También sería conveniente reemplazar `_presencias` por una tabla hash si la ruta de compatibilidad sin mapa siguiera siendo pública y frecuente. No es necesario para el flujo actual del rastreador, que recibe referencias directas a `Sala`.

### 4.8 Bitácora en pantalla

**Evaluación: adecuada. La cola circular conserva exactamente los últimos 20 mensajes con memoria acotada e inserción O(1), sin desplazar los anteriores.**

#### Estructuras utilizadas

1. **Arreglo circular de capacidad fija (`ColaCircular`).**
   - `_datos` se crea una sola vez con 20 posiciones para la bitácora.
   - `_frente` identifica el mensaje más antiguo.
   - `_final` identifica la posición que recibirá el siguiente mensaje.
   - `_tamano` distingue una cola parcialmente ocupada de una cola llena.
2. **Fachada específica (`BitacoraPantalla`).**
   - Fija `CAPACIDAD = 20` y delega la inserción y consulta en `ColaCircular`.
   - La vista de consola y la vista gráfica publican sus mensajes mediante esta clase.
3. **Instancia compartida entre controlador y vista.**
   - `ControladorJuego._vincular_bitacora()` reutiliza la bitácora de la vista cuando existe.
   - `_publicar()` evita insertar dos veces cuando controlador y vista apuntan a la misma instancia.

#### Funcionamiento y complejidad

Mientras hay espacio, `encolar()` escribe en `_final`, incrementa `_tamano` y avanza el índice con módulo 20. Cuando la cola está llena:

1. sobrescribe únicamente `_datos[_final]`, que también corresponde a la posición más antigua;
2. avanza `_frente` una posición;
3. avanza `_final` una posición;
4. conserva `_tamano == 20`.

No se copia ni desplaza ninguna de las otras 19 referencias. Agregar cuesta O(1) y utiliza una cantidad constante de operaciones, independientemente del número de mensajes generados anteriormente.

`obtener_elementos()` recorre desde `_frente` y construye una lista auxiliar en orden cronológico. Su costo es O(k), con `k ≤ 20`, y la copia temporal también está acotada a 20 referencias. Modificar esa lista devuelta no altera el buffer real.

La memoria permanente de la estructura es O(20), equivalente a O(1) durante la partida. Al sobrescribir una posición deja de conservarse desde la bitácora la referencia al mensaje antiguo. El tamaño textual de los veinte mensajes vigentes puede variar, pero no se acumulan mensajes de acciones anteriores fuera de esa ventana.

#### Comprobaciones realizadas

- Las 94 pruebas ejecutadas de cola circular, bitácora, controlador y vistas finalizaron correctamente; siete pruebas gráficas condicionadas por el entorno fueron omitidas.
- Las pruebas cubren cola vacía, orden cronológico, mensaje 21, varias vueltas completas, capacidad exacta de 20, consultas no destructivas y ausencia de duplicación entre controlador y vista.
- En una comprobación adicional se conservaron referencias al arreglo interno, se agregaron 10.001 mensajes y se verificó que:
  - seguía siendo el mismo arreglo;
  - su longitud y cantidad continuaban siendo 20;
  - al agregar el mensaje 21, las otras 19 posiciones no cambiaron;
  - los mensajes visibles finales eran exactamente `m9981` a `m10000`.
- `benchmarks/integrante3.py` mide la cola circular y la compara con una lista que ejecuta `pop(0)` al llegar a 20 elementos.

#### Por qué la estructura es adecuada

- El límite físico del arreglo impide que la memoria crezca con la duración de la partida.
- Los índices circulares reutilizan las mismas posiciones indefinidamente.
- Sobrescribir la posición antigua satisface directamente la política de conservar los últimos 20 mensajes.
- La consulta reconstruye el orden lógico sin exigir que los datos estén físicamente ordenados dentro del arreglo.

#### Alternativas descartadas

- **Lista de Python sin límite:** permite `append()` O(1) amortizado, pero acumula todos los mensajes y viola el consumo constante de memoria.
- **Lista de Python con `pop(0)`:** mantiene 20 elementos, pero cada descarte desplaza físicamente las 19 referencias restantes, operación prohibida por el enunciado.
- **Lista doble enlazada:** permite agregar al final y retirar al inicio en O(1), pero asigna y libera un nodo por mensaje, usa más referencias y no aprovecha que la capacidad es fija y conocida.
- **Pila:** conserva primero el mensaje más reciente, pero no representa naturalmente el descarte del más antiguo ni el orden cronológico de presentación.
- **Archivo como bitácora de pantalla:** podría conservar mensajes sin usar memoria creciente, pero requeriría I/O para una función efímera y seguiría necesitando localizar los últimos 20. La bitácora de reproducción de §4.11 es una responsabilidad distinta.
- **`collections.deque(maxlen=20)`:** también cumpliría los costos y el límite, pero la cola circular propia hace explícitos el arreglo fijo, los índices y la política de sobrescritura requerida para la evaluación de estructuras.

#### Sugerencia

No se requiere sustituir la estructura. Conviene mantener como invariantes `0 ≤ _tamano ≤ 20`, índices dentro del arreglo y orden cronológico correcto después de múltiples vueltas. La bitácora de pantalla debe continuar separada de cualquier registro persistente o de reproducción, que sí puede crecer por requisitos diferentes.

### 4.9 Ordenamiento

**Evaluación: parcialmente adecuada. Los dos algoritmos propios, la selección adaptativa, la estabilidad y las mediciones son apropiados, pero el índice del guardado utiliza directamente `list.sort()`.**

#### Estructuras y algoritmos utilizados

1. **Arreglos auxiliares de referencias.**
   - `OrdenadorAdaptativo` recibe una lista y devuelve una lista nueva, sin alterar la colección original.
   - Las claves se guardan junto a cada referencia para evitar recalcular criterios costosos.
2. **Insertion sort estable.**
   - Desplaza únicamente elementos con clave estrictamente mayor, por lo que conserva el orden relativo de los empates.
   - Su costo puede expresarse como O(n + s), donde `s` es la cantidad de desplazamientos; el peor caso sin límite es O(n²).
   - Requiere O(n) memoria en esta implementación porque ordena una copia y mantiene un arreglo paralelo de claves.
3. **Merge sort estable.**
   - Divide recursivamente, ordena ambas mitades y las mezcla.
   - En empate toma primero el elemento de la mitad izquierda, conservando estabilidad.
   - Su tiempo es O(n log n) y requiere memoria auxiliar O(n) en el máximo nivel activo, además de las listas temporales creadas por la recursión.
4. **Selector adaptativo.**
   - Para `n ≤ 16` usa insertion sort, evitando la sobrecarga recursiva de merge en colecciones pequeñas.
   - Para listas mayores calcula una vez todas las claves e intenta insertion sort con un límite de `n` desplazamientos.
   - Si termina dentro del límite, aprovecha que los datos estaban ordenados o casi ordenados; si lo supera, descarta la copia parcial y aplica merge sort sobre los datos originales con claves ya calculadas.

#### Propiedades medibles utilizadas para elegir

La elección no depende del nombre del contexto, sino de dos propiedades observadas en los datos:

- **cantidad de elementos**, mediante el umbral 16; y
- **cantidad real de desplazamientos requerida**, mediante el intento limitado a `n`.

Una colección grande ya ordenada requiere cero desplazamientos y completa insertion sort en O(n). Una casi ordenada con pocos intercambios también puede terminar dentro del límite. Una colección invertida o suficientemente desordenada supera pronto el presupuesto y pasa a merge sort; el intento fallido añade solo trabajo lineal antes del O(n log n).

Las claves se evalúan una sola vez para `n > 16`, incluso si se cambia de algoritmo. Esta decisión es especialmente importante cuando obtener peso, valor o nombre implica resolver una ficha o cuando la función de criterio realiza trabajo costoso.

#### Contextos integrados correctamente

1. **Vistas de inventario.** `ServicioInventario.vista_ordenada()` construye pares de clave y objeto para peso, valor o nombre. La lista ordenada no modifica nodos, cursor ni orden real.
2. **Tabla de puntajes.** `RepositorioPuntajes.listar_ordenados()` aplica el ordenador a acciones ejecutadas, enemigos derrotados o reloj final, sin reescribir el archivo y conservando empates.
3. **Listas auxiliares del catálogo.** `InicializadorPartida` ordena los IDs antes de formar lotes y `CatalogoPartida.entidades()` publica las fichas por ID mediante el mismo ordenador.

#### Contexto incorrectamente integrado

`GuardadoBinario._guardar()` crea `offsets_salas`, cuyos pares deben quedar ordenados por ID para que la carga parcial realice búsqueda binaria. Sin embargo, ejecuta:

`offsets_salas.sort(key=...)`

Este uso corresponde exactamente a uno de los ordenamientos evaluados y viola la prohibición de `list.sort()`. El índice queda funcionalmente ordenado, pero no demuestra ni utiliza la selección propia. El incumplimiento también quedó registrado en `incumplimientos_enunciados.md`.

Los usos de `sorted()` dentro de pruebas y como alternativa comparativa de benchmark no forman parte de la implementación seleccionada. El `sorted()` de `FuenteOffline` ordena nombres de archivos para descubrir fixtures locales, no uno de los cuatro productos de ordenamiento evaluados; aun así, el uso del guardado sí es inequívocamente alcanzable en producción y está nombrado por el enunciado.

#### Evidencia empírica

- `benchmarks/integrante3.py` mide tamaños 8, 16, 32, 64, 128 y 512.
- Para cada tamaño utiliza datos ordenados, casi ordenados, invertidos y aleatorios.
- Ejecuta tanto un criterio simple como uno artificialmente costoso.
- Compara insertion sort, merge sort, el selector adaptativo y `sorted()` únicamente como referencia externa.
- Calibra factores de desplazamiento 1, 2, 4 y 8.
- La documentación del proyecto registra, para datos invertidos, 6,8 µs frente a 8,8 µs en `n=8`, y 86,7 µs frente a 44,7 µs en `n=32`; esto sustenta el umbral reducido a 16. Para `n=512` registra 33,7539 ms para insertion, 1,4299 ms para merge y 1,8152 ms para el adaptativo.
- Una ejecución reducida realizada durante esta revisión produjo 192 mediciones para tamaños 8, 16 y 32, cubriendo los cuatro órdenes, ambos costos de criterio, los tres algoritmos propios/adaptativo y la referencia de Python.
- Las 91 pruebas dirigidas de algoritmos e integración finalizaron correctamente, aunque no detectan el `.sort()` del guardado.

#### Por qué se complementan ambos algoritmos

- Insertion sort tiene implementación simple, es estable y aprovecha colecciones pequeñas o casi ordenadas, pero se degrada cuadráticamente con muchas inversiones.
- Merge sort mantiene O(n log n) independientemente del orden inicial y es estable, pero usa memoria auxiliar y tiene mayor sobrecarga para entradas pequeñas.
- El intento acotado obtiene la ventaja adaptativa de insertion sin aceptar su peor caso para listas grandes.

#### Alternativas descartadas

- **Usar siempre insertion sort:** favorece inventarios pequeños, pero perjudica índices, catálogos o puntajes grandes y desordenados con O(n²).
- **Usar siempre merge sort:** garantiza O(n log n), pero desaprovecha datos pequeños u ordenados y añade recursión y copias.
- **Medir solo el tamaño:** no distingue una lista grande ya ordenada de otra invertida.
- **Contar todas las inversiones previamente:** permitiría clasificar el desorden, pero calcularlas ingenuamente sería O(n²); el intento limitado obtiene una señal útil mientras ya realiza trabajo de ordenamiento.
- **Quicksort:** suele ser rápido, pero una versión simple no es estable y puede degradarse a O(n²); la estabilidad es necesaria para conservar el orden real en empates.
- **Heap sort:** garantiza O(n log n) y poco espacio, pero no es estable de forma natural y no aprovecha datos casi ordenados.
- **`list.sort()` o `sorted()`:** son alternativas muy optimizadas, pero están expresamente prohibidas para estos contextos y no permiten demostrar los algoritmos propios exigidos.

#### Sugerencia

Conservar el selector actual y reemplazar únicamente el `.sort()` del índice de guardado por `OrdenadorAdaptativo`. Conviene centralizar los cuatro contextos en esa interfaz y añadir una prueba estática o dinámica que impida regresiones hacia ordenamientos de biblioteca. Los umbrales deben permanecer configurables y volver a calibrarse si cambia el entorno, el costo de las claves o los tamaños reales de las colecciones.

### 4.10 Guardado binario de la partida

**Evaluación: parcialmente adecuada. El formato binario propio, el índice para carga parcial y la versión son funcionales; la comparación publicada contra JSON no puede reproducirse con los archivos del proyecto.**

#### Estructuras utilizadas

1. **Cabecera binaria fija.**
   - Empieza con la firma de cuatro bytes `CRPT` y la versión de formato `5`.
   - Guarda además el ID de cripta, semilla, reloj, cantidad de salas, offset del índice y offset del jugador.
   - `struct` usa orden little-endian y tamaños explícitos mediante `HEADER_FORMAT = "<4sH32sqIIII"`; la cabecera ocupa 62 bytes.
2. **Registros binarios secuenciales.**
   - Después de la cabecera se escriben jugador, estado adicional y una secuencia de registros de sala.
   - Los campos escalares usan enteros y banderas de tamaño explícito; los identificadores ocupan bloques de 32 bytes.
   - Cada sala comienza con su ID y las cantidades de puertas, enemigos, objetos y trampas. Esas cantidades permiten decodificar sus segmentos variables.
   - Algunos datos internos de forma variable, como los datos de eventos y el estado del generador aleatorio, usan JSON delimitado por longitud; el segundo se comprime con zlib. Esto no convierte al archivo completo en JSON: la organización, cabecera, offsets y registros pertenecen al formato binario propio.
3. **Arreglo de índice ordenado al final del archivo.**
   - Por cada sala conserva un par fijo de 36 bytes: ID de sala de 32 bytes y offset de cuatro bytes.
   - Los pares se ordenan por ID para habilitar búsqueda binaria.
   - Actualmente el orden se obtiene con `list.sort()`, incumplimiento independiente ya documentado en §4.9; el índice resultante sí conserva el orden que necesita la carga parcial.
4. **Diccionario de salas en la carga completa.**
   - `cargar()` lee y valida todo el archivo y reconstruye un diccionario `id_sala → datos de sala`.
   - Este índice en memoria permite que el restaurador relacione salas y referencias posteriormente.
5. **Archivo temporal y reemplazo atómico.**
   - `guardar()` escribe primero en un archivo temporal del mismo directorio y luego usa `os.replace()`.
   - Un error de escritura no sustituye una instantánea anterior válida por un archivo parcialmente escrito.

#### Recuperación de una sala específica

`leer_sala()` no llama a `read()` sin límite ni carga el contenido completo. Su recorrido es:

1. leer solo la cabecera de 62 bytes y comprobar firma y versión;
2. consultar el tamaño con `seek()` para validar que el índice termina exactamente al final del archivo;
3. saltar al offset del índice y leer sus `36n` bytes;
4. realizar búsqueda binaria por ID sobre ese bloque;
5. recorrer los offsets del índice para encontrar el comienzo del registro siguiente en orden físico;
6. saltar al registro objetivo y leer únicamente sus bytes;
7. decodificar esa sala y verificar nuevamente su ID.

La búsqueda por ID cuesta O(log n), pero la operación completa actual cuesta O(n + r) en tiempo y lectura, donde `n` es la cantidad de salas y `r` el tamaño del registro solicitado: se carga todo el índice y además se recorre para descubrir el final del registro. La memoria auxiliar es O(n + r). Aun así, no se leen el jugador, los extras ni los registros de las demás salas, por lo que satisface el requisito funcional de no leer el archivo completo.

En una comprobación instrumentada con 500 salas, el archivo midió 121.344 bytes y `leer_sala(250)` realizó tres lecturas de 62, 18.000 y 206 bytes: 18.268 bytes en total, equivalentes al 15,05 % del archivo. La sala recuperada fue la solicitada.

#### Detección de versión e integridad básica

- Tanto `cargar()` como `leer_sala()` exigen simultáneamente `MAGIC == b"CRPT"` y `VERSION == 5`.
- Un archivo con otra versión se rechaza devolviendo `None`; las capas de servicio lo convierten en un error que menciona una versión incompatible o no soportada.
- También se validan tamaño mínimo, posición fija del jugador, terminación exacta del índice, offsets dentro de la zona de registros, IDs y longitudes suficientes para desempaquetar.
- Al cambiar experimentalmente los dos bytes de versión de 5 a 6, tanto la carga completa como la carga de una sala devolvieron `None`.

Esta detección evita interpretar silenciosamente otra versión con la disposición actual. No ofrece migración hacia versiones anteriores, pero el enunciado exige detectar la incompatibilidad, no migrarla.

#### Complejidades principales

- **Guardado:** O(B + n log n) con la ordenación actual, donde `B` es la cantidad de bytes serializados y `n` la cantidad de salas; requiere O(n) referencias auxiliares para los offsets.
- **Carga completa:** O(B) en tiempo y memoria porque `cargar()` lee el archivo entero y reconstruye todas las salas.
- **Carga de una sala:** O(n + r) en tiempo y bytes leídos, y O(n + r) de memoria temporal, por la lectura completa del índice y el registro objetivo.
- **Comprobación de versión:** O(1), incluida en la lectura de la cabecera.

#### Pruebas y mediciones encontradas

- Las 95 pruebas dirigidas de guardado, estrés, flujo y reanudación finalizaron correctamente.
- La cobertura incluye round trip, lectura directa de sala, archivos inexistentes, firma corrupta, cientos de salas, inventario, efectos, agenda, azar, equipo, rastro, campos de sesión y corrupciones de versión, índice, offsets y contenido.
- `docs/comparacion_binario_json.md` informa, para una partida de 52 salas y 500 iteraciones, 52,7 KB frente a 69,8 KB, carga completa de 1,29 ms frente a 0,98 ms y acceso a una sala de 0,21 ms frente a 0,90 ms.
- Sin embargo, no existe un benchmark ni un serializador JSON asociado que permita volver a producir esos valores o verificar que representan exactamente el mismo estado. El faltante se registró en `incumplimientos_enunciados.md`.

#### Por qué las estructuras son adecuadas

- La cabecera fija permite reconocer el archivo y ubicar sus secciones sin analizar todos los registros.
- Los offsets convierten la búsqueda de una sala en acceso dirigido, en lugar de recorrer y decodificar todas las salas anteriores.
- El índice al final permite conocer cada offset mientras se escribe el flujo una sola vez y completar luego la cabecera.
- Los conteos y longitudes explícitos hacen posible recorrer registros variables sin delimitadores textuales.
- La escritura temporal reduce el riesgo de perder el guardado anterior ante un fallo parcial.

#### Alternativas descartadas

- **JSON como formato principal:** es portable y sencillo de inspeccionar, pero repite nombres de campos y, sin un índice externo, exige leer y analizar el documento completo para recuperar una sala.
- **Binario secuencial sin índice:** reduce el espacio adicional, pero obliga a recorrer todos los registros anteriores hasta encontrar la sala solicitada.
- **Tabla hash serializada:** podría aproximar acceso O(1), pero necesita resolver colisiones, reservar espacio y definir cuidadosamente una representación portable; para un archivo estático, un índice compacto y ordenado es más simple.
- **Árbol B o base de datos embebida:** favorece actualizaciones y consultas frecuentes sobre archivos grandes, pero añade complejidad innecesaria cuando se escribe una instantánea completa y las salas no se modifican dentro del archivo.
- **Serialización nativa de Python (`pickle`):** simplifica la implementación, pero no constituye un formato controlado y portable, dificulta la compatibilidad explícita y no debe cargarse desde fuentes no confiables.

#### Sugerencias

1. Incorporar al índice la longitud de cada registro, o almacenar los registros físicamente en el mismo orden que el índice. Así `leer_sala()` podría leer entradas del índice bajo demanda y evitar el recorrido lineal para hallar el final.
2. Sustituir el `list.sort()` por `OrdenadorAdaptativo`, como exige §4.9.
3. Agregar el benchmark reproducible binario–JSON descrito en `incumplimientos_enunciados.md`, usando exactamente el mismo estado lógico y separando serialización, carga completa y acceso a una sala.
4. Mantener pruebas que alteren explícitamente firma, versión, offsets y longitudes antes de intentar reconstruir objetos.

### 4.11 Bitácora de partida y reproducción

**Evaluación: parcialmente adecuada. El formato append-only, la validación completa, la reproducción determinista y el rechazo de versiones incompatibles son apropiados, pero el registro debe activarse manualmente y por ello no cubre todas las partidas.**

#### Estructuras utilizadas

1. **Archivo secuencial JSON Lines.**
   - Cada línea es un objeto JSON independiente codificado en UTF-8.
   - La primera línea es una cabecera con `cripta_id`, `version_cripta`, `version_catalogo` y `semilla`, además del discriminador `registro = "cabecera"`.
   - Cada línea posterior representa una acción con tipo, ID estable del objetivo y dirección.
2. **Creación exclusiva y anexado.**
   - `RegistroPartida.crear()` abre la ruta con modo `x`: crea una bitácora nueva y se niega a truncar una existente.
   - `anexar_accion()` abre con modo `a`, por lo que cada acción nueva se escribe al final sin reescribir registros anteriores.
3. **Marca de identidad e integridad del archivo activo.**
   - `JuegoService` conserva dispositivo, inodo, tamaño y tiempo de modificación del log.
   - Antes de ejecutar otra acción compara esa marca para detectar eliminación, reemplazo o modificación externa.
   - Tras anexar actualiza la marca con los nuevos metadatos.
4. **Arreglo de acciones validado antes del replay.**
   - `EjecutorReplay._leer_log()` recorre todas las líneas, valida su esquema y acumula pares `(número_de_línea, registro)`.
   - Solo después de validar el log completo prepara una partida y comienza a ejecutar acciones.
   - El número de línea permite reportar con precisión un registro inválido o una acción imposible.
5. **Tupla de versiones esperadas.**
   - El replay compara `(version_cripta, version_catalogo)` de la cabecera contra la fuente configurada.
   - Si no coincide, intenta una fuente offline local; si tampoco coincide, aborta con un error explícito.
   - Durante la inicialización fija temporalmente las versiones exigidas para impedir que cambien entre la comprobación y la construcción del estado.
6. **IDs estables en lugar de referencias de memoria.**
   - Actores y objetos se registran por `id_actor` o `id_instancia`; movimiento y apertura registran la dirección.
   - Durante el replay, `JuegoService.resolver_accion()` busca la instancia vigente correspondiente en sala o inventario.
   - `EQUIPAR` conserva expresamente el ID del objeto seleccionado, porque el movimiento del cursor no es una acción registrada.

#### Funcionamiento del registro

`iniciar_registro()` solo acepta una partida nueva inicializada por `JuegoService`, con reloj cero y sin acciones coordinadas. Obtiene las versiones verificadas de la partida y crea la cabecera antes de que pueda anexarse una acción.

Después de cada acción exitosa, `_cerrar_accion()` escribe una línea. Las acciones rechazadas, que no modifican el estado ni consumen tiempo, no se añaden. Si la escritura falla después de que el motor ya actuó, el servicio:

- informa que el estado cambió pero el log quedó incompleto;
- no finge que la acción fue rechazada ni la ejecuta otra vez;
- bloquea acciones posteriores para evitar ampliar la divergencia.

Esta política es coherente para un log ya conectado. El problema es que `_ruta_registro` comienza y vuelve a quedar en `None` al iniciar cada partida. Solo el comando opcional `registro RUTA` llama a `iniciar_registro()`. Una acción realizada sin ese paso no entra en ninguna bitácora. Este incumplimiento está registrado en `incumplimientos_enunciados.md`.

#### Funcionamiento del replay

1. Lee y valida la totalidad del archivo antes de modificar una partida.
2. Rechaza líneas vacías, JSON inválido, claves duplicadas, campos desconocidos, tipos incorrectos y acciones fuera del vocabulario admitido.
3. Comprueba las versiones de cripta y catálogo contra la fuente disponible.
4. Si no coinciden, busca una copia offline con exactamente ambas versiones.
5. Si tampoco existe, produce `No hay una copia local con versiones compatibles con el log.` y no inicializa otra partida silenciosamente.
6. Configura la semilla de la cabecera y reconstruye el estado inicial mediante el mismo `InicializadorPartida` usado por el juego.
7. Resuelve cada ID contra las instancias actuales y delega la acción al mismo `JuegoService` y `MotorJuego`.
8. Si una acción ya no es posible, informa su número de línea y detiene el replay.

El modo `main.py --replay partida.log` toma una rama anterior a la creación de cualquier vista. Las pruebas sustituyen `input()` y los constructores de vista por operaciones que fallan y confirman que no son invocados. El contexto de replay tampoco conecta un registro ni modifica la partida normal que pudiera existir.

#### Complejidad

Para `a` registros, validar y almacenar el log cuesta O(a) tiempo y O(a) memoria. La reproducción añade el costo de las acciones del motor y de resolver objetivos. Las búsquedas actuales de un ID recorren linealmente los enemigos de la sala o los objetos del inventario, por lo que cada resolución cuesta O(e) u O(i), respectivamente.

Anexar una acción requiere serializar un registro de tamaño pequeño y realizar una escritura al final; respecto de la cantidad histórica de acciones es O(1). El archivo sí crece O(a), como corresponde a una bitácora persistente completa, a diferencia del buffer fijo de pantalla de §4.8.

#### Comprobaciones realizadas

- Las 114 pruebas dirigidas de registro, replay, conexión e inicialización finalizaron correctamente.
- Se comprueban creación exclusiva, preservación de prefijos tras varios anexados, IDs estables, fallos de escritura, modificación externa, cabeceras inválidas, claves duplicadas y acciones imposibles.
- Las pruebas comparan el estado serializado después de jugar normalmente y después de reproducir el mismo log, incluidos reloj, agenda, inventario, equipo, azar y retrocesos.
- También ejecutan `main.py --offline --replay partida.log` como subproceso sin entrada ni vista.
- Una prueba cambia las versiones del log y confirma que, sin copia compatible, no se llama a la fábrica ni se altera el estado previo.
- La comprobación adicional de esta revisión confirmó el faltante: un ataque exitoso en una partida nueva, sin ejecutar `registro RUTA`, dejó `registro_activo = False` y no creó ningún `.log`.
- `benchmarks/integrante3.py` compara el parseo JSON Lines con un arreglo JSON. La documentación registra para 512 acciones 2,0901 ms frente a 0,4837 ms; la alternativa es más rápida al leer, pero no permite anexar conservando un JSON completo sin reescribir su cierre.

#### Por qué JSON Lines es adecuado

- Cada registro forma una unidad textual independiente, fácil de inspeccionar y adjuntar a un reporte de error.
- El modo append permite agregar una acción sin leer ni reescribir el historial anterior.
- Una línea parcialmente escrita puede localizarse por su número y se rechaza antes de ejecutar el replay.
- JSON representa explícitamente campos opcionales y escapa saltos de línea o caracteres Unicode sin romper la separación física de registros.
- Los IDs estables evitan serializar direcciones de memoria o representaciones dependientes del proceso.

#### Alternativas descartadas

- **Arreglo JSON único:** se analiza más rápido según la medición, pero anexarlo exige retirar y volver a escribir el delimitador final o reescribir el documento completo.
- **Texto separado por espacios:** es compacto, pero requiere reglas propias para escape, valores nulos, Unicode y argumentos con espacios.
- **CSV:** funciona para columnas fijas, pero resulta menos claro para acciones con argumentos mutuamente excluyentes y requiere cuidado adicional con escapes.
- **Formato binario:** podría ser más compacto, pero dificulta la inspección y el intercambio del archivo como reporte de error; además, la sección exige texto.
- **Guardar instantáneas completas por acción:** simplificaría saltos aleatorios, pero multiplicaría el tamaño y ocultaría la secuencia exacta de decisiones que debe reproducirse.
- **Usar nombres visibles como objetivos:** facilita lectura humana, pero los nombres pueden repetirse o cambiar; los IDs de instancia son inequívocos.

#### Sugerencias

1. Activar automáticamente un archivo nuevo y único al iniciar cualquier partida reproducible, antes de admitir acciones desde consola o Pygame.
2. Conservar `registro RUTA` como configuración anticipada de destino, no como condición para que exista bitácora.
3. Mantener la validación previa completa y las comprobaciones de versión antes y durante la inicialización.
4. Para logs muy grandes, una primera pasada de validación sin acumular registros y una segunda pasada de ejecución reducirían la memoria a O(1), manteniendo la garantía de no mutar el estado ante errores sintácticos posteriores.
