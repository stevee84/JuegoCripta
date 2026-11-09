# Modelo de datos (fase 1): Línea de tiempo

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Investigación**: [research.md](./research.md)

Notación: n = acciones del jugador que siguen en la línea; K = acciones entre puntos de control;
«antes de #k» = estado justo antes de la acción k (FR-003); #1 es el estado inicial.

## Línea de tiempo

Una por partida. Vive junto al estado y se guarda en el archivo de partida (FR-028).

| Campo | Contenido | Regla |
|---|---|---|
| `k` | Entero ≥ 1 | Fijo durante toda la partida; al cargar se conserva el guardado (FR-030). |
| `instantes` | Arreglo contiguo; `instantes[i]` = reloj al decidir la acción i + 1 | No decreciente. Se agrega al final al cerrar cada acción. `instantes[0] = 0` en una partida nueva. Longitud n + 1: el último es el instante de la decisión pendiente. |
| `puntos` | Arreglo contiguo de puntos de control; `puntos[j]` es el de la acción j·K | `puntos[0]` es el estado inicial (m = 0). Nunca más de uno cada K acciones (FR-017). |
| `cola` | Referencias vivas a las transacciones de las últimas L acciones, con L = max(2K, K + 5), más las posteriores al último punto de control (menos de K) | No son copias. Sirven para armar el siguiente punto de control y para recortar (research R5). |

**Transiciones**:
- *Acción cerrada* → agregar su transacción a `cola` e `instantes`; si n es múltiplo de K, crear
  `puntos[n / K]`.
- *Pergamino que revierte r acciones* (r ≤ 5) → quitar r elementos del final de `instantes` y de
  `cola`; quitar los puntos con m > n; anotar el consumo del pergamino en el registro solo de línea de
  la transacción n (si existe y no está ya dentro de un punto). Costo O(r) (FR-013).
- *Acción rechazada* → nada (constitución VII).

## Punto de control

| Campo | Contenido |
|---|---|
| `accion` | m, siempre múltiplo de K, también después de cargar (research R8) |
| `paquete` | Una sola copia profunda de: el estado antes de #(m+1) y las transacciones m − K + 1 … m |

Las transacciones del paquete apuntan a los objetos del estado copiado, no a los vivos (research R2).

## Transacción (cambio sobre la existente en `logica/cambios.py`)

| Campo | Contenido |
|---|---|
| `_cambios` (existente) | Cambios en orden de llegada (el más reciente primero) |
| marca «solo línea» (nuevo, por cambio) | Los cambios que **solo** deshace la línea: recoger y soltar un pergamino, consumo del pergamino (research R6). Van en la misma lista para conservar el orden relativo. |

Operaciones nuevas:
- registrar un cambio con la marca «solo línea»;
- **deshacer mientras se cumpla una condición** (para R4: mientras el reloj sea > t), del más
  reciente al más antiguo e incluyendo los marcados, **sin vaciar la transacción ni marcarla como
  revertida**, y devolviendo los inversos de lo deshecho;
- aplicar esos inversos en orden contrario para rehacer (research R3).

`revertir`, que usa el pergamino, salta los marcados y por lo demás no cambia.

**Inverso de un cambio**: un cambio que, antes de deshacer, captura el valor actual del mismo dato
(atributo, dato de ficha, estado del azar, posición en una lista, evento de la agenda, objeto del
inventario). Aplicarlo deja el dato como estaba antes de deshacer. Solo existe durante la consulta.

## Consulta

| Campo | Contenido | Validación |
|---|---|---|
| `tipo` | `instante` o `accion` | — |
| `valor` | t o k | t entero ≥ 0 y ≤ reloj actual (FR-006, FR-007); k entero en 1 … n + 1 (FR-007) |

**Resolución de una consulta por acción k** (sin copiar el estado; research R3):
1. Si k = n + 1: el resumen se arma sobre el estado vivo; no se deshace nada.
2. Si no: j = ⌈(k − 1) / K⌉. Si `puntos[j]` existe, se deshacen **sobre su paquete** las
   transacciones j·K … k (j·K − k + 1 ≤ K). Si todavía no existe (k está en la cola), se deshacen
   **sobre el estado vivo** las transacciones n … k (n − k + 1 < K por construcción).
3. Se arma el resumen y, en un `finally`, se aplican los inversos en orden contrario. Después de la
   consulta, el paquete o el estado vivo son idénticos a como estaban (FR-005).

**Resolución de una consulta por instante t**: búsqueda binaria en `instantes` de la mayor posición
i con `instantes[i]` ≤ t; k = i + 1. Si `instantes[i]` = t, responder «antes de #k». Si no,
reconstruir «antes de #(k+1)» y deshacer la transacción k mientras el reloj sea > t (research R4).

## Resumen de estado

Lo que se muestra (FR-004), en este orden fijo, igual en consola, pygame y `--replay --hasta`:

1. Instante consultado y reloj del estado (o «antes de la acción #k»).
2. Sala del jugador (id y nombre).
3. Vida actual / máxima, ataque, defensa y velocidad efectivos.
4. Inventario, en el orden real del inventario.
5. Efectos activos con su vencimiento.
6. Enemigos de la sala con su vida.
7. Mapa conocido (contrato con la spec 003; «no disponible» mientras no exista).
