# Data Model: Terreno y cazador

Este modelo distingue estado canónico reversible de cálculos derivados. Los nombres describen el diseño previsto; no cambian las reglas de `spec.md`.

## 1. Sala

**Responsabilidad**: nodo estable del esqueleto.

| Campo | Tipo/relación | Validación | Estado |
|---|---|---|---|
| `id_sala` | entero | `type(valor) is int`; sin conversión | canónico, inmutable durante la partida |
| `puertas` | lista de `Puerta` | conserva orden recibido | canónico |
| `enemigos` | lista compatible + índices propios | identidad por `id_actor` | canónico reversible |
| contenido | objetos/trampas/enemigos | puede cargarse gradualmente | canónico, no afecta rutas del cazador salvo actores activos |

**Relaciones**: una sala tiene cero o más salidas; puede ser sala actual de varios enemigos y del jugador.

## 2. Puerta/Salida

**Responsabilidad**: arista dirigida; puede existir o no el sentido inverso.

| Campo | Tipo/relación | Validación | Estado |
|---|---|---|---|
| `id_puerta` | texto no vacío | contrato heredado | canónico |
| `destino_sala_id` | entero | ID estricto existente | canónico |
| `destino_sala` | referencia a `Sala` | resuelta por índice; misma instancia del mapa | enlace derivado del esqueleto |
| `costo` | entero `>= 1` | ausente→100; booleano/no entero/<1 rechaza | canónico de la versión, inmutable |
| `abierta` | booleano | estado actual | canónico reversible |
| cierre/llave/evento | contrato heredado | validación existente | canónico reversible |

**Invariante**: cuando existen los dos sentidos de una salida, comparten costo. Se identifican por origen/destino y una multiplicidad entre el mismo par debe detectarse como ambigua; una contradicción rechaza la cripta antes de jugar (`FR-002`). Un sentido sin inversa es válido y no crea una conexión implícita.

**Estado integrado (`5000d1f`)**: `Puerta` y ambos caminos de `DecodificadorDatos.convertir_sala()` publican `costo`; Steven implementó 100 solo por ausencia y rechazo de todo valor presente inválido.

**Transiciones**:

- cerrada → abierta: acción de apertura; invalida rutas dependientes de puertas;
- abierta → cerrada: cierre automático; invalida rutas dependientes de puertas;
- retroceso: restaura el valor canónico previo y descarta derivados.

## 3. MapaCripta

**Responsabilidad**: propietario del esqueleto y de sus referencias.

| Componente | Estructura | Propósito |
|---|---|---|
| salas en orden | lista de referencias | recorrido determinista, guardado y precarga |
| sala por ID | `TablaHashImpl` | acceso esperado O(1) en turnos/rutas |

**Invariantes**:

- una entrada por ID;
- el índice y la lista apuntan a la misma instancia;
- ninguna decisión usa el orden de iteración de la tabla hash;
- vincular destinos no cambia el orden de salas ni puertas.
- el recorrido posterior a `vincular_salidas()` identifica sentidos por `(origen_id, destino_id)`, detecta pares múltiples ambiguos, rechaza costos asimétricos cuando ambos existen y acepta sentidos únicos antes de ejecutar 002.

**Sustitución infrecuente**: si `agregar_sala` recibe un ID existente, recorre la lista O(`V`) para encontrar su posición, coloca allí la nueva referencia y actualiza la tabla. Si el mapa estaba vinculado, vuelve a resolver todas las referencias `destino_sala` desde sus IDs antes de exponerlo; esto actualiza las salidas entrantes y las de la sala nueva, con O(`V+E`) esperado y O(`V·E`) peor caso si el índice hash degenera. Durante carga inicial puede diferirse hasta el único `vincular_salidas` final.

**Estado integrado**: `MapaCripta` conserva `_salas`, `_enlaces_listos` y sustitución en posición, y añade `_salas_por_id: TablaHashImpl`; `obtener_sala()` y el enlace consultan el índice sin cambiar el orden de la lista.

**Propiedad y compatibilidad**: `MapaCripta` es un componente de Sofía y Steven solicitó expresamente que Sofía implemente su índice por ID. La solicitud conserva las firmas existentes y no asigna DTO, inicialización o persistencia. Los consumidores comprobados incluyen construcción/restauración (`main.py`, inicializador, restaurador y `PartidaService`), simulación/verificación (motor, resolubilidad, rastro y efectos), servicios/datos (juego, carga gradual, decodificador y guardado), vista, benchmarks y pruebas. Todos deben seguir observando el mismo orden, las mismas instancias y los mismos destinos enlazados.

**Medición existente**: T073–T075 separan construcción de lista+índice, consultas por ID y vinculación de salidas. La aceptación de sentidos únicos no interviene en esos fixtures estructurales.

## 4. Actor

**Campos relevantes**:

- `id_actor`: identidad textual estable;
- `sala_actual`: referencia canónica reversible;
- `velocidad`: entero positivo canónico reversible;
- próxima acción: representada por evento en agenda.

**Regla temporal**: un movimiento usa `max(1, costo_salida*100//velocidad)`. Un cambio de velocidad reprograma el tiempo restante y asigna secuencia nueva.

## 5. Cazador

**Extensión de enemigo**:

| Campo | Tipo | Validación |
|---|---|---|
| `comportamiento` | `"cazador"` | ficha de enemigo |
| `rango` | entero `>= 0` | obligatorio; booleano, cadena, fracción, negativo o ausencia rechazan la ficha |

**Estado integrado (`5000d1f`)**: `Enemigo.rango` se materializa y valida en el camino externo y se conserva en reconstrucción/guardado v10.

**Estado de decisión**: no se persiste. En cada turno se produce `ATACAR`, `ESPERAR` o `MOVER` a una primera vecina con costo de acción.

**Transición de turno**:

1. muerto/inactivo: no actúa;
2. comparte sala con jugador vivo: `ATACAR`;
3. ruta mínima inexistente o costo `> rango`: `ESPERAR`, costo 100;
4. ruta mínima con costo `<= rango`: `MOVER` un paso, costo de la salida.

## 6. VistaGrafoPonderado

**Responsabilidad**: límite de lectura para el buscador de rutas.

Operaciones conceptuales:

- `contiene_sala`: comprobar que un ID pertenece a la vista;
- `salidas_transitables`: enumerar desde una sala pares conceptuales `(destino_id, costo)`;
- obtener una sala por ID sin búsqueda lineal.

Implementaciones previstas:

- vista real del cazador: esqueleto completo + estado actual de puertas;
- vista del mapa conocido de «ir a», construida por Steven: solo contiene salas exploradas y solo enumera, desde ellas, puertas recordadas abiertas hacia otras salas exploradas.

Steven aceptó estas dos capacidades conceptuales y construirá una prueba futura de independencia frente al estado real oculto. También aceptó recalcular por paso. Las firmas Python, el protocolo/clase, el tipo exacto de cada retorno y la asignación de archivos compartidos continúan abiertos. La vista no expone contenido de salas, red, niebla ajena ni mutaciones.

## 7. EtiquetaRuta y frontera (derivadas)

| Campo | Tipo | Significado |
|---|---|---|
| `sala_id` | entero | sala alcanzada |
| `distancia` | entero no negativo | costo acumulado |
| `primera_vecina_id` | entero | primer paso desde el origen |

**Orden total de trabajo**: `(distancia, primera_vecina_id, sala_id)`. Solo los dos primeros componentes determinan la ruta observable.

La tabla de mejores etiquetas contiene como máximo una etiqueta vigente por sala descubierta. El montículo contiene `EntradaFrontera` inmutables y puede guardar varias para la misma sala: cada mejora inserta una nueva. Una entrada extraída es obsoleta si sus tres valores no coinciden con la mejor etiqueta actual o si la sala ya está fijada; se descarta sin expandir. No hay actualización de prioridad en sitio.

**Estados de una sala durante la consulta**:

- **descubierta**: tiene una mejor etiqueta dentro del rango; puede seguir pendiente;
- **en frontera**: tiene al menos una entrada almacenada, vigente u obsoleta;
- **fijada**: se extrajo su entrada vigente mínima y su etiqueta quedó definitiva; solo entonces se examinan sus salidas.

No se insertan etiquetas con distancia superior al rango. Con costos positivos, descartarlas no puede ocultar una ruta que regrese dentro del límite. Al terminar se liberan mejores etiquetas, fijadas y todas las entradas restantes. Nada de esto es reversible ni persistente.

## 8. ResultadoRuta (derivado; representación acordada)

La firma acordada es `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta` y distingue:

| Estado conceptual | Paso | Costo total |
|---|---|---|
| paso disponible | solo la primera vecina | entero positivo dentro del límite aplicable |
| origen igual a destino | ninguno | 0 |
| sin ruta | ninguno | ausencia explícita, distinta del caso anterior |

Steven acepta que la operación nunca entregue una secuencia comprometida: cada paso de «ir a» se consulta de nuevo con origen, destino y conocimiento vigentes.

`ResultadoRuta` es inmutable y fija estos campos:

| Campo | Valor |
|---|---|
| `alcanzable` | `True` para paso/origen=objetivo; `False` para ausencia de ruta o límite insuficiente |
| `costo_total` | entero o ausencia |
| `primera_vecina_id` | entero o ausencia |
| `costo_primera_salida` | entero o ausencia |
| instrumentación | fijadas `F`, descubiertas `D`, salidas examinadas `E`, entradas insertadas `P`, frontera máxima `Q`, obsoletas extraídas y frontera final limpiada; no altera los cuatro observables |

El comportamiento transforma el resultado en una acción; `ATACAR` y `ESPERAR` no pertenecen al buscador. El resultado no modifica estado.

## 9. InstantáneaRutaCompartida (solo benchmark; no producción)

| Campo | Dependencia |
|---|---|
| versión de cripta | esqueleto/costos |
| generación de puertas | aperturas/cierres actuales |
| `objetivo_id` | sala actual del jugador |
| límite agregado | rango máximo cubierto |
| distancias | tabla propia por sala |

**Invalidación experimental medida**: puerta, objetivo, versión, retroceso exitoso o inicio/carga de estado. `historia` no invalida. Velocidad y movimiento/muerte de otro actor no cambian distancias; sí pueden cambiar quién consume la instantánea.

No se implementa ni habilita en producción hasta que `--bench` la justifique y una actualización posterior de plan/tareas asigne propietario, claves y archivos.

Para «ir a», el mecanismo de reutilización, sus claves y su propietario siguen sin acuerdo. La primera propuesta calcula cada paso individualmente y solo permite reutilización tras demostrar equivalencia con origen/destino/conocimiento vigentes y medir construcción, consulta, invalidación y limpieza frente al límite de 5 ms de 003.

**Ubicación actual**: `benchmarks/`, como alternativa local al benchmark. Si se habilitara después, pertenecería al motor o al servicio de rutas, nunca a `EstadoPartida`, entidades canónicas o cambios.

**Producción actual planificada**: recálculo sin estado retenido; no existen fronteras de invalidación. Las fronteras anteriores solo son escenarios que debe medir la alternativa experimental.

## 10. Evento de agenda

**Campos relevantes**: ID, tiempo virtual, secuencia, tipo, destinatario y datos.

**Invariante**: prioridad única `(tiempo, secuencia)`. Reprogramar conserva identidad del evento, cambia tiempo y asigna secuencia nueva. Todos los cambios se registran en el intervalo reversible abierto.

## 11. IntervaloReversible

**Contenido canónico de 001**:

- sala de cada actor movido;
- pertenencia/posición en listas de enemigos;
- vida y estado de muerte/actividad;
- puerta abierta/cerrada y eventos de cierre;
- eventos insertados, retirados o reprogramados;
- reloj, secuencias y azar cuando corresponda.

**Excluido**: montículos de ruta, etiquetas, distancias, métricas e instantáneas. Después de deshacer, esos derivados se eliminan y se reconstruyen desde el estado restaurado.

**Mecanismo real local**: las mutaciones usan `logica.mutaciones.atributo`, `agregar`, `quitar_identidad` o `registrar`, además del registro automático de agenda, mientras `HistorialReversible` mantiene una transacción abierta. `Sofia@3df43c6…` contiene `registrar_solo_linea`, `deshacer_mientras`, `rehacer`, la extensión `fotografiar_para_rehacer(inverso, estado)` y `HistorialReversible.vincular_linea` mediante `972af542…`/`927d886…`. Esto hace disponible la interfaz base, no la clase completa `LineaTiempo` contenida en la punta posterior `origin/joshua@b039b8b…`, ni demuestra todavía las pruebas conjuntas con cambios nuevos de 001.

**Compatibilidad con 004**: un cambio nuevo solo retiene valores y referencias canónicas incluidas en el paquete `(estado, transacciones)`. Debe conservar alias correctos al copiar ese paquete con `deepcopy` y al serializar conjuntamente estado/línea con `pickle`; no referencia motor, servicio de rutas, cachés, callbacks ni recursos externos.

**Excepción heredada**: el pergamino usado queda consumido y la cantidad de pergaminos no se revierte (`FR-016`).

## 12. Dependencias entre datos

| Cambio | Estado canónico afectado | Derivados a descartar/recalcular |
|---|---|---|
| abrir/cerrar puerta | `Puerta.abierta`, agenda de cierre | distancias que dependan de puertas |
| mover jugador | `Jugador.sala_actual`, listas/rastro | cálculo compartido por objetivo |
| mover cazador | `Enemigo.sala_actual`, listas | decisión individual de ese cazador |
| cambiar velocidad | velocidad, tiempo/secuencia del evento | ninguna distancia; sí próxima acción |
| muerte de actor | vida/actividad/listas/eventos | lote de cazadores, no distancias por sí solas |
| cargar contenido | contenido de sala | ninguna ruta del cazador |
| retroceder con éxito | varios campos anteriores | ninguno entre decisiones con recálculo; invalidación solo si una estrategia futura retiene derivados |
| iniciar/cargar estado | estado vivo nuevo o reconstruido | ninguno entre decisiones con recálculo; invalidación solo si una estrategia futura retiene derivados |
| consultar `historia` | mutación temporal que 004 rehace en `finally` | ninguno; no ejecuta 001 ni altera cachés externas |

## 13. Persistencia y reconstrucción vigentes

**Versión actual comprobada**: `GuardadoBinario.VERSION = 9`. El lector acepta únicamente esa versión y rechaza una cabecera distinta.

| Punto actual | Datos relevantes para 001 | Impacto pendiente |
|---|---|---|
| `GuardadoBinario._escribir_sala()` | puerta: destino, dirección, apertura, llave y cierre; enemigo: estadísticas y comportamiento | no escribe costo de salida ni rango materializado |
| `GuardadoBinario._leer_sala_datos()` | reconstruye los mismos registros de puerta/enemigo | debe leer los campos acordados bajo una nueva versión de formato |
| `DecodificadorDatos.convertir_sala()` | adapta tanto API (`salidas`) como registro interno (`puertas`) | ambos caminos deben producir el mismo `costo` validado |
| `DecodificadorDatos.convertir_contenido()` | reconstruye enemigos desde registros internos | debe conservar/materializar rango según el contrato acordado |
| `RestauradorPartida._reconstruir_mapa()` | crea salas, comprueba destinos y vincula referencias | reconstruye costo canónico; nunca resultados de ruta |
| `RestauradorPartida.restaurar_para_reanudar()` | publica estado nuevo, agenda reconstruida e historial vacío | `MotorJuego.iniciar` invalida explícitamente cualquier caché anterior al enlazarlo |

V9 también guarda el informe de resolubilidad de 002. Añadir costo/rango modifica el esquema y requiere una versión nueva explícita porque no hay lectura flexible de versiones. Steven asume persistir costo/rango/mapa conocido coordinado con Joshua, pero `Steve@757d747…` sigue en v9 y no publica esa entrega. 001 no reserva v10 ni otra versión: campos, representación, compatibilidad, archivos y versión final deben comprobarse en el hash que finalmente se integre. Etiquetas, fronteras, distancias, métricas e instantáneas permanecerán fuera del guardado.

## 14. Reconstrucción histórica de 004

La producción reconstruye **hacia atrás desde el punto de control siguiente**. El punto contiene una única copia profunda del estado canónico y las transacciones de su ventana; 004 deshace como máximo K transacciones sin vaciarlas, captura inversos y los aplica en orden contrario en `finally`. Si la consulta está después del último punto, opera temporalmente sobre el estado vivo y lo deja idéntico. Para un instante entre decisiones puede detenerse dentro de una transacción cuando el reloj ya no sea mayor que `t`.

Re-simular hacia adelante no es transición del modelo de producción: permanece como alternativa de `--bench`. Ninguna reconstrucción llama al comportamiento del cazador o necesita una caché de rutas.
