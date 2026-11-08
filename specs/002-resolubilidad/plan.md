# Plan de implementación: Verificación de resolubilidad de una cripta

**Directorio**: `specs/002-resolubilidad` | **Fecha**: 2026-11-07 | **Spec**:
[spec.md](./spec.md)

**Integrante**: Steven Moya Porras (Integrante 2). Secciones del enunciado: §3.5, §4.2, §5.4.

## Resumen

Antes de iniciar una partida hay que decidir si la cripta puede ganarse, y explicarlo cuando no.
La decisión se toma con el esqueleto y la ubicación de las llaves, bajo los supuestos de §3.5:
las llaves no se gastan, todo enemigo puede ser derrotado, y ni las trampas ni los cierres
automáticos bloquean.

El enfoque es **un solo recorrido en anchura que se reanuda**. Parte de la sala inicial y avanza
por las salidas abiertas y por las cerradas cuya llave ya se obtuvo. Cuando encuentra una puerta
cerrada cuya llave falta, no la descarta: la **aparca en una lista indexada por esa llave**.
Cuando el recorrido alcanza la sala donde está esa llave, reanuda desde todas las puertas que la
estaban esperando. Termina cuando no queda nada por reanudar.

Cada sala entra una vez en el recorrido y cada puerta se examina a lo sumo dos veces (una al
encontrarla cerrada, otra al liberarla su llave), así que el costo crece de forma lineal con
salas, salidas y llaves, como exige §5.4. Al terminar, lo que quedó aparcado **es** la frontera
bloqueada y **es** el grafo de dependencias entre llaves: los dos salen del mismo recorrido, sin
pasadas adicionales por llave (§5.4, `FR-018`).

## Contexto técnico

**Lenguaje**: Python 3.11, el del proyecto. Sin dependencias nuevas.

**Dependencias**: ninguna nueva. Se reutilizan las estructuras propias ya entregadas en la
Parte I (ver más abajo). `requests` y `pygame` siguen siendo las únicas externas.

**Almacenamiento**: la respuesta de la consulta de llaves se persiste con el resto de los datos
de la cripta y vale mientras coincida la versión (§4.2). El informe viaja en el archivo de
partida (`FR-020`).

**Pruebas**: `pytest`, que también ejecuta las escritas con `unittest`. Fixtures reales en
`tests/fixtures/api_real/`.

**Plataforma**: escritorio, consola y pygame. La verificación no depende de la vista (`FR-012`).

**Tipo de proyecto**: aplicación MVC de un solo paquete, ya existente.

**Objetivo de rendimiento**: verificación en menos de 200 ms sobre la cripta publicada más grande
(§6.1). Crecimiento aproximadamente lineal en salas, salidas y llaves (`SC-002`).

**Restricciones**: §6.2 prohíbe `heapq`, `bisect`, `collections`, `networkx` y cualquier
biblioteca de grafos o rutas; `set` queda prohibido igual que `dict` como índice; `sorted()` y
`.sort()` quedan fuera de los ordenamientos evaluados.

**Escala**: criptas publicadas de 6 a 50 salas; las criptas sintéticas del `--bench` llegan a
cientos de salas con muchas llaves encadenadas.

## Verificación contra la constitución

*Puerta previa a la implementación. Se vuelve a revisar al cerrar el diseño.*

| Principio | Cómo lo cumple este plan |
|---|---|
| I. Estructuras propias | Cero estructuras nuevas y ninguna de biblioteca: `TablaHashImpl`, `ColaCircular` y `MonticuloMinimo`, ya entregadas. La alternativa ingenua aparece solo dentro de `--bench`. |
| II. Acceso por identificador eficiente | Salas visitadas, llaves obtenidas, ubicación de llaves y puertas en espera se consultan por id en O(1) promedio con `TablaHashImpl`. Ningún recorrido lineal para buscar una sala o una llave. |
| III. Determinismo | El orden de obtención se fija por cercanía y, a igual distancia, por menor id de sala; dentro de una misma sala, por id de llave. Dos ejecuciones dan el mismo resultado (`SC-003`, `FR-006`). |
| IV. Separación por capas | El verificador vive en `logica/` y no conoce la red: recibe el mapa y la ubicación de las llaves ya resueltos. Quien los trae es `service/`. |
| V. Validación por versión | La respuesta de llaves se persiste junto a los datos de la cripta y se invalida por versión, con el mecanismo ya implementado. |
| VI. Presupuesto de red | Una sola consulta de llaves por cripta, que cuenta en el presupuesto (§4.3) y se reutiliza: una partida verificada no vuelve a pedir nada (`FR-016`, `SC-004`). |
| VII. Estado reversible | El informe no es estado de juego: se calcula antes de empezar y no cambia durante la partida (`FR-014`). No entra en el pergamino ni en la línea de tiempo. |
| VIII. Contratos estables | `FuenteDatos` gana un método; se actualizan sus dos implementaciones y el doble de prueba. Ver *Riesgos*. |
| IX. Rendimiento medido | `--bench` compara el recorrido incremental contra rehacerlo por cada llave, con criptas sintéticas deterministas por semilla (`SC-007`, §6.3). |
| X. Especificación primero | `spec.md` confirmado en `14f4fda`, antes de este plan y de cualquier código. Cada tarea citará sus `FR`. |
| XI. Pruebas | Se añaden pruebas sin romper las existentes. Los cuatro casos obligatorios de §3.5 tienen prueba propia (`SC-006`). |

**Resultado: pasa.** Sin violaciones que justificar, así que no hay nada en *Seguimiento de
complejidad*.

## Estructura

### Documentación de esta capacidad

```text
specs/002-resolubilidad/
├── spec.md                  # qué y por qué (ya confirmado)
├── plan.md                  # este archivo
├── research.md              # alternativas evaluadas y por qué se descartaron
├── contracts/
│   ├── consulta-llaves.md   # el contrato de datos de §4.2
│   └── cli-verificar.md     # la salida de --verificar y --forzar
├── quickstart.md            # cómo validarlo de punta a punta
└── tasks.md                 # lo genera /speckit.tasks
```

### Código

Archivos nuevos:

```text
logica/verificador_resolubilidad.py   # el recorrido, el informe y la detección de círculos
tests/test_logica/test_resolubilidad.py
tests/fixtures/api_real/cripta-0N/llaves.json   # respuesta de §4.2 por cripta
```

Archivos existentes que se tocan:

```text
contratos/fuente_datos.py       # obtener_llaves(cripta_id)
datos/cliente_api.py            # GET /criptas/<id>/llaves
datos/fuente_offline.py         # leer llaves.json del paquete
service/inicializador_partida.py# verificar antes de construir la partida
service/juego_service.py        # exponer el informe a la vista y al controlador
configuracion.py                # --verificar <cripta> y --forzar
main.py                         # rama de --verificar, sin instanciar la vista
datos/guardado_binario.py       # el informe sobrevive al guardado (v8 → v9)
benchmarks/integrante2.py       # incremental contra repetido por llave
```

**Decisión de estructura**: se conserva el reparto por capas que ya existe. El verificador es
lógica pura en `logica/`, sin red ni vista, igual que `motor_juego.py`. `service/` decide cuándo
llamarlo y de dónde salen los datos.

## El recorrido, en detalle

### Estructuras y por qué

| Dato | Estructura | Por qué |
|---|---|---|
| Salas ya visitadas | `TablaHashImpl` id_sala → bool | pertenencia en O(1); `set` está prohibido (§6.2) |
| Llaves obtenidas | `TablaHashImpl` id_llave → bool | lo mismo, por id de llave |
| Dónde está cada llave | `TablaHashImpl` id_llave → id_sala | se llena de una vez con la respuesta de §4.2 |
| Llaves de cada sala | `TablaHashImpl` id_sala → lista | una sala puede tener varias llaves |
| Puertas esperando una llave | `TablaHashImpl` id_llave → lista de puertas | es la frontera bloqueada y el grafo de dependencias a la vez |
| Frontera del recorrido | `ColaCircular` | el recorrido en anchura es FIFO |
| Desempate dentro de un nivel | `MonticuloMinimo` | mismo patrón que `mas_cercanas` en `cargador_contenido.py:53`: saca los ids en orden sin usar `sorted()` |

Ninguna es nueva. Las cinco tablas se consultan por id en O(1) promedio, que es lo que pide el
Principio II.

### Complejidad

Sean `V` salas, `E` salidas y `L` llaves.

- Cada sala entra en la cola una sola vez: `O(V)`.
- Cada salida se examina al visitarla su sala y, si estaba cerrada y aparcada, una segunda vez al
  liberarse su llave: `O(E)` en total, no `O(L·E)`.
- Cada llave se obtiene una vez y reanuda su lista de puertas una vez: `O(L + E)`.
- Agotada la región alcanzable, **el mismo recorrido continúa** más allá de las puertas
  aparcadas, cruzándolas aunque falte su llave y arrastrando cuál bloquea el paso. Cada sala del
  otro lado entra también una sola vez, así que sigue siendo `O(V + E)`, y al terminar cada sala
  lleva anotada la llave que impide llegar a ella.
- Detección de círculos: seguir, para cada llave sin obtener, la llave que bloquea la sala donde
  está. Esas flechas ya quedaron anotadas por el recorrido, así que es `O(L)` y no hace falta
  construir ningún grafo aparte.

Total **`O(V + E + L)`**, que es el crecimiento lineal que exige `SC-002`. La alternativa
ingenua, rehacer el recorrido entero cada vez que se obtiene una llave, es `O(L · (V + E))`: esa
es la comparación del `--bench`.

### Determinismo

Acordado: primero las llaves más cercanas a la sala inicial; a igual distancia, la de la sala con
menor id; dentro de una misma sala, por id de llave. El recorrido avanza por niveles y cada nivel
sale ordenado del montículo, igual que en `mas_cercanas`, así que no hace falta ordenar nada al
final ni usar `sorted()`.

### Círculos de llaves

Una llave `K` depende de `K'` cuando `K` está en una sala que solo se alcanza atravesando una
puerta que exige `K'`. Esa dependencia no se calcula aparte: cuando el recorrido se queda sin
región alcanzable, sigue cruzando las puertas aparcadas y marca cada sala del otro lado con la
llave que impide llegar a ella. Al terminar, la dependencia de una llave es la marca de su sala,
y buscar círculos es seguir esas flechas.

Acordado: **se reportan todos los círculos**, no solo el primero, ordenados por la llave de menor
id de cada uno. Encontrarlos todos cuesta lo mismo que encontrar uno, y así quien diseñó la
cripta no tiene que verificar varias veces para descubrirlos de a uno.

## Riesgos y cómo se tratan

**`FuenteDatos` es un contrato compartido.** Añadir `obtener_llaves` como método abstracto rompe a
quien no lo implemente. Los consumidores son `datos/cliente_api.py:17`, `datos/fuente_offline.py:12`
y un doble en `tests/test_service/test_inicializador_partida.py`. Se actualizan los tres en el
mismo cambio. Se declara abstracto, no con una implementación por defecto que devuelva vacío: un
valor por defecto silencioso haría que una cripta sin llaves pareciera verificada.

**El formato de guardado cambia de v8 a v9** para que el informe sobreviva a reanudar (`FR-020`).
Un archivo v8 debe reportarse como incompatible, no cargarse a medias. Es el mismo mecanismo que
ya se usó al pasar de v7 a v8.

**El paquete sin conexión todavía no trae `llaves.json`.** Hasta que exista, las pruebas usan
fixtures propios y una cripta sin ese archivo cae en `FR-019`: no se verificó, y no inicia salvo
`--forzar`.

**`--verificar` corre sin vista** (§3.5), así que no puede depender de nada de `vista/`. Por eso
el verificador vive en `logica/` y el informe se devuelve como dato, no impreso desde dentro.

## Lo que este plan deja fuera

- Cualquier juicio sobre el combate. §3.5 supone que todo enemigo puede ser derrotado, y la
  advertencia de ruta que se consideró se retiró por chocar con la niebla de guerra de §3.3. El
  caso y el motivo van al Documento de Decisiones.
- Recalcular el informe durante la partida: describe la cripta, no el avance (`FR-014`).
- Persistir esqueleto y contenido entre partidas, que es la capacidad `005-persistencia-de-cripta`
  anotada en `REPARTO_PARTE2.md`.
