# Cómo validar la niebla de guerra y el viaje automático

Guía para comprobar la capacidad de punta a punta, y para la defensa (§7.4), donde se pide
recorrer la trazabilidad de un requisito: escenario → tarea → código → prueba.

## Requisitos previos

```bash
python -m pip install -r requirements.txt
```

Sin conexión no hace falta nada más: los fixtures están en `tests/fixtures/api_real/`.

## 1. El jugador ya no ve toda la cripta

Iniciar una partida y pedir el mapa conocido. Debe aparecer **solo** la sala inicial como
explorada y las salas detrás de sus salidas como avistadas (`FR-001` a `FR-005`). De una avistada
no debe verse ni el nombre ni sus salidas.

## 2. Explorar revela, y recuerda

Moverse a una vecina y volver a pedir el mapa. La sala nueva debe estar explorada con sus salidas
y sus costos, y sus vecinas deben haber pasado a avistadas (`FR-002`, `FR-003`).

## 3. La memoria de puertas puede quedar desactualizada

Observar una puerta con cierre automático estando en su sala, alejarse hasta que se cierre sola, y
pedir el mapa: debe seguir mostrándola **abierta**, porque esa fue la última observación
(`FR-006`). Volver a su sala y pedirlo otra vez: ahora debe mostrarla cerrada.

## 4. Viajar a una sala explorada

```text
ir a <sala explorada>
```

El jugador debe llegar mediante movimientos ordinarios, uno por paso, consumiendo tiempo según el
costo de cada salida (`FR-009`, `FR-013`). Ver
[contracts/cli-ir-a.md](./contracts/cli-ir-a.md).

## 5. Los destinos inválidos se rechazan

```text
ir a <sala avistada>
```

Debe rechazarse indicando que está avistada pero no explorada (`FR-010`). Lo mismo con una sala
desconocida o inexistente.

## 6. El viaje se detiene por un motivo, y se ve cuál

Provocar cada condición y comprobar el motivo (`FR-016` a `FR-019`):

| Para provocar | Motivo esperado |
|---|---|
| llegar al destino | llegó |
| viajar hacia una sala con un enemigo dormido | hay enemigos |
| cruzar una trampa durante el viaje | recibió daño |
| cerrar la única puerta conocida del camino | no hay camino conocido |

El caso de la puerta que el mapa recordaba abierta y en realidad se cerró **no** detiene el viaje:
al llegar a la sala el mapa se corrige y el siguiente cálculo busca otro camino (`FR-014`).

## 7. El conocimiento es parte de la partida

Explorar, guardar, cerrar el programa y reanudar: el mapa conocido debe ser el mismo (`FR-023`).
Un archivo de partida de la versión anterior debe reportarse como incompatible.

Usar el pergamino durante un viaje: debe revertirse **solo el último paso**, y el mapa conocido
debe volver al estado anterior a ese paso, sin las salas que ese paso reveló (`FR-022`, `FR-023`).

## 8. La antorcha

Entrar a una sala con la antorcha encendida: las vecinas deben quedar **exploradas**, por
cualquier salida, sin que se active ninguno de sus enemigos ni trampas (`FR-024`). Con la antorcha
apagada deben quedar solo avistadas.

## 9. Rendimiento

```bash
python main.py --bench
```

Debe incluir el paso de «ir a» por debajo de 5 ms con el mapa conocido completo de la cripta de
referencia (`SC-001`, §6.1), y la comparación del mapa conocido contra la alternativa que recorre
el mapa (`SC-008`, §6.3).

## 10. Pruebas automáticas

```bash
python -m pytest -q
```

```bash
python -m pytest -q tests/test_logica/test_mapa_conocido.py tests/test_logica/test_viaje.py
```

Los seis casos obligatorios de §3.4 tienen cada uno su prueba (`SC-007`):

| Caso | Requisito |
|---|---|
| Destino avistado, no válido | `FR-010` |
| Puerta recordada abierta que en realidad se cerró | `FR-014` |
| Enemigo dormido detiene el viaje | `FR-016` |
| Empate de costos, desempate por menor id | `FR-012` |
| Pergamino revierte un solo paso | `FR-022` |
| Antorcha revela vecinas sin activar nada | `FR-024` |

Y la separación que acordó 001 (`SC-005`): dos estados reales distintos con el mismo mapa conocido
producen el mismo viaje.

```bash
python -m pytest -q tests/test_restricciones_enunciado.py
```

Comprueba que nada de esto usa `heapq`, `set`, `collections` ni `sorted()` (§6.2).
