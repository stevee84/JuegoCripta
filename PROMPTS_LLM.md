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
| 29 | `/speckit.specify` para terreno y cazador | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 30 | `/speckit.clarify` para terreno y cazador | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 31 | Revisión final del spec 001 | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 32 | `/speckit.plan` para terreno y cazador | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 33 | Revisión técnica de los artefactos de planificación 001 | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 34 | Impacto de integrar `origin/Steve` sobre la planificación 001 | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 35 | Impacto de integrar `origin/joshua` sobre la planificación 001 | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |
| 36 | Compatibilidad de copia y serialización de salas | Tema 12. Parte II dirigida por especificaciones | 07/11/2026 |

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

### Tema 12. Parte II dirigida por especificaciones

## Prompt 29 — `/speckit.specify` para terreno y cazador

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Crear la especificación 001-terreno-y-cazador de la Parte II
> de JuegoCripta, correspondiente a Sofía.
>
> Lee primero:
> - .specify/memory/constitution.md, sin modificarla.
> - REPARTO_PARTE2.md.
> - El PDF oficial de la Parte II en la ruta que ya verificaste.
> - PROMPTS_LLM.md y las instrucciones del comando.
>
> Trabaja en la rama Sofia. Usa explícitamente el número 001 y
> el directorio specs/001-terreno-y-cazador. Conserva la rama
> existente; no crees ni cambies de rama.
>
> Alcance normativo:
> Parte II §3.1, §3.2, §5.1, §5.2, la revisión de la agenda de
> §5.6 y los requisitos aplicables de §6.1–§6.3.
>
> La especificación debe cubrir:
> - Costo entero de salida >= 1, predeterminado 100 e igual
>   en ambos sentidos.
> - Movimiento de todos los actores con intervalo
>   max(1, costo_salida * 100 // velocidad).
> - Conservación de las reglas de las demás acciones y de los
>   comportamientos anteriores.
> - Cazador: ataque prioritario si comparte sala; de lo contrario,
>   ruta abierta de costo mínimo hacia el jugador; espera con
>   costo 100 si no existe ruta o supera su rango.
> - Movimiento de un solo paso, con el costo de la salida elegida.
> - Desempate por menor ID de la vecina que inicia una ruta mínima.
> - Conocimiento completo del esqueleto y puertas actuales,
>   independiente de la niebla y del contenido descargado.
> - Equivalencia de cada decisión con calcular desde cero en ese
>   instante, aunque se reutilicen resultados.
> - Determinismo y compatibilidad con retroceso.
> - Búsqueda con rango pequeño cuyo trabajo dependa de la región
>   dentro del rango, según §5.1.
> - Ciclos de menos de 20 ms bajo las condiciones de §6.1.
> - Comparaciones exigidas en --bench: uno/muchos cazadores,
>   rangos pequeños/grandes, cálculo individual/compartido,
>   reutilización/recálculo y puertas estables/inestables.
> - Repetición de mediciones de agenda con la carga nueva.
>
> Incluye explícitamente los siete casos de terreno y cazador del
> Apéndice B. Añade escenarios para ataque prioritario, límite
> d == rango, independencia del contenido descargado y retroceso.
>
> Asigna identificadores estables a requisitos funcionales y de
> rendimiento. Enlaza escenarios con sus requisitos.
> Describe resultados observables y criterios verificables.
>
> No incluyas nombres de clases, módulos, algoritmos ni estructuras
> de datos en spec.md: esas decisiones corresponden al plan.
> No inventes reglas para resolver ambigüedades; señálalas para
> la fase clarify y distingue lo explícito del PDF de lo pendiente.
>
> Registra este prompt real y el resultado en mi apartado de
> PROMPTS_LLM.md, indicando OpenCode y el modelo real de esta
> sesión. No inventes el modelo ni fechas de consultas anteriores.
>
> Genera únicamente los artefactos de esta fase y su checklist.
> No generes plan.md, tasks.md, pruebas ni código.
> No ejecutes constitution ni avances a implement.
> No hagas commit ni push.
>
> Al terminar, informa los archivos creados/modificados, los
> requisitos y escenarios cubiertos y las dudas para clarify.

**Qué se obtuvo.** Se creó `specs/001-terreno-y-cazador/spec.md` con 18 requisitos funcionales (FR-001–FR-018), 6 requisitos de rendimiento (PR-001–PR-006), escenarios enlazados y los siete casos del Apéndice B. También se creó su checklist de calidad y se fijó `.specify/feature.json` al directorio solicitado. La constitución se leyó y no se modificó. No se generaron plan, tareas, pruebas ni código.

**Pendiente para aclarar.** La fuente oficial no define la política ante costos inválidos o contradictorios, el dominio y tratamiento de un rango inválido, ni cómo ordenar IDs heterogéneos o no numéricos. Estos puntos quedaron señalados para `/speckit.clarify`, sin inventar reglas.

**Complejidad o costo.** Esta fase produce documentación y trazabilidad; no modifica el costo de ejecución del juego. Los límites y comparaciones de rendimiento quedan expresados como resultados medibles para la fase de planificación e implementación.

## Prompt 30 — `/speckit.clarify` para terreno y cazador

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Revisa specs/001-terreno-y-cazador/spec.md contra el PDF oficial,
> el contrato de datos heredado y la constitución v1.0.0.
>
> Trabaja solo sobre la especificación 001, su checklist y mi
> apartado de PROMPTS_LLM.md. Conserva la rama Sofia.
>
> Antes de formular preguntas:
> 1. Comprueba en las fuentes heredadas que reprogramar por velocidad
>    asigna una secuencia nueva y hazlo explícito en FR-006 y AC-B07.
> 2. Comprueba el dominio de id_sala. Si el contrato establece enteros,
>    elimina la duda sobre IDs heterogéneos y fija el desempate
>    numérico, sin admitir conversiones silenciosas.
> 3. Expresa las mediciones obligatorias mediante --bench.
> 4. Precisa que el retroceso restaura el estado reversible respetando
>    la excepción heredada de consumo del pergamino.
> 5. Añade escenarios de equivalencia con cálculo desde cero tras
>    apertura de puertas, cambios de velocidad y movimiento o muerte
>    de otros actores. No presupongas que todos invalidan las mismas
>    partes del cálculo.
> 6. Detalla la cobertura de agenda pendiente: insertar, extraer,
>    cancelar por ID, cancelar por actor, reprogramar y resolver
>    empates, con cientos de eventos y una alternativa comparable.
>
> Después pregunta, de una en una, únicamente lo que las fuentes no
> resuelvan: costos inválidos o contradictorios y rango ausente o
> inválido. Para cada pregunta cita la sección aplicable, distingue
> la regla explícita de la política propuesta y espera mi respuesta.
>
> Registra las preguntas y respuestas reales en la sección de
> aclaraciones y el prompt real en PROMPTS_LLM.md. No inventes
> respuestas ni decisiones del grupo.
>
> No edites la constitución ni archivos de compañeros.
> No generes plan, tareas, pruebas ni código.
> No hagas commit, push, merge ni cambio de rama.

**Qué se obtuvo.** Se verificaron contra las fuentes heredadas la secuencia nueva al reprogramar por velocidad, el dominio entero de los IDs de sala y la excepción de consumo de pergaminos. La especificación explicita esas reglas, añade equivalencia con cálculo desde cero ante aperturas, velocidad y cambios de otros actores, expresa las mediciones mediante `--bench` y detalla seis operaciones de agenda con cientos de eventos y una alternativa comparable.

**Aclaraciones reales.** Sofía acordó rechazar la cripta ante costos presentes inválidos o contradictorios, con un error que identifique la salida y los valores, sin conversión ni reemplazo silencioso; solo el costo ausente conserva 100. También acordó admitir rangos enteros mayores o iguales que 0 y rechazar fichas con rango ausente, negativo, booleano o no entero, sin convertir cadenas ni aplicar un valor predeterminado. Ambas decisiones se registraron como políticas del grupo y no como texto explícito del PDF.

**Complejidad o costo.** Esta fase solo precisa reglas y cobertura verificable. No genera plan, tareas, pruebas ni código y no cambia el costo de ejecución del juego.

## Prompt 31 — Revisión final del spec 001

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Realiza únicamente estos ajustes finales en el spec 001:
>
> 1. Ajusta SC-008 para exigir igualdad del estado reversible,
>    respetando expresamente la excepción de pergaminos de FR-016.
>    La continuación determinista se compara con el mismo estado
>    posterior al retroceso y las mismas acciones posteriores.
>
> 2. Añade escenarios de aceptación enlazados con los FR:
>    - costo presente inválido, incluidos booleanos: rechazo descriptivo;
>    - costos contradictorios entre sentidos: rechazo descriptivo;
>    - rango ausente o inválido: rechazo descriptivo;
>    - rango 0: espera con costo 100 en otra sala y ataca cuando
>      comparte sala con el jugador.
>    Pueden agruparse valores inválidos en escenarios parametrizados.
>    Conserva los identificadores existentes y agrega nuevos.
>
> 3. Explicita en FR-001 que un booleano no es un costo entero válido.
>
> Actualiza el checklist y registra esta revisión en mi apartado de
> PROMPTS_LLM.md, sin modificar entradas anteriores ni de compañeros.
> No generes plan, tareas, pruebas ni código.
> No hagas commit, push ni merge.
>
> Devuelve solo el diff de estos ajustes y el estado de Git.

**Qué se obtuvo.** SC-008 exige igualdad del estado reversible, conserva la excepción de pergaminos de FR-016 y compara continuaciones desde el mismo estado posterior al retroceso con las mismas acciones. Se añadieron AC-019–AC-023 para costos inválidos —incluidos booleanos—, costos contradictorios, rango ausente o inválido y los dos resultados de rango 0. FR-001 excluye expresamente los booleanos y el checklist registra toda la cobertura.

**Complejidad o costo.** Revisión documental sin cambios en plan, tareas, pruebas, código ni ejecución del juego.

## Prompt 32 — `/speckit.plan` para terreno y cazador

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Planifica exclusivamente specs/001-terreno-y-cazador, trabajando
> en la rama Sofia y conservando la numeración 001.
>
> Lee primero:
> - La constitución v1.0.0, sin modificarla.
> - El spec 001 y su checklist.
> - El PDF oficial de la Parte II.
> - REPARTO_PARTE2.md.
> - Los specs 002 y 004 para identificar dependencias.
> - El código actual relacionado con mapa, movimiento, enemigos,
>   agenda, efectos de velocidad, cambios reversibles y --bench.
>
> Usa los scripts PowerShell existentes mediante el puente a Windows,
> como ya verificamos. No cambies de rama ni regeneres la configuración.
>
> Genera plan.md y los artefactos asociados de esta fase, incluyendo
> research.md, data-model.md y propuestas de contratos entre partes.
>
> El plan debe:
>
> 1. Enlazar cada decisión con los FR y PR que atiende. No introducir
>    reglas nuevas. Si descubres una contradicción o ambigüedad,
>    señálala antes de modificar la especificación.
>
> 2. Comparar alternativas de rutas ponderadas: búsqueda individual
>    limitada por rango y cálculo compartido hacia el jugador.
>    Justificar una elección provisional y definir las mediciones que
>    podrían cambiarla. No presentar hipótesis como resultados medidos.
>
> 3. Garantizar el desempate por menor ID de la primera vecina,
>    independientemente del orden de descubrimiento. Explicar por qué
>    el procedimiento elegido siempre produce ese resultado.
>
> 4. Incluir el costo completo de cada consulta: preparación de
>    estructuras auxiliares, búsquedas, limpieza e invalidación.
>    Evitar inicializar o recorrer todo el mapa por cada cazador de
>    rango pequeño. Analizar tiempo y memoria con variables definidas.
>
> 5. Examinar el índice de salas de MapaCripta y comparar conservar la
>    búsqueda lineal con reutilizar TablaHashImpl propia. Mantener el
>    orden determinista de recorrido y las referencias de las salas.
>    Distinguir costos esperados, amortizados y de peor caso.
>
> 6. Definir qué información depende de puertas, objetivo, posición
>    del cazador y velocidades; qué cambios la invalidan y cuáles no.
>    Incluir apertura, cierre automático, movimiento, muerte y retroceso.
>    Toda reutilización debe equivaler a calcular desde cero.
>
> 7. Integrar costos de movimiento para todos los actores, sin alterar
>    las demás acciones. Conservar la reprogramación proporcional y
>    la asignación de una secuencia nueva al cambiar velocidad.
>
> 8. Separar el estado reversible del juego de los cálculos derivados.
>    Explicar cómo evitar resultados obsoletos después de un retroceso
>    y cómo colaborar con la línea de tiempo de Joshua sin copiar
>    estados completos por acción.
>
> 9. Proponer contratos para acordar:
>    - Con Steven: costos y rango validados, y acceso al cálculo de
>      rutas para «ir a», usando exclusivamente su mapa conocido.
>    - Con Joshua: cambios reversibles y reconstrucción histórica.
>    Identificarlos como propuestas pendientes de acuerdo, no como
>    contratos ya aceptados. No modificar sus archivos.
>
> 10. Diseñar la medición desde --bench: uno/muchos cazadores,
>     rangos pequeños/grandes, cálculo individual/compartido,
>     reutilización/recálculo y puertas estables/inestables.
>     Incluir el ciclo completo de menos de 20 ms bajo la referencia
>     oficial, diferenciando escenarios sintéticos de la referencia.
>     Incluir las seis operaciones de agenda y alternativas comparables.
>     Aprovechar el benchmark real existente cuando corresponda.
>     Excluir red y renderizado; no ocultar trabajo necesario del ciclo
>     fuera del cronómetro.
>
> 11. Proponer pruebas para todos los escenarios del spec, con sus
>     identificadores, incluyendo los siete casos del Apéndice B.
>     Definir cómo contrastar resultados con una referencia independiente
>     y cómo comprobar reversión y determinismo.
>
> 12. Usar estructuras propias. Respetar las prohibiciones de dict y
>     set como índices o cachés, heapq, bisect, collections y bibliotecas
>     de grafos/rutas en los problemas evaluados. Revisar la constitución
>     y las pruebas de restricciones antes de proponer dependencias.
>
> Delimita archivos de Sofía y puntos de integración de compañeros.
> Registra el prompt real y el resultado en mi apartado de PROMPTS_LLM.md,
> con OpenCode y el modelo real de la sesión.
>
> No generes tasks.md ni implementes código o pruebas.
> No edites la constitución ni los specs de mis compañeros.
> No hagas commit, push, merge ni cambio de rama.
>
> Al finalizar informa:
> - artefactos creados;
> - decisiones provisionales y alternativas;
> - contratos que debemos acordar;
> - riesgos o cuestiones pendientes antes de generar tareas.

**Qué se obtuvo.** Se generó el plan de 001 con trazabilidad a FR/PR, análisis de costo y memoria, prueba del desempate por primera vecina y límites de propiedad. La elección provisional es una búsqueda individual limitada por rango con estructuras propias y auxiliares perezosos; el cálculo inverso compartido y la reutilización quedan como alternativas que solo podrán habilitarse con evidencia de `--bench`. También se diseñaron el índice propio de salas, la invalidación de derivados, la integración de costos/velocidad/reversión, la matriz completa de mediciones y la cobertura propuesta de los 30 escenarios.

**Artefactos y acuerdos.** Además de `plan.md`, se crearon `research.md`, `data-model.md`, `quickstart.md` y dos propuestas pendientes: con Steven para validar costo/rango y compartir rutas sin salir del mapa conocido, y con Joshua para cambios reversibles, reconstrucción histórica e invalidación de derivados. No se modificaron la constitución, los specs de compañeros, código ni pruebas; tampoco se creó `tasks.md`.

**Complejidad o costo.** La ruta individual se diseña con costo esperado O((V_R+E_R) log V_R) y memoria O(V_R), incluyendo auxiliares de la consulta. La alternativa compartida cuesta O((V_L+E_L) log V_L) más la selección de los cazadores; la elección final y cualquier umbral adaptativo quedan pendientes de medición completa.

## Prompt 33 — Revisión técnica de los artefactos de planificación 001

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Revisa únicamente los artefactos de planificación de 001:
>
> 1. Define cómo se actualizan las prioridades del montículo:
>    una entrada por sala con actualización, o entradas duplicadas
>    descartadas al extraer. Ajusta tiempo, memoria y peor caso al
>    mecanismo elegido. No atribuyas operaciones al montículo actual
>    sin comprobar que existen.
>
> 2. Distingue salas fijadas, descubiertas y frontera almacenada.
>    Incluye todas en las cotas y explica cómo el límite de rango
>    evita trabajo innecesario fuera de la región pertinente.
>
> 3. Corrige la estrategia del oráculo: compara decisiones y costos;
>    el trabajo y el orden interno pueden diferir y se miden aparte.
>
> 4. Precisa cómo agregar_sala sustituye una sala conservando su
>    posición y cómo se actualizan las referencias entrantes.
>    Declara el costo real de esa operación, aunque siga siendo lineal.
>    No es obligatorio optimizar una operación infrecuente.
>
> 5. Revisa las declaraciones PASS y “sin incógnitas”: distingue
>    comprobaciones satisfechas, acuerdos pendientes y decisiones
>    provisionales que dependen de mediciones.
>
> 6. Registra correctamente los entornos: la suite local previamente
>    validada usó .venv con Python 3.12.10; el soporte mínimo es 3.11.
>    No confundas el Python general con el entorno del proyecto.
>
> Conserva las reglas del spec y actualiza coherentemente plan.md,
> research.md y data-model.md cuando corresponda. Registra esta
> revisión en mi apartado de PROMPTS_LLM.md.
>
> No generes tasks.md, código ni pruebas. No hagas commit ni push.
> Devuelve el diff de las correcciones.

**Qué se obtuvo.** El plan fija entradas duplicadas e inmutables en `MonticuloMinimo`: cada mejora inserta otra entrada y las obsoletas se descartan al extraer, sin atribuir una actualización de prioridad inexistente. Las cotas distinguen salas fijadas y descubiertas, salidas examinadas, inserciones totales, frontera máxima y limpieza final. El oráculo compara solo decisión y costos observables; el trabajo se instrumenta aparte.

**Precisiones adicionales.** La sustitución de una sala conserva su posición mediante búsqueda lineal y revincula referencias entrantes, con O(V+E) esperado. Los estados constitucionales distinguen comprobaciones de diseño, acuerdos pendientes y elecciones sujetas a `--bench`. El entorno de validación queda registrado como `.venv` con Python 3.12.10 y soporte mínimo 3.11.

**Complejidad o costo.** Para una consulta individual, el costo esperado completo es O(E_R + P_R log max(2, Q_R) + Q_fin) y la memoria O(D_R + Q_R); el peor caso incorpora colisiones de la tabla propia y hasta O(E_R) entradas duplicadas.

## Prompt 34 — Impacto de integrar `origin/Steve` sobre la planificación 001

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Se integró origin/Steve en Sofia. La suite completa pasó con:
> .venv/Scripts/python.exe -m pytest -q -rs --tb=short
> Resultado: 1071 passed, sin omisiones.
>
> Revisa el impacto del merge sobre la planificación de
> specs/001-terreno-y-cazador.
>
> 1. Lee el código actualizado, especialmente main.py,
>    datos/decodificador_datos.py, datos/guardado_binario.py,
>    service/inicializador_partida.py, service/restaurador_partida.py,
>    logica/verificador_resolubilidad.py y la conexión actual de --bench.
>
> 2. Contrasta esos cambios con plan.md, research.md, data-model.md,
>    quickstart.md y las dos propuestas de contracts/ de 001.
>
> 3. Actualiza únicamente los documentos de planificación de 001
>    que hayan quedado desactualizados. Identifica la versión actual
>    del guardado y los puntos concretos de integración, sin modificar
>    código ni fijar unilateralmente responsabilidades de compañeros.
>
> 4. Comprueba si el spec 002 actualizado resolvió las observaciones
>    sobre fallo de verificación y divulgación de información frente
>    a la niebla. Informa lo encontrado; no lo edites.
>
> 5. Mantén las propuestas con Steven y Joshua como pendientes de
>    aceptación. No presentes el merge como aprobación de contratos.
>
> Registra esta revisión y su resultado en mi apartado de
> PROMPTS_LLM.md, conservando las entradas de todos.
>
> No regeneres el plan ni cambies las reglas de spec.md.
> No generes tasks.md, código ni pruebas.
> No hagas commit, push, merge ni cambio de rama.
>
> Devuelve los hallazgos, los archivos modificados y el diff de
> los ajustes. Si no hace falta modificar algo, indícalo.

**Qué se encontró.** El merge no implementa costo, rango ni rutas de 001. Sí concreta sus fronteras: el guardado vigente es v9 y persiste el informe de 002; el decodificador tiene caminos separados para datos externos y reconstruidos; el inicializador reúne/vincula el esqueleto y verifica 002 antes del contenido; y el restaurador publica un estado nuevo con agenda reconstruida e historial vacío. `main.py --bench` concatena proveedores de Steven y adicionales mediante `benchmarks.integrante3.ejecutar`, pero todavía no conecta el benchmark real de ciclo de 001 ni las seis operaciones de agenda.

**Resultado documental.** Se actualizaron los artefactos de 001 con los puntos exactos de integración y la línea base `1071 passed`, sin presentar el merge como acuerdo. Ambas propuestas conservan sus criterios sin marcar. Se confirmó que spec 002 corrigió el fallo de verificación —bloqueo salvo `--forzar` y estado «sin verificar»— y retiró la divulgación de contenido de rutas frente a la niebla; no se editó 002. Se anotó un borde de implementación separado: el inicializador no captura el `TypeError` que el decodificador puede emitir por un ID de sala de llave con tipo inválido.

**Persistencia y cuestiones pendientes.** `GuardadoBinario.VERSION = 9`; costo/rango no se serializan y su incorporación requiere acordar una nueva versión. La constante y el arranque dicen v9, aunque una línea de ayuda aún dice v8. Siguen pendientes la asignación de responsabilidades con Steven, el contrato de invalidación con Joshua y la evidencia de `--bench` para decidir la estrategia.

## Prompt 35 — Impacto de integrar `origin/joshua` sobre la planificación 001

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Acabo de integrar la rama de Joshua en Sofia. Revisa el estado
> actual con Git de Windows. Si hay conflictos, detente e informa;
> no los resuelvas ni descartes cambios.
>
> Lee la implementación, plan y contratos de 004 incorporados por
> el merge, especialmente la interfaz de cambios reversibles,
> la reconstrucción histórica y el contrato de guardado.
>
> Actualiza únicamente la planificación de 001 y su propuesta con
> Joshua para reflejar lo que realmente quedó integrado:
>
> 1. Registrar las mutaciones canónicas mediante las transacciones
>    y mecanismos acordados con Joshua.
>
> 2. Mantener las cachés de rutas fuera de EstadoPartida y de los
>    objetos alcanzables desde las transacciones guardadas.
>    Pueden pertenecer al motor o al servicio de rutas.
>
> 3. historia no requiere invalidación: no ejecuta decisiones de
>    001 y debe restaurar el estado vivo sin alterar sus cachés.
>    No introducir observadores de cambios de atributos.
>
> 4. Invalidar explícitamente los derivados después de un retroceso
>    exitoso y al iniciar/cargar un estado.
>
> 5. Usar la interfaz real de deshacer/rehacer si ya existe.
>    Comprobar los requisitos de deepcopy y pickle para cambios
>    nuevos, sin referencias al motor ni a cachés.
>    Si la interfaz todavía es propuesta, mantenerla pendiente;
>    no inventar firmas.
>
> 6. Reflejar el método de reconstrucción definido por 004:
>    hacia atrás desde el punto de control siguiente.
>    Re-simular permanece como alternativa medida, no como regla
>    de producción, salvo que los documentos integrados indiquen
>    un cambio posterior; en ese caso informa la discrepancia.
>
> 7. Registrar la aceptación condicionada de Joshua, separándola
>    de las pruebas y comprobaciones todavía no realizadas.
>
> 8. Comprobar la versión real de guardado y distinguirla de la
>    versión propuesta en contratos. Identificar nuevos puntos
>    de integración que afecten a 001.
>
> Puedes actualizar plan.md, research.md, data-model.md, quickstart.md,
> contracts/propuesta-joshua-cambios-reversibles.md y mi apartado de
> PROMPTS_LLM.md, únicamente cuando sea necesario.
>
> No cambies las reglas de spec.md ni la constitución.
> No edites código, pruebas o documentos de mis compañeros.
> No generes tasks.md ni hagas commit, push, merge o cambio de rama.
>
> Devuelve:
> - estado de Git;
> - acuerdos e interfaces encontrados;
> - archivos modificados;
> - discrepancias o pendientes;
> - si el merge añadió código que requiere verificar con pytest.

**Estado y alcance del merge.** Git de Windows informó `Sofia...origin/Sofia`, árbol limpio y ninguna ruta sin fusionar. El merge `49f8ed0` añadió únicamente artefactos de planificación de 004 y su bitácora; no añadió implementación. Por eso no se requirió ejecutar pytest solo para validar código nuevo del merge.

**Interfaces encontradas.** La interfaz real continúa siendo `CambioReversible.deshacer`, `TransaccionAccion.registrar/revertir` e `HistorialReversible.deshacer_ultimo(estado) -> bool`; no existe `rehacer`. 004 propone, todavía sin nombres o firmas, un deshacer temporal que devuelve inversos sin vaciar la transacción y avisos desde el historial a la línea. La producción reconstruirá hacia atrás desde el punto de control siguiente y rehará en `finally`; re-simular queda solo en `--bench`.

**Acuerdo condicionado.** El contrato de dependencias de 004 acepta FR-016 de 001 si todas las mutaciones observables se registran dentro de la transacción, permite cachés no observables fuera de ella y confirma que la línea no llama al cazador. Se separó ese acuerdo de lo aún pendiente: implementación, pruebas de `deepcopy`/`pickle`, inversos exactos, invalidación tras retroceso e inicio/carga y continuación determinista. `historia` no invalida ni usa observadores.

**Guardado e integración.** La versión real permanece en v9. V10 es una propuesta de 004 a Steven para serializar juntos el estado vivo y la línea; no está implementada y debe coordinarse con costo/rango. Las cachés de ruta quedan fuera de `EstadoPartida`, puntos de control, transacciones y guardado.

## Prompt 36 — Compatibilidad de copia y serialización de salas

**Herramienta:** OpenCode

**Modelo real de la sesión:** OpenAI GPT-5.6 Sol

**Fecha:** 07/11/2026

> **Prompt**
>
> Corrige exclusivamente la compatibilidad de copia y serialización
> de Sala y _ListaEnemigosSala, en la rama Sofia.
>
> Joshua detectó al copiar una partida real con deepcopy o pickle:
> AttributeError: 'Sala' object has no attribute '_enemigos_por_id'
>
> Durante la reconstrucción, append de _ListaEnemigosSala consulta
> el índice de la Sala antes de que esté restaurado. Esto bloquea
> los puntos de control de 004 y el futuro guardado v10.
>
> 1. Lee dto/sala.py y las pruebas relacionadas.
> 2. Reproduce el fallo con un estado cargado de los fixtures reales,
>    preferiblemente cripta-04, sin red.
> 3. Implementa la solución mínima y robusta. Evalúa los protocolos
>    de copia/serialización apropiados; no adoptes __reduce__ sin
>    comprobar el orden de reconstrucción, los ciclos y el memo.
> 4. Conserva el comportamiento y las firmas de la lista de enemigos,
>    sus índices y las operaciones reversibles existentes.
>
> Añade regresiones significativas que comprueben:
> - copy.deepcopy(estado).
> - pickle.loads(pickle.dumps(estado)).
> - Misma cantidad, orden e IDs de enemigos.
> - Coherencia del índice con las instancias reconstruidas.
> - Las referencias sala_actual de los actores apuntan a las salas
>   reconstruidas correctas, conservando los alias internos.
> - En deepcopy, la copia es independiente del estado original.
> - Agregar y retirar enemigos después de reconstruir mantiene
>   los índices correctos.
>
> No ocultes el problema eliminando índices del estado sin
> reconstruirlos ni introduzcas un barrido lineal en cada operación.
> No cambies reglas del juego, formatos de guardado ni código de 004.
> No implementes terreno, cazador o línea de tiempo.
>
> Modifica únicamente dto/sala.py y sus pruebas necesarias.
> Registra el prompt real y el resultado en mi apartado de
> PROMPTS_LLM.md. No cambies la constitución ni los specs.
>
> Ejecuta las regresiones y después la suite completa con el
> Python de .venv de Windows, que tiene las dependencias del proyecto.
>
> No hagas commit, push, merge ni cambio de rama.
> Devuelve causa reproducida, solución, archivos y pruebas ejecutadas.

**Causa reproducida.** Con `cripta-04` offline (50 salas y 21 enemigos), `deepcopy` restauraba la referencia `_sala` de la lista antes de que la nueva `Sala` tuviera sus índices; `pickle` repoblaba la subclase de `list` antes de restaurar incluso `_sala`. Ambos caminos fallaron en `append`/`extend` con `AttributeError`.

**Solución.** No se usó `__reduce__`. `_ListaEnemigosSala.__deepcopy__` registra primero la nueva lista en `memo`, copia el dueño y los enemigos preservando ciclos y usa `list.append` durante la construcción. Para pickle, `append` tolera únicamente la fase previa a restaurar `_sala`. `Sala.__getstate__` omite los dos índices derivados y `Sala.__setstate__` restablece el ciclo con la lista y reconstruye ambos índices una sola vez al final. Las operaciones ordinarias conservan las actualizaciones O(1) esperadas y las firmas reversibles existentes.

**Regresiones y resultado.** Se añadieron pruebas con la fixture real de `cripta-04` para `deepcopy` y la ida y vuelta de `pickle`: cantidad/orden/IDs, alias `sala_actual`, identidad de índices, independencia y extracción/restauración posterior. La ejecución final del archivo nuevo terminó en `2 passed`; la suite completa con `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` terminó en `1073 passed` en 100.85 s.

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

---

# Joshua Cabrera Bonilla — Parte II

**Herramienta:** Claude Code v2.1.317 (Claude Opus 5.5), con spec-kit 1.2.3. Los prompts se redactaron con apoyo de Claude (claude.ai) a partir del enunciado de la Parte II y de las observaciones del profesor sobre la primera parte.

| # | Tema | Fecha |
| --- | --- | --- |
| 26 | Constitución del proyecto (`/speckit-constitution`) | 02/11/2026 |
| 27 | Correcciones a la constitución antes de confirmarla | 02/11/2026 |
| 28 | Especificación de la línea de tiempo (`/speckit-specify`) | 06/11/2026 |
| 29 | Clarificación de la línea de tiempo (`/speckit-clarify`) | 06/11/2026 |
| 30 | Plan de la línea de tiempo (`/speckit-plan`) | 07/11/2026 |
| 31 | Tareas de la línea de tiempo (`/speckit-tasks`) | 07/11/2026 |
| 32 | Análisis de la línea de tiempo y correcciones (`/speckit-analyze`) | 07/11/2026 |
| 33 | Implementación de T001: medición del riesgo R3 (`/speckit-implement`) | 07/11/2026 |
| 34 | Implementación de T003 y T004: deshacer y rehacer para la línea de tiempo | 08/11/2026 |
| 35 | Implementación de T036 a T038: resolubilidad en la interfaz (002-T049 y 002-T050) | 09/11/2026 |
| 36 | Implementación de T005 y T006: el historial avisa a la línea de tiempo | 09/11/2026 |
| 37 | Implementación de T007 a T009: estructura de la línea de tiempo | 09/11/2026 |

## Prompt 26 — Constitución del proyecto (`/speckit-constitution`)

> **Prompt**
>
> /speckit-constitution Proyecto Cripta, Estructuras de Datos II-2026, segunda parte sobre el código ya entregado de la primera. Redacta la constitución en español con estos principios, cada uno con su justificación y cómo se verifica:
>
> I. Estructuras propias en los problemas evaluados. Las estructuras de datos de los problemas evaluados (agenda, índices, cachés, búsquedas de ruta, mapa conocido, resolubilidad, línea de tiempo, historial) se implementan a mano. Prohibido usar dict o set como índice, caché o tabla de búsqueda, y prohibidos heapq, bisect, collections (deque, OrderedDict, defaultdict, Counter), networkx y cualquier biblioteca de grafos o rutas. Se permiten dict para leer JSON y list como almacenamiento contiguo de bajo nivel. Prohibido sorted() y list.sort() en los ordenamientos evaluados. Las alternativas de biblioteca solo pueden aparecer en --bench como comparación. Todo plan.md o tarea que proponga una dependencia prohibida es un defecto que debe detectarse en /speckit-analyze.
>
> II. Acceso por identificador eficiente. Toda búsqueda frecuente por id (salas, actores, objetos, puertas) usa una estructura propia con acceso esperado O(1), como la tabla hash propia ya existente. No se aceptan recorridos lineales en operaciones que se ejecutan en cada turno o en cada búsqueda de ruta.
>
> III. Determinismo. Misma cripta, misma semilla y mismas acciones producen la misma partida. El modelo usa solo su instancia random.Random(semilla). La hora real y la latencia de red nunca alteran la simulación. La agenda desempata por tiempo virtual y luego por número de secuencia. Todo desempate nuevo (por ejemplo, la vecina de menor id) se define en la especificación de forma independiente del algoritmo.
>
> IV. Separación MVC. El modelo contiene las reglas y el estado. La vista solo presenta y recoge interacción, sin introducir reglas ni alterar resultados. El controlador interpreta comandos y coordina. Red y disco van detrás de adaptadores. --replay, --bench y --verificar nunca instancian la vista.
>
> V. Datos desde el servicio. Ningún dato de una cripta concreta (estadísticas, cantidades, costos, rangos, ubicaciones de llaves) se escribe en el código. Todo viene del servicio o de la fuente offline compatible. Lo persistido se invalida mediante la validación de versión existente, nunca borrando archivos a mano.
>
> VI. Presupuesto de solicitudes. Se respeta presupuesto_solicitudes, que viene de la cripta a través del contrato FuenteDatos. Toda solicitud HTTP cuenta, incluidos los reintentos y la consulta de llaves. El tiempo real de espera no avanza el reloj virtual.
>
> VII. Estado reversible sin copias completas. Todo cambio de estado del juego, incluido el conocimiento del jugador, se registra como un cambio reversible para el pergamino de retroceso (límite de 5 acciones) y para la línea de tiempo. No se implementa el retroceso con copias completas. Las únicas copias completas permitidas son los puntos de control de la línea de tiempo, como máximo uno cada K acciones del jugador. Las acciones rechazadas no consumen tiempo ni dejan cambios parciales. Las consultas (historia, mapa, estado) no modifican el estado ni el historial.
>
> VIII. Contratos estables y cambios mínimos. Se conservan nombres, firmas, constructores y archivos que usan otros integrantes. La identidad de las instancias se mantiene por sus ids reales. Antes de modificar un componente compartido se identifican sus consumidores y se acuerda el cambio en el plan.md. Se preservan las decisiones ya entregadas: carga gradual de contenido, catálogo vivo con protección de fichas activas, lotes de hasta diez ids, registro de partida JSON Lines con ids estables y creación automática del log, y guardado binario versionado.
>
> IX. Rendimiento medido. Toda afirmación de rendimiento o complejidad se respalda con --bench. Cada medición compara la estructura elegida contra al menos una alternativa descartada, separa la preparación del intervalo cronometrado, usa calentamiento y repeticiones, y genera criptas sintéticas deterministas por semilla. Las mediciones deben estar conectadas a --bench. Un benchmark que ningún punto de entrada ejecuta no cuenta como evidencia. Las operaciones de cada subsistema (no solo la operación masiva) se miden con cargas realistas: ciclos sobre criptas reales y operaciones de punta a punta, no solo la estructura aislada. Límites: ciclo de eventos de 20 ms con decenas de cazadores, resolubilidad de 200 ms, historia de 50 ms con 5 000 acciones, paso de «ir a» de 5 ms.
>
> X. Especificación primero y trazabilidad. Cada capacidad tiene spec.md confirmado en Git antes de su código. spec.md describe reglas, historias, escenarios y requisitos numerados (FR-xxx), sin nombrar estructuras, clases ni módulos. plan.md elige estructuras y no inventa reglas. Cada tarea cita sus FR y cada prueba cita el FR que verifica. Cada caso del Apéndice B es un escenario con prueba o con un partida.log. Si la especificación estaba mal, se corrige primero la especificación y luego el código, en commits separados. Cada comando de spec-kit con texto propio se registra en PROMPTS_LLM.md.
>
> XI. Pruebas. Se mantienen unittest y pytest. Las pruebas nuevas no rompen las existentes. Se distingue entre pruebas aprobadas, omitidas, con fixtures de API y contra el servicio en línea.
>
> Gobernanza: la constitución prevalece sobre spec, plan y tareas. Una enmienda requiere acuerdo de los tres integrantes, versión semántica y fecha. /speckit-analyze verifica el cumplimiento de cada principio antes de implementar. Stack: Python 3.11 o superior, sin dependencias nuevas salvo requests y pygame ya existentes.

**Qué se obtuvo.** `.specify/memory/constitution.md` v1.0.0 con los 11 principios (cada uno con justificación y verificación), restricciones técnicas, flujo de trabajo y gobernanza. Recoge los principios de §2.3 y las prohibiciones de §6.2 del enunciado, las decisiones ya entregadas en la Parte I (presupuesto en `FuenteDatos`, carga gradual, catálogo vivo, logs automáticos, guardado versionado) y, como principios II y IX, las observaciones del profesor sobre la primera parte (búsqueda de salas lineal y benchmarks no conectados a `--bench` o sin medir operaciones completas).

**Qué hubo que corregir.** La revisión contra el enunciado encontró cinco imprecisiones, corregidas en el Prompt 27 antes del primer commit.

## Prompt 27 — Correcciones a la constitución antes de confirmarla

> **Prompt**
>
> Corrige .specify/memory/constitution.md sin cambiar la versión 1.0.0 ni nada más:
> 1. Principio VII: aclara que la prohibición de copias completas aplica a copias en memoria usadas como mecanismo de retroceso o de línea de tiempo; el archivo de guardado de partida no cuenta como copia prohibida.
> 2. Restricciones técnicas: agrega a los puntos de entrada --forzar, --checkpoint-cada K y --replay partida.log --hasta t.
> 3. Principio IX, límites: ciclo de eventos de 20 ms entre dos decisiones del jugador, en la cripta de referencia con decenas de cazadores; resolubilidad de 200 ms en la cripta publicada más grande; historia de 50 ms con al menos 5 000 acciones del jugador y K por defecto; paso de «ir a» de 5 ms con el mapa conocido completo de la cripta de referencia. Agrega que estos valores pueden ajustarse por enmienda del enunciado.
> 4. Principio XI, verificación: la suite completa se ejecuta con pytest, que también ejecuta las pruebas escritas con unittest.
> 5. Principio V, verificación: los datos persistidos de la cripta con versión incompatible se invalidan y se vuelven a solicitar; un archivo de partida de la primera parte se reporta como incompatible o se migra explícitamente, nunca se carga en silencio.
> 6. En el Sync Impact Report, elimina la frase que dice que el informe se elimina antes de confirmar.
> No modifiques otros archivos.

**Qué se obtuvo y por qué.** Se corrigieron cinco puntos que contradecían el enunciado o prometían algo que el proyecto no hace: el guardado de partida parecía una copia prohibida (§3.6); faltaban banderas de §7.2; los límites no tenían las condiciones de §6.1; se afirmaba ejecutar dos ejecutores de pruebas; y se trataba igual el caché de la cripta que un archivo de partida de la Parte I (Apéndice B). La versión se mantuvo en 1.0.0 porque las correcciones se hicieron antes de ratificarla en Git.

## Prompt 28 — Especificación de la línea de tiempo (`/speckit-specify`)

> **Prompt**
>
> /speckit-specify Usa el número de feature 004 y el nombre corto linea-de-tiempo: la carpeta debe quedar specs/004-linea-de-tiempo/. No crees ramas de Git.
>
> Capacidad: línea de tiempo y puntos de control de Cripta (enunciado de la Parte II, §3.6, §5.5, §6.1, §7.3 y Apéndice B). Describe solo QUÉ debe hacer el juego y por qué. No nombres estructuras de datos, clases, módulos ni archivos de código. Respeta la constitución v1.0.0, en especial los principios III, IV, VII, IX y X.
>
> Contexto. El pergamino de retroceso de la Parte I sigue limitado a 5 acciones. La línea de tiempo es independiente: permite consultar, sin modificar la partida, el estado en cualquier instante desde el inicio.
>
> Reglas que la especificación debe recoger:
> 1. Estado en el instante t: el estado después de ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla. Si varios eventos ocurren en el mismo t, se muestra el estado después de todos ellos.
> 2. Acción número k: historia #k muestra el estado justo antes de la acción número k del jugador. Solo cuentan las acciones aceptadas que siguen en la línea de tiempo (las rechazadas y las revertidas con pergamino no cuentan).
> 3. El resumen de una consulta muestra como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido por el jugador en ese momento.
> 4. Una consulta no consume tiempo virtual, no es una acción del jugador, no se registra en partida.log y no altera ningún estado del juego, ni el historial de retroceso, ni el estado del generador aleatorio.
> 5. Se rechaza, con un mensaje y sin efectos: historia <t> con t mayor que el reloj actual; un t que no sea un entero mayor o igual que 0; un #k fuera del rango de acciones existentes; una consulta sin partida iniciada.
> 6. Las acciones revertidas con un pergamino dejan de existir en la línea de tiempo: la línea describe la historia de la partida tal como quedó. Ese recorte no debe recorrer toda la historia.
> 7. --replay partida.log --hasta <t> reproduce la partida hasta t e imprime el mismo resumen, sin instanciar la vista. Si t es posterior al final de la partida, muestra el estado final e indica que la partida terminó antes. Sin --hasta, --replay se comporta como en la Parte I.
> 8. Puntos de control: se permite guardar copias completas del estado, pero no más de una cada K acciones del jugador. K se configura con --checkpoint-cada K (entero mayor o igual que 1; otro valor se rechaza al arrancar). El valor por defecto lo escoge el grupo y se justifica con mediciones. Fuera de los puntos de control solo se almacena la información necesaria para reconstruir los cambios.
> 9. Una consulta de cualquier instante no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. Ubicar el punto de control más cercano al instante pedido es una búsqueda frecuente y su costo no debe crecer linealmente con la longitud de la partida.
> 10. La reconstrucción puede hacerse hacia adelante desde un punto de control (re-simulando) o hacia atrás desde el estado actual (invirtiendo cambios); la elección se documenta con evidencia. Si se re-simula, el punto de control incluye el estado del generador aleatorio.
> 11. La memoria total crece con la cantidad de cambios ocurridos más un punto de control cada K acciones; nunca con «acciones por tamaño del estado».
> 12. Todo el estado que otras capacidades agregan (costos y cazadores de la spec 001, conocimiento del jugador y mapa conocido de la spec 003) forma parte de lo que la línea de tiempo reconstruye.
> 13. Persistencia: guardar y cargar la partida conserva la línea de tiempo completa; después de cargar, toda consulta da el mismo resultado que antes de guardar. Como contrato con el guardado (sin definir el formato), el archivo debe conservar: los puntos de control, la información de cambios necesaria para reconstruir cualquier instante desde el inicio, el valor de K con que se crearon, el número de acciones y el reloj de cada punto de control, y el estado del generador aleatorio si la reconstrucción re-simula.
> 14. Un archivo de partida de la Parte I se reporta como incompatible o se migra de forma explícita; nunca se carga en silencio.
> 15. La interfaz permite consultar historia <t> e historia #k y ver el resumen.
>
> Historias de usuario (con prioridad):
> - P1: Como jugador, consulto el estado en un instante pasado t para revisar qué pasó.
> - P1: Como jugador, consulto el estado justo antes de mi acción número k.
> - P2: Como jugador, uso un pergamino de retroceso y la línea de tiempo deja de mostrar lo revertido.
> - P2: Como evaluador, reproduzco un partida.log hasta un instante t sin abrir la vista.
> - P3: Como desarrollador, ajusto la frecuencia de puntos de control con --checkpoint-cada K y mido su efecto.
> - P3: Como jugador, guardo y cargo la partida sin perder la línea de tiempo.
>
> Escenarios de aceptación obligatorios (Apéndice B), en formato Given/When/Then:
> 1. historia <t> con t mayor que el reloj actual: se rechaza.
> 2. historia después de usar un pergamino: no muestra las acciones revertidas.
> 3. Varios eventos ocurren en el mismo instante t: historia <t> muestra el estado después de todos ellos.
> 4. historia no consume tiempo virtual, no se registra en partida.log y no modifica el historial de retroceso.
> 5. --replay partida.log --hasta t con t posterior al final de la partida: muestra el estado final e indica que la partida terminó antes.
> 6. Se carga un archivo de partida de la primera parte: se reporta la incompatibilidad de formato o se migra explícitamente; nunca se carga en silencio.
> Agrega también escenarios para: historia #1 (estado inicial), historia #k igual a la acción siguiente (estado actual), K = 1, y consultar después de guardar y cargar.
>
> Requisitos de rendimiento y medición (medibles):
> - historia responde en menos de 50 ms en una partida de al menos 5 000 acciones del jugador con el K por defecto, medido en el equipo local sin red ni renderizado (§6.1).
> - --bench mide memoria y tiempo de consulta para al menos tres valores de K y para la alternativa sin puntos de control, y con eso se justifica el K por defecto (§5.5, §6.3).
> - --bench repite con la carga nueva las mediciones de la Parte I relacionadas (§5.6): un retroceso con pergamino medido de punta a punta (reloj, agenda, rastro, puertas, trampas, inventario) frente a la alternativa de copia completa; una reproducción completa de partida.log y el rechazo por versión incompatible; y la vista ordenada del inventario por peso, valor y nombre sin alterar el orden real, más el rechazo al llegar al máximo de inventario.
>
> Fuera de alcance: cambiar el límite de 5 acciones del pergamino; usar la línea de tiempo para volver a jugar desde un instante pasado.
>
> Marca como [NEEDS CLARIFICATION] lo que el enunciado no defina, por ejemplo: si el uso del pergamino cuenta como acción número k; qué muestra historia <t> justo en el instante del retroceso; qué K se usa al cargar una partida guardada con otro --checkpoint-cada; si historia se permite con la partida terminada.

**Qué se obtuvo.** `specs/004-linea-de-tiempo/spec.md` con 6 historias de usuario, los 6 casos de línea de tiempo del Apéndice B como escenarios de aceptación (US1-1, US1-2, US1-3, US3-1, US4-2 y US5-3), casos borde, 31 requisitos (FR-001 a FR-031) y 6 criterios de éxito, entre ellos el límite de 50 ms de §6.1. Además, `specs/004-linea-de-tiempo/checklists/requirements.md` con la validación de calidad de spec-kit. Antes de redactar el prompt se leyó, sin modificarlo, el código que usará la capacidad (motor, historial de retroceso, cambios reversibles, replay, registro de partida y guardado v8), para no especificar algo que contradiga lo existente. El texto del prompt lo redactó Claude Code y Joshua lo aprobó antes de ejecutarlo.

**Qué hubo que corregir.** El comando dejó dos puntos marcados como [NEEDS CLARIFICATION]. Joshua pidió elegir la opción más conforme al enunciado y se tomó la opción A en ambos: (1) FR-012, el uso del pergamino no cuenta como acción #k y su consumo forma parte de la historia tal como quedó (§3.6); (2) FR-030, al cargar una partida se conserva el K con que se guardó, para que siga valiendo que una consulta no aplica ni deshace más de K acciones. Se ajustaron los escenarios US3-3 y US5-2 en consecuencia.

## Prompt 29 — Clarificación de la línea de tiempo (`/speckit-clarify`)

> **Prompt**
>
> /speckit-clarify Revisa specs/004-linea-de-tiempo/spec.md contra el enunciado de la Parte II (§3.6, §5.5, §6.1, Apéndice B) y la constitución v1.0.0. Las preguntas y respuestas deben quedar registradas en la especificación, en español.

**Qué se obtuvo.** El comando hizo 4 preguntas y Joshua aceptó la opción recomendada en las cuatro: `historia` está disponible en consola y en pygame con el mismo resumen (FR-008); `--replay --hasta` imprime el mismo texto, líneas y orden que `historia` (FR-009); el mapa conocido del resumen tiene el mismo contenido que el comando de mapa conocido de la spec 003 (FR-004); y las estadísticas del resumen son vida actual y máxima, ataque, defensa y velocidad efectivos (FR-004). Las preguntas y respuestas quedaron en la sección `## Clarifications` de `spec.md`.

**Qué hubo que corregir.** Nada en las respuestas. Al integrar FR-009 se agregó un valor por defecto que no se preguntó: un `--hasta` inválido, o sin `--replay`, se rechaza antes de reproducir. Se eliminó la suposición sobre el formato de `--replay --hasta`, porque la clarificación la reemplazó.


---

## Prompt 30 — Plan de la línea de tiempo (`/speckit-plan`)

> **Prompt**
>
> /speckit-plan Plan de specs/004-linea-de-tiempo. Elige estructuras propias (sin dict/set como índice, heapq, bisect, collections), compara con alternativas descartadas, decide reconstrucción hacia adelante o hacia atrás con evidencia prevista, propone K por defecto a confirmar con --bench, lista consumidores de componentes compartidos (motor, historial, controlador, vista, main, guardado) con cambios mínimos, define el contrato con Steven (guardado v10 y mapa conocido de la 003) y con Sofía (cambios reversibles del cazador), e incluye las tareas de interfaz T049 y T050 de la spec 002 (FR-013, FR-014). No modifiques código de Steven ni de Sofía. Todo en español.

**Qué se obtuvo.** `plan.md`, `research.md`, `data-model.md`, `quickstart.md` y tres contratos en `specs/004-linea-de-tiempo/contracts/` (`cli-historia.md`, `guardado-v10.md` y `dependencias.md`). Decisión principal, provisional hasta medirla en `--bench`: reconstruir **hacia atrás** desde el punto de control siguiente. Cada punto de control copia juntos el estado y las transacciones de su ventana, porque los cambios guardan referencias a los objetos vivos. Se ubica el punto de control por aritmética y el instante t por búsqueda binaria propia. K por defecto provisional: 50, a medir con K = 10, 50 y 200 y sin puntos de control. La línea se engancha en el historial reversible, así que no se modifica el motor de Sofía. El guardado v10 queda como contrato para Steven, sin tocar su archivo.

**Qué hubo que corregir.** Antes de escribir el plan se leyó el código y aparecieron tres cosas que el enunciado no dice. (1) Los cambios solo saben deshacerse y apuntan a objetos vivos: por eso se descartó re-simular hacia adelante como mecanismo principal, ya que además pediría contenido de salas al servicio. (2) Recoger, soltar y consumir un pergamino no se registran como cambios, así que se agregó un registro «solo línea de tiempo». (3) Una primera versión ubicaba el punto de control con ⌈k / K⌉; se corrigió a ⌈(k − 1) / K⌉, porque el punto de control de la acción m guarda el estado de antes de la acción m + 1. Quedaron dos desviaciones documentadas en la tabla de complejidad: la copia de trabajo temporal de cada consulta y un posible punto de control extra después de cargar; la segunda se consultará con el grupo.

## Prompt 31 — Tareas de la línea de tiempo (`/speckit-tasks`)

> **Prompt**
>
> /speckit-tasks Genera tasks.md para specs/004-linea-de-tiempo en español. Cada tarea cita los FR que atiende; cada prueba cita el FR que verifica; los 6 casos del Apéndice B tienen prueba. Primera tarea: medir el costo de copiar el estado (riesgo R3 del plan). Incluye T049 y T050 de la spec 002. Marca como dependientes las tareas que necesitan el guardado v10 de Steven o la spec 003. Bloques pequeños, sin tocar código de Steven ni de Sofía.

**Qué se obtuvo.** `specs/004-linea-de-tiempo/tasks.md` con 50 tareas en 12 fases: preparación (T001 mide el riesgo R3 antes de construir), base, una fase por historia de usuario, interfaz §7.3 con T049 y T050 de la spec 002, mapa conocido, mediciones y cierre. Los 6 casos del Apéndice B tienen prueba (tabla al final del archivo). Tres tareas quedan marcadas como dependientes: T034 y T035 del guardado v10 de Steven y T040 de la spec 003.

**Qué hubo que corregir.** La revisión automática de trazabilidad encontró que FR-020 (estado del azar si se re-simula) no tenía tarea; se agregó a T042, que es la única parte que re-simula.

## Prompt 32 — Análisis de la línea de tiempo y correcciones (`/speckit-analyze`)

> **Prompt**
>
> /speckit-analyze Analiza la consistencia de specs/004-linea-de-tiempo (spec.md, plan.md, tasks.md, research.md, data-model.md, contracts/) entre sí, con la constitución v1.0.0 y con el enunciado de la Parte II (§3.6, §5.5, §6.1, §7.3, Apéndice B). Informe en español.

**Qué se obtuvo.** Un informe con cobertura de 100 % (los 31 FR y los 6 SC tienen tareas; ninguna tarea sin requisito) y 9 hallazgos: 2 críticos, 4 medios y 3 bajos. Los dos críticos contradecían el principio VII de la constitución: (C1) el plan hacía una copia de trabajo del estado en cada consulta, y la constitución solo permite como copias completas los puntos de control; (C2) después de cargar una partida podía quedar un punto de control extra, contra «no más de una cada K acciones» (§3.6, FR-017).

**Qué hubo que corregir.** Con la aprobación de Joshua se corrigieron el plan y sus artefactos; `spec.md` no cambió. (C1) La consulta ahora deshace en sitio, sobre el punto de control o el estado vivo, anotando el inverso de cada cambio, y rehace en un `finally` (research R3). (C2) El guardado v10 serializa juntos el estado vivo y la línea, y al cargar el estado sale de la línea (research R8 y `contracts/guardado-v10.md`; hay que acordarlo con Steven). Medios: se agregó `service/juego_service.py` a la tabla de componentes, T001 ahora mide deshacer y rehacer en sitio, y las tareas de Steven se renombraron 002-T049 y 002-T050 para no confundirlas con las propias. Bajos: se agregaron pruebas con la partida terminada, con dos pergaminos seguidos y con K mayor que la cantidad de acciones; `pickle` quedó anotado como límite conocido. Los dos errores críticos eran del diseño que propuso Claude en el Prompt 30, no del enunciado.

## Prompt 33 — Implementación de T001: medición del riesgo R3 (`/speckit-implement`)

> **Prompt**
>
> /speckit-implement Implementa únicamente T001 de specs/004-linea-de-tiempo/tasks.md (medición del riesgo R3 en benchmarks/linea_tiempo.py y anotación del resultado en research.md). No implementes otras tareas ni toques código de Steven ni de Sofía.

**Qué se obtuvo.** `benchmarks/linea_tiempo.py` (nuevo), que juega una partida real sin red sobre `cripta-04` (50 salas) y mide, para K = 10, 50 y 200, deshacer K transacciones sobre una copia conjunta del estado frente a copiar el estado completo. Resultados en research R3: con K = 10, deshacer tarda 5,6 ms de mediana; con K = 50, 30 ms; la copia completa por consulta es de 8 a 14 veces más lenta. Deshacer sobre la copia conjunta da exactamente el estado de K acciones antes.

**Qué hubo que corregir.** (1) La primera ejecución falló: `copy.deepcopy` del estado real reventaba en la lista de enemigos de la sala (`dto/sala.py`, de Sofía). El plan decía que la copia ya funcionaba porque se había comprobado con un estado más simple. Sofía lo arregló en `f89b7b5` y research R2 se corrigió en un commit aparte (`d1b7dba`). (2) El jugador moría a las 45 acciones; se le dio vida muy alta solo dentro de la medición. (3) La comprobación de deshacer estaba mal escrita (comparaba contra una partida que había terminado antes) y se corrigió. (4) Con los datos, K = 50 no cabe en los 50 ms de §6.1, así que el K por defecto provisional pasó a 10 (research R7) y se agregó a T041 medir el costo de crear un punto de control frente al límite de 20 ms por ciclo. Rehacer todavía no existe: su costo es una estimación hasta T004.

## Prompt 34 — Implementación de T003 y T004: deshacer y rehacer para la línea de tiempo

> **Prompt**
>
> ok, continuemos

(Continuación de `/speckit-implement` del Prompt 33, sobre la Fase 2 de `specs/004-linea-de-tiempo/tasks.md`.)

**Qué se obtuvo.** T003: `tests/test_logica/test_cambios_linea.py`, con 8 pruebas que citan FR-001, FR-005 y FR-012; la principal juega 120 acciones reales en `cripta-04` (moverse, atacar, recoger, soltar, equipar, usar) y comprueba que cada transacción queda idéntica después de deshacer y rehacer. T004: en `logica/cambios.py` (archivo de Joshua), `CambioSoloLinea`, `TransaccionAccion.registrar_solo_linea`, `deshacer_mientras` (no vacía la transacción) y `rehacer`, más un inverso por cada uno de los 13 tipos de cambio. `revertir` salta los cambios «solo línea» y no cambió en lo demás. Suite: 1083 aprobadas.

**Qué hubo que corregir.** (1) Los cambios de inventario se marcan como deshechos y no se pueden deshacer dos veces; el inverso guarda también el propio cambio para que la línea pueda consultar muchas veces. (2) La agenda queda con otra forma interna después de cancelar y restaurar un evento, aunque con los mismos eventos; la prueba compara la agenda por sus eventos, como ya ocurría con el pergamino. (3) En la partida de prueba no hubo turnos de enemigos, así que el inverso del azar se prueba aparte. Un tipo de cambio sin inverso hace fallar la consulta antes de tocar el estado; las specs 001 y 003 deben declararlo (contrato de dependencias).

## Prompt 35 — Implementación de T036 a T038: resolubilidad en la interfaz (002-T049 y 002-T050)

> **Prompt**
>
> revisa si ya se hizo bien el merge, si es asi continua

(Continuación de `/speckit-implement`. Steven pidió terminar las dos tareas pendientes de su spec 002, que tocan `controller/` y `vista/`.)

**Qué se obtuvo.** `controller/resumen_resolubilidad.py` (nuevo) con `linea_inicio` (las tres líneas distinguibles de FR-013 de la 002) y `lineas_informe` (el informe completo). En `controller/controlador_juego.py`: al iniciar una partida se muestra la línea de resolubilidad; si la cripta no tiene solución o no se pudo verificar, la partida no inicia y se muestra el informe; y el comando nuevo `resolubilidad` muestra el informe de antes de empezar. En `vista/vista_pygame.py`, un botón «Resolubilidad». Pruebas en `tests/test_controller/test_resolubilidad_interfaz.py` (9, citan FR-013 y FR-014 de la 002). Suite: 1095 aprobadas.

**Qué hubo que corregir.** (1) El comando `cripta` no atrapaba `CriptaNoResoluble`: con una cripta sin solución la consola se cerraba con un error en lugar de mostrar el informe. (2) `main.imprimir_informe` (de Steven) imprime en lugar de devolver texto; para no modificar su archivo se reescribió el formato en `lineas_informe` y una prueba compara las dos salidas línea por línea para que no se separen. El botón de pygame no se revisó en pantalla; solo se comprobó que cabe en el panel.

## Prompt 36 — Implementación de T005 y T006: el historial avisa a la línea de tiempo

> **Prompt**
>
> Sí, sigue

(Continuación de `/speckit-implement`, Fase 2 de `specs/004-linea-de-tiempo/tasks.md`.)

**Qué se obtuvo.** En `logica/historial_reversible.py` (archivo de Joshua): `vincular_linea`; al cerrar una acción el historial le entrega la transacción a la línea y al retroceder le avisa el recorte. Sin línea vinculada se comporta igual que antes y el límite de 5 del pergamino no cambia. Pruebas en `tests/test_logica/test_historial_linea.py` (6, citan FR-013, FR-014 y FR-021). Suite: 1101 aprobadas.

**Qué hubo que corregir.** Antes de implementar se vio que, si el historial guarda la línea, copiar el estado para un punto de control copiaría también la línea con todos sus puntos de control, y la copia crecería sin fin. El historial excluye la línea al copiarse o serializarse (`__getstate__`), y hay una prueba para eso.

## Prompt 37 — Implementación de T007 a T009: estructura de la línea de tiempo

> **Prompt**
>
> continua

(Continuación de `/speckit-implement`, Fase 2 de `specs/004-linea-de-tiempo/tasks.md`.)

**Qué se obtuvo.** `logica/linea_tiempo.py` (nuevo): `LineaTiempo` con los instantes de decisión en un arreglo no decreciente, un punto de control cada K acciones (una sola copia profunda del estado y de las transacciones de su ventana) y la cola de referencias vivas; `buscar_ultimo_menor_o_igual`, búsqueda binaria propia sin `bisect`. Pruebas en `tests/test_logica/test_linea_tiempo.py` (10, citan FR-001, FR-015, FR-017, FR-019 y FR-021), sobre partidas reales en `cripta-04`. Suite: 1112 aprobadas. También quedó escrito `recortar`, que es T023; no se marca como hecha hasta tener sus pruebas (T021 y T022).

**Qué hubo que corregir.** El plan decía que la cola conserva las últimas 2K acciones; con K chico eso no alcanza para recortar después de un pergamino que revierte 5 acciones (con K = 1 serían 2). Se corrigió a max(2K, K + 5) en research, data-model y tasks, en un commit anterior al código (`169d211`).

# Steven Moya Porras — Parte II

**Herramienta:** Claude Code (Claude Opus 5), con spec-kit 1.2.3. Capacidades a mi cargo según
`REPARTO_PARTE2.md`: `002-resolubilidad` y `003-niebla-y-ir-a`.

| # | Tema | Fecha |
| --- | --- | --- |
| 11 | `/speckit.specify` de la resolubilidad | 05/11/2026 |
| 12 | `/speckit.clarify` de la resolubilidad | 07/11/2026 |

## Prompt 11 — `/speckit.specify` de la capacidad 002-resolubilidad

Primer comando de spec-kit de la Parte II. Se fijó el directorio con
`SPECIFY_FEATURE_DIRECTORY=specs/002-resolubilidad` para conservar la numeración del
`REPARTO_PARTE2.md` y no chocar con la capacidad 001 de Sofía.

> **Prompt**
>
> SPECIFY_FEATURE_DIRECTORY=specs/002-resolubilidad
>
> Verificación de resolubilidad de una cripta.
>
> CONTEXTO. Cripta es un juego de mazmorras por turnos en Python. El jugador empieza en una sala y debe llegar a la sala de salida atravesando una puerta que exige una llave concreta. Las salas se conectan por salidas; una salida puede estar cerrada y exigir una llave. Al iniciar una cripta, el programa ya descarga de un servicio web el "esqueleto" completo: todas las salas con sus salidas, cuáles están cerradas y qué llave pide cada una, más la sala inicial, la sala de salida y la llave de salida. El servicio ofrece además la ubicación de cada llave: la sala donde está, y si la suelta un enemigo, la sala donde ese enemigo empieza. Esa consulta gasta presupuesto de solicitudes, que es limitado por cripta. El juego ya funciona contra el servicio y en modo offline.
>
> QUÉ HAY QUE LOGRAR. Antes de que empiece una partida, el programa debe determinar si esa cripta se puede ganar, y explicarlo cuando no.
>
> REGLAS DE LA VERIFICACIÓN. Se asume que el jugador puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; que las llaves no se consumen; que todo enemigo puede ser derrotado; que una llave que suelta un enemigo se obtiene en la sala donde ese enemigo empieza; y que ni las trampas ni los cierres automáticos bloquean, porque una puerta siempre puede volver a abrirse con la misma llave.
>
> Una cripta es resoluble si, partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener la llave de salida y llegar a la sala de salida atravesando una puerta que la exige.
>
> RESULTADO. Si es resoluble, el programa informa un orden de obtención de llaves en el que cada llave aparece después de todas las que hacen falta para alcanzarla; si hay varios órdenes válidos cualquiera sirve, pero dos ejecuciones iguales deben dar el mismo. Si no es resoluble, el informe dice: qué llaves no pueden obtenerse; qué puertas cerradas limitan la región alcanzable y qué llave pide cada una; y dónde está cada una de esas llaves. Si una llave está encerrada detrás de puertas que solo ella abre, sea directamente o por una cadena de llaves, el informe debe señalar esa cadena.
>
> CÓMO SE USA. Una cripta no resoluble no inicia partida, salvo que se pida forzarlo expresamente. Debe existir también una forma de ejecutar solo la verificación de una cripta, sin abrir la interfaz del juego. Al iniciar una partida, el jugador ve una línea con el resultado: que es resoluble y con cuántas llaves, o la alerta si no lo es; y un comando del juego muestra el informe completo. Todo esto funciona igual contra el servicio web y con los datos locales del modo sin conexión.
>
> PRESUPUESTO. La verificación usa el esqueleto y la ubicación de las llaves, que son los mismos datos que la partida necesita después: si la partida inicia, esos datos no deben volver a pedirse. Si la cripta no es resoluble y la partida no inicia, esas solicitudes ya se gastaron, y eso es aceptable.
>
> CASOS QUE DEBEN TENER UN RESULTADO DEFINIDO (van como escenarios de aceptación):
> - La llave de salida está detrás de la única puerta que ella misma abre: no es resoluble y el informe señala el ciclo.
> - Una llave la suelta un enemigo que se mueve: la verificación la ubica en la sala donde ese enemigo empieza, no donde pueda estar después.
> - Hay varios órdenes válidos de obtención de llaves: dos ejecuciones dan el mismo orden.
> - La cripta no es resoluble y no se pidió forzar: la partida no inicia y se muestra el informe.
>
> RENDIMIENTO. La verificación debe terminar en menos de 200 ms sobre la cripta publicada más grande. Obtener una llave puede volver alcanzable toda una región, y el costo total debe crecer aproximadamente de forma lineal con la cantidad de salas, salidas y llaves.
>
> NO incluyas en la especificación estructuras de datos, algoritmos, nombres de clases ni de módulos: eso va después en el plan.

**Qué se obtuvo.** `specs/002-resolubilidad/spec.md` con cuatro historias priorizadas (P1 saber si
se puede ganar, P2 entender por qué no, P3 detectar llaves encerradas entre sí, P3 verificar sin
abrir el juego), 21 requisitos `FR-001`…`FR-017`, seis criterios medibles `SC-001`…`SC-006`,
entidades, casos límite y supuestos; más la lista de calidad en
`specs/002-resolubilidad/checklists/requirements.md`.

**Por qué el texto se escribió así.** El enunciado abre §8 preguntando qué se le dio al modelo. El
prompt da el contexto que el modelo no puede deducir (qué es el juego, las reglas exactas de §3.5,
los cuatro casos del Apéndice B y los límites de §6.1) y le prohíbe explícitamente nombrar
estructuras, algoritmos, clases o módulos, para respetar la separación de §2.4 y el Principio X de
la constitución. Las decisiones de interfaz (una línea al iniciar más un comando de detalle,
verificación aislada, igual comportamiento sin conexión) y la de presupuesto (reutilizar el
esqueleto y las llaves que la partida necesita igual) se acordaron antes de redactar el prompt.

**Qué quedó abierto.** Dos marcas `[NEEDS CLARIFICATION]` deliberadas, para `/speckit.clarify`:
si llegar a la sala de salida por una puerta que no exige la llave de salida cuenta como ganar
(`FR-004`), y qué hacer cuando no se puede obtener la ubicación de las llaves (`FR-016`).

**Verificado.** El comando no creó ni cambió de rama (`create-new-feature.ps1` no toca git y no hay
hook `before_specify` instalado): antes y después la rama es `Steve`. La especificación no menciona
ninguna estructura de datos, algoritmo, clase ni módulo.

### Corrección al Prompt 11, tras leer el enunciado de la Parte II

El prompt anterior se redactó antes de tener el enunciado de la Parte II en el repositorio. Al
leerlo (§3.5, §4.2, §5.4 y §6.1) se corrigió la especificación sin reescribir el prompt, para que
quede el rastro de qué se supuso mal:

- **§4.2 precisa la consulta de llaves.** `GET /criptas/<id>/llaves` devuelve
  `{ "id": ..., "sala": ..., "enemigo": ... }`, donde `enemigo` es un **id de instancia** y, cuando
  está presente, `sala` es donde ese enemigo inicia. La respuesta se puede persistir mientras
  coincida la versión de la cripta. El prompt hablaba de «la ubicación de cada llave» sin ese
  detalle, que resulta decisivo: la instancia no trae estadísticas, así que las de ese enemigo solo
  están disponibles junto con los datos de su sala.
- **§3.5 cierra una ambigüedad que habíamos marcado.** Dice literalmente «llegar a `sala_salida` a
  través de una puerta que la requiere», así que `FR-004` ya no pregunta: se exige atravesar esa
  puerta y alcanzar la sala por otra vía no cuenta como ganar. Queda una sola marca
  `[NEEDS CLARIFICATION]`, la de `FR-016`.
- **§5.4 define «frontera bloqueada»** como «las puertas cerradas adyacentes a la región
  alcanzable». `FR-008` adopta el término textual del enunciado.
- **§5.4 y §6.3 exigen una medición que faltaba**: comparar el recorrido incremental contra repetir
  el recorrido completo por cada llave, con criptas sintéticas de muchas llaves encadenadas y
  deterministas por semilla. Se añadió como `SC-007`.

**Además, el caso de la cripta más pequeña.** Steve señaló que una cripta puede no ganarse porque el
jugador muere con los enemigos del camino, no porque falte una llave. Se comprobó con los fixtures
reales: en `cripta-01` el jugador (vida 30, ataque 6, defensa 2) recorre 1→2→3→4 pasando por dos
ratas rastreadoras (velocidad 150) y una trampa de dardos, con el guardián óseo en la sala de la
llave de salida; sin equipo esa ruta no sobrevive, pero en el camino hay una daga (+3 ataque), una
coraza (+2 defensa) y 24 de curación en pociones. **La cripta sí tiene solución**: lo que falla es
el orden de juego.

Como §3.5 asume que todo enemigo puede ser derrotado, y `logica/motor_juego.py:369-394` confirma que
un enemigo nunca impide atravesar una sala, el combate no puede alterar el veredicto. Se añadió en
su lugar una **advertencia de ruta** (Historia 5, `FR-019`, `FR-020`): describe los enemigos,
trampas, equipo y pociones de las salas de la ruta frente a la vida del jugador, se construye solo
con los datos ya disponibles —sin gastar ninguna solicitud— y nunca convierte una cripta con
solución en una sin solución. Se descartó simular el combate: decidir si existe alguna secuencia de
acciones que sobreviva es una búsqueda en el espacio de estados (vida × inventario × posiciones ×
reloj × semilla) que no cabe en los 200 ms de §6.1.

## Prompt 12 — Clarificación de la resolubilidad (`/speckit-clarify`)

Comando sin texto propio: `/speckit-clarify` escanea la especificación por categorías (alcance,
dominio, interacción, atributos de calidad, integraciones, casos límite, restricciones,
terminología y criterios de cierre) y pregunta solo donde la respuesta cambia la implementación o
las pruebas. Se hicieron cuatro preguntas, una a la vez, y las cuatro respuestas quedaron
integradas en `specs/002-resolubilidad/spec.md`, bajo `## Clarifications` y en los requisitos
afectados.

| Pregunta | Respuesta | Dónde quedó |
|---|---|---|
| ¿Qué hacer si no se puede obtener la ubicación de las llaves? | La partida inicia y se avisa que no se pudo verificar, sin necesidad de forzar | `FR-022`, `FR-013`, `FR-011` |
| ¿De dónde sale ese dato sin conexión? | Del paquete de datos guardados, por el mismo camino lógico que con el servicio | `FR-015` |
| ¿El informe se recalcula con las llaves ya conseguidas? | No: describe la cripta, no el avance de la partida | `FR-014` |
| ¿Sigue consultable tras guardar, cerrar y reanudar? | Sí, con el mismo contenido, y reanudar no vuelve a verificar | `FR-023` |

**Por qué estas respuestas.** La primera distingue «no se verificó» de «no tiene solución», que es
una diferencia real: §4.3 dice que el servicio publica criptas sin solución a propósito, así que
jugar una cripta no verificada es parte del ejercicio, y un fallo de red no es un defecto de la
cripta que deba costar la partida. La segunda evita un segundo camino para el mismo dato: P1 §3.4
exige que el modelo no sepa si los datos vinieron de HTTP o de archivos, y deducir la ubicación de
las llaves desde el contenido habría podido divergir del resultado con red sin que nada lo
delatara. La tercera mantiene la verificación dentro de lo que define §3.5, que la sitúa antes de
iniciar la partida y supone llaves que no se gastan y enemigos siempre derrotables: recalcularla a
media partida mezclaría ese modelo con el estado real. La cuarta se decidió ahora porque el
guardado binario cambia de versión en esta parte, y el informe tiene que entrar en esa decisión
antes de fijar el formato, no después.

**Resultado.** Ninguna marca `[NEEDS CLARIFICATION]` pendiente; la lista de calidad pasa 16 de 16.
Se añadieron `FR-023` y cuatro escenarios de aceptación (cripta sin verificar, partida reanudada,
informe no recalculado) y dos casos límite. La especificación sigue sin nombrar estructuras de
datos, algoritmos, clases ni módulos.

### Revisión del spec 002 tras la observación de Sofía

Sofía contrastó la especificación con el enunciado y señaló dos puntos. Los dos eran correctos y
los dos se corrigieron; ninguno se defendió.

**1. Iniciar sin verificar.** `FR-019` (antes `FR-022`) decía que, cuando no se puede obtener la
ubicación de las llaves, la partida inicia sin necesidad de `--forzar`. El argumento para eso era
que un fallo de red no es un defecto de la cripta. Pero §3.5 abre diciendo que «antes de iniciar
una partida, el programa determina si la cripta puede ganarse»: arrancar sin haber determinado
nada, y sin que el usuario lo pida, no lo cumple. Ahora la partida no inicia salvo `--forzar`,
igual que una cripta sin solución. Lo que sí se conserva es que el aviso distinga los dos estados:
«no se pudo verificar» no es «no tiene solución», y el informe no debe afirmar lo que no comprobó.

**2. La advertencia de ruta rompía la niebla de guerra.** Los antiguos `FR-019` a `FR-021` y la
Historia 5 describían los enemigos, trampas, equipo y pociones de las salas del camino. §3.3 es
explícito: «todo lo que la vista muestra […] debe derivarse exclusivamente del conocimiento del
jugador», y ni siquiera la antorcha revela contenido, solo nombre y salidas. La advertencia
mostraba el contenido de salas que el jugador no había pisado, así que contradecía la capacidad
`003-niebla-y-ir-a`, que es de este mismo integrante. Se retiró entera.

Conviene registrar por qué existió: la cripta más pequeña (`cripta-01`) **tiene solución** y aun
así mata al jugador que va directo por la llave de salida, porque la ruta pasa por dos ratas
rastreadoras y una trampa, y el equipo que la vuelve superable está repartido por esas mismas
salas. Eso es real, pero no es resolubilidad: §3.5 supone que todo enemigo puede ser derrotado, y
avisarlo exigía revelar lo que §3.3 oculta. El caso y el motivo del descarte van al Documento de
Decisiones.

La ubicación de las llaves sí se informa, sin conflicto: §3.5 la pide expresamente para el informe
de una cripta sin solución, lo que es una excepción del propio enunciado a la niebla.

**Resultado.** 20 requisitos `FR-001`…`FR-020` sin huecos (se renumeró al retirar tres, antes de
que existan tareas o pruebas que los citen), 7 criterios, 4 historias y ninguna marca pendiente.

## Prompt 13 — `/speckit.plan`, `/speckit.tasks` y `/speckit.analyze` de 002-resolubilidad

Los tres comandos sin texto propio: operan sobre `spec.md` y los artefactos ya generados.

**`/speckit.plan`.** Antes de ejecutarlo se acordaron las dos decisiones que fijan el
determinismo: el orden de obtención de llaves (por cercanía, a igual distancia menor id de sala,
dentro de una sala por id de llave) y cuántos círculos reportar (todos, no solo el primero).
Produjo `plan.md`, `research.md`, `contracts/consulta-llaves.md`, `contracts/cli-verificar.md` y
`quickstart.md`.

**`/speckit.tasks`.** 50 tareas por historia, cada una citando sus `FR`. Se incluyeron tareas de
prueba porque `SC-006` y el Principio XI las exigen.

**`/speckit.analyze`.** Encontró cuatro problemas, los cuatro reales: `FR-013` y `FR-014` no
tenían ninguna tarea que llegara a la interfaz; una tarea apuntaba a un directorio de pruebas
inexistente; seis tareas no citaban ruta de archivo; y `FR-011` y `FR-019` repetían la misma
regla. Se corrigieron antes de escribir código. El primero resultó ser una **frontera entre
integrantes**: el servicio entrega el informe como dato y la interfaz, que es de Joshua, lo
pinta.

## Prompt 14 — Implementación de 002-resolubilidad

Ejecución de `tasks.md` por fases, escribiendo las pruebas antes del código. Lo que vale la pena
registrar no es el código sino lo que salió al escribirlo:

**Una prueba falló y el error estaba en la prueba.** Había escrito que al abrir un atajo hacia la
sala de salida «la cripta se gana igual», lo que contradice `FR-004`: al abrir esa puerta deja de
existir toda entrada que exija la llave de salida, así que no resoluble es la respuesta correcta.

**Exigir la consulta de llaves rompió 63 pruebas.** La causa fue imponer un bloqueo duro sin dar
a los fixtures existentes el dato que ahora se exige. Se corrigió de raíz y no caso por caso: los
paquetes temporales de las pruebas pasan por un único fixture compartido, y una línea allí
arregló 38 de golpe.

**La verificación cuesta una solicitud más por partida.** El arranque pasó de 7 a 8 y el
presupuesto sintético de `test_carga_gradual` ya no alcanzaba: subió de 8 a 9. La señal era
legítima, ese test existe para proteger el presupuesto ajustado.

**Probar el `quickstart` a mano encontró dos cosas que las pruebas no.** `--verificar` con una
cripta inexistente escupía un traceback, y el propio `quickstart.md` documentaba una bandera
`--cripta` que no existe, porque la cripta se elige desde el menú.

**El enunciado pedía un solo recorrido, no dos.** La primera versión calculaba las dependencias
entre llaves en una segunda pasada. §5.4 dice «del mismo recorrido», así que se fusionaron; el
resultado fue más simple, no más complejo: desapareció una función de 35 líneas y una sola tabla
sustituyó a dos.
