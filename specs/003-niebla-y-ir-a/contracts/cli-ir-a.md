# Contrato: el mapa conocido y el comando «ir a»

§7.3 exige dos cosas en la interfaz funcional mínima: **ver el mapa conocido** y **ejecutar ir a
una sala y ver por qué se detuvo un viaje**. Las dos las pinta la interfaz; esta capacidad entrega
los datos.

## Ver el mapa conocido

Muestra las salas exploradas con sus salidas, y las salas avistadas como lo único que el jugador
sabe de ellas: que existen.

```
Mapa conocido (4 exploradas, 3 avistadas)

  Sala 1  Entrada derruida
     NORTE  -> sala 2    abierta     costo 100
  Sala 2  Pasillo de las urnas
     SUR    -> sala 1    abierta     costo 100
     NORTE  -> sala 3    abierta     costo 100
     ESTE   -> sala 5    cerrada     costo 100   exige itm_llave_bronce
  Sala 3  Cripta baja
     SUR    -> sala 2    abierta     costo 100
     NORTE  -> sala 4    abierta     costo 250
  Sala 4  Osario profundo
     SUR    -> sala 3    abierta     costo 250
     ESTE   -> sala 6    cerrada     costo 100   exige itm_llave_negra

  Avistadas: 5, 6
```

El estado de cada puerta es **el recordado**, no el real: puede decir «abierta» una que ya se
cerró sola. Esa es la regla de §3.3 y no un defecto.

El mapa conocido **no** muestra enemigos, objetos ni trampas: eso es contenido de las salas y se
rige por las reglas de juego ya existentes.

## Ejecutar «ir a»

El jugador indica una sala explorada. El viaje avanza paso a paso y termina con un motivo.

```
ir a 1
  ... se desplaza, un movimiento por paso ...
Viaje terminado: llegaste a la sala 1.
```

Los motivos de parada, que §3.4 fija y el jugador debe poder ver:

| Motivo | Cuándo |
|---|---|
| llegó al destino | el jugador está en la sala pedida |
| hay enemigos | entró a una sala con enemigos, activos o dormidos |
| recibió daño | le llegó daño, moviéndose o entre dos pasos |
| no hay camino conocido | dejó de existir un camino con lo que el jugador sabe |

```
Viaje detenido en la sala 3: hay enemigos.
Viaje detenido en la sala 2: recibiste daño.
Viaje detenido en la sala 2: ya no hay un camino conocido hasta la sala 6.
```

Destinos que se rechazan antes de empezar, indicando el motivo:

```
No puedes viajar a la sala 5: la has avistado pero no explorado.
No puedes viajar a la sala 9: no la conoces.
```

Pedir ir a la sala en la que ya se está termina de inmediato, sin gastar tiempo ni pasos.

## Lo que el viaje nunca hace

- No abre puertas, aunque el jugador tenga la llave (`FR-015`).
- No usa salas avistadas ni desconocidas como pasos intermedios.
- No sigue una ruta calculada de antemano: pide el siguiente paso antes de cada movimiento.

## En la bitácora de la partida

Cada paso se anota como un movimiento individual, igual que si el jugador lo hubiera tecleado. La
orden de ir a se anota además como un comentario, para depuración (`FR-021`).
