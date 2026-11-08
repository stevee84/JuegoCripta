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

**Responsabilidad**: arista dirigida que representa un sentido de una salida bidireccional.

| Campo | Tipo/relación | Validación | Estado |
|---|---|---|---|
| `id_puerta` | texto no vacío | contrato heredado | canónico |
| `destino_sala_id` | entero | ID estricto existente | canónico |
| `destino_sala` | referencia a `Sala` | resuelta por índice; misma instancia del mapa | enlace derivado del esqueleto |
| `costo` | entero `>= 1` | ausente→100; booleano/no entero/<1 rechaza | canónico de la versión, inmutable |
| `abierta` | booleano | estado actual | canónico reversible |
| cierre/llave/evento | contrato heredado | validación existente | canónico reversible |

**Invariante**: los dos sentidos de una salida comparten costo. Una contradicción rechaza la cripta antes de jugar (`FR-002`).

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

**Sustitución infrecuente**: si `agregar_sala` recibe un ID existente, recorre la lista O(`V`) para encontrar su posición, coloca allí la nueva referencia y actualiza la tabla. Si el mapa estaba vinculado, vuelve a resolver todas las referencias `destino_sala` desde sus IDs antes de exponerlo; esto actualiza las salidas entrantes y las de la sala nueva, con O(`V+E`) esperado y O(`V·E`) peor caso si el índice hash degenera. Durante carga inicial puede diferirse hasta el único `vincular_salidas` final.

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

**Estado de decisión**: no se persiste. En cada turno se produce `ATACAR`, `ESPERAR` o `MOVER` a una primera vecina con costo de acción.

**Transición de turno**:

1. muerto/inactivo: no actúa;
2. comparte sala con jugador vivo: `ATACAR`;
3. ruta mínima inexistente o costo `> rango`: `ESPERAR`, costo 100;
4. ruta mínima con costo `<= rango`: `MOVER` un paso, costo de la salida.

## 6. VistaGrafoPonderado

**Responsabilidad**: límite de lectura para el buscador de rutas.

Operaciones conceptuales:

- comprobar que un ID pertenece a la vista;
- enumerar salidas transitables desde una sala como `(destino_id, costo)`;
- obtener una sala por ID sin búsqueda lineal.

Implementaciones previstas:

- vista real del cazador: esqueleto completo + estado actual de puertas;
- vista del mapa conocido de «ir a»: solo salas exploradas y puertas recordadas abiertas, pendiente de acuerdo con Steven.

La vista no expone contenido de salas, red, niebla ajena ni mutaciones.

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

## 8. ResultadoRuta (derivado)

| Campo | Valor |
|---|---|
| `alcanzable` | verdadero/falso dentro del límite |
| `costo_total` | entero o ausencia |
| `primera_vecina_id` | entero o ausencia |
| `costo_primera_salida` | entero o ausencia |
| métricas | fijadas `F`, descubiertas `D`, salidas examinadas `E`, entradas insertadas `P`, frontera máxima `Q`, obsoletas extraídas y frontera final limpiada; solo instrumentación/bench |

El comportamiento transforma el resultado en una acción; el resultado no modifica estado.

## 9. InstantáneaRutaCompartida (derivada y experimental)

| Campo | Dependencia |
|---|---|
| versión de cripta | esqueleto/costos |
| generación de puertas | aperturas/cierres actuales |
| `objetivo_id` | sala actual del jugador |
| límite agregado | rango máximo cubierto |
| distancias | tabla propia por sala |

**Invalidación**: puerta, objetivo, versión o retroceso/reconstrucción. Velocidad y movimiento/muerte de otro actor no cambian distancias; sí pueden cambiar quién consume la instantánea.

No se habilita en producción hasta que `--bench` la justifique.

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
| retroceder/reconstruir | varios campos anteriores | todos los cálculos derivados |
