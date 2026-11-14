# Contrato: lo que la línea de tiempo necesita de las specs 001 y 003

La línea de tiempo reconstruye el pasado **deshaciendo cambios registrados** (research R1). Todo
estado que otra capacidad agregue y que no se registre como cambio reversible quedaría mal en las
consultas (FR-022).

## Spec 001 — Terreno y cazador (Sofía)

- Su FR-016 ya exige que todo cambio de terreno y cazadores sea reversible dentro del intervalo.
  Con eso basta.
- Se pide además: no registrar ni aplicar cambios de estado del juego **fuera** de una transacción
  abierta. Un cálculo reutilizado del cazador (caché de rutas) puede vivir fuera de las transacciones
  solo si **no** forma parte del estado observable. Si lo es, debe registrarse como cambio reversible
  como cualquier otro estado, porque la línea de tiempo no recalcula nada: solo deshace cambios.
- La línea no llama al código del cazador: no se necesita ninguna interfaz nueva.

## Spec 003 — Niebla e «ir a» (Steven)

- Los cambios del mapa conocido (explorar, avistar, recordar una puerta, antorcha) deben registrarse
  como cambios reversibles con el mismo mecanismo del historial, dentro de la transacción de la acción.
- Una consulta de **solo lectura** que, dado un estado de partida (vivo o un punto de control), devuelva el mapa
  conocido como datos: salas exploradas con sus salidas, costo y estado recordado de cada puerta, y
  salas avistadas. `historia` la llama sobre el estado reconstruido y el comando de mapa la usa sobre
  el estado vivo, así muestran lo mismo (clarificación de 2026-11-06).
- Mientras no exista, el resumen muestra `Mapa conocido: no disponible` y las pruebas que lo
  verifican quedan marcadas como dependientes de la 003.

## Spec 002 — Resolubilidad (Steven)

- Ya disponible: `JuegoService.obtener_informe_resolubilidad()`. 002-T049 y 002-T050 se implementan
  en la 004 con el formato de [cli-verificar.md](../../002-resolubilidad/contracts/cli-verificar.md).

## Cómo rehace la línea un cambio propio de otra capacidad

La línea deshace cambios y los vuelve a aplicar en cada consulta (research R3). Para un tipo de
cambio nuevo hay tres caminos, en este orden:

1. **`rehacer(estado)`**: el cambio sabe volver a aplicarse. Es lo más simple para cambios que
   modifican en su sitio una estructura propia (tablas hash del mapa conocido, estado del
   cazador). Debe dejar el estado exactamente como estaba antes de `deshacer`, en O(1) por hecho
   y sin copias (principio VII).
2. **`fotografiar_para_rehacer(inverso, estado)`**: el cambio anota en el inverso qué atributos,
   listas o diccionarios restaurar.
3. **Los helpers de `logica/mutaciones.py`** (`atributo`, `agregar`, `quitar`, `quitar_identidad`):
   no hace falta nada más.

Un tipo que no use ninguno de los tres hace fallar la consulta con un error que lo explica, antes de
tocar el estado.
