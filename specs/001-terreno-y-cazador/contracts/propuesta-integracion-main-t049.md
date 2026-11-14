# Propuesta de integración T049 — `main.py --bench`

**Estado**: BORRADOR PARA ACUERDO; NO APLICADO.

**Autora**: Sofía Delgado (001).

**Propietario de `main.py`**: por confirmar en la revisión conjunta.

**Fecha**: 2026-11-10.

**Referencias**: T049, T062, T067, T070, T072, T076; FR-011, FR-013, FR-018; PR-001–PR-006.

Esta propuesta no modifica `main.py`, no cambia producción y no afirma PR-001 ni el límite de 20 ms. Solo describe el cambio mínimo para que `main.py --bench` ejecute los proveedores de 001 que hoy se lanzan por separado.

## 1. Situación actual

`main.py` importa, dentro de `if config.bench`:

- `PROVEEDORES` de `benchmarks.integrante2`;
- `PROVEEDORES_ADICIONALES` de `benchmarks.bench_ampliado`;
- `PROVEEDORES_MAPA` de `benchmarks.mapa_cripta_integrante1`;

y ejecuta `benchmarks.integrante3.ejecutar(proveedores=...)`.

El proveedor del mapa ya se ejecuta desde `main.py --bench`. Rutas, agenda y ciclo real todavía no están registrados allí; por eso T049, T062, T067, T070, T072 y T076 siguen abiertas.

## 2. Cambio mínimo propuesto

Añadir dos importaciones locales al bloque `--bench` y concatenar sus tuplas una sola vez:

```python
from benchmarks.terreno_cazador_integrante1 import (
    PROVEEDORES as PROVEEDORES_TERRENO,
)
from benchmarks.benchmark_ciclo_real_integrante1 import (
    PROVEEDORES as PROVEEDORES_CICLO,
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

No se toca `_crear_fuente`, `--replay`, `--verificar`, la vista ni ningún camino de producción. Las importaciones permanecen dentro de `if config.bench` para no encarecer el arranque normal.

## 3. Proveedores que quedarían registrados

| Tupla | Proveedores | Cobertura |
|---|---|---|
| `PROVEEDORES_MAPA` | `medir_mapa_cripta` | construcción de `_salas`, consultas por ID y vinculación (T073–T075) |
| `PROVEEDORES_TERRENO` | `medir_agenda`, `medir_agenda_ciclo`, `medir_rutas_region`, `medir_rutas_matriz` | agenda (T047/T069), rutas por región y matriz (T044–T046/T065) |
| `PROVEEDORES_CICLO` | `medir_ciclos_sinteticos` | ciclo completo sintético (T048) |

`PROVEEDORES` y `PROVEEDORES_ADICIONALES` existentes se conservan sin cambios.

**Decisión pendiente del propietario**: T049 nombra rutas, mapa y ciclo. La agenda viaja en el mismo `PROVEEDORES` de `terreno_cazador_integrante1.py`. Si se prefiere limitar T049 a rutas/mapa/ciclo, puede importarse `PROVEEDORES_RUTAS` en lugar de `PROVEEDORES`; la agenda necesitaría entonces una tarea de integración separada, pero T067/T070 la requieren para la evidencia literal de `--bench`. La recomendación es registrar `PROVEEDORES` completo porque no añade una segunda ejecución de rutas y evita dejar la agenda fuera de la interfaz oficial.

## 4. Validación posterior a la aplicación

1. Ejecutar `python main.py --bench` y guardar el JSON fuera de la medición.
2. Comprobar que aparecen, una sola vez por nombre, las filas de mapa, agenda, rutas y ciclo.
3. Verificar el esquema común (`medicion`, `n`, `carga`, `repeticiones`, `unidad`, `mediana`, `p95`, `maximo`, `minimo`, `muestras`, `trabajo`, `memoria`).
4. Comparar las cargas con los artefactos ya conservados:
   - `benchmarks/resultados/rutas_t044-t046-t065_c1_r9_32-128-512.json`;
   - `benchmarks/resultados/agenda_ciclo001_t047_c1_r9_256-512-1024.json`;
   - `benchmarks/resultados/ciclo_sintetico_t048_t047_c1_r9_32-64.json`;
   - el artefacto del mapa correspondiente.
5. Ejecutar las pruebas de benchmark y restricciones, y después la suite completa.
6. T050 comprueba la inclusión real en `main.py --bench`; T062/T072/T076 usan esa salida. No se interpretan las filas sintéticas como PR-001 ni como cumplimiento de 20 ms.

## 5. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Aumento del tiempo de `--bench` | La preparación sigue fuera del intervalo cronometrado; el propietario puede ejecutar solo un subconjunto con `--bench` si el equipo lo acuerda. |
| Duplicación de proveedores | Concatenar cada tupla una sola vez y comprobar nombres únicos antes de aceptar. |
| Importaciones pesadas en arranque normal | Mantenerlas dentro de `if config.bench`. |
| Dependencia circular | Los módulos de benchmark importan producción, no `main`; verificar con `py_compile` y una ejecución real. |
| Ruido de medición | Conservar repeticiones, calentamiento y preparación fuera del reloj; no cambiar los proveedores ni sus cargas en esta tarea. |
| Confundir integración con cierre de PR-001 | T049 solo registra la ejecución; T051/G6 siguen siendo la referencia oficial. |

## 6. Criterio de aceptación

- El propietario revisa y aplica el diff exacto, o propone una variante equivalente.
- `main.py --bench` incluye una sola vez los proveedores acordados.
- No cambia el comportamiento de producción ni se añaden cachés.
- T049 se cierra; T050, T062, T067, T070, T072 y T076 pueden continuar con evidencia literal de `--bench`.
- La propuesta no se considera acuerdo hasta que el propietario de `main.py` la acepte.
