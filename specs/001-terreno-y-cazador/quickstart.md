# Quickstart de validación: Terreno y cazador

Esta guía describe cómo validar la futura implementación. En esta fase no se crean pruebas ni código.

## Prerrequisitos

- Rama Git real: `Sofia`.
- Soporte mínimo Python 3.11. Para reproducir la validación local previa, usar el entorno del proyecto `.venv` con Python 3.12.10 y `requirements.txt`; el Python general del sistema no sustituye ese entorno.
- Paquete offline de fixtures para pruebas sin red.
- G1/G2 cerradas: Steven aceptó `proximo_paso(...) -> ResultadoRuta`; `5000d1f` integra costo/rango estrictos, simetría de sentidos existentes y v10 para esos campos. Las salidas sin inversa son válidas.
- Estado local base: `Sofia@5000d1fe8af268987206827e4c524c05bd599357`. Mapa conocido, clase completa `LineaTiempo` y persistencia conjunta restante continúan pendientes.

## Comandos previstos

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_restricciones_enunciado.py
.\.venv\Scripts\python.exe -m pytest tests/test_logica -k "terreno or cazador or velocidad or retroceso"
.\.venv\Scripts\python.exe main.py --bench
```

Las pruebas del servicio en línea se ejecutan y reportan aparte; aceptación funcional y benchmarks no dependen de red ni de Pygame.

### Línea base posterior al merge

Para `Sofia@5000d1f`, Sofía comunicó una corrida de `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` con `1204 passed, 4 subtests passed`. Esta revisión documental no ejecutó esa suite y no presenta el conteo como propio. Costo/rango están integrados; cazador/rutas todavía requieren la validación propia de este bloque.

## Oráculos independientes

1. **Grafos pequeños**: enumeración exhaustiva de rutas simples usando listas. Selecciona el mínimo `(costo_total, primera_vecina_id)` y sirve de referencia para acción, alcanzabilidad/rango, costo total, primera vecina y costo del paso.
2. **Grafos sintéticos mayores**: relajación completa independiente, sin parada por rango ni reutilizar el buscador de producción. Calcula desde cero la misma decisión observable antes de cada comparación.
3. **Reversión**: serialización/comparación de campos canónicos antes y después; excluye expresamente la cantidad de pergaminos según FR-016.
4. **Determinismo**: dos estados construidos con distinta ordenación incidental de salidas pero mismos datos producen la misma secuencia observable.

Una diferencia en esos resultados observables falla antes de medir tiempos. El orden interno, las salas descubiertas/fijadas, las entradas duplicadas y el tamaño de frontera pueden diferir; se miden aparte y no se comparan por igualdad con el oráculo.

## Matriz funcional completa

| Escenario | Prueba propuesta | Referencia/comprobación |
|---|---|---|
| AC-001 | salida sin costo en ambos sentidos | costo efectivo 100 y mismo intervalo; FR-001/FR-002 |
| AC-002 | varios costos y velocidades | fórmula exacta y reloj siguiente; FR-003 |
| AC-003 | atacar/esperar/usar/equipar/recoger/soltar/abrir | costos heredados sin cambio; FR-004/FR-005 |
| AC-B06 | costo 1 con velocidad alta | intervalo 1; FR-003 |
| AC-B07 | velocidad cambia durante salida costosa | tiempo proporcional y secuencia estrictamente nueva; FR-006 |
| AC-019 | parametrizar `True`, `False`, texto, fracción, 0 y negativo | rechazo descriptivo, sin conversión; FR-001 |
| AC-020 | dos sentidos con costos distintos | rechazo identifica salida y ambos valores; FR-002 |
| AC-004 | cazador comparte sala | ataca antes de ruta/rango; FR-007 |
| AC-B01 | puertas separan al objetivo | espera costo 100; FR-008 |
| AC-B02 | ruta mínima cuesta rango+1 | espera costo 100; FR-008/FR-009 |
| AC-005 | ruta mínima cuesta exactamente rango | mueve un paso; FR-009/FR-010 |
| AC-B03 | ruta de más aristas pero menor costo | oráculo exhaustivo elige menor costo; FR-009/FR-010 |
| AC-B04 | primeras vecinas empatadas e inputs permutados | siempre menor ID numérico; FR-011 |
| AC-006 | ruta mínima de varios pasos | mueve solo el primero y cobra esa salida; FR-010/FR-012 |
| AC-007 | mismo esqueleto con contenidos remotos distintos | decisión idéntica; FR-013 |
| AC-021 | rango ausente, negativo, booleano, texto y fracción | rechazo identifica ficha; FR-009 |
| AC-022 | rango 0 en otra sala con salida costo 1/100 | espera costo 100; FR-008/FR-009 |
| AC-023 | rango 0 en la misma sala | ataca; FR-007/FR-009 |
| AC-B05 | cerrar puerta de ruta entre turnos | siguiente decisión igual a cero; FR-014 |
| AC-008 | mover jugador entre turnos | objetivo actual y resultado igual a cero; FR-014 |
| AC-009 | reutilización experimental frente a cero | acción, vecina y costo idénticos; FR-013/FR-014 |
| AC-010 | dos ejecuciones, misma semilla/acciones | log, tiempos y empates idénticos; FR-011/FR-015 |
| AC-011 | intervalo con cazadores y pergamino | estado reversible restaurado, excepción de pergaminos y recálculo; FR-016 |
| AC-016 | abrir puerta entre turnos | resultado igual a cero con puerta abierta; FR-014 |
| AC-017 | cambiar velocidad entre turnos | agenda cambia conforme FR-006; ruta solo si datos relevantes cambian; FR-014 |
| AC-018 | mover/matar otro actor | comparar desde cero sin asumir invalidación idéntica; FR-014 |

### Verificaciones cruzadas futuras con Steven/003

Estos criterios están planificados; no se han implementado ni ejecutado en esta actualización:

1. **Default estricto**: omitir `costo` produce 100; presentar `True`, `False`, texto, fracción, cero o negativo rechaza el dato sin sustituirlo.
2. **Simetría después del enlace**: identificar sentidos por origen/destino, rechazar costos distintos y detectar múltiples salidas ambiguas. Una salida sin inversa se acepta y no crea otro sentido.
3. **Resolubilidad independiente del peso**: variar costos válidos sin cambiar puertas/llaves conserva el resultado de alcanzabilidad de 002.
4. **Mapa conocido independiente**: dos estados reales distintos con las mismas salas exploradas y puertas recordadas abiertas producen el mismo siguiente paso.
5. **Conocimiento vigente**: después de cada paso de «ir a», cambiar origen o conocimiento obliga a decidir otra vez y nunca continúa una secuencia precalculada.
6. **Casos terminales aceptados**: origen=destino produce costo 0 sin paso; sin ruta produce un estado explícito distinto. La prueba de integración queda bloqueada por la representación/firma y la entrega de 003, no por la semántica.
7. **Separación de comportamiento**: el buscador no devuelve `ATACAR` ni `ESPERAR`; esas acciones se deciden fuera con el resultado geométrico.

## Matriz de rendimiento

| Escenario | Medición `--bench` | Criterio |
|---|---|---|
| AC-012 | mapa base y mapas ampliados solo fuera del rango | fijadas `F_R`, descubiertas `D_R`, salidas `E_R`, inserciones `P_R` y frontera `Q_R` no crecen proporcionalmente a `V`/`E`; PR-002 |
| AC-013 | ciclo real de referencia con decenas de cazadores | cada muestra válida `<20 ms`, sin red/render; PR-001 |
| AC-014 | matriz individual/compartida, uno/muchos, pequeño/grande, reutilizar/cero, puertas estables/inestables | equivalencia primero; reporte de tiempo, trabajo y memoria; PR-003/PR-004/PR-006 |
| AC-015 | seis operaciones de agenda con cientos de eventos | comparación por operación y ciclo mixto; PR-005 |
| Integración 003 (pendiente) | una decisión de «ir a» desde cero y alternativas reutilizadas | equivalencia primero; costo completo frente a 5 ms, sin afirmar cumplimiento antes de medir |
| Índice de `MapaCripta` — construcción | mismos IDs/instancias en varios tamaños | generación fuera; construcción de lista+índice y memoria separadas |
| Índice de `MapaCripta` — búsqueda | aciertos inicio/medio/final y ausencias | índice propio frente a recorrido lineal benchmark-local; identidad primero |
| Índice de `MapaCripta` — vinculación | mismos grafos y densidades antes/después | tiempo de enlace separado; orden, destinos y alias canónicos iguales antes de medir |

## Casos del Apéndice B

La ejecución de aceptación debe mostrar explícitamente estos siete IDs en el reporte:

```text
AC-B01 AC-B02 AC-B03 AC-B04 AC-B05 AC-B06 AC-B07
```

Cada prueba incluye en su nombre o docstring el AC y los FR asociados. No se acepta cubrirlos solo de forma incidental.

## Diseño de `--bench`

### Conexión actual comprobada

`main.py --bench` concatena los proveedores existentes y ya registra `PROVEEDORES_MAPA` de 001. Esa es la parte entregada de T049. Los proveedores de rutas y ciclo de 001 aún requieren integración conjunta, sin reemplazar ni registrar dos veces los existentes.

El ciclo común actual ejecuta `prueba_rendimiento_sofia.py`; `benchmarks/benchmark_ciclo_real_integrante1.py` todavía necesita un adaptador para aparecer en el informe estándar. La agenda común actual reporta extracción; las otras cinco operaciones exigidas por `PR-005` siguen siendo parte del proveedor de 001.

### Rutas

- semillas fijas publicadas en la salida;
- `H=1` y una carga de decenas;
- rangos pequeños/grandes;
- individual frente a inversa compartida;
- recálculo frente a reutilización;
- puertas casi estables y cambios frecuentes;
- conteos separados de salas fijadas y descubiertas, salidas examinadas, entradas insertadas, frontera máxima/final, extracciones obsoletas, limpieza y memoria auxiliar.
- para «ir a», una consulta por paso con origen/destino/conocimiento vigentes; comparación desde cero antes de cualquier reutilización;
- medición conjunta con 003 frente a 5 ms, incluyendo construcción de auxiliares y, si aplica, invalidación y limpieza.

### Ciclo real

Se adapta `benchmarks/benchmark_ciclo_real_integrante1.py`. La carga e inicialización común se hacen antes; el cronómetro incluye acción, agenda, decisiones de cazadores y auxiliares de ruta hasta la próxima decisión. Invalidación/limpieza se incluye solo para variantes experimentales con estado retenido. Sintéticos y referencia oficial se etiquetan por separado.

### Agenda

Para `N` de cientos y al menos un tamaño superior:

1. insertar;
2. extraer;
3. cancelar por ID;
4. cancelar por actor;
5. reprogramar;
6. resolver empates por tiempo/secuencia.

Cada flujo usa los mismos eventos para `AgendaEventos` y una alternativa lineal/manual permitida solo en benchmark. Para inserción se incluye construir la agenda vacía; para las demás operaciones la carga común queda fuera, pero las búsquedas, cambios de índices y limpieza propios de la operación quedan dentro. Un ciclo mixto mide la carga de punta a punta.

### Mapa e índice por ID

`benchmarks/mapa_cripta_integrante1.py` usa generadores deterministas para varios tamaños y densidades. El proveedor informa tres grupos sin mezclar intervalos:

1. construir `_salas` y `TablaHashImpl`, dejando fuera únicamente la generación del fixture;
2. consultar secuencias equivalentes de IDs presentes/ausentes frente a un recorrido lineal local al benchmark;
3. vincular los mismos grafos mediante resolución lineal y mediante el índice propio, sin incluir la construcción o las consultas independientes.

Antes de comparar tiempos se exige igualdad de IDs y ausencias, mismo orden de salas/puertas y que cada `destino_sala` sea exactamente la instancia canónica correspondiente. `main.py --bench` ya conecta el proveedor de mapa; los sentidos únicos aceptados no forman parte de estos fixtures estructurales.

## Reversión y determinismo

1. Capturar el estado canónico anterior a una acción.
2. Ejecutar movimiento con costo, turnos de cazadores, apertura/cierre y cambio de velocidad.
3. Usar pergamino.
4. Comparar sala/vida/reloj/agenda/secuencias/puertas/actores con el estado anterior, excepto pergaminos.
5. Desde el mismo estado posterior al retroceso, repetir las mismas acciones posteriores en dos ejecuciones.
6. Comparar decisiones, tiempos, secuencias y `partida.log`.

### Integración con la línea de tiempo 004

Además de la reversión funcional:

1. Verificar que cada mutación canónica de 001 se registra dentro de la transacción mediante los cambios y helpers existentes; una acción rechazada no publica cambios.
2. Comprobar que ninguna caché/servicio de rutas es alcanzable desde `EstadoPartida`, entidades canónicas o cambios guardados.
3. Copiar en una sola operación `(estado, ventana_de_transacciones)` con `copy.deepcopy`; cada cambio de la copia debe apuntar a las entidades copiadas. Deshacer temporalmente y aplicar los inversos debe dejar bytes/estructura equivalentes aun si el resumen falla.
4. Cuando exista el formato conjunto acordado por Steven y Joshua, hacer ida y vuelta del `pickle` de estado vivo y línea y repetir consultas; las cachés no aparecen en los bytes.
5. Con la producción inicial de recálculo, comprobar que no se conserva caché/instantánea entre decisiones y que `historia`, `RETROCEDER` e `iniciar` no requieren ganchos de invalidación.
6. Si una decisión posterior adopta reutilización, ejecutar entonces las pruebas planificadas de `historia`, retroceso e inicio/carga sobre la caché externa; no anticiparlas como requisito de la vía sin estado retenido.

El checkout local ofrece `deshacer_ultimo`/`revertir`, `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, `fotografiar_para_rehacer(inverso, estado)` y `HistorialReversible.vincular_linea`. T005 conserva la revisión cruzada de estas interfaces como requisito de proceso. Esto no equivale a tener local la clase completa `LineaTiempo` de `origin/joshua@b039b8b…`, ni permite ejecutar todavía las pruebas conjuntas sobre cambios nuevos de 001 que no se han implementado.

### Estado de persistencia

La versión ejecutable es v10 y persiste costo/rango. Las pruebas de ida y vuelta de mapa conocido más línea de tiempo permanecen bloqueadas hasta la entrega conjunta completa; este bloque no modifica ese guardado.

## Señales de salida

- Suite heredada y nueva sin regresiones.
- Prueba AST de restricciones aprobada.
- 30 escenarios con referencia a FR/PR; siete AC-B explícitos.
- Ninguna divergencia observable respecto del oráculo; trabajo y orden interno reportados por separado.
- Informe `--bench` conectado a `main.py --bench`, con resultados sintéticos separados de la referencia oficial.
- La decisión final individual/compartida/adaptativa se documenta después de medir; este plan no anticipa el ganador.
