# Quickstart de validación: Terreno y cazador

Esta guía describe cómo validar la futura implementación. En esta fase no se crean pruebas ni código.

## Prerrequisitos

- Rama Git real: `Sofia`.
- Soporte mínimo Python 3.11. Para reproducir la validación local previa, usar el entorno del proyecto `.venv` con Python 3.12.10 y `requirements.txt`; el Python general del sistema no sustituye ese entorno.
- Paquete offline de fixtures para pruebas sin red.
- Contrato de datos/guardado con Steven acordado y condiciones de Joshua implementadas antes de ejecutar pruebas de integración cruzada; la frontera de 004 está aceptada solo de forma condicionada.

## Comandos previstos

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -rs --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_restricciones_enunciado.py
.\.venv\Scripts\python.exe -m pytest tests/test_logica -k "terreno or cazador or velocidad or retroceso"
.\.venv\Scripts\python.exe main.py --bench
```

Las pruebas del servicio en línea se ejecutan y reportan aparte; aceptación funcional y benchmarks no dependen de red ni de Pygame.

### Línea base posterior al merge

La ejecución comunicada para `.venv/Scripts/python.exe -m pytest -q -rs --tb=short` terminó con `1071 passed`, sin omisiones. Esta revisión no volvió a ejecutar pruebas. El resultado demuestra que el merge conserva la regresión existente; no demuestra todavía los 30 escenarios ni los requisitos de rendimiento de 001, porque costo, rango, cazador ponderado y sus proveedores aún no están implementados.

## Oráculos independientes

1. **Grafos pequeños**: enumeración exhaustiva de rutas simples usando listas. Selecciona el mínimo `(costo_total, primera_vecina_id)` y sirve de referencia para acción, alcanzabilidad/rango, costo total, primera vecina y costo del paso.
2. **Grafos sintéticos mayores**: relajación completa independiente, sin parada por rango ni reutilizar el buscador de producción. Calcula desde cero la misma decisión observable antes de cada comparación.
3. **Reversión**: serialización/comparación de campos canónicos antes y después; excluye expresamente la cantidad de pergaminos según FR-016.
4. **Determinismo**: dos estados construidos con distinta ordenación incidental de salidas pero mismos datos producen la misma secuencia observable.

Una diferencia en esos resultados observables falla antes de medir tiempos. El orden interno, las salas descubiertas/fijadas, las entradas duplicadas y el tamaño de frontera pueden diferir; se miden aparte y no se comparan por igualdad con el oráculo.

## Matriz funcional completa

| Escenario | Prueba propuesta | Referencia/comprobación |
|---|---|---|
| AC-001 | salida sin costo en ambos sentidos | costo efectivo 100 y mismo intervalo; FR-001/FR-002 |
| AC-002 | varios costos y velocidades | fórmula exacta y reloj siguiente; FR-003 |
| AC-003 | atacar/esperar/usar/equipar/recoger/soltar/abrir | costos heredados sin cambio; FR-004/FR-005 |
| AC-B06 | costo 1 con velocidad alta | intervalo 1; FR-003 |
| AC-B07 | velocidad cambia durante salida costosa | tiempo proporcional y secuencia estrictamente nueva; FR-006 |
| AC-019 | parametrizar `True`, `False`, texto, fracción, 0 y negativo | rechazo descriptivo, sin conversión; FR-001 |
| AC-020 | dos sentidos con costos distintos | rechazo identifica salida y ambos valores; FR-002 |
| AC-004 | cazador comparte sala | ataca antes de ruta/rango; FR-007 |
| AC-B01 | puertas separan al objetivo | espera costo 100; FR-008 |
| AC-B02 | ruta mínima cuesta rango+1 | espera costo 100; FR-008/FR-009 |
| AC-005 | ruta mínima cuesta exactamente rango | mueve un paso; FR-009/FR-010 |
| AC-B03 | ruta de más aristas pero menor costo | oráculo exhaustivo elige menor costo; FR-009/FR-010 |
| AC-B04 | primeras vecinas empatadas e inputs permutados | siempre menor ID numérico; FR-011 |
| AC-006 | ruta mínima de varios pasos | mueve solo el primero y cobra esa salida; FR-010/FR-012 |
| AC-007 | mismo esqueleto con contenidos remotos distintos | decisión idéntica; FR-013 |
| AC-021 | rango ausente, negativo, booleano, texto y fracción | rechazo identifica ficha; FR-009 |
| AC-022 | rango 0 en otra sala con salida costo 1/100 | espera costo 100; FR-008/FR-009 |
| AC-023 | rango 0 en la misma sala | ataca; FR-007/FR-009 |
| AC-B05 | cerrar puerta de ruta entre turnos | siguiente decisión igual a cero; FR-014 |
| AC-008 | mover jugador entre turnos | objetivo actual y resultado igual a cero; FR-014 |
| AC-009 | reutilización experimental frente a cero | acción, vecina y costo idénticos; FR-013/FR-014 |
| AC-010 | dos ejecuciones, misma semilla/acciones | log, tiempos y empates idénticos; FR-011/FR-015 |
| AC-011 | intervalo con cazadores y pergamino | estado reversible restaurado, excepción de pergaminos y recálculo; FR-016 |
| AC-016 | abrir puerta entre turnos | resultado igual a cero con puerta abierta; FR-014 |
| AC-017 | cambiar velocidad entre turnos | agenda cambia conforme FR-006; ruta solo si datos relevantes cambian; FR-014 |
| AC-018 | mover/matar otro actor | comparar desde cero sin asumir invalidación idéntica; FR-014 |

## Matriz de rendimiento

| Escenario | Medición `--bench` | Criterio |
|---|---|---|
| AC-012 | mapa base y mapas ampliados solo fuera del rango | fijadas `F_R`, descubiertas `D_R`, salidas `E_R`, inserciones `P_R` y frontera `Q_R` no crecen proporcionalmente a `V`/`E`; PR-002 |
| AC-013 | ciclo real de referencia con decenas de cazadores | cada muestra válida `<20 ms`, sin red/render; PR-001 |
| AC-014 | matriz individual/compartida, uno/muchos, pequeño/grande, reutilizar/cero, puertas estables/inestables | equivalencia primero; reporte de tiempo, trabajo y memoria; PR-003/PR-004/PR-006 |
| AC-015 | seis operaciones de agenda con cientos de eventos | comparación por operación y ciclo mixto; PR-005 |

## Casos del Apéndice B

La ejecución de aceptación debe mostrar explícitamente estos siete IDs en el reporte:

```text
AC-B01 AC-B02 AC-B03 AC-B04 AC-B05 AC-B06 AC-B07
```

Cada prueba incluye en su nombre o docstring el AC y los FR asociados. No se acepta cubrirlos solo de forma incidental.

## Diseño de `--bench`

### Conexión actual comprobada

`main.py --bench` concatena `benchmarks.integrante2.PROVEEDORES` y `benchmarks.bench_ampliado.PROVEEDORES`, y pasa el resultado a `benchmarks.integrante3.ejecutar`. Ese ejecutor incorpora además las mediciones heredadas de agenda y ciclo. La integración futura de 001 añade una sola tupla de proveedores a esa concatenación, sin reemplazar ni registrar dos veces los proveedores existentes.

El ciclo común actual ejecuta `prueba_rendimiento_sofia.py`; `benchmarks/benchmark_ciclo_real_integrante1.py` todavía necesita un adaptador para aparecer en el informe estándar. La agenda común actual reporta extracción; las otras cinco operaciones exigidas por `PR-005` siguen siendo parte del proveedor de 001.

### Rutas

- semillas fijas publicadas en la salida;
- `H=1` y una carga de decenas;
- rangos pequeños/grandes;
- individual frente a inversa compartida;
- recálculo frente a reutilización;
- puertas casi estables y cambios frecuentes;
- conteos separados de salas fijadas y descubiertas, salidas examinadas, entradas insertadas, frontera máxima/final, extracciones obsoletas, limpieza y memoria auxiliar.

### Ciclo real

Se adapta `benchmarks/benchmark_ciclo_real_integrante1.py`. La carga e inicialización común se hacen antes; el cronómetro incluye la acción, agenda, decisiones de cazadores, auxiliares de ruta, invalidación y limpieza hasta la próxima decisión del jugador. Sintéticos y referencia oficial se etiquetan por separado.

### Agenda

Para `N` de cientos y al menos un tamaño superior:

1. insertar;
2. extraer;
3. cancelar por ID;
4. cancelar por actor;
5. reprogramar;
6. resolver empates por tiempo/secuencia.

Cada flujo usa los mismos eventos para `AgendaEventos` y una alternativa lineal/manual permitida solo en benchmark. Para inserción se incluye construir la agenda vacía; para las demás operaciones la carga común queda fuera, pero las búsquedas, cambios de índices y limpieza propios de la operación quedan dentro. Un ciclo mixto mide la carga de punta a punta.

## Reversión y determinismo

1. Capturar el estado canónico anterior a una acción.
2. Ejecutar movimiento con costo, turnos de cazadores, apertura/cierre y cambio de velocidad.
3. Usar pergamino.
4. Comparar sala/vida/reloj/agenda/secuencias/puertas/actores con el estado anterior, excepto pergaminos.
5. Desde el mismo estado posterior al retroceso, repetir las mismas acciones posteriores en dos ejecuciones.
6. Comparar decisiones, tiempos, secuencias y `partida.log`.

### Integración con la línea de tiempo 004

Además de la reversión funcional:

1. Verificar que cada mutación canónica de 001 se registra dentro de la transacción mediante los cambios y helpers existentes; una acción rechazada no publica cambios.
2. Comprobar que ninguna caché/servicio de rutas es alcanzable desde `EstadoPartida`, entidades canónicas o cambios guardados.
3. Copiar en una sola operación `(estado, ventana_de_transacciones)` con `copy.deepcopy`; cada cambio de la copia debe apuntar a las entidades copiadas. Deshacer temporalmente y aplicar los inversos debe dejar bytes/estructura equivalentes aun si el resumen falla.
4. Cuando exista v10, hacer ida y vuelta del `pickle` conjunto de estado vivo y línea y repetir consultas; las cachés no aparecen en los bytes.
5. Calentar una caché y ejecutar `historia` tanto sobre un punto de control como sobre el estado vivo posterior al último punto: no cambia su identidad/generación, no ejecuta decisiones de 001 y la decisión siguiente coincide con cálculo desde cero.
6. Calentar una caché, efectuar un `RETROCEDER` exitoso y comprobar que queda invalidada después de `deshacer_ultimo`; si el retroceso falla, no se presenta como estado restaurado.
7. Enlazar mediante `MotorJuego.iniciar` un estado nuevo y uno cargado; en ambos casos se descarta cualquier derivado del estado anterior antes de la primera decisión.

La interfaz actual solo ofrece deshacer destructivo (`deshacer_ultimo`/`revertir`). Las pruebas de deshacer temporal y rehacer usarán los métodos que implemente 004; no se supone un nombre o firma antes de que existan.

### Estado de persistencia

La versión ejecutable sigue siendo v9. El v10 citado por 004 es un contrato propuesto y sus pruebas de ida y vuelta permanecen bloqueadas hasta su implementación coordinada con costo/rango. La aceptación condicionada de la frontera con Joshua no equivale a que estas comprobaciones hayan pasado.

## Señales de salida

- Suite heredada y nueva sin regresiones.
- Prueba AST de restricciones aprobada.
- 30 escenarios con referencia a FR/PR; siete AC-B explícitos.
- Ninguna divergencia observable respecto del oráculo; trabajo y orden interno reportados por separado.
- Informe `--bench` conectado a `main.py --bench`, con resultados sintéticos separados de la referencia oficial.
- La decisión final individual/compartida/adaptativa se documenta después de medir; este plan no anticipa el ganador.
