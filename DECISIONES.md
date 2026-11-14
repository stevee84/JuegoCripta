# Documento de Decisiones de Diseño — Parte II

Continúa el documento de la primera parte (`docs/decisiones_diseno.pdf`), con el mismo formato de
seis apartados: problema, alternativas consideradas, decisión, análisis de complejidad, evidencia
empírica y límites conocidos. Cada sección añade, como pide P2 §7.1, el enlace a la especificación
y al plan de spec-kit de los que proviene, y si la decisión final coincide con la del `plan.md`.

**Entorno de las mediciones.** Las de esta parte se tomaron en el equipo local con
`.venv/Scripts/python.exe`, mediana de repeticiones, con la preparación fuera del intervalo
cronometrado y las criptas sintéticas generadas de forma determinista por semilla (§6.3). Las
mediciones de §5.4 y de la subsección del índice salen de `--bench`. Las de §5.1, §5.2 y la
subsección de agenda de §5.6 provienen de los proveedores de 001 ejecutados mediante
`benchmarks.integrante3.ejecutar`; su
registro en `main.py --bench` sigue pendiente de T049/T050, así que se presentan como evidencia
sintética provisional y no como cierre del Principio IX.

---

## 5.1 Estrategia de rutas del cazador

**Especificación**: [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md) ·
**Plan**: [specs/001-terreno-y-cazador/plan.md](specs/001-terreno-y-cazador/plan.md) ·
**Diseño medido**: [research.md](specs/001-terreno-y-cazador/research.md) (R-01, R-05, R-13)

**¿Coincide con el plan original?** Sí en la decisión: el plan ya fijaba el recálculo individual
como producción provisional y prohibía adoptar reutilización sin medición. La diferencia es que
ahora existe la medición y se documenta la decisión; no se cambió el plan.

### 1. Problema

Cada cazador debe decidir en su turno entre atacar, esperar o moverse un único paso por una ruta
abierta de costo mínimo dentro de su rango. Con decenas de cazadores activos, repetir esa búsqueda
en cada decisión puede dominar el ciclo de eventos entre dos decisiones del jugador. La elección
no es solo de velocidad: cualquier estrategia debe conservar la decisión observable, el
determinismo y la independencia del contenido descargado (`FR-007`–`FR-014`, `PR-002`–`PR-004`).

Las alternativas de diseño son la búsqueda individual, la construcción de una inversa compartida
desde el jugador y la reutilización de esa inversa entre ciclos con invalidación. Una estrategia
adaptativa podría cambiar entre ellas, pero necesita un umbral medido. La referencia oficial de
`PR-001` sigue sin publicarse; las cifras de esta sección son sintéticas.

### 2. Alternativas consideradas

**Búsqueda individual por cazador, limitada por rango.** Es la producción inicial. Crea de forma
perezosa un `MonticuloMinimo` y tablas propias por consulta, etiqueta por
`(distancia, primera_vecina_id, sala_id)`, no inserta candidatos fuera del rango y libera los
auxiliares al terminar. No conserva estado entre decisiones.

**Inversa compartida construida una vez por ciclo.** Recorre el grafo desde el jugador y cada
cazador elige el mínimo `(costo(u,v)+dist(v), v.id)` entre sus salidas. Puede amortizar trabajo con
muchos cazadores, pero un solo rango grande amplía la región para todos. Vive solo en
`benchmarks/terreno_cazador_integrante1.py`.

**Inversa reutilizada entre ciclos con invalidación explícita.** Evita reconstruir mientras las
puertas y el objetivo no cambien, a cambio de mantener estado derivado, detectar invalidaciones y
reconstruir cuando corresponda. También vive solo en el benchmark y mide construcción, consultas,
invalidación, reconstrucción y limpieza dentro del intervalo.

**Estrategia adaptativa.** Elegiría individual o compartida según cantidad de cazadores, rango y
estabilidad de puertas. No se implementó porque no existe un umbral medido que justifique el
cambio ni una carga oficial que lo valide.

**Devolver la ruta completa.** Se descartó: el siguiente paso puede quedar obsoleto antes de
usarse y el contrato de «ir a» solo necesita un paso. Además ampliaría la superficie de
invalidación.

**Bibliotecas de grafos o `heapq`/`sorted()`.** Prohibidas por la Constitución I en producción; las
alternativas de comparación solo pueden existir dentro de `--bench`.

### 3. Decisión

La producción conserva el **recálculo individual por cazador y por decisión**, sin caché,
generación ni estado retenido. La inversa compartida y la reutilizada permanecen como
comparaciones del benchmark. No se adopta la estrategia adaptativa.

La decisión no declara incorrecta la alternativa compartida: solo aplaza su adopción hasta que
existan tareas productivas concretas en `plan.md`/`tasks.md`, una política de invalidación y
limpieza, y una validación del ciclo completo con la referencia oficial. Mientras tanto no se crea
ninguna caché productiva ni se altera el estado canónico.

### 4. Análisis de complejidad

Con `E_R`, `P_R`, `Q_R` y `Q_fin` definidos en `plan.md`:

| Estrategia | Tiempo esperado | Memoria adicional | Estado retenido |
|---|---|---|---|
| Individual, una consulta | `O(E_R + P_R log max(2,Q_R) + Q_fin)` | `O(D_R+Q_R)`, peor `O(D_R+E_R)` | Ninguno |
| `H` consultas individuales | Suma de las regiones de cada cazador | `O(max(D_R+Q_R))`, liberada entre consultas | Ninguno |
| Inversa compartida por ciclo | `O(E_L + P_L log max(2,Q_L) + Q_fin_L + H)` | `O(D_L+Q_L)` | Solo durante el ciclo del benchmark |
| Inversa reutilizada | Consultas más invalidación/reconstrucción | `O(D_L+Q_L)` retenida | Solo en el benchmark |
| Adaptativa | Decisión de estrategia no medida | La de la estrategia elegida | No implementada |

La ventaja de compartir crece con `H`, pero también con el tamaño de la región que impone el rango
máximo. La reutilización añade el costo de detectar y pagar invalidaciones; no se asume que sea
gratis. El benchmark mide esos componentes por separado y no atribuye a la variante retenida un
costo que no haya cronometrado.

### 5. Evidencia empírica

Entorno: Python 3.12.10 sobre Windows 11, `perf_counter_ns`, semilla 2609, un calentamiento y nueve
repeticiones; preparación del fixture fuera del intervalo y todas las muestras conservadas en los
JSON. T046 usa 64 salas, 20 cazadores, rango 640 y lotes de tres ciclos; T048 usa 64 salas, 28
cazadores, rango 16 400 y un ciclo completo por muestra. **Las dos tablas no son intercambiables**:
distinta cantidad de cazadores y distinto número de ciclos por lote.

**Comparación de rutas (T046/T065), medianas:**

| Carga (64 salas, 20 cazadores, rango 640) | Individual | Inversa compartida | Inversa reutilizada |
|---|---:|---:|---:|
| Puertas estables, 3 ciclos | 26 813 300 ns/lote | 587 200 ns/lote | 301 700 ns/lote |
| Cambios frecuentes, 3 ciclos | 18 713 300 ns/lote | 662 300 ns/lote | 586 800 ns/lote |

**Ciclo completo (T048), medianas:**

| Carga (64 salas, 28 cazadores, rango 16 400) | Producción individual | Retención experimental |
|---|---:|---:|
| Puertas estables | 20.5445 ms; p95/máx. 36.8259 ms; 7/9 muestras `>=20 ms` | 3.1269 ms; p95/máx. 4.0276 ms; 0/9 |
| Puertas inestables | 17.9640 ms; p95/máx. 33.2342 ms; 2/9 | 2.6901 ms; p95/máx. 3.6784 ms; 0/9 |

Antes de cada reloj, T046 comparó acción, alcanzabilidad, costo total, primera vecina y costo del
primer paso; T048 comparó la huella de reloj, secuencia, agenda, salas, enemigos, puertas, jugador,
azar, resultado y orden de notificaciones. No hubo divergencias observables y los 288 ciclos
sintéticos clasificaron `completo`. La retención experimental pagó dentro del intervalo una
construcción, 26 consultas y 135 salidas examinadas en estable; 23 consultas, una invalidación por
`puertas`, una reconstrucción y 267 salidas en inestable. Producción no expone contadores internos
de ruta: sus filas solo reportan 28 y 24 notificaciones enemigas y, en inestable, un cierre.

### 6. Límites conocidos

- Las cifras son sintéticas, de un solo equipo y de nueve muestras; no son la referencia oficial
  de `PR-001` y no permiten afirmar cumplimiento ni incumplimiento de los 20 ms.
- T046 y T048 no comparten carga; no se comparan sus cocientes ni se les atribuye una causa.
- La alternativa compartida/reutilizada no se adopta y no hay caché productiva. Cualquier
  adopción futura exige actualizar primero `plan.md`/`tasks.md` con tareas productivas concretas y
  repetir la validación de ciclo completo.
- La estrategia adaptativa no tiene umbral medido y no se implementó.
- Las filas aún no están registradas en `main.py --bench`; T049/T050 siguen abiertas y estas
  mediciones son evidencia aislada de los proveedores, no cierre del Principio IX.
- No se afirma que la decisión individual sea la más rápida en todos los escenarios; solo es la
  estrategia productiva acordada y validada hasta ahora.

**Trazabilidad**: `logica/rutas_ponderadas.py`; `logica/comportamiento_enemigos.py`;
`benchmarks/terreno_cazador_integrante1.py`; `benchmarks/benchmark_ciclo_real_integrante1.py`;
`benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json`;
`benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json`; `tasks.md` (T046, T048, T057,
T065).

---

## 5.2 Recálculo frente a reutilización

**Especificación**: [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md) ·
**Plan**: [specs/001-terreno-y-cazador/plan.md](specs/001-terreno-y-cazador/plan.md) ·
**Diseño medido**: [research.md](specs/001-terreno-y-cazador/research.md) (R-05, R-06, R-13)

**¿Coincide con el plan original?** Sí para el alcance productivo actual: el plan fija recálculo
desde cero sin estado retenido y reserva la reutilización para `--bench`. La medición favoreció a
la retención en las cargas sintéticas, pero no cubre la referencia oficial ni toda la política de
invalidación requerida para adoptar estado retenido en producción.

### 1. Problema

`FR-014` exige que cada decisión del cazador sea observablemente idéntica a calcularla desde cero
en ese instante. La reutilización puede ahorrar trabajo, pero solo es válida si respeta aperturas y
cierres de puertas —incluido el cierre automático—, cambios de sala del jugador y del cazador,
cambios de velocidad y movimientos o muertes de otros actores cuando alteran ataque, espera,
primera vecina o costo. No se presupone que todos esos cambios invaliden lo mismo.

La pregunta es si producción debe conservar el recálculo o adoptar una inversa retenida con
invalidación. La segunda opción introduce estado derivado, una política de invalidación y limpieza;
la primera es más simple y coincide con la referencia normativa.

### 2. Alternativas consideradas

**Recálculo desde cero por decisión.** No conserva resultados, no necesita invalidación y libera
sus auxiliares al terminar. Es la producción actual.

**Inversa retenida con invalidación explícita.** Mantiene la inversa entre ciclos y la reconstruye
cuando cambian las puertas o el objetivo. Debe pagar consultas, invalidación, reconstrucción y
limpieza dentro del intervalo. Vive solo en el benchmark.

**Invalidación global por generación.** Cualquier cambio descarta toda la inversa. Es segura pero
pierde la mayor parte de la reutilización; no se implementó porque no hay una decisión productiva
que la justifique.

**Invalidación selectiva por puerta.** Requiere un índice puerta→resultados y una medición del
ahorro; es una candidata futura, no una decisión actual.

**Invertir las mutaciones de la caché en el historial.** Se rechazó: mezcla estado derivado con
estado canónico y aumenta los cambios reversibles sin valor observable.

**Copia completa por decisión.** Prohibida por la Constitución VII.

### 3. Decisión

Producción conserva el **recálculo desde cero**, sin caché ni estado retenido. Esto no afirma que
sea la vía más rápida: la evidencia sintética medida favorece a la retención. La inversa
reutilizada es una comparación exclusiva del benchmark; su construcción, consultas, invalidación,
reconstrucción y limpieza se pagan dentro del intervalo medido. No se añaden ganchos de
invalidación a `historia`, `RETROCEDER` ni `iniciar` porque no existe caché productiva que
invalidar.

Si una decisión posterior adopta reutilización, primero deben añadirse tareas productivas
concretas con propietario y archivos, definir la política de invalidación y validar el ciclo
completo. Mientras tanto no se crea ninguna caché.

### 4. Análisis de complejidad

| Vía | Costo por decisión/ciclo | Memoria | Invalidación y limpieza |
|---|---|---|---|
| Recálculo individual | `O(E_R + P_R log max(2,Q_R) + Q_fin)` por cazador | `O(D_R+Q_R)`, peor `O(D_R+E_R)`, liberada al terminar | No aplica |
| Inversa retenida | Consulta esperada `O(1)` por cazador; reconstrucción `O(E_L + P_L log max(2,Q_L) + Q_fin_L)` cuando se invalida | `O(D_L+Q_L)` retenida | Invalidación de generación `O(1)`; reconstrucción y limpieza completas |
| Generación global | Descarta toda la inversa ante cualquier cambio | La de la inversa | `O(1)` para descartar; reconstrucción completa |
| Selectiva por puerta | Debe identificar y reconstruir solo lo afectado | Índice adicional puerta→resultados | No medida |

El recálculo evita el costo de mantener y limpiar estado derivado. La reutilización solo compensa
si la frecuencia de consultas supera el costo de invalidaciones y reconstrucciones; el benchmark
mide ambos lados, pero no autoriza a asumir que la balanza se mantenga en la referencia oficial.

### 5. Evidencia empírica

T046 comparó ambas vías con 64 salas, 20 cazadores, rango 640 y tres ciclos por lote. Las medianas
de la inversa compartida y reutilizada fueron 587 200/301 700 ns con puertas estables y
662 300/586 800 ns con cambios frecuentes, frente a 26 813 300/18 713 300 ns del recálculo
individual. La reutilización incluyó la invalidación en el intervalo.

T048 comparó el ciclo completo de producción con la retención experimental sobre la misma
plantilla, acción `ESPERAR`, semilla 2609 y carga:

| Carga (64 salas, 28 cazadores, rango 16 400) | Producción | Retención experimental | Trabajo retenido |
|---|---:|---:|---|
| Puertas estables | 20.5445 ms; 7/9 `>=20 ms` | 3.1269 ms; 0/9 | 26 consultas, 1 construcción, 0 invalidaciones, 135 salidas |
| Puertas inestables | 17.9640 ms; 2/9 `>=20 ms` | 2.6901 ms; 0/9 | 23 consultas, 1 construcción, 1 invalidación (`puertas`), 1 reconstrucción, 267 salidas |

Las nueve muestras productivas `>=20 ms` fueron: estable, índices 1/2/4/5/6/7/8 con
20.5445/20.4867/21.7241/22.2237/20.0708/21.0831/36.8259 ms; inestable, índices 5/6 con
33.2342/22.9758 ms. Todas clasificaron `completo` y `exito=true`. Cada muestra estable registró
28 notificaciones y 28 eventos enemigos, sin evento de puerta; cada muestra inestable registró
24 notificaciones, 24 eventos enemigos, un evento de puerta y el cierre `p2-1`. Producción no
instrumentó contadores internos de ruta (`contadores_internos_comparados=false`), así que no se
atribuye la demora a una fase concreta ni se deriva un umbral adaptativo.

La huella previa al cronómetro comparó reloj, secuencia, agenda, salas, enemigos, puertas, jugador,
azar, resultado y orden de notificaciones. Los 288 ciclos sintéticos fueron completos y no hubo
divergencias observables. En estable no hubo cierres; en inestable se observó un cierre (`p2-1`)
dentro del intervalo. Producción reporta 28 y 24 notificaciones enemigas, respectivamente.

### 6. Límites conocidos

- Son mediciones sintéticas de un equipo y nueve repeticiones; no son la referencia oficial ni
  prueban el límite de 20 ms.
- La retención experimental es más rápida en estas cargas, pero no se adopta: faltan tareas
  productivas, política de invalidación y validación oficial. No se atribuye la diferencia a una
  causa no medida.
- El tiempo retenido incluye construcción, consultas, invalidación, reconstrucción y limpieza; no
  es un coste de consulta aislado.
- La conexión a `main.py --bench` sigue pendiente de T049/T050; estas filas son evidencia aislada.
- Solo caracterizan el equipo y las cargas indicadas. No se infiere el comportamiento en la
  referencia oficial ni en otras máquinas.
- Cualquier adopción futura debe actualizar `plan.md`/`tasks.md` y repetir la validación; no se
  crea caché mientras tanto.

**Trazabilidad**: `logica/motor_juego.py`; `logica/comportamiento_enemigos.py`;
`logica/rutas_ponderadas.py`; `benchmarks/benchmark_ciclo_real_integrante1.py`;
`benchmarks/terreno_cazador_integrante1.py`;
`benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json`; `tasks.md` (T048, T068).

---

## 5.3 El mapa conocido

**Especificación**: [specs/003-niebla-y-ir-a/spec.md](specs/003-niebla-y-ir-a/spec.md) ·
**Plan**: [specs/003-niebla-y-ir-a/plan.md](specs/003-niebla-y-ir-a/plan.md) ·
**Alternativas**: [specs/003-niebla-y-ir-a/research.md](specs/003-niebla-y-ir-a/research.md)

**¿Coincide con el plan original?** Sí en lo esencial: las dos ideas del plan —no almacenar lo
desconocido y reutilizar el buscador de 001 con otra vista— se implementaron tal cual. Lo que el
plan no previó fue el choque con la línea de tiempo, descrito en *Límites conocidos*.

### 1. Problema

El jugador deja de ver la cripta entera y pasa a conocer solo lo que descubrió. Hay que mantener,
por cada sala, uno de tres estados desde su punto de vista, y recordar el estado de cada puerta
tal como la observó la última vez, aunque haya cambiado después.

§5.3 fija tres exigencias que tiran en direcciones distintas:

- **Consultar** si una sala está explorada, avistada o desconocida, y el estado recordado de una
  puerta, son operaciones muy frecuentes: ocurren en cada dibujo de la vista, en cada paso de
  «ir a» y en cada actualización por antorcha.
- **Explorar** salas nuevas debe costar en proporción a las salas reveladas, no al tamaño del
  mapa conocido.
- **Registrar y deshacer** un cambio debe ser barato, porque el mapa se revierte con el pergamino
  y se reconstruye en la línea de tiempo.

Y una cuarta, de §3.4: calcular un paso del viaje por debajo de 5 ms.

### 2. Alternativas consideradas

**Marcar el estado en cada sala del mapa real.** Mezcla el conocimiento del jugador con el
esqueleto, que §3.3 separa expresamente, y deja a la línea de tiempo sin forma de reconstruir el
conocimiento de un instante pasado sin tocar el mapa.

**Una lista de salas exploradas.** Consultar pasaría a recorrer la lista, justo lo que §5.3
señala como operación frecuente y lo que el Principio II prohíbe. Se midió: ver más abajo.

**Guardar también las desconocidas, con su estado.** Hace que explorar y consultar dependan del
tamaño del mapa completo en vez de lo descubierto, y rompe la proporcionalidad.

**Una copia del mapa recortada al conocimiento.** Habría que rehacerla en cada revelación y
copiarla entera para el retroceso, que es lo que el Principio VII prohíbe.

**Un buscador de caminos propio para «ir a».** §5.3 pide justificar si se comparte implementación
con la búsqueda del cazador: **se comparte**. El buscador de 001 ya minimiza la suma de costos y
desempata por la vecina de menor id, que es exactamente lo que §3.4 pide. Lo que se separa es el
**dato**, no el algoritmo.

### 3. Decisión

**Lo desconocido no se almacena.** Tres tablas hash propias indexadas por id: salas exploradas,
salas avistadas y puertas observadas. Una sala desconocida simplemente no está en ninguna.

De ahí salen las tres exigencias de §5.3 sin trucos: consultar es una búsqueda por id; revelar
`k` salas son `k` inserciones, independientemente de cuántas haya ya; y cada revelación es un
hecho pequeño e independiente, así que deshacerla es quitar esos hechos y nada más.

Para el viaje se construye una **vista** con la misma interfaz que ya consume el buscador de 001
—`contiene_sala` y `salidas_transitables`— pero que responde solo con lo que el jugador sabe:
`contiene_sala` solo por salas exploradas, y `salidas_transitables` solo por salidas que el mapa
**recuerda** abiertas hacia salas exploradas.

La separación la garantiza la vista y no la disciplina de quien la use: el buscador **no recibe
el mapa real**, así que no puede observar lo que el jugador no sabe aunque el código cambiara.

### 4. Análisis de complejidad

Con `V` salas conocidas y `E` salidas conocidas:

- Consultar el estado de una sala o de una puerta: **O(1)** promedio.
- Entrar a una sala y revelar sus vecinas: **O(salidas de esa sala)**, no O(V).
- Registrar o deshacer una revelación: **O(1)** por hecho revelado.
- Un paso del viaje: lo que cueste el buscador de 001 sobre el subgrafo conocido.

### 5. Evidencia empírica

Consultar el estado de una sala, mediana de 5 repeticiones, sobre mallas deterministas por
semilla:

| SALAS | TABLA PROPIA | RECORRIENDO EL MAPA | VECES |
|---|---|---|---|
| 100 | 612 ns | 2 502 ns | 4× |
| 400 | 628 ns | 9 181 ns | 15× |
| 900 | 687 ns | 19 220 ns | 28× |
| 1 600 | 671 ns | 34 189 ns | **51×** |

La tabla propia se mantiene plana —de 612 a 671 ns entre 100 y 1 600 salas— mientras recorrer
crece de forma lineal. Eso es `SC-002`.

Explorar una sala, con mapas conocidos de distinto tamaño:

| SALAS YA CONOCIDAS | POR REVELACIÓN |
|---|---|
| 100 | 14,9 µs |
| 400 | 20,5 µs |
| 900 | 20,1 µs |
| 1 600 | 20,5 µs |

Se estabiliza: revelar cuesta lo mismo sobre un mapa de 400 que sobre uno de 1 600. Eso es
`SC-003`.

Un paso de «ir a», contra el límite de 5 ms de §6.1:

| SALAS | MEDIANA | LÍMITE |
|---|---|---|
| 9 | 0,242 ms | 5 ms |
| 25 | 0,876 ms | 5 ms |
| 49 | 1,971 ms | 5 ms |
| 64 | 2,497 ms | 5 ms |

Las criptas publicadas tienen entre 6 y 50 salas, así que el caso real queda en unos 2 ms, con
algo más del doble de margen.

### 6. Límites conocidos

- **El paso de «ir a» se pasa de 5 ms en criptas mucho mayores que las publicadas.** Con 100
  salas conocidas son 4,3 ms y con 1 600 son 89,9 ms. No se optimizó porque las criptas
  publicadas llegan a 50 y §6.1 admite ajustar los valores cuando se publique la cripta de
  referencia. Si esa cripta resultara mucho mayor, el camino sería reutilizar el cálculo entre
  pasos mientras el mapa conocido no cambie, que es lo que el contrato con 001 dejó abierto
  —«podemos reutilizar auxiliares después, si demostramos equivalencia»—, no cambiar la
  estructura.
- **El conocimiento todavía no se revierte ni se guarda.** `FR-022` está sin implementar: el
  mecanismo de rehacer de la línea de tiempo (§5.5) solo sabe restaurar atributos, listas y
  diccionarios, y el conocimiento vive en tablas propias que se modifican en su sitio, como exige
  §6.2. Hace falta que esa capacidad ofrezca una forma de volver a aplicar un cambio; está
  planteado al grupo. Mientras tanto el conocimiento avanza pero no retrocede.
- **Las mediciones usan mallas regulares.** Validan el crecimiento, no cualquier topología.
- Las mediciones son de un solo equipo y no caracterizan otras máquinas.

**Trazabilidad**: `logica/mapa_conocido.py`; `logica/viaje.py`;
`logica/rutas_ponderadas.py` (buscador de 001, no se modifica);
`benchmarks/integrante2.py` (`medir_mapa_conocido`, `medir_paso_ir_a`);
`tests/test_logica/test_mapa_conocido.py`; `tests/test_logica/test_viaje.py`.

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

El recorrido en sí es **`O(V + E + L)`**, frente a `O(L·(V+E))` de la alternativa ingenua. La
memoria es `O(V + E + L)`.

**Pero el costo observado no es lineal, y la causa está fuera de esta capacidad.**
`MapaCripta.obtener_sala` recorre el arreglo de salas —su propio comentario lo declara: «búsqueda
O(n), sin índice hash»—, así que cada consulta por id cuesta `O(V)` y el recorrido completo se
vuelve `O(V²)` en criptas grandes. Medido con un perfilador sobre una cripta de 641 salas, esa
función sola se lleva el 35 % del tiempo de verificación.

Sustituyéndola por un índice por id, con la misma tabla hash propia, el tiempo baja de 18,85 ms a
7,34 ms en 641 salas y el factor al duplicar el tamaño pasa de 2,9 a 2,1, que es lo que `SC-002`
pide. No se cambió aquí porque `MapaCripta` es un componente compartido y el Principio VIII exige
identificar a sus consumidores y acordar el cambio; además es justo la observación que el profesor
hizo sobre la primera parte y que el Principio II recoge. Queda reportado al grupo.

Esto **no** compromete el límite de §6.1: la cripta publicada más grande tiene 50 salas y se
verifica en 0,51 ms. El efecto solo aparece en las criptas sintéticas de cientos de salas que
genera el `--bench`.

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

---

## 5.5 Línea de tiempo y puntos de control

**Especificación**: [specs/004-linea-de-tiempo/spec.md](specs/004-linea-de-tiempo/spec.md) ·
**Plan**: [specs/004-linea-de-tiempo/plan.md](specs/004-linea-de-tiempo/plan.md) ·
**Alternativas y mediciones previas**: [specs/004-linea-de-tiempo/research.md](specs/004-linea-de-tiempo/research.md) ·
**Responsable**: Joshua Cabrera Bonilla

**¿Coincide con el plan original?** En el mecanismo, sí: reconstruir hacia atrás desde el punto de
control siguiente. Cambió en cuatro puntos, todos por mediciones o pruebas: (1) la primera versión
del plan copiaba el estado en cada consulta; `/speckit-analyze` lo marcó contra el principio VII y
se cambió a deshacer y rehacer en sitio; (2) el K por defecto pasó de 50 a 10 con la medición de
T001; (3) la copia del estado real exigió arreglar la serialización de las salas (Sofía, `f89b7b5`)
y de la lista doble, que se copiaba de forma recursiva; (4) el punto de control comparte el historial
del pergamino y las tuplas del azar en lugar de copiarlos, lo que bajó la copia de 71,5 a 19,1 ms.

### 1. Problema

`historia <t>` e `historia #k` deben mostrar el estado de la partida en cualquier instante pasado
sin modificarla (§3.6). Se permiten copias completas del estado, pero como máximo una cada K
acciones del jugador, y una consulta no puede aplicar ni deshacer cambios de más de K acciones
(§5.5). Ubicar el punto de control más cercano es frecuente y su costo importa en partidas largas.
Al usar un pergamino la línea debe recortarse sin recorrer la historia. El límite es 50 ms con al
menos 5 000 acciones y el K por defecto (§6.1).

### 2. Alternativas consideradas

| Alternativa | Resultado |
|---|---|
| Sin puntos de control: deshacer desde el estado actual | Viola «como máximo K». Medido: hasta 97 s por consulta con 5 000 acciones. |
| Una copia completa por acción (K = 1) | Viola la memoria de §5.5 («acciones por tamaño del estado»). |
| Copia de trabajo del punto de control en cada consulta | Choca con el principio VII. Medido en T001: de 8 a 14 veces más lenta que deshacer. |
| Re-simular hacia adelante desde el punto de control anterior | Llega al mismo estado (comprobado). Con el contenido de todas las salas cargado salió más rápida (10 ms frente a 44 ms con K = 10). Se descartó para producción porque ejecuta las reglas del motor en cada consulta y, con salas descargadas después del punto de control, necesitaría volver a pedir contenido al servicio (presupuesto de solicitudes, principio VI). Las copias tampoco llevan el catálogo de fichas. |
| **Hacia atrás desde el punto de control siguiente, deshaciendo y rehaciendo en sitio** | **Elegida.** |

### 3. Decisión

- **Instantes**: arreglo contiguo no decreciente con el reloj de cada decisión; el instante t se
  traduce a una acción con una búsqueda binaria propia (sin `bisect`).
- **Puntos de control**: arreglo contiguo; el de la acción j·K está en la posición j, así que se
  ubica por aritmética, ⌈(k − 1) / K⌉. Cada punto es una sola copia profunda del estado y de las
  transacciones de su ventana, hecha junta para que los cambios copiados apunten al estado copiado.
  Comparte en vez de copiar el historial del pergamino y las tuplas inmutables del azar.
- **Consulta**: deshace sobre el punto de control (o sobre el estado vivo si la acción está después
  del último punto) como máximo K transacciones, la última a medias si t cae entre dos decisiones;
  arma el resumen y rehace con los inversos en un `finally`. Nunca copia el estado.
- **Pergamino**: la línea quita lo revertido del final de sus arreglos y descarta los puntos
  posteriores. Recoger, soltar y consumir pergaminos se anotan como cambios «solo línea» para que el
  pasado los muestre bien.
- **K por defecto: 10** (`LineaTiempo.K_POR_DEFECTO`, configurable con `--checkpoint-cada`).
- **Persistencia**: pendiente del guardado de Steven (contrato `specs/004-linea-de-tiempo/contracts/guardado-v10.md`).

### 4. Análisis de complejidad

| Operación | Costo |
|---|---|
| Registrar una acción | O(1) amortizado, más una copia del estado cada K acciones |
| Ubicar el punto de control de #k | O(1) |
| Ubicar la acción de un instante t | O(log n) |
| `historia` | O(c · K) para deshacer y rehacer, con c cambios por acción, más armar el resumen |
| Recorte por pergamino | O(r), con r ≤ 5 acciones revertidas |
| Memoria | ⌈n / K⌉ copias del estado más los cambios de todas las acciones |

### 5. Evidencia empírica

Todo sale de `main.py --bench` (`benchmarks/linea_tiempo.py`, proveedor `medir_linea_tiempo`) y
queda guardado en `benchmarks/resultados/linea_tiempo_5000.json` (los cuatro K en una partida) y
`benchmarks/resultados/linea_tiempo_5000_k10.json` (K = 10 solo, en un proceso aparte). Carga:
5 000 acciones de `cripta-04` (50 salas), semilla 7, jugador con vida muy alta solo en la medición
para que la partida dure, lo que va activando enemigos de toda la cripta (unos 110 cambios por
acción). Es un peor caso.

| K | `historia`: mediana / p95 / máximo | Crear un punto (mediana) | Memoria de la línea | Máx. transacciones por consulta |
|---|---|---|---|---|
| **10 (solo)** | **16,3 / 59,7 / 82,7 ms** | **50,6 ms** | **647 MB** | 9 |
| 50 | 128,7 / 473,0 / 482,4 ms | 294 ms | 518 MB | 48 |
| 200 | 549,6 / 1 918 / 2 307 ms | 1 372 ms | 439 MB | 193 |
| sin puntos | 22,9 s / — / 97,2 s | — | 0,3 MB | 3 932 |

Las filas de 50 y 200 se midieron con las cuatro líneas en el mismo proceso (más de 1,5 GB), lo
que agrega pausas del sistema; por eso K = 10 se midió también por separado. Otras mediciones:
un retroceso de punta a punta cuesta 3,1 ms frente a 82,8 ms de copiar el estado; reconstruir hacia
atrás y re-simular llegan al mismo estado con los tres K; el replay rechaza un log de otra versión.

**Por qué K = 10.** Es el único de los tres que deja la mediana de `historia` muy por debajo de
50 ms (16 ms). Con K = 50 la mediana ya pasa los 100 ms. La memoria baja poco al subir K (de 647 a
439 MB), porque la mayor parte son los cambios de las acciones, que se guardan igual con cualquier K
(eso es lo que pide §5.5: crecer con los cambios); por eso subir K no compensa.

### 6. Límites conocidos

- **`historia` no cumple 50 ms en todos los casos** con esta carga: el p95 es 60 ms y el máximo
  83 ms. La mediana sí (16 ms). En una partida normal, con menos enemigos activos por acción, cada
  transacción es más chica y las consultas son más rápidas (T001: 5,6 ms de mediana con 600 acciones).
- **La acción que crea un punto de control pasa los 20 ms por ciclo** (unos 51 ms, una de cada 10
  acciones). Mejoras posibles, no implementadas: tomar el punto de control fuera del ciclo de la
  decisión, o una copia propia del estado más barata que `copy.deepcopy`.
- **Memoria alta en partidas muy largas** (unos 650 MB con 5 000 acciones en esta carga).
- **Guardar y cargar la línea** depende del guardado de Steven; mientras tanto, una partida cargada
  empieza sin línea de tiempo.
- **El mapa conocido** del resumen dice «no disponible» hasta que exista la spec 003.
- `pickle` ejecuta código al cargar un archivo malicioso; se acepta porque el archivo de partida es
  local y lo produce el propio juego.

**Archivos**: `logica/linea_tiempo.py`, `logica/cambios.py`, `logica/historial_reversible.py`,
`logica/servicio_inventario.py`, `logica/inventario.py`, `estructuras/lista_doble.py`,
`controller/resumen_historia.py`, `controller/ejecutor_replay.py`, `controller/controlador_juego.py`,
`benchmarks/linea_tiempo.py`.

---

## 5.6 Revisión de decisiones con la carga nueva

**Historial de retroceso (Joshua, spec 004, FR-025).** Con la carga nueva (cazadores, costos
variables y la línea de tiempo vinculada), un retroceso con pergamino de punta a punta (reloj, agenda,
rastro, puertas, trampas, inventario y azar) cuesta 3,1 ms de mediana, frente a 82,8 ms de guardar una
copia completa del estado por acción (`benchmarks/resultados/linea_tiempo_5000.json`, fila
`retroceso_punta_a_punta`). La decisión de la Parte I (cambios reversibles, sin copias) sigue siendo
adecuada. Cambió un detalle: la lista doble que usa el historial se copiaba de forma recursiva y
reventaba en partidas largas; ahora se copia y serializa de forma iterativa (ver §5.5).

**Especificación**: [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md) ·
**Plan**: [specs/001-terreno-y-cazador/plan.md](specs/001-terreno-y-cazador/plan.md) ·
**Diseño medido**: [research.md](specs/001-terreno-y-cazador/research.md) (R-05, R-10)

**¿Coincide con el plan original?** Sí: se conserva `AgendaEventos` como agenda productiva. La
carga nueva no cambia la decisión de la Parte I; la alternativa lineal sigue siendo exclusiva del
benchmark.

### Agenda bajo carga nueva (T069)

#### 1. Problema

`PR-005` exige repetir las mediciones de agenda de la Parte I con cientos de eventos, costos
variables y cazadores activos, comparando por separado insertar, extraer, cancelar por ID,
cancelar por actor, reprogramar y resolver empates frente a una alternativa comparable. La
decisión de la Parte I eligió `AgendaEventos`; la pregunta es si la carga nueva la sigue
justificando o si algún patrón aconseja cambiarla.

La agenda participa en el ciclo completo entre decisiones del jugador, pero esta medición es un
workload aislado: no incluye rutas, motor, red ni renderizado. Por tanto, sus tiempos no se
presentan como el ciclo de `PR-001`.

#### 2. Alternativas consideradas

**`AgendaEventos` productiva.** Usa la agenda de la Parte I con sus índices, árbol AVL y montículo
propios para insertar, extraer, cancelar y reprogramar por tiempo y secuencia. Es la decisión
vigente.

**Lista lineal manual, solo en el benchmark.** Busca y retira por recorrido; no reimplementa ni
sustituye la agenda productiva. Sirve como alternativa comparable con la misma carga y los mismos
resultados observables.

**Cambiar la producción a una lista lineal.** Se descarta: perdería las operaciones por tiempo,
secuencia e índices que la agenda ya ofrece y trasladaría al ciclo completo un costo que la
medición no justifica.

**Reimplementar la agenda dentro del benchmark.** Se descarta: la alternativa debe ser comparable,
no una segunda agenda productiva que oculte diferencias de contrato.

#### 3. Decisión

Se conserva **`AgendaEventos`** como agenda productiva y no se modifica su implementación. La
lista lineal permanece como alternativa local al benchmark. La decisión de la Parte I se mantiene
aunque la lista lineal haya sido más rápida en cancelaciones por ID y por actor en esta carga: las
otras cuatro operaciones y el flujo mixto favorecen a la agenda, y no se adopta un cambio parcial
sin una tarea productiva y una validación del ciclo completo.

#### 4. Análisis de complejidad

Con `N` eventos y `K_a` eventos de un actor:

| Operación | `AgendaEventos` | Lista lineal benchmark-local |
|---|---|---|
| Insertar | `O(log N)` esperado por índice/AVL/montículo | `O(N)` para buscar la posición; `O(1)` para insertar si se recorre una vez |
| Extraer el mínimo | `O(log N)` | `O(N)` para localizar el mínimo |
| Cancelar por ID | `O(log N)` | `O(N)` por búsqueda y retiro |
| Cancelar por actor | `O(log N + K_a)` para localizar; retiro total `O(K_a log N)` | `O(N + K_a)` por recorrido y retiro |
| Reprogramar | `O(log N)` | `O(N)` por búsqueda y reubicación |
| Resolver empates | `O(N log N)` para extraer todos | `O(N²)` por búsquedas repetidas |

La lista lineal puede ser competitiva cuando la operación retira pocos elementos ya localizados,
pero pierde cuando se repite la búsqueda por valor o se extrae repetidamente. El benchmark mide
cada operación por separado y no mezcla esa observación con el ciclo completo.

#### 5. Evidencia empírica

`benchmarks/resultados/agenda_ciclo001_t047_c1_r9_256-512-1024.json` conserva **36 filas/324
muestras** con semilla 2609, un calentamiento y nueve repeticiones. La carga usa 256/512/1024
eventos, tipos `EFECTO`, `CERRAR_PUERTA`, `ENEMIGO`, `JUGADOR_DISPONIBLE` y `VENCER_EFECTO`, 28
destinatarios cazador, puertas y demoras derivadas de costos variables. La equivalencia de estado,
resultado, orden y tiempos se comprobó antes de cada reloj.

Medianas/p95/máximo en **ms por lote de 1024 eventos**:

| Operación | `AgendaEventos` | Lista lineal | Muestras lineales `>=20 ms` |
|---|---:|---:|---:|
| Insertar | 4.9556 / 11.6659 / 11.6659 | 20.0797 / 21.5294 / 21.5294 | 6/9 |
| Extraer | 4.6489 / 14.3053 / 14.3053 | 17.3550 / 19.8748 / 19.8748 | 0/9 |
| Cancelar por ID | 4.6092 / 14.3324 / 14.3324 | 3.9687 / 4.7648 / 4.7648 | 0/9 |
| Cancelar por actor | 0.7760 / 2.1155 / 2.1155 | 0.4667 / 0.5790 / 0.5790 | 0/9 |
| Reprogramar | 10.0860 / 18.0415 / 18.0415 | 24.9376 / 25.2668 / 25.2668 | 9/9 |
| Resolver empates | 15.3412 / 16.3880 / 16.3880 | 39.6939 / 40.7043 / 40.7043 | 9/9 |

Las **24 muestras `>=20 ms`** pertenecen todas a la lista lineal: insertar (6), reprogramar (9) y
resolver empates (9); se conservan sin reducir carga. En esta carga aislada, ninguna muestra de
`AgendaEventos` alcanzó los 20 ms, pero eso no demuestra el ciclo completo de `PR-001`.

#### 6. Límites conocidos

- Es una medición aislada de agenda, no un ciclo completo entre decisiones del jugador; no incluye
  rutas, motor, red ni renderizado.
- Las cifras son sintéticas, de un solo equipo y nueve repeticiones; no son la referencia oficial.
- Que la lista lineal gane en cancelaciones por ID/actor no cambia la decisión: no se atribuye a
  una causa no medida ni se adopta un cambio parcial sin tarea productiva y validación completa.
- Las 24 muestras lentas son de la alternativa lineal, no de `AgendaEventos`; no se presentan como
  incumplimiento de `PR-001`.
- La conexión a `main.py --bench` sigue pendiente de T049/T050; estas filas son evidencia aislada
  de los proveedores, no cierre del Principio IX.
- Solo caracterizan el equipo y las cargas indicadas.

**Trazabilidad**: `logica/agenda_eventos.py`; `logica/motor_juego.py`;
`benchmarks/terreno_cazador_integrante1.py`; `tests/test_bench_agenda_t047.py`;
`benchmarks/resultados/agenda_ciclo001_t047_c1_r9_256-512-1024.json`; `tasks.md` (T047, T069).

La evidencia complementaria del mapa se documenta en [Índice por ID de MapaCripta (evidencia
complementaria de 001)](#índice-por-id-de-mapacripta-evidencia-complementaria-de-001). Esta
referencia no cambia la decisión de Resolubilidad de §5.4 ni atribuye a 001 el componente de 002.

### Índice por ID de MapaCripta (evidencia complementaria de 001)

**Especificación**: [specs/001-terreno-y-cazador/spec.md](specs/001-terreno-y-cazador/spec.md) ·
**Plan**: [specs/001-terreno-y-cazador/plan.md](specs/001-terreno-y-cazador/plan.md) ·
**Diseño medido**: [benchmarks/mapa_cripta_integrante1.py](benchmarks/mapa_cripta_integrante1.py)

#### 1. Problema y consumidores

`MapaCripta` necesita conservar el orden de llegada de las salas, pero una lista sola obliga a
recorrer hasta `V` referencias para resolver cada ID. Esa búsqueda aparece en operaciones
frecuentes y, al vincular `E` salidas, puede repetirse una vez por puerta. El costo lineal no es
solo del verificador de Resolubilidad: también afecta, entre otros, inicialización y restauración
(`datos/decodificador_datos.py`, `service/inicializador_partida.py`,
`service/restaurador_partida.py`), simulación (`logica/motor_juego.py`,
`logica/registro_rastro.py`, `logica/gestor_efectos.py`), carga gradual, servicios, vista y pruebas
de identidad/serialización. El cambio debía preservar las firmas y la instancia canónica que esos
consumidores ya observaban.

#### 2. Decisión y alternativa

Se conserva `_salas` como lista de referencias para mantener orden estable, recorrido, guardado y
la sustitución de una sala en su misma posición. En paralelo, `_salas_por_id` usa la
`TablaHashImpl` propia para `obtener_sala` y `contiene_sala`. Altas y sustituciones actualizan las
dos representaciones; `vincular_salidas` consulta el índice y deja cada `Puerta.destino_sala`
apuntando a la instancia canónica. El orden de buckets de la tabla nunca define el orden del mapa.

La comparación usa `_MapaLinealBenchmark`, limitada a
`benchmarks/mapa_cripta_integrante1.py`: conserva únicamente una lista, busca y sustituye por
recorrido y resuelve cada destino de cada puerta con otra búsqueda lineal. Antes de cronometrar se
comprobaron los mismos IDs y orden, aciertos y ausencias idénticos, orden de puertas, destinos y
alias canónicos. La generación de salas/puertas quedó fuera; construcción, consultas y
vinculación tuvieron intervalos separados.

#### 3. Complejidad

Con `V` salas y `E` salidas dirigidas:

| Operación | Lista + `TablaHashImpl` | Peor caso hash | Alternativa lineal medida |
|---|---|---|---|
| Construir | `O(V)` esperado total; inserción `O(1)` esperada/amortizada | `O(V²)` por colisiones patológicas y rehashes | `O(V²)`, porque cada alta comprueba el ID por recorrido |
| Consultar/contener por ID | `O(1)` esperado | `O(V)` | `O(V)` |
| Sustituir una sala | `O(V)` para conservar exactamente la posición; índice esperado `O(1)` | `O(V)` | `O(V)` |
| Vincular todas las salidas | `O(V+E)` esperado | `O(V·E)` si cada consulta degenera | `O(V·E)` |
| Sustituir y revincular | `O(V+E)` esperado | `O(V·E)` | `O(V·E)` |

El índice añade `O(V)` memoria. `obtener_salas()` sigue copiando solo la lista de referencias y no
expone ni ordena la tabla.

#### 4. Entorno, cargas y resultados originales

La ejecución original se conserva en
[`benchmarks/resultados/mapa_cripta_original_c1_r9_32-128-512.json`](benchmarks/resultados/mapa_cripta_original_c1_r9_32-128-512.json).
Usó Python 3.12.10 sobre Windows 11 (`Intel64 Family 6 Model 154 Stepping 3`),
`perf_counter_ns`, semilla de fixture 1729, un calentamiento y nueve repeticiones. La unidad es
**ns por lote** y todas las muestras permanecen en el JSON. Con nueve muestras, p95 por
*nearest-rank* ocupa el rango 9 y coincide con el máximo.

**Construcción** — cada lote añade `V` salas; la densidad indica las puertas ya presentes en el
fixture, cuya generación no forma parte del intervalo:

| V | Salidas/sala | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|
| 32 | 1 | 32 800 | 35 400 | 22 100 | 23 600 |
| 32 | 4 | 37 900 | 40 100 | 17 900 | 18 700 |
| 128 | 1 | 236 500 | 322 500 | 255 900 | 309 700 |
| 128 | 4 | 150 200 | 169 100 | 238 100 | 258 500 |
| 512 | 1 | 675 400 | **33 018 900** | 3 887 900 | 4 211 300 |
| 512 | 4 | 602 900 | 629 200 | 3 613 600 | 4 164 000 |

**Consultas por ID** — cada patrón contiene aciertos al inicio, medio y final y dos ausencias, y se
repite `V` veces:

| V | Consultas/lote | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|
| 32 | 160 | 25 500 | 26 700 | 64 100 | 66 500 |
| 128 | 640 | 100 100 | 102 600 | 1 026 600 | 1 184 500 |
| 512 | 2 560 | 486 100 | 536 700 | 13 630 700 | 13 821 400 |

**Vinculación** — cada lote resuelve todas las salidas del grafo:

| V | Salidas/sala | E | Índice mediana | Índice p95=máx. | Lineal mediana | Lineal p95=máx. |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 1 | 32 | 7 100 | 11 100 | 15 700 | 19 200 |
| 32 | 4 | 128 | 21 300 | 21 800 | 42 800 | 45 000 |
| 128 | 1 | 128 | 29 100 | 37 900 | 181 500 | 193 000 |
| 128 | 4 | 512 | 117 400 | 322 100 | 656 300 | 979 900 |
| 512 | 1 | 512 | 151 100 | 211 500 | 2 541 000 | 3 081 200 |
| 512 | 4 | 2 048 | 376 700 | 433 800 | 9 146 900 | 10 785 800 |

La consulta indexada conserva un costo aproximadamente constante por consulta mientras el lote
crece; la lineal aumenta también con `V`. La vinculación muestra el mismo contraste entre resolver
`E` destinos por hash y hacer `E` recorridos. La construcción paga la estructura adicional y en
32 salas puede ser más lenta; desde 128/512 salas sus medianas son menores que las de la
alternativa lineal medida. Esto matiza la hipótesis histórica de §5.4: confirma el cuello de
botella en las primitivas de consulta/vinculación, pero no vuelve a medir ni atribuye a este
benchmark el cambio de 18,85 ms a 7,34 ms del verificador completo de 002.

#### 5. Muestra extrema y repetición conservada

La construcción indexada de 512 salas y una salida por sala tuvo en la corrida original una
muestra de **33 018 900 ns**, que por el tamaño de nueve muestras fue a la vez p95 y máximo; la
mediana del mismo lote fue 675 400 ns. La muestra se conserva y no se descarta ni se le asigna una
causa no comprobada.

La repetición posterior está en
[`benchmarks/resultados/mapa_cripta_repeticion_c5_r30_512.json`](benchmarks/resultados/mapa_cripta_repeticion_c5_r30_512.json).
Usó el mismo entorno, semilla 1729, tamaño 512 y densidades 1/4, con cinco calentamientos, treinta
repeticiones, todas las muestras conservadas y p95 *nearest-rank* en el rango 29:

| Operación (512 salas) | Densidad | Índice mediana/p95/máx. | Lineal mediana/p95/máx. |
|---|---:|---:|---:|
| Construcción | 1 | 639 950 / 685 600 / 718 600 | 4 484 950 / 4 737 100 / 4 995 200 |
| Construcción | 4 | 652 000 / 897 800 / 1 252 100 | 3 914 450 / 4 462 900 / 4 476 700 |
| Vinculación (`E=512`) | 1 | 218 200 / 1 093 100 / 1 636 300 | 2 394 800 / 2 738 700 / 2 827 800 |
| Vinculación (`E=2 048`) | 4 | 467 850 / 1 449 200 / 1 985 500 | 9 563 400 / 10 065 200 / 10 077 100 |
| Consulta (2 560) | — | 407 000 / 485 200 / 601 000 | 14 014 750 / 14 866 900 / 16 212 400 |

La muestra extrema original no se repitió en esas treinta mediciones de construcción; esta
observación no demuestra por qué apareció y no autoriza a borrar el dato original.

#### 6. Límites y estado de integración

- El proveedor publica `PROVEEDORES` y funciona mediante la interfaz de
  `benchmarks.integrante3.ejecutar`, pero todavía no está registrado en `main.py --bench`; esa
  integración conjunta corresponde a T049. Por eso estos números son evidencia aislada
  complementaria y no una medición final conectada de §5.6.
- Las mediciones validan construcción, consulta e identidad de vinculación; no miden un ciclo de
  juego completo, rutas de cazadores, agenda ni red/renderizado. No demuestran el presupuesto de
  20 ms de PR-001.
- Solo caracterizan el equipo y las cargas indicadas. El peor caso de la tabla hash sigue siendo
  lineal por colisiones, aunque no se observó esa degeneración en estos fixtures.
- T076 permanece abierta hasta que T049/T050/T071 conecten, ejecuten y validen las filas por
  `main.py --bench`; documentar la evidencia aislada no sustituye esas dependencias.

**Trazabilidad**: `logica/mapa_cripta.py`; `estructuras/tabla_hash.py`;
`benchmarks/mapa_cripta_integrante1.py`; `tests/test_bench_mapa_cripta.py`;
`specs/001-terreno-y-cazador/tasks.md` (T007–T009, T049–T050, T071–T076).

---
