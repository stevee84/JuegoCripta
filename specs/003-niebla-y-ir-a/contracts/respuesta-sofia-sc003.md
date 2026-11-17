# Respuesta a la nota de Sofía sobre la medición de SC-003

**Para**: Sofía (spec 001) · **De**: Steven (specs 002 y 003) · **Fecha**: 17/11/2026
**Responde a**: `specs/001-terreno-y-cazador/contracts/nota-coordinacion-steven-sc003.md`
**Alcance**: cambia `benchmarks/integrante2.py` y `tests/test_bench_integrante2.py`, que son míos.
No toca `logica/mapa_conocido.py` ni ningún artefacto de 001.

## Aceptada entera, y el diagnóstico era correcto

Los cinco puntos entran. El central —**cero revelaciones**— lo confirmé de forma determinista
antes de tocar nada, sin depender del cronómetro:

```
n=  400  objetivo= 200  revelaciones_de=0  hechos_reales=0
n= 1600  objetivo= 800  revelaciones_de=0  hechos_reales=0
```

La medición cronometraba `_conocer` y los chequeos de puertas, nunca el costo de revelar.

Hay un sexto problema que la nota no menciona y que encontré al revisarlo: el objetivo
`salas // 2` cae en una posición distinta de la malla según el tamaño, y en `_cripta_malla` las
salas de borde tienen 3 salidas y las de esquina 2. A lo largo de los tamaños de `--bench` el
grado del objetivo iba **3, 3, 4, 3, 4, 3**: las dos cargas que se comparaban no eran la misma ni
en revelaciones ni en salidas examinadas.

## Qué quedó hecho, punto por punto

| Tu punto | Qué se hizo |
|---|---|
| 1. `k` revelaciones nuevas, salas del mismo grado | hasta 8 salas **interiores** (grado 4 en todos los tamaños), separadas a distancia ≥ 3 para que las revelaciones de una no le quiten hechos a la siguiente; el mapa conocido explora todo salvo las objetivo y su entorno a distancia 2 |
| 2. comprobar antes de medir que producen los mismos hechos | la medición publica `revelaciones_por_lote`, calculado con `MapaConocido.revelaciones_de`, y **falla** si el lote no revelaría nada; la prueba exige que los dos tamaños publiquen el mismo número antes de mirar un solo tiempo |
| 3. lote largo, normalizar y comparar medianas alternando el orden | se cronometra el lote completo, se divide por revelación, se comparan medianas y se mide en los dos órdenes, `(400, 1600)` y `(1600, 400)` |
| 4. varias salas objetivo | 8 en vez de 1, repartidas por la malla en vez de una posición fija |
| 5. mantener el umbral | el `<2×` no se tocó |

De 128 salas en adelante todos los tamaños revelan **40 hechos previstos y 72 reales**, idénticos.
Por debajo la malla no admite 8 objetivos separados y el lote es menor, por eso la medición publica
el número en vez de suponerlo.

## Resultado

| | antes | ahora |
|---|---|---|
| revelaciones medidas | 0 | 40 por lote |
| razón 1600 / 400 | 2,13× (Actions #96) | **1,11× de mediana**, 1,24× el peor de 8 pasadas |
| estadístico | mínimo de 7 | mediana, orden alternado |

El 1,1× que queda no es el mapa: es el crecimiento de la tabla hash. Cuatro veces más salas por
1,1× de costo es justo lo que SC-003 afirma.

**De acuerdo en no tocar `MapaConocido`.** Tu lectura es la correcta y el arreglo no lo necesitó.

## Lo mismo le pasaba a la otra prueba, y también quedó

`test_consultar_el_estado_no_crece_con_el_mapa_conocido` sí medía lo correcto, pero el lote era una
pasada por las salas: 100 consultas en el tamaño chico contra 900 en el grande, normalizando por
consulta pero sin comparar lotes iguales, y con una ventana de unos 70 µs donde pesa el reloj.
Ahora son 2000 consultas fijas en los dos, en orden pseudoaleatorio con semilla fija, y se compara
la mediana: razón **1,09×** con una dispersión de 0,07× en 8 pasadas.

Los valores por consulta que salen —622 ns a 100 salas y 687 ns a 900, y 28× de ventaja sobre
recorrer el mapa— coinciden con la tabla de SC-002 que ya está en `DECISIONES.md` §5.3, así que esa
evidencia **sigue valiendo** sin rehacerla.

## Dos cosas que te tocan a ti

1. **Tu corrida oficial T050 contiene la medición vieja.** En
   `benchmarks/resultados/main_bench_completo_t050.json`, `mapa_conocido_explorar_una_sala` va de
   5 900 ns con 9 salas a 12 600 ns con 484: un 2,1× monótono que se lee como una violación de
   SC-003 y que en realidad medía cero revelaciones. Es un archivo que tu `DECISIONES.md` cita como
   evidencia. Conviene rehacer esa corrida, o fechar la tabla y decir que esa fila es anterior al
   arreglo. Las demás filas no las toqué.
2. **Tres archivos de contabilidad de la corrida** entraron al repo con T050:
   `main_bench_t050.pid` (6 bytes con un PID ya muerto), `main_bench_t050.exitcode.txt` (2 bytes) y
   `main_bench_t050.stderr.log`. No son evidencia de ninguna medición. Los JSON de resultados sí los
   defiendo —son lo que pide el Principio IX y ya había precedente—, pero esos tres yo los sacaría
   antes del miércoles. Son tuyos, así que no los toco.

## Estado

`origin/Steve` contiene ya tu rama completa, la de Joshua y lo mío, con la suite en **1470
aprobadas**. Es la candidata para main.
