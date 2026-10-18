# PROMPTS_LLM

Bitácora de prompts del equipo (§10.3 del enunciado) del proyecto CRIPTA: Steven (Integrante 2), Sofía Delgado (Integrante 1) y Joshua (Integrante 3).

---

# Steven — Integrante 2: Datos y Persistencia

Bitácora de prompts (§10.3) de Steven. Este trabajo se hizo como una conversación continua con Claude: yo planteaba el problema o la decisión, Claude proponía y escribía el código, y juntos revisábamos qué fallaba y qué había que corregir antes de seguir, validando siempre contra el API real y el enunciado. Los Prompts 1 y 2 son la planificación inicial del proyecto; los Prompts 3 a 10 recogen el trabajo posterior con Claude Code. Cada entrada indica la herramienta, el prompt, qué se obtuvo y qué hubo que corregir.

| # | Tema | Fecha |
| --- | --- | --- |
| 1 | Reparto del trabajo en tres bloques independientes | 21/09/2026 |
| 2 | Plan consolidado del Integrante 2: Datos y Persistencia | 21/09/2026 |
| 3 | Arquitectura MVC: un solo main y pygame por defecto | 12/10/2026 |
| 4 | Vista pygame: botones, mapa, sala actual e inventario | 12/10/2026–13/10/2026 |
| 5 | Datos: fichas en uso, índice ordenado y métricas (§4.4, §4.9, §5.1) | 12/10/2026–13/10/2026 |
| 6 | Salir, guardar y continuar la partida (§10.2, §4.10) | 13/10/2026–16/10/2026 |
| 7 | Validar con el API real: criptas, errores y contratos | 13/10/2026–14/10/2026 |
| 8 | Un agente juega la cripta de verdad contra el API | 14/10/2026 y 16/10/2026 |
| 9 | Cumplir el enunciado: restricciones y mediciones | 14/10/2026–16/10/2026 |
| 10 | Carga gradual de la cripta y fichas sin retención (§4.2, §4.4, §9) | 17/10/2026 |

## Prompt 1 — Reparto del trabajo en tres bloques independientes

**Herramienta:** asistente LLM (planificación)

### Integrante 1 — sin depender de nadie

- Entidades: Actor, Jugador, Enemigo, Sala, Puerta, Trampa, ObjetoInstancia, EstadoPartida
- MonticuloMinimo: es 100% suyo, estructura propia con sus pruebas
- AgendaEventos: puede usar un dict temporal como índice hasta que llegue la TablaHash del 2 (mismo contrato: insertar, obtener, eliminar, contiene)
- RegistroRastro: lógica de frescura, sin dependencias externas
- ReglasCombate, ComportamientoEnemigos, GestorEfectos: toda la lógica de simulación
- MotorJuego: validar y ejecutar acciones — puede crear salas y enemigos "a mano" en tests, sin necesitar la API

*Lo que queda bloqueado hasta integrar: datos reales de la API (usa datos inventados) y la TablaHash real.*

### Integrante 2 — sin depender de nadie

- TablaHash: 100% suya, estructura propia con pruebas
- ClienteAPI y FuenteOffline: todo el acceso a red/archivos
- DecodificadorDatos: convertir JSON a entidades (puede definir entidades simples temporales o usar las del contrato acordado)
- PresupuestoSolicitudes: conteo y límites
- PlanificadorPrecarga: lotes, estados pendiente/disponible/fallido
- CacheCatalogo con política LRU: puede usar una lista doble temporal propia hasta que llegue la del 3 (mismo contrato: insertar, quitar_nodo, mover_al_frente)
- GuardadoBinario: formato, cabecera, índice — puede serializar datos de prueba inventados
- AlmacenPersistente: lectura/escritura de fichas en disco

*Lo que queda bloqueado hasta integrar: la ListaDoble real del 3 y la representación del estado real de los módulos del 1 y 3.*

### Integrante 3 — sin depender de nadie

- ListaDoble y NodoDoble: 100% suyas, estructura propia
- ColaCircular / BúferCircular: 100% suya
- Inventario y ServicioInventario: toda la lógica de cursor, recoger, soltar, equipar — puede crear objetos ficticios
- BitacoraPantalla: búfer circular de 20, completamente independiente
- OrdenadorAdaptativo: insertion sort y merge sort propios, benchmarks comparativos — no depende de nadie
- CambioReversible, TransaccionAccion, HistorialReversible: el framework de retroceso completo (las operaciones inversas de prueba las escribe él; las reales las aporta cada dueño después)
- VistaConsola: input/output por consola
- RegistroPartida: log append-only
- RepositorioPuntajes: tabla local

*Lo que queda bloqueado hasta integrar: el MotorJuego real del 1 y los datos reales del 2 para el ControladorJuego y el Replay.*

### Receta práctica

- Día 1 juntos (30-60 min): acordar las firmas de Accion, ResultadoAccion, FuenteDatos, CambioReversible, TablaHash y ListaDoble. Escribirlas como clases/protocolos vacíos en archivos compartidos.
- Cada uno trabaja solo usando stubs: el 1 usa un dict como hash, el 2 usa una lista doble simple, y el 3 usa un motor que siempre aprueba acciones.
- Primer merge: cuando las estructuras propias estén listas (TablaHash, ListaDoble, Montículo) — se reemplazan los stubs por las reales.
- Segundo merge: primera partida jugable de extremo a extremo (hito 3 del plan).

Así cada uno puede avanzar semanas sin esperar a los otros, y los merges son solo "conectar piezas" que ya funcionan por separado.

La clave está en definir los contratos (interfaces/clases abstractas) juntos al inicio, y luego cada uno trabaja con dobles de prueba (mocks/stubs) del resto.

Pendiente mañana Día 1 juntos (30-60 min): acordar las firmas de Accion, ResultadoAccion, FuenteDatos, CambioReversible, TablaHash y ListaDoble. Escribirlas como clases/protocolos vacíos en archivos compartidos. En este caso estamos bajo el contexto de que somos estudiantes de estructuras de datos en nuestro tercer año de ingeniería, queremos planear como tal lo que sería nuestra base de nuestro proyecto para poder cada uno continuar en nuestras ramas respectivas, ahí viene respectivamente que hace cada uno de los estudiantes de forma independiente. El programa llevará el modelo MVC, con service -> modelo -> controller -> view, controller teniendo una instancia del view y del modelo, el modelo tiene un wrapper del service. Quiero planear poco a poco esto, hazme preguntas, solo quiero dejar la base hecha para comenzar a crear las ramas.

**Respuestas a las preguntas de aclaración:**

1. Lenguaje/stack: Python puro + consola. El proyecto llevará específicos de JSON en el futuro porque usará una API para la info, pero de eso se encarga el Integrante 2 más adelante.
2. Mapeo MVC: Confirmado — Model = MotorJuego + entidades + lógica de simulación (Integrante 1, envuelve al Service); Service = ClienteAPI/FuenteOffline/Cache/Persistencia (Integrante 2); View = VistaConsola (Integrante 3); Controller = ControladorJuego nuevo, orquesta Model + View.
3. Estilo de contratos: ABC con @abstractmethod.
4. Git/ramas: Solo dejar la estructura de archivos, sin tocar git (ni git init ni ramas — eso lo hace el equipo).
5. Testing: pytest.
6. Stubs: Sí, escribir ya los 3 dobles temporales de la receta (dict-como-hash, lista-simple, motor-que-siempre-aprueba) en una carpeta stubs/.
7. Ubicación de Inventario/ServicioInventario: Dentro de model/, porque es lógica de juego (no la capa Service, a pesar del nombre).
8. Ubicación de RegistroPartida/RepositorioPuntajes: Carpeta propia persistencia/, separada de service/ (que es solo del Integrante 2).

## Prompt 2 — Plan consolidado del Integrante 2: Datos y Persistencia

**Herramienta:** asistente LLM (planificación)

CRIPTA es un juego roguelike de mazmorra en Python 3.11+, proyecto de Estructuras de Datos II Ciclo 2026. Equipo de 3 integrantes, arquitectura MVC con capas: dto/, logica/, datos/, service/, controller/, vista/, estructuras/, contratos/. Soy el Integrante 2 (Steve). Mi bloque es Datos y Persistencia: todo lo que entra y sale del programa — red, archivos, caché, guardado.

### TablaHash — estructuras/tabla_hash.py

Mi estructura evaluada. La implemento yo, la usan otros.

- Tipo: encadenamiento (chaining) — cada bucket es una lista de pares (clave, valor)
- Función hash: hash(clave) % capacidad
- Capacidad inicial: número primo (ej. 17)
- Rehashing: cuando factor de carga > 0.75, duplicar capacidad y reinsertar todo
- Operaciones: insertar, obtener, eliminar, contiene — O(1) amortizado
- Métodos extra necesarios: len, iter, claves() para uso interno
- Quién la usa: Integrante 1: agenda de eventos (buscar/cancelar eventos por ID), mapa de salas (buscar sala por ID)
- NO se usa en mi caché (restricción del profesor)

### Caché LRU — service/cache_catalogo.py

(actualmente en logica/) Política LRU (Least Recently Used) sin TablaHash. Usa arreglo ordenado + ListaDoble.

- Arreglo ordenado: pares (clave, nodo) ordenados alfabéticamente por clave. Búsqueda binaria O(log n). Insertar/eliminar O(n) por desplazamiento.
- ListaDoble (del Integrante 3): orden de uso. Frente = más reciente, cola = más viejo.
- Capacidad: configurable con --cache-size (default 25)

**Operaciones:**

- obtener(ficha_id): búsqueda binaria en arreglo → nodo → mover_al_frente en ListaDoble → retornar valor
- insertar(ficha_id, ficha): si lleno → desalojar cola (el más viejo no fijado) → insertar en arreglo (mantener orden) + ListaDoble (al frente)
- fijar(ficha_id): proteger ficha — no se desaloja aunque sea la más vieja (ficha en uso activo)
- liberar_referencia(ficha_id): quitar protección, puede ser desalojada
- Contadores: aciertos y fallos para métricas
- Justificación: con 25 elementos, O(log 25) ≈ 5 comparaciones, diferencia con O(1) es irrelevante. El cuello de botella es la red (400ms), no el caché (microsegundos).

### Precarga adaptativa — service/planificador_precarga.py

Decide qué salas precargar según tamaño de cripta y presupuesto restante.

**Estrategia según tamaño:**

- Criptas chicas (≤20 salas): cargar TODO el contenido de una vez (2 lotes)
- Criptas medianas (≤50): profundidad 2 desde jugador (20 salas)
- Criptas grandes (50+): profundidad 1, conservar presupuesto

**Adaptación por presupuesto:**

- Restantes > 5: precarga agresiva (profundidad 2)
- Restantes 2-5: precarga moderada (profundidad 1 completa)
- Restantes < 2: solo la sala destino del movimiento
- Lotes: hasta 10 salas por solicitud de obtener_contenido
- Al moverse: solo pedir las salas del nuevo borde, no recalcular todo
- Puertas cerradas: precargar solo profundidad 1 detrás de puertas cerradas
- Siempre consultar caché/disco antes de pedir — filtrar pendientes contra lo que ya tenemos

### Repositorio catálogo — service/repositorio_catalogo.py

Tres niveles de búsqueda para fichas del catálogo:

- Memoria (caché LRU) → SÍ → retornar
- Disco (almacén persistente) → SÍ → ¿versión vigente? → SÍ → cargar al caché, retornar → NO → descartar, ir a red
- Red (API) → obtener → guardar en disco + caché → retornar
- resolver(ficha_id): busca en los 3 niveles
- resolver_lote(ids): filtra los que ya tiene, pide solo los faltantes en un lote Las fichas se acumulan entre sesiones — cada partida nueva gasta menos solicitudes Primera partida: máximo gasto. Quinta partida: la mayoría ya está en disco.

### Cliente API — datos/cliente_api.py

Comunicación HTTP con el servidor de CRIPTA.

- Header obligatorio: X-Cripta-Client-Id generado con uuid.uuid4() una vez por ejecución
- Timeout: 10 segundos explícito en cada solicitud
- Biblioteca: requests
- 7 métodos del contrato FuenteDatos: listar_criptas, obtener_generales, obtener_pagina, obtener_contenido (hasta 10 sala_ids), obtener_catalogo (hasta 10 ids), obtener_version_cripta, obtener_version_catalogo

**Manejo de errores completo:**

- 200 OK: Procesar JSON. ¿Cuenta como solicitud? Sí
- 429 Too Many Requests: Esperar reintentar_en segundos (tope 30s), reintentar (máx 3 veces). ¿Cuenta como solicitud? Sí (cada una)
- Timeout: Reportar con contexto, marcar fallido. ¿Cuenta como solicitud? Sí
- Sin conexión: Reportar, sugerir --offline. ¿Cuenta como solicitud? No
- 404/500/otro: Reportar código + operación que falló. ¿Cuenta como solicitud? Sí
- JSON inválido: Reportar, tratar como error. ¿Cuenta como solicitud? Sí
- Sin presupuesto: No pedir, usar caché/disco. ¿Cuenta como solicitud? No
- 200 incompleto: Procesar lo que vino, repedir faltantes. ¿Cuenta como solicitud? Sí
- Datos no solicitados en respuesta: Ignorar extras.
- Conexión cortada a medio camino: Tratar como error de red. ¿Cuenta como solicitud? Sí
- Versión de cripta/catálogo cambió: Validar, recargar si difiere. ¿Cuenta como solicitud? Sí (extra)
- Presupuesto agotado a medio lote: Priorizar por cercanía al jugador.
- Error de disco al guardar: Seguir solo en memoria.
- Datos corruptos en disco: Descartar, ir a la red.
- Regla: el juego NUNCA se cae por un error de red. Siempre reportar con contexto.
- Reintentos 429 cuentan como solicitudes — un 429 cuesta doble presupuesto.

### Guardado binario — datos/guardado_binario.py

Formato binario propio para guardar/cargar partidas con acceso directo a salas.

**Estructura del archivo: CABECERA (tamaño fijo):**

- "CRPT" (4 bytes, firma mágica)
- versión formato (2 bytes)
- id cripta (32 bytes)
- semilla (8 bytes)
- reloj actual (4 bytes)
- cantidad salas (4 bytes)
- offset al índice (4 bytes)

**offset datos jugador (4 bytes) DATOS DEL JUGADOR:**

- id, nombre, vida, vida_max, ataque, defensa, velocidad
- sala actual (id)

**inventario, efectos activos SALAS (tamaño variable cada una):**

- id_sala (32 bytes)
- cantidades: puertas, enemigos, objetos, trampas (2 bytes cada una)
- N puertas serializadas (101 bytes c/u)
- N enemigos serializados (101 bytes c/u)
- N objetos serializados

**N trampas serializadas (69 bytes c/u) ÍNDICE DE SALAS (al final):**

- [(id_sala, offset_en_archivo), ...] para acceso directo
- Índice al final porque no se sabe el tamaño de cada sala hasta escribirla
- Módulo Python: struct para pack/unpack de bytes

**3 operaciones:**

- guardar(ruta, estado): cabecera + jugador + salas + índice
- cargar(ruta): leer todo, reconstruir estado
- leer_sala(ruta, id_sala): leer cabecera → saltar al índice → buscar offset → leer solo esa sala
- Validación: firma "CRPT", versión compatible, offsets dentro del archivo. Nunca crashear por archivo corrupto.

### Almacén persistente — datos/almacen_persistente.py

Fichas del catálogo guardadas en disco entre sesiones. Formato JSON (mismo que devuelve el API). datos_locales/catalogo/ ├── version.txt ├── espada_oxidada.json ├── pocion_vida.json └── esqueleto_guardian.json

- guardar(ficha_id, ficha, version): escribir JSON + versión en disco
- leer(ficha_id): leer JSON del disco o None si no existe
- validar_version(ficha_id, version): comparar versión guardada con la actual
- JSON porque: el API ya lo da en JSON, guardarlo tal cual evita conversiones innecesarias. El decodificador procesa lo mismo sin importar si vino de red o disco.
- Errores: disco lleno → seguir en memoria. JSON corrupto → descartar, ir a red.

### Decodificador de datos — datos/decodificador_datos.py

Convierte JSON crudo (del API o disco) en objetos Python del juego.

- convertir_sala(datos): JSON → objeto Sala con Puertas
- convertir_contenido(datos): JSON → enemigos, objetos, trampas por sala
- convertir_ficha(datos): JSON → ficha del catálogo tipada
- Único punto de conversión: si el API cambia formato, solo se toca este archivo
- Mismo decodificador para datos de red y datos de disco

### Fuente offline — datos/fuente_offline.py

Mismo contrato FuenteDatos pero leyendo archivos locales en vez de HTTP. datos_offline/ ├── criptas.json ├── cripta_01/ │ ├── generales.json │ ├── pagina_1.json │ ├── contenido.json │ └── version.txt ├── catalogo/ │ ├── {ficha_id}.json │ └── version.txt

- Cada método del contrato lee su archivo correspondiente
- Se activa con --offline en main.py
- Cero solicitudes HTTP, cero presupuesto gastado
- Para desarrollo sin internet, tests deterministas y evaluación

### Archivos de mi responsabilidad

| Archivo | Qué hace |
| --- | --- |
| estructuras/tabla_hash.py | Tabla hash propia (estructura evaluada) |
| datos/cliente_api.py | HTTP con headers, timeout, errores |
| datos/fuente_offline.py | Mismo contrato desde archivos locales |
| datos/decodificador_datos.py | JSON a objetos Python |
| datos/presupuesto_solicitudes.py | Conteo de solicitudes y límite |
| datos/almacen_persistente.py | Fichas JSON en disco entre sesiones |
| datos/guardado_binario.py | Formato binario para partidas |
| service/repositorio_catalogo.py | memoria → disco → red |
| service/planificador_precarga.py | Lotes, estrategia adaptativa |
| service/cache_catalogo.py | LRU con arreglo ordenado + ListaDoble |

### Stub que uso

- stubs/lista_doble_simple.py — lista Python como ListaDoble hasta que Integrante 3 entregue la real

### Correcciones posteriores sobre este plan

- Error 429: el plan ponía un tope de 30 s a la espera; ahora se espera exactamente lo que indica reintentar_en, y cualquier excepción de requests termina como un error con la operación y la URL (§3.1).
- Guardado binario: el plan reservaba 32 bytes por ID; ahora los textos son de largo variable (v6) y cada sala marca si su contenido ya se cargó (v7). El índice sigue al final, ordenado con el OrdenadorAdaptativo propio y buscado con búsqueda binaria.
- Precarga: el PlanificadorPrecarga (profundidad según tamaño y presupuesto) nunca llegó a conectarse al juego; lo reemplazó CargadorContenido, integrado a MOVER y al guardado.
- Repositorio: devuelve {"entidades": [...]} igual que el API, registra el origen (disco o red) para las métricas y no esconde los errores de red cuando no hay una copia en disco.
- Caché: se mantuvo el arreglo ordenado con ListaDoble, pero se agregaron fijación por dueño, métricas por partida y fichas “vivas” (las entidades ya no retienen su ficha, así --cache-size limita la memoria real). Sin dict ni set (§7).
- Almacén persistente: la carpeta pasó de datos_locales/catalogo a cache/catalogo, separada de los guardados.
- Fuente offline: el plan suponía contenido.json y version.txt; los datos reales usan contenido_<ids>.json y version.json (se aceptan ambos formatos), con un error claro si falta un archivo; la carpeta por defecto es datos_offline/.
- TablaHash: además de la agenda y el mapa, se usa en los índices de datos (catálogo por id, salas por id, detección de duplicados); nunca en el caché.
- Presupuesto: ahora es por partida (nueva o cargada) y el modo offline reporta 0 solicitudes contra el presupuesto declarado por la cripta.

## Prompt 3 — Arquitectura MVC: un solo main y pygame por defecto

**Herramienta:** Claude Code (Claude Opus 4.6)

> Prompt “Solamente que el main llame al controlador y el controlador llame a la vista, como debería de ser… Quiero que sea un main limpio, hay demasiadas cosas aquí; y el juego correrá solo en vista [pygame]. Pruébalo con pygame.”

**Qué se obtuvo.** main.py quedó como único punto de entrada: crea la fuente de datos, la vista y el controlador, y delega todo el flujo en el controlador (main_pygame.py se eliminó). --vista pygame es el valor por defecto y --vista consola se reserva para pruebas y replay.

**Correcciones sobre la marcha**

- Los tests que lanzaban main.py como subproceso se quedaban esperando una ventana: se les agregó --vista consola.
- Algunos objetos de configuración de prueba no tenían el campo vista: se agregó al argparse y a los fixtures.
- El menú de criptas mostraba “?” cuando el API no traía salas o dificultad: ahora omite esos campos.

## Prompt 4 — Vista pygame: botones, mapa, sala actual e inventario

**Herramienta:** Claude Code (Claude Opus 4.6)

> Prompt “¿Cómo vamos a navegar el inventario?… Dejemos los botones de forma uniforme y ordenada, ahorita cambian de lugar y tamaño según lo que haya en pantalla… ¿Cómo manejaremos el mapa con 20 salas?… Hay un overlapping con los botones y el texto.” Luego, con la idea de mis compañeros: “un pequeño mapa en la esquina superior izquierda y en grande solo la sala actual; si la sala quedó limpia que se vea clara, con cosas por hacer opaca o gris, y si no se ha visitado oscura. Enfoquémonos en cambiar la vista y no la lógica.”

**Qué se obtuvo.** Botones con medidas y posiciones uniformes, inventario navegable, minimapa con tres estados de color y vista grande de la sala actual con sus entidades y puertas.

**Correcciones sobre la marcha**

- Los botones se calculaban antes de dibujar el panel y quedaban encima del texto: se invirtió el orden de dibujo y la altura del panel se mide en cada cuadro.
- Con criptas grandes el mapa se salía de la pantalla: primero se centró en el jugador y luego se reemplazó por el minimapa.
- Más tarde: “con el inventario realmente uno no sabe qué tiene en la mano, qué tiene equipado ni qué va a usar”. Se rehízo con un bloque fijo de arma y armadura equipadas, la lista con nombre y efecto reales de cada objeto, selección por clic y botones según la clase (Equipar, Usar, Retroceder, Soltar).

## Prompt 5 — Datos: fichas en uso, índice ordenado y métricas (§4.4, §4.9, §5.1)

**Herramienta:** Claude Code (Claude Opus 4.6)

> Prompt “Veamos lo mío; lo de medición todavía no, quiero que el código como está esté listo.” Pendientes: no desalojar del caché las fichas en uso (§4.4), índice de salas ordenado con búsqueda binaria en el guardado (§4.9) y métricas de caché al terminar la partida (§5.1).

**Qué se obtuvo.** CacheCatalogo.fijar y liberar_referencia, índice del guardado ordenado por sala con búsqueda binaria en leer_sala, y metricas() reportadas al final de la partida.

**Correcciones sobre la marcha**

- Al reiniciar la partida quedaban fichas fijadas de la anterior y fallaron dos tests: se liberan al iniciar.
- Más tarde se vio que el inventario y la sala se pisaban las fijaciones (si uno liberaba, el otro perdía la protección): la fijación pasó a llevar dueño.
- Al contrastar con el enunciado, §4.4 se ajustó a su definición de “ficha en uso”: enemigos vivos, objetos del suelo y trampas de la sala actual, e inventario.

## Prompt 6 — Salir, guardar y continuar la partida (§10.2, §4.10)

**Herramienta:** Claude Code (Claude Opus 4.6 y Opus 5.5)

> Prompt “¿Cuál es la lógica de salida y guardado?” → “Un mensaje de ¿está seguro de salir? o ¿desea guardar antes?, y que al salir se cierre la vista.” Más tarde: “cuando perdemos la partida solo tira las métricas y ya, no hay ningún mensaje; las métricas no las cierra el usuario, se cierran solas y además cierra el programa completo.” Y: “cuando guardo la partida, ¿qué ocurre?, ¿cuando continúo en la misma mazmorra sigue ahí? Respóndeme acorde a las especificaciones del profe.”

**Qué se obtuvo.** Diálogo de salida (guardar y salir, salir sin guardar, cancelar); pantalla final con el resultado (derrota, victoria, guardada o abandonada), las métricas y los botones “Volver al menú” y “Salir del juego”; guardar y cargar sin argumento usan partidas/partida.bin y el menú inicial ofrece “Continuar partida guardada”; no se guarda una partida terminada.

**Correcciones sobre la marcha**

- La primera versión cerraba la ventana sola y terminaba el programa: se reemplazó por la pantalla final con regreso al menú.
- Al continuar una partida cargada el presupuesto quedaba sin límite (“7/0”) y las fichas se pedían a la red aunque ya estaban en disco: cargar ahora aplica el presupuesto de la cripta y resuelve memoria → disco → red.
- “Guardar y salir” cerraba el juego aunque el guardado fallara: ahora solo sale si se guardó.

## Prompt 7 — Validar con el API real: criptas, errores y contratos

**Herramienta:** Claude Code (Claude Opus 5.5)

> Prompt “Hagamos merge con la rama de Sofía y veamos qué fue lo que ella arregló; ya hay más de un tipo de sala en el API. Quiero que veas qué del código que hicimos falló y trabajemos en cubrir que no vuelva a pasar. Quiero mi código limpio y evitar que sigamos encontrando tantos errores.”

**Qué se obtuvo.** Se descargaron las 4 criptas publicadas (6, 20, 40 y 50 salas) y se pasaron por el flujo completo (inicializar, jugar, guardar, cargar). Quedaron como fixtures reales en tests/fixtures/api_real, con tests de contrato que fallan si el API cambia de forma.

**Correcciones sobre la marcha**

- --offline buscaba la carpeta datos/ (el código) en vez de datos_offline/ y, si faltaba un archivo, devolvía un resultado vacío sin avisar: ahora lee el formato real del API y falla diciendo qué archivo falta.
- cargar pedía las 11 fichas en una sola solicitud y el API acepta como máximo 10 (HTTP 400): ahora va en lotes de 10, y la fuente offline aplica el mismo límite.
- El controlador no atrapaba los errores de red y un fallo cerraba el juego.
- Causa de fondo: los tests usaban JSON inventados con la forma que suponíamos. Por eso había 791 tests en verde y aun así fallaba al jugar.

## Prompt 8 — Un agente juega la cripta de verdad contra el API

**Herramienta:** Claude Code (Claude Opus 5.5)

> Prompt “Antes de hacer push, pon un agente a jugar de verdad el juego, no en test, con el API y demás; que juegue una cripta con una cantidad media de salas y preséntame sus opiniones y observaciones.” Segunda vuelta, ya integrado lo de Sofía y Joshua: “pongamos al mismo agente a jugar a ver si encuentra nuevos errores.”

**Qué se obtuvo.** Un subagente jugó por consola la cripta-03 (40 salas) contra el API real. En la primera ronda no llegó a la salida; en la segunda ganó 3 de 5 semillas y una partida guardada, cargada en otro proceso y terminada.

**Correcciones sobre la marcha**

- Pociones inutilizables: el adaptador de fichas buscaba el campo curacion y el API manda cura.
- Cargar en un proceso nuevo fallaba con HTTP 400 (más de 10 ids por solicitud).
- Falsos errores descartados con el enunciado: las ratas de velocidad 150 atacan más de una vez por acción del jugador (§2.3 y §2.13), las puertas con cierre automático se cierran solas (§2.5) y las trampas se rearman a las 300 unidades (§2.10).
- Los problemas de presentación (mensajes internos en consola, numeración de enemigos, últimos 20 mensajes, estado con inventario) se pasaron a Joshua y quedaron resueltos en su rama.

## Prompt 9 — Cumplir el enunciado: restricciones y mediciones

**Herramienta:** Claude Code (Claude Opus 5.5)

> Prompt Con el enunciado adjunto: “¿Las ratas son así porque lo pide el documento o por la lógica a la que llegó Sofía?”, “¿el enunciado habla de regeneración y veneno?” y, sobre el documento de incumplimientos de Sofía: “arreglemos todo lo que sea de nosotros”. Con un reparo: “¿por qué pasamos a una tabla hash? tenía entendido que no podíamos usar esto.”

**Qué se obtuvo.** Se contrastó cada punto del enunciado con el código. Veneno y regeneración: el Swagger del API no declara ningún campo para ellos (enemigos y trampas son esquemas cerrados), así que las 4 criptas no los traen; el motor ya aplica la regeneración si la ficha trae “regeneracion” y el veneno está implementado pero sin disparador.

**Correcciones sobre la marcha**

- El enunciado prohíbe el dict de Python como índice (§7), no las tablas hash propias; la restricción de no usar tabla hash aplica solo al caché. Los índices de datos pasaron del dict a TablaHashImpl.
- Joshua detectó que el caché usaba un dict para las fichas fijadas: se cambió por un arreglo ordenado con búsqueda binaria.
- El índice del guardado usaba list.sort() (prohibido en §4.9): ahora usa el OrdenadorAdaptativo propio. Un test revisa con AST que no vuelvan sorted, sort, set, heapq, bisect ni deque.
- Errores de red con contexto y 429 que respeta reintentar_en (§3.1); el repositorio ya no oculta errores.
- Presupuesto y métricas de caché por partida, y modo offline que reporta 0 solicitudes contra el presupuesto de la cripta (§5.1).
- --bench mide caché, recuperación de fichas liberadas, TablaHashImpl y guardado/carga contra JSON, con resultados reproducibles y documentados (§5.3, §4.10).
- IDs de más de 32 bytes no podían guardarse: formato v6 con textos de largo variable.
- El enunciado.pdf del repositorio estaba dañado: se reemplazó por enunciado.md.

## Prompt 10 — Carga gradual de la cripta y fichas sin retención (§4.2, §4.4, §9)

**Herramienta:** Claude Code (Claude Opus 5.5)

> Prompt “Veamos lo de Sofía y lo mío: explícame qué falla de cada lado, la forma de resolverlo y veamos si es posible resolverlo todo aquí.” Después: “vamos a separarlo en partes para que cada uno arregle lo propio; dame un mensaje bien específico para Sofía y yo me encargo de lo que cubre lo mío.”

**Qué se obtuvo.** El problema común era que el arranque descargaba toda la cripta y cada entidad retenía su ficha. Se acordó un contrato en Sala (contenido_cargado e incorporar_contenido) y se repartió el trabajo: carga gradual, fichas y guardado para Steve; validación en MOVER, historial y rastreadores para Sofía.

**Correcciones sobre la marcha**

- CargadorContenido: esqueleto completo al inicio y contenido por lotes de 10 salas; si el presupuesto alcanza con holgura se carga todo (las 4 criptas reales), si no, la sala inicial con su vecindad y el resto al moverse. Una cripta de prueba de 21 salas con presupuesto 8 se juega completa.
- CatalogoVivo: las entidades ya no guardan su ficha, la leen del caché (o del disco) en cada uso; --cache-size limita de verdad la memoria (§4.4).
- Guardado v7: marca qué salas faltan por cargar para seguir cargándolas al continuar.
- Se quitaron 2 solicitudes de versión repetidas al iniciar y al cargar, y se eliminó PlanificadorPrecarga, que quedó reemplazado.
- Ajuste obligado: el caché y el catálogo vivo se excluyen del estado serializado, porque el retroceso no debe incluirlos (§2.11).

## Resultado

976 pruebas automáticas pasan. El juego se juega completo contra el API real y en modo offline: las 4 criptas publicadas cargan con entre 5 y 8 solicitudes de presupuestos que van de 9 a 52; se guarda y se continúa la partida; y --bench mide caché, tabla hash, guardado y carga con resultados reproducibles.

---

# Sofía Delgado — Integrante 1: Motor del juego y simulación

Bitácora de prompts (§10.3) de Sofía, ordenada por tema. Cada entrada incluye el prompt, qué se construyó y por qué, y el costo de la solución. Las fechas están en la tabla.

| # | Prompt | Tema | Fecha |
| --- | --- | --- | --- |
| 1 | Análisis de estructura de datos para el sistema de eventos | Tema 1. Estructuras de datos y agenda de eventos | 30/09/2026 |
| 2 | Diseño e implementación de un Montículo Mínimo propio | Tema 1. Estructuras de datos y agenda de eventos | 30/09/2026 |
| 3 | Diseño de la entidad Evento y pruebas unitarias | Tema 1. Estructuras de datos y agenda de eventos | 01/10/2026 |
| 4 | Diseño de una Agenda de Eventos utilizando estructuras propias | Tema 1. Estructuras de datos y agenda de eventos | 01/10/2026 |
| 5 | Análisis de cancelación y reprogramación de eventos | Tema 1. Estructuras de datos y agenda de eventos | 01/10/2026 |
| 6 | Revisión y simplificación de Agenda de Eventos | Tema 1. Estructuras de datos y agenda de eventos | 02/10/2026 |
| 7 | Diseño de entidades principales del estado del juego | Tema 2. Entidades, mapa y comportamiento de enemigos | 02/10/2026 |
| 8 | Diseño del mapa de la cripta como grafo | Tema 2. Entidades, mapa y comportamiento de enemigos | 03/10/2026 |
| 9 | Diseño de sistema de rastros y comportamiento de enemigos | Tema 2. Entidades, mapa y comportamiento de enemigos | 03/10/2026 |
| 10 | Diseño e integración del gestor de efectos temporales | Tema 3. Efectos, motor y combate | 04/10/2026 |
| 11 | Diseño e integración del Motor del Juego | Tema 3. Efectos, motor y combate | 04/10/2026 |
| 12 | Diseño de reglas de combate y procesamiento de eventos | Tema 3. Efectos, motor y combate | 04/10/2026 |
| 13 | Equipamiento | Tema 4. Equipamiento, reversión e integración | 09/10/2026 |
| 14 | Soltar equipo | Tema 4. Equipamiento, reversión e integración | 09/10/2026 |
| 15 | Servicio compartido | Tema 4. Equipamiento, reversión e integración | 10/10/2026 |
| 16 | Condición de victoria | Tema 4. Equipamiento, reversión e integración | 11/10/2026 |
| 17 | Pruebas de regresión | Tema 4. Equipamiento, reversión e integración | 11/10/2026 |
| 18 | Rendimiento | Tema 5. Medición inicial de rendimiento | 12/10/2026 |
| 19 | Sprites del jugador y la rata gigante | Tema 6. Imágenes de personajes y objetos | 13/10/2026 |
| 20 | Imágenes de objetos, trampas y enemigos | Tema 6. Imágenes de personajes y objetos | 13/10/2026 |
| 21 | Fondo del menú inicial | Tema 7. Fondos de la interfaz | 14/10/2026 |
| 22 | Fondo de la sala actual | Tema 7. Fondos de la interfaz | 14/10/2026 |
| 23 | Benchmark de ciclos con las cuatro criptas | Tema 8. Rendimiento con datos reales | 14/10/2026 |
| 24 | Correcciones de la vista después del merge | Tema 9. Revisión de conflictos e integración de ramas | 14/10/2026 |
| 25 | Verificación del menú, imágenes y diferencias con Steve | Tema 9. Revisión de conflictos e integración de ramas | 14/10/2026 |
| 26 | Regresión de ratas y trampa con semilla 3 | Tema 10. Reglas del motor y avisos al jugador | 14/10/2026 |
| 27 | Avisos automáticos y campo de curación | Tema 10. Reglas del motor y avisos al jugador | 15/10/2026 |
| 28 | Sprite del guardián muerto | Tema 11. Presentación del guardián derrotado | 16/10/2026 |

### Tema 1. Estructuras de datos y agenda de eventos

## Prompt 1 — Análisis de estructura de datos para el sistema de eventos

> **Prompt**
>
> Estoy desarrollando un sistema de simulación basado en eventos para un juego en Python. La simulación requiere administrar eventos futuros ordenados por tiempo de ejecución y resolver empates mediante un criterio determinista.
>
> Analiza qué estructura de datos sería más adecuada para administrar estos eventos considerando eficiencia, restricciones académicas y la necesidad de implementar la estructura manualmente sin utilizar librerías externas.
>
> Explica la justificación de la estructura seleccionada, sus operaciones principales, complejidades y cómo debería integrarse dentro de una arquitectura separada por capas.

**Qué se construyó y por qué.** Se eligió un montículo mínimo propio como estructura de la agenda: siempre hace falta el evento más próximo en el tiempo virtual y los empates se resuelven con la secuencia, lo que vuelve determinista la simulación. Una lista ordenada obliga a desplazar elementos en cada inserción y una tabla hash no conserva el orden.

**Complejidad o costo.** Insertar y extraer el mínimo O(log n); consultar el mínimo O(1).

## Prompt 2 — Diseño e implementación de un Montículo Mínimo propio

> **Prompt**
>
> Diseña una implementación propia de un Montículo Mínimo en Python para ser utilizado como base de una agenda de eventos.
>
> La estructura debe utilizar almacenamiento interno mediante listas y mantener la propiedad de prioridad utilizando índices de padre e hijos.
>
> Implementa las operaciones necesarias para:
>
> - Insertar elementos.
> - Extraer el elemento mínimo.
> - Consultar el mínimo.
> - Verificar estado vacío.
> - Obtener cantidad de elementos.
>
> Agrega comentarios dentro del código explicando las decisiones de diseño, la razón de utilizar esta estructura y la complejidad de las operaciones.

**Qué se construyó y por qué.** MonticuloMinimo (estructuras/monticulo_minimo.py): lista de Python que representa el árbol binario implícito, con padre en (i−1)//2 e hijos en 2i+1 y 2i+2. Insertar sube el elemento y extraer baja la nueva raíz hasta restaurar la propiedad. Cada elemento recuerda su posición, así puede retirarse sin recorrer el montículo.

**Complejidad o costo.** insertar y extraer_minimo O(log n); ver_minimo, esta_vacio y tamano O(1); eliminar un elemento conocido por referencia O(log n).

## Prompt 3 — Diseño de la entidad Evento y pruebas unitarias

> **Prompt**
>
> En un sistema de simulación temporal necesito crear una entidad llamada Evento que pueda ser administrada por una agenda de eventos.
>
> Define qué información debe almacenar esta clase considerando una arquitectura donde los DTO contienen datos y la lógica se maneja en otra capa.
>
> Implementa el criterio de comparación entre eventos utilizando prioridad por tiempo y secuencia para garantizar un comportamiento determinista.
>
> Además, diseña pruebas unitarias que validen:
>
> - Creación correcta de eventos.
> - Comparación por tiempo.
> - Comparación por secuencia.
> - Validación de datos incorrectos.

**Qué se construyó y por qué.** Evento (dto/evento.py) es un DTO con id, tiempo, secuencia, tipo, destinatario y datos; solo valida y se compara. La prioridad es (tiempo, secuencia): la secuencia rompe los empates, así la misma semilla produce siempre el mismo orden. La lógica queda en la agenda y en el motor.

**Complejidad o costo.** Crear y comparar un evento O(1).

## Prompt 4 — Diseño de una Agenda de Eventos utilizando estructuras propias

**Etapa:** propuesta inicial con tabla hash, posteriormente descartada para la agenda.

> **Prompt**
>
> Diseña una clase AgendaEventos para administrar los eventos futuros de un juego utilizando un Montículo Mínimo como estructura principal.
>
> La agenda debe permitir:
>
> - Agregar eventos.
> - Obtener el siguiente evento según prioridad.
> - Preparar operaciones futuras como cancelación y reprogramación.
>
> Explica cómo debe separarse la responsabilidad entre:
>
> - Evento.
> - Montículo Mínimo.
> - Agenda de Eventos.
> - Tabla Hash como índice auxiliar.
>
> Mantén la solución alineada con una arquitectura MVC por capas.

**Qué se construyó y por qué.** Se separaron las responsabilidades: Evento guarda datos, MonticuloMinimo ordena por prioridad y AgendaEventos ofrece programar, extraer, cancelar y reprogramar. La tabla hash propuesta como índice auxiliar quedó como propuesta histórica descartada para la agenda; la implementación actual usa el montículo mínimo más índices AVL propios (IndiceOrdenado). Esto no significa que el proyecto dejó de usar tablas hash en otros módulos.

**Complejidad o costo.** programar y extraer O(log n); localizar un evento por id O(log n) con el AVL.

## Prompt 5 — Análisis de cancelación y reprogramación de eventos

**Etapa:** propuesta inicial con tabla hash, posteriormente descartada para la agenda.

> **Prompt**
>
> Analiza cómo implementar las operaciones de cancelación y reprogramación dentro de una agenda de eventos basada en un Montículo Mínimo.
>
> Considera que el sistema debe localizar eventos mediante un identificador único y mantener la propiedad de orden del montículo después de modificar la agenda.
>
> Propón una solución utilizando una estructura auxiliar de búsqueda (Tabla Hash) y explica:
>
> - Flujo de búsqueda.
> - Eliminación segura del evento.
> - Actualización del tiempo.
> - Reinserción en la estructura de prioridad.
>
> La solución debe mantener separación entre estructuras de datos y lógica del juego.

**Qué se construyó y por qué.** Cancelar y reprogramar exigen localizar el evento por id sin recorrer el montículo. La propuesta con tabla hash buscaba O(1) amortizado y quedó como propuesta histórica descartada para la agenda: la implementación actual usa IndiceOrdenado (AVL) por id, por prioridad y por destinatario. Cancelar retira el evento del montículo por su posición y de los índices; reprogramar es cancelar y volver a programar con el nuevo tiempo.

**Complejidad o costo.** cancelar y reprogramar O(log n); consultar los eventos de un destinatario O(log n + k).

## Prompt 6 — Revisión y simplificación de Agenda de Eventos

> **Prompt**
>
> Estoy desarrollando una agenda de eventos. Inicialmente se planteó utilizar un índice auxiliar mediante una tabla hash, pero se decidió simplificar la arquitectura utilizando únicamente un Montículo Mínimo.
>
> Analiza cómo debería quedar la responsabilidad de la clase AgendaEventos bajo este nuevo diseño.
>
> Considera las operaciones:
>
> - Programar eventos.
> - Extraer el siguiente evento.
> - Cancelar eventos.
> - Reprogramar eventos.
>
> Explica cómo mantener la propiedad del montículo después de modificar eventos y cómo debe separarse la responsabilidad entre la agenda y la estructura de prioridad.

**Qué se construyó y por qué.** Versión final de AgendaEventos: ya no es solo un montículo, sino un montículo mínimo más índices AVL propios para localizar por id, por prioridad y por destinatario. La agenda valida (id único, tiempo y secuencia enteros no negativos, prioridad única) y registra cada cambio en el historial para poder deshacerlo; el montículo solo conoce la prioridad.

**Complejidad o costo.** programar, cancelar, extraer, restaurar y buscar por id O(log n).

### Tema 2. Entidades, mapa y comportamiento de enemigos

## Prompt 7 — Diseño de entidades principales del estado del juego

> **Prompt**
>
> Estoy desarrollando las entidades base.
>
> Analiza cómo deberían diseñarse las clases DTO principales:
>
> - Actor.
> - Jugador.
> - Enemigo.
> - Sala.
> - Puerta.
> - Trampa.
> - EstadoPartida.
>
> Define qué información debe almacenar cada clase y qué lógica debería permanecer fuera de estas entidades para mantener una correcta separación entre datos y comportamiento.

**Qué se construyó y por qué.** Los DTO almacenan el estado e incluyen validaciones y consultas auxiliares, como esta_vivo() y esta_activo(): Actor (vida, ataque, defensa, velocidad), Jugador y Enemigo que lo extienden, Sala con sus puertas, enemigos, objetos y trampas, Trampa y EstadoPartida, que reúne mapa, jugador, reloj, agenda e historial. Las reglas del juego viven en logica/. Algunas ampliaciones actuales llegaron desde las ramas de los compañeros.

**Complejidad o costo.** Crear y consultar atributos O(1). Es la base de la separación entre datos y comportamiento.

## Prompt 8 — Diseño del mapa de la cripta como grafo

> **Prompt**
>
> Necesito implementar la estructura del mapa de un juego tipo cripta donde las habitaciones están conectadas mediante puertas.
>
> Diseña una clase MapaCripta que represente el mapa como un grafo de salas.
>
> La clase debe permitir:
>
> - Agregar salas.
> - Buscar salas mediante identificadores.
> - Obtener salas vecinas mediante conexiones disponibles.
>
> Explica cómo representar las relaciones entre salas y cómo separar la estructura del mapa de la lógica de movimiento del jugador.

**Qué se construyó y por qué.** MapaCripta (logica/mapa_cripta.py) es un grafo: cada sala es un nodo y las puertas son las conexiones. Guarda las salas en una lista y resuelve los vecinos a partir de las puertas. No mueve al jugador: esa regla es del motor. No usa tabla hash para el índice de salas.

**Complejidad o costo.** Agregar o buscar una sala por id O(n). Obtener los vecinos cuesta O(grado) cuando las conexiones ya están vinculadas y se recibe la sala directamente; si primero se busca por id, se suma el recorrido de salas, y la vinculación inicial de conexiones tiene un costo adicional.

## Prompt 9 — Diseño de sistema de rastros y comportamiento de enemigos

> **Prompt**
>
> Estoy implementando enemigos con diferentes comportamientos dentro de un juego de simulación.
>
> Los enemigos pueden tener comportamientos como:
>
> - Guardián.
> - Errante.
> - Rastreador.
>
> Analiza cómo debería diseñarse una clase encargada de decidir acciones de enemigos sin ejecutar directamente las acciones.
>
> Además, define cómo implementar un registro de rastros del jugador que permita determinar si existe una presencia reciente utilizando una ventana temporal determinada.
>
> Mantén separadas las responsabilidades entre:
>
> - Datos del enemigo.
> - Registro del rastro.
> - Decisión de comportamiento.
> - Ejecución dentro del motor del juego.

**Qué se construyó y por qué.** ComportamientoEnemigos decide la acción (atacar, esperar o moverse) según el comportamiento guardián, errante o rastreador, sin ejecutarla: ejecutar le toca al motor. RegistroRastro guarda en cada sala el tiempo de la última presencia del jugador (ultimo_rastro); el rastro es reciente si pasaron menos de 400 unidades de tiempo virtual.

**Complejidad o costo.** Consultar o actualizar el rastro de una sala O(1), porque se guarda en la propia sala; decidir una acción cuesta lo que cueste revisar las puertas de la sala actual.

### Tema 3. Efectos, motor y combate

## Prompt 10 — Diseño e integración del gestor de efectos temporales

> **Prompt**
>
> En un juego de simulación necesito administrar efectos temporales como veneno, regeneración, aumento de velocidad, antorchas y trampas.
>
> Diseña una clase GestorEfectos encargada de administrar estos estados temporales.
>
> La clase debe permitir:
>
> - Aplicar efectos.
> - Cancelar efectos.
> - Procesar eventos relacionados con efectos.
>
> Explica cómo debería interactuar con el estado actual de la partida y con el sistema de eventos.
>
> Considera una arquitectura donde:
>
> - Los DTO almacenan información.
> - La lógica administra reglas.
> - Los eventos activan cambios en el tiempo.

**Qué se construyó y por qué.** GestorEfectos administra los efectos temporales: veneno (daño cada 80 unidades durante 400), regeneración (cada 200) y velocidad, como eventos de la agenda con los identificadores guardados; cancelar un efecto cancela esos eventos. La activación y el rearme de las trampas los integra el motor, no el gestor. Todo cambio pasa por mutaciones reversibles para que el retroceso funcione.

**Complejidad o costo.** Aplicar o cancelar un efecto O(log n) por evento de agenda.

## Prompt 11 — Diseño e integración del Motor del Juego

> **Prompt**
>
> Actualmente cuento con componentes como una agenda de eventos, sistema de combate, gestor de efectos y comportamiento de enemigos. Necesito definir cómo debe estructurarse una clase MotorJuego que funcione como controlador principal de la simulación.
>
> Analiza qué responsabilidades debería tener esta clase y cómo debería interactuar con:
>
> - EstadoPartida.
> - AgendaEventos.
> - ReglasCombate.
> - GestorEfectos.
> - ComportamientoEnemigos.
>
> Considera principios de diseño como separación de responsabilidades, encapsulamiento y bajo acoplamiento. La clase debe permitir iniciar una partida, ejecutar acciones del jugador y avanzar la simulación mediante eventos.

**Qué se construyó y por qué.** MotorJuego coordina estado, agenda, combate, efectos y comportamiento: ejecuta la acción del jugador, avanza el reloj virtual y procesa los eventos hasta la siguiente decisión. Cada acción abre un intervalo del historial. El motor no dibuja ni pide entradas.

**Complejidad o costo.** Las operaciones de agenda de cada acción cuestan O(log n) por evento procesado, es decir O(e log n) con e eventos. Eso describe solo ese componente: el ciclo completo también incluye validaciones, búsquedas y la ejecución de las reglas.

## Prompt 12 — Diseño de reglas de combate y procesamiento de eventos

> **Prompt**
>
> Necesito diseñar una clase encargada de administrar las reglas de enfrentamiento entre actores.
>
> La clase debe permitir:
>
> - Ejecutar ataques entre personajes.
> - Calcular daño considerando ataque y defensa.
> - Actualizar puntos de vida.
> - Determinar cuándo un actor es derrotado.
> - Procesar las consecuencias de una muerte dentro del estado de partida.
>
> Analiza cómo separar correctamente la lógica de combate del resto del sistema, evitando que esta clase controle eventos, movimiento o administración del juego.
>
> Además, considera cómo debería integrarse posteriormente con un motor de juego basado en eventos.

**Qué se construyó y por qué.** ReglasCombate.atacar calcula daño = max(1, ataque + azar entre 0 y 4 − defensa), actualiza la vida con cambios reversibles y devuelve el resultado. procesar_muerte marca la muerte una sola vez, cancela los eventos del actor y gestiona el botín. No programa eventos ni mueve actores.

**Complejidad o costo.** Un ataque O(1); procesar una muerte O(log n) por cada evento cancelado.

### Tema 4. Equipamiento, reversión e integración

## Prompt 13 — Equipamiento

> **Prompt**
>
> Revisa MotorJuego e integra EQUIPAR usando ServicioInventario. La acción debe aplicar las bonificaciones, cobrar el costo una sola vez y registrar cambios reversibles. Modifica únicamente mi motor y sus pruebas.

**Qué se construyó y por qué.** Mi aporte fue integrar ServicioInventario con MotorJuego para EQUIPAR: el motor aplica las bonificaciones, cobra el costo de tiempo una sola vez y deja cambios reversibles para poder deshacer. El servicio de inventario como tal lo implementó otro integrante.

**Complejidad o costo.** Aplicar bonos y mover el nodo al frente O(1); localizar el objeto en el inventario O(n).

## Prompt 14 — Soltar equipo

> **Prompt**
>
> Corrige SOLTAR para que retire las bonificaciones de un objeto equipado y conserve la posibilidad de deshacer. Mantén funcionando recoger y soltar objetos simples sin exigir fichas de uso.

**Qué se construyó y por qué.** Mi aporte fue la integración en el motor: SOLTAR un objeto equipado retira sus bonificaciones, lo deja en el suelo de la sala y registra el cambio para poder deshacer. Recoger y soltar objetos simples sigue funcionando sin fichas de uso.

**Complejidad o costo.** Quitar el nodo seleccionado O(1); agregar el objeto al suelo con append es O(1) amortizado. Buscar o retirar objetos del suelo en otras operaciones sí puede requerir recorrer la lista.

## Prompt 15 — Servicio compartido

> **Prompt**
>
> Agrega a MotorJuego un método para conectar una instancia compartida de ServicioInventario antes de ejecutar acciones. Evita reemplazar un servicio que ya esté en uso y verifica la conexión mediante pruebas.

**Qué se construyó y por qué.** Integración en MotorJuego: recibe una instancia compartida de ServicioInventario antes de actuar, la misma de JuegoService, para que jugador, inventario e historial sean los mismos. No reemplaza un servicio que ya esté en uso.

**Complejidad o costo.** Conectar el servicio O(1).

## Prompt 16 — Condición de victoria

> **Prompt**
>
> Corrige la victoria para que dependa de haber abierto la puerta de salida con la llave correcta, aunque después se suelte la llave. Registra ese antecedente de forma reversible y conserva la prioridad de derrota por trampas.

**Qué se construyó y por qué.** La victoria depende de haber abierto la puerta de salida con la llave correcta. Ese antecedente se guarda como cambio reversible: soltar la llave después no quita la victoria y deshacer sí puede revertirla. La derrota por trampas conserva la prioridad.

**Complejidad o costo.** Comprobar la condición O(1).

## Prompt 17 — Pruebas de regresión

> **Prompt**
>
> Añade pruebas para equipar, reemplazar un arma, soltar equipo y deshacer. Comprueba bonificaciones, ubicación de objetos, reloj e historial. Ejecuta la suite y explica cualquier fallo sin modificar clases de mis compañeros.

**Qué se construyó y por qué.** Pruebas de regresión de equipar, reemplazar un arma, soltar equipo y deshacer: comprueban bonificaciones, ubicación de objetos, reloj e historial.

**Complejidad o costo.** No añaden costo al juego. Verifican que deshacer deje el estado idéntico en cada caso.

### Tema 5. Medición inicial de rendimiento

## Prompt 18 — Rendimiento

> **Prompt**
>
> Prepara una medición del ciclo completo entre decisiones del jugador, incluyendo eventos enemigos. Excluye preparación, red y renderizado; reporta mediana, máximo y ciclos de 20 ms o más.

**Qué se construyó y por qué.** Medición del ciclo completo entre decisiones del jugador, con eventos enemigos y sin preparación, red ni renderizado. Reporta mediana, máximo y ciclos de 20 ms o más para comprobar el requisito de respuesta.

**Complejidad o costo.** Mide el ciclo completo, que incluye las operaciones de agenda O(e log n), validaciones, búsquedas y reglas; la mediana y el máximo muestran si existen ciclos lentos.

### Tema 6. Imágenes de personajes y objetos

## Prompt 19 — Sprites del jugador y la rata gigante

> **Prompt**
>
> Integra jugador.png y rata_gigante.png en VistaPygame para mostrarlos en las casillas de la sala. Carga las imágenes una sola vez, conserva su proporción y transparencia, y utiliza el símbolo original si falta un archivo. Mantén las reglas del motor y los nombres y puntos de vida visibles.

**Qué se construyó y por qué.** Aporte de presentación: sprites del jugador y la rata gigante en VistaPygame. Se cargan una sola vez, conservan proporción y transparencia y, si falta el archivo, se usa el símbolo original.

**Complejidad o costo.** Carga única por sprite. Dibujar una imagen depende de sus píxeles; como su tamaño es fijo en el juego, el costo por casilla se mantiene constante en la práctica.

## Prompt 20 — Imágenes de objetos, trampas y enemigos

> **Prompt**
>
> Agrega los sprites llave_negra.png, arma.png, trampa_dardos.png, guardian_oseo.png y rata_muerta.png donde correspondan. Asocia arma.png con la daga oxidada y distingue la llave negra de las demás llaves. Usa la imagen de rata muerta solo cuando la rata esté derrotada y conserva el símbolo de respaldo para entidades sin imagen.

**Qué se construyó y por qué.** Aporte de presentación: sprites de objetos, trampas y enemigos asociados a su ficha: arma.png para la daga oxidada, una llave negra distinta de las demás y la rata muerta solo cuando está derrotada. Las entidades sin imagen conservan el símbolo.

**Complejidad o costo.** Carga única; dibujar cada imagen depende de sus píxeles, que son fijos en el juego.

### Tema 7. Fondos de la interfaz

## Prompt 21 — Fondo del menú inicial

> **Prompt**
>
> Incorpora assets/fondos/menu_inicio.png como fondo del menú inicial de Pygame. Escálalo conservando su proporción y recorta desde el centro para cubrir la ventana. Mantén legibles los títulos y botones, carga el fondo una sola vez y conserva un fondo de respaldo si la imagen no está disponible.

**Qué se construyó y por qué.** Aporte de presentación: fondo del menú inicial escalado conservando la proporción y recortado desde el centro, cargado una sola vez, con un fondo de respaldo si falta la imagen.

**Complejidad o costo.** Escalar una vez O(píxeles); dibujar el fondo en cada cuadro depende de los píxeles de la ventana.

## Prompt 22 — Fondo de la sala actual

> **Prompt**
>
> Agrega assets/fondos/sala.png al panel que muestra la sala actual. Ajusta la imagen al área del panel conservando la proporción y aplica una capa oscura para que los textos y sprites se distingan. Conserva la distribución de personajes, objetos, trampas y puertas, sin cambiar las reglas del juego.

**Qué se construyó y por qué.** Aporte de presentación: fondo de la sala actual ajustado al panel con una capa oscura para que se distingan textos y sprites. La distribución de personajes, objetos, trampas y puertas no cambia y las reglas tampoco.

**Complejidad o costo.** Escalar una vez O(píxeles); dibujar el fondo en cada cuadro depende de los píxeles del panel.

### Tema 8. Rendimiento con datos reales

## Prompt 23 — Benchmark de ciclos con las cuatro criptas

> **Prompt**
>
> Crea benchmarks/benchmark_ciclo_real_integrante1.py para medir ciclos completos entre decisiones del jugador con las criptas reales previamente cargadas. Usa semilla fija, calentamiento separado y perf_counter_ns; excluye red, renderizado y preparación. Permite seleccionar una cripta o medir todas, incluye enemigos y efectos, y guarda las mediciones individuales junto con mediana, p95, máximo y cantidad de ciclos de 20 ms o más. No modifiques producción.

**Qué se construyó y por qué.** Benchmark de ciclos con las cuatro criptas reales: semilla fija, calentamiento separado, perf_counter_ns, sin red ni render. Guarda las mediciones individuales con mediana, p95, máximo y cantidad de ciclos de 20 ms o más.

**Complejidad o costo.** Los resultados demuestran el cumplimiento en los escenarios, el equipo y la versión medidos; no prueban todos los recorridos posibles ni el rendimiento de futuras actualizaciones. El p95 y el máximo revelan colas largas que la mediana oculta.

### Tema 9. Revisión de conflictos e integración de ramas

## Prompt 24 — Correcciones de la vista después del merge

> **Prompt**
>
> Revisa vista/vista_pygame.py después del merge. Corrige mostrar_menu_criptas para aceptar opcion_continuar=None y conservar el botón de continuar partida. En la sala, muestra el nombre y efecto de los objetos en lugar de sus IDs internos, manteniendo sus sprites. Haz cambios mínimos y conserva los demás cambios locales.

**Qué se construyó y por qué.** Tras el merge se verificó y recuperó la compatibilidad de la vista: mostrar_menu_criptas acepta opcion_continuar=None y conserva el botón de continuar partida, que ya existía, y en la sala se muestran el nombre y el efecto de los objetos en lugar de sus ids internos, manteniendo los sprites. No se implementó desde cero la opción de continuar partidas.

**Complejidad o costo.** Dibujar O(k) por k objetos visibles.

## Prompt 25 — Verificación del menú, imágenes y diferencias con Steve

> **Prompt**
>
> Verifica el menú con y sin partida guardada, la carga de sprites y fondos, y la presentación de nombres y efectos. Compara estos puntos con origin/Steve sin hacer merge ni reemplazar archivos completos. Informa si reaparecieron proteger_sala/liberar_sala o faltan llamadas a registrar_origen en service/repositorio_catalogo.py, sin modificar ese archivo. Usa el entorno .venv y distingue pruebas automatizadas de inspección visual.

**Qué se construyó y por qué.** Revisión de integración: se verificó el menú, los sprites y los nombres, y se comparó con origin/Steve sin hacer merge. Se comprobó que no reaparecieran proteger_sala/liberar_sala ni faltaran llamadas a registrar_origen; las diferencias del catálogo se detectaron y comunicaron, no se corrigieron sus clases, y las modificaciones posteriores de Steve conservan su atribución. Se distinguió lo probado automáticamente de lo inspeccionado a mano.

**Complejidad o costo.** No aplica: es una revisión, no un cambio de código.

### Tema 10. Reglas del motor y avisos al jugador

## Prompt 26 — Regresión de ratas y trampa con semilla 3

> **Prompt**
>
> Reproduce la entrada a la sala 2 de cripta-01 con semilla 3 y datos reales. Contrasta el enunciado y registra tiempo, secuencia, actor, daño y próxima acción. Verifica que cada rata tenga una sola acción pendiente, que moverse no incluya atacar en el mismo evento y que la trampa no se dispare antes del rearme. Añade una regresión determinista y ejecuta tests/test_contrato_api_real.py. No ajustes daño ni velocidad para facilitar el juego.

**Qué se construyó y por qué.** Regresión determinista con semilla 3 en la sala 2 de cripta-01: cada rata mantiene una sola acción pendiente, moverse no incluye atacar en el mismo evento y la trampa no se dispara antes del rearme, sin tocar daño ni velocidad.

**Complejidad o costo.** Cada rata aporta un único evento pendiente; las operaciones de agenda siguen costando O(log n) por evento, sin contar las validaciones y reglas del ciclo.

## Prompt 27 — Avisos automáticos y campo de curación

> **Prompt**
>
> Comprueba que los avisos de cierre automático y rearme lleguen a consola y Pygame sin duplicados ni anuncios de eventos cancelados o deshechos. Verifica que AdaptadorFichas utiliza el mapeo "curacion": "cura" para las pociones del API. Si ya funciona, conserva producción y añade únicamente la cobertura que falte. Ejecuta las pruebas relevantes y de contrato, sin modificar reglas del motor ni documentación.

**Qué se construyó y por qué.** Se verificaron los avisos de cierre automático de puertas y rearme de trampas en consola y Pygame. Se amplió la cobertura en tests/test_controller/test_presentacion_jugador.py para comprobar su recepción, evitar duplicados y validar eventos deshechos o cancelados. También se confirmó que el alias interno curacion consulta el campo cura del API, mediante una corrección previamente incorporada por Steve. Los avisos ya los había implementado Joshua; no se modificó código de producción.

**Complejidad o costo.** Un aviso O(1) por evento procesado.

### Tema 11. Presentación del guardián derrotado

## Prompt 28 — Sprite del guardián muerto

> **Prompt**
>
> Incorpora assets/personajes/guardian_muerto.png en VistaPygame. Cárgalo una sola vez y muéstralo cuando el guardián óseo esté derrotado, conservando la imagen específica de las ratas muertas. Si el guardián revive al deshacer, debe volver a utilizar su sprite de vivo. Mantén la proporción, transparencia y símbolo de respaldo, sin modificar el combate ni el historial.

**Qué se construyó y por qué.** Aporte de presentación: sprite del guardián muerto, cargado una sola vez. Si el guardián revive al deshacer, vuelve a usarse el sprite de vivo, sin tocar el combate ni el historial.

**Complejidad o costo.** Elegir el sprite O(1) según la vida; dibujarlo depende de sus píxeles, que son fijos en el juego.

---

# Joshua Cabrera Bonilla — Integrante 3: Estructuras de apoyo, controlador y vista

Bitácora de prompts (§10.3) de Joshua, ordenada por tema. Cada entrada incluye el prompt, qué se construyó y por qué, y el costo de la solución. Las fechas están en la tabla.

| # | Prompt | Tema | Fecha |
| --- | --- | --- | --- |
| 1 | Implementación de una lista doble enlazada | Lista doble e inventario | 29/09/2026–01/10/2026 |
| 2 | Implementación del inventario utilizando ListaDobleImpl | Lista doble e inventario | 29/09/2026–01/10/2026 |
| 3 | Implementación de una cola circular propia | Cola circular y bitácora | 29/09/2026–01/10/2026 |
| 4 | Implementación de BitacoraPantalla utilizando ColaCircular | Cola circular y bitácora | 29/09/2026–01/10/2026 |
| 5 | Pruebas de las estructuras y del inventario | Pruebas de estructuras | 29/09/2026–01/10/2026 |
| 6 | Implementación de ordenamientos propios | Ordenamientos | 29/09/2026–01/10/2026 |
| 7 | Selección adaptativa entre Insertion sort y Merge sort | Ordenamientos | 29/09/2026–01/10/2026 |
| 8 | Implementación de cambios reversibles de vida y reloj | Retroceso e historial | 29/09/2026–01/10/2026 |
| 9 | Agrupación de cambios mediante una pila sobre lista doble | Retroceso e historial | 29/09/2026–01/10/2026 |
| 10 | Historial reversible de cinco acciones utilizando lista doble | Retroceso e historial | 29/09/2026–01/10/2026 |
| 11 | Implementación del registro de partida | Registro de partida | 01/10/2026–04/10/2026 |
| 12 | Implementación del repositorio de puntajes | Puntajes | 01/10/2026–04/10/2026 |
| 13 | Implementación de la vista de consola | Consola | 01/10/2026–04/10/2026 |
| 14 | Configuración y argumentos del programa | Configuración | 01/10/2026–04/10/2026 |
| 15 | Controlador de comandos y coordinación de servicios | Controlador | 01/10/2026–07/10/2026 |
| 16 | Consultas de puntajes con ordenamiento adaptativo | Puntajes y ordenamientos | 01/10/2026–06/10/2026 |
| 17 | Servicio de inventario, equipo y consumibles | Inventario, equipo y consumibles | 01/10/2026–07/10/2026 |
| 18 | Medición de las estructuras del integrante 3 | Mediciones | 01/10/2026–07/10/2026 |
| 19 | Reproducción determinista y selección al equipar | Replay | 04/10/2026–07/10/2026 |
| 20 | Construcción de la partida desde la fuente de datos | Inicialización de partidas | 07/10/2026–16/10/2026 |
| 21 | Reconstrucción de referencias al restaurar una partida | Restauración | 06/10/2026–07/10/2026 |
| 22 | Guardado y reanudación mediante JuegoService | Guardado y reanudación | 06/10/2026–16/10/2026 |
| 23 | Mensajes legibles y consultas después del final | Presentación y consultas | 14/10/2026–15/10/2026 |
| 24 | Integración de inventario y controles en Pygame | Interfaz Pygame | 14/10/2026–16/10/2026 |
| 25 | Registro automático de cada partida y verificación del replay | Registro automático | 16/10/2026 |

## Prompt 1 — Implementación de una lista doble enlazada

> **Prompt**
>
> Para el proyecto Cripta voy a utilizar una lista doble enlazada propia. Necesito que completes las clases NodoDoble y ListaDobleImpl respetando el contrato existente. Cada nodo debe almacenar un valor y referencias al nodo anterior y al siguiente. La lista debe mantener el primer nodo, el último y la cantidad de elementos.
>
> Implementa las siguientes operaciones:
>
> - Insertar un elemento al inicio y devolver el nodo creado.
> - Quitar un nodo recibido por referencia.
> - Mover un nodo al frente conservando el mismo nodo.
>
> Considera los casos de lista vacía, un único elemento y nodos ubicados al inicio, al final o en medio. Explica cómo se actualizan las referencias y la complejidad de cada operación.

**Qué se construyó y por qué.** ListaDobleImpl con NodoDoble (valor, anterior y siguiente), primero, último y cantidad. Quitar y mover al frente trabajan sobre el mismo nodo y solo actualizan a sus vecinos, sin recorrer la lista; así el cursor es estable y deshacer puede reinsertar el mismo nodo.

**Complejidad o costo.** Insertar al inicio, quitar un nodo y mover al frente O(1) cuando se recibe el nodo.

## Prompt 2 — Implementación del inventario utilizando ListaDobleImpl

> **Prompt**
>
> Voy a utilizar ListaDobleImpl como estructura interna del inventario y un cursor que apunte al nodo seleccionado. Implementa la clase Inventario con una capacidad máxima recibida mediante el constructor.
>
> Debe permitir:
>
> - Agregar objetos al inicio y seleccionar el objeto nuevo.
> - Rechazar inserciones cuando esté lleno.
> - Consultar el objeto seleccionado.
> - Avanzar y retroceder mediante los enlaces del nodo.
> - Quitar el objeto actual y seleccionar un vecino.
> - Mover el objeto actual al frente.
> - Consultar la cantidad y capacidad.
> - Obtener una lista auxiliar sin modificar el orden real.
>
> Al alcanzar un extremo, el cursor debe conservar su posición. Mantén las reglas de uso y equipamiento fuera de esta clase y explica el funcionamiento de los métodos.

**Qué se construyó y por qué.** Inventario con capacidad fija y un cursor al nodo seleccionado: navega por los enlaces, rechaza insertar si está lleno, conserva el cursor en los extremos y entrega una lista auxiliar sin alterar el orden real. Las reglas de uso quedan en ServicioInventario.

**Complejidad o costo.** agregar, siguiente, anterior, quitar el actual y mover al frente O(1) con el nodo conocido; comprobar si queda capacidad O(1); buscar un objeto recorriendo la lista O(n); lista auxiliar O(n).

## Prompt 3 — Implementación de una cola circular propia

> **Prompt**
>
> Para almacenar los elementos recientes voy a utilizar una cola circular de capacidad fija, implementada sobre una lista de Python. Completa la clase ColaCircular utilizando un índice de frente, un índice para la próxima inserción y un contador de elementos.
>
> Implementa las operaciones necesarias para:
>
> - Encolar elementos.
> - Reemplazar el elemento más antiguo cuando esté llena.
> - Desencolar el elemento del frente.
> - Consultar el frente sin retirarlo.
> - Verificar si está vacía o llena.
> - Consultar cantidad y capacidad.
> - Obtener los elementos en orden de llegada.
>
> Utiliza el operador módulo para que los índices regresen al inicio al alcanzar el final del arreglo. No redimensiones el almacenamiento. Explica cómo se reutilizan las posiciones y el costo de las operaciones.

**Qué se construyó y por qué.** ColaCircular: lista de tamaño fijo con índice de frente, índice de inserción y contador. El módulo reutiliza las posiciones y, al llenarse, reemplaza al elemento más antiguo sin redimensionar.

**Complejidad o costo.** encolar, desencolar y ver_frente O(1); obtener_elementos O(n).

## Prompt 4 — Implementación de BitacoraPantalla utilizando ColaCircular

> **Prompt**
>
> Voy a utilizar ColaCircular para almacenar los últimos 20 mensajes del juego. Completa BitacoraPantalla para que cree una cola con capacidad 20 y conserve los métodos agregar y obtener_mensajes.
>
> La clase debe:
>
> - Agregar mensajes mediante las operaciones de ColaCircular.
> - Reemplazar el mensaje más antiguo cuando se alcance el límite.
> - Devolver los mensajes del más antiguo al más reciente.
> - Permitir consultar los mensajes sin eliminarlos.
> - Conservar mensajes repetidos como entradas independientes.
>
> Reutiliza el manejo de posiciones de ColaCircular. La bitácora debe almacenar los mensajes y dejar que la vista se encargue de mostrarlos.

**Qué se construyó y por qué.** BitacoraPantalla guarda los últimos 20 mensajes en una ColaCircular. Los mensajes repetidos son entradas independientes y la vista decide cómo mostrarlos.

**Complejidad o costo.** Agregar O(1); consultar O(n) con n ≤ 20.

## Prompt 5 — Pruebas de las estructuras y del inventario

> **Prompt**
>
> Utiliza unittest para crear las pruebas de ListaDobleImpl, Inventario, ColaCircular y BitacoraPantalla, siguiendo el estilo de las pruebas existentes del proyecto.
>
> Comprueba:
>
> - Inserción, eliminación y movimiento de nodos en la lista doble.
> - Enlaces hacia adelante y hacia atrás.
> - Actualización del cursor y límite de capacidad del inventario.
> - Reutilización de posiciones y reemplazo del elemento más antiguo en la cola circular.
> - Conservación de los últimos 20 mensajes en la bitácora.
> - Comportamiento con estructuras vacías y con un único elemento.
> - Consultas que no alteren los datos almacenados.
>
> Entrega cada archivo completo en su carpeta correspondiente de tests e indica cómo ejecutarlos desde la carpeta principal utilizando unittest.

**Qué se construyó y por qué.** Pruebas de ListaDobleImpl, Inventario, ColaCircular y BitacoraPantalla con los casos límite: vacío, un elemento y capacidad llena, y consultas que no alteran los datos.

**Complejidad o costo.** No añaden costo al juego; protegen los casos de borde de cada estructura.

## Prompt 6 — Implementación de ordenamientos propios

> **Prompt**
>
> Para ordenar los datos del proyecto voy a utilizar Insertion sort y Merge sort. Completa la clase OrdenadorAdaptativo respetando el contrato ordenar(elementos, criterio). El criterio será una función que indique el valor por el que debe ordenarse cada elemento.
>
> Implementa ambos algoritmos sin utilizar sorted() ni list.sort(). Deben devolver una lista nueva, conservar los objetos originales y mantener el orden relativo de los elementos con igual criterio.
>
> Calcula las claves sin repetir innecesariamente la evaluación del criterio. Explica el funcionamiento de cada algoritmo y sus complejidades. La implementación debe servir para ordenar vistas del inventario, puntajes y otras colecciones del proyecto.

**Qué se construyó y por qué.** OrdenadorAdaptativo con Insertion sort y Merge sort propios, sin sorted ni list.sort. Devuelven una lista nueva, son estables y evalúan una sola vez cada criterio.

**Complejidad o costo.** Insertion O(n + I), con I inversiones (lineal solo si I = O(n)) y O(n²) en el peor caso; Merge O(n log n) con memoria O(n); ambos estables.

## Prompt 7 — Selección adaptativa entre Insertion sort y Merge sort

> **Prompt**
>
> En OrdenadorAdaptativo quiero seleccionar automáticamente entre los dos algoritmos implementados.
>
> Utiliza Insertion sort para listas pequeñas. Para listas mayores, intenta ordenarlas con Insertion sort contando los desplazamientos y cambia a Merge sort si se supera un límite proporcional a la cantidad de elementos.
>
> El intento interrumpido no debe modificar la lista original. Reutiliza las claves calculadas cuando se cambie de algoritmo, especialmente si el criterio resulta costoso.
>
> Define umbrales configurables que podamos ajustar mediante mediciones. Agrega pruebas con unittest para comprobar ambos algoritmos, estabilidad, conservación de los datos originales y selección utilizada con listas pequeñas, ordenadas, casi ordenadas e invertidas.

**Qué se construyó y por qué.** Hasta 16 elementos usa Insertion. Con más, intenta Insertion contando desplazamientos con límite n y, si lo supera, cambia a Merge reutilizando las claves ya calculadas; el intento interrumpido no toca la lista original. Los umbrales se calibraron con benchmarks/integrante3.py.

**Complejidad o costo.** Insertion es lineal solo si las inversiones son O(n); si los desplazamientos superan el límite n se pasa a Merge, por lo que el peor caso es O(n log n) más, como máximo, n desplazamientos descartados.

## Prompt 8 — Implementación de cambios reversibles de vida y reloj

> **Prompt**
>
> Para el retroceso del juego voy a utilizar clases que implementen el contrato CambioReversible mediante el método deshacer(estado). Implementa CambioVida y CambioReloj.
>
> Cada clase debe capturar el valor anterior antes de que se modifique y conservar únicamente la información necesaria para restaurarlo. CambioVida debe guardar la referencia al actor y su vida anterior. CambioReloj debe guardar el tiempo virtual anterior y restaurarlo sobre el estado recibido.
>
> No utilices copias completas del actor ni de la partida. Explica cuándo deben crearse estos registros y agrega pruebas con unittest para verificar la restauración de los valores.

**Qué se construyó y por qué.** CambioVida y CambioReloj guardan solo el valor anterior (y la referencia al actor) y lo restauran en deshacer; no copian el actor ni la partida.

**Complejidad o costo.** Registrar y deshacer O(1) cada uno.

## Prompt 9 — Agrupación de cambios mediante una pila sobre lista doble

> **Prompt**
>
> Voy a utilizar nuestra ListaDobleImpl como una pila para almacenar los cambios de una TransaccionAccion. Cada transacción debe agrupar los cambios de una acción del jugador y de los eventos posteriores hasta la siguiente decisión.
>
> Implementa las operaciones para:
>
> - Registrar cada cambio al inicio de la lista.
> - Consultar la cantidad de cambios.
> - Verificar si la transacción está vacía.
> - Revertir los cambios desde el más reciente hasta el más antiguo.
> - Evitar que una transacción se revierta dos veces.
> - Rechazar nuevos registros después de revertirla.
>
> Explica por qué es necesario deshacer en orden inverso. Agrega pruebas con unittest que incluyan varios cambios sobre el mismo dato y cambios asociados a distintos actores.

**Qué se construyó y por qué.** TransaccionAccion usa ListaDobleImpl como pila (lo más reciente al inicio) para revertir en orden inverso: si un dato cambió dos veces, deshacer al revés devuelve el valor original. Una transacción revertida no puede revertirse otra vez ni aceptar más registros.

**Complejidad o costo.** Registrar O(1); recorrer k cambios O(k). El costo total de revertir depende además de las validaciones y operaciones de cada cambio reversible.

## Prompt 10 — Historial reversible de cinco acciones utilizando lista doble

> **Prompt**
>
> Para administrar el historial voy a utilizar nuestra ListaDobleImpl, colocando la transacción más reciente al inicio y la más antigua al final.
>
> Implementa HistorialReversible para conservar hasta cinco transacciones cerradas y mantener por separado el intervalo que está recibiendo cambios.
>
> La clase debe permitir:
>
> - Iniciar un intervalo.
> - Registrar cambios en el intervalo actual.
> - Cerrar y guardar una transacción.
> - Deshacer primero la transacción más reciente.
> - Descartar la más antigua al superar cinco, sin revertir sus efectos.
> - Consultar la cantidad de transacciones y si existe un intervalo abierto.
>
> Impide iniciar dos intervalos simultáneos, registrar sin un intervalo abierto y deshacer mientras una acción está en curso. Agrega pruebas del orden de retroceso, la reutilización del historial y el límite de cinco acciones. Mantén el consumo del pergamino fuera de esta clase.

**Qué se construyó y por qué.** HistorialReversible conserva hasta cinco transacciones cerradas en una lista doble (la más reciente primero) y, aparte, el intervalo abierto. Al superar cinco descarta la más antigua sin revertirla.

**Complejidad o costo.** Cerrar un intervalo y descartar O(1); deshacer la última recorre sus k cambios, más el costo de validar y aplicar cada uno.

## Prompt 11 — Implementación del registro de partida

> **Prompt**
>
> Para Cripta necesito completar RegistroPartida conservando las firmas de crear y anexar_accion. Utiliza un archivo de texto UTF-8 en formato JSON Lines, con un registro por línea.
>
> La clase debe permitir:
>
> - Crear una cabecera con identificador de cripta, versión de cripta, versión de catálogo y semilla.
> - Evitar sobrescribir archivos existentes.
> - Anexar acciones sin eliminar registros anteriores.
> - Guardar tipo de acción, dirección e identificador estable del objetivo.
> - Obtener el identificador desde los atributos reales de los objetos del proyecto.
> - Rechazar objetivos sin un identificador válido.
>
> No guardes representaciones de objetos en memoria ni estados completos. Agrega pruebas con archivos temporales para comprobar la cabecera, el anexado y la protección de archivos existentes.

**Qué se construyó y por qué.** RegistroPartida escribe JSON Lines: una cabecera (cripta, versión de cripta, versión de catálogo, semilla) y una línea por acción con tipo, dirección e id estable del objetivo. No sobrescribe archivos ni guarda estados en memoria. Es la base del replay.

**Complejidad o costo.** Anexar no recorre el archivo anterior: serializar y escribir el registro cuesta O(b) en sus bytes (O(1) si el tamaño está acotado); leer el log completo O(n).

## Prompt 12 — Implementación del repositorio de puntajes

> **Prompt**
>
> Completa RepositorioPuntajes conservando registrar_resultado(resultado) y listar(). Utiliza el archivo local puntajes.dat y almacena cada resultado como una línea JSON.
>
> La clase debe:
>
> - Recibir un diccionario con los datos del resultado.
> - Conservar nombre del jugador, identificador y versión de cripta, acciones ejecutadas, enemigos derrotados y tiempo virtual final.
> - Anexar resultados sin borrar partidas anteriores.
> - Recuperar los registros entre distintas instancias del repositorio.
> - Devolver una lista vacía cuando el archivo todavía no exista.
> - Informar errores de contenido inválido sin borrar el archivo.
>
> Conserva el orden de registro. Las estadísticas deben recibirse del modelo; no inventes una fórmula de puntaje.

**Qué se construyó y por qué.** RepositorioPuntajes guarda cada resultado como una línea JSON en puntajes.dat, anexa sin borrar, devuelve una lista vacía si el archivo no existe y no inventa una fórmula de puntaje.

**Complejidad o costo.** registrar_resultado O(b) en el tamaño del registro (O(1) si está acotado); listar O(n).

## Prompt 13 — Implementación de la vista de consola

> **Prompt**
>
> Completa VistaConsola utilizando los atributos existentes de EstadoPartida, Jugador y Sala. Conserva mostrar_estado, leer_comando, mostrar_error y mostrar_mensaje.
>
> Implementa lo necesario para:
>
> - Mostrar cripta, reloj virtual, acciones ejecutadas y enemigos derrotados.
> - Mostrar nombre, vida, ataque, defensa y velocidad del jugador.
> - Mostrar sala actual, puertas, enemigos, objetos y trampas.
> - Presentar inventario, objeto seleccionado y equipo.
> - Mostrar efectos activos y los últimos 20 mensajes.
> - Manejar estados sin jugador o sin sala.
> - Leer comandos sin interpretarlos y tratar el fin de entrada de forma controlada.
>
> La vista únicamente presenta información y recoge entradas. No debe modificar el modelo ni ejecutar reglas del juego.

**Qué se construyó y por qué.** VistaConsola presenta estado, sala, inventario, efectos y los últimos 20 mensajes, y lee comandos sin interpretarlos. No modifica el modelo: respeta la separación MVC.

**Complejidad o costo.** Mostrar el estado O(n) en lo visible; leer y devolver un comando O(L) en su longitud, sin contar la espera del usuario.

## Prompt 14 — Configuración y argumentos del programa

> **Prompt**
>
> Completa Configuracion y parsear_argumentos conservando las opciones y rutas existentes del proyecto.
>
> Permite configurar:
>
> - Uso de fuente offline.
> - Capacidad de caché mediante cache-size.
> - Archivo de reproducción mediante replay.
> - Ejecución de mediciones mediante bench.
> - Semilla aleatoria.
> - Vista de consola o pygame.
> - Modo de demostración.
>
> Valida cache-size como entero positivo y conserva 25 como valor predeterminado. Los argumentos inválidos deben informarse mediante argparse.
>
> Cuando el constructor reciba argumentos directamente, valida sus valores sin consultar nuevamente la línea de comandos. Conserva la URL de API configurada y agrega pruebas de valores predeterminados, opciones válidas y entradas inválidas.

**Qué se construyó y por qué.** Configuracion y parsear_argumentos con argparse: offline, cache-size (entero positivo, 25 por defecto), replay, bench, semilla, vista y demo.

**Complejidad o costo.** Validar cada argumento O(L) en su longitud.

## Prompt 15 — Controlador de comandos y coordinación de servicios

> **Prompt**
>
> Implementa ControladorJuego para interpretar los comandos del usuario y coordinar JuegoService con la vista.
>
> Debe permitir:
>
> - Consultar estado, criptas, puntajes, inventario, ayuda y bitácora.
> - Iniciar una cripta y terminar la sesión.
> - Moverse, abrir puertas, atacar, esperar y recoger objetos.
> - Usar, equipar, soltar y seleccionar objetos del inventario.
> - Recorrer el inventario y solicitar vistas ordenadas.
> - Ejecutar el retroceso mediante un pergamino.
> - Solicitar guardado y carga.
>
> Valida los argumentos antes de delegar y admite rutas entre comillas. Cada acción debe ejecutarse una sola vez.
>
> Mantén las reglas, el reloj virtual y los eventos bajo responsabilidad del motor. Agrega pruebas con pytest para comprobar comandos válidos, rechazos y conservación del estado ante entradas inválidas.

**Qué se construyó y por qué.** ControladorJuego interpreta los comandos, valida los argumentos antes de delegar y coordina JuegoService con la vista. Cada acción se ejecuta una sola vez y las reglas siguen en el motor.

**Complejidad o costo.** Leer, analizar y validar un comando O(L) en su longitud, sin contar la espera del usuario ni la operación ejecutada, cuyo costo depende de la acción delegada.

## Prompt 16 — Consultas de puntajes con ordenamiento adaptativo

> **Prompt**
>
> Para consultar los resultados de Cripta quiero reutilizar OrdenadorAdaptativo. Agrega listar_ordenados(campo) a RepositorioPuntajes conservando registrar_resultado(resultado) y listar().
>
> Implementa lo necesario para:
>
> - Ordenar por acciones_ejecutadas, enemigos_derrotados o reloj_final.
> - Validar que el criterio pertenezca a los campos permitidos.
> - Comprobar que los valores sean enteros no negativos, sin aceptar booleanos.
> - Devolver los resultados en orden ascendente.
> - Conservar el orden relativo de los empates.
> - Mantener intactos el archivo y los registros originales.
>
> En ControladorJuego permite utilizar puntajes con un criterio opcional. Sin argumento debe conservarse el orden de registro. Reutiliza los algoritmos propios, sin utilizar sorted() ni list.sort().

**Qué se construyó y por qué.** listar_ordenados(campo) reutiliza OrdenadorAdaptativo sobre acciones_ejecutadas, enemigos_derrotados o reloj_final, valida enteros no negativos (sin booleanos) y conserva el orden de los empates gracias a la estabilidad.

**Complejidad o costo.** Ordenar con el costo de Insertion O(n + I) o Merge O(n log n), según el caso; leer el archivo O(n).

## Prompt 17 — Servicio de inventario, equipo y consumibles

> **Prompt**
>
> Implementa ServicioInventario utilizando Inventario, las fichas de catálogo y el historial reversible existentes.
>
> Debe permitir:
>
> - Recoger y soltar una instancia concreta.
> - Equipar como máximo un arma y una armadura.
> - Sustituir el equipo anterior sin eliminarlo del inventario.
> - Mover al frente el objeto equipado.
> - Aplicar y retirar los bonos correspondientes.
> - Usar pociones, antídotos y antorchas según sus fichas.
> - Consultar vistas ordenadas sin alterar el orden real.
> - Registrar los cambios necesarios para deshacer las operaciones reversibles.
> - Mantener los pergaminos fuera de la restauración de cantidades.
>
> Conecta el mismo servicio con JuegoService y MotorJuego, compartiendo jugador, inventario e historial. Reutiliza el gestor de efectos existente para los consumibles temporales y conserva las referencias de caché.
>
> Valida las operaciones antes de modificar los datos y agrega pruebas de capacidad, equipo, consumo y retroceso.

**Qué se construyó y por qué.** ServicioInventario concentra recoger, soltar, equipar (un arma y una armadura), usar consumibles y consultar vistas ordenadas, con cambios reversibles. Los pergaminos no se restauran al deshacer.

**Complejidad o costo.** Las operaciones básicas sobre el cursor cuestan O(1); el servicio completo también recorre para validar objetos, gestionar efectos y actualizar referencias, y las vistas ordenadas cuestan O(n log n).

## Prompt 18 — Medición de las estructuras del integrante 3

> **Prompt**
>
> Para evaluar las decisiones de mi parte de Cripta necesito un benchmark reproducible de inventario, lista doble, historial, bitácora y ordenamientos.
>
> Implementa mediciones para:
>
> - Insertar, recorrer y retirar el objeto seleccionado del inventario.
> - Mover un nodo al frente de la lista.
> - Registrar transacciones y revertir sus cambios.
> - Mantener los últimos 20 mensajes.
> - Comparar Insertion sort, Merge sort y la selección adaptativa.
> - Probar datos ordenados, casi ordenados e invertidos.
> - Medir criterios de ordenamiento costosos.
> - Comparar al menos una estructura implementada con una alternativa descartada.
>
> Separa la preparación de los datos del intervalo medido. Utiliza calentamiento y varias repeticiones, e informa tamaño, unidad, entorno y tiempos obtenidos.
>
> Integra estas mediciones en el ejecutor de --bench sin crear una vista ni solicitar entradas. Las implementaciones de biblioteca utilizadas como comparación deben permanecer únicamente en el benchmark.

**Qué se construyó y por qué.** benchmarks/integrante3.py, ejecutado con --bench, mide inventario, lista doble, historial, bitácora y ordenamientos con datos ordenados, casi ordenados e invertidos, con calentamiento y repeticiones. La comparación con alternativas de biblioteca vive solo en el benchmark.

**Complejidad o costo.** Reporta tamaño, unidad y tiempos reproducibles; con ellos se justificaron los umbrales (16 elementos y n desplazamientos).

## Prompt 19 — Reproducción determinista y selección al equipar

> **Prompt**
>
> Implementa EjecutorReplay para reproducir el archivo JSON Lines mediante el mismo JuegoService y MotorJuego utilizados durante una partida normal.
>
> La reproducción debe:
>
> - Validar la cabecera y todas las acciones antes de comenzar.
> - Comprobar las versiones de cripta y catálogo.
> - Utilizar una copia local compatible cuando corresponda.
> - Rechazar versiones incompatibles con un mensaje claro.
> - Restaurar la semilla indicada en la cabecera.
> - Resolver los objetivos mediante sus identificadores reales.
> - Ejecutarse sin vista, entrada interactiva ni modificación del archivo.
>
> Para EQUIPAR, conserva en el registro el identificador del objeto seleccionado, aunque los movimientos del cursor no se registren. Durante el replay selecciona la misma instancia y envía EQUIPAR al motor respetando su contrato.
>
> Conserva la lectura de registros anteriores sin objetivo e informa la línea de las acciones inválidas. Agrega pruebas de inventario, equipo, estadísticas, reloj y estado del azar.

**Qué se construyó y por qué.** EjecutorReplay reproduce el JSON Lines a través del mismo JuegoService y MotorJuego: valida cabecera y acciones antes de empezar, comprueba versiones, restaura la semilla y resuelve los objetivos por su id real. EQUIPAR registra el id del objeto seleccionado.

**Complejidad o costo.** Leer y validar los bytes del log O(b), reconstruir la partida y ejecutar las a acciones registradas; el costo total es la suma de las tres partes.

## Prompt 20 — Construcción de la partida desde la fuente de datos

> **Prompt**
>
> Implementa InicializadorPartida como una fábrica compatible con JuegoService y con las fuentes de datos existentes.
>
> Debe:
>
> - Leer los datos generales de la cripta.
> - Obtener todas las páginas de su esqueleto.
> - Construir MapaCripta y las salas con sus conexiones.
> - Crear al jugador con las estadísticas recibidas.
> - Vincular sala_actual con la instancia real de la sala inicial.
> - Crear el inventario con la capacidad declarada.
> - Preparar el contenido inicial antes de aceptar acciones.
> - Conectar el catálogo y el cargador de contenido existentes.
> - Conservar las versiones, la semilla y el presupuesto de solicitudes.
>
> Reutiliza los conversores y la estrategia de carga gradual del proyecto. No fijes cantidades de salas, identificadores o estadísticas de una cripta concreta.
>
> La fábrica debe servir tanto para partidas normales como para replay, sin depender de la vista. Valida los datos antes de publicar la partida.

**Qué se construyó y por qué.** InicializadorPartida es una fábrica: lee la cripta, obtiene todas las páginas del esqueleto, construye MapaCripta, salas, jugador e inventario y prepara el contenido inicial con el CargadorContenido (carga gradual). Sirve tanto para partidas normales como para replay.

**Complejidad o costo.** Descargar el esqueleto requiere aproximadamente ⌈s/p⌉ solicitudes (s salas, p por página); construir el mapa, resolver referencias y cargar el contenido por lotes de hasta 10 ids suman costos adicionales.

## Prompt 21 — Reconstrucción de referencias al restaurar una partida

> **Prompt**
>
> Implementa RestauradorPartida para transformar los datos entregados por GuardadoBinario en un EstadoPartida conectado.
>
> La reconstrucción debe:
>
> - Crear las salas y el mapa.
> - Crear al jugador y los enemigos.
> - Vincular cada actor con la instancia real de su sala.
> - Recuperar objetos del suelo, inventario y selección.
> - Reconectar arma y armadura sin aplicar dos veces sus bonos.
> - Relacionar los efectos activos con sus actores mediante los identificadores guardados.
> - Recuperar agenda, secuencias, reloj, rastro y estado actual del azar.
> - Conservar puertas, trampas, botín y salas con contenido pendiente.
>
> Reutiliza el formato binario y los DTO existentes. Valida referencias y tipos antes de entregar el estado.
>
> El historial anterior al guardado se descarta según el acuerdo del equipo; las acciones nuevas deben generar su propio historial. Agrega pruebas de identidad de referencias y continuidad de la simulación.

**Qué se construyó y por qué.** RestauradorPartida reconstruye un EstadoPartida conectado desde GuardadoBinario: salas y mapa, actores con su sala real, inventario, equipo sin duplicar bonos, efectos por id, agenda, secuencias, reloj, rastro y azar. El historial anterior se descarta.

**Complejidad o costo.** Crece con el tamaño del guardado y, además, con las búsquedas y validaciones de referencias que se hacen al reconstruir.

## Prompt 22 — Guardado y reanudación mediante JuegoService

> **Prompt**
>
> Conecta guardar y cargar en JuegoService y ControladorJuego utilizando GuardadoBinario y RestauradorPartida.
>
> Implementa lo necesario para:
>
> - Guardar la partida actual en la ruta indicada o predeterminada.
> - Validar la compatibilidad de las versiones necesarias.
> - Conservar el archivo anterior si falla el guardado.
> - Reconstruir una carga antes de sustituir el estado vigente.
> - Mantener la partida actual si el archivo es inválido.
> - Reconectar inventario, equipo, efectos, caché y motor.
> - Continuar utilizando el reloj y el estado del azar guardados.
> - Impedir que el guardado sobrescriba el registro activo.
>
> No ejecutes nuevamente los efectos de inicio ni sumes otra vez los bonos del equipo al cargar. Conserva la exportación parcial como operación separada.
>
> Agrega pruebas que comparen una partida continua con otra guardada y reanudada, verificando estadísticas, eventos y acciones posteriores.

**Qué se construyó y por qué.** Guardar y cargar desde JuegoService y ControladorJuego con GuardadoBinario: valida versiones, conserva el archivo anterior si falla el guardado, reconstruye antes de sustituir el estado y no ejecuta de nuevo efectos de inicio ni suma otra vez los bonos.

**Complejidad o costo.** Al menos proporcional al tamaño del estado, más las búsquedas, validaciones y ordenamientos del guardado y de la restauración.

## Prompt 23 — Mensajes legibles y consultas después del final

> **Prompt**
>
> Implementa funciones compartidas de presentación para convertir los datos del modelo en información comprensible para el jugador.
>
> Permite:
>
> - Mostrar nombres legibles de objetos, enemigos y trampas.
> - Distinguir enemigos del mismo tipo mediante numeración.
> - Identificar enemigos muertos.
> - Mostrar qué llave requiere una puerta y cuál es la sala de salida.
> - Traducir movimiento, combate, botín, efectos y finalización a mensajes.
> - Avisar cuando una puerta se cierre automáticamente o una trampa se rearme.
> - Mostrar claramente los rechazos por inventario lleno o falta de pergamino.
>
> Comparte una única BitacoraPantalla de 20 mensajes y evita insertar otra vez los mensajes al consultar estado o bitácora.
>
> Después de ganar o morir, la consola debe permitir consultar puntajes y bitácora, cargar, iniciar otra cripta o salir. Conserva el bloqueo de reemplazo durante una partida activa con historial.
>
> La presentación no debe modificar los resultados originales de las acciones ni introducir reglas nuevas.

**Qué se construyó y por qué.** presentacion_juego.py reúne funciones comunes que convierten datos del modelo en mensajes legibles (nombres, numeración de enemigos, llave de una puerta, avisos de cierre y rearme) y comparte una única BitacoraPantalla. Tras ganar o morir, la consola permite consultar, cargar, iniciar otra cripta o salir.

**Complejidad o costo.** Formatear un mensaje puede requerir buscar actores, objetos o fichas. La bitácora única la comparten el controlador y la vista; estas funciones solo generan los textos.

## Prompt 24 — Integración de inventario y controles en Pygame

> **Prompt**
>
> Integra las operaciones del integrante 3 con la vista Pygame existente, conservando sus sprites, fondos, menús, minimapa y pantalla final.
>
> La interfaz debe permitir:
>
> - Seleccionar una cripta o continuar una partida guardada.
> - Ejecutar las acciones disponibles mediante botones.
> - Recorrer el inventario y seleccionar objetos.
> - Consultar vistas ordenadas sin alterar el orden real.
> - Usar, equipar, soltar y ejecutar retroceso.
> - Mostrar equipo, efectos y los últimos 20 mensajes.
> - Identificar los enemigos y objetos con nombres legibles.
> - Guardar, salir y regresar al menú cuando corresponda.
>
> Utiliza páginas cuando las entidades o el inventario no quepan en pantalla. Conserva visible el objeto seleccionado y evita que los controles se superpongan.
>
> Los botones deben enviar los identificadores reales al controlador. Agrega pruebas gráficas con SDL en modo dummy para comprobar navegación, selección y visibilidad de controles sin modificar el modelo al dibujar.

**Qué se construyó y por qué.** VistaPygame integra botones, inventario paginado, vistas ordenadas, equipo, efectos y los últimos 20 mensajes. Los botones envían ids reales al controlador y las pruebas usan SDL en modo dummy.

**Complejidad o costo.** La paginación limita lo que se dibuja, pero la vista también recorre colecciones y dibuja el minimapa; el costo por cuadro no depende solo de las entidades visibles.

## Prompt 25 — Registro automático de cada partida y verificación del replay

> **Prompt**
>
> Conecta automáticamente RegistroPartida al iniciar cada cripta reproducible, antes de la primera acción, utilizando el flujo compartido de consola y Pygame.
>
> Implementa lo necesario para:
>
> - Crear los logs dentro de la carpeta de guardado configurada, bajo logs/.
> - Generar nombres únicos con un identificador de cripta seguro.
> - Conservar el identificador original, versiones y semilla en la cabecera.
> - Mostrar la ubicación del archivo al iniciar.
> - Evitar sobrescrituras y consultas HTTP adicionales.
> - Registrar las acciones exitosas mediante el servicio existente.
> - Permitir elegir otra ruta con registro RUTA antes de actuar.
> - Conservar la conexión anterior si falla el cambio de ruta.
> - Rechazar el cambio de registro después de la primera acción.
>
> Si falla la creación automática, informa claramente que la partida no podrá reproducirse. Al cargar una partida o iniciar un estado externo de demostración, muestra la limitación correspondiente sin crear un inicio de replay ficticio.
>
> Agrega pruebas que creen una partida sin ejecutar registro, realicen acciones y reproduzcan su log. Compara reloj, jugador, inventario, equipo, sala, azar y eventos pendientes. Comprueba también que --replay no cree otro archivo ni modifique el original.

**Qué se construyó y por qué.** Cada cripta reproducible crea su log en partidas/logs antes de la primera acción, con nombre único e id seguro; se muestra la ruta, se registran las acciones exitosas, se puede cambiar con registro RUTA antes de actuar y se rechaza el cambio después. Las pruebas reproducen el log y comparan reloj, jugador, inventario, equipo, sala, azar y eventos pendientes.

**Complejidad o costo.** Anexar cuesta O(b) en el tamaño del registro (O(1) si está acotado) y no relee el log; crear el archivo no usa red.
