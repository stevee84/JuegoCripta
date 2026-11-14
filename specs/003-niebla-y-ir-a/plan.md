# Plan de implementación: Niebla de guerra y viaje automático «ir a»

**Directorio**: `specs/003-niebla-y-ir-a` | **Fecha**: 2026-11-11 | **Spec**:
[spec.md](./spec.md)

**Integrante**: Steven Moya Porras (Integrante 2). Secciones del enunciado: §3.3, §3.4, §5.3.

## Resumen

Dos cosas unidas. La primera es que el jugador deje de ver la cripta entera: a partir de aquí el
programa mantiene **lo que el jugador sabe**, que avanza al entrar a una sala y al observar sus
puertas, y todo lo que se le muestra sale de ahí. La segunda es que pueda pedir que lo lleven a una
sala que ya exploró, paso a paso, por el camino más barato **de los que él conoce**.

El enfoque descansa en dos ideas:

- **El desconocimiento no se almacena.** Solo se guarda lo que el jugador ya descubrió; una sala
  desconocida simplemente no está. Así explorar cuesta en proporción a lo revelado y no al tamaño
  del mapa conocido, que es lo que pide §5.3.
- **El viaje no inventa nada.** El buscador de caminos de la capacidad 001 ya existe y ya recibe
  una vista de solo lectura. Esta capacidad le entrega **otra vista**, construida solo con el
  conocimiento del jugador. No se escribe un segundo buscador.

## Contexto técnico

**Lenguaje**: Python 3.11, el del proyecto. Sin dependencias nuevas.

**Dependencias**: ninguna nueva. Se reutilizan las estructuras propias ya entregadas, el buscador
de caminos de 001 y el mecanismo de cambios reversibles ya existente.

**Almacenamiento**: el mapa conocido es estado de la partida, así que viaja en el archivo de
guardado. El formato está hoy en **v10**; esta capacidad lo lleva a **v11**.

**Pruebas**: `pytest`. Fixtures reales en `tests/fixtures/api_real/` y criptas de prueba propias.

**Plataforma**: escritorio, consola y pygame.

**Objetivo de rendimiento**: un paso del viaje por debajo de **5 ms** con el mapa conocido completo
de la cripta de referencia (§6.1). Consultas de estado en tiempo constante y exploración
proporcional a lo revelado (§5.3).

**Restricciones**: §6.2 prohíbe `heapq`, `bisect`, `collections`, bibliotecas de grafos y rutas;
`set` queda prohibido igual que `dict` como índice; `sorted()` y `.sort()` fuera de los
ordenamientos evaluados.

**Escala**: criptas publicadas de 6 a 50 salas; las sintéticas del `--bench` llegan a cientos.

## Verificación contra la constitución

| Principio | Cómo lo cumple este plan |
|---|---|
| I. Estructuras propias | Cero estructuras nuevas y ninguna de biblioteca: `TablaHashImpl` para el conocimiento, y el buscador de 001 para el camino. |
| II. Acceso por identificador eficiente | El estado de una sala y el de una puerta recordada se consultan por id en O(1) promedio. Son las consultas más frecuentes del juego (§5.3) y ninguna recorre el mapa. |
| III. Determinismo | El camino lo fija el buscador de 001, que desempata por la vecina de menor id. Dos ejecuciones iguales dan el mismo viaje (`SC-006`). |
| IV. Separación por capas | El conocimiento y el viaje viven en `logica/`. La vista y el controlador solo consultan; ningún archivo de `vista/` recibe el esqueleto completo. |
| V. Validación por versión | No introduce datos nuevos del servicio; el mapa conocido se deriva de lo que el jugador hace. |
| VI. Presupuesto de red | **Cero solicitudes nuevas.** La niebla no cambia qué se descarga, solo qué se muestra: la precarga sigue usando el esqueleto completo, que §3.3 declara infraestructura. |
| VII. Estado reversible | El mapa conocido se revierte con el pergamino mediante el mecanismo de cambios reversibles ya existente, sin copias completas. |
| VIII. Contratos estables | Se añade una vista nueva **sin tocar** el buscador de 001 ni su vista. Ver *Riesgos* para el guardado y los cambios reversibles. |
| IX. Rendimiento medido | `--bench` compara el mapa conocido contra una alternativa que recorre el mapa, y mide el paso de «ir a» (`SC-008`, §6.3). |
| X. Especificación primero | `spec.md` confirmado antes de este plan y de cualquier código. Cada tarea citará sus `FR`. |
| XI. Pruebas | Se añaden pruebas sin romper las existentes. Los seis casos obligatorios de §3.4 tienen prueba propia (`SC-007`). |

**Resultado: pasa.** Sin violaciones que justificar.

## Estructura

### Documentación de esta capacidad

```text
specs/003-niebla-y-ir-a/
├── spec.md                   # qué y por qué (confirmado)
├── plan.md                   # este archivo
├── research.md               # alternativas evaluadas
├── contracts/
│   ├── vista-conocida.md     # qué ve el buscador, y qué no
│   └── cli-ir-a.md           # el comando, el mapa conocido y los motivos de parada
├── quickstart.md             # validación de punta a punta
└── tasks.md                  # lo genera /speckit.tasks
```

### Código

Archivos nuevos:

```text
logica/mapa_conocido.py        # el conocimiento del jugador y la vista que ve el buscador
logica/viaje.py                # la orden de ir a, sus pasos y por qué se detuvo
tests/test_logica/test_mapa_conocido.py
tests/test_logica/test_viaje.py
```

Archivos existentes que se tocan:

```text
dto/estado_partida.py          # el estado lleva el mapa conocido
logica/motor_juego.py          # al entrar a una sala se actualiza el conocimiento
service/juego_service.py       # expone el mapa conocido y el viaje como datos
datos/guardado_binario.py      # el mapa conocido viaja en el archivo (v10 → v11)
service/restaurador_partida.py # lo reconstruye al reanudar
controller/controlador_juego.py# comandos «mapa» e «ir a»   ← de Joshua, ver Riesgos
benchmarks/integrante2.py      # mediciones de §5.3 y del paso de «ir a»
```

**Decisión de estructura**: se conserva el reparto por capas. El conocimiento es lógica pura y no
sabe de red, de vista ni de archivos.

## El diseño, en detalle

### Qué sabe el jugador, y cómo se guarda

| Dato | Estructura | Por qué |
|---|---|---|
| Salas exploradas | `TablaHashImpl` id_sala → sala conocida | pertenencia y consulta en O(1); `set` está prohibido (§6.2) |
| Salas avistadas | `TablaHashImpl` id_sala → True | lo mismo; se excluye de exploradas |
| Puertas observadas | `TablaHashImpl` id_puerta → estado recordado | el estado de una puerta se consulta en cada dibujo (§5.3) |

**Lo desconocido no se almacena.** Una sala desconocida no está en ninguna de las dos tablas, así
que no cuesta memoria ni tiempo. Esa es la razón de que explorar cueste en proporción a las salas
reveladas y no al tamaño del mapa conocido (`SC-003`): revelar `k` salas son `k` inserciones,
independientemente de cuántas haya ya.

### El viaje

El buscador de 001 ya resuelve el camino. Esta capacidad aporta **la vista**: la misma interfaz
que ya consume el buscador —`contiene_sala` y `salidas_transitables`— pero respondiendo solo con
lo que el jugador conoce:

- `contiene_sala` responde verdadero solo para salas **exploradas**. Una avistada no es un paso
  intermedio válido ni un destino, que es lo acordado con 001.
- `salidas_transitables` devuelve solo las salidas que el mapa del jugador **recuerda abiertas**,
  con el costo que él conoce, y solo hacia salas exploradas.

Así, el buscador no puede observar nada fuera del conocimiento aunque quisiera: no recibe el mapa
real. `SC-005` lo comprueba con dos estados reales distintos que produzcan el mismo mapa conocido.

El viaje no guarda la ruta: pide un paso, lo ejecuta como acción ordinaria, deja correr los
eventos y vuelve a pedir el siguiente con el conocimiento ya actualizado (`FR-014`). Por eso una
puerta que resultó estar cerrada queda descartada sola, sin tratarla como un caso especial.

### Reversibilidad

Cada revelación —una sala que pasa a explorada, una avistada nueva, una puerta observada— se
registra como un cambio reversible, con el mecanismo que el proyecto ya usa. Registrar y deshacer
cuestan O(1) por revelación, que es lo que pide §5.3, y no hay copias completas del mapa, que el
Principio VII prohíbe.

### Complejidad

Con `V` salas conocidas y `E` salidas conocidas:

- Consultar el estado de una sala o de una puerta: **O(1)** promedio.
- Entrar a una sala y revelar sus vecinas: **O(salidas de esa sala)**, no O(V).
- Un paso del viaje: lo que cueste el buscador de 001 sobre el subgrafo conocido.
- Registrar o deshacer una revelación: **O(1)**.

## Riesgos y cómo se tratan

**El guardado pasa de v10 a v11.** No se pudo meter en el mismo salto que costo y rango porque v10
ya está publicada y mergeada en las tres ramas. Se avisa al grupo: si la línea de tiempo necesita
campos nuevos, que entren en este mismo salto en vez de provocar un v12.

**`controller/` y `vista/` son de Joshua.** Los comandos de ver el mapa conocido y de «ir a» son
interfaz, y §7.3 se los pide a él. Esta capacidad entrega el mapa conocido y el resultado del viaje
**como datos** desde el servicio, y él los pinta; las tareas correspondientes quedarán marcadas
como suyas, igual que se hizo en 002.

**Los cambios reversibles viven en un archivo compartido.** Para no tocarlo, los cambios propios de
esta capacidad se definen en `logica/mapa_conocido.py` heredando del contrato reversible existente.
Si eso no bastara, se acuerda con Joshua antes de modificar su archivo (Principio VIII).

**La vista actual muestra el mapa completo.** Dejar de mostrarlo es parte de la capacidad, pero
toca archivos de la vista. Se hará entregando el mapa conocido como dato y cambiando lo mínimo en
la vista, coordinándolo con Joshua.

## Lo que este plan deja fuera

- Un segundo buscador de caminos: el de 001 sirve, y duplicarlo sería inventar un problema.
- Guardar la ruta de un viaje: §3.4 exige recalcular antes de cada paso, así que una ruta guardada
  sería una respuesta que puede haber caducado.
- Revelar contenido de las salas: la antorcha revela nombre y salidas, no lo que hay dentro
  (`FR-024`), y la verificación de resolubilidad tampoco lo revela, como quedó en 002.
