# Acuerdo condicionado con Joshua: cambios reversibles y reconstrucción

**Estado**: ACEPTACIÓN CONDICIONADA; INTERFAZ BASE PUBLICADA, AÚN NO INTEGRADA LOCALMENTE. `specs/004-linea-de-tiempo/contracts/dependencias.md` declara que FR-016 de 001 basta si todo estado observable se registra dentro de la transacción y que la línea no llama al cazador. Joshua publicó deshacer temporal/rehacer y el gancho para cambios nuevos, pero el checkout `Sofia` todavía no los contiene; la línea completa, el guardado coordinado y las pruebas conjuntas de 001 siguen pendientes. Este documento no modifica archivos de Joshua ni de Steven.

## 1. Objetivo

Permitir que retroceso y línea de tiempo restauren exactamente el estado introducido o afectado por 001, sin copiar el estado completo por acción y sin conservar cálculos de ruta obsoletos (`FR-014`, `FR-016`; spec 004 FR-022).

## Estado comprobado local y remoto

**Checkout local consultado**: `Sofia@f89b7b53722e92c1337fe57c7bebf5528c1ec53e`. Su interfaz disponible sigue siendo:

- `CambioReversible.deshacer(estado)`;
- `TransaccionAccion.registrar(cambio)` y `revertir(estado)`; `revertir` vacía y marca la transacción;
- `HistorialReversible.deshacer_ultimo(estado) -> bool`; elimina la transacción después de revertirla;
- no existe localmente una operación de rehacer ni una interfaz implementada de consulta histórica.

**Publicación remota consultada sin checkout/merge**: `joshua@112cd78ab85a5b0f9a580353e5824f4aeb517889`; la implementación fue introducida en `972af5421d628171a4464709858275b100151c1e`. Publica en `logica/cambios.py`:

- `TransaccionAccion.registrar_solo_linea(cambio)`;
- `TransaccionAccion.deshacer_mientras(estado, condicion, inversos: list) -> None`, sin vaciar ni marcar la transacción;
- `TransaccionAccion.rehacer(estado, inversos: list) -> None`;
- extensión para cualquier cambio nuevo mediante `fotografiar_para_rehacer(inverso, estado)`; si falta, falla antes de deshacer;
- pruebas en `tests/test_logica/test_cambios_linea.py`.

Que esté publicado en otra rama no lo vuelve disponible en el checkout local. 001 no copia ni reedita ese código: lo consumirá y verificará cuando se integre por el flujo acordado. En el hash consultado aún no está publicada una clase `LineaTiempo` ni un enlace nuevo de `HistorialReversible`.

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
- el resto del estado reversible de terreno, cazadores, agenda y puertas sí vuelve al punto anterior.

001 no implementa una segunda política de inventario; consume el contrato existente y verifica el resultado de punta a punta.

## 6. Reconstrucción histórica definida por 004

La regla de producción documentada por 004 es **hacia atrás desde el punto de control siguiente**:

1. cada punto de control copia en un solo paquete el estado canónico y las transacciones de su ventana, de modo que los cambios apunten a las entidades copiadas;
2. para consultar antes de la acción `k`, se toma el primer punto `m >= k-1` y se deshacen sobre el paquete las transacciones `m…k`;
3. si la consulta cae después del último punto, se deshace temporalmente sobre el estado vivo;
4. antes de cada deshacer se captura el inverso y se aplican los inversos en orden contrario dentro de `finally`;
5. para un instante entre decisiones se puede deshacer parcialmente la transacción mientras el reloj sea mayor que `t`;
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
- [x] 004 publica deshacer temporal/rehacer y `fotografiar_para_rehacer(inverso, estado)` en `972af5421d628171a4464709858275b100151c1e`, visible en la punta remota consultada `112cd78ab85a5b0f9a580353e5824f4aeb517889`.
- [ ] Esas interfaces se integran en `Sofia` y se verifican allí; su publicación remota no cierra esta dependencia local.
- [ ] Sofía implementa todas las mutaciones canónicas de 001 mediante cambios registrados; cada tipo nuevo declara `fotografiar_para_rehacer` si lo exige la interfaz integrada.
- [ ] Si la evidencia adopta reutilización productiva, se planifican y prueban entonces sus puntos de invalidación; con recálculo sin estado retenido no se añaden.
- [ ] Los cambios nuevos pasan pruebas de `deepcopy`, `pickle`, deshacer/rehacer exacto y ausencia de referencias a motor/cachés.
- [ ] Se prueba la excepción de pergaminos, la continuación determinista y que `historia` no altera cachés.
- [ ] Steven publica la persistencia de costo/rango/mapa conocido coordinada con Joshua y se comprueba la versión real; hasta entonces el formato ejecutable consultado continúa en v9.
