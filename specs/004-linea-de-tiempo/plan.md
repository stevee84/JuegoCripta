# Plan de implementación: Línea de tiempo y puntos de control

**Directorio**: `specs/004-linea-de-tiempo` | **Rama**: `joshua` | **Fecha**: 2026-11-07 |
**Spec**: [spec.md](./spec.md)

**Integrante**: Joshua Cabrera Bonilla. Secciones del enunciado: §3.6, §5.5, §5.6, §6.1, §7.3 y
Apéndice B. Este plan es el borrador de la sección §5.5 de `DECISIONES.md` (§2.4 del enunciado).

## Resumen

La línea de tiempo responde «¿cómo estaba la partida en el instante t, o antes de la acción #k?»
sin modificar la partida y sin guardar una copia por acción.

El enfoque es **reconstruir hacia atrás desde el punto de control siguiente**. Cada K acciones, la
línea copia en un solo paquete el estado de la partida y las transacciones de las K acciones que
terminan ahí. Para consultar la acción k se toma el primer paquete con m ≥ k, se hace una copia de
trabajo y se deshacen sobre ella las transacciones m … k con el mecanismo de deshacer que ya usa el
pergamino. Nunca se deshacen más de K acciones. El instante de cada decisión se guarda en un arreglo
contiguo, y una búsqueda binaria propia traduce t a la acción que le corresponde.

La línea se engancha en el historial reversible (archivo de Joshua), no en el motor (archivo de
Sofía). El detalle y las alternativas están en [research.md](./research.md).

## Contexto técnico

**Lenguaje**: Python 3.11, el del proyecto.

**Dependencias**: ninguna nueva. De la biblioteca estándar se usan `copy` (copia profunda de los
puntos de control), `pickle` (sección de la línea en el guardado) y `tracemalloc` (solo en
`--bench`). `requests` y `pygame` siguen siendo las únicas externas.

**Almacenamiento**: en memoria durante la partida; en el archivo de partida v10, como una sección
opaca que escribe y lee el guardado de Steven (ver
[contracts/guardado-v10.md](./contracts/guardado-v10.md)).

**Pruebas**: `pytest`, que también ejecuta las de `unittest`. Cada prueba nueva cita su FR.

**Plataforma**: escritorio, vista de consola y pygame. `--replay --hasta` y `--bench` sin vista.

**Tipo de proyecto**: aplicación MVC de un solo paquete, ya existente.

**Objetivos de rendimiento**: `historia` en menos de 50 ms con al menos 5 000 acciones y el K por
defecto, en el equipo local sin red ni renderizado (SC-001). Recorte por pergamino O(acciones
revertidas) ≤ 5 (FR-013).

**Restricciones**: constitución I y §6.2: sin `dict` ni `set` como índice, sin `heapq`, `bisect`,
`collections`, `sorted()` ni `.sort()`. La búsqueda binaria y los arreglos de la línea son propios.

**Escala**: partidas de hasta 5 000 o más acciones del jugador; criptas publicadas y sintéticas
deterministas por semilla en `--bench`.

**Incógnitas**: el costo de copiar el estado completo en cada consulta (R3). No bloquea el diseño:
la primera tarea lo mide y el plan B ya está definido.

## Verificación contra la constitución

*Puerta previa a la implementación. Revisada otra vez al cerrar el diseño (ver final).*

| Principio | Cómo lo cumple este plan |
|---|---|
| I. Estructuras propias | Los arreglos de la línea son `list` usadas como almacenamiento contiguo (permitido). La búsqueda del instante es una búsqueda binaria propia, sin `bisect`. No se usa `dict` ni `set` como índice. `copy`, `pickle` y `tracemalloc` no son estructuras de los problemas evaluados. |
| II. Acceso por id en O(1) | La línea no busca por id: ubica puntos de control por número de acción (aritmética sobre un arreglo) e instantes por búsqueda binaria. |
| III. Determinismo | Consultar no toca el azar vivo: se deshace sobre una copia (FR-005). El resultado no depende de K (FR-023, probado con varios K). |
| IV. Separación MVC | El resumen se arma en el controlador como líneas de texto; `--replay --hasta` lo imprime sin instanciar la vista. |
| V. Datos desde el servicio | La consulta no ejecuta reglas ni pide contenido: no hace solicitudes. Un archivo v8 o anterior se reporta incompatible (FR-031). |
| VI. Presupuesto de solicitudes | Ninguna operación de la línea hace solicitudes HTTP. |
| VII. Estado reversible sin copias completas | Las únicas copias guardadas son los puntos de control, uno cada K acciones. La copia de trabajo de cada consulta es temporal y se descarta (ver tabla de complejidad). Las acciones rechazadas no llegan a la línea. Las consultas no modifican el estado ni el historial del pergamino. |
| VIII. Contratos estables y cambios mínimos | No se toca `logica/motor_juego.py` (Sofía) ni `datos/guardado_binario.py` (Steven): el cambio de v10 lo hace Steven con el contrato de [guardado-v10.md](./contracts/guardado-v10.md). En archivos compartidos (`main.py`, `configuracion.py`, `controller/controlador_juego.py`, `vista/vista_pygame.py`) solo se agregan ramas o banderas. |
| IX. Rendimiento medido | `--bench` mide K = 10, 50 y 200, sin puntos de control, hacia adelante frente a hacia atrás, y repite las mediciones de P1 de punta a punta (FR-024 a FR-027). Todo se conecta en `main.py --bench`. |
| X. Especificación primero | spec.md confirmado en `b589c27` y `024e943`. Cada tarea citará sus FR. |
| XI. Pruebas | Las 1071 pruebas actuales deben seguir pasando. Las nuevas distinguen las que dependen de la spec 003. |

**Resultado**: pasa, con una desviación justificada (copia de trabajo temporal) y una desviación por
confirmar con el grupo (punto de control extra tras cargar), ambas en la tabla de complejidad.

## Estructuras de datos elegidas

| Problema (§5.5) | Estructura elegida | Complejidad | Alternativa descartada |
|---|---|---|---|
| Ubicar el punto de control de la acción k | Arreglo contiguo de puntos de control en orden de acción; índice = ⌈(k − 1) / K⌉ (ver [data-model.md](./data-model.md)) | O(1) | Recorrer la lista de puntos de control, O(n / K) (viola FR-019) |
| Traducir el instante t a una acción | Arreglo contiguo no decreciente de instantes de decisión + búsqueda binaria propia | O(log n) | Recorrido lineal O(n); árbol de búsqueda (más memoria, sin ventaja, porque solo se agrega al final) |
| Guardar los cambios entre puntos de control | Las transacciones existentes (lista doble de cambios), una por acción, dentro del paquete | Registrar O(1), deshacer O(cambios) | Guardar el estado completo por acción (viola FR-021) |
| Reconstruir | Copia de trabajo del paquete + deshacer ≤ K transacciones | O(tamaño del estado + cambios de ≤ K acciones) | Re-simular hacia adelante (R1); deshacer desde el estado actual, O(n) |
| Recortar al usar el pergamino | Quitar del final de los arreglos, descartar paquetes con m > n | O(acciones revertidas) ≤ 5 | Reconstruir la línea desde el principio |

## Componentes afectados y sus consumidores

| Archivo | Dueño | Cambio | Consumidores revisados |
|---|---|---|---|
| `logica/linea_tiempo.py` (nuevo) | Joshua | La línea: registrar, recortar, puntos de control, consultar | Historial, controlador, replay, `--bench` |
| `logica/historial_reversible.py` | Joshua | Método para vincular la línea; avisar al cerrar y al deshacer. Sin cambiar firmas existentes. | Motor, controlador, servicio, pruebas del historial |
| `logica/cambios.py` | Joshua | `TransaccionAccion`: registro aparte solo para la línea (R6) y deshacer parcial mientras se cumpla una condición (R4). Métodos nuevos; `revertir` no cambia. | Historial, servicio de inventario |
| `logica/servicio_inventario.py` | Joshua | Anotar en el registro de la línea recoger/soltar un pergamino y su consumo al retroceder (R6) | Motor, controlador |
| `controller/resumen_historia.py` (nuevo) | Joshua | Arma las líneas del resumen (FR-004) a partir de un estado | Controlador, replay |
| `controller/controlador_juego.py` | Steven y Joshua | Comandos `historia <t>`, `historia #k` y el del informe de resolubilidad (T050); línea de resolubilidad al iniciar (T049) | Vistas, pruebas del controlador |
| `controller/ejecutor_replay.py` | Joshua | Parámetro `hasta` en `reproducir` | `main.py`, pruebas del replay |
| `configuracion.py` | Steven | Banderas `--checkpoint-cada K` y `--hasta t`, con su validación | `main.py`, pruebas de configuración |
| `main.py` | Steven | Pasar K y `--hasta`; agregar el proveedor de mediciones de la línea a `--bench` | Todos |
| `vista/vista_consola.py` | Joshua | Mostrar el resumen y la línea de resolubilidad (ya muestra mensajes) | Controlador |
| `vista/vista_pygame.py` | Steven (mayor parte) | Botón o entrada para `historia` y panel para el resumen y la línea de resolubilidad. Cambio aislado en métodos nuevos. | Controlador |
| `benchmarks/linea_tiempo.py` (nuevo) | Joshua | Mediciones FR-024 a FR-027 | `main.py --bench` |
| `datos/guardado_binario.py` | Steven | **No lo toca Joshua.** Steven agrega la sección v10 con el contrato. | — |
| `logica/motor_juego.py` | Sofía | **Sin cambios.** | — |

## Contratos con otros integrantes

- **Steven, guardado v10**: [contracts/guardado-v10.md](./contracts/guardado-v10.md).
- **Steven, spec 003**: mapa conocido reversible y una consulta de solo lectura sobre un estado.
  Ver [contracts/dependencias.md](./contracts/dependencias.md).
- **Sofía, spec 001**: su FR-016 (todo cambio de terreno y cazadores reversible dentro del
  intervalo) cubre FR-022. Ver [contracts/dependencias.md](./contracts/dependencias.md).
- **Steven, spec 002**: T049 y T050 se implementan aquí sobre
  `JuegoService.obtener_informe_resolubilidad()` y el formato de
  [cli-verificar.md](../002-resolubilidad/contracts/cli-verificar.md) (FR-013 y FR-014 de la 002).

## Mediciones planificadas (`--bench`)

| Medición | Requisito | Variantes |
|---|---|---|
| Tiempo de `historia` (peor caso y promedio) con 5 000 acciones | SC-001, FR-024 | K = 10, 50, 200; sin puntos de control |
| Memoria retenida por la línea | FR-021, SC-005 | Mismos K; 2 500 frente a 5 000 acciones |
| Hacia atrás frente a hacia adelante | FR-024, §5.5 | Cripta sintética con todo el contenido cargado |
| Copia de trabajo frente a deshacer y rehacer en sitio | R3 | Solo si la copia supera la mitad del presupuesto |
| Retroceso con pergamino de punta a punta frente a copia completa | FR-025 | Carga de la Parte II |
| Replay completo y rechazo por versión | FR-026 | — |
| Vista ordenada del inventario y rechazo por capacidad | FR-027 | Peso, valor y nombre |

Todas usan calentamiento, repeticiones y criptas sintéticas deterministas por semilla
(constitución IX).

## Estructura del proyecto

### Documentación (esta capacidad)

```text
specs/004-linea-de-tiempo/
├── spec.md
├── plan.md              # este archivo
├── research.md          # fase 0
├── data-model.md        # fase 1
├── quickstart.md        # fase 1
├── contracts/
│   ├── cli-historia.md  # comandos y banderas
│   ├── guardado-v10.md  # contrato con Steven
│   └── dependencias.md  # lo que se pide a las specs 001 y 003
├── checklists/
│   └── requirements.md
└── tasks.md             # lo crea /speckit-tasks
```

### Código fuente (raíz del repositorio)

```text
logica/
├── linea_tiempo.py          # nuevo
├── historial_reversible.py  # vincular la línea
├── cambios.py               # registro solo de línea y deshacer parcial
└── servicio_inventario.py   # pergaminos en el registro de la línea
controller/
├── resumen_historia.py      # nuevo
├── controlador_juego.py     # comandos historia y resolubilidad
└── ejecutor_replay.py       # --hasta
vista/
├── vista_consola.py
└── vista_pygame.py
benchmarks/
└── linea_tiempo.py          # nuevo
configuracion.py, main.py    # banderas y --bench
tests/
├── test_logica/test_linea_tiempo.py         # nuevo
├── test_controller/test_historia.py         # nuevo
├── test_controller/test_replay_hasta.py     # nuevo
└── test_bench_linea_tiempo.py               # nuevo
```

**Decisión de estructura**: se sigue la organización MVC existente. Lo nuevo va en archivos nuevos;
lo existente solo gana métodos o ramas de comando.

## Seguimiento de complejidad

| Desviación | Por qué hace falta | Alternativa más simple descartada |
|---|---|---|
| Copia de trabajo temporal del punto de control en cada consulta | Deshacer es destructivo y el punto de control debe seguir intacto para la siguiente consulta. La copia dura lo que la consulta y nunca se guarda: no es un punto de control más (§3.6 limita los que se **guardan**). | Deshacer sobre el punto de control y rehacer (plan B de R3, más código delicado); re-simular (R1). |
| Tras cargar una partida puede haber un punto de control extra dentro de una misma ventana de K acciones | La cola de acciones posteriores al último punto de control se guarda junto con su estado para no perderla (FR-028). | Re-simular la cola al cargar, con el problema de contenido de R1. **Se consulta con el grupo** antes de implementar. |

## Revisión de la constitución después del diseño

Se revisó de nuevo con `data-model.md` y los contratos: no aparecen dependencias prohibidas, el
motor de Sofía y el guardado de Steven no se modifican, y cada requisito de rendimiento tiene su
medición en `--bench`. Las dos desviaciones siguen siendo las de la tabla anterior.
