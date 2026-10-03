# Cierre del Integrante 1 — parte 3

## Estado y auditoría inicial

Referencia de trabajo: rama `Sofia`, `HEAD 90bf9f9` (`parte 2`). Se conservaron
todos los cambios locales; no se cambió de rama ni se hizo reset, commit o push.
La suite de referencia, ejecutada antes de modificar, fue de **403 pruebas
aprobadas en 4.51 s**.

### Ya implementado al comenzar

- DTO con IDs de sala `int` e IDs de instancia `str`, mapa y conexiones.
- Montículo mínimo, orden `(tiempo, secuencia)`, intervalos por velocidad y
  secuencia nueva al reprogramar.
- Combate con azar centralizado, activación, guardianes, errantes y rastreadores.
- Rastro local fresco, desempate numérico, actualización y reversión.
- Historial de cinco intervalos y cambios pequeños, sin copiar la partida.
- Veneno, antídoto, regeneración, antorcha, velocidad temporal y trampas.
- Formato binario v2 marcado como no reanudable al reconstruirse.

### Pendientes propios encontrados y completados

- Llaves, cierre automático robusto y condición exacta de salida.
- Muerte común con botín preparado, cancelación y reversión determinista.
- Estado final y datos requeridos por el registro de resultados.
- Conexión del pergamino de retroceso con motor, inventario e historial.
- Eliminación de recorridos globales de agenda mediante posiciones e índices
  ordenados propios.
- Adaptación explícita de contenido externo y validación de fichas resueltas.

### Ajustes compartidos mínimos

- `ServicioInventario` reconoce y consume pergaminos sin registrarlos como
  cambios reversibles.
- `Inventario.restaurar_retiro` tolera únicamente la desaparición irreversible
  de un pergamino vecino; sigue rechazando una posición ocupada por otra
  modificación.
- `DecodificadorDatos` adapta la forma publicada por las fuentes a los DTO del
  Integrante 1. No realiza solicitudes.

## Reglas comprobadas del enunciado

- **§2.3, página 5:** costos base, intervalo
  `max(1, costo * 100 // velocidad)` y prioridad nueva al reprogramar.
- **§2.4–§2.6, páginas 5–7:** activación, turnos, combate, muerte y cancelación
  de actividad futura.
- **§2.7, página 7:** fichas de llave y pergamino, objetos no consumibles y
  acciones de inventario.
- **§2.8–§2.9, páginas 7–8:** salida/victoria, botín y retroceso por intervalos.
- **§2.10–§2.11, páginas 8–9:** efectos temporales, eventos posteriores y
  reversión completa sin instantáneas del estado.
- **§3.3–§3.4, páginas 11–12:** contenido y catálogo en lotes; los datos
  publicados se contrastaron además con el OpenAPI y la cripta disponible.
- **§4.1, página 13:** agenda por `(tiempo, secuencia)`, unicidad y acceso sin
  recorridos globales para acciones pendientes.
- **§4.3, página 13:** fichas resueltas antes de simular; ningún evento consulta
  API, disco o repositorios.
- **§4.10, página 15:** versión del guardado e incompatibilidad explícita.
- **Sección de rendimiento, página 17:** intervalo de 10 000 eventos por debajo
  del límite de 2 s, excluyendo preparación, I/O y renderizado.

Las convenciones ambiguas de la parte 2 —vencimiento exclusivo de veneno,
reemplazo de veneno y rechazo de una segunda antorcha/velocidad— se conservan
como decisiones del proyecto, no como reglas textuales del PDF.

## Funcionalidad completada

### Llaves y puertas

`ABRIR` busca en todo el inventario una instancia cuya ficha resuelta coincida
con `puerta.llave_requerida` y tenga clase `llave`. Una llave incorrecta,
ausente o sin resolver rechaza antes de abrir historial; la correcta no se
consume. Abrir cuesta 50 y no mueve al jugador.

Una puerta conserva la referencia y el ID de su cierre pendiente. El
despachador exige identidad de referencia, no solo igualdad de ID, de modo que
un evento antiguo restaurado o recreado después de un retroceso no puede cerrar
una apertura posterior. Los enemigos solo recorren puertas abiertas; no hay
ruta que les permita abrirlas.

### Muerte y botín

El adaptador crea antes de simular las instancias declaradas en `suelta`, con
IDs deterministas `botin:<actor>:<posición>` y fichas resueltas. Los objetos del
suelo que el API publica solo por tipo reciben de forma análoga
`objeto:<sala>:<posición>`. No se usa azar, red ni almacenamiento durante una
muerte.

`ReglasCombate.procesar_muerte` sigue siendo la única vía para combate, veneno
y trampas. Procesa una muerte una vez, cancela eventos y efectos del actor,
deposita las mismas instancias preparadas, actualiza actividad y contador, y
registra cada mutación. Deshacer restaura botín, vida, actividad, contador,
agenda, efectos y estado del generador. Repetir con la misma semilla produce las
mismas notificaciones y daño.

### Victoria y resultado

Solo se declara victoria al entrar en `sala_salida_id` por la puerta de salida
correspondiente y conservar la ficha `llave_salida_id`. Poseer la llave sin
entrar o entrar en otra sala no gana. Una trampa letal al entrar prevalece y no
se declara victoria.

El final establece `fin_partida` como `VICTORIA` o `DERROTA`, detiene la
simulación y mantiene `victoria` separada. `EstadoPartida.datos_resultado()`
expone jugador, cripta, versión, acciones, enemigos derrotados, tiempo final y
resultado para que el Integrante 3 lo entregue a su repositorio de puntajes.

### Pergaminos

`RETROCEDER` consume el pergamino seleccionado, cuesta 0, no abre un intervalo,
no actualiza rastro, no avanza el reloj y no programa disponibilidad. Cada uso
extrae del historial un intervalo distinto; el límite continúa siendo cinco.

Recoger, soltar y consumir pergaminos no incorpora el traslado del objeto al
historial, aunque recoger/soltar siguen siendo acciones ordinarias cuyo reloj y
eventos sí pueden deshacerse. Un pergamino consumido nunca reaparece. Se permite
retroceder el intervalo final después de victoria o derrota; la validación se
hace antes del bloqueo genérico de partida terminada.

### Datos y fichas

`FuenteOffline` conserva la forma externa:

```json
{"contenido": [{"sala": 1, "enemigos": [], "objetos": [], "trampas": []}]}
```

`DecodificadorDatos.convertir_contenido` la adapta explícitamente. El camino
interno del guardado continúa aceptando claves `int`; una clave textual no se
convierte silenciosamente. Enemigos, objetos, trampas y botín externos exigen
su ficha. `aplicar_generales` vincula versiones, sala y llave de salida.

El OpenAPI y el catálogo publicado no contienen `veneno` ni un campo que
identifique qué enemigo, objeto o trampa lo aplica. Por ello no se conectó un
origen ficticio. `GestorEfectos.aplicar_veneno` queda preparado y probado para
cuando datos/persistencia proporcionen una relación documentada.

## Agenda: diseño y complejidad real

Se añadió `IndiceOrdenado`, un AVL propio. La agenda mantiene tres índices:
ID, prioridad y `(destinatario, ID)`. Cada `Evento` mantiene su posición en el
montículo; todos los intercambios, extracciones, cancelaciones y restauraciones
la actualizan.

| Operación | Complejidad |
| --- | --- |
| Ver siguiente | `O(1)` |
| Buscar por ID | `O(log n)` |
| Programar/restaurar | `O(log n)` |
| Extraer/cancelar por ID | `O(log n)` |
| Reprogramar | `O(log n)` |
| Eventos de actor | `O(log n + k)` |
| Cancelar todos los eventos de actor | `O(log n + k log n)` |
| Cancelar los `k` eventos conocidos de un efecto | `O(k log n)` |
| Recorrer para inspección/guardado | `O(n)` |

`MonticuloMinimo.buscar_por_id` y `eliminar(id)` se mantienen por compatibilidad
estructural y cuestan `O(n)`, pero `AgendaEventos` no los llama. Cambiar velocidad
y activar enemigos consultan el índice de destinatario. No se añadió tabla hash,
`dict` de índice ni ordenamiento de biblioteca.

La reversión usa las mismas operaciones indexadas: restaurar o quitar un evento
actualiza AVL y posición. Las pruebas prohíben deliberadamente
`agenda.recorrer()` durante cambio de velocidad, activación y cancelación por
actor.

## Archivos modificados en esta parte

- `dto/estado_partida.py`: metadatos de salida/versiones, tipo de final y datos
  de resultado.
- `dto/actor.py`: ficha de tipo y botín preparado.
- `dto/evento.py`: posición de montículo.
- `dto/objeto_instancia.py`: validación estricta de ambos IDs.
- `dto/sala.py`: referencias de cierre y rearme vigentes.
- `estructuras/indice_ordenado.py`: AVL propio nuevo.
- `estructuras/monticulo_minimo.py`: posiciones actualizadas y eliminación por
  referencia.
- `logica/agenda_eventos.py`: índices AVL y operaciones sin recorrido global.
- `logica/comportamiento_enemigos.py`: acepta la etiqueta publicada
  `guardián`, además de la variante histórica sin tilde.
- `logica/motor_juego.py`: llaves, victoria, pergaminos y consultas indexadas.
- `logica/reglas_combate.py`: botín y estado de derrota.
- `logica/inventario.py`: restauración coherente ante un vecino irreversible.
- `logica/servicio_inventario.py`: identificación y consumo de pergaminos.
- `logica/gestor_efectos.py`: documentación de la complejidad corregida.
- `datos/decodificador_datos.py`: adaptación externa, fichas, botín y generales.
- `tests/test_logica/test_cierre_integrante1_parte3.py`: regresiones de cierre.
- `benchmarks/benchmark_agenda_integrante1.py`: medición reproducible.
- `docs/revision_efectos_trampas_parte2.md`: pendiente lineal marcado como
  resuelto por esta parte.

## Pruebas y medición ejecutadas

Referencia previa:

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q
```

Resultado: **403 aprobadas en 4.51 s**.

Pruebas relacionadas finales:

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q \
  tests/test_logica/test_cierre_integrante1_parte3.py \
  tests/test_datos/test_decodificador.py \
  tests/test_datos/test_fuente_offline.py \
  tests/test_logica/test_motor_juego.py \
  tests/test_logica/test_reglas_combate.py \
  tests/test_logica/test_agenda_eventos.py \
  tests/test_estructuras/test_monticulo_minimo.py \
  tests/test_integracion_sofia.py \
  tests/test_logica/test_efectos_trampas_parte2.py \
  tests/test_flujo_sofia.py
```

Resultado final relacionado: **130 aprobadas en 2.69 s**.

Suite completa final:

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q
```

Resultado: **424 aprobadas en 4.29 s, 0 fallidas**.

Medición:

```bash
/tmp/opencode/juegocripta-venv/bin/python -m benchmarks.benchmark_agenda_integrante1
```

Entorno: Python 3.14.4, WSL2 Linux 6.18.40.1, x86_64. Escenario: agenda
preparada con 10 000 eventos; se mide solo extracción indexada hasta vaciarla.
Resultado final: **10 000 eventos en 0.166061 s**, por debajo de 2 s. Una medición
aislada verifica el escenario, no demuestra por sí sola la complejidad; esta se
deriva además de heap y AVL.

## Persistencia: datos que aún deben guardarse

La versión binaria sigue siendo 2 y `PartidaService.cargar` conserva
`reanudable=False`. Para una carga fiel el Integrante 2 deberá serializar y
reconstruir, como mínimo:

- reloj, secuencia de agenda, eventos y sus datos/referencias;
- estado completo y posición del generador de azar;
- inventario, cursor, equipo, ubicaciones y pergaminos consumidos/trasladados;
- efectos activos y sus eventos pendientes;
- puertas, referencia/ID de cierre, trampas y referencia/ID de rearme;
- actores, fichas, botín preparado/suelto, actividad y muerte procesada;
- historial de cinco intervalos y cambios reversibles;
- rastros, salas visitadas, estadísticas, victoria/derrota y versiones.

No se cambió `reanudable` a verdadero ni se debilitó la detección de versión.

## Ambigüedades y bloqueos concretos

- El API publica objetos de sala y entradas de `suelta` solo como IDs de ficha,
  sin ID de instancia. Se adoptó un ID determinista basado en sala/actor y
  posición; no se usa azar ni se genera durante un evento.
- El veneno no tiene origen expresable en el OpenAPI actual: no aparece un campo
  `veneno`, daño periódico ni relación equivalente en enemigo, objeto o trampa.
  Falta que el contrato de datos identifique origen, objetivo y daño de la
  aplicación. El mecanismo temporal no está bloqueado; solo su disparador normal.
- La restauración de un objeto ordinario cuyo vecino era un pergamino consumido
  usa el vecino superviviente. Una posición ocupada por otra modificación sigue
  siendo un error, para no ocultar corrupción del inventario.
- Las decisiones ambiguas de efectos adoptadas en la parte 2 se mantienen y
  están enumeradas en `docs/revision_efectos_trampas_parte2.md`.
- El arranque normal, la carga reanudable y el registro final dependen de módulos
  de los Integrantes 2 y 3; no se simularon como completos.

## Pendientes separados de los compañeros

### Integrante 2 — datos y persistencia

- Actualizar `ClienteAPI` al contrato HTTP publicado actual: rutas GET,
  parámetros por lote y envoltorio `entidades` del catálogo.
- Conectar generales, páginas, contenido, catálogo, caché y precarga para
  construir una partida normal; hoy `main.py` solo crea estado con `--demo`.
- Completar los estados de precarga y resolver todas las fichas antes del motor.
- Diseñar una versión binaria posterior que conserve el estado reanudable
  enumerado arriba.

### Integrante 3 — interacción y operaciones

- Equipar/desequipar, bonificaciones y demás usos no asignados aquí, incluida la
  poción curativa publicada.
- Integrar el registro append-only, replay y repositorio de puntajes; sus métodos
  continúan pendientes.
- Completar arranque normal, comandos/vistas finales y acceso interactivo al
  pergamino después del fin si la interfaz decide ofrecerlo.
- Completar ordenamientos, modo `--bench`, evidencia y entregables generales.

## Cómo probar el flujo integrado

1. Ejecutar la suite completa con el comando indicado arriba.
2. Ejecutar el benchmark con `python -m benchmarks.benchmark_agenda_integrante1`.
3. La regresión
   `test_flujo_controlador_servicio_motor_abre_gana_y_retrocede` atraviesa
   controlador → servicio → motor: abre con llave, entra a salida, gana y usa un
   pergamino para restaurar el intervalo final.
4. La regresión de fuente offline crea archivos reales, filtra contenido,
   resuelve catálogo y adapta enemigos, objetos, trampas y botín.

## Confirmación de alcance

Los requisitos verificables de **simulación y reglas del Integrante 1** quedan
completos. El proyecto global no está terminado: continúan los pendientes de
datos/persistencia e interacción/operaciones listados arriba. No se inició ningún
trabajo fuera de esas conexiones mínimas.
