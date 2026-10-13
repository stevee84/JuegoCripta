# Comparacion Binario vs JSON (§4.10)

Mediciones con una partida de 52 salas, ~150 enemigos, ~100 objetos, ~50 trampas.
Python 3.14, Windows 11, promedio de 500 iteraciones.

## Resultados

| Metrica              | Binario (v5)  | JSON          | Ventaja binario |
|----------------------|---------------|---------------|-----------------|
| Tamano en disco      | 52.7 KB       | 69.8 KB       | 1.3x compacto   |
| Carga completa       | 1.29 ms       | 0.98 ms       | JSON mas rapido  |
| Acceso a 1 sala      | 0.21 ms       | 0.90 ms       | 4.4x rapido      |

## Analisis

- **Tamano:** el binario ahorra ~25% al eliminar claves repetidas, comillas y
  delimitadores JSON. Cada campo ocupa exactamente los bytes de `struct.pack`.

- **Carga completa:** JSON es ligeramente mas rapido porque `json.load` esta
  implementado en C puro, mientras que `GuardadoBinario.cargar` recorre el
  archivo con multiples llamadas a `struct.unpack_from` en Python.

- **Acceso directo a sala:** la ventaja real del binario. El indice al final del
  archivo mapea cada `id_sala` a su offset, permitiendo leer una sola sala sin
  deserializar las demas. JSON obliga a parsear todo el archivo para extraer
  una sala.

## Justificacion del formato binario

El formato binario se justifica por:

1. **Acceso directo por indice** (`leer_sala`): 4.4x mas rapido que JSON.
   Permite restaurar salas individuales sin cargar la partida completa.
2. **Tamano compacto:** reduce almacenamiento en disco un 25%.
3. **Formato fijo:** la estructura de bytes fija facilita la validacion de
   integridad (firma "CRPT", offsets dentro del archivo, checksums).
4. **Desventaja aceptada:** la carga completa es marginalmente mas lenta que
   JSON, pero la diferencia (0.3 ms) es irrelevante frente a la latencia de
   red (~400 ms por solicitud API).
