# Mediciones de `TablaHashImpl` (§1, §7)

## Dónde se usa y por qué importa

`estructuras/tabla_hash.py::TablaHashImpl` es la tabla hash propia: encadenamiento por
bucket, capacidad inicial 17 y rehash al doble cuando el factor de carga supera 0,75.
Reemplaza al `dict` de Python, prohibido como índice por §7, en:

- `CatalogoPartida`: índice `id_ficha → ficha` de la partida;
- el contenido por sala (`DecodificadorDatos`, `FuenteOffline`): `id_sala → contenido`;
- las salas del guardado (`GuardadoBinario.cargar`): `id_sala → registro`;
- la detección de duplicados (`tiene_duplicados`).

La caché LRU **no** la usa, por indicación del profesor. Usa un arreglo ordenado con
búsqueda binaria más una ListaDoble; ver `cache_buscar_*` en `--bench`.

## Cómo se reproduce

```
python main.py --bench
```

Filas `tabla_hash_*`, `lista_pares_buscar_*_alternativa` y
`arreglo_ordenado_buscar_*_alternativa`, generadas por
`benchmarks/integrante2.py::medir_tabla_hash`:

- **Alternativas medidas:** las que podrían usarse en esos índices sin `dict`. Una es la
  lista de pares con búsqueda secuencial; la otra, el arreglo ordenado con búsqueda
  binaria, que es la técnica de la caché.
- **Claves:** con la forma real del proyecto. IDs de ficha de texto con prefijo común
  (`itm_00042`) e IDs de sala enteros consecutivos.
- **Cada lote** busca las n claves (presentes) o n claves que no están (ausentes).
- **Medición:** la preparación queda fuera del cronómetro, con 1 calentamiento y
  15 repeticiones. Se informa la mediana.

Entorno: Python 3.14.0, Windows 11 (10.0.26200).

## Resultados: costo por búsqueda (mediana del lote / n), en µs

IDs de ficha de texto:

| n | Tabla hash presente | Arreglo ordenado presente | Lista lineal presente | Tabla hash ausente | Arreglo ordenado ausente | Lista lineal ausente |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0,31 | 0,64 | 0,34 | 0,25 | 0,68 | 0,50 |
| 32 | 0,29 | 0,86 | 0,86 | 0,27 | 0,91 | 1,54 |
| 128 | 0,30 | 1,10 | 3,10 | 0,28 | 1,17 | 5,95 |
| 512 | 0,30 | 1,53 | 10,70 | 0,28 | 1,48 | 22,99 |

IDs de sala enteros:

| n | Tabla hash presente | Arreglo ordenado presente | Lista lineal presente | Tabla hash ausente | Arreglo ordenado ausente | Lista lineal ausente |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 0,25 | 0,63 | 0,30 | 0,21 | 0,55 | 0,44 |
| 32 | 0,22 | 0,79 | 0,69 | 0,18 | 0,73 | 1,25 |
| 128 | 0,21 | 1,39 | 2,43 | 0,17 | 0,90 | 4,47 |
| 512 | 0,22 | 1,35 | 9,98 | 0,19 | 1,37 | 21,18 |

Inserción con rehash (mediana del lote completo; rehashes = duplicaciones de capacidad):

| n | IDs de texto | IDs enteros | Rehashes | Por inserción (texto) |
|---:|---:|---:|---:|---:|
| 8 | 4,7 µs | 3,8 µs | 0 | 0,59 µs |
| 64 | 116,2 µs | 95,4 µs | 3 | 1,82 µs |
| 512 | 1 033,1 µs | 859,5 µs | 6 | 2,02 µs |

## Análisis

- **La búsqueda en la tabla hash es constante en la práctica:** entre 0,2 y 0,3 µs desde
  8 hasta 512 claves, en ambas distribuciones. El arreglo ordenado crece como log n
  (de 0,6 a 1,5 µs) y la lista lineal como n (de 0,3 a 23 µs).
- **Las búsquedas fallidas son el peor caso de la lista lineal**, porque recorre todo.
  Con 512 claves es 82 veces más lenta que la tabla hash. En la tabla hash cuestan lo
  mismo que las exitosas: solo se revisa un bucket corto.
- **Con muy pocas claves (8)**, la lista lineal empata con la tabla hash. Es la misma
  conclusión que para la caché: con muy pocos elementos no hay diferencia práctica.
- **El rehash se amortiza:** el costo por inserción pasa de 0,6 a 2 µs al crecer de 8 a
  512 claves, con 6 duplicaciones de capacidad, sin picos que dominen el total.
- **Ambas distribuciones se comportan igual.** `hash()` de texto y de enteros reparte
  bien las claves con prefijo común o consecutivas, y no se observan cadenas largas.

## Decisión y límites

Se usa `TablaHashImpl` en los índices por ID porque la búsqueda no depende del tamaño de
la cripta. Esto importa en la revisión con una cripta desconocida, posiblemente mayor
(§9). El arreglo ordenado sería una alternativa válida (O(log n), sin rehash), pero es
entre 4 y 6 veces más lento a partir de 128 claves.

**Límite conocido:** `hash()` de cadenas en Python se aleatoriza por proceso
(`PYTHONHASHSEED`). La distribución de colisiones puede variar entre ejecuciones; el
orden del juego no, porque ningún índice se recorre para decidir la simulación.
