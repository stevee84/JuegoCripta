# Propuesta de integración T049 — `main.py --bench`

**Estado**: BORRADOR PARA ACUERDO; NO APLICADO.

**Autora**: Sofía Delgado (001).

**Propietario de `main.py`**: por confirmar en la revisión conjunta.

**Fecha**: 2026-11-10; revisada el 2026-11-14 sobre `integracion-parte2@31f58ca`.

**Referencias**: T049, T062, T067, T070, T072, T076; FR-011, FR-013, FR-018; PR-001–PR-006.

Esta propuesta no modifica `main.py`, no cambia producción y no afirma PR-001 ni el límite de 20 ms. Solo describe el cambio mínimo para que `main.py --bench` ejecute los proveedores de 001 que hoy se lanzan por separado.

## 1. Situación actual

`main.py` importa, dentro de `if config.bench`:

- `PROVEEDORES` de `benchmarks.integrante2`;
- `PROVEEDORES_ADICIONALES` de `benchmarks.bench_ampliado`;
- `PROVEEDORES_MAPA` de `benchmarks.mapa_cripta_integrante1`;
- `bench_linea.PROVEEDORES` de `benchmarks.linea_tiempo` (Joshua), después de
  asignar `bench_linea.K_CONFIGURADO` desde `--checkpoint-cada`;

y ejecuta `benchmarks.integrante3.ejecutar(proveedores=...)`.

Los doce proveedores de `benchmarks.integrante2` incluyen ahora los cambios de
Steven para mapa conocido y un paso de «ir a» (`medir_mapa_conocido` y
`medir_paso_ir_a`). El proveedor del índice de mapa y el de línea de tiempo ya
se ejecutan desde `main.py --bench`. Rutas, agenda ampliada y ciclo sintético
completo de 001 todavía no están registrados allí; por eso T049/T050 y sus
tareas documentales dependientes siguen abiertas.

## 2. Cambio mínimo propuesto

Añadir dos importaciones locales al bloque `--bench` y concatenar sus tuplas
una sola vez, **sin sustituir ni reordenar los proveedores ya registrados**.
El diff exacto de registro es:

```diff
@@
         from benchmarks.mapa_cripta_integrante1 import PROVEEDORES as PROVEEDORES_MAPA
+        from benchmarks.terreno_cazador_integrante1 import (
+            PROVEEDORES_MAIN as PROVEEDORES_TERRENO,
+        )
+        from benchmarks.benchmark_ciclo_real_integrante1 import (
+            PROVEEDORES_MAIN as PROVEEDORES_CICLO,
+        )
         # Spec 004 (T046): línea de tiempo, retroceso, replay e inventario.
         import benchmarks.linea_tiempo as bench_linea
@@
-        print(json.dumps(ejecutar(proveedores=PROVEEDORES + PROVEEDORES_ADICIONALES + PROVEEDORES_MAPA
-                                  + bench_linea.PROVEEDORES), ensure_ascii=False, indent=2))
+        proveedores = (
+            PROVEEDORES
+            + PROVEEDORES_ADICIONALES
+            + PROVEEDORES_MAPA
+            + bench_linea.PROVEEDORES
+            + PROVEEDORES_TERRENO
+            + PROVEEDORES_CICLO
+        )
+        print(json.dumps(
+            ejecutar(proveedores=proveedores),
+            ensure_ascii=False,
+            indent=2,
+        ))
```

La concatenación anterior conserva en el mismo orden relativo datos,
resolubilidad, mapa conocido, «ir a», los proveedores adicionales, el índice
de `MapaCripta` y la línea de tiempo. La inspección estática da 25 callables y
25 identidades distintas: 20 existentes y 5 pendientes de 001.

### 2.1 Compatibilidad resuelta mediante adaptadores de 001

`benchmarks.integrante3.ejecutar` llama a todos los proveedores con los mismos
`tamanos=(8, 16, 32, 64, 128, 512)`, pero ese campo global no representa las
cargas heterogéneas de 001. Los cinco adaptadores aceptan formalmente
`repeticiones` y `tamanos`, ignoran exclusivamente los tamaños globales y
delegan una vez, sin reducir las repeticiones recibidas:

```text
medir_agenda_main                 -> medir_agenda              (256, 512, 1024)
medir_agenda_ciclo_main           -> medir_agenda_ciclo        (256, 512, 1024)
medir_rutas_region_main           -> medir_rutas_region        (32, 128, 512)
medir_rutas_matriz_main           -> medir_rutas_matriz        (32, 64)
medir_ciclos_sinteticos_main      -> medir_ciclos_sinteticos   (32, 64)
```

Ambos módulos exportan estos grupos mediante una tupla diferenciada
`PROVEEDORES_MAIN`. Las funciones y tuplas originales `PROVEEDORES`,
`PROVEEDORES_RUTAS` y `PROVEEDORES_AGENDA` permanecen intactas. No se modifica
`benchmarks.integrante3.py` ni se introduce lógica especial de cargas en
`main.py`.

`tests/test_bench_adaptadores_001.py` sustituye cada productor original, llama
al adaptador con tamaños globales ficticios y comprueba una sola delegación con
las cargas y repeticiones correctas. Junto con las regresiones de agenda,
rutas y ciclo: **60 passed in 19.98s**.

El fragmento anterior sustituye al borrador previo, que proponía directamente:

```python
from benchmarks.terreno_cazador_integrante1 import (
    PROVEEDORES_MAIN as PROVEEDORES_TERRENO,
)
from benchmarks.benchmark_ciclo_real_integrante1 import (
    PROVEEDORES_MAIN as PROVEEDORES_CICLO,
)

proveedores = (
    PROVEEDORES
    + PROVEEDORES_ADICIONALES
    + PROVEEDORES_MAPA
    + PROVEEDORES_TERRENO
    + PROVEEDORES_CICLO
)
print(json.dumps(
    ejecutar(proveedores=proveedores),
    ensure_ascii=False,
    indent=2,
))
```

Ese fragmento previo se conserva solo como referencia histórica: omitía
`bench_linea.PROVEEDORES` al construir `proveedores`. El diff vigente de §2
conserva Joshua y usa exclusivamente las tuplas adaptadas `PROVEEDORES_MAIN`.

No se toca `_crear_fuente`, `--replay`, `--verificar`, la vista ni ningún camino de producción. Las importaciones permanecen dentro de `if config.bench` para no encarecer el arranque normal.

## 3. Proveedores que quedarían registrados

| Tupla | Proveedores | Cobertura |
|---|---|---|
| `PROVEEDORES_MAPA` | `medir_mapa_cripta` | construcción de `_salas`, consultas por ID y vinculación (T073–T075) |
| `PROVEEDORES_TERRENO` (`PROVEEDORES_MAIN`) | cuatro adaptadores nominales de agenda/rutas | agenda (T047/T069), rutas por región y matriz (T044–T046/T065) con cargas propias |
| `PROVEEDORES_CICLO` (`PROVEEDORES_MAIN`) | `medir_ciclos_sinteticos_main` | ciclo completo sintético 32/64 (T048) |
| `bench_linea.PROVEEDORES` | `medir_linea_tiempo` | línea de tiempo, retroceso, replay e inventario de 004; ya registrado y conservado |
| `PROVEEDORES` de `integrante2` | 12 proveedores, incluidos `medir_mapa_conocido` y `medir_paso_ir_a` | datos, resolubilidad y entregas posteriores de Steven; ya registrados y conservados |

`PROVEEDORES`, `PROVEEDORES_ADICIONALES`, `PROVEEDORES_MAPA` y
`bench_linea.PROVEEDORES` existentes se conservan sin cambios y sin duplicados.

Los nombres emitidos por los cinco proveedores pendientes son:

- `agenda_insertar`, `agenda_extraer`, `agenda_cancelar_id`,
  `agenda_cancelar_actor`, `agenda_reprogramar` y
  `agenda_resolver_empates`;
- los seis equivalentes con prefijo `agenda_ciclo001_`;
- `rutas_ac012_region` y `rutas_ac014_matriz`;
- `ciclo_real_intervalo`.

Cada nombre de agenda/ruta/ciclo aparece legítimamente en varias filas por
alternativa, escenario y carga. T050 debe comprobar presencia y ausencia de
duplicación de proveedores, no exigir unicidad global del campo `medicion`.

La tupla `PROVEEDORES_MAIN` de terreno contiene exactamente los cuatro
adaptadores de agenda/rutas exigidos. No debe sustituirse por `PROVEEDORES`,
porque esa tupla histórica recibe los tamaños globales directamente y se
conserva para ejecuciones focalizadas y compatibilidad de pruebas.

## 4. Validación posterior a la aplicación

1. Al aplicar el diff de `main.py`, adaptar `test_bench_desde_main_no_inicializa_fuente_ni_vista`
   y el patrón de `test_fr016_main_bench_registra_el_proveedor_y_el_k` para
   capturar los proveedores de terreno/ciclo, comprobar una inclusión por
   callable y confirmar que línea de tiempo y los demás existentes permanecen.
2. Conservar `tests/test_bench_adaptadores_001.py`, que verifica firma,
   despacho único, cargas, repeticiones, ausencia de duplicados e invariancia
   de las tuplas históricas sin ejecutar las cargas completas.
3. Ejecutar `python main.py --bench` y guardar el JSON fuera de la medición solo
   en T050, después de autorizar y aplicar el registro compartido.
4. Comprobar que aparecen, una sola vez por combinación identificadora, las filas de mapa, agenda, rutas y ciclo. El nombre `medicion` no es único por sí solo: agenda, alternativas y escenarios producen varias filas legítimas con el mismo nombre.
5. Verificar el esquema de 001 (`medicion`, `n`, `carga`, `repeticiones`, `unidad`, `mediana`, `p95`, `maximo`, `minimo`, `muestras`, `trabajo`, `memoria`) sin exigir esos campos a proveedores ajenos con contratos anteriores.
6. Comparar las cargas con los artefactos ya conservados:
   - `benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json`;
   - `benchmarks/resultados/agenda_ciclo001_t047_c1_r9_256-512-1024.json`;
   - `benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json`;
   - el artefacto del mapa correspondiente.
7. Ejecutar primero las pruebas focalizadas de registro, proveedores y esquema;
   dejar la suite completa para el cierre coordinado posterior.
8. T050 comprueba la inclusión real en `main.py --bench`; T062/T072/T076 usan esa salida. No se interpretan las filas sintéticas como PR-001 ni como cumplimiento de 20 ms.

## 5. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Aumento del tiempo de `--bench` | La preparación sigue fuera del intervalo cronometrado; el propietario puede ejecutar solo un subconjunto con `--bench` si el equipo lo acuerda. |
| Duplicación de proveedores | Concatenar cada tupla una sola vez y comprobar nombres únicos antes de aceptar. |
| El ejecutor fuerza una carga común incompatible | Resuelto por `PROVEEDORES_MAIN`; interpretar cada fila por su carga propia, no por `informe["tamanos"]`. |
| Falso positivo en “nombres únicos” | Validar una inclusión por callable y unicidad por la clave completa de escenario/alternativa/carga, no solo por `medicion`. |
| Importaciones pesadas en arranque normal | Mantenerlas dentro de `if config.bench`. |
| Dependencia circular | Los módulos de benchmark importan producción, no `main`; verificar con `py_compile` y una ejecución real. |
| Ruido de medición | Conservar repeticiones, calentamiento y preparación fuera del reloj; no cambiar los proveedores ni sus cargas en esta tarea. |
| Confundir integración con cierre de PR-001 | T049 solo registra la ejecución; T051/G6 siguen siendo la referencia oficial. |

## 6. Criterio de aceptación

- El propietario revisa y aplica el diff exacto de registro, o propone una variante equivalente.
- `main.py --bench` incluye una sola vez los proveedores acordados.
- No cambia el comportamiento de producción ni se añaden cachés.
- T049 se cierra; T050, T062, T067, T070, T072 y T076 pueden continuar con evidencia literal de `--bench`.
- La propuesta no se considera acuerdo hasta que el propietario de `main.py` la acepte.
