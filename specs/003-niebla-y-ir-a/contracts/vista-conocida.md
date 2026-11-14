# Contrato: la vista que recibe el buscador de caminos

La capacidad 001 expone un buscador que, dado un origen, un destino y una **vista de solo
lectura**, devuelve el primer paso del camino más barato. Esta capacidad le entrega una vista
distinta de la que usa el cazador: una construida solo con el conocimiento del jugador.

## Las dos vistas, lado a lado

| | Vista del cazador (001) | Vista conocida («ir a», 003) |
|---|---|---|
| Qué salas contiene | todas las del esqueleto | solo las **exploradas** |
| Qué salidas enumera | las realmente abiertas en este instante | las que el jugador **recuerda** abiertas |
| Qué costos usa | los reales | los que el jugador conoce, que son los mismos |
| Qué no consulta | contenido, niebla, red | el esqueleto real, el estado real de las puertas, el contenido, la red |

## Operaciones

Las mismas que ya consume el buscador, sin nombres nuevos:

```text
contiene_sala(sala_id) -> bool
salidas_transitables(sala_id) -> iterable de (destino_id, costo)
```

**`contiene_sala`** responde verdadero solo para salas **exploradas**. Una sala avistada responde
falso: el jugador no conoce sus salidas ni sus costos, así que no puede ser ni destino ni paso
intermedio. Acordado con 001.

**`salidas_transitables`** devuelve únicamente las salidas que cumplen las tres condiciones a la
vez: el mapa del jugador las recuerda **abiertas**, su destino está **explorado**, y el costo es el
que el jugador conoce. Una salida recordada abierta hacia una sala solo avistada **no** se
enumera.

## Lo que la vista nunca hace

- No consulta el esqueleto real ni el estado real de una puerta, ni siquiera para comprobar.
- No revela contenido de las salas: enemigos, objetos ni trampas.
- No descarga nada ni toca la red.
- No modifica el conocimiento del jugador: es de solo lectura.

## Cómo se comprueba la separación

Dos estados reales distintos de la cripta que produzcan **el mismo mapa conocido** deben producir
**el mismo viaje**. Es la prueba que pidió 001 al cerrar el contrato, y es la garantía de que el
cálculo no observa nada fuera del conocimiento: si observara algo del mapa real, los dos estados
darían resultados distintos.

## Casos que debe cubrir la prueba de contrato

- Sala explorada: `contiene_sala` verdadero.
- Sala avistada y sala desconocida: `contiene_sala` falso.
- Puerta recordada abierta hacia sala explorada: se enumera.
- Puerta recordada abierta hacia sala avistada: **no** se enumera.
- Puerta recordada cerrada: no se enumera, aunque en realidad esté abierta.
- Puerta recordada abierta que en realidad se cerró: **sí** se enumera, porque esa es la última
  observación del jugador; el viaje la descubrirá al llegar.
- Una cripta entera inexplorada: solo la sala inicial está en la vista.
