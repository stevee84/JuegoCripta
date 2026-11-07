# Cómo validar la verificación de resolubilidad

Guía para comprobar la capacidad de punta a punta, y para la defensa (§7.4), donde se pide
recorrer la trazabilidad de un requisito: escenario → tarea → código → prueba.

## Requisitos previos

```bash
python -m pip install -r requirements.txt
```

Sin conexión no hace falta nada más: los fixtures están en `tests/fixtures/api_real/`.

## 1. Verificar una cripta sin abrir el juego

```bash
python main.py --verificar cripta-01 --offline
```

Debe imprimir que tiene solución y el orden de obtención de llaves, sin abrir ninguna ventana y
sin pedir ninguna acción. Códigos de salida: `0` con solución, `1` sin solución, `2` no se pudo
verificar. Ver [contracts/cli-verificar.md](./contracts/cli-verificar.md).

## 2. Comprobar que el resultado no depende de la fuente

```bash
python main.py --verificar cripta-01 --offline
```

```bash
python main.py --verificar cripta-01
```

Las dos salidas deben ser idénticas (`FR-015`). La segunda consume una solicitud de la consulta
de llaves.

## 3. Comprobar que el orden es siempre el mismo

```bash
python main.py --verificar cripta-01 --offline > /tmp/a.txt; python main.py --verificar cripta-01 --offline > /tmp/b.txt; diff /tmp/a.txt /tmp/b.txt && echo "identico"
```

Sin diferencias (`SC-003`, `FR-006`).

## 4. Una cripta sin solución no inicia

El juego no recibe la cripta por bandera: se elige desde el menú. Para probarlo, se copia una
cripta sin solución al paquete local y se la elige al arrancar.

```bash
cp -r tests/fixtures/resolubilidad/cripta-ciclo datos_offline/
```

```bash
python main.py --offline --vista consola
```

Al elegir `cripta-ciclo` la partida no debe empezar, y el informe debe nombrar las llaves
inalcanzables, la frontera bloqueada con la llave de cada puerta y los círculos de llaves
(`FR-007` a `FR-010`).

```bash
python main.py --offline --vista consola --forzar
```

Con `--forzar` la partida empieza después de mostrar el informe (`FR-011`).

El informe suelto, sin abrir el juego, sale con `--verificar`:

```bash
python main.py --offline --verificar cripta-ciclo
```

## 5. El informe sobrevive a guardar y reanudar

Iniciar una partida verificada, guardarla, cerrar el programa, reanudarla y pedir el informe: debe
mostrar lo mismo que al empezar, y reanudar no debe volver a verificar (`FR-020`).

Un archivo de partida de la versión anterior debe reportarse como incompatible, no cargarse a
medias.

## 6. Rendimiento

```bash
python main.py --bench
```

Debe incluir la verificación sobre la cripta más grande por debajo de 200 ms (`SC-001`, §6.1) y
la comparación contra rehacer el recorrido por cada llave, sobre criptas sintéticas con muchas
llaves encadenadas y reproducibles por semilla (`SC-007`, §6.3).

## 7. Pruebas automáticas

```bash
python -m pytest -q
```

```bash
python -m pytest -q tests/test_logica/test_resolubilidad.py
```

Los cuatro casos obligatorios de §3.5 tienen cada uno su prueba (`SC-006`):

| Caso | Requisito |
|---|---|
| La llave de salida está detrás de la única puerta que ella abre | `FR-010` |
| Una llave la suelta un enemigo que se desplaza | `FR-003` |
| Hay varios órdenes válidos y dos ejecuciones dan el mismo | `FR-006` |
| Cripta sin solución y sin `--forzar`: no inicia | `FR-011` |

La suite de restricciones comprueba además que nada de esto use `heapq`, `set`, `collections` ni
`sorted()` (§6.2):

```bash
python -m pytest -q tests/test_restricciones_enunciado.py
```
