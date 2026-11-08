# Tareas: Línea de tiempo y puntos de control

**Entrada**: [spec.md](./spec.md), [plan.md](./plan.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Pruebas**: obligatorias (§2.5 del enunciado y constitución X). Cada prueba cita en su nombre o
docstring el FR que verifica. Se escriben antes de la implementación de su historia y deben fallar
primero.

**Formato**: `- [ ] T### [P] [US#] Descripción con ruta`. `[P]` = se puede hacer en paralelo (otro
archivo, sin dependencias pendientes). `[US#]` = historia de usuario de la spec.

**Marcas de dependencia externa**:
- **[DEPENDE v10]**: necesita la sección v10 del guardado de Steven ([contrato](./contracts/guardado-v10.md)).
- **[DEPENDE 003]**: necesita la spec 003 de Steven ([contrato](./contracts/dependencias.md)).

**Archivos que no se tocan**: `logica/motor_juego.py`, `logica/agenda_eventos.py`,
`logica/comportamiento_enemigos.py`, `logica/mapa_cripta.py` (Sofía); `datos/guardado_binario.py` y
la capa de datos (Steven); `.specify/scripts/`, `.specify/templates/` y la constitución. En archivos
compartidos (`main.py`, `configuracion.py`, `service/juego_service.py`,
`controller/controlador_juego.py`, `vista/vista_pygame.py`) solo se agregan ramas, banderas o
métodos nuevos, sin cambiar firmas existentes (constitución VIII).

---

## Fase 1: Preparación (riesgo R3 primero)

**Meta**: saber, antes de construir, si deshacer y rehacer en sitio cabe en los 50 ms y deja el
estado exacto.

- [X] T001 Medir en `benchmarks/linea_tiempo.py` (archivo nuevo), para K = 10, 50 y 200, el costo de deshacer K transacciones reales anotando inversos y de rehacerlas, sobre el estado de la cripta offline más grande disponible, con calentamiento y repeticiones; medir también, como alternativa descartada, `copy.deepcopy` del estado con esas transacciones. Comprobar que después de rehacer el estado es idéntico al de antes. Anotar el resultado en `specs/004-linea-de-tiempo/research.md` (R3). Si no cabe en el presupuesto, se corrige primero el plan en un commit separado (§2.6) (FR-005, FR-018, SC-001). **Hecho el 2026-11-07**: rehacer se estimó con el costo de deshacer porque los inversos llegan con T004; la comprobación exacta de rehacer pasa a T003 (ver research R3)
- [ ] T002 Crear en `benchmarks/linea_tiempo.py` un generador de partidas largas determinista por semilla: cripta sintética con todo el contenido cargado y una secuencia de N acciones válidas (mover, esperar, atacar) ejecutadas con el motor existente, sin red. Lo usan las pruebas y `--bench` (FR-024, constitución IX)

---

## Fase 2: Base (bloquea todas las historias)

**Meta**: la línea registra cada acción cerrada y arma puntos de control, sin cambiar en nada el
comportamiento del pergamino ni de las 1071 pruebas actuales.

- [ ] T003 [P] Escribir `tests/test_logica/test_cambios_linea.py`: (a) un cambio registrado con la marca «solo línea» no lo deshace `TransaccionAccion.revertir`; (b) el deshacer condicional deshace del más reciente al más antiguo, incluidos los marcados, se detiene cuando la condición deja de cumplirse y no vacía la transacción; (c) para cada tipo de cambio de `logica/cambios.py`, deshacer y aplicar el inverso deja el estado idéntico, también si la consulta lanza una excepción a la mitad (FR-001, FR-005, FR-012)
- [ ] T004 Implementar en `logica/cambios.py`, en `TransaccionAccion`, el registro de cambios con la marca «solo línea» en la misma lista de cambios (para conservar el orden), el método de deshacer mientras se cumpla una condición que devuelve los inversos sin vaciar la transacción, y el inverso de cada tipo de cambio. `revertir` y `validar_capacidad` saltan los marcados; ninguna firma existente cambia (FR-001, FR-005, FR-012)
- [ ] T005 [P] Escribir `tests/test_logica/test_historial_linea.py`: con una línea vinculada, `cerrar_intervalo` le entrega la transacción y el reloj; `deshacer_ultimo` le avisa el recorte; sin línea vinculada el historial se comporta exactamente igual que hoy, y `LIMITE` sigue en 5 (FR-013, FR-014)
- [ ] T006 Implementar en `logica/historial_reversible.py` un método para vincular la línea de tiempo y los avisos al cerrar y al deshacer, con el estado vinculado (research R5). Sin cambios en las firmas existentes (FR-013, FR-014)
- [ ] T007 [P] Escribir `tests/test_logica/test_linea_tiempo.py` con pruebas de la estructura: «`instantes` no decreciente», «`puntos[0]` es el estado inicial (m = 0)», «nunca más de uno cada K acciones», la cola guarda referencias (no copias) de como máximo las últimas 2K acciones, y una acción rechazada no agrega nada (FR-017, FR-021)
- [ ] T008 Implementar en `logica/linea_tiempo.py` (archivo nuevo) la clase `LineaTiempo` con `k`, `instantes`, `puntos` y `cola` según [data-model.md](./data-model.md): registrar una acción cerrada y crear el paquete del punto de control con una sola copia profunda del estado y de las transacciones de su ventana cada K acciones (research R2). Sin `dict` ni `set` como índice (FR-015, FR-017, FR-021)
- [ ] T009 Implementar en `logica/linea_tiempo.py` la búsqueda binaria propia sobre `instantes` (mayor posición con instante ≤ t), con prueba en `tests/test_logica/test_linea_tiempo.py` que cubre instantes repetidos y los extremos (FR-019)
- [ ] T010 Crear y vincular la línea al estado cuando se inicia una partida nueva, en el mismo punto de `service/juego_service.py` donde hoy se vincula el historial, con K recibido por parámetro y K = 10 provisional por omisión (research R7). Prueba en `tests/test_logica/test_linea_tiempo.py`: tras N acciones reales con el motor, la línea tiene N + 1 instantes (FR-015, FR-016)
- [ ] T011 [P] Crear `controller/resumen_historia.py` (archivo nuevo): dado un estado, devuelve las líneas del resumen en el orden fijo de [data-model.md](./data-model.md) y con el texto de [cli-historia.md](./contracts/cli-historia.md); la sección del mapa dice «Mapa conocido: no disponible» mientras no exista la 003. Prueba en `tests/test_controller/test_resumen_historia.py` con un estado armado a mano (FR-004)

**Punto de control**: la suite completa sigue en 1071 aprobadas más las nuevas.

---

## Fase 3: Historia 1 — Consultar el estado en un instante pasado (P1) 🎯 MVP

**Meta**: `historia <t>` en consola.

**Prueba independiente**: partida corta con eventos conocidos; cada `historia <t>` coincide con el
estado observado al jugar en ese instante.

- [ ] T012 [P] [US1] Escribir en `tests/test_logica/test_linea_tiempo.py`: el estado en t es el de después de todos los eventos con tiempo ≤ t; si a t le corresponde una decisión, el de justo antes de tomarla; `historia 0` es el estado inicial (US1-2, US1-4, US1-5; **Apéndice B: varios eventos en el mismo t**) (FR-001, FR-002)
- [ ] T013 [P] [US1] Escribir en `tests/test_controller/test_historia.py`: t mayor que el reloj se rechaza con el mensaje de [cli-historia.md](./contracts/cli-historia.md) y sin efectos; un t no entero o negativo se rechaza; sin partida se rechaza (US1-1, US1-6; **Apéndice B: historia con t futuro**) (FR-006, FR-007)
- [ ] T014 [P] [US1] Escribir en `tests/test_controller/test_historia.py`: tras varias consultas, el reloj no cambió, `partida.log` no tiene líneas nuevas, el historial del pergamino es el mismo, el estado del azar es el mismo y la acción siguiente da el mismo resultado que sin consultas (US1-3, SC-003; **Apéndice B: historia no consume tiempo ni se registra**) (FR-005)
- [ ] T015 [US1] Implementar en `logica/linea_tiempo.py` la consulta por instante, sin copiar el estado: búsqueda de la acción; deshacer en sitio, sobre el paquete o sobre el estado vivo, hasta «antes de #(k+1)» y después la transacción k mientras el reloj sea > t; armar el resumen y rehacer con los inversos en un `finally` (research R3 y R4). Nunca más de K transacciones (FR-001, FR-002, FR-005, FR-006, FR-018)
- [ ] T016 [US1] Agregar en `controller/controlador_juego.py` el comando `historia <t>`: no pasa por el motor ni por el registro de partida; valida t y devuelve las líneas de `controller/resumen_historia.py` (FR-005, FR-006, FR-007, FR-008)
- [ ] T017 [US1] Mostrar el resumen en `vista/vista_consola.py` con el método de mensajes que ya existe, y agregar `historia` a la ayuda de comandos (FR-008)

**Punto de control**: US1 funciona y se prueba sola en consola.

---

## Fase 4: Historia 2 — Consultar el estado antes de la acción #k (P1)

**Meta**: `historia #k`.

**Prueba independiente**: secuencia de acciones conocida; `#1`, una intermedia y `#(n+1)` coinciden
con los estados observados.

- [ ] T018 [P] [US2] Escribir en `tests/test_logica/test_linea_tiempo.py`: `#1` es el estado inicial; `#(n+1)` es el estado actual; `#0` y `#(n+2)` se rechazan con el rango válido; en una partida de miles de acciones cada `#k` coincide con el estado guardado al jugar; con la partida terminada (victoria o muerte) las consultas siguen funcionando (US2-1 a US2-4, Assumptions) (FR-003, FR-007, SC-002)
- [ ] T019 [US2] Implementar en `logica/linea_tiempo.py` la consulta por acción según [data-model.md](./data-model.md): j = ⌈(k − 1) / K⌉; deshacer en sitio sobre el paquete `puntos[j]` si existe, o sobre el estado vivo si k está después del último punto, hasta k; rehacer en un `finally` (FR-003, FR-005, FR-018)
- [ ] T020 [US2] Aceptar `historia #k` en `controller/controlador_juego.py` (distinguir `#k` de `t` al leer el argumento) con los mensajes de [cli-historia.md](./contracts/cli-historia.md) (FR-003, FR-007, FR-008)

---

## Fase 5: Historia 3 — La línea se recorta al usar un pergamino (P2)

**Meta**: lo revertido deja de existir; el pergamino aparece en el pasado y consumido desde que se usó.

**Prueba independiente**: acciones, pergamino, y ninguna consulta muestra lo revertido.

- [ ] T021 [P] [US3] Escribir en `tests/test_logica/test_linea_tiempo.py`: después de un pergamino ninguna consulta muestra el estado de la acción revertida; `historia` con un t entre el reloj nuevo y el anterior se rechaza; `historia #n` es el estado actual con el pergamino consumido y `#(n+1)` se rechaza; las consultas anteriores muestran el pergamino en el inventario; dos pergaminos seguidos recortan dos veces (US3-1 a US3-3, casos borde; **Apéndice B: historia después de usar un pergamino**) (FR-012, FR-014)
- [ ] T022 [P] [US3] Escribir en `tests/test_logica/test_linea_tiempo.py` la prueba de costo del recorte: en partidas de 1 000 y de 5 000 acciones el recorte toca la misma cantidad de elementos (US3-4) (FR-013)
- [ ] T023 [US3] Implementar el recorte en `logica/linea_tiempo.py` (quitar del final de `instantes` y `cola`, descartar los puntos con m > n) llamado desde el aviso de `deshacer_ultimo` de T006 (FR-012, FR-013)
- [ ] T024 [US3] En `logica/servicio_inventario.py`, registrar con la marca «solo línea» recoger y soltar un pergamino y, al retroceder, el consumo del pergamino en la última transacción que sigue en la línea (research R6). El pergamino de retroceso no cambia su comportamiento (FR-012, FR-014)

---

## Fase 6: Historia 4 — Reproducir hasta un instante sin vista (P2)

**Meta**: `--replay partida.log --hasta t`.

**Prueba independiente**: con un `partida.log` conocido, el resumen coincide con `historia t` en la
partida original.

- [ ] T025 [P] [US4] Escribir `tests/test_controller/test_replay_hasta.py`: el resumen del replay es idéntico, línea por línea, al de `historia t`; con t posterior al final imprime el estado final y el aviso «terminó antes»; sin `--hasta` el replay es el de la Parte I; un log con versión incompatible se rechaza igual que antes; no se instancia la vista (US4-1 a US4-4; **Apéndice B: --replay --hasta más allá del final**) (FR-009, FR-010, FR-011)
- [ ] T026 [US4] Agregar la bandera `--hasta t` en `configuracion.py`: entero ≥ 0 y solo junto con `--replay`; si no, error antes de reproducir. Prueba en `tests/test_configuracion.py` (FR-009)
- [ ] T027 [US4] Agregar el parámetro `hasta` a `EjecutorReplay.reproducir` en `controller/ejecutor_replay.py`: reproducir con la línea vinculada y detenerse antes de la primera acción cuyo instante de decisión sea > t; luego consultar t en la línea o, si t supera el final, imprimir el estado final y el aviso (FR-009, FR-010, FR-011)
- [ ] T028 [US4] En `main.py`, pasar `--hasta` al replay e imprimir el resumen sin instanciar la vista (FR-009, constitución IV)

---

## Fase 7: Historia 6 — Ajustar la frecuencia de puntos de control (P3)

**Meta**: `--checkpoint-cada K`.

**Prueba independiente**: la misma partida con varios K da los mismos resúmenes.

- [ ] T029 [P] [US6] Escribir en `tests/test_logica/test_linea_tiempo.py`: con K = 1, K = 7, K = 50 y un K mayor que la cantidad de acciones, todas las consultas de la misma partida son idénticas; ninguna consulta deshace más de K transacciones (contar en la prueba) (US6-1, US6-3, casos borde) (FR-018, FR-023)
- [ ] T030 [US6] Agregar la bandera `--checkpoint-cada K` en `configuracion.py` (entero ≥ 1; 0, negativos o no enteros: error al arrancar), con prueba en `tests/test_configuracion.py` (US6-2) (FR-015)
- [ ] T031 [US6] Pasar K desde `main.py` a la partida interactiva, al replay y a `--bench` (FR-015, FR-016)

---

## Fase 8: Historia 5 — Guardar y cargar sin perder la línea (P3)

**Meta**: la línea sobrevive a guardar y reanudar.

- [ ] T032 [P] [US5] Escribir en `tests/test_logica/test_linea_tiempo.py`: `exportar_bytes` e `importar_bytes` conservan el estado vivo, K, instantes, puntos y cola; tras importar, todas las consultas dan lo mismo que antes, la cantidad de puntos de control es la misma (ninguno extra) y todos siguen en múltiplos de K; al importar con otro K pedido se conserva el guardado y se informa (US5-1, US5-2) (FR-017, FR-028, FR-029, FR-030)
- [ ] T033 [US5] Implementar `exportar_bytes(estado)` e `importar_bytes(datos) -> (estado, linea)` en `logica/linea_tiempo.py` según [guardado-v10.md](./contracts/guardado-v10.md), serializando el estado vivo y la línea en una sola operación con `pickle` (FR-017, FR-028, FR-029, FR-030)
- [ ] T034 [US5] **[DEPENDE v10]** Escribir en `tests/test_datos/test_guardado_linea.py` la prueba de punta a punta: guardar con el guardado v10, cargar y repetir consultas; usar el aviso de K de FR-030 en `controller/controlador_juego.py` al cargar (US5-1, US5-2) (FR-028, FR-030)
- [ ] T035 [US5] **[DEPENDE v10]** Escribir en `tests/test_datos/test_guardado_linea.py` que un archivo v9, uno v8 y uno de la Parte I se reportan como incompatibles y nunca se cargan en silencio (US5-3; **Apéndice B: archivo de la Parte I**) (FR-031)

---

## Fase 9: Interfaz §7.3 (resolubilidad de la spec 002 y pygame)

**Meta**: las partes de §7.3 que no dependen de la 003.

- [ ] T036 [P] Escribir en `tests/test_controller/test_resolubilidad_interfaz.py`: al iniciar se muestra una de las tres líneas de [cli-verificar.md](../002-resolubilidad/contracts/cli-verificar.md) según el informe (con solución, sin solución, no verificada); el comando `resolubilidad` muestra el informe completo y es el mismo antes y después de conseguir llaves (FR-013 y FR-014 de la spec 002)
- [ ] T037 Tarea **002-T049** (de la spec 002): mostrar la línea de resolubilidad al iniciar la partida desde `controller/controlador_juego.py`, en `vista/vista_consola.py` y en `vista/vista_pygame.py`, a partir de `JuegoService.obtener_informe_resolubilidad()` (FR-013 de la 002)
- [ ] T038 Tarea **002-T050** (de la spec 002): comando `resolubilidad` en `controller/controlador_juego.py` que muestra el informe completo en consola y en pygame (FR-014 y FR-017 de la 002)
- [ ] T039 Agregar en `vista/vista_pygame.py`, en métodos nuevos, un botón «Historia» que pide t o #k y muestra las líneas del resumen en un panel; la lógica sigue en el controlador (FR-008)

---

## Fase 10: Mapa conocido en el resumen (depende de la spec 003)

- [ ] T040 [US1] **[DEPENDE 003]** Usar en `controller/resumen_historia.py` la consulta de solo lectura del mapa conocido de la 003 sobre el estado reconstruido, y escribir en `tests/test_controller/test_resumen_historia.py` que el mapa de `historia <t>` coincide con el que mostraba el comando de mapa en ese instante, incluido después de un pergamino que revierte una exploración con antorcha (FR-004, FR-022)

---

## Fase 11: Mediciones (`--bench`)

- [ ] T041 [P] En `benchmarks/linea_tiempo.py`, medir tiempo de consulta (peor caso y promedio), memoria retenida por la línea con `tracemalloc` y el costo de la acción que crea un punto de control frente al límite de 20 ms por ciclo (riesgo de T001), con 5 000 acciones, para K = 10, 50 y 200 y sin puntos de control; y memoria con 2 500 frente a 5 000 acciones (FR-024, SC-001, SC-004, SC-005)
- [ ] T042 [P] En `benchmarks/linea_tiempo.py`, medir reconstrucción hacia atrás frente a hacia adelante re-simulando, sobre la cripta sintética de T002 con todo el contenido cargado. La variante hacia adelante restaura el estado del azar desde el punto de control y comprueba que la re-simulación produce exactamente el mismo estado (FR-020, FR-024, research R1)
- [ ] T043 [P] En `benchmarks/linea_tiempo.py`, medir un retroceso con pergamino de punta a punta (reloj, agenda, rastro, puertas, trampas, inventario) frente a restaurar una copia completa del estado, con la carga de la Parte II (FR-025)
- [ ] T044 [P] En `benchmarks/linea_tiempo.py`, medir una reproducción completa de `partida.log` y el rechazo de un log con versión incompatible (FR-026)
- [ ] T045 [P] En `benchmarks/linea_tiempo.py`, medir la vista ordenada del inventario por peso, valor y nombre, comprobando que el orden real no cambia, y el rechazo de recoger con el inventario lleno (FR-027)
- [ ] T046 Conectar `benchmarks/linea_tiempo.py` como proveedor de `main.py --bench`, y escribir `tests/test_bench_linea_tiempo.py` que comprueba que la salida de `--bench` incluye cada medición de T041 a T045 (constitución IX)

---

## Fase 12: Cierre

- [ ] T047 Elegir el K por defecto con los datos de T041 y fijarlo en `configuracion.py`; actualizar R7 en `research.md`. Si cambia el valor del plan, corregir primero el plan en un commit separado (FR-016)
- [ ] T048 Escribir la sección §5.5 de `DECISIONES.md`: problema, alternativas, decisión, complejidad, evidencia de `--bench`, límites, enlace a spec y plan, y si la decisión final coincide con el plan (enunciado §7.1)
- [ ] T049 Agregar a `README.md` las banderas `--checkpoint-cada` y `--replay … --hasta` y el comando `historia` (enunciado §7.2)
- [ ] T050 Correr `python -m pytest -q` completo y los pasos de [quickstart.md](./quickstart.md); informar aprobadas, omitidas (las [DEPENDE]) y fallidas por separado (constitución XI)

---

## Dependencias y orden

- **Fase 1** → **Fase 2** → historias. T001 puede obligar a corregir el plan (R3) antes de la Fase 2.
- **US1** (Fase 3) es el MVP. **US2** necesita la consulta de US1 (comparte el mecanismo).
- **US3**, **US4** y **US6** dependen solo de la Fase 2 y de US1; se pueden hacer en cualquier orden.
- **US5**: T032-T033 dependen de la Fase 2; T034-T035 esperan el guardado v10 de Steven.
- **Fase 9**: T036-T038 no dependen de nada de la 004 (solo de la 002, ya disponible); T039 necesita US1.
- **Fase 10** espera la spec 003.
- **Fase 11** necesita US1, US2 y US3 (T043 y T045 se pueden adelantar).

## Paralelismo

- Fase 2: T003, T005, T007 y T011 son archivos distintos.
- US1: T012, T013 y T014 a la vez; después T015 → T016 → T017.
- Fase 9 en paralelo con las historias de la línea.
- Fase 11: T041 a T045 en paralelo (mismo archivo pero funciones independientes: coordinar el
  orden de los commits).

## Estrategia

1. Fase 1 (decidir A o B con datos) → Fase 2 → US1: **MVP**, demostrable con `historia <t>`.
2. US2 y US3 (Apéndice B completo salvo replay y archivo).
3. US4 y US6; Fase 9 (§7.3 de la 002) cuando convenga.
4. US5 cuando Steven tenga la v10; Fase 10 cuando exista la 003.
5. Fase 11 y cierre.

## Trazabilidad del Apéndice B (línea de tiempo)

| Caso | Escenario | Prueba |
|---|---|---|
| historia con t futuro | US1-1 | T013 |
| historia tras un pergamino | US3-1 | T021 |
| varios eventos en el mismo t | US1-2 | T012 |
| historia no consume tiempo ni se registra | US1-3 | T014 |
| --replay --hasta más allá del final | US4-2 | T025 |
| archivo de la Parte I | US5-3 | T035 [DEPENDE v10] |
