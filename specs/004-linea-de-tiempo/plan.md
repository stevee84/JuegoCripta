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
terminan ahí. Para consultar «antes de la acción k» se toma el primer paquete con m ≥ k − 1, se
deshacen **sobre el paquete mismo** las transacciones m … k anotando el inverso de cada cambio, se
arma el resumen y se aplican los inversos para dejarlo como estaba. Nunca se deshacen más de K
acciones y la consulta no copia el estado (principio VII). El instante de cada decisión se guarda en un arreglo
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

**Incógnitas**: el costo de deshacer y rehacer en sitio con la carga real, y que cada tipo de cambio
tenga un inverso exacto (R3). La primera tarea lo mide y lo comprueba.

## Verificación contra la constitución

*Puerta previa a la implementación. Revisada otra vez al cerrar el diseño (ver final).*

| Principio | Cómo lo cumple este plan |
|---|---|
| I. Estructuras propias | Los arreglos de la línea son `list` usadas como almacenamiento contiguo (permitido). La búsqueda del instante es una búsqueda binaria propia, sin `bisect`. No se usa `dict` ni `set` como índice. `copy`, `pickle` y `tracemalloc` no son estructuras de los problemas evaluados. |
| II. Acceso por id en O(1) | La línea no busca por id: ubica puntos de control por número de acción (aritmética sobre un arreglo) e instantes por búsqueda binaria. |
| III. Determinismo | Consultar deja el azar y todo el estado exactamente como estaban: lo deshecho se rehace en un `try/finally` (FR-005). El resultado no depende de K (FR-023, probado con varios K). |
| IV. Separación MVC | El resumen se arma en el controlador como líneas de texto; `--replay --hasta` lo imprime sin instanciar la vista. |
| V. Datos desde el servicio | La consulta no ejecuta reglas ni pide contenido: no hace solicitudes. Un archivo v8 o anterior se reporta incompatible (FR-031). |
| VI. Presupuesto de solicitudes | Ninguna operación de la línea hace solicitudes HTTP. |
| VII. Estado reversible sin copias completas | Las únicas copias completas en memoria son los puntos de control, uno cada K acciones, también después de cargar (R8). Las consultas no copian: deshacen y rehacen en sitio (R3). Las acciones rechazadas no llegan a la línea. Las consultas dejan el estado y el historial del pergamino como estaban. |
| VIII. Contratos estables y cambios mínimos | No se toca `logica/motor_juego.py` (Sofía) ni `datos/guardado_binario.py` (Steven): el cambio de v10 lo hace Steven con el contrato de [guardado-v10.md](./contracts/guardado-v10.md). En archivos compartidos (`main.py`, `configuracion.py`, `controller/controlador_juego.py`, `vista/vista_pygame.py`) solo se agregan ramas o banderas. |
| IX. Rendimiento medido | `--bench` mide K = 10, 50 y 200, sin puntos de control, hacia adelante frente a hacia atrás, y repite las mediciones de P1 de punta a punta (FR-024 a FR-027). Todo se conecta en `main.py --bench`. |
| X. Especificación primero | spec.md confirmado en `b589c27` y `024e943`. Cada tarea citará sus FR. |
| XI. Pruebas | Las 1071 pruebas actuales deben seguir pasando. Las nuevas distinguen las que dependen de la spec 003. |

**Resultado**: pasa, sin desviaciones. La primera versión tenía dos (una copia de trabajo por
consulta y un punto de control extra tras cargar); `/speckit-analyze` las marcó como críticas contra
el principio VII y se corrigieron en R3 y R8.

## Estructuras de datos elegidas

| Problema (§5.5) | Estructura elegida | Complejidad | Alternativa descartada |
|---|---|---|---|
| Ubicar el punto de control de la acción k | Arreglo contiguo de puntos de control en orden de acción; índice = ⌈(k − 1) / K⌉ (ver [data-model.md](./data-model.md)) | O(1) | Recorrer la lista de puntos de control, O(n / K) (viola FR-019) |
| Traducir el instante t a una acción | Arreglo contiguo no decreciente de instantes de decisión + búsqueda binaria propia | O(log n) | Recorrido lineal O(n); árbol de búsqueda (más memoria, sin ventaja, porque solo se agrega al final) |
| Guardar los cambios entre puntos de control | Las transacciones existentes (lista doble de cambios), una por acción, dentro del paquete | Registrar O(1), deshacer O(cambios) | Guardar el estado completo por acción (viola FR-021) |
| Reconstruir | Deshacer ≤ K transacciones sobre el paquete, anotando inversos, y rehacer al terminar | O(cambios de ≤ K acciones) | Copia de trabajo por consulta (principio VII); re-simular hacia adelante (R1); deshacer desde el estado actual, O(n) |
| Recortar al usar el pergamino | Quitar del final de los arreglos, descartar paquetes con m > n | O(acciones revertidas) ≤ 5 | Reconstruir la línea desde el principio |

## Componentes afectados y sus consumidores

| Archivo | Dueño | Cambio | Consumidores revisados |
|---|---|---|---|
| `logica/linea_tiempo.py` (nuevo) | Joshua | La línea: registrar, recortar, puntos de control, consultar | Historial, controlador, replay, `--bench` |
| `logica/historial_reversible.py` | Joshua | Método para vincular la línea; avisar al cerrar y al deshacer. Sin cambiar firmas existentes. | Motor, controlador, servicio, pruebas del historial |
| `logica/cambios.py` | Joshua | `TransaccionAccion`: cambios marcados «solo línea» (R6), deshacer mientras se cumpla una condición sin vaciar la transacción (R4) y el inverso de cada tipo de cambio para rehacer (R3). Métodos nuevos; `revertir` no cambia. | Historial, servicio de inventario |
| `logica/servicio_inventario.py` | Joshua | Anotar en el registro de la línea recoger/soltar un pergamino y su consumo al retroceder (R6) | Motor, controlador |
| `service/juego_service.py` | Steven y Joshua | Crear y vincular la línea al iniciar una partida, en el mismo punto donde hoy se vincula el historial (T010). Solo un método o rama nueva. | Controlador, replay, `--bench`, pruebas del servicio |
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
| Costo de crear un punto de control frente al límite de 20 ms por ciclo (§6.1) | FR-017, riesgo de T001 | Cripta de referencia; copia del estado ≈ 29 ms en T001 |
| Hacia atrás frente a hacia adelante | FR-024, §5.5 | Cripta sintética con todo el contenido cargado |
| Deshacer y rehacer en sitio frente a copia de trabajo por consulta | R3 | La copia solo como alternativa descartada |
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

Sin desviaciones de la constitución.

Las dos que tenía la primera versión del plan se corrigieron después de `/speckit-analyze`:

| Desviación original | Por qué violaba la constitución | Corrección |
|---|---|---|
| Copia de trabajo temporal del punto de control en cada consulta | Principio VII: las únicas copias completas en memoria son los puntos de control | Deshacer y rehacer en sitio (R3) |
| Punto de control extra tras cargar una partida | §3.6, FR-017 y principio VII: como máximo uno cada K | Serializar juntos el estado vivo y la línea; al cargar, el estado vivo sale de la línea (R8) |

## Revisión de la constitución después del diseño

Se revisó de nuevo con `data-model.md` y los contratos: no aparecen dependencias prohibidas, el
motor de Sofía y el guardado de Steven no se modifican (el cambio de v10 lo hace Steven con el
contrato), las consultas no copian el estado y cada requisito de rendimiento tiene su medición en
`--bench`.
