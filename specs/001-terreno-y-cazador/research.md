# Research: Terreno y cazador

Este documento registra decisiones de diseño provisionales. Las afirmaciones de rendimiento son hipótesis que `--bench` debe confirmar; no son resultados medidos.

## R-01 — Estrategia provisional de rutas

**Decision**: usar una búsqueda ponderada individual, desde cada cazador y limitada por su rango, como estrategia de producción inicial (`FR-007`–`FR-010`, `PR-002`). Implementar la alternativa inversa compartida como comparación de `--bench`, no como optimización asumida.

**Rationale**: la búsqueda individual no inserta candidatos cuyo costo ya supere el rango y solo expande salas fijadas dentro de él. Como los costos son positivos, una ruta que ya excedió el rango no puede volver a entrar. Esto evita recorrer o inicializar el exterior, aunque dentro de la región pertinente deben contarse por separado salas fijadas, salas descubiertas y todas las entradas almacenadas en frontera. También reduce el riesgo de invalidación y ofrece una referencia de producción simple frente a la cual validar reutilización.

**Alternatives considered**:

- **Una búsqueda inversa completa desde el jugador**: amortiza trabajo entre decenas de cazadores, pero paga potencialmente `V+E` aunque un único cazador tenga rango pequeño.
- **Búsqueda inversa limitada al rango máximo activo**: puede compartir trabajo, pero un solo rango grande amplía la región para todos y requiere gestionar cazadores fuera de la región.
- **Estrategia adaptativa**: prometedora, pero el umbral depende de cantidad/distribución de cazadores, rangos y estabilidad de puertas. No se fija sin datos.

**Measurement that may change the decision**: costo completo por ciclo para uno/decenas de cazadores, rangos pequeños/grandes y puertas estables/inestables. Si la compartida reduce consistentemente el ciclo completo, mantiene `PR-002`, pasa equivalencia y cumple `<20 ms`, puede habilitarse para el segmento medido.

## R-02 — Desempate independiente del descubrimiento

**Decision**: en búsqueda hacia adelante, propagar la etiqueta `(distancia, primera_vecina_id)` y priorizar lexicográficamente; usar `sala_id` solo como tercer componente determinista (`FR-011`, `FR-015`). En la alternativa inversa, calcular distancias y seleccionar al final el mínimo `(costo_salida + distancia_vecino, vecino_id)`.

**Rationale**: el primer componente obtiene el costo mínimo y el segundo codifica exactamente la regla observable. Con pesos positivos, un camino alternativo de igual costo llega a través de un predecesor con menor distancia, por lo que puede actualizar el objetivo antes de que este se fije. La prioridad por primera vecina impide que el orden de las puertas o de inserción decida el resultado.

**Alternatives considered**:

- **Aceptar el primer camino encontrado**: rechazado; depende del orden de descubrimiento.
- **Ordenar previamente todas las listas de vecinos**: insuficiente por sí solo y prohibiría apoyarse en `sorted()`/`.sort()`; una ruta descubierta después aún puede empatar con primera vecina menor.
- **Reconstruir un único predecesor al final**: insuficiente si los empates intermedios descartaron la primera vecina correcta.

## R-03 — Estructuras auxiliares propias y perezosas

**Decision**: reutilizar `MonticuloMinimo` con entradas inmutables duplicadas y `TablaHashImpl` para mejores etiquetas y salas fijadas. Se verificó que el montículo actual tiene `insertar`, `extraer_minimo`, `ver_minimo` y eliminación de una referencia conocida, pero no una operación para actualizar prioridad. Cada mejora inserta otra entrada; al extraer, se descarta si no coincide con la mejor etiqueta vigente o la sala ya fue fijada. El diseño no usa actualización en sitio ni atribuye decrease-key al montículo.

**Rationale**: cumple la constitución y evita inicializar `V` posiciones por cazador o mantener un handle mutable por sala. Si `D_R` es la cantidad de salas distintas descubiertas, `E_R` cuenta todas las salidas inspeccionadas —también las cerradas—, `P_R` las entradas insertadas y `Q_R` la frontera máxima, la memoria es O(`D_R+Q_R`), con peor caso O(`D_R+E_R`) porque cada relajación exitosa puede insertar un duplicado. El tiempo esperado completo es O(`E_R + P_R log max(2,Q_R) + Q_fin`), incluyendo salidas examinadas, inserciones/extracciones vigentes u obsoletas y limpieza de la frontera restante.

**Alternatives considered**:

- **Arreglo indexado por ID**: los IDs no garantizan densidad y su inicialización global viola el objetivo de rango pequeño.
- **`heapq`, `dict`, `set` o bibliotecas de rutas**: prohibidos en producción.
- **Una entrada por sala con actualización de prioridad**: requeriría una operación que el montículo actual no publica o un contrato nuevo de handles/eliminación y reinserción; se descarta para mantener el cambio mínimo y medir explícitamente los duplicados.
- **Explorar linealmente la menor distancia**: sirve como alternativa comparable/oráculo, pero cuesta O(`D_R²+E_R`) para las salas descubiertas y salidas examinadas.

## R-04 — Índice de `MapaCripta`

**Decision**: conservar `_salas` para recorrido determinista y referencias, y añadir `TablaHashImpl` ID→sala. Para un ID existente, localizar linealmente su posición O(`V`), sustituir allí, actualizar la tabla y revincular todas las salidas antes de volver a exponer un mapa ya vinculado. No se añade un índice de posiciones para optimizar una operación infrecuente. Las consultas del turno y las rutas nunca usan el recorrido lineal.

**Rationale**: `obtener_sala` actual es O(`V`) y `vincular_salidas` puede llegar a O(`EV`). La tabla ofrece O(1) esperado y amortizado por inserción, con O(`V`) peor caso por colisiones. La lista conserva el contrato observable de recorrido que un hash no garantiza. Sustituir conserva la posición, pero cuesta O(`V+E`) esperado por la búsqueda lineal y el pase que vuelve a resolver cada `destino_sala`; así las referencias entrantes dejan de apuntar a la instancia antigua. El peor caso de esa revinculación es O(`V·E`) si el hash degenera.

**Alternatives considered**:

- **Mantener solo lista lineal**: rechazado por Constitución II y por multiplicar el costo de cada búsqueda.
- **Reemplazar la lista por hash**: rechazado; perdería orden estable y contrato de referencias/recorrido.
- **Usar `dict`**: prohibido como índice.

## R-05 — Reutilización e invalidación

**Decision**: recalcular cada decisión en la primera versión. Las instantáneas compartidas experimentales se tratan como derivadas y se identifican por versión del esqueleto, generación de puertas y sala objetivo. Después de retroceso o reconstrucción se descartan todas (`FR-014`, `FR-016`).

**Rationale**: calcular desde cero es la referencia normativa y minimiza el riesgo inicial. Una generación permite invalidar en O(1), pero su memoria pendiente de reclamar debe contarse. No se intenta deshacer una caché porque no es estado de juego.

**Alternatives considered**:

- **Invertir cada mutación de la caché en el historial**: rechazado; mezcla estado derivado con canónico y aumenta `C` sin valor observable.
- **No invalidar después de retroceso si las versiones coinciden**: rechazado; una versión monotónica puede no representar el estado restaurado y conservar referencias obsoletas.
- **Invalidación selectiva por puerta**: candidata futura; necesita índice puerta→resultados y medición de ahorro. No se justifica antes de comparar con recálculo.

## R-06 — Matriz de dependencias

**Decision**:

- puertas abiertas/cerradas y costos determinan distancias;
- sala del jugador determina el objetivo compartido;
- sala/rango del cazador determinan su consulta;
- velocidad determina tiempos de agenda, no distancias;
- movimiento/muerte de otros actores no bloquean rutas, pero cambian el lote de actores activos;
- contenido descargado y niebla no afectan al cazador (`FR-013`, `FR-014`).

**Rationale**: separa invalidación de rutas de reprogramación temporal y evita invalidar todo ante cambios irrelevantes, sin asumir que todas las mutaciones tienen el mismo efecto.

**Alternatives considered**: una generación global para cualquier cambio es correcta pero puede eliminar toda reutilización. Se conservará como fallback seguro para retroceso; durante ejecución normal se usarán dependencias específicas solo si la reutilización es habilitada por medición.

## R-07 — Integración del costo de movimiento

**Decision**: mantener `calcular_intervalo(costo, velocidad)` y hacer que cada ejecución de `MOVER` entregue el costo de la salida realmente atravesada. Las demás acciones conservan `costo_base`; el cazador espera/ataca con las reglas heredadas (`FR-003`–`FR-005`, `FR-012`).

**Rationale**: existe una única fórmula para todos los actores y no se duplican reglas de velocidad. El resultado de acción ya es el punto que el motor usa para programar el siguiente turno.

**Alternatives considered**:

- **Cambiar la constante global `COSTO_MOVER`**: no representa salidas distintas.
- **Aplicar el costo solo al jugador o solo al cazador**: contradice FR-003/FR-005.
- **Modificar `costo_base` para recibir una puerta en todas las acciones**: ensancha innecesariamente un contrato compartido.

## R-08 — Estado reversible y línea de tiempo

**Decision**: registrar solo mutaciones canónicas con los cambios pequeños existentes; costos y rangos son datos inmutables de la versión cargada. Las decisiones/rutas se recalculan después de restaurar. Proponer a Joshua un aviso explícito de reconstrucción/retroceso para limpiar derivados.

**Rationale**: el historial actual ya agrupa una acción y sus eventos, registra agenda, atributos, listas y azar, y revierte en orden inverso. Añadir snapshots por decisión violaría Constitución VII. La excepción de pergaminos permanece en el servicio de inventario y no se replica en rutas.

**Alternatives considered**:

- **Guardar mapa/estado completo por turno**: prohibido.
- **Persistir cachés de ruta en checkpoints**: innecesario; no son observables y pueden reconstruirse.
- **Confiar en que una caché vieja “probablemente” sirve**: contradice FR-014.

## R-09 — Oráculos de corrección

**Decision**: para grafos pequeños, enumerar rutas simples de forma exhaustiva y escoger por `(costo, primera_vecina)`; para matrices de benchmark mayores, usar una relajación completa independiente sobre listas. Antes de medir, comparar únicamente la decisión observable: acción, alcanzabilidad/dentro de rango, costo total, primera vecina y costo del paso (`PR-004`, `PR-006`). El trabajo, orden de descubrimiento, cantidad de entradas y frontera pueden diferir; se instrumentan y comparan aparte, sin exigir igualdad con el oráculo.

**Rationale**: un oráculo con estructura y recorrido distintos detecta errores de frontera, parada anticipada y desempate que una segunda invocación del mismo algoritmo ocultaría.

**Alternatives considered**:

- **Comparar la implementación consigo misma**: no es independiente.
- **`networkx` como único oráculo**: permitido solo en benchmark, pero no verifica por sí solo el desempate específico y añade una dependencia innecesaria.
- **Logs dorados únicamente**: útiles para Apéndice B, pero no cubren combinaciones generadas.

## R-10 — Diseño de `--bench`

**Decision**: añadir un proveedor a `main.py --bench`, reutilizar el benchmark real de ciclo y medir rutas, invalidación y las seis operaciones de agenda con alternativas. El fixture común se prepara fuera; todo trabajo requerido por la operación/ciclo permanece dentro.

**Rationale**: la constitución exige una vía ejecutable y comparaciones; los scripts aislados no bastan. El benchmark existente ya separa carga de fuente y renderizado, pero debe incorporar cazadores y conectarse a la salida estándar.

**Alternatives considered**:

- **Microbenchmarks aislados solamente**: no demuestran el ciclo de 20 ms.
- **Cronometrar carga HTTP**: mezcla latencia externa con simulación y contradice el alcance del límite.
- **Sacar creación de auxiliares de ruta del cronómetro**: oculta el costo que paga cada decisión.

## R-11 — Contratos entre integrantes

**Decision**: documentar dos propuestas pendientes, no modificar archivos ajenos y bloquear tareas de integración hasta el acuerdo.

**Rationale**: `dto/sala.py`, `datos/decodificador_datos.py`, persistencia, mapa conocido y línea de tiempo son compartidos. La Constitución VIII exige identificar consumidores y acordar cambios antes de implementarlos.

**Alternatives considered**: modificar directamente los archivos compartidos o asumir una firma. Ambas se rechazan porque crearían contratos de hecho sin revisión.
