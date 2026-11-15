# Quickstart de validación: Terreno y cazador

Esta guía describe cómo validar la implementación y sus integraciones todavía pendientes.

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

### Ejecución de US1 y US2 sobre la base integrada

- Puerta T064: **133 passed, 2 subtests passed in 4.71s**.
- Foco US2 ampliado: **30 passed in 0.15s**.
- Regresiones relacionadas: **505 passed, 4 subtests passed in 7.20s**.
- Restricciones del enunciado: **56 passed in 0.59s**.
- Contrato offline completo: **41 passed**.
- Suite completa con `.venv/Scripts/python.exe -m pytest -q -rs --tb=short`: **1251 passed, 4 subtests passed in 104.16s**.

Estas cifras sí corresponden a la ejecución del bloque. No incluyen benchmarks ni demuestran el límite oficial de 20 ms.

### Ejecución del núcleo US3 con recálculo desde cero

- Foco T031 (los cinco archivos requeridos): **13 passed in 1.48s**.
- Foco con copia/serialización canónica: **15 passed in 0.67s**.
- Regresiones relacionadas de lógica, integración, costo/rango y copia: **493 passed, 4 subtests passed in 3.52s**.
- Restricciones del enunciado: **56 passed in 0.51s**.
- Contrato offline completo: **41 passed in 5.06s**.
- `py_compile` de los siete archivos de prueba modificados y `git diff --check`: correctos.

El oráculo de US3 enumera rutas simples sin invocar `proximo_paso`. Las pruebas comprueban recálculo tras puertas, jugador, velocidad, otros actores, retroceso, reinicio y enlace de un estado deserializado; empate numérico y orden incidental permutado; bytes de `partida.log`; restauración de salas, actores, vida, reloj, agenda, secuencias, puertas y azar; excepciones de pergamino/`registrar_solo_linea`; y alias de copias conjuntas por `deepcopy` y `pickle`. La instrumentación por referencias débiles confirma que cada consulta libera su montículo y sus dos tablas. No se encontró un defecto de producción y no se añadieron cachés, generaciones ni observadores.

No se ejecutó la suite completa en ese bloque porque solo cambió pruebas y documentación; la corrida completa posterior se registra en «Validación completa del bloque documental (T060)». Tampoco se ejecutaron benchmarks en ese bloque. `LineaTiempo` completa y el formato conjunto con mapa conocido siguen ausentes; por ello T041/T055/T056 permanecen abiertas. T040 quedó redactado y validado contra `origin/joshua`, pero su ejecución local se omite hasta G4b/T056.

### Ejecución aislada de rutas US4 (T044–T046/T065)

Comando reproducible equivalente al ejecutado:

```powershell
@'
import json
from pathlib import Path
from benchmarks.terreno_cazador_integrante1 import (
    CALENTAMIENTO, SEMILLA, _entorno, medir_rutas_region, medir_rutas_matriz,
)
filas = medir_rutas_region(9, (32, 128, 512)) + medir_rutas_matriz(9, (32, 64))
Path("benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json").write_text(
    json.dumps({
        "entorno_ejecutor": _entorno(), "semilla": SEMILLA,
        "calentamiento": CALENTAMIENTO, "repeticiones": 9,
        "cargas_region": [32, 128, 512], "cargas_matriz": [32, 64],
        "alcance": "sintetico_no_demuestra_pr_001_ni_20_ms_oficial",
        "integracion_main_bench": "pendiente_t049_acuerdo_propietario_main",
        "mediciones": filas,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
'@ | .\.venv\Scripts\python.exe -
```

El archivo conservado contiene **30 filas y 270 muestras** con semilla 2609, un calentamiento y nueve repeticiones. AC-012 usa 32/128/512 salas y una región alcanzable fija de cinco; los contadores productivos permanecieron `F=5`, `D=5`, `E=6`, `P=5`, `Q=2`. AC-014 usa 64 salas, 1/20 cazadores, rangos pequeño/grande, puertas estables/inestables y tres ciclos. Cada fila separa costo inicial, reconstrucciones, consultas recalculadas/iniciales/reutilizadas, invalidación, mantenimiento, limpieza y total; la memoria se mide aparte.

Como referencia descriptiva, no decisoria, para 20 cazadores y rango grande las medianas de lote estable fueron 26 813 300 ns (individual), 587 200 ns (compartida recalculada) y 301 700 ns (reutilizada); con cambios frecuentes fueron 18 713 300, 662 300 y 586 800 ns. En AC-012 el recálculo individual mantuvo medianas de 42 900/48 600/139 900 ns (32/128/512 salas; trabajo `F=5, D=5, E=6, P=5, Q=2` constante), mientras la construcción inversa compartida creció 38 500/107 800/417 300 ns al barrer el grafo total. Son cargas sintéticas: no cierran PR-001, no prueban 20 ms oficiales y no autorizan una estrategia productiva.

Validación: **55 pruebas de benchmark/conexión**, **21 pruebas de rutas relacionadas** y **56 restricciones** aprobadas. `PROVEEDORES_RUTAS` conecta correctamente por `benchmarks.integrante3.ejecutar`; no se modificó `main.py` porque rutas/ciclo siguen reservados a la integración conjunta T049.

### Agenda equivalente y ciclo completo T047/T048

La validación inicial ejecutó los productores directamente; T049/T050 los conectaron y ejecutaron
después mediante `main.py --bench`. El comando focalizado original fue:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_bench_ciclo_real.py `
  tests/test_bench_agenda_t047.py `
  tests/test_bench_terreno_cazador.py

.\.venv\Scripts\python.exe benchmarks/benchmark_ciclo_real_integrante1.py `
  --datos-offline tests/fixtures/api_real `
  --muestras 3 --calentamiento 1 `
  --resultados benchmarks/resultados/ciclo_real_criptas_disponibles.json
```

La ejecución focalizada terminó en **52 passed in 4.45s**, incluida una carga real con catálogo vivo reconectado fuera del intervalo; los seis módulos de benchmark terminaron en **70 passed in 7.58s**. Los artefactos conservados son:

- `agenda_ciclo001_t047_c1_r9_256-512-1024.json`: **36 filas/324 muestras**, seis operaciones, 256/512/1024 eventos, mezcla de eventos del ciclo, 28 destinatarios cazador y demoras variables. En 1024 eventos, resolver empates obtuvo medianas de **15.341 ms** (`AgendaEventos`) y **39.694 ms** (lista lineal). Se conservaron las 24 muestras lineales `>=20 ms`: insertar 256 eventos (6/9), reprogramar 256 (9/9) y resolver 1024 empates (9/9).
- `ciclo_sintetico_t048_t047_c1_r9_32-64.json`: **32 filas/288 muestras**, 32/64 salas, 1/28 cazadores, rango pequeño/grande y puertas estables/inestables. Todas las muestras fueron ciclos completos; no hubo rechazos, muertes, victorias, terminales, incompletos ni errores.
- `ciclo_real_criptas_disponibles.json`: cuatro criptas locales reales, **12/12 ciclos completos**, medianas de **0.102 a 0.225 ms** y cero muestras de 20 ms o más. El archivo dice explícitamente `referencia_oficial=pendiente_publicacion_g6` y `afirma_pr001=false`.

La mayor carga sintética fue 64 salas, 28 cazadores, rango grande y puertas estables con recálculo productivo: mediana **20.545 ms**, p95 **36.826 ms** y **7/9** muestras de al menos 20 ms; cada muestra reporta 28 decisiones/notificaciones de enemigo. La variante inestable equivalente conservó otras **2/9** muestras lentas (mediana 17.964 ms, p95 33.234 ms), 24 decisiones/notificaciones y un cierre. En total se conservan las **9 muestras `>=20 ms`** sin reducir trabajo. La alternativa retenida estable dio 3.127 ms de mediana, pero es experimental, incluye creación/consultas/invalidación/limpieza dentro del intervalo y no autoriza un cambio de producción. PR-001/T051 continúan bloqueados hasta publicar la referencia oficial.

### Validación completa del bloque documental (T060)

Ejecutada el 2026-11-10 con `.venv/Scripts/python.exe` desde la raíz:

- **Suite completa final, con T040 añadido** (`pytest -q -rs --tb=short`): **1287 passed, 1 skipped, 4 subtests passed in 173.39s**. La omisión es el módulo `tests/test_integracion_001_004.py`, que espera G4b/T056.
- **Suite completa previa, sin T040**: **1287 passed, 4 subtests passed, 0 skipped, 0 failed in 188.09s**.
- **Foco funcional US1–US4 e integraciones no bloqueadas**: **159 passed, 2 subtests passed in 9.99s**.
- **Módulos de benchmark y restricciones del enunciado**: **126 passed in 30.26s**.

Una corrida intermedia falló solo en `tests/test_bench_integrante2.py::test_el_costo_crece_de_forma_aproximadamente_lineal` (factor 3.8 frente a 3.0). Esa prueba pasó 3/3 aislada y volvió a pasar en la corrida completa final; se registra como fluctuación de medición, no como regresión, y no se modificó. Las corridas usaron fixtures offline; no se ejecutaron pruebas contra el servicio en línea. Los conteos focalizados se solapan con la suite completa y no se suman. La conexión y ejecución posteriores de mapa, rutas, agenda y ciclo mediante `main.py --bench` quedaron cerradas en T049/T050/T062. Esta validación histórica no demuestra PR-001 ni el límite oficial de 20 ms.

### Validación de integraciones en `integracion-parte2@d86819d`

Ejecutada el 2026-11-13 sin repetir la suite completa:

- `tests/test_integracion_001_004.py` y `tests/test_integracion_ir_a_001_003.py`: **10 passed in 0.29s**, sin omisiones.
- `tests/test_logica/test_mapa_conocido.py`, `tests/test_logica/test_viaje.py` y `tests/test_logica/test_rutas_ponderadas.py`: **45 passed in 0.30s**.
- Evidencia aceptada de PowerShell posterior a la integración: **79 pruebas específicas aprobadas** y suite completa de **1402 pruebas, 4 subtests**, sin fallos ni omisiones.

T004/T052/T053 verifican la frontera de mapa conocido y recálculo por paso; T056 ejecuta ya contra `LineaTiempo` integrada, incluidos punto K=2, restauración del estado vivo, inversos en `finally` y prohibición de llamar al cazador. Persistencia T006/T055 y benchmarks T049/T050 permanecen fuera de este cierre.

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

### Verificaciones cruzadas con Steven/003

Los criterios 1–3 se cerraron en los bloques de datos anteriores. Los criterios 4–7 quedaron ejecutados en T004/T052/T053 sobre `integracion-parte2@d86819d`:

1. **Default estricto**: omitir `costo` produce 100; presentar `True`, `False`, texto, fracción, cero o negativo rechaza el dato sin sustituirlo.
2. **Simetría después del enlace**: identificar sentidos por origen/destino, rechazar costos distintos y detectar múltiples salidas ambiguas. Una salida sin inversa se acepta y no crea otro sentido.
3. **Resolubilidad independiente del peso**: variar costos válidos sin cambiar puertas/llaves conserva el resultado de alcanzabilidad de 002.
4. **Mapa conocido independiente**: dos estados reales distintos con las mismas salas exploradas y puertas recordadas abiertas producen el mismo siguiente paso.
5. **Conocimiento vigente**: después de cada paso de «ir a», cambiar origen o conocimiento obliga a decidir otra vez y nunca continúa una secuencia precalculada.
6. **Casos terminales aceptados**: origen=destino produce costo 0 sin paso; sin ruta produce un estado explícito distinto.
7. **Separación de comportamiento**: el buscador no devuelve `ATACAR` ni `ESPERAR`; esas acciones se deciden fuera con el resultado geométrico.

## Matriz de rendimiento

| Escenario | Medición `--bench` | Criterio |
|---|---|---|
| AC-012 | mapa base y mapas ampliados solo fuera del rango | fijadas `F_R`, descubiertas `D_R`, salidas `E_R`, inserciones `P_R` y frontera `Q_R` no crecen proporcionalmente a `V`/`E`; PR-002 |
| AC-013 | ciclo real de referencia con decenas de cazadores | cada muestra válida `<20 ms`, sin red/render; PR-001 |
| AC-014 | matriz individual/compartida, uno/muchos, pequeño/grande, reutilizar/cero, puertas estables/inestables | equivalencia primero; reporte de tiempo, trabajo y memoria; PR-003/PR-004/PR-006 |
| AC-015 | seis operaciones de agenda con cientos de eventos | comparación por operación y ciclo mixto; PR-005 |
| Integración 003 (funcional y rendimiento cerrados en T054) | una decisión de «ir a» desde cero y alternativa reutilizada experimental | equivalencia primero; costo completo frente a 5 ms, separado por carga y estado de conocimiento |
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

`main.py --bench` concatena los 20 proveedores existentes —incluidos `PROVEEDORES_MAPA` de 001 y `bench_linea.PROVEEDORES` de Joshua— con los cinco adaptadores de agenda, rutas y ciclo publicados en las dos tuplas `PROVEEDORES_MAIN`. La prueba de conexión compara las 25 identidades en su orden real, exige unicidad y comprueba una aparición exacta de cada adaptador. T049 y T050 están cerradas con ejecución oficial reproducible.

El ciclo común histórico sigue disponible; `benchmarks/benchmark_ciclo_real_integrante1.py` conserva `PROVEEDORES = (medir_ciclos_sinteticos,)` y registra mediante `PROVEEDORES_MAIN = (medir_ciclos_sinteticos_main,)` las cargas 32/64. `benchmarks/terreno_cazador_integrante1.py` conserva `PROVEEDORES_AGENDA`, `PROVEEDORES_RUTAS` y `PROVEEDORES`, y registra cuatro adaptadores nominales mediante `PROVEEDORES_MAIN`. El argumento global `tamanos` de `integrante3.ejecutar` no describe esas cargas particulares: al interpretar la salida se usan `n`, `carga`, escenario y alternativa de cada fila. Pruebas focalizadas de registro: **10 passed in 0.64s**; no se ejecutó el benchmark completo.

### Evidencia oficial T050

La ejecución oficial usa `benchmarks.ejecutar_t050_integrante1`: stdout se
conserva como JSON completo, stderr, PID y código real del hijo quedan en
archivos separados y ninguna ruta existente se sobrescribe. El proceso hijo
terminó con código **0** y después se ejecutó:

```powershell
.\.venv\Scripts\python.exe -m benchmarks.extraer_resultados_terreno_cazador_integrante1 `
  --entrada benchmarks\resultados\main_bench_completo_t050.json `
  --salida benchmarks\resultados_terreno_cazador_integrante1.json
```

El extractor selecciona conjuntos exactos de nombres y alternativas de mapa,
agenda, rutas y ciclo; conserva cada fila completa, exige que muestras y
repeticiones coincidan y rechaza claves lógicas duplicadas. No reemplaza las
cargas particulares por `tamanos` del ejecutor. El JSON completo contiene 916
filas y el filtrado **194 filas/2910 muestras**: mapa 60/900, agenda 72/1080,
rutas 30/450 y ciclo 32/480; las 194 claves son únicas y el subconjunto coincide
exactamente con el original. stderr conserva cinco avisos por falta del paquete
offline de `cripta-01`. Las 32 filas de ciclo continúan etiquetadas como
sintéticas, referencia oficial pendiente y `afirma_pr001=false`.

### Cierre integral T062/T071

No se repite el benchmark completo. La validación usa los JSON oficiales existentes y ejecuta solo
los módulos focalizados:

```powershell
.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_bench_terreno_cazador.py `
  tests\test_bench_mapa_cripta.py

.\.venv\Scripts\python.exe -m pytest -q `
  tests\test_bloque3_conexiones.py::test_bench_desde_main_no_inicializa_fuente_ni_vista
```

Resultados: **33 passed in 2.66s** para los dos módulos de US4 y **1 passed in 0.23s** para la
composición exacta del punto de entrada. Esta última prueba intercepta el ejecutor antes de medir:
confirma 25 proveedores únicos y una sola inclusión de los adaptadores de mapa, agenda, rutas y
ciclo. La auditoría en memoria vuelve a extraer desde las 916 filas completas y obtiene exactamente
el JSON conservado de **194 filas/2910 muestras**, con 194 claves únicas, 15 repeticiones por fila y
la distribución mapa 60/900, agenda 72/1080, rutas 30/450 y ciclo 32/480.

Estado frente a los requisitos de rendimiento:

- **PR-002, satisfecho en la carga sintética**: AC-012 conserva en producción
  `(F,D,E,P,Q)=(5,5,6,5,2)` para 32, 128 y 512 salas mientras solo crece el exterior.
- **PR-003, cubierto**: AC-014 conserva 24 filas con 1/20 cazadores, rango pequeño/grande, puertas
  estables/inestables e individual/compartida/reutilizada.
- **PR-004 y PR-006, cubiertos**: semilla, calentamiento, carga, unidad, 15 muestras y preparación
  fuera del intervalo están presentes; agenda, rutas y ciclo declaran equivalencia observable, y
  mapa conserva las mismas huellas de orden/resultados/enlaces e identidad canónica.
- **PR-005, cubierto sin umbral temporal propio**: 36 filas de carga nueva cruzan seis operaciones,
  256/512/1024 eventos y agenda/lista lineal. Hay **43/540 muestras `>=20 ms`**, todas de la lista
  lineal benchmark-local; no son un incumplimiento de PR-005 porque ese requisito no fija 20 ms.
- **PR-001/AC-013, no concluyente y bloqueado por T051**: las 32 filas/480 muestras de ciclo son
  sintéticas y declaran `referencia_oficial=pendiente_publicacion_g6` y `afirma_pr001=false`. En la
  alternativa productiva hay **10/240 muestras `>=20 ms`**: 8/15 en 64 salas, 28 cazadores, rango
  grande y puertas estables (mediana 20.3797 ms; p95/máximo 33.2902 ms), y 2/15 con puertas
  inestables (mediana 17.2163 ms; p95/máximo 23.9919 ms). La retención experimental tiene 0/240,
  pero no autoriza un cambio productivo. Estas superaciones describen la carga sintética; sin la
  cripta oficial no permiten declarar cumplimiento ni incumplimiento oficial del límite de 20 ms.

Con esta evidencia, T062 y el alcance sintético de US4/T071 quedan cerrados. La publicación y
validación oficial de AC-013 permanece exclusivamente en T051.

### Medición de un paso de «ir a» (T054/T066)

La medición es propia de 001 y no sustituye `benchmarks.integrante2.medir_paso_ir_a`, que pertenece
a la entrega de Steven. Usa `Viaje`, `MapaConocido` y `VistaMapaConocido` reales; la creación del
viaje/vista, los auxiliares del buscador, la consulta y la limpieza quedan dentro del intervalo.
Solo la construcción del fixture queda fuera. Antes del reloj se comparan siguiente sala, alcance,
costo total, costo de la primera salida y motivo.

```powershell
@'
import json
from pathlib import Path
from benchmarks.terreno_cazador_integrante1 import (
    CALENTAMIENTO, CARGAS_IR_A, LIMITE_IR_A_NS, SEMILLA,
    _entorno, medir_paso_ir_a_001,
)
salida = Path(
    "benchmarks/resultados/paso_ir_a_t054_c1_r15_32-128-512-publicado50.json")
if salida.exists():
    raise SystemExit(f"No se sobrescribe: {salida}")
filas = medir_paso_ir_a_001(
    repeticiones=15, tamanos=CARGAS_IR_A, incluir_publicado=True)
salida.write_text(
    json.dumps({
        "entorno_ejecutor": _entorno(), "semilla": SEMILLA,
        "calentamiento": CALENTAMIENTO, "repeticiones": 15,
        "cargas_sinteticas": list(CARGAS_IR_A),
        "mapa_publicado": {"cripta_id": "cripta-04", "salas": 50,
                           "conocimiento": "completo"},
        "limite_ns": LIMITE_IR_A_NS,
        "alcance": "t054_ir_a_001_no_reemplaza_integrante2_ni_afirma_pr001",
        "mediciones": filas,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
'@ | .\.venv\Scripts\python.exe -
```

El artefacto conserva **26 filas/390 muestras**, semilla 2609, un calentamiento y 15 repeticiones.
Los sintéticos de 32/128/512 salas cubren desempate, puerta recordada cerrada, cambio de
conocimiento y ausencia de camino. La carga publicada usa el conocimiento completo de `cripta-04`
(50 salas) y el par alcanzable 46→41, con paso 45 y costo 4000.

Con el mapa publicado, el recálculo productivo obtuvo **0.4965/0.5136/0.5136 ms** de
mediana/p95/máximo y **15/15 muestras `<5 ms`**; la inversa fría experimental obtuvo
0.2510/0.3344/0.3344 ms y su consulta reutilizada 0.0036 ms de mediana. En 32/128 salas todas las
muestras productivas cumplieron. En 512 salas, desempate registró **9/15 muestras que cumplen y
6/15 que superan** el límite; puerta cerrada, **12/15 que cumplen y 3/15 que superan**. No se redujo
la carga ni se cambió el umbral. El total productivo fue **186/195** muestras bajo el límite, con
**9/195** superaciones, y la alternativa experimental **195/195** en su costo frío.
La consulta reutilizada es experimental y solo representa conocimiento sin cambios; no se creó
caché productiva.

Pruebas focalizadas de benchmark/adaptadores: **38 passed in 3.78s**. Integración funcional
001/003 y lógica asociada: **49 passed in 0.42s**. Restricciones del enunciado: **61 passed in
0.57s**. La prueba temporal de `tests/test_bench_integrante2.py` que mide exploración falló una vez
con factor 2.7× y pasó al repetirse aislada; cinco mediciones directas oscilaron entre 1.36× y
2.23×. Se registra como fluctuación de una prueba ajena, no como regresión de T054, y no se
modificó.

La decisión T066 conserva el recálculo y no introduce caché. El cumplimiento corresponde al mapa
conocido completo de la mayor cripta publicada local, no a PR-001; la referencia oficial de T051
sigue pendiente. Si esa referencia cambia la carga, la medición se repetirá como parte de T051;
una adopción de reutilización requeriría antes tareas y archivos acordados con 003.

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

`benchmarks/benchmark_ciclo_real_integrante1.py` mide ya una llamada real a `MotorJuego.ejecutar_accion()`: la copia/inicialización queda antes y el cronómetro incluye acción, agenda, decisiones de cazadores y creación, consultas, invalidación y limpieza de auxiliares hasta la próxima decisión. La retención solo existe en el benchmark mediante sustitución temporal restaurada en `finally`; producción conserva recálculo individual. Cargas sintéticas, criptas reales disponibles y referencia oficial pendiente se etiquetan por separado.

### Agenda

Para `N` de cientos y al menos un tamaño superior:

1. insertar;
2. extraer;
3. cancelar por ID;
4. cancelar por actor;
5. reprogramar;
6. resolver empates por tiempo/secuencia.

Cada flujo usa los mismos eventos para `AgendaEventos` y una alternativa lineal/manual permitida solo en benchmark. Para inserción se incluye construir la agenda vacía; para las demás operaciones la carga común queda fuera, pero las búsquedas, cambios de índices y limpieza propios de la operación quedan dentro. `medir_agenda_ciclo` repite las seis operaciones con la mezcla `EFECTO/CERRAR_PUERTA/ENEMIGO/JUGADOR_DISPONIBLE/VENCER_EFECTO`, costos variables y cazadores activos.

### Mapa e índice por ID

`benchmarks/mapa_cripta_integrante1.py` usa generadores deterministas para varios tamaños y densidades. El proveedor informa tres grupos sin mezclar intervalos:

1. construir `_salas` y `TablaHashImpl`, dejando fuera únicamente la generación del fixture;
2. consultar secuencias equivalentes de IDs presentes/ausentes frente a un recorrido lineal local al benchmark;
3. vincular los mismos grafos mediante resolución lineal y mediante el índice propio, sin incluir la construcción o las consultas independientes.

Antes de comparar tiempos se exige igualdad de IDs y ausencias, mismo orden de salas/puertas y que cada `destino_sala` sea exactamente la instancia canónica correspondiente. `main.py --bench` ya conecta el proveedor de mapa; los sentidos únicos aceptados no forman parte de estos fixtures estructurales.

El cierre T072 se reproduce sin volver a ejecutar el benchmark completo:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests\test_bench_mapa_cripta.py
```

La prueba de integración llama al `main.main()` real en modo `--bench`, sustituye solo el ejecutor
antes de que mida y comprueba 25 proveedores únicos y una única inclusión de MapaCripta. La prueba
de evidencia lee `benchmarks/resultados/main_bench_completo_t050.json` y valida **60 filas/900
muestras** de mapa: seis tamaños (8–512), densidades 1/4, 15 repeticiones, alternativas exactas,
huellas/cargas equivalentes, destinos canónicos y ausencia de duplicados. Resultado focalizado:
**6 passed**. Las tablas oficiales de mediana/p95/máximo y su comparación separada con las corridas
anteriores de 9 y 30 repeticiones están en
[`DECISIONES.md`](../../DECISIONES.md#índice-por-id-de-mapacripta-evidencia-complementaria-de-001).
Estas mediciones aisladas no afirman PR-001 ni el presupuesto del ciclo completo de 20 ms.

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

El checkout integrado ofrece `LineaTiempo`, puntos de control, `deshacer_mientras`, `rehacer`, el gancho `rehacer(estado)`/`fotografiar_para_rehacer(inverso, estado)` y `HistorialReversible.vincular_linea`. T056 ejecutó la integración local: el módulo propio cubre el protocolo y las 79 pruebas específicas aceptadas cubren además puntos de control y partidas reales. La persistencia conjunta conserva tareas separadas y no se considera cerrada por esta integración.

### Estado de persistencia

La versión ejecutable es v10 y persiste costo/rango. Las pruebas de ida y vuelta de mapa conocido más línea de tiempo permanecen bloqueadas hasta la entrega conjunta completa; este bloque no modifica ese guardado.

## Señales de salida

- Suite heredada y nueva sin regresiones.
- Prueba AST de restricciones aprobada.
- 30 escenarios con referencia a FR/PR; siete AC-B explícitos.
- Ninguna divergencia observable respecto del oráculo; trabajo y orden interno reportados por separado.
- Informe `--bench` conectado a `main.py --bench`, con resultados sintéticos separados de la referencia oficial.
- La decisión final individual/compartida/adaptativa se documenta después de medir; este plan no anticipa el ganador.
