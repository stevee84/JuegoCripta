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

Entorno de los números de abajo (guardado v7, 18/10/2026): Python 3.14.0, Windows 11 (10.0.26200).

## Resultados (formato v7)

| Cripta | Salas | Bytes binario | Bytes JSON | Binario más chico |
|---|---:|---:|---:|---:|
| cripta-01 | 6 | 5 359 | 12 709 | 58 % |
| cripta-02 | 20 | 8 757 | 21 580 | 59 % |
| cripta-03 | 40 | 14 320 | 36 218 | 60 % |
| cripta-04 | 50 | 17 008 | 43 328 | 61 % |

En v5 cada ID ocupaba 32 bytes fijos; desde v6 ocupa 2 bytes de largo más su texto UTF-8.
Por eso el binario bajó, por ejemplo de 30 914 a 16 958 bytes en cripta-04, y además ya
no limita el largo de los IDs (§9). La v7 agrega un byte por sala (`contenido_cargado`,
carga gradual de §4.2): en cripta-04 son 50 bytes más (17 008).

Mediana en microsegundos por operación:

| Cripta | Leer 1 sala binario | Leer 1 sala JSON | Cargar todo binario | Cargar todo JSON | Guardar binario | Guardar JSON |
|---|---:|---:|---:|---:|---:|---:|
| cripta-01 (6) | 219 | 304 | 472 | 324 | 2 648 | 1 493 |
| cripta-02 (20) | 242 | 386 | 749 | 390 | 2 572 | 2 105 |
| cripta-03 (40) | 214 | 578 | 1 046 | 536 | 2 885 | 2 722 |
| cripta-04 (50) | 213 | 601 | 1 209 | 607 | 2 768 | 3 243 |

## Análisis

- **Leer una sala (la razón del formato):** en binario el tiempo se mantiene
  casi constante (213–242 µs, dominado por abrir el archivo), porque la
  cabecera apunta al índice y la búsqueda binaria salta directo al offset.
  En JSON crece con la partida, porque siempre hay que parsear todo. Con 50
  salas el binario es **2,8 veces más rápido**, y la diferencia aumenta con
  criptas mayores, como las que se usarán en la revisión (§9).
- **Tamaño:** el binario ocupa entre un 58 y un 61 % menos, porque no repite
  nombres de claves, comillas ni delimitadores, y los textos solo ocupan su largo real.
- **Cargar todo:** JSON es unas 2 veces más rápido. `json.load` está escrito en
  C, mientras que `GuardadoBinario.cargar` decodifica campo por campo con
  `struct` en Python y además valida cada registro.
- **Guardar:** en criptas chicas el binario es más lento, porque escribe en un archivo
  temporal, valida la reconstrucción completa y recién entonces reemplaza el anterior
  (si falla, el guardado previo queda intacto); JSON solo hace `json.dump`. Con 50
  salas los dos quedan parejos (2,8 ms frente a 3,2 ms), porque el JSON escribe más bytes.

## Decisión

Se mantiene el binario. §4.10 exige poder recuperar una sala sin leer el
archivo completo, y es la única operación donde JSON no tiene una respuesta
equivalente. La desventaja en carga completa y guardado es de 1 a 2 ms por
partida, ocurre una vez por sesión y es despreciable frente a una sola
solicitud al API (~400 ms, §3.4).

**Límite conocido:** si el juego solo cargara partidas completas y nunca salas
sueltas, JSON sería más simple y más rápido de cargar.
