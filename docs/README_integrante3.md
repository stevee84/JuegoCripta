# Aportación de integrante 3 — JuegoCripta

Trabajo desde `joshua`, `2a51b9d`; referencia de compatibilidad Steve
`74d01ecb3e66360c7488249f6b05bb530f8a03e5`. Este documento es una aportación
separada: no reemplaza documentación compartida ni promete un juego completo.

## Instalación y comprobación

Python 3.11+. Desde la raíz:

```bash
python -m venv .venv
python -m pip install -r requirements.txt
python -m pytest -q
```

Activar antes el entorno (`.venv\Scripts\activate` en Windows;
`source .venv/bin/activate` en Linux). En el entorno de este trabajo se ejecutó
`.venv/Scripts/python.exe -m pytest -q`.

## Modos

```bash
python main.py --offline --cache-size 25 --semilla 123
python main.py --replay partida.log --offline
python main.py --bench > mediciones.json
python -m benchmarks.integrante3 > mediciones.json
```

`--bench` se selecciona ANTES de crear fuente, motor o vista. `--replay` no
crea vista ni solicita entrada; sin URL configurada intenta datos locales.
Si ambas opciones se proporcionan, prevalece `--bench`. Caché predeterminada
25; rechaza capacidades no positivas. Sin `--semilla`, el coordinador usa 0.
La URL de API sigue sin estar definida; no se inventó una. El modo normal
sin `--offline` informa ese dato faltante.

**Inicialización automática bloqueada por campos desconocidos**, no por PDFs:
solo `generales.inventario_max` está confirmado. Se consulta/valida ese campo;
no se fabrican jugador, páginas ni sala inicial. La fábrica compatible previa
permanece para pruebas y futuras conexiones, no se presenta como datos reales.

Ejemplos JSON exactos que necesitamos del integrante 2/API:

1. Respuesta completa de `obtener_generales(cripta_id)`: ubicación/nombres de
   campos de jugador (ID, nombre, vida, ataque, defensa, velocidad), sala inicial,
   `inventario_max` y metadatos de paginación (primer índice, fin/total/enlace).
2. Respuestas de primera y última `obtener_pagina(cripta_id, pagina)`: nombre y
   estructura de la colección de salas; mecanismo para detectar fin. No se
   presupone que empezar en 0/1 o pedir páginas vacías sea una política válida.
3. `obtener_contenido(cripta_id, [sala_inicial_id])`: enemigos, objetos, trampas
   y confirmación de completitud. El decodificador ya acepta esos DTO, pero no
   define el envoltorio de las páginas ni las estadísticas iniciales del jugador.
4. `obtener_catalogo([id_arma, id_armadura, id_pocion, id_llave, id_pergamino])`:
   nombre real de categoría, curación, peso/valor/nombre, bonos y semántica de
   `abre`; versiones respectivas. El adaptador local admite remapeo explícito.

## Interfaz local provisional de fichas

`AdaptadorFichas` NO representa el esquema confirmado de la API. Nombres
provisionales: `clase`, `curacion`, `peso`, `valor`, `nombre`, `ataque_bonus`,
`defensa_bonus`, `abre`. Remapeo, por ejemplo:

```python
adaptador = AdaptadorFichas({"categoria": "campo_real", "arma": "bono_real"})
servicio.conectar_contexto(jugador, repositorio_catalogo, historial,
                           adaptador, cache)
```

El catálogo acepta `resolver(ficha_id)` (RepositorioCatalogo existente), un
callable, o diccionarios explícitos de prueba. Los campos ausentes se rechazan:
no se interpretan patrones de ID. `abre` se interpreta localmente como ID de
una única puerta en la sala; debe confirmarse contra fichas reales.

## Estado funcional y comandos

Equipo, sustitución, soltar equipo, curación inmediata, llave no consumida,
pergaminos y vistas ordenadas están probados sobre DTO/estructuras reales con
fichas **sintéticas**. No se declara completa la integración con datos reales.

- Consultas: `estado`, `criptas`, `puntajes`, `bitacora`, `ayuda`.
- Inventario conectado: `siguiente`, `anterior`, `inventario [peso|valor|nombre]`.
- Motor actual: `mover N/S/E/O`, `atacar ID` (primitivas, no turnos completos).
- `usar [ID]` / `retroceder [ID]`: solo pergaminos, con inventario/catálogo e
  historial válido conectados; delega los inversos, no avanza el motor.
- `cripta ID` depende del esquema de inicialización faltante.
- `registro RUTA`: nueva ruta, antes de la primera acción coordinada.
- `salir`: termina la sesión, NO inventa derrota/victoria ni un puntaje.
- `guardar` y `cargar`: no se anuncian como conservación/restauración completas.
- `exportar_parcial RUTA`: inspección del formato binario existente; **no
  reanudable**. Es optativo y no puede sobrescribir el log activo.

Los costos del servicio local son equipar/usar llave/poción 50, recoger/soltar
25 y pergamino 0. El motor todavía devuelve 1 para MOVER/ATACAR y no delimita
turnos. No se compensa esa incoherencia sumando tiempo desde el controlador.
Equipar/recoger/soltar y consumibles temporales no tienen despacho temporal
completo en el juego normal; se bloquean ahí, sin mutaciones ficticias.

## Archivos generados

- Logs elegidos por usuario: UTF-8 JSON Lines, cabecera y acciones exitosas.
- `puntajes.dat`: resultados de partidas realmente finalizadas, una vez por
  estado/coordinador; append order, sin fórmula de puntaje ni ranking.
- Binarios elegidos con `exportar_parcial`: versión existente sin ampliar.
- Benchmarks: JSON por stdout; tamaños, repeticiones, entorno, unidades.
- `docs/mediciones_integrante3*.json`: resultados reales de estas mediciones.

Rechazos, consultas, exportación, selección de cursor y salida de sesión no
son acciones de log. Usar pergamino registra `USAR` con `id_instancia`; el log
no se elimina al deshacer. Fallar una escritura después de actuar no puede
revertirse sin inversos del motor: se informa lo ocurrido y se bloquean nuevas
acciones, sin reejecutar ni afirmar que el rechazo no modificó el estado.

## Pendientes por propietario

| Propietario | Archivo/método | Capacidad mínima requerida |
|---|---|---|
| Datos, integrante 2 | FuenteDatos/DecodificadorDatos | Ejemplos anteriores y contrato de datos iniciales; no estadísticas por defecto. |
| Simulación, integrante 1 | MotorJuego.ejecutar_accion | Despachar acciones de inventario/ESPERAR/ABRIR; callback al servicio y costo base real. |
| Simulación, integrante 1 | MotorJuego.avanzar_hasta_decision | Una decisión delimitada por `max(1,costo*100//velocidad)`, retorno de todos los CambioReversible del intervalo, no vaciado de agenda. |
| Simulación, integrante 1 | AgendaEventos.reprogramar | Reprogramación con secuencia nueva y consulta/cancelación por ID de efecto; aplicar la fórmula de velocidad indicada por requisitos. |
| Simulación, integrante 1 | GestorEfectos | Velocidad con vencimiento, antorcha con usos/apagado; antídoto que cancele solo veneno del jugador y todas sus activaciones futuras. |
| Simulación, integrante 1 | Cambios de motor/efectos | Inversos de movimiento, combate, agenda, reloj, RNG y contadores. No se sustituyen por snapshots. |
| Datos, integrante 2 | GuardadoBinario.guardar/cargar | Serializar/reconectar inventario, equipo, historial, agenda, efectos, versiones, RNG y contadores; preservar IDs y marcas de orden. |
| Coordinación de caché | CacheCatalogo.fijar/liberar_referencia | Hoy son fijaciones booleanas; hace falta acordar propiedad/contadores si simulación protege los mismos IDs. |

`ServicioInventario.exportar_representacion()` entrega al responsable del
binario capacidad, instancias, cursor, marcas de nodos, equipo/bonos y
metadatos de inversos propios. No modifica el formato ajeno ni implementa un
cargador alternativo. Los cambios desconocidos se marcan como no exportables;
la representación NO se presenta como guardado completo restaurable.

Propuestas mínimas **para acordar, no implementadas en código ajeno**:

- `MotorJuego.conectar_servicio_inventario(servicio)`: despacho al servicio
  existente; `ejecutar_accion` devuelve ResultadoAccion con costo base real y
  todos los inversos de acción+eventos hasta la decisión, para cerrar historial.
- `AgendaEventos.eventos_por_efecto(efecto_id)` y
  `reprogramar_con_secuencia(evento_id, tiempo, secuencia)`: consulta dirigida,
  cancelación con `cancelar(id)` ya existente y renovación del orden total.
- `GestorEfectos.aplicar_consumible(estado, objeto, ficha)`: ResultadoAccion
  reversible para velocidad/antídoto/antorcha, sin interpretación duplicada
  de duraciones ni reprogramación desde ServicioInventario.
- `CacheCatalogo.fijar_para(ficha_id, propietario)` /
  `liberar_para(ficha_id, propietario)`: coexistencia de protecciones de datos,
  simulación e inventario sin liberar una protección de otro propietario.
- El responsable del binario acuerda un codificador/decodificador de los
  registros exportados y los cambios de simulación; no basta convertir sus
  diccionarios actuales en DTO sin agenda, RNG, historial y referencias.

Benchmark admite `proveedores=(callable, ...)` para incorporar mediciones
entregadas por compañeros. No hay mediciones aportadas actualmente; no se
escribieron ni simularon sus subsistemas. Para detalles de decisiones, costos
y evidencia ver [secciones técnicas](secciones_integrante3.md).
