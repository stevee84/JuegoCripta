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
| `copy.deepcopy` ya funciona sobre el estado de la partida. | `benchmarks/benchmark_ciclo_real_integrante1.py:60` | Los puntos de control pueden ser una copia profunda del estado. Su costo está sin medir (R3). |
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
| **Hacia adelante rehaciendo cambios**: guardar también el valor nuevo de cada cambio. | Hay que escribir un «rehacer» para cada tipo de cambio (listas, agenda, inventario), y eso duplica la lógica más delicada de la Parte I. Queda como plan B de R3 si copiar el punto de control resulta caro. |
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

**Decisión (provisional)**: cada consulta hace **una copia de trabajo** del paquete, deshace sobre
ella como máximo K transacciones, arma el resumen y descarta la copia. La copia es temporal: dura lo
que dura la consulta y nunca se guarda, así que no es un punto de control adicional.

**Riesgo**: el costo de copiar el estado completo no está medido. Con la cripta de referencia y
5 000 acciones puede comerse parte importante de los 50 ms. **La primera tarea de implementación es
medirlo** (tarea de spike en `tasks.md`).

**Plan B (si la copia no cabe en el presupuesto)**: deshacer **sobre el paquete mismo**, guardando
mientras se deshace un cambio inverso de cada cambio (para un cambio de atributo, el valor que tenía
antes de deshacer), y al terminar la consulta aplicar esos inversos para dejar el paquete como
estaba. Evita la copia, pero exige un inverso exacto por tipo de cambio.

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
conserva las referencias vivas de las transacciones de las **últimas 2K acciones**. Es memoria de
cambios (no de copias) acotada por 2K, compatible con FR-021.

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

**Decisión (provisional)**: **K = 50**. Con 5 000 acciones son 100 puntos de control, y una consulta
deshace como máximo 50 transacciones. Valores medidos en `--bench`: **10, 50 y 200**, más la
alternativa sin puntos de control (FR-024). El valor final es el menor K que cumpla los 50 ms con
margen y el menor uso de memoria; se justifica con la tabla de `--bench` en `DECISIONES.md` §5.5.

**Cómo se mide la memoria**: `tracemalloc` (biblioteca estándar, solo en `--bench`), midiendo los
bytes retenidos por la línea de tiempo después de 5 000 acciones, separado del estado de la partida.

## R8. Persistencia y contrato con Steven (guardado v10)

**Decisión**: el archivo de partida sube a **v10** y gana una sección de bytes opaca, con su
longitud, que **produce y consume la línea de tiempo**. El guardado de Steven solo la escribe y la lee
tal cual: no necesita entender su contenido. La sección contiene: K, los arreglos de números de
acción e instantes de decisión, los paquetes de puntos de control y la cola viva copiada junto con el
estado actual. La serialización usa `pickle` (biblioteca estándar, permitida).

Al cargar, la cola guardada se convierte en el punto de control de la acción en la que se guardó.
**Desviación conocida**: tras una carga puede haber, en una sola ventana de K acciones, un punto de
control más de los permitidos. Queda en la tabla de complejidad del plan y se consulta con el grupo.
La alternativa sin desviación (re-simular la cola al cargar) tiene el problema de contenido de R1.

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
  `historia` la llame sobre la copia reconstruida. Mientras no exista, el resumen muestra «mapa
  conocido: no disponible» y la prueba correspondiente queda marcada como dependiente.
- **Spec 002 (Steven)**: T049 y T050 se hacen en esta spec, consumiendo
  `JuegoService.obtener_informe_resolubilidad()` con el formato de
  [cli-verificar.md](../002-resolubilidad/contracts/cli-verificar.md).

## R10. ¿Dónde se arma el texto del resumen?

**Decisión**: en una función del controlador que devuelve líneas de texto a partir de un estado.
La usan la consola, pygame y `--replay --hasta`, así los tres imprimen lo mismo (FR-009,
clarificación de 2026-11-06) y `--replay` sigue sin instanciar la vista (constitución IV).
