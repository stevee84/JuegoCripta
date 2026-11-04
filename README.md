# CRIPTA

Juego de mazmorra por eventos con criptas descargadas de un servicio web. Proyecto de
**Estructuras de Datos II** (II Ciclo 2026), escrito en Python.

El jugador recorre una cripta sala por sala: combate enemigos, recoge y equipa objetos,
abre puertas con llaves y busca la salida. El juego no avanza por rondas: un **reloj
virtual** y una **agenda de eventos** deciden quién actúa y cuándo, de modo que la misma
cripta, la misma semilla y las mismas acciones producen siempre la misma partida.

Todas las estructuras de datos centrales (agenda, tabla hash, listas, caché, ordenamiento,
historial reversible y guardado binario) están implementadas en este repositorio, sin
usar las equivalentes de la biblioteca estándar.

## Contenido

- [Características](#características)
- [Requisitos e instalación](#requisitos-e-instalación)
- [Cómo ejecutarlo](#cómo-ejecutarlo)
- [Cómo se juega](#cómo-se-juega)
- [Arquitectura](#arquitectura)
- [Estructuras de datos propias](#estructuras-de-datos-propias)
- [Red, caché y modo offline](#red-caché-y-modo-offline)
- [Guardado, continuar y reproducción](#guardado-continuar-y-reproducción)
- [Mediciones](#mediciones)
- [Pruebas](#pruebas)
- [Archivos que genera el programa](#archivos-que-genera-el-programa)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Equipo](#equipo)

## Características

- **Simulación determinista** con reloj virtual, velocidades por actor y azar con semilla propia.
- **Tres comportamientos de enemigos**: guardián, errante y rastreador (sigue el rastro del jugador).
- **Combate, puertas con llave y cierre automático, trampas con rearme y efectos temporales**
  (veneno, regeneración, antorcha y cambio de velocidad).
- **Inventario con cursor**, equipo (un arma y una armadura) y vistas ordenadas por peso, valor o nombre.
- **Pergamino de retroceso**: deshace hasta 5 acciones del jugador sin copiar el estado de la partida.
- **Cliente HTTP con presupuesto de solicitudes**: lotes de hasta 10 elementos, reintentos ante
  HTTP 429, caché de fichas en memoria y en disco, y carga de contenido por demanda.
- **Guardar y continuar** la partida en un formato binario propio, con lectura directa de una sala.
- **Bitácora de cada partida** y reproducción con `--replay`, sin interfaz.
- **Dos vistas**: gráfica con pygame (por defecto) y de consola.
- **Modo offline** y modo de **mediciones** (`--bench`).

## Requisitos e instalación

- **Python 3.11 o superior** (desarrollado y probado con Python 3.14).
- Dependencias, en `requirements.txt`:

| Paquete | Para qué se usa |
|---|---|
| `requests` | Cliente HTTP del servicio web |
| `pygame-ce` | Vista gráfica (la vista por defecto) |
| `pytest` | Pruebas automáticas (no hace falta para jugar) |

Obtener el código y entrar a la carpeta del proyecto:

```bash
git clone https://github.com/stevee84/JuegoCripta.git
cd JuegoCripta
```

Crear el entorno virtual e instalar las dependencias:

```bash
python -m venv .venv
# Windows:      .venv\Scripts\activate
# Linux/macOS:  source .venv/bin/activate
python -m pip install -r requirements.txt
```

`pygame-ce` publica el módulo `pygame`; no lo instales junto con el paquete `pygame`.

## Cómo ejecutarlo

Ejecuta siempre los comandos **desde la carpeta del proyecto**: las carpetas de datos
(`partidas/`, `cache/`, `datos_offline/`) se resuelven relativas al directorio actual.

```bash
python main.py                       # vista gráfica contra el servicio web
python main.py --vista consola       # vista de consola
python main.py --offline             # lee las respuestas desde datos_offline/ (sin red)
python main.py --demo                # partida de demostración, sin servicio web
python main.py --replay partidas/logs/<bitacora>.log
python main.py --bench               # mediciones por subsistema, sin interfaz
```

| Opción | Descripción |
|---|---|
| `--vista {pygame,consola}` | Vista a usar. Por defecto, `pygame`. |
| `--offline` | Lee la cripta y el catálogo desde `datos_offline/` en vez del servicio web. No gasta solicitudes. |
| `--demo` | Partida sintética de dos salas con las clases reales; no necesita red ni paquete offline. |
| `--cache-size N` | Fichas del catálogo que se mantienen en memoria (por defecto, 25). |
| `--semilla N` | Semilla del azar de la partida (por defecto, 0). La misma semilla repite el mismo azar. |
| `--replay RUTA` | Reproduce una bitácora de partida sin vista ni entrada del usuario. |
| `--bench` | Ejecuta cargas sintéticas y reporta tiempos en JSON. No crea ninguna vista. |

Al iniciar con el servicio web, el juego muestra el menú de criptas publicadas y, si existe
una partida guardada, la opción **Continuar partida guardada**.

## Cómo se juega

### Vista gráfica

Se maneja con el ratón:

- **Minimapa** (arriba a la izquierda): todas las salas. La actual se marca con `@`; las limpias
  se ven claras, las que tienen cosas por hacer apagadas y las no visitadas oscuras.
- **Sala actual** (centro): jugador, enemigos con su vida, objetos del suelo, trampas y puertas.
- **Panel derecho**: vida y estadísticas, efectos activos, botones de movimiento (según las
  salidas abiertas o cerradas), acciones (atacar, recoger, esperar) y el inventario con el
  arma y la armadura equipadas. El inventario se puede ver en orden real o por peso, valor
  y nombre, sin alterar el orden real.
- **Bitácora** (abajo): los últimos 20 mensajes del juego.
- **Guardar** y **Salir**. Al salir se pregunta si se desea guardar. Al terminar la partida
  aparece el resultado con las métricas y las opciones de volver al menú o salir.

### Consola

| Comando | Efecto |
|---|---|
| `estado` | Muestra la sala, el jugador, el inventario, los efectos y los últimos 20 mensajes. |
| `mover DIRECCION`, `abrir DIRECCION` | Se mueve o abre una puerta con llave (norte, sur, este, oeste). |
| `atacar X`, `recoger X` | `X` es el número mostrado, el nombre o el identificador. |
| `esperar` | Deja pasar el tiempo. |
| `siguiente`, `anterior`, `seleccionar X` | Mueve el cursor del inventario. |
| `inventario [peso\|valor\|nombre]` | Vista ordenada del inventario. |
| `usar [X]`, `equipar`, `soltar` | Operan sobre el objeto seleccionado (o sobre `X`). |
| `retroceder [X]` | Usa un pergamino de retroceso; no consume tiempo. |
| `criptas`, `cripta ID` | Lista las criptas e inicia una partida. |
| `guardar [RUTA]`, `cargar [RUTA]` | Sin ruta usan `partidas/partida.bin`. |
| `bitacora`, `puntajes [criterio]` | Mensajes del juego y tabla de puntajes. |
| `registro RUTA`, `exportar_parcial RUTA` | Opciones técnicas. |
| `ayuda`, `salir` | Ayuda y salida. |

### Reglas principales

Las reglas completas están en [`docs/enunciado.md`](docs/enunciado.md). Un resumen:

- **Tiempo.** Tras una acción de costo `c`, el actor vuelve a actuar después de
  `max(1, c * 100 // velocidad)` unidades. Costos: mover, atacar y esperar, 100; usar, equipar
  y abrir una puerta, 50; recoger y soltar, 25. Un enemigo rápido puede actuar varias veces
  entre dos decisiones del jugador.
- **Combate.** `daño = max(1, ataque + azar.randint(0, 4) - defensa)`. Los enemigos solo
  atacan al jugador y, al morir, sueltan los objetos de su ficha.
- **Enemigos.** Si comparten sala con el jugador atacan. Si no, el guardián espera, el errante
  escoge una salida abierta al azar y el rastreador sigue la sala vecina con el rastro más
  fresco (menos de 400 unidades de antigüedad).
- **Entrada a una sala.** Las trampas armadas se activan, quedan desarmadas y se rearman
  300 unidades después. Una puerta con cierre automático se vuelve a cerrar.
- **Efectos.** Veneno (daño cada 80 unidades durante 400), regeneración de enemigos
  (cada 200), antorcha y cambio temporal de velocidad.
- **Fin de la partida.** Derrota si la vida llega a 0. Victoria al entrar a la sala de salida
  después de abrir con la llave correspondiente la puerta que lleva a ella. El resultado se
  registra en la tabla local de puntajes.

## Arquitectura

El programa sigue el patrón **Modelo–Vista–Controlador**. `main.py` solo crea las dependencias
y entrega el control al controlador.

```text
main.py ──► ControladorJuego ──► Vista (pygame o consola)
                 │
                 └──► JuegoService ──► MotorJuego + entidades (modelo)
                            │
                            ├──► InicializadorPartida · CargadorContenido
                            ├──► RepositorioCatalogo (memoria → disco → red)
                            └──► FuenteDatos: ClienteAPI  |  FuenteOffline
```

| Capa | Carpeta | Responsabilidad |
|---|---|---|
| Modelo | `dto/`, `logica/` | Entidades, reglas del juego, agenda, combate, efectos, inventario, historial reversible |
| Servicios | `service/` | Arranque de la partida, carga de contenido, catálogo de fichas, guardar y cargar |
| Datos | `datos/` | Red, archivos, decodificación del JSON, presupuesto, guardado binario, puntajes |
| Controlador | `controller/` | Traduce las acciones del usuario, coordina el flujo y la reproducción |
| Vista | `vista/` | Vista gráfica y vista de consola |
| Estructuras | `estructuras/` | Estructuras de datos propias |
| Contratos | `contratos/` | Interfaces entre capas (por ejemplo `FuenteDatos`) |

El modelo no conoce HTTP, archivos ni la interfaz. `--offline` cambia la fuente de datos
por otra que cumple el mismo contrato, sin condicionales en el modelo. `--replay` y
`--bench` se ejecutan sin crear ninguna vista.

## Estructuras de datos propias

| Estructura | Archivo | Dónde se usa |
|---|---|---|
| Montículo mínimo | `estructuras/monticulo_minimo.py` | Agenda de eventos: siguiente evento por `(tiempo, secuencia)` |
| Índice AVL | `estructuras/indice_ordenado.py` | Agenda: buscar y cancelar eventos por identificador, actor o prioridad |
| Tabla hash (encadenamiento y rehash) | `estructuras/tabla_hash.py` | Índices por identificador del catálogo, de las salas y del guardado; detección de duplicados |
| Lista doble | `estructuras/lista_doble.py` | Inventario con cursor y orden de uso de la caché |
| Cola circular | `estructuras/cola_circular.py` | Bitácora en pantalla de 20 mensajes con memoria constante |
| Caché LRU | `logica/cache_catalogo.py` | Arreglo ordenado con búsqueda binaria y lista doble; con fijación de las fichas en uso |
| Ordenador adaptativo | `logica/ordenamiento.py` | Inserción y mezcla propias; elige según el tamaño y el desorden de los datos |
| Historial reversible | `logica/historial_reversible.py` | Retroceso de hasta 5 acciones guardando solo los cambios inversos |
| Guardado binario | `datos/guardado_binario.py` | Formato propio con índice de salas ordenado y búsqueda binaria |

La caché no usa tabla hash por restricción del curso. Ninguna ruta de producción usa
`dict` ni `set` como índice, `sorted()`, `.sort()`, `heapq`, `bisect` ni `deque`; un test
(`tests/test_restricciones_enunciado.py`) lo comprueba revisando el código.

## Red, caché y modo offline

**Servicio web.** `datos/cliente_api.py` implementa los siete accesos del contrato
(`listar_criptas`, `obtener_generales`, `obtener_pagina`, `obtener_contenido`,
`obtener_catalogo`, `obtener_version_cripta`, `obtener_version_catalogo`):

- identificador de ejecución `X-Cripta-Client-Id` generado una vez por ejecución;
- tiempo de espera explícito de 10 s en cada solicitud;
- ante HTTP 429 espera el tiempo que indica el servidor y reintenta;
- cualquier fallo de red o de código HTTP se informa con la operación y la dirección,
  sin terminar el programa.

**Presupuesto.** Cada cripta declara cuántas solicitudes se permiten. El contador es
independiente en cada partida (nueva o cargada), incluye el listado de criptas y se
reporta al terminar junto con los aciertos y fallos de la caché.

**Carga por demanda.** El esqueleto de la cripta (salas y puertas) se descarga completo al
iniciar. El contenido (enemigos, objetos y trampas) llega por lotes de hasta 10 salas: si el
presupuesto alcanza con holgura se carga todo al inicio, y si no, la sala inicial con su
vecindad y el resto al moverse. Antes de confirmar un movimiento, el contenido de la sala
destino ya está disponible.

**Fichas del catálogo.** Se resuelven en tres niveles: caché en memoria, disco (`cache/catalogo/`,
válido mientras coincida la versión del catálogo) y, solo si nunca se guardó, la red. Las
entidades no conservan su ficha: la consultan en cada uso, de modo que `--cache-size`
limita la memoria realmente usada. Las fichas en uso (enemigos vivos, objetos del suelo y
trampas de la sala actual, e inventario) no se liberan.

**Modo offline.** `--offline` lee un paquete de respuestas del servicio desde `datos_offline/`:

```text
datos_offline/
├── criptas.json
├── catalogo/                 ficha por archivo + version.json
└── cripta-01/                generales.json · pagina_1.json · contenido_<ids>.json · version.json
```

Si no tienes el paquete del curso, puedes generarlo desde el servicio web:

```bash
python -m tests.fixtures.capturar_api datos_offline
```

## Guardado, continuar y reproducción

**Guardar y continuar.** `guardar` escribe `partidas/partida.bin` (formato binario propio,
versión 7) de forma segura: se valida el archivo antes de reemplazar el anterior. El menú
inicial ofrece continuar la partida; se restauran las salas, los enemigos, el inventario, la
agenda de eventos y el estado del azar. Al cargar se verifica que la versión de la cripta y
del catálogo coincidan con las del guardado. El formato guarda los textos con largo variable,
tiene un índice de salas al final y permite leer una sola sala sin leer el archivo completo.
No se guarda una partida ya terminada.

**Bitácora y reproducción.** Cada partida nueva crea su bitácora en `partidas/logs/` con la
cripta, las versiones, la semilla y cada acción del jugador. Para reproducirla sin interfaz:

```bash
python main.py --offline --replay partidas/logs/<bitacora>.log
```

Si las versiones de la bitácora ya no están disponibles, el programa informa que no puede
garantizar una reproducción fiel en lugar de continuar con datos distintos.

## Mediciones

`python main.py --bench` imprime en JSON tiempos por subsistema, con la preparación fuera del
cronómetro: agenda de eventos, búsquedas y recuperación de fichas en la caché, inventario,
historial de retroceso, ordenamientos, tabla hash, guardado y carga, y el ciclo completo de
la simulación (muy por debajo de los 20 ms exigidos). También incluye las mediciones
complementarias de `benchmarks/bench_ampliado.py`: precarga BFS (tabla hash frente a listas),
resolución del catálogo por lotes, rastreadores, retiro del inventario por posición, anexado y
validación del registro de replay, y perfiles de frecuencia (conteos de llamadas por ciclo y de
solicitudes por arranque, no tiempos). Varias mediciones incluyen la alternativa descartada.

```bash
python main.py --bench > mediciones_entrega.json
```

El **Documento de Decisiones de Diseño** (§8) está en
[`docs/decisiones_diseno.pdf`](docs/decisiones_diseno.pdf). La corrida de mediciones que usa está en
[`docs/mediciones_entrega.json`](docs/mediciones_entrega.json) (633 filas, Python 3.14.0, Windows 11).
Los resultados comentados están en:

- [`docs/comparacion_binario_json.md`](docs/comparacion_binario_json.md): guardado binario frente a JSON.
- [`docs/tabla_hash_mediciones.md`](docs/tabla_hash_mediciones.md): tabla hash frente a lista y arreglo ordenado.

Los tiempos dependen del equipo; los bytes del guardado también pueden variar unos bytes según la
biblioteca zlib de la instalación de Python (ver la nota en la comparación binario frente a JSON).

## Pruebas

```bash
python -m pytest -q
```

Más de 900 pruebas automáticas. Además de las unitarias, hay pruebas de contrato con
**respuestas reales del servicio** guardadas en `tests/fixtures/api_real/` (las cuatro
criptas publicadas): recorren cada cripta de punta a punta, guardan, cargan y continúan.
Si el servicio cambia de forma, esas pruebas fallan antes que el juego. Para volver a
capturar las respuestas:

```bash
python -m tests.fixtures.capturar_api
```

## Archivos que genera el programa

| Ruta | Contenido |
|---|---|
| `partidas/partida.bin` | Partida guardada |
| `partidas/logs/*.log` | Bitácora de cada partida, para `--replay` |
| `cache/catalogo/` | Fichas del catálogo guardadas entre sesiones |
| `puntajes.dat` | Tabla local de puntajes |

Todas se crean automáticamente, relativas al directorio desde el que se ejecuta el programa.

## Estructura del repositorio

```text
main.py               Punto de entrada
configuracion.py      Opciones de línea de comandos y rutas
PROMPTS_LLM.md        Bitácora de prompts del equipo (§10.3)
dto/                  Entidades y estado de la partida
logica/               Motor, reglas, agenda, inventario, caché, historial
service/              Arranque, carga de contenido, catálogo y guardado
datos/                Red, archivos, decodificador, presupuesto, guardado binario
controller/           Controlador del juego y reproducción
vista/                Vista gráfica (pygame) y de consola
estructuras/          Estructuras de datos propias
contratos/            Interfaces entre capas
assets/               Imágenes de la vista gráfica
benchmarks/           Mediciones para --bench
tests/                Pruebas automáticas y respuestas reales del servicio
stubs/                Dobles de prueba usados por los tests
docs/                 Enunciado, Documento de Decisiones y resultados de las mediciones
```

## Equipo

| Integrante | Bloque |
|---|---|
| Sofía Delgado | Simulación y reglas: entidades, agenda de eventos, motor, combate, enemigos y efectos |
| Steven Moya Porras | Datos y persistencia: cliente HTTP, presupuesto, catálogo y caché, modo offline, guardado binario |
| Joshua Cabrera Bonilla | Interacción: inventario, historial reversible, controlador y vistas |
