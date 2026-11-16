# Nota para Steven: medición robusta de SC-003

**Alcance**: coordinación desde la especificación 001; no modifica producción, pruebas, benchmarks,
umbrales ni artefactos de 003.

GitHub Actions #96 sobre `c4bb758` falló únicamente en
`tests/test_bench_integrante2.py::test_explorar_no_crece_con_el_mapa_ya_conocido`: 10 332 ns
para 400 salas y 21 997 ns para 1600, una relación de 2,13 frente al límite estricto `<2×`.
Actions #95 había aprobado. La suite local completa también observó una relación de 2,2×, pero la
prueba pasó aislada; 40 comparaciones focalizadas posteriores aprobaron, con medianas de 1,437× y
1,440× al alternar el orden, y 20 procesos con semillas de hash distintas también aprobaron.

La medición actual prepara un mapa conocido completo y vuelve a explorar una sala ya conocida: hace
**cero revelaciones nuevas**, aunque SC-003 exige medir el costo de revelar la misma cantidad de
salas nuevas sobre mapas conocidos de distinto tamaño. Además cronometra una sola operación de unas
decenas de microsegundos, compara el mínimo de siete repeticiones y queda expuesta a caché, GC,
planificación del sistema y colisiones de los IDs textuales de puerta.

**Propuesta para coordinar con Steven, conservando SC-003 y el límite `<2×`**:

1. Preparar fuera del intervalo dos mapas con distinto conocimiento previo y el mismo número fijo
   `k` de revelaciones realmente nuevas, usando salas objetivo del mismo grado.
2. Resolver las salas objetivo fuera del reloj y comprobar antes de medir que ambas cargas producen
   los mismos `k` hechos y examinan la misma cantidad de puertas.
3. Cronometrar un lote de revelaciones independientes suficientemente largo, normalizar por
   revelación y comparar medianas emparejadas alternando el orden de tamaños.
4. Usar varias salas objetivo o distribuciones de hash para que una sola cadena de colisiones no
   decida el resultado; fijar solo `PYTHONHASHSEED` no corrige por sí mismo el diseño.
5. Mantener el umbral actual y ejecutar después la suite completa en Actions.

La evidencia disponible no justifica cambiar `MapaConocido`: su camino productivo itera las salidas
de la sala y usa accesos esperados O(1), sin recorrer el mapa conocido completo.
