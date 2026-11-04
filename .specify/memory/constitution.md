<!--
Sync Impact Report
- Cambio de versión: plantilla sin completar → 1.0.0 (ratificación inicial)
- Principios definidos (todos nuevos; la plantilla tenía 5 marcadores, se usan 11):
  I. Estructuras propias en los problemas evaluados
  II. Acceso por identificador eficiente
  III. Determinismo
  IV. Separación MVC
  V. Datos desde el servicio
  VI. Presupuesto de solicitudes
  VII. Estado reversible sin copias completas
  VIII. Contratos estables y cambios mínimos
  IX. Rendimiento medido
  X. Especificación primero y trazabilidad
  XI. Pruebas
- Secciones añadidas: Restricciones técnicas; Flujo de trabajo y puertas de calidad; Gobernanza
- Secciones eliminadas: ninguna
- Plantillas dependientes: no se modifican (leen la constitución en tiempo de ejecución)
- TODO diferidos: ninguno
-->

# Constitución del Proyecto Cripta

Proyecto Cripta, Estructuras de Datos, II-2026. Segunda parte, construida sobre el código ya
entregado en la primera parte.

## Principios fundamentales

### I. Estructuras propias en los problemas evaluados

- Las estructuras de datos de los problemas evaluados (agenda, índices, cachés, búsquedas de
  ruta, mapa conocido, resolubilidad, línea de tiempo e historial) DEBEN implementarse a mano.
- Está PROHIBIDO usar `dict` o `set` como índice, caché o tabla de búsqueda.
- Están PROHIBIDOS `heapq`, `bisect`, `collections` (`deque`, `OrderedDict`, `defaultdict`,
  `Counter`), `networkx` y cualquier biblioteca de grafos o de rutas.
- Están PROHIBIDOS `sorted()` y `list.sort()` en los ordenamientos evaluados.
- Se PERMITEN `dict` para leer JSON y `list` como almacenamiento contiguo de bajo nivel.
- Las alternativas de biblioteca SOLO pueden aparecer dentro de `--bench`, como comparación.

**Justificación**: el curso evalúa el diseño y la implementación de las estructuras. Usar una
biblioteca en su lugar elimina justamente lo que se evalúa.

**Verificación**: revisión de importaciones y usos en los módulos evaluados (búsqueda de
`heapq`, `bisect`, `collections`, `networkx`, `sorted(`, `.sort(` y `dict`/`set` usados como
índice). Todo `plan.md` o tarea que proponga una dependencia prohibida es un defecto que
`/speckit-analyze` DEBE señalar.

### II. Acceso por identificador eficiente

- Toda búsqueda frecuente por id (salas, actores, objetos, puertas) DEBE usar una estructura
  propia con acceso esperado O(1), como la tabla hash propia ya existente.
- No se aceptan recorridos lineales en operaciones que se ejecutan en cada turno o en cada
  búsqueda de ruta.

**Justificación**: estas búsquedas están en el camino crítico de cada turno y de cada ruta. Un
recorrido lineal ahí multiplica el costo y compromete los límites del Principio IX.

**Verificación**: `plan.md` declara la estructura de cada búsqueda por id. La revisión de código
rechaza recorridos lineales en el ciclo de turno y en la búsqueda de ruta. `--bench` mide el
acceso por id frente a una alternativa lineal.

### III. Determinismo

- La misma cripta, la misma semilla y las mismas acciones DEBEN producir la misma partida.
- El modelo usa SOLO su instancia `random.Random(semilla)`. Ningún otro generador aleatorio.
- La hora real y la latencia de red NUNCA alteran la simulación.
- La agenda desempata primero por tiempo virtual y luego por número de secuencia.
- Todo desempate nuevo (por ejemplo, «la vecina de menor id») DEBE definirse en la
  especificación, de forma independiente del algoritmo que lo implemente.

**Justificación**: sin determinismo no hay repetición (`--replay`), ni verificación
reproducible, ni comparación justa entre integrantes o entre estructuras.

**Verificación**: pruebas que ejecutan dos veces la misma cripta, semilla y secuencia de acciones
y comparan el registro de partida resultante. Revisión de que no se usen `random` global,
`time` ni la latencia dentro del modelo.

### IV. Separación MVC

- El modelo contiene las reglas y el estado.
- La vista solo presenta y recoge interacción. No introduce reglas ni altera resultados.
- El controlador interpreta comandos y coordina.
- Red y disco quedan detrás de adaptadores.
- `--replay`, `--bench` y `--verificar` NUNCA instancian la vista.

**Justificación**: permite probar y medir las reglas sin interfaz gráfica, y cambiar la vista o
el origen de datos sin tocar el modelo.

**Verificación**: el modelo no importa `pygame` ni `requests`. Los modos `--replay`, `--bench`
y `--verificar` se ejecutan sin inicializar la vista. Pruebas del modelo sin vista.

### V. Datos desde el servicio

- Ningún dato de una cripta concreta (estadísticas, cantidades, costos, rangos, ubicaciones de
  llaves) se escribe en el código.
- Todo dato viene del servicio o de la fuente offline compatible.
- Lo persistido se invalida mediante la validación de versión existente, NUNCA borrando
  archivos a mano.

**Justificación**: el juego debe funcionar con cualquier cripta que entregue el servicio. Los
valores incrustados ocultan errores y rompen con criptas nuevas.

**Verificación**: revisión de código sin constantes propias de una cripta. Pruebas con al menos
dos criptas distintas o fixtures. Prueba de que los datos persistidos de la cripta con versión
incompatible se invalidan y se vuelven a solicitar. Prueba de que un archivo de partida de la
primera parte se reporta como incompatible o se migra explícitamente, y nunca se carga en
silencio.

### VI. Presupuesto de solicitudes

- Se respeta `presupuesto_solicitudes`, que viene de la cripta a través del contrato
  `FuenteDatos`.
- Toda solicitud HTTP cuenta, incluidos los reintentos y la consulta de llaves.
- El tiempo real de espera no avanza el reloj virtual.

**Justificación**: el servicio limita las solicitudes. Excederlo invalida la partida, y mezclar
la espera real con el reloj virtual rompe el Principio III.

**Verificación**: pruebas con una fuente simulada que cuenta solicitudes (reintentos incluidos)
y confirman que nunca se supera el presupuesto, y que una espera simulada no cambia el tiempo
virtual.

### VII. Estado reversible sin copias completas

- Todo cambio de estado del juego, incluido el conocimiento del jugador, DEBE registrarse como
  un cambio reversible. Sirve al pergamino de retroceso (límite de 5 acciones) y a la línea de
  tiempo.
- El retroceso NO se implementa con copias completas del estado.
- La prohibición aplica a copias completas en memoria usadas como mecanismo de retroceso o de
  línea de tiempo. El archivo de guardado de partida no cuenta como copia prohibida.
- Las únicas copias completas permitidas son los puntos de control de la línea de tiempo, como
  máximo uno cada K acciones del jugador.
- Las acciones rechazadas no consumen tiempo ni dejan cambios parciales.
- Las consultas (historia, mapa, estado) no modifican el estado ni el historial.

**Justificación**: copiar el estado completo en cada acción es costoso en memoria y tiempo, y
esconde qué cambió. Los cambios reversibles hacen el retroceso exacto y barato.

**Verificación**: pruebas de hacer y deshacer que comparan el estado antes y después (incluido el
conocimiento del jugador). Pruebas de que una acción rechazada deja estado, reloj e historial
iguales. Pruebas de que las consultas no alteran nada. Revisión de que no hay copias completas
fuera de los puntos de control.

### VIII. Contratos estables y cambios mínimos

- Se conservan nombres, firmas, constructores y archivos que usan otros integrantes.
- La identidad de las instancias se mantiene por sus ids reales.
- Antes de modificar un componente compartido se identifican sus consumidores y el cambio se
  acuerda en `plan.md`.
- Se preservan las decisiones ya entregadas en la primera parte: carga gradual de contenido,
  catálogo vivo con protección de fichas activas, lotes de hasta diez ids, registro de partida
  JSON Lines con ids estables y creación automática del log, y guardado binario versionado.

**Justificación**: tres integrantes trabajan en paralelo sobre código ya entregado. Romper un
contrato compartido rompe el trabajo de otro y lo ya evaluado.

**Verificación**: `plan.md` lista los consumidores de cada componente compartido que toca. Las
pruebas existentes de la primera parte siguen pasando. Revisión de diferencias en firmas
públicas.

### IX. Rendimiento medido

- Toda afirmación de rendimiento o complejidad se respalda con `--bench`.
- Cada medición compara la estructura elegida contra al menos una alternativa descartada.
- Cada medición separa la preparación del intervalo cronometrado, usa calentamiento y
  repeticiones, y genera criptas sintéticas deterministas por semilla.
- Las mediciones DEBEN estar conectadas a `--bench`. Un benchmark que ningún punto de entrada
  ejecuta no cuenta como evidencia.
- Las operaciones de cada subsistema (no solo la operación masiva) se miden con cargas
  realistas: ciclos sobre criptas reales y operaciones de punta a punta, no solo la estructura
  aislada.
- Límites:
  - ciclo de eventos: 20 ms entre dos decisiones del jugador, en la cripta de referencia con
    decenas de cazadores;
  - resolubilidad: 200 ms en la cripta publicada más grande;
  - historia: 50 ms con al menos 5 000 acciones del jugador y K por defecto;
  - paso de «ir a»: 5 ms con el mapa conocido completo de la cripta de referencia.
- Estos valores pueden ajustarse por enmienda del enunciado.

**Justificación**: la elección de una estructura solo se defiende con datos, medidos en
condiciones reales y comparables.

**Verificación**: `--bench` ejecuta cada medición declarada en `plan.md` e informa estructura
elegida, alternativa y límite. Una afirmación de rendimiento sin medición en `--bench` es un
defecto.

### X. Especificación primero y trazabilidad

- Cada capacidad tiene su `spec.md` confirmado en Git antes de su código.
- `spec.md` describe reglas, historias, escenarios y requisitos numerados (FR-xxx), sin nombrar
  estructuras, clases ni módulos.
- `plan.md` elige estructuras y no inventa reglas.
- Cada tarea cita sus FR y cada prueba cita el FR que verifica.
- Cada caso del Apéndice B es un escenario con prueba o con un `partida.log`.
- Si la especificación estaba mal, se corrige primero la especificación y luego el código, en
  commits separados.
- Cada comando de spec-kit con texto propio se registra en `PROMPTS_LLM.md`.

**Justificación**: separar el qué (spec) del cómo (plan) permite revisar las reglas sin
detalles de implementación y rastrear cada línea de código hasta un requisito.

**Verificación**: el historial de Git muestra `spec.md` antes que el código de la capacidad.
`/speckit-analyze` detecta tareas o pruebas sin FR, casos del Apéndice B sin cobertura y nombres
de estructuras o módulos dentro de `spec.md`. `PROMPTS_LLM.md` tiene una entrada por comando con
texto propio.

### XI. Pruebas

- Se mantienen `unittest` y `pytest`.
- Las pruebas nuevas no rompen las existentes.
- Se distingue entre pruebas aprobadas, omitidas, con fixtures de API y contra el servicio en
  línea.

**Justificación**: el código de la primera parte ya tiene pruebas. La suite debe seguir verde y
dejar claro qué depende del servicio en línea.

**Verificación**: la suite completa se ejecuta con `pytest`, que también ejecuta las pruebas
escritas con `unittest`. El informe separa
aprobadas, omitidas, con fixtures y en línea. Ninguna prueba previa pasa a fallar.

## Restricciones técnicas

- Python 3.11 o superior.
- Sin dependencias nuevas. Solo se permiten `requests` y `pygame`, ya existentes.
- Las bibliotecas prohibidas por el Principio I solo pueden importarse dentro de `--bench`.
- Puntos de entrada que DEBEN existir y respetar los Principios III y IV: juego normal,
  `--replay`, `--replay partida.log --hasta t`, `--bench`, `--verificar`, `--forzar` y
  `--checkpoint-cada K`.

## Flujo de trabajo y puertas de calidad

1. `/speckit-specify` produce `spec.md`, que se confirma en Git antes de escribir código.
2. `/speckit-plan` produce `plan.md`, que elige estructuras, lista los consumidores de
   componentes compartidos y declara las mediciones de `--bench`.
3. `/speckit-tasks` produce `tasks.md`, donde cada tarea cita sus FR.
4. `/speckit-analyze` DEBE ejecutarse antes de implementar y verificar cada principio. Toda
   violación se corrige antes de `/speckit-implement`.
5. Al implementar, la suite de pruebas sigue verde y `--bench` cubre las afirmaciones de
   rendimiento.
6. Cada comando de spec-kit con texto propio se registra en `PROMPTS_LLM.md`.

## Gobernanza

- Esta constitución prevalece sobre `spec.md`, `plan.md` y `tasks.md`. Ante un conflicto, se
  corrige el documento dependiente, no la constitución.
- Una enmienda requiere el acuerdo de los tres integrantes, un nuevo número de versión y la
  fecha de la enmienda.
- Versionado semántico:
  - MAYOR: se elimina o redefine un principio de forma incompatible.
  - MENOR: se agrega un principio o sección, o se amplía de forma material.
  - PARCHE: aclaraciones, redacción o erratas sin cambio de significado.
- `/speckit-analyze` verifica el cumplimiento de cada principio antes de implementar. Toda
  revisión de código también lo verifica.

**Versión**: 1.0.0 | **Ratificada**: 2026-11-02 | **Última enmienda**: 2026-11-02
