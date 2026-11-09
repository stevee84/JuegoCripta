# Acuerdo condicionado con Joshua: cambios reversibles y reconstrucción

**Estado**: ACEPTACIÓN CONDICIONADA; INTERFAZ BASE INTEGRADA Y REVISADA LOCALMENTE; LÍNEA COMPLETA PENDIENTE. `specs/004-linea-de-tiempo/contracts/dependencias.md` declara que FR-016 de 001 basta si todo estado observable se registra dentro de la transacción y que la línea no llama al cazador. El checkout `Sofia` contiene y T005 verificó deshacer temporal/rehacer, el gancho para cambios nuevos y el enlace del historial. La clase completa `LineaTiempo` publicada después, el guardado coordinado y las pruebas conjuntas con cambios nuevos de 001 siguen pendientes. Este documento no modifica archivos de Joshua ni de Steven.

## 1. Objetivo

Permitir que retroceso y línea de tiempo restauren exactamente el estado introducido o afectado por 001, sin copiar el estado completo por acción y sin conservar cálculos de ruta obsoletos (`FR-014`, `FR-016`; spec 004 FR-022).

## Estado comprobado local y remoto

**Checkout local consultado**: revisión del 2026-11-09 sobre `Sofia@b046f8820d33ff9a20dedf0e37db90f850d5f30a` (para T005 del 2026-11-08 se consultó `Sofia@e89574de14df8a9e672ef0a62590630d37242f05`), descendiente de la integración `3df43c63c68a33f692148b737c12b0c0a4208569` con `joshua@927d8860639f3efa6260172d3e03cae61f74301b`. Contiene la implementación introducida en `972af5421d628171a4464709858275b100151c1e`. Su interfaz disponible en `logica/cambios.py` incluye:

- `TransaccionAccion.registrar_solo_linea(cambio)`;
- `TransaccionAccion.deshacer_mientras(estado, condicion, inversos: list) -> None`, sin vaciar ni marcar la transacción;
- `TransaccionAccion.rehacer(estado, inversos: list) -> None`;
- extensión para cualquier cambio nuevo mediante `fotografiar_para_rehacer(inverso, estado)`; si falta, falla antes de deshacer;
- pruebas en `tests/test_logica/test_cambios_linea.py`.

Además, `logica/historial_reversible.py` publica localmente `HistorialReversible.vincular_linea(linea)`, avisa `registrar_accion` al cerrar y `recortar(1)` al retroceder, y tiene pruebas en `tests/test_logica/test_historial_linea.py`.

La disponibilidad local es un hecho del checkout y T005 ya cerró su revisión cruzada de proceso. La punta observada de Joshua pasó a `origin/joshua@f4da930dbdbf951609894a1501bfca2c4ea9264a` y acumula cuatro commits propios no integrados: `d055563` (estructura de la línea y búsqueda binaria), `b039b8b` (creación al iniciar y resumen), `5b67c08` (consulta `historia <t>`) y `4cbac6d` (consultas `historia #k`, recorte por pergamino y R6). Ninguno es ancestro de `HEAD`: la clase completa `LineaTiempo` no está integrada localmente y **G4b permanece abierta**; su existencia remota no la cierra. 001 consume la interfaz base y no copia ni reedita código de Joshua.

### Revisión del análisis cruzado (2026-11-09)

- **A2 — firma y restauración de eventos**: la firma `TransaccionAccion.deshacer_mientras(estado, condicion, inversos: list) -> None` no cambió, pero el **protocolo de la condición sí**: con `927d886` la condición se invocaba como `condicion(estado)`; en la punta remota `f4da930` se invoca como `condicion(estado, cambio)` (diff en `logica/cambios.py`). La restauración de eventos posteriores al instante consultado está publicada solo en remoto: `LineaTiempo.consultar_instante(t)` reconstruye con `_reconstruir(..., hasta_instante=t)` y la condición `_hasta(instante)` sigue deshaciendo los `CambioAgenda` de eventos con `evento.tiempo > instante` incluso después de cruzar el reloj, y el `finally` los devuelve con `TransaccionAccion.rehacer`. T040/T056 se redactan contra este protocolo.
- **M1 — hashes y disponibilidad local**: consultados `Sofia@e89574d` (2026-11-08), `Sofia@b046f882` (2026-11-09), merge base `joshua@927d8860639f3efa6260172d3e03cae61f74301b` y la punta remota `origin/joshua@f4da930` con `d055563`, `b039b8b`, `5b67c08`, `4cbac6d`. La disponibilidad real local sigue siendo la interfaz base; G4b no se cierra por existencia remota y requiere integración por el flujo del equipo antes de ejecutar T056.
- **M2 — enlaces técnicos y derivados fuera de copias y guardado**: los enlaces técnicos no son estado del juego y no se copian ni persisten: `HistorialReversible.__getstate__` ya omite `_linea` (local) y la punta remota añade `Inventario.__getstate__` que omite `historial_linea`; la línea los reconecta al restaurar. Los cálculos derivados (índice de mapa, cachés, fronteras de búsqueda) conservan su regla del §2: se reconstruyen desde el estado canónico y jamás se registran como estado. 001 no añade enlaces técnicos; si un cambio de 001 necesitara uno, su exclusión en `deepcopy`/`pickle`/guardado se documentará allí antes de implementarlo.
- **B1 — cambios de pergaminos «solo línea»**: documentados en §5 con el mecanismo de la punta remota; forman parte de 004/006 y 001 solo los consume; los cambios nuevos de 001 no se marcan «solo línea» salvo decisión explícita.

Este análisis no marca tareas; T040/T056/T041/T055 permanecen abiertas.

### Evidencia de T005

- `TransaccionAccion.registrar` exige `CambioReversible`; `revertir` valida primero, deshace en orden inverso, omite `CambioSoloLinea`, vacía la transacción y evita una segunda reversión.
- `deshacer_mientras` fotografía antes de tocar estado, no vacía ni marca la transacción e incorpora cambios solo-línea; `rehacer` consume los inversos en orden contrario.
- `_fotografiar` reconoce por tipo exacto los cambios existentes y ofrece la extensión `fotografiar_para_rehacer(inverso, estado)`; un tipo nuevo sin extensión falla antes de `deshacer`.
- `logica/mutaciones.py` registra antes de mutar y sus helpers `atributo`, `dato`, `agregar`, `quitar` y `quitar_identidad` producen `CambioAtributo`, `CambioDato` o `CambioLista`, todos cubiertos por `_fotografiar`.
- `HistorialReversible.vincular_linea` entrega cada transacción cerrada mediante `registrar_accion`, notifica `recortar(1)` tras retroceso y excluye `_linea` de `deepcopy`/`pickle` mediante `__getstate__`.
- Pruebas ejecutadas: `tests/test_logica/test_cambios_linea.py`, `test_historial_linea.py`, `test_cambios.py`, `test_historial_reversible.py` y `test_cambio_soltar_objeto.py` → **44 passed in 0.76s**.
- Alcance: esta evidencia valida la interfaz base y su compatibilidad estructural con futuros cambios de 001; no prueba cambios de terreno/cazador aún inexistentes, `LineaTiempo` completa, T056 ni persistencia conjunta.

El guardado real es **v9** (`GuardadoBinario.VERSION = 9`). El **v10** de `specs/004-linea-de-tiempo/contracts/guardado-v10.md` es una propuesta para Steven: serializar en una sola operación el estado vivo y la línea como bytes opacos. No está implementado y debe coordinarse con la incorporación de costo/rango.

## 2. Separación propuesta

### Estado canónico que sí se registra/reconstruye

- sala actual de jugador y enemigos;
- pertenencia de enemigos a las salas e identidad de instancias;
- vida, actividad y procesamiento de muerte;
- apertura de puertas y eventos de cierre automático;
- reloj virtual;
- agenda: eventos insertados, extraídos, cancelados y reprogramados;
- tiempo y secuencia de próximas acciones;
- velocidad y efectos que la modifican;
- estado de azar cuando una acción lo consume;
- costos de salida y rango como datos de la versión cargada, disponibles en checkpoints/guardado donde corresponda.

### Datos derivados que no se registran ni persisten

- fronteras de búsqueda, etiquetas y predecesores;
- tablas de distancias;
- primera vecina precalculada;
- instantáneas compartidas y métricas de rutas;
- generación/caché usada solo para detectar vigencia.

Los derivados se reconstruyen desde el estado canónico y no aparecen en resúmenes históricos. Pertenecen al motor o al servicio de rutas; no son campos de `EstadoPartida`, de entidades canónicas ni de objetos alcanzables desde los cambios guardados.

## 3. Contrato de cambios de 001

Sofía muta mediante cambios pequeños compatibles con `CambioReversible`, usando la transacción abierta y los mecanismos reales de `logica.mutaciones` (`atributo`, `agregar`, `quitar_identidad`, `registrar`) y el registro de `AgendaEventos`:

| Mutación | Inverso esperado |
|---|---|
| mover actor | restaurar listas de salas y `sala_actual` con la misma identidad |
| atacar/morir | restaurar vida, actividad, botín/listas y eventos afectados |
| abrir/cerrar puerta | restaurar `abierta` y referencias/IDs del cierre pendiente |
| programar/extraer/cancelar | insertar o retirar el mismo evento y restaurar contadores |
| reprogramar por velocidad | restaurar velocidad, tiempo y secuencia anteriores del mismo evento |
| avanzar reloj | restaurar reloj anterior |

Una acción rechazada aborta sus cambios y no se publica a la línea de tiempo.

No se introducen observadores de cambios de atributos. Cada mutación canónica se registra en el punto que ya conoce la operación y antes de modificarla.

## 4. Derivados y posible invalidación

La producción inicial de 001 recalcula desde cero y no retiene resultados de ruta; en ese caso **no existe caché que invalidar**. Solo si una decisión posterior a `--bench` adopta reutilización, 001 deberá invalidar explícitamente esos derivados:

- después de que `HistorialReversible.deshacer_ultimo(estado)` devuelve `True` en `RETROCEDER`;
- al enlazar cualquier estado nuevo o cargado mediante `MotorJuego.iniciar(estado)`.

El propietario puede ser el motor o el servicio de rutas. El nombre interno no se fija mientras no exista la implementación. El efecto requerido es desacoplar resultados anteriores y obligar a calcular desde el estado enlazado/restaurado en la siguiente decisión, sin modificar reloj, agenda, azar, historial o `partida.log`.

`historia` **no requiere invalidación**: no pasa por el motor, no ejecuta decisiones de 001 y deshace/rehace temporalmente en `try/finally`, dejando idéntico el estado vivo. Como las cachés están fuera del estado y de las transacciones, 004 no las alcanza. El recorte de la línea tras un pergamino tampoco necesita un segundo aviso: el retroceso exitoso ya invalidó.

Una invalidación condicional puede ser O(1) por cambio de generación, pero la memoria pendiente de liberar se mide. No se implementan ganchos, observadores ni generaciones productivas mientras la estrategia siga siendo recálculo sin estado retenido.

## 5. Pergaminos

La línea de tiempo y 001 conservan la excepción heredada:

- el pergamino utilizado queda consumido;
- la cantidad de pergaminos no forma parte de la reversión, incluidos recogidos/soltados en el intervalo;
- los movimientos de pergaminos (recoger/soltar con `reversible=False`) se anotan «solo línea» mediante `HistorialReversible.registrar_solo_linea` en la punta remota de Joshua; la lista de cambios de `ResultadoAccion` sigue vacía, como en la Parte I;
- el consumo del pergamino se guarda aparte con `anotar_para_linea` y la línea lo publica con `anotar_solo_linea` justo después del `recortar`, para que `historia <t>` anterior al consumo lo muestre disponible en el inventario y las consultas posteriores lo muestren consumido;
- el resto del estado reversible de terreno, cazadores, agenda y puertas sí vuelve al punto anterior.

001 no implementa una segunda política de inventario; consume el contrato existente y verifica el resultado de punta a punta.

## 6. Reconstrucción histórica definida por 004

La regla de producción documentada por 004 es **hacia atrás desde el punto de control siguiente**:

1. cada punto de control copia en un solo paquete el estado canónico y las transacciones de su ventana, de modo que los cambios apunten a las entidades copiadas;
2. para consultar antes de la acción `k`, se toma el primer punto `m >= k-1` y se deshacen sobre el paquete las transacciones `m…k`;
3. si la consulta cae después del último punto, se deshace temporalmente sobre el estado vivo;
4. antes de cada deshacer se captura el inverso y se aplican los inversos en orden contrario dentro de `finally`;
5. para un instante entre decisiones se deshace parcialmente la transacción mientras el reloj sea mayor que `t` y, en la punta remota de Joshua (`f4da930`), se devuelven a la agenda los eventos posteriores extraídos usando la condición `condicion(estado, cambio)` de `deshacer_mientras`;
6. nunca se ejecuta el comportamiento del cazador ni se consulta una caché de rutas.

Re-simular hacia adelante permanece únicamente como alternativa medida en `--bench`, sobre datos sintéticos con todo el contenido cargado. No es la regla de producción.

## 7. Requisitos de copia y serialización

Los cambios nuevos de 001 deben cumplir ambos contratos de 004:

- `copy.deepcopy((estado, ventana_de_transacciones))` copia el paquete en una sola operación; cada cambio copiado debe apuntar a la entidad copiada correspondiente, no a la viva;
- el `pickle` conjunto propuesto para v10 debe conservar estado vivo, línea, transacciones y alias de referencias tras ida y vuelta.

Por tanto, un cambio de 001 puede retener valores anteriores e identidades/referencias canónicas incluidas en ese paquete, pero no referencias al `MotorJuego`, servicio de rutas, cachés, funciones de cierre, archivos, red u otros recursos externos. Estas propiedades requieren pruebas específicas; no se consideran verificadas por la aceptación documental.

La representación serializable exacta de cada cambio pertenece al acuerdo de 004/guardado; 001 ofrece IDs estables y valores anteriores necesarios, sin asumir formato binario.

## 8. Pruebas conjuntas pendientes

1. Capturar estado canónico, mover/atacar/reprogramar/cerrar puerta, retroceder y comparar igualdad salvo pergaminos.
2. Desde el mismo estado posterior al retroceso, aplicar las mismas acciones en dos ejecuciones y comparar registros.
3. Calentar una instantánea de ruta, cambiar una puerta, retroceder y verificar que la siguiente decisión coincide con cálculo desde cero.
4. Calentar una caché, ejecutar `historia` sobre paquete y sobre estado vivo, y comprobar que su identidad/generación no cambia y que la decisión posterior coincide con cálculo desde cero.
5. Copiar profundamente estado y ventana con cada cambio nuevo; verificar que el cambio copiado apunta solo a entidades copiadas y que deshacer/rehacer restaura el paquete.
6. Hacer ida y vuelta `pickle` del estado vivo y línea bajo el contrato v10, conservando alias y resultados históricos.
7. Medir retroceso con cambios de 001 frente a copia completa, sin que los derivados inflen el historial.

## 9. Estado de aceptación y cierre

- [x] 004 confirma que FR-016 basta si todo estado observable de 001 se registra dentro de la transacción.
- [x] 004 confirma que la línea no llama al cazador ni necesita una interfaz nueva de 001.
- [x] Se acuerda que las cachés no observables viven fuera del estado/transacciones y no forman parte de puntos de control o guardado.
- [x] Se delimita que `historia` no invalida y que 001 invalida tras retroceso exitoso e inicio/carga.
- [x] 004 publica deshacer temporal/rehacer y `fotografiar_para_rehacer(inverso, estado)` en `972af5421d628171a4464709858275b100151c1e`.
- [x] Esa interfaz base y `HistorialReversible.vincular_linea` están integrados en `Sofia@3df43c63c68a33f692148b737c12b0c0a4208569` mediante `972af542…`/`927d886…`.
- [x] T005 completa la revisión cruzada de proceso sobre interfaces y pruebas locales; disponibilidad y revisión no se confunden.
- [ ] Se integra y verifica la clase completa `LineaTiempo` publicada posteriormente; no se asume disponible por existir en `origin/joshua@5b67c08…`.
- [ ] Sofía implementa todas las mutaciones canónicas de 001 mediante cambios registrados; cada tipo nuevo declara `fotografiar_para_rehacer` si lo exige la interfaz integrada.
- [ ] Si la evidencia adopta reutilización productiva, se planifican y prueban entonces sus puntos de invalidación; con recálculo sin estado retenido no se añaden.
- [ ] Los cambios nuevos pasan pruebas de `deepcopy`, `pickle`, deshacer/rehacer exacto y ausencia de referencias a motor/cachés.
- [ ] Se prueba la excepción de pergaminos, la continuación determinista y que `historia` no altera cachés.
- [ ] Steven publica la persistencia de costo/rango/mapa conocido coordinada con Joshua y se comprueba la versión real; hasta entonces el formato ejecutable consultado continúa en v9.
