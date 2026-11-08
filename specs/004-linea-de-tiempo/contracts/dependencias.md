# Contrato: lo que la línea de tiempo necesita de las specs 001 y 003

La línea de tiempo reconstruye el pasado **deshaciendo cambios registrados** (research R1). Todo
estado que otra capacidad agregue y que no se registre como cambio reversible quedaría mal en las
consultas (FR-022).

## Spec 001 — Terreno y cazador (Sofía)

- Su FR-016 ya exige que todo cambio de terreno y cazadores sea reversible dentro del intervalo.
  Con eso basta.
- Se pide además: no registrar ni aplicar cambios de estado del juego **fuera** de una transacción
  abierta. Un cálculo reutilizado del cazador (caché de rutas) puede vivir fuera de las transacciones
  solo si **no** forma parte del estado observable. Si lo es, debe reconstruirse desde cero sobre una
  copia sin cambiar la decisión (equivalencia observable de §3.2).
- La línea no llama al código del cazador: no se necesita ninguna interfaz nueva.

## Spec 003 — Niebla e «ir a» (Steven)

- Los cambios del mapa conocido (explorar, avistar, recordar una puerta, antorcha) deben registrarse
  como cambios reversibles con el mismo mecanismo del historial, dentro de la transacción de la acción.
- Una consulta de **solo lectura** que, dado un estado de partida (vivo o copia), devuelva el mapa
  conocido como datos: salas exploradas con sus salidas, costo y estado recordado de cada puerta, y
  salas avistadas. `historia` la llama sobre la copia reconstruida y el comando de mapa la usa sobre
  el estado vivo, así muestran lo mismo (clarificación de 2026-11-06).
- Mientras no exista, el resumen muestra `Mapa conocido: no disponible` y las pruebas que lo
  verifican quedan marcadas como dependientes de la 003.

## Spec 002 — Resolubilidad (Steven)

- Ya disponible: `JuegoService.obtener_informe_resolubilidad()`. T049 y T050 se implementan en la
  004 con el formato de [cli-verificar.md](../../002-resolubilidad/contracts/cli-verificar.md).
