# Comparación binario vs JSON (§4.10)

## Cómo se reproduce

```
python main.py --bench
```

Las filas `guardado_binario_*` y `guardado_json_*_alternativa` salen de
`benchmarks/integrante2.py::medir_guardado`. Para cada una de las 4 criptas
publicadas se arma una partida real (`InicializadorPartida` + `FuenteOffline`
sobre las respuestas del API guardadas en `tests/fixtures/api_real/`).

- **Mismo estado lógico:** el JSON es exactamente lo que devuelve
  `GuardadoBinario.cargar` del binario, con las salas como lista de registros.
- **Medición:** la preparación queda fuera del cronómetro (`perf_counter_ns`),
  con 1 calentamiento y 15 repeticiones. Se informa la mediana.
- **Leer una sala:** se lee la última sala del índice. En JSON hay que parsear
  el archivo completo y buscarla; en binario se usa el índice ordenado con
  búsqueda binaria.
- **Coherencia:** el benchmark verifica que los dos formatos devuelvan la misma sala.

Entorno de los números de abajo (guardado v6): Python 3.14.0, Windows 11 (10.0.26200).

## Resultados (formato v6)

| Cripta | Salas | Bytes binario | Bytes JSON | Binario más chico |
|---|---:|---:|---:|---:|
| cripta-01 | 6 | 5 353 | 12 547 | 57 % |
| cripta-02 | 20 | 8 737 | 21 040 | 58 % |
| cripta-03 | 40 | 14 280 | 35 138 | 59 % |
| cripta-04 | 50 | 16 958 | 41 978 | 60 % |

En v5 cada ID ocupaba 32 bytes fijos; en v6 ocupa 2 bytes de largo más su texto UTF-8.
Por eso el binario bajó, por ejemplo de 30 914 a 16 958 bytes en cripta-04, y además ya
no limita el largo de los IDs (§9).

Mediana en microsegundos por operación:

| Cripta | Leer 1 sala binario | Leer 1 sala JSON | Cargar todo binario | Cargar todo JSON | Guardar binario | Guardar JSON |
|---|---:|---:|---:|---:|---:|---:|
| cripta-01 (6) | 166 | 294 | 428 | 331 | 2 404 | 1 235 |
| cripta-02 (20) | 179 | 385 | 650 | 437 | 2 798 | 2 013 |
| cripta-03 (40) | 241 | 520 | 1 046 | 571 | 3 555 | 2 809 |
| cripta-04 (50) | 204 | 583 | 1 259 | 604 | 3 470 | 3 322 |

## Análisis

- **Leer una sala (la razón del formato):** en binario el tiempo se mantiene
  casi constante (166–241 µs, dominado por abrir el archivo), porque la
  cabecera apunta al índice y la búsqueda binaria salta directo al offset.
  En JSON crece con la partida, porque siempre hay que parsear todo. Con 50
  salas el binario es **2,9 veces más rápido**, y la diferencia aumenta con
  criptas mayores, como las que se usarán en la revisión (§9).
- **Tamaño:** el binario ocupa entre un 57 y un 60 % menos, porque no repite
  nombres de claves, comillas ni delimitadores, y los textos solo ocupan su largo real.
- **Cargar todo:** JSON es unas 2 veces más rápido. `json.load` está escrito en
  C, mientras que `GuardadoBinario.cargar` decodifica campo por campo con
  `struct` en Python y además valida cada registro.
- **Guardar:** el binario es más lento porque escribe en un archivo temporal,
  valida la reconstrucción completa y recién entonces reemplaza el anterior
  (si falla, el guardado previo queda intacto). JSON solo hace `json.dump`.

## Decisión

Se mantiene el binario. §4.10 exige poder recuperar una sala sin leer el
archivo completo, y es la única operación donde JSON no tiene una respuesta
equivalente. La desventaja en carga completa y guardado es de 1 a 2 ms por
partida, ocurre una vez por sesión y es despreciable frente a una sola
solicitud al API (~400 ms, §3.4).

**Límite conocido:** si el juego solo cargara partidas completas y nunca salas
sueltas, JSON sería más simple y más rápido de cargar.
