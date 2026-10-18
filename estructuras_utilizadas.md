# Estructuras de datos utilizadas

Este documento registra, para cada punto revisado del enunciado:

- la estructura de datos utilizada;
- dónde y cómo se utiliza;
- por qué resulta adecuada para el requisito;
- por qué se prefirió frente a otras estructuras pertinentes;
- y, cuando corresponda, la estructura sugerida para corregir una elección inadecuada.

Las secciones usan el mismo número de punto del enunciado.

**Última actualización: 18/10/2026.** Revisado contra el código de la rama `Steve` (igual a `main` salvo la limpieza de entrega). Las secciones 4.2, 4.3, 4.4, 4.6, 4.7, 4.9, 4.10 y 4.11 se actualizaron con las correcciones posteriores a la revisión anterior; 4.1, 4.5 y 4.8 no cambiaron. Al final hay un resumen para repasar antes de la defensa.

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

**Evaluación: adecuada. La carga gradual por cercanía está integrada en el flujo real, distingue salas pendientes de salas vacías y respeta el presupuesto.**

#### Estructuras utilizadas

1. **Grafo mediante listas de adyacencia.**
   - `MapaCripta` guarda las salas en la lista `_salas`.
   - Cada `Sala` guarda sus conexiones en la lista `puertas`. Cada `Puerta` recibe una referencia `destino_sala` cuando `MapaCripta.vincular_salidas()` resuelve los IDs una sola vez.
   - Recorrer vecinos usa solo las puertas de la sala; no se consulta el mapa completo.
2. **Marca de estado por sala (`Sala.contenido_cargado`).**
   - `True` indica que el contenido ya llegó. `False` indica que la sala existe (ID y puertas), pero su contenido todavía no se pidió.
   - Así se distingue “sala vacía” de “contenido desconocido”, que antes eran lo mismo: listas vacías.
   - `Sala.incorporar_contenido(enemigos, objetos, trampas)` **agrega** al final de las listas, asigna `sala_actual` a los enemigos y marca la sala como cargada. No reemplaza nada: si un enemigo dejó botín antes de que llegara el contenido, se conserva.
   - La incorporación no pasa por el historial reversible, porque es infraestructura y no estado del juego (§2.11).
3. **Búsqueda en anchura por niveles (`CargadorContenido.mas_cercanas`).**
   - Usa las listas `frontera` y `siguiente` para los niveles, y dos `TablaHashImpl` propias: `visitadas` (salas ya alcanzadas) y `pendientes` (salas sin contenido). Acumula pares `(distancia, id_sala)`.
   - Los pares se ordenan con `OrdenadorAdaptativo` por distancia y luego por ID. De ahí se toman las primeras 10 salas pendientes.
4. **Lotes con orden de incorporación fijo (`_cargar_lotes`).**
   - Cada lote tiene como máximo 10 salas (`MAX_IDS_POR_SOLICITUD`).
   - La lista `orden` conserva el orden en que se **pidieron** las salas. El contenido se incorpora en ese orden, nunca en el que llega la respuesta, así el resultado no depende de la red (§2.4).
   - Es una operación de todo o nada: primero se piden todos los lotes y se resuelven sus fichas, y solo después se incorpora. Si algo falla, ninguna sala cambia.
5. **Contador de presupuesto (`PresupuestoSolicitudes`).**
   - Limita las solicitudes HTTP de la partida al `presupuesto_solicitudes` que publica la cripta.
   - En offline no existe contador y las lecturas no cuentan (§5.1).

#### Dónde y cómo se utilizan

- `InicializadorPartida._construir()` arma el **esqueleto completo** (todas las páginas y las llaves) y delega el contenido en `CargadorContenido`.
- **Estrategia adaptativa según el presupuesto:**
  - **Con holgura** (`alcanza_para_todo()`: quedan al menos `2·lotes + 3` solicitudes), se carga todo al inicio. Es el caso de las 4 criptas publicadas, que cargan con entre 5 y 8 solicitudes de presupuestos que van de 9 a 52. El jugador nunca espera en una puerta.
  - **Con presupuesto ajustado**, al inicio se carga solo la sala inicial y su vecindad (un lote). Después de cada acción, `precargar_cerca()` adelanta el lote de las vecinas pendientes si quedan al menos 2 solicitudes; la última se reserva para poder moverse.
- **Antes de confirmar un `MOVER`**, `JuegoService` llama a `asegurar(destino)`: si la sala está pendiente, se carga primero. La espera no avanza el reloj virtual, porque el reloj solo lo mueve el motor (Apéndice B).
- **Sin presupuesto y con el destino pendiente**, el movimiento se rechaza con un mensaje y sin consumir tiempo.
- **Red de seguridad en el motor:** `MotorJuego` rechaza un `MOVER` hacia una sala con `contenido_cargado = False` antes de abrir el intervalo, por si algún flujo llegara sin pasar por el servicio.

#### Por qué es adecuada

- La marca booleana por sala resuelve el problema central de la versión anterior: saber qué falta sin una estructura aparte.
- El BFS por distancia aprovecha cada solicitud con las salas que más probablemente se visiten a continuación.
- Incorporar en orden de solicitud hace la carga determinista, aunque las respuestas tarden distinto.
- La estrategia adaptativa evita las dos fallas extremas: descargar toda la cripta cuando el presupuesto no alcanza, o hacer esperar al jugador cuando sí alcanza.

#### Costos

- `mas_cercanas()` es un BFS **O(V + E)**: comprobar si una sala ya fue visitada o si está pendiente es O(1) promedio con las tablas hash. Antes `visitadas` era una lista y cada `in` costaba O(V), lo que llevaba el peor caso a O(V²); se corrigió el 18/10/2026 pensando en las criptas más grandes de la revisión (§9). Ordenar los pares añade O(V log V).
- `pendientes()` recorre las salas en O(V).
- `MapaCripta.obtener_sala(id)` sigue siendo una búsqueda lineal O(V). Solo se usa al vincular y al incorporar, no en cada decisión.
- Incorporar un lote cuesta O(contenido del lote), porque solo agrega al final de las listas.

#### Comprobaciones realizadas

- `tests/test_carga_gradual.py` usa una cripta sintética cuyo contenido completo no cabe en el presupuesto: arranca igual, se recorre y se gana sin pasarse del presupuesto, un `MOVER` hacia una sala pendiente sin presupuesto no consume tiempo, y una partida guardada con salas pendientes las sigue cargando al continuar.
- `tests/test_dto/test_sala_contenido.py` y `tests/test_logica/test_salas_pendientes_motor.py` comprueban que `incorporar_contenido` agrega sin reemplazar (el botín previo se conserva) y que el motor rechaza moverse a una sala pendiente sin abrir un intervalo.
- Las pruebas de contrato contra respuestas reales del API (`tests/test_contrato_api_real.py`) cargan las 4 criptas con la estrategia de holgura.
- En modo offline, un agente jugó cripta-01 completa: el reporte final fue “Presupuesto: 0/9 solicitudes usadas”.
- `tests/test_service/test_cargador_bfs.py` comprueba el orden por distancia y luego por ID, que se omitan las salas ya cargadas y que en una cuadrícula de 900 salas se elija el lote correcto de 10.

#### Por qué algunas alternativas no son adecuadas

- **Precargar siempre toda la cripta:** era el comportamiento anterior. Garantiza disponibilidad, pero una cripta grande con presupuesto ajustado no podía ni arrancar. Hoy se usa solo cuando el presupuesto alcanza con holgura.
- **`PlanificadorPrecarga` aislado:** tenía un BFS correcto, pero no participaba en el flujo real. Se eliminó; `CargadorContenido` reutiliza su idea y sí está conectado.
- **Matriz de adyacencia:** O(V²) de memoria en criptas dispersas, sin ventaja para recorrer pocos vecinos.
- **Incorporar cada respuesta apenas llega:** el estado dependería del orden real de la red y se perdería el determinismo.
- **Una tabla de estados con cuatro valores (no solicitada, pendiente, disponible, fallida):** la carga es síncrona, así que “pendiente” y “fallida” nunca se observan desde el modelo. La marca booleana más el todo-o-nada cubren el mismo caso con menos estructura.

#### Sugerencia

- Agregar en `MapaCripta` un índice `id_sala → sala` para que `obtener_sala()` sea O(1) promedio.

### 4.3 Resolución de referencias del catálogo

**Evaluación: adecuada. Las referencias se resuelven por lotes de hasta 10, incluido el botín de forma transitiva, y cada tipo de ficha existe una sola vez en memoria.**

#### Estructuras utilizadas

1. **Listas temporales de IDs únicos.**
   - `InicializadorPartida` reúne las llaves de las puertas y la llave de salida con `_agregar_id()`.
   - `CargadorContenido._validar()` reúne los IDs de enemigos, objetos y trampas de cada lote.
   - Antes de consultar, los IDs se ordenan con `OrdenadorAdaptativo` y se dividen en lotes de hasta 10.
2. **Resolución transitiva del botín (`CargadorContenido._resolver_fichas`).**
   - Usa una lista `pendientes` como cola de trabajo y una lista `vistas` para no repetir IDs.
   - Cuando una ficha es de clase `enemigo`, los IDs de su campo `suelta` se agregan a `pendientes`. Así el botín queda resuelto antes de que un enemigo muera.
3. **Catálogo de la partida que no retiene fichas (`CatalogoVivo`).**
   - No guarda fichas propias. Cada `resolver(id)` pasa por el repositorio: caché → disco → red.
   - Reemplazó como catálogo de la partida a `CatalogoPartida`, que guardaba todas las fichas en una `TablaHashImpl` sin límite. `CatalogoPartida` queda solo como índice temporal para validar fichas al conectar el inventario y al restaurar una partida sin catálogo vivo.
4. **Caché LRU compartida entre partidas (`CacheCatalogo`).**
   - Combina una lista doble para el orden de uso con un arreglo ordenado `(ficha_id, nodo)` con búsqueda binaria O(log c). Ver §4.4.
5. **Almacenamiento persistente indexado por archivo (`AlmacenPersistente`).**
   - Cada ficha se guarda en `<ficha_id>.json` junto con la versión del catálogo. La ruta funciona como índice directo por ID.
6. **Repositorio por niveles (`RepositorioCatalogo.resolver_lote`).**
   - Consulta en orden memoria → disco con versión vigente → red, y pide a la red solo los faltantes, en una sola solicitud por lote.
   - Si la red falla y existe una copia en disco de una versión anterior, la usa como respaldo en vez de perder la ficha.

#### Dónde y cómo se resuelven las referencias

- Las fichas de cada lote de contenido se resuelven juntas, antes de incorporar las salas. Una entidad nunca se muestra ni se simula sin su ficha.
- Las entidades (`Enemigo`, `ObjetoInstancia`, `Trampa`) heredan `FichaResoluble`. Guardan solo `tipo_ficha_id` y leen `entidad.ficha` a través del `CatalogoVivo`. Dos ratas del mismo tipo leen la misma ficha de la caché.
- La caché y el disco sobreviven al cambio de cripta cuando la versión del catálogo coincide. Al iniciar otra cripta con las mismas fichas no se gasta red.

#### Por qué las estructuras son adecuadas

- Pedir por lotes aprovecha que consultar 10 IDs cuesta prácticamente lo mismo que consultar 1 (§3.3).
- Resolver el botín de forma transitiva evita una solicitud de emergencia en mitad del combate.
- Una sola ficha por tipo evita duplicar estadísticas e inconsistencias entre instancias.
- Ordenar los IDs antes de formar lotes hace determinista el orden de las consultas, aunque se descubran desde salas distintas.

#### Comprobaciones realizadas

- Las pruebas de repositorio, caché e inicialización verifican que no se repitan IDs entre lotes y que reiniciar la misma cripta no pida catálogo otra vez.
- Las pruebas de contrato contra el API real resuelven las fichas de las 4 criptas, incluido el botín.

#### Por qué no se utilizaron otras estructuras

- **Una lista simple como catálogo principal:** O(n) por cada resolución.
- **La ficha copiada dentro de cada instancia:** más memoria e inconsistencias entre instancias. Además, impedía que `--cache-size` limitara la memoria real (§4.4).
- **Solicitudes individuales por ID:** desperdician presupuesto y latencia.
- **Una tabla hash sin desalojo como catálogo de partida:** era `CatalogoPartida`; retenía todas las fichas y anulaba el límite de la caché.
- **Consultar siempre el disco:** evita la red, pero añade I/O a cada lectura. La memoria debe ser el primer nivel.

#### Mejora sugerida

La deduplicación de IDs usa listas (`f not in ids_fichas`), con costo O(u) por consulta y hasta O(u²) en total, donde `u` es la cantidad de IDs únicos. Con los catálogos actuales (11 tipos en cripta-01) no se nota. Para catálogos grandes conviene mantener una lista para el orden y una `TablaHashImpl` para la pertenencia.

### 4.4 Reutilización y caché persistente

**Evaluación: adecuada. `--cache-size` limita la cantidad real de fichas en memoria; una ficha desalojada se recupera del disco sin usar la red, y las fichas en uso nunca se desalojan.**

#### Estructuras utilizadas

1. **Caché LRU acotada (`CacheCatalogo`).**
   - Una `ListaDobleImpl` mantiene las fichas de la más reciente (frente) a la menos reciente (final).
   - Un arreglo ordenado `_arreglo` de pares `(ficha_id, nodo)` localiza cada ficha con búsqueda binaria.
   - No usa tabla hash, por indicación del profesor para la caché.
2. **Registro de fijaciones por dueño (`_fijados`).**
   - Es otro arreglo ordenado de pares `(ficha_id, [dueños])`.
   - Hay dos dueños: `DUEÑO_GENERAL` (inventario, equipo e historial, vía `ServicioInventario`) y `DUEÑO_EN_USO` (enemigos vivos, objetos del suelo y trampas de la sala actual, vía `JuegoService._sincronizar_fichas_en_uso`).
   - Una ficha sigue protegida mientras le quede algún dueño. Antes, un solo indicador hacía que el inventario y la sala se “pisaran” la protección.
3. **Entidades que no retienen la ficha (`FichaResoluble` + `CatalogoVivo`).**
   - `entidad.ficha` es una propiedad: si la entidad está conectada a un catálogo vivo, cada lectura pasa por la caché y, si fue desalojada, por el disco.
   - La entidad solo guarda `tipo_ficha_id`. Por eso la única copia en memoria es la de la caché.
4. **Almacenamiento persistente por ID (`AlmacenPersistente`).**
   - Un JSON por ficha con `{version, datos}`, en `cache/catalogo/`. Sobrevive al cierre del programa.
5. **Métricas de la caché.**
   - Aciertos, fallos, fallos resueltos desde disco y desde red. Se reportan al terminar la partida (§5.1).

#### Cómo funciona

- **Acierto:** búsqueda binaria en `_arreglo` O(log c), y luego `mover_al_frente(nodo)` en la lista doble O(1).
- **Fallo:** el repositorio busca en el disco y, si la versión es vigente, inserta en la caché. Solo si no está en disco pide a la red; lo que llega de la red se escribe primero en disco.
- **Desalojo:** recorre la lista desde el final hasta encontrar la primera ficha **no fijada** y la elimina de la lista y del arreglo. Como ninguna entidad guarda la ficha, desaparece de la memoria.
- **Volver a necesitarla:** el repositorio la reconstruye desde el JSON del disco y la reinserta, sin red.
- El estado guardado y el retroceso no incluyen la caché: `CacheCatalogo.__getstate__` conserva solo la capacidad, y `CatalogoVivo` y `FichaResoluble` excluyen el catálogo al serializar (§2.11).

#### Aspectos correctamente resueltos

- `--cache-size` (25 por defecto, entero positivo) llega desde `configuracion.py` hasta `CacheCatalogo`.
- El problema de la revisión anterior está corregido: `CatalogoPartida` ya no retiene fichas y las entidades tampoco, así que el límite de la caché es el límite real.
- LRU libera primero la ficha que lleva más tiempo sin usarse, la candidata razonable a tardar más en volver a necesitarse.
- Los guardados de partida incluyen las versiones de cripta y catálogo y se comparan antes de reanudar.

#### Costos y riesgos

- Presencia O(log c); insertar o eliminar en `_arreglo` cuesta O(c) por el desplazamiento. Con `c = 25` es despreciable.
- Buscar una víctima puede recorrer hacia atrás varias fichas fijadas, hasta O(c).
- **Riesgo pendiente:** `AlmacenPersistente.guardar()` descarta en silencio los errores de escritura (`except OSError: pass`). Si una ficha no llegó a escribirse y luego se desaloja, volver a necesitarla gastaría una solicitud de red.

#### Comprobaciones realizadas

- `test_cache_size_limita_las_fichas_retenidas_y_recupera_desde_disco` (`tests/test_contrato_api_real.py`): con una caché de 3 y cripta-04 completa, ninguna entidad guarda su ficha, la caché nunca pasa de 3 y leer la ficha de un objeto lejano la trae del disco sin pedirla a la red.
- `test_cache_ficha_compartida_por_dos_duenos_no_se_desaloja`: liberar desde la sala no desprotege una ficha que también está en el inventario.
- Partida offline real: “Fallos resueltos desde disco: 11; desde la red: 0”.

#### Por qué LRU es preferible a otras políticas

- **FIFO:** libera la ficha más antigua aunque se use constantemente.
- **Aleatorio:** puede expulsar una ficha recién usada.
- **LFU:** necesita contadores y puede retener fichas que fueron populares en una cripta anterior.
- **Caché sin límite:** contradice el tope configurable.
- **Solo disco:** cumple la persistencia, pero obliga a hacer I/O en cada acceso.

#### Sugerencia

- Propagar el error de escritura del almacén, o escribir de forma atómica, para garantizar que una ficha desalojada siempre pueda recuperarse del disco. **Decisión: se deja como está, a propósito**: si el disco falla (permisos, disco lleno) el juego sigue funcionando y, en el peor caso, al volver a necesitar esa ficha se gasta una solicitud de red. Propagar el error haría caer la partida por un problema de infraestructura.
- Si la capacidad de la caché creciera mucho, el arreglo ordenado tendría inserciones O(c). Con la restricción de no usar tabla hash en la caché, un árbol AVL (como `IndiceOrdenado`) daría O(log c) en todas las operaciones.

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

**Evaluación: adecuada. El historial acotado a 5, las transacciones de cambios inversos y la exclusión de los pergaminos cumplen §2.11. Se corrigieron los cambios de colección por índice y la falta de atomicidad.**

#### Estructuras utilizadas

1. **Lista doble de transacciones cerradas (`HistorialReversible`).**
   - La transacción más reciente se inserta al frente y la más antigua queda al final.
   - Como máximo 5 nodos (`LIMITE = 5`). Al cerrar la sexta, se elimina directamente el último nodo **sin revertirlo**.
   - Agregar, retirar la reciente y descartar la antigua cuestan O(1).
2. **Pila de cambios inversos por acción (`TransaccionAccion`).**
   - Otra `ListaDobleImpl`, con el cambio más reciente al frente.
   - Al deshacer, recorre desde ese extremo: primero la inversa de la última mutación.
3. **Objetos de cambio.**
   - `CambioAtributo`, `CambioDato` y `CambioLista` guardan la referencia afectada y el valor anterior mínimo necesario.
   - Hay cambios especializados para agenda, azar, inventario, equipo, consumo, puertas y traslados de objetos.
   - `CambioAzar` conserva el estado del generador seudoaleatorio, no una copia del juego.
4. **Agenda reversible conectada al mismo historial.**
   - `AgendaEventos` registra inserciones, extracciones, cancelaciones, reprogramaciones y cambios de secuencia mientras haya un intervalo abierto.
5. **Intervalo abierto durante la simulación.**
   - `MotorJuego.ejecutar_accion()` abre la transacción antes de aplicar la decisión y la cierra al llegar a la siguiente decisión del jugador. Los turnos enemigos, efectos, cierres de puertas, rearmes y el reloj de ese tramo pertenecen a la misma transacción.

#### Cómo se usa un pergamino (`RETROCEDER`)

1. Se valida que exista un intervalo cerrado y un pergamino seleccionado en el inventario.
2. `ServicioInventario.consumir_pergamino()` retira el pergamino **fuera del historial** y lo marca como `consumido`.
3. `HistorialReversible.deshacer_ultimo()` revierte la transacción más reciente y la quita.
4. Si la reversión falla, el motor devuelve el pergamino al inventario: un intento fallido no cuesta un pergamino.
5. No abre un intervalo, no consume tiempo virtual y no cuenta como acción del jugador.
6. Recoger o soltar un pergamino se marca como no reversible. Así, la cantidad de pergaminos queda como estaba al invocar el retroceso, menos el consumido (§2.11).

#### Correcciones respecto de la revisión anterior

1. **Cambios de colección con identidad estable.**
   - `CambioLista` ya no deshace con `pop(posicion)` sobre un índice histórico.
   - Guarda el elemento y sus vecinos `anterior` y `siguiente`. Al deshacer, localiza la **misma instancia** por identidad y calcula el lugar de restauración respecto de los vecinos que aún existen (`_posicion_restauracion`).
   - Esto resuelve el caso del pergamino recogido junto a un botín, en el que antes saltaba un `IndexError`.
2. **Reversión validada y atómica.**
   - `TransaccionAccion.revertir()` primero **simula todos los inversos** sobre vistas superficiales (`_ContextoValidacionReversion`: listas, inventarios y agendas virtuales con referencias, sin copiar entidades) y solo después aplica.
   - Ningún registro se descarta hasta terminar la validación completa. Si algo es inválido, el estado no se toca.

#### Prueba con 6 pergaminos (18/10/2026)

En una partida offline real de cripta-01 se agregaron 6 pergaminos y se hicieron 6 acciones (recoger, esperar ×2, usar antorcha, esperar ×2):

| Pergamino | Resultado | Reloj |
|---|---|---|
| 1.º–5.º | “Último intervalo retrocedido” | 475 → 375 → 275 → 225 → 125 → 25 |
| 6.º | “No hay acciones cerradas para deshacer” | se queda en 25 |

- Nunca se retroceden más de 5 acciones: la sexta no se deshace aunque queden pergaminos.
- Cada retroceso exitoso gastó un pergamino y el fallido no (quedó 1 de 6).
- Se restauraron la antorcha, su efecto, el reloj y el contador de acciones; los pergaminos no se restauraron.

#### Por qué las estructuras son adecuadas

- La lista doble exterior da O(1) para la acción más reciente (deshacer) y para la más antigua (descartar).
- La pila interior representa el orden inverso de las mutaciones: si la vida pasó de 30 a 25 y luego a 20, deshacer al revés deja 30.
- Se guardan deltas pequeños, no copias: la memoria es proporcional a los cambios de las últimas 5 acciones.
- No hay `deepcopy`, serializaciones ni instantáneas de `EstadoPartida` en el historial (lo prohíbe §2.11).

#### Costos

- Registrar un cambio O(1). Revertir una transacción O(k), con `k` cambios, más el costo de validar y aplicar cada uno.
- Localizar un elemento por identidad en una lista cuesta O(m) en el tamaño de esa lista (por ejemplo, los objetos del suelo).

#### Alternativas descartadas

- **Instantánea completa por acción:** prohibida; además, su costo depende del tamaño de todo el mapa, la agenda y el inventario.
- **Registrar solo las acciones y volver a simular:** exige reproducir desde un punto anterior y pagar muchas acciones para deshacer una.
- **Una pila global sin transacciones:** no permite saber qué cambios pertenecen a la última decisión y a sus eventos.
- **Lista de Python para las 5 transacciones:** insertar al frente o descartar al inicio desplaza referencias.
- **Guardar solo índices de listas:** los índices no son estables frente a cambios irreversibles, como mostraba el fallo corregido.

#### Sugerencia

No se requiere sustituir la estructura. Conviene mantener como regresiones `test_pergamino_botin_y_dos_retrocesos_restauran_toda_la_accion` (`tests/test_logica/test_regresiones_incumplimientos.py`) y el escenario de 6 pergaminos.

### 4.7 El rastro del jugador

**Evaluación: adecuada. La decisión de cada rastreador cuesta O(d) en las salidas de su sala y el trabajo agregado de varios rastreadores ya no es O(n²).**

#### Estructuras utilizadas

1. **Grafo mediante listas de adyacencia.**
   - Después de `vincular_salidas()`, cada `Puerta` referencia su `destino_sala`. El rastreador solo itera las puertas de su sala.
2. **Una marca temporal por sala (`Sala.ultimo_rastro`).**
   - Guarda el último instante del reloj virtual en que estuvo el jugador.
   - `RegistroRastro.obtener_tiempo()` la lee en O(1) a partir del objeto `Sala`.
   - Se actualiza con `CambioAtributo`, así que participa del retroceso.
3. **Enemigos de la sala con índices de pertenencia (`_ListaEnemigosSala`).**
   - Es una lista compatible (`list`) que además mantiene dos tablas hash propias en la sala: `_enemigos_por_id` (`id_actor → enemigo`) y `_posiciones_enemigos` (`id_actor → posición`).
   - `Sala.contiene_enemigo(actor)` comprueba la pertenencia en O(1) promedio.
   - `extraer_o1(enemigo)` intercambia el enemigo con el último y hace `pop()` del final, sin recorrer ni desplazar el resto.
   - Los índices se actualizan en `append`, en `incorporar_contenido` y al restaurar una extracción en el retroceso.
4. **Lista auxiliar de compatibilidad.**
   - `_presencias` guarda pares `(id_sala, tiempo)` solo si `RegistroRastro` se usa sin mapa. No interviene en el flujo normal.

#### Costo de la decisión de rastro

`ComportamientoEnemigos._accion_rastreador()` recorre las `d` puertas de su sala. Por cada una comprueba si está abierta, lee `destino_sala.ultimo_rastro` en O(1), calcula la edad y compara. La decisión cuesta **O(d)** y no depende de la cantidad de salas ni del largo del recorrido del jugador.

#### Política de caducidad

**Caducidad perezosa al consultar.** Un rastro es vigente si:

`0 <= reloj_actual - ultimo_rastro < 400`

Como hay un solo entero por sala, una marca vencida no hace crecer la memoria. Eliminarla activamente exigiría programar y cancelar eventos o recorrer salas, sin bajar el costo de la consulta.

#### Corrección respecto de la revisión anterior

Antes, `MotorJuego._turno_enemigo()` validaba la pertenencia con `any(e is enemigo for e in sala.enemigos)` (O(m)) y retiraba de una lista de Python desplazando elementos. Con `n` rastreadores en una sala, el total era `n(n+1)/2` visitas (55 para 10, 5.050 para 100, 45.150 para 300).

Hoy la validación usa `contiene_enemigo` (O(1) promedio) y la salida usa `extraer_o1` (O(1)). Procesar `a` rastreadores cuesta O(a + Σdᵢ), más los costos O(log n) de la agenda (§4.1).

El intercambio con el último elemento cambia el orden físico de la lista, pero no afecta el determinismo: el orden en que actúan los enemigos lo decide la agenda por `(tiempo, secuencia)`.

#### Por qué algunas alternativas no son adecuadas

- **Lista con todas las visitas del jugador:** la decisión dependería del largo del recorrido y la memoria crecería con cada acción.
- **Búsqueda global de salas con rastro:** O(V) por rastreador.
- **BFS o DFS:** contradice la regla de mirar solo vecinos y cuesta O(V + E).
- **Eventos de expiración por rastro:** agrandan la agenda y el historial sin ahorrar memoria.
- **Solo una lista de Python:** pertenencia y retiro O(m), lo que llevaba al O(n²) corregido.

#### Sugerencia

No se requiere sustituir la estructura. Conviene conservar la prueba que cuenta las visitas con 10, 100 y 300 rastreadores para que no vuelva el costo cuadrático.

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

**Evaluación: adecuada. Los dos algoritmos propios, la selección adaptativa y la estabilidad se usan en todos los contextos evaluados, incluido el índice del guardado, y una prueba estática impide volver a ordenamientos de biblioteca.**

#### Estructuras y algoritmos utilizados

1. **Arreglos auxiliares de referencias.**
   - `OrdenadorAdaptativo` recibe una lista y devuelve una lista nueva; la original no cambia.
   - Las claves se calculan una sola vez y se guardan junto a cada referencia.
2. **Insertion sort estable.**
   - Desplaza solo elementos con clave estrictamente mayor, así conserva el orden de los empates.
   - Cuesta O(n + I), donde `I` es la cantidad de inversiones: es lineal solo si `I = O(n)`. El peor caso sin límite es O(n²).
3. **Merge sort estable.**
   - En empate toma primero el de la mitad izquierda.
   - O(n log n) en tiempo y O(n) de memoria auxiliar.
4. **Selector adaptativo.**
   - Con `n ≤ 16` usa insertion sort (`LIMITE_PEQUENO = 16`).
   - Con más elementos intenta insertion sort con un límite de `n` desplazamientos (`FACTOR_DESPLAZAMIENTOS = 1`). Si lo supera, descarta su copia y aplica merge sort reutilizando las claves ya calculadas.

#### Propiedades medibles utilizadas para elegir

- **Cantidad de elementos**, con el umbral 16.
- **Desplazamientos reales necesarios**, con el intento limitado a `n`.

Una lista grande ya ordenada termina en O(n). Una invertida supera pronto el límite y pasa a merge sort; el intento fallido solo suma trabajo lineal.

#### Contextos integrados

1. **Vistas del inventario** por peso, valor o nombre (`ServicioInventario.vista_ordenada`), sin tocar nodos, cursor ni orden real.
2. **Puntajes** por acciones, enemigos derrotados o reloj final (`RepositorioPuntajes.listar_ordenados`), sin reescribir el archivo.
3. **Catálogo y carga de contenido:** IDs de fichas antes de formar lotes y pares `(distancia, id_sala)` del BFS de `CargadorContenido`.
4. **Índice del guardado binario:** `GuardadoBinario` ordena los offsets de las salas por ID con `OrdenadorAdaptativo`. Antes usaba `list.sort()`; está **corregido**.
5. **Archivos del paquete offline:** `FuenteOffline` ordena los archivos `contenido_*.json` con el mismo ordenador.

#### Prueba de restricciones

`tests/test_restricciones_enunciado.py` revisa el código de producción con AST (no por texto, así que comentarios y cadenas no dan falsos positivos). Falla si aparece `sorted`, `.sort()`, `set`, `heapq`, `bisect`, `deque`, `OrderedDict`, `defaultdict` o `Counter` en `datos/`, `logica/`, `service/`, `controller/`, `dto/` o `estructuras/`. La vista y los benchmarks quedan fuera a propósito: la vista no resuelve problemas de §4 y los benchmarks miden alternativas de biblioteca.

#### Evidencia empírica

- `benchmarks/integrante3.py` mide tamaños 8, 16, 32, 64, 128 y 512 con datos ordenados, casi ordenados, invertidos y aleatorios, y con un criterio simple y otro costoso.
- Compara insertion, merge, el adaptativo y `sorted()` solo como referencia externa, y calibra factores de desplazamiento 1, 2, 4 y 8 (`docs/mediciones_integrante3_calibracion.json`).
- Con datos invertidos: 6,8 µs frente a 8,8 µs en `n = 8`, y 86,7 µs frente a 44,7 µs en `n = 32`, lo que sustenta el umbral 16. Con `n = 512`: 33,75 ms insertion, 1,43 ms merge y 1,82 ms el adaptativo.

#### Por qué se complementan ambos algoritmos

- Insertion sort es simple y estable, y aprovecha datos pequeños o casi ordenados, pero se degrada con muchas inversiones.
- Merge sort mantiene O(n log n) en cualquier caso, pero usa memoria auxiliar y tiene más sobrecarga en entradas pequeñas.
- El intento acotado obtiene lo mejor de insertion sin aceptar su peor caso.

#### Alternativas descartadas

- **Siempre insertion sort:** O(n²) en colecciones grandes desordenadas.
- **Siempre merge sort:** desaprovecha los datos pequeños u ordenados.
- **Medir solo el tamaño:** no distingue una lista ordenada de una invertida.
- **Contar todas las inversiones antes:** hacerlo ingenuamente cuesta O(n²).
- **Quicksort:** no es estable en su versión simple y puede caer a O(n²).
- **Heap sort:** no es estable de forma natural y no aprovecha datos casi ordenados.
- **`list.sort()` o `sorted()`:** prohibidos en estos contextos.

#### Sugerencia

Conservar el selector y volver a calibrar los umbrales si cambian el entorno, el costo de las claves o los tamaños reales.

### 4.10 Guardado binario de la partida

**Evaluación: adecuada. Formato binario propio (versión 7) con índice ordenado para leer una sala sin cargar el archivo, detección de versión, textos de largo variable y una comparación reproducible contra JSON.**

#### Estructuras utilizadas

1. **Cabecera binaria fija.**
   - `HEADER_FORMAT = "<4sHqIIII"` (little-endian, 30 bytes): firma `CRPT`, versión `7`, semilla, reloj, cantidad de salas, offset del índice y offset del jugador.
   - El ID de la cripta y las versiones ya no van en bloques fijos de 32 bytes: se escriben como texto de largo variable.
2. **Textos de largo variable.**
   - Cada texto es un `uint16` con el largo más los bytes UTF-8 (`_texto`), hasta 65.535 bytes.
   - En la versión 5 cada ID ocupaba 32 bytes fijos, lo que limitaba los IDs y desperdiciaba espacio. Ahora un ID largo del API se puede guardar (§9) y el archivo es más chico (por ejemplo, cripta-04 bajó de 30.914 a 16.958 bytes).
3. **Registros de sala secuenciales.**
   - Cada sala empieza con su ID y las cantidades de puertas, enemigos, objetos y trampas, que permiten decodificar sus segmentos variables.
   - **Versión 7:** cada sala incluye un byte `contenido_cargado`. Una partida guardada con salas pendientes (carga gradual, §4.2) las sigue cargando al continuar.
   - Datos internos de forma variable, como los eventos o el estado del azar, van como JSON delimitado por largo; el del azar, comprimido con zlib. El archivo sigue siendo binario: cabecera, offsets e índice son propios.
4. **Índice ordenado al final del archivo.**
   - Una entrada por sala: ID (32 bytes) y offset (4 bytes).
   - Se ordena por ID con `OrdenadorAdaptativo` (antes con `list.sort()`; corregido).
5. **Tabla hash de salas en la carga completa.**
   - `cargar()` reconstruye `id_sala → registro` en una `TablaHashImpl` propia, no en un `dict` (§7).
6. **Archivo temporal y reemplazo atómico.**
   - `guardar()` escribe en un temporal, valida que se pueda reconstruir y recién entonces usa `os.replace()`. Un fallo no destruye el guardado anterior.

#### Recuperación de una sala específica (`leer_sala`)

1. Leer solo la cabecera y comprobar firma y versión.
2. Validar con `seek()` que el índice termina exactamente al final del archivo.
3. Saltar al índice, leer sus `36·n` bytes y hacer **búsqueda binaria** por ID.
4. Buscar en el índice el offset siguiente para saber dónde termina el registro.
5. Saltar al registro, leer solo sus bytes, decodificarlo y comprobar el ID.

La búsqueda cuesta O(log n), pero la operación completa es O(n + r): se lee todo el índice y se recorre para hallar el final del registro. No se leen el jugador, los extras ni las demás salas, que es lo que exige §4.10.

#### Detección de versión

- `cargar()` y `leer_sala()` exigen la firma `CRPT` y la versión 7. Un archivo v5 o v6 se rechaza y el servicio informa “versión incompatible”, en lugar de interpretarlo mal.
- También se validan el tamaño mínimo, la posición del jugador, el final exacto del índice, los offsets y los largos.
- Al cargar se inicia un historial vacío: el retroceso no viaja en el guardado.

#### Complejidades principales

- **Guardado:** O(B + n log n), con `B` bytes serializados y `n` salas (el índice usa el ordenador propio).
- **Carga completa:** O(B).
- **Una sala:** O(n + r) de tiempo y bytes leídos.
- **Versión:** O(1), dentro de la cabecera.

#### Comparación reproducible contra JSON

`python main.py --bench` ejecuta `benchmarks/integrante2.py::medir_guardado` sobre las 4 criptas publicadas. El JSON contiene **exactamente el mismo estado lógico** que devuelve `GuardadoBinario.cargar`, y el benchmark verifica que ambos formatos devuelvan la misma sala. Resultados (versión 7, medidos el 18/10/2026, mediana, `docs/comparacion_binario_json.md`):

| Cripta | Bytes binario / JSON | Leer 1 sala binario / JSON | Cargar todo binario / JSON |
|---|---|---|---|
| cripta-01 (6 salas) | 5.359 / 12.709 | 219 / 304 µs | 472 / 324 µs |
| cripta-04 (50 salas) | 17.008 / 43.328 | 213 / 601 µs | 1.209 / 607 µs |

- **Leer una sala**, la razón del formato: el binario se mantiene casi constante y con 50 salas es 2,8 veces más rápido; en JSON crece porque hay que parsear todo.
- **Tamaño:** el binario ocupa entre un 58 y un 61 % menos.
- **Guardar:** en criptas chicas el binario es más lento por la escritura temporal y la validación; con 50 salas quedan parejos (2,8 ms frente a 3,2 ms).
- **Cargar todo:** JSON es unas 2 veces más rápido, porque `json.load` está en C y el binario decodifica y valida campo por campo. La diferencia es de 1 a 2 ms por partida.

#### Por qué las estructuras son adecuadas

- La cabecera fija ubica las secciones sin analizar los registros.
- Los offsets convierten la búsqueda de una sala en un acceso dirigido.
- El índice al final permite escribir el flujo una sola vez y completar la cabecera después.
- La escritura temporal protege el guardado anterior.

#### Alternativas descartadas

- **JSON como formato principal:** más simple de inspeccionar, pero repite nombres de campos y obliga a leer el documento entero para una sala.
- **Binario sin índice:** obliga a recorrer los registros anteriores.
- **Tabla hash serializada:** complica colisiones y portabilidad en un archivo estático.
- **Árbol B o base embebida:** complejidad innecesaria para una instantánea que no se modifica en el lugar.
- **`pickle`:** no es un formato controlado ni portable, y no debe cargarse desde fuentes no confiables.

#### Sugerencias

1. Guardar en el índice el largo de cada registro, para que `leer_sala()` no recorra el índice buscando el final y baje a O(log n + r). **Decisión: no se hace antes de la entrega**: obligaría a una versión 8 que invalida los guardados v7, y la ganancia es mínima (el índice de 50 salas son 1.800 bytes y la búsqueda ya es binaria).
2. La tabla de `docs/comparacion_binario_json.md` ya está medida con la versión 7 (18/10/2026); conviene volver a correr `--bench` si cambia el formato.

### 4.11 Bitácora de partida y reproducción

**Evaluación: adecuada. Cada partida reproducible crea su bitácora automáticamente; el formato append-only, la validación completa, la reproducción determinista y el rechazo de versiones incompatibles cumplen el punto.**

#### Estructuras utilizadas

1. **Archivo secuencial JSON Lines.**
   - Cada línea es un objeto JSON independiente en UTF-8.
   - La primera es una cabecera con `cripta_id`, `version_cripta`, `version_catalogo` y `semilla`.
   - Cada línea posterior es una acción con su tipo, el ID estable del objetivo y la dirección.
2. **Creación exclusiva y anexado.**
   - `RegistroPartida.crear()` abre con modo `x`: nunca trunca un archivo existente.
   - `anexar_accion()` abre con modo `a`: cada acción se escribe al final sin reescribir lo anterior.
3. **Marca de identidad del archivo activo.**
   - `JuegoService` conserva dispositivo, inodo, tamaño y fecha del log, y antes de cada acción detecta si alguien lo borró, lo reemplazó o lo modificó.
4. **Arreglo de acciones validado antes del replay.**
   - `EjecutorReplay._leer_log()` valida todas las líneas y guarda pares `(número_de_línea, registro)` antes de ejecutar nada.
5. **Versiones esperadas.**
   - El replay compara `(version_cripta, version_catalogo)` con la fuente. Si no coinciden, busca una copia offline compatible; si tampoco hay, aborta con un error explícito.
6. **IDs estables en lugar de referencias de memoria.**
   - Actores y objetos se registran por `id_actor` o `id_instancia`. `EQUIPAR` guarda el ID del objeto seleccionado, porque mover el cursor no es una acción registrada.

#### Funcionamiento del registro

- **Corrección:** antes la bitácora solo existía si el jugador escribía `registro RUTA`. Hoy, `ControladorJuego._iniciar_registro_automatico()` crea un archivo nuevo y único en `partidas/logs/<cripta>-<fecha>-<uuid>.log` al iniciar cada cripta reproducible, **antes** de la primera acción, en consola y en Pygame. La ruta se muestra al iniciar.
- `registro RUTA` sigue disponible para elegir otra ruta, pero solo antes de la primera acción. Si falla el cambio, se conserva la conexión anterior.
- Si la creación automática falla, el juego avisa que la partida no se podrá reproducir.
- Al cargar una partida guardada o usar `--demo`, se avisa la limitación sin crear un inicio de replay ficticio.
- Solo se anotan las acciones exitosas. Si la escritura falla después de que el motor ya actuó, se informa, no se repite la acción y se bloquean las siguientes para no ampliar la divergencia.

#### Funcionamiento del replay

1. Lee y valida todo el archivo antes de modificar una partida.
2. Rechaza líneas vacías, JSON inválido, claves duplicadas, campos desconocidos, tipos incorrectos y acciones fuera del vocabulario.
3. Comprueba las versiones contra la fuente y, si no coinciden, busca una copia offline con ambas versiones.
4. Usa la semilla de la cabecera y el mismo `InicializadorPartida`, `JuegoService` y `MotorJuego` que el juego normal.
5. Si una acción ya no es posible, informa su número de línea y se detiene.
6. `main.py --replay` corre sin vista ni entrada; si el archivo no existe, muestra un mensaje en vez de un traceback.

#### Complejidad

- Validar y almacenar el log: O(a) en tiempo y memoria, con `a` registros.
- Anexar una acción: serializar y escribir cuesta O(b) en los bytes del registro, O(1) si el tamaño está acotado. No se relee el archivo anterior.
- Resolver cada objetivo recorre los enemigos de la sala o el inventario: O(e) u O(i).

#### Comprobaciones realizadas

- Las pruebas crean una partida sin ejecutar `registro`, hacen acciones y reproducen el log. Comparan reloj, jugador, inventario, equipo, sala, azar y eventos pendientes, y confirman que `--replay` no crea otro archivo ni modifica el original.
- En la prueba offline del 18/10/2026, el replay de un log real terminó sin errores.

#### Por qué JSON Lines es adecuado

- Cada línea es una unidad independiente, fácil de inspeccionar y adjuntar a un reporte.
- El modo append agrega sin leer ni reescribir lo anterior.
- Una línea dañada se localiza por su número y se rechaza antes de ejecutar.
- Los IDs estables evitan depender de direcciones de memoria.

#### Alternativas descartadas

- **Un arreglo JSON único:** se lee más rápido (512 acciones: 0,48 ms frente a 2,09 ms), pero para anexar hay que reescribir el cierre del arreglo o el documento completo.
- **Texto separado por espacios o CSV:** necesitan reglas propias de escape y no expresan bien los argumentos opcionales.
- **Formato binario:** dificulta inspeccionar el archivo como reporte de error, y la sección pide texto.
- **Instantáneas por acción:** multiplican el tamaño y ocultan la secuencia de decisiones.
- **Nombres visibles como objetivos:** pueden repetirse o cambiar; los IDs no.

#### Sugerencias

1. Mostrar un mensaje al terminar un replay correcto (por ejemplo, “Replay reproducido: N acciones”); hoy termina en silencio.
2. Para logs muy grandes, validar en una primera pasada sin acumular registros y ejecutar en una segunda.

## Resumen para la defensa

| Punto | Estructura principal | Operación clave y costo | Responsable |
|---|---|---|---|
| 4.1 Agenda | Montículo mínimo indexado + 3 AVL (`IndiceOrdenado`) | Siguiente evento O(1) consultar, O(log n) extraer; cancelar por ID O(log n) | Sofía |
| 4.2 Carga gradual | Grafo por adyacencia + `Sala.contenido_cargado` + BFS por distancia | Lotes de ≤10 salas más cercanas; incorporación en orden de solicitud | Steven |
| 4.3 Catálogo | Lotes de ≤10 IDs + `CatalogoVivo` + repositorio memoria → disco → red | Una ficha por tipo; botín resuelto de forma transitiva | Steven |
| 4.4 Caché | LRU: `ListaDobleImpl` + arreglo ordenado (búsqueda binaria), fijación por dueño; disco por ID | Acierto O(log c) + mover al frente O(1); desalojada → disco sin red | Steven |
| 4.5 Inventario | Lista doble + cursor al nodo | Avanzar, soltar y mover al frente O(1); vistas ordenadas en copia | Joshua |
| 4.6 Retroceso | Lista doble de ≤5 transacciones + pila de cambios inversos | Registrar O(1), deshacer O(k); validación completa antes de aplicar | Joshua y Sofía |
| 4.7 Rastro | `ultimo_rastro` por sala + enemigos con índice hash por sala | Decisión O(d); pertenencia y retiro O(1) | Sofía |
| 4.8 Bitácora | Cola circular de 20 | Agregar O(1), memoria fija | Joshua |
| 4.9 Ordenamiento | Insertion (≤16 o pocos desplazamientos) + Merge | O(n + I) o O(n log n), estables; prueba AST contra `sorted`/`.sort()` | Joshua |
| 4.10 Guardado | Binario v7: cabecera + registros + índice ordenado | Leer una sala con búsqueda binaria sin leer el archivo | Steven |
| 4.11 Replay | JSON Lines append-only, log automático | Anexar O(b); validar todo antes de reproducir | Joshua |

**Preguntas probables y dónde está la respuesta:**

- *¿Por qué la caché no usa tabla hash?* Por indicación del profesor: arreglo ordenado con búsqueda binaria (§4.4). Las tablas hash propias (`TablaHashImpl`) sí se usan fuera de la caché, por ejemplo en el contenido por sala, la carga del guardado y los enemigos de cada sala.
- *¿Cómo sé que `--cache-size` limita la memoria real?* Las entidades no guardan la ficha (`FichaResoluble`); la única copia es la de la caché (§4.4).
- *¿Qué pasa si una cripta no cabe en el presupuesto?* Carga gradual por cercanía (§4.2).
- *¿Por qué el retroceso no usa copias?* Lo prohíbe §2.11: se guardan solo los cambios inversos de las últimas 5 acciones (§4.6).
- *¿Por qué binario y no JSON?* Para leer una sala sin cargar el archivo completo: 2,9 veces más rápido con 50 salas (§4.10).
- *¿Dónde se elige offline?* Solo con `--offline` al lanzar; el modelo no sabe si los datos vienen de HTTP o de archivos (§3.4).
