# Investigación (fase 0): Línea de tiempo y puntos de control

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Fecha**: 2026-11-07

Este documento resuelve las incógnitas del contexto técnico antes del diseño. Cada decisión dice qué
se eligió, por qué y qué se descartó. Las decisiones marcadas **provisional** se confirman o se
cambian con las mediciones de `--bench` (FR-024) y el cambio, si lo hay, se documenta en
`DECISIONES.md` §5.5 (enunciado §7.1).

## Lo que ya existe y condiciona el diseño (comprobado en el código)

| Hecho | Dónde | Consecuencia |
|---|---|---|
| Cada acción del jugador y los eventos hasta su siguiente decisión forman **una** transacción de cambios reversibles. | `logica/motor_juego.py:445-468`, `logica/cambios.py` (`TransaccionAccion`) | La unidad «acción del jugador» de la spec ya existe. K cuenta transacciones. |
| Cada cambio guarda el **valor anterior** y una **referencia directa al objeto vivo** (no un id). Solo sabe deshacerse, no rehacerse. | `logica/cambios.py` (`CambioAtributo`, `CambioLista`, `CambioAgenda`…), `logica/mutaciones.py` | Un cambio solo se puede aplicar sobre los mismos objetos que lo registraron. Sobre una copia del estado hay que copiar estado y cambios **juntos** para que las referencias sigan apuntando a los mismos objetos (R2). |
| El estado del azar ya se registra como cambio en cada turno enemigo. | `logica/motor_juego.py:588` (`CambioAzar`) | Deshacer hacia atrás restaura también el azar; no hay que guardarlo aparte. |
| El reloj cambia solo con un cambio registrado, uno por evento con tiempo distinto. | `logica/motor_juego.py:686`, `logica/mutaciones.py` (`atributo`) | Se puede detener el deshacer dentro de una transacción justo cuando el reloj vuelve a ser ≤ t (R4). |
| El historial del pergamino guarda solo 5 transacciones y descarta las antiguas. | `logica/historial_reversible.py` | La línea de tiempo necesita su propio registro; no puede leer del historial. |
| Recoger o soltar un pergamino y consumir el pergamino al retroceder **no** se registran como cambio reversible (excepción de P1 §2.11). | `logica/motor_juego.py:507-528`, `logica/servicio_inventario.py:152-167` | Sin un registro adicional, la línea mostraría mal los pergaminos en el pasado (R6). |
| `copy.deepcopy` y `pickle` funcionan sobre el estado de una partida real **desde `f89b7b5`** (Sofía). Antes fallaban en la lista de enemigos de cada sala; la primera versión de este documento afirmaba que ya funcionaban porque se comprobó con un estado más simple. Lo detectó T001. | `dto/sala.py`, `tests/test_dto/test_sala_copia_serializacion.py` | Los puntos de control pueden ser una copia profunda del estado, tomada una vez cada K acciones, y el guardado v10 puede usar `pickle`. Las consultas no copian (R3). |
| El guardado binario ya está en v9 (Steven, spec 002). Al cargar, el historial del pergamino empieza vacío. | `datos/guardado_binario.py:21`, `controller/controlador_juego.py:129` | La línea de tiempo necesita la v10 (R8). El archivo es de Steven. |

## R1. ¿Reconstruir hacia adelante o hacia atrás?

**Decisión (provisional)**: **hacia atrás, desde el punto de control siguiente al instante pedido**.
Para responder «antes de la acción k», se toma el primer punto de control con número de acción
m ≥ k − 1 (su estado es el de antes de la acción m + 1) y se deshacen las transacciones m, m−1, …, k.
Como los puntos de control están cada K acciones, se deshacen m − k + 1 ≤ K transacciones (FR-018).

**Por qué**:
- Usa el mecanismo de deshacer que ya existe y que ya prueban las 1071 pruebas. Hacia adelante haría
  falta **rehacer**, que hoy no existe en ningún cambio.
- No ejecuta reglas del juego para consultar: no puede pedir contenido de salas al servicio ni gastar
  presupuesto de solicitudes (constitución VI), y no depende de que el motor de Sofía sea reentrante.
- El azar se restaura solo, porque ya es un cambio registrado (FR-020 no aplica: no se re-simula).

**Alternativas consideradas**:

| Alternativa | Por qué se descarta (o se deja solo en `--bench`) |
|---|---|
| **Hacia adelante re-simulando** desde el punto de control anterior: restaurar la copia y volver a ejecutar las acciones con el motor. | Una sala cuyo contenido se descargó después del punto de control figura sin cargar en la copia, y el motor rechaza entrar (`logica/motor_juego.py:376-378`). Para re-simular habría que volver a cargar contenido: solicitudes HTTP o cambios en la capa de datos de Steven. Además ejecuta todas las reglas (combate, efectos, cazadores) en cada consulta. **Se implementa solo dentro de `--bench`**, sobre criptas sintéticas con todo el contenido cargado, para la comparación que pide §5.5 y FR-024. |
| **Hacia adelante rehaciendo cambios**: guardar también el valor nuevo de cada cambio. | Hay que escribir un «rehacer» para cada tipo de cambio (listas, agenda, inventario), y eso duplica la lógica más delicada de la Parte I. R3 solo necesita un inverso temporal durante la consulta, que se captura al deshacer y no se guarda. |
| **Hacia atrás desde el estado actual**, sin puntos de control. | Consultar el inicio de una partida de 5 000 acciones obligaría a deshacer 5 000 transacciones: viola FR-018. Es la alternativa «sin puntos de control» que mide `--bench`. |
| **Una copia completa por acción** (K = 1 forzado). | Memoria = acciones × tamaño del estado: viola FR-021. Se mide como K = 1. |

## R2. ¿Qué es un punto de control si los cambios apuntan a objetos vivos?

**Decisión**: un punto de control en la acción m es un **paquete** que se copia en una sola
operación de copia profunda: el estado de la partida justo antes de la acción m + 1 **y** las
transacciones de las acciones m − K + 1 … m (la ventana que termina en él). Al copiarlos juntos,
cada cambio copiado apunta a los objetos copiados y no a los vivos, así que se puede deshacer
sobre la copia sin tocar la partida.

**Por qué**: es la única forma de deshacer sobre una copia sin cambiar los ~15 tipos de cambio de
`logica/cambios.py` para que trabajen con ids. Las transacciones dejan de estar duplicadas: lo que
queda en el paquete es la única copia de esa ventana (salvo R5).

**Alternativas**: cambios con ids estables en lugar de referencias (reescribir todos los cambios y
el motor de Sofía, descartado por la constitución VIII); copias del estado sin la ventana de
cambios (no se podría deshacer sobre ellas).

## R3. ¿Cómo se consulta sin destruir el punto de control?

**Decisión (corregida tras `/speckit-analyze`, hallazgo C1)**: **deshacer y rehacer en sitio**.
La consulta deshace directamente sobre el paquete del punto de control (o sobre el estado vivo, si la
acción pedida está después del último punto de control). Antes de deshacer cada cambio, anota su
**inverso**: un cambio que captura el valor actual (para un cambio de atributo, el valor que tiene
antes de deshacer). Arma el resumen y aplica los inversos en orden contrario, dentro de un bloque
`try/finally`, para que el paquete o el estado vivo queden exactamente como estaban aunque la consulta
falle. Las transacciones no se vacían ni se marcan como revertidas.

**Por qué**: el principio VII prohíbe las copias completas en memoria usadas como mecanismo de la
línea de tiempo, salvo los puntos de control. Una copia de trabajo por consulta, que era la primera
versión de este plan, es justamente eso. Deshacer y rehacer en sitio no copia nada: cuesta
O(cambios de ≤ K acciones) dos veces.

**Riesgo**: cada tipo de cambio necesita un inverso exacto. Los de atributo, dato y azar son
inmediatos; los de listas, agenda e inventario necesitan uno propio. **La primera tarea de
implementación mide el costo y comprueba que la restauración es exacta** (tarea de spike en
`tasks.md`).

**Resultado de T001** (2026-11-07, `python -m benchmarks.linea_tiempo`, `cripta-04` de 50 salas,
partida de 600 acciones reales, semilla 7, 3 de calentamiento y 15 repeticiones). Para que la partida
durara se le dio al jugador vida muy alta **solo en la medición**; es un peor caso, porque se activan
los enemigos de casi toda la cripta (unos 100 cambios por acción).

| K | Cambios deshechos | Deshacer: mediana / máximo | Deshacer + rehacer (estimado) | Copia completa por consulta |
|---|---|---|---|---|
| 10 | 1 060 | 5,6 / 36,3 ms | ≈ 11 ms típico, ≈ 73 ms peor | 86,6 / 135,2 ms |
| 50 | 5 228 | 30,1 / 93,0 ms | ≈ 60 ms típico | 314,2 / 384,5 ms |
| 200 | 20 825 | 109,4 / 145,7 ms | ≈ 219 ms típico | 1 511 / 1 760 ms |

- Deshacer 20 transacciones sobre una copia conjunta del estado da exactamente el estado de 20
  acciones antes, y la partida original no cambia: confirma R2.
- Rehacer todavía no existe (T004); se estima con el mismo costo que deshacer. La comprobación
  exacta queda en T003.
- La copia completa por consulta es de 8 a 14 veces más lenta: confirma descartarla.
- Copiar solo el estado (lo que hace un punto de control al crearse) cuesta 28,8 ms de mediana, y el
  estado serializado ocupa unos 422 KB. **Riesgo nuevo**: la acción que crea un punto de control suma
  ese costo y puede pasar el límite de 20 ms por ciclo de §6.1. Se mide en T041 y se documenta.

**Conclusión**: el mecanismo de R3 se mantiene; **K = 50 no cabe** en los 50 ms de §6.1 con esta carga.
Ver R7.

**Alternativa descartada**: copia de trabajo temporal por consulta (choca con el principio VII).
Solo se mide en `--bench` como alternativa, que es donde la constitución permite las alternativas.

## R4. ¿Cómo se responde un instante t que cae entre dos decisiones?

**Decisión**: se guarda, por cada acción, el **instante de su decisión** Dₖ en un arreglo contiguo
no decreciente. Para `historia <t>`:

1. Búsqueda binaria propia: k = la mayor acción con Dₖ ≤ t. Costo O(log n).
2. Si Dₖ = t, la respuesta es el estado antes de #k (regla de §3.6: «justo antes de tomarla»).
3. Si no, se reconstruye el estado antes de #(k+1) y se sigue deshaciendo la transacción k,
   cambio por cambio, **mientras el reloj sea mayor que t**. Los cambios de cada evento se
   registran después del cambio de reloj de ese evento, así que al detenerse quedan aplicados
   exactamente los eventos con tiempo ≤ t (FR-001, FR-002). La transacción k es la única deshecha a
   medias: el total sigue ≤ K.

**Alternativas**: buscar k recorriendo las acciones (O(n), viola FR-019); guardar un punto de
control por evento (viola FR-017).

## R5. ¿Dónde se engancha la línea de tiempo y cómo se recorta?

**Decisión**: la línea de tiempo se vincula al **historial reversible** (archivo de Joshua), no al
motor (archivo de Sofía):
- Al cerrar una transacción, el historial se la entrega a la línea junto con el reloj de la siguiente
  decisión. La línea la guarda en una **cola viva** (referencias, sin copiar).
- Al completar K acciones desde el último punto de control, la línea arma el paquete de R2.
- Al deshacer con un pergamino, el historial avisa y la línea **recorta**: quita del final de sus
  arreglos las acciones revertidas y descarta los puntos de control con m mayor que la nueva
  cantidad de acciones. Cuesta O(acciones revertidas), como máximo 5 (FR-013).

Para que el recorte pueda volver a armar la cola viva cuando descarta un punto de control, la línea
conserva las referencias vivas de las transacciones de las **últimas L = max(2K, K + 5) acciones**
(K + 5 porque un pergamino puede revertir hasta 5 acciones y después hay que seguir teniendo la cola
que va desde el punto de control anterior; con K = 1, 2K no alcanzaría). Es memoria de cambios (no de
copias) acotada por L + K, compatible con FR-021.

**Alternativas**: engancharse en `MotorJuego.ejecutar_accion` (archivo de Sofía, zona de choque
según el reparto); leer el log y re-ejecutar (es R1 hacia adelante).

## R6. Pergaminos irreversibles

**Decisión**: la transacción admite cambios con la marca **«solo línea de tiempo»**, en la misma
lista para conservar el orden; el pergamino los salta y nunca los deshace. Ahí van recoger y soltar un pergamino (que hoy no se registran) y,
al retroceder, el consumo del pergamino, anotado en la última transacción que sigue en la línea. Así:
- el pergamino de retroceso sigue igual (P1 §2.11 y FR-016 de la spec 001);
- la línea de tiempo muestra el pergamino en el inventario antes de usarlo y consumido después
  (FR-012).

Archivos: `logica/cambios.py`, `logica/historial_reversible.py`, `logica/servicio_inventario.py`
(los tres de Joshua). `logica/motor_juego.py` no cambia.

## R7. K por defecto

**Decisión (provisional, corregida con T001)**: **K = 10**. La primera versión decía K = 50, pero T001
mostró que con K = 50 deshacer y rehacer tarda unos 60 ms típicos, por encima de los 50 ms de §6.1.
Con K = 10 son unos 11 ms típicos. Costo: con 5 000 acciones son 500 puntos de control, unos 210 MB si
cada uno pesara lo que el estado serializado (422 KB); hay que medirlo con `tracemalloc`, porque en
memoria puede ser distinto. Valores medidos en `--bench`: **10, 50 y 200** (y 20 si la memoria de 10
resulta excesiva), más la alternativa sin puntos de control (FR-024). El valor final es el menor K que cumpla los 50 ms con
margen y el menor uso de memoria; se justifica con la tabla de `--bench` en `DECISIONES.md` §5.5.

**Cómo se mide la memoria**: `tracemalloc` (biblioteca estándar, solo en `--bench`), midiendo los
bytes retenidos por la línea de tiempo después de 5 000 acciones, separado del estado de la partida.

## R8. Persistencia y contrato con Steven (guardado v10)

**Decisión**: el archivo de partida sube a **v10** y gana una sección de bytes opaca, con su
longitud, que **produce y consume la línea de tiempo**. El guardado de Steven solo la escribe y la lee
tal cual: no necesita entender su contenido.

**Corregido tras `/speckit-analyze` (hallazgo C2)**: la sección serializa **en una sola operación**
el estado vivo y la línea completa (K, instantes, puntos de control y cola). Como la cola apunta a
objetos del estado vivo, serializarlos juntos conserva esas referencias. **Al cargar, el estado vivo
de la partida es el que devuelve la línea de tiempo**; el resto del archivo de Steven se sigue usando
para validar cabecera, versión y compatibilidad. Así, después de cargar no queda ninguna copia
completa además de los puntos de control, y los puntos de control siguen en múltiplos de K.

La primera versión de este plan convertía la cola guardada en un punto de control extra, lo que
violaba «como máximo uno cada K» (§3.6, FR-017, principio VII). Re-simular la cola al cargar también
se descartó, por el problema de contenido de R1. La serialización usa `pickle` (biblioteca estándar).
**Límite conocido**: `pickle` puede ejecutar código al cargar un archivo malicioso; se acepta porque
el archivo de partida es local y lo produce el propio juego. Se documenta en `DECISIONES.md` §5.5.

Un archivo v8 o anterior (Parte I y comienzos de la Parte II) se sigue reportando como incompatible
con el mecanismo que ya usó Steven de v8 a v9 (FR-031). Un v9 se reporta incompatible también: no
tiene línea de tiempo.

## R9. Contratos con las otras specs

- **Spec 001 (Sofía)**: su FR-016 ya exige que todo cambio de terreno y cazadores sea reversible
  dentro del intervalo. Eso basta para FR-022. Se le pide que no registre cambios fuera de una
  transacción abierta.
- **Spec 003 (Steven, aún sin spec)**: se le pide (1) que los cambios del mapa conocido sean
  reversibles con el mismo mecanismo; (2) una función de solo lectura que, dado un estado, devuelva el
  mapa conocido como datos (exploradas con salidas, costos y puertas recordadas, y avistadas), para que
  `historia` la llame sobre el estado reconstruido. Mientras no exista, el resumen muestra «mapa
  conocido: no disponible» y la prueba correspondiente queda marcada como dependiente.
- **Spec 002 (Steven)**: T049 y T050 se hacen en esta spec, consumiendo
  `JuegoService.obtener_informe_resolubilidad()` con el formato de
  [cli-verificar.md](../002-resolubilidad/contracts/cli-verificar.md).

## R10. ¿Dónde se arma el texto del resumen?

**Decisión**: en una función del controlador que devuelve líneas de texto a partir de un estado.
La usan la consola, pygame y `--replay --hasta`, así los tres imprimen lo mismo (FR-009,
clarificación de 2026-11-06) y `--replay` sigue sin instanciar la vista (constitución IV).
