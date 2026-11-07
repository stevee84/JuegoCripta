---

description: "Tareas de la capacidad 002-resolubilidad"
---

# Tareas: Verificación de resolubilidad de una cripta

**Entrada**: documentos de diseño en `specs/002-resolubilidad/`

**Requisitos previos**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Pruebas**: incluidas. El spec las pide en `SC-006` («los cuatro casos obligatorios tienen cada
uno una prueba automática») y el Principio XI de la constitución las exige.

**Organización**: por historia de usuario, para que cada una se implemente y se pruebe sola.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: puede ir en paralelo (archivo distinto, sin depender de tareas incompletas)
- **[US1]…[US4]**: a qué historia pertenece
- Cada tarea lleva la ruta exacta y los `FR` que cumple (§2.5)

## Rutas del proyecto

El proyecto no usa `src/`. Las capas son `contratos/`, `datos/`, `dto/`, `logica/`, `service/`,
`controller/`, `vista/`, `estructuras/`, `benchmarks/` y `tests/`, en la raíz del repositorio.

---

## Fase 1: Preparación

**Propósito**: fijar los datos de prueba antes de tocar código, para que todo lo demás se pueda
verificar sin red.

- [ ] T001 [P] Crear `tests/fixtures/api_real/cripta-01/llaves.json` con la respuesta de §4.2 que
      corresponde al fixture actual: `itm_llave_bronce` en la sala 3 e `itm_llave_negra` en la
      sala 4, ambas sin campo `enemigo`, porque en ese fixture están en el suelo
- [ ] T002 [P] Crear el paquete `tests/fixtures/resolubilidad/cripta-ciclo/` con una cripta
      cuya llave de salida está detrás de la única puerta que ella misma abre, para el caso
      obligatorio del círculo de llaves
- [ ] T003 [P] Crear el paquete `tests/fixtures/resolubilidad/cripta-enemigo/` con una llave
      que suelta un enemigo, incluyendo el campo `enemigo` y la sala donde ese enemigo inicia
- [ ] T004 [P] Crear el paquete `tests/fixtures/resolubilidad/cripta-ordenes/` con dos llaves
      alcanzables a la vez desde la sala inicial, a la misma distancia, para comprobar que el
      desempate es estable

Los tres son paquetes con la estructura que `FuenteOffline` ya sabe leer
(`generales.json`, `pagina_1.json`, `llaves.json`, `version.txt`), así que las
pruebas los cargan con esa clase y no hace falta ningún lector nuevo. Además ejercitan el mismo
camino que recorre el programa de verdad.

---

## Fase 2: Base (bloquea todo lo demás)

**Propósito**: la ubicación de las llaves tiene que poder llegar al programa. Sin esto ninguna
historia funciona.

**Crítico**: ninguna historia puede empezar hasta que esta fase esté completa.

- [ ] T005 Añadir el método abstracto `obtener_llaves(self, cripta_id: str) -> dict` a
      `contratos/fuente_datos.py`, siguiendo el contrato de
      [contracts/consulta-llaves.md](./contracts/consulta-llaves.md). Abstracto, sin
      implementación por defecto: una fuente que devolviera vacío en silencio haría pasar por
      verificada una cripta de la que no se sabe nada
- [ ] T006 [P] Implementar `obtener_llaves` en `datos/cliente_api.py` como
      `GET /criptas/<id>/llaves`, reutilizando `_solicitar` para que herede reintentos,
      presupuesto y registro (§4.3: la consulta cuenta en el presupuesto)
- [ ] T007 [P] Implementar `obtener_llaves` en `datos/fuente_offline.py` leyendo `llaves.json` del
      paquete de la cripta, igual que `generales.json`. Si el archivo no existe, señalarlo como
      dato ausente, no como lista vacía (`FR-019`)
- [ ] T008 Añadir `obtener_llaves` al doble de fuente de
      `tests/test_service/test_inicializador_partida.py`, que dejará de instanciarse al volverse
      abstracto el método (Principio VIII: se actualizan los consumidores en el mismo cambio)
- [ ] T009 Validar la respuesta en `datos/decodificador_datos.py`: `llaves` debe ser lista; cada
      entrada, `id` textual no vacío y `sala` entera; `enemigo`, si viene, texto no vacío; sin
      `id` repetidos. Una respuesta inválida se rechaza, no se completa con valores por defecto
- [ ] T010 [P] Escribir la prueba de contrato en `tests/test_datos/test_contrato_llaves.py` con
      los casos de [contracts/consulta-llaves.md](./contracts/consulta-llaves.md): con y sin
      `enemigo`, sala inexistente, `llaves` vacío, falta `llaves`, y `llaves` que no es lista

**Punto de control**: la ubicación de las llaves llega por red y sin conexión por el mismo
contrato. Las historias pueden empezar.

---

## Fase 3: Historia 1 — Saber antes de jugar si la cripta se puede ganar (P1) — MVP

**Meta**: decidir si la cripta tiene solución y, si la tiene, con qué orden de llaves; no iniciar
partida cuando no la tiene o no se pudo verificar.

**Prueba independiente**: verificar una cripta con solución y otra sin ella, y comprobar que la
primera deja empezar la partida y la segunda no.

### Pruebas de la Historia 1

- [ ] T011 [P] [US1] Escribir en `tests/test_logica/test_resolubilidad.py` la prueba de que
      `cripta-01` tiene solución y el orden de llaves coloca cada llave después de las que hacen
      falta para alcanzarla (`FR-005`)
- [ ] T012 [P] [US1] Escribir la prueba de que dos verificaciones de la misma cripta dan un
      resultado idéntico, usando `cripta_varios_ordenes.json` (`FR-006`, `SC-003`, caso
      obligatorio de §3.5)
- [ ] T013 [P] [US1] Escribir la prueba de que una llave que suelta un enemigo se ubica en la sala
      donde ese enemigo inicia, usando `cripta_llave_de_enemigo.json` (`FR-003`, caso obligatorio)
- [ ] T014 [P] [US1] Escribir la prueba de que alcanzar la sala de salida por una puerta que no
      exige la llave de salida **no** cuenta como ganar (`FR-004`)

### Implementación de la Historia 1

- [ ] T015 [US1] Crear `logica/verificador_resolubilidad.py` con el recorrido en anchura que
      aparca las puertas cerradas en una `TablaHashImpl` indexada por la llave que exigen y las
      reanuda cuando esa llave aparece (`FR-001`, `FR-002`, `FR-004`, `FR-018`). Usar
      `ColaCircular` para la frontera y `MonticuloMinimo` para el desempate por id dentro de cada
      nivel, como en `service/cargador_contenido.py:53`. Prohibidos `heapq`, `set`, `collections`
      y `sorted()` (§6.2)
- [ ] T016 [US1] Implementar en `logica/verificador_resolubilidad.py` el orden de obtención de llaves: por cercanía a
      la sala inicial, a igual distancia por menor id de sala, y dentro de una sala por id de
      llave (`FR-005`, `FR-006`)
- [ ] T017 [US1] Ubicar las llaves que sueltan enemigos en la sala donde el enemigo inicia, usando
      el campo `enemigo` de la consulta de §4.2 (`FR-003`)
- [ ] T018 [US1] Llamar a la verificación desde `service/inicializador_partida.py` antes de
      construir la partida, reutilizando el esqueleto y las llaves que la partida necesita
      después, de modo que iniciar no vuelva a pedirlos (`FR-016`, `SC-004`)
- [ ] T019 [US1] Impedir el inicio cuando la cripta no tiene solución o no se pudo verificar, en
      `service/inicializador_partida.py`, distinguiendo los dos casos (`FR-011`, `FR-019`)
- [ ] T020 [US1] Añadir las banderas `--verificar <cripta>` y `--forzar` a `configuracion.py`,
      junto a las existentes
- [ ] T021 [US1] Exponer desde `service/juego_service.py` el resultado de la verificación como
      dato, con los tres estados distinguibles —con solución y cuántas llaves, sin solución, o no
      se pudo verificar—, para que la interfaz lo pinte sin interpretar texto. El formato está en
      [contracts/cli-verificar.md](./contracts/cli-verificar.md) (`FR-013`)
- [ ] T049 [US1] **Depende de Joshua** (`controller/` y `vista/` son suyos según
      `REPARTO_PARTE2.md`): mostrar esa línea al iniciar la partida en consola y en pygame.
      §7.3 lo exige en la interfaz funcional mínima: «ver el reporte de resolubilidad al iniciar
      una partida» (`FR-013`)

**Punto de control**: la Historia 1 funciona y se puede probar sola.

---

## Fase 4: Historia 2 — Entender por qué una cripta no se puede ganar (P2)

**Meta**: cuando no hay solución, decir qué llaves faltan, qué puertas frenan el avance y dónde
está cada llave.

**Prueba independiente**: verificar una cripta sin solución y comprobar que el informe nombra las
tres cosas.

### Pruebas de la Historia 2

- [ ] T022 [P] [US2] Escribir en `tests/test_logica/test_resolubilidad.py` la prueba de que el
      informe de una cripta sin solución enumera las llaves inalcanzables, la frontera bloqueada
      con la llave de cada puerta y la ubicación de cada llave (`FR-007`, `FR-008`, `FR-009`)
- [ ] T023 [P] [US2] Escribir la prueba de que el informe no se recalcula con las llaves que el
      jugador ya consiguió (`FR-014`)
- [ ] T024 [P] [US2] Escribir en `tests/test_datos/test_guardado_binario.py` la prueba de que el
      informe sobrevive a guardar y reanudar con el mismo contenido, y que un archivo de la
      versión anterior se reporta como incompatible (`FR-020`)

### Implementación de la Historia 2

- [ ] T025 [US2] Construir el informe en `logica/verificador_resolubilidad.py` a partir de lo que
      quedó aparcado al terminar el recorrido: llaves no obtenidas, frontera bloqueada —las
      puertas cerradas adyacentes a la región alcanzable, con su llave— y dónde está cada llave
      (`FR-007`, `FR-008`, `FR-009`, `FR-018`)
- [ ] T026 [US2] En `logica/verificador_resolubilidad.py`, hacer que el informe se lea sin conocer la cripta: cada llave, puerta y sala que
      mencione debe quedar identificada (`FR-017`), con el formato de
      [contracts/cli-verificar.md](./contracts/cli-verificar.md)
- [ ] T027 [US2] Exponer el informe completo desde `service/juego_service.py` para que el
      controlador lo consulte durante la partida, devolviendo siempre el de antes de empezar, sin
      recalcular (`FR-014`)
- [ ] T050 [US2] **Depende de Joshua** (`controller/` y `vista/` son suyos): añadir el comando de
      la partida que muestra el informe completo, en consola y en pygame, consumiendo lo que
      expone T027 (`FR-014`, `FR-017`)
- [ ] T028 [US2] Subir `GuardadoBinario.VERSION` de 8 a 9 en `datos/guardado_binario.py` y guardar
      el informe en el archivo de partida, de modo que siga consultable tras reanudar y que
      reanudar no vuelva a verificar (`FR-020`)
- [ ] T029 [US2] En `datos/guardado_binario.py`, hacer que un archivo de partida de la versión 8 se reporte como incompatible en
      lugar de cargarse a medias, con el mecanismo que ya se usó al pasar de v7 a v8

**Punto de control**: las Historias 1 y 2 funcionan por separado.

---

## Fase 5: Historia 3 — Detectar llaves encerradas por sí mismas (P3)

**Meta**: señalar los círculos de llaves, no solo listar una por una las que no se pueden
conseguir.

**Prueba independiente**: verificar una cripta donde la llave de salida está detrás de la única
puerta que ella abre, y comprobar que el informe nombra el círculo.

### Pruebas de la Historia 3

- [ ] T030 [P] [US3] Escribir en `tests/test_logica/test_resolubilidad.py` la prueba del caso
      obligatorio de §3.5: la llave de salida detrás de la única puerta que ella misma abre, con
      `cripta_sin_solucion.json`; la cripta no tiene solución y el informe señala el círculo
      (`FR-010`)
- [ ] T031 [P] [US3] Escribir la prueba de un círculo de dos llaves, A detrás de una puerta que
      exige B y B detrás de una que exige A, y de que dos ejecuciones señalan el mismo círculo
      (`FR-010`, `FR-006`)
- [ ] T032 [P] [US3] Escribir la prueba de una cripta con dos círculos independientes: el informe
      reporta los dos, ordenados por la llave de menor id de cada uno

### Implementación de la Historia 3

- [ ] T033 [US3] Detectar los círculos en `logica/verificador_resolubilidad.py` recorriendo en
      profundidad el grafo de dependencias entre llaves que el recorrido ya dejó construido, sin
      pasadas adicionales por llave (`FR-010`, `FR-018`). Usar `TablaHashImpl` para el estado de
      cada llave y una lista como pila; sin `set` ni `collections`
- [ ] T034 [US3] En `logica/verificador_resolubilidad.py`, reportar todos los círculos encontrados, ordenados por la llave de menor id de
      cada uno, según lo acordado en [research.md](./research.md) (`FR-006`, `FR-010`)

**Punto de control**: las tres historias funcionan por separado.

---

## Fase 6: Historia 4 — Verificar una cripta sin abrir el juego (P3)

**Meta**: `--verificar <cripta>` da el resultado y el informe sin instanciar la vista, igual con
red y sin conexión.

**Prueba independiente**: pedir la verificación de una cripta sin iniciar partida y obtener el
mismo resultado que al empezarla.

### Pruebas de la Historia 4

- [ ] T035 [P] [US4] Escribir en `tests/test_verificar_cli.py` la prueba de que
      `--verificar` devuelve el resultado sin instanciar la vista y con los códigos de salida 0, 1
      y 2 de [contracts/cli-verificar.md](./contracts/cli-verificar.md) (`FR-012`)
- [ ] T036 [P] [US4] Escribir la prueba de que la verificación da el mismo resultado con la fuente
      de red y con la fuente sin conexión (`FR-015`)
- [ ] T037 [P] [US4] Escribir la prueba de que una cripta sin solución no inicia partida sin
      `--forzar`, y sí con ella (`FR-011`, caso obligatorio de §3.5)

### Implementación de la Historia 4

- [ ] T038 [US4] Añadir en `main.py` la rama de `--verificar`: ejecuta solo la verificación,
      imprime el informe y termina con el código de salida que corresponda, sin construir la vista
      (`FR-012`)
- [ ] T039 [US4] En `datos/fuente_offline.py`, comprobar que la ruta sin conexión usa el mismo camino lógico que la de red para
      la ubicación de las llaves, sin deducirla del contenido de las salas (`FR-015`)

**Punto de control**: las cuatro historias funcionan por separado.

---

## Fase 7: Cierre y asuntos transversales

- [ ] T040 Añadir a `benchmarks/integrante2.py` la medición del recorrido incremental frente a
      rehacer el recorrido completo por cada llave, con criptas sintéticas de muchas llaves
      encadenadas y deterministas por semilla (`SC-007`, §5.4, §6.3)
- [ ] T041 Medir la verificación sobre la cripta publicada más grande y comprobar que queda por
      debajo de 200 ms, separando la preparación del intervalo cronometrado y con calentamiento y
      repeticiones, como exige el Principio IX (`SC-001`)
- [ ] T042 Comprobar que `SC-002` se cumple: al duplicar la suma de salas, salidas y llaves, el
      tiempo no más que se duplica, dentro del margen de medición
- [ ] T043 Conectar la medición nueva a `--bench`, porque un benchmark que ningún punto de entrada
      ejecuta no cuenta como evidencia (Principio IX)
- [ ] T044 [P] Comprobar que `tests/test_restricciones_enunciado.py` sigue en verde sobre el
      código nuevo: sin `heapq`, `set`, `collections`, bibliotecas de grafos ni `sorted()` (§6.2)
- [ ] T045 Ejecutar la validación de punta a punta de [quickstart.md](./quickstart.md), los siete
      pasos
- [ ] T048 Comprobar el invariante de `SC-005` sobre todas las criptas sin solución disponibles,
      las de `tests/fixtures/`: cada informe nombra al menos una llave inalcanzable o un círculo
      de llaves. Nunca se rechaza una cripta sin explicar el motivo. Es una comprobación
      transversal sobre el informe de la Historia 2, por eso va aquí y no en su fase
- [ ] T046 Registrar en `PROMPTS_LLM.md`, en la sección «Steven Moya Porras — Parte II», los
      comandos de spec-kit usados en esta capacidad (§2.6)
- [ ] T047 Escribir en `DECISIONES.md`, en la raíz, la sección §5.4 del Documento de Decisiones con el formato de §7.1 —problema,
      alternativas consideradas, decisión, análisis de complejidad, evidencia empírica y límites
      conocidos—, enlazando a [spec.md](./spec.md) y [plan.md](./plan.md), indicando si la
      decisión final coincide con la del plan y, si no, qué medición la cambió. Las alternativas
      están en [research.md](./research.md) y la evidencia sale de T040 a T042

---

## Dependencias y orden

### Entre fases

- **Fase 1 (Preparación)**: sin dependencias, puede empezar ya
- **Fase 2 (Base)**: depende de la Fase 1 y **bloquea todas las historias**
- **Fases 3 a 6 (Historias)**: todas dependen de la Fase 2
- **Fase 7 (Cierre)**: depende de las historias que se quieran entregar

### Entre historias

- **US1 (P1)**: arranca al cerrar la Fase 2. No depende de ninguna otra historia
- **US2 (P2)**: arranca al cerrar la Fase 2. Usa el recorrido de US1, así que en la práctica
  conviene después, pero su informe se prueba solo
- **US3 (P3)**: necesita el grafo de dependencias que construye T015, de US1
- **US4 (P3)**: necesita que exista algo que verificar, o sea US1

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar antes de implementar
- El recorrido antes del informe; el informe antes de la salida por consola

### Qué puede ir en paralelo

- T001 a T004: cuatro fixtures, archivos distintos
- T006 y T007: dos implementaciones del contrato, archivos distintos
- Las pruebas de cada historia entre sí: T011–T014, T022–T024, T030–T032, T035–T037
- US2, US3 y US4 pueden repartirse una vez que T015 esté listo

### Ejemplo en paralelo: Historia 1

```text
T011  prueba de que cripta-01 tiene solución y el orden es válido
T012  prueba de que dos verificaciones dan el mismo resultado
T013  prueba de la llave que suelta un enemigo
T014  prueba de la puerta que no exige la llave de salida
```

---

## Estrategia de entrega

### Mínimo entregable: solo la Historia 1

1. Fase 1: preparación
2. Fase 2: base (bloquea todo)
3. Fase 3: Historia 1
4. **Parar y validar**: la cripta se verifica, el resultado sale al iniciar y una cripta sin
   solución no arranca
5. Con eso ya se cumple el núcleo de §3.5

### Entrega incremental

1. Fases 1 y 2 → la ubicación de las llaves llega al programa
2. + US1 → se sabe si la cripta tiene solución (mínimo entregable)
3. + US2 → se entiende por qué no, y el informe sobrevive a reanudar
4. + US3 → se señalan los círculos de llaves
5. + US4 → `--verificar` sin abrir el juego
6. + Fase 7 → mediciones y Documento de Decisiones

### Reparto

Esta capacidad es de un solo integrante, así que las fases van en orden. Lo que sí conviene es
cerrar la Fase 2 pronto: toca `contratos/fuente_datos.py`, que es compartido, y cuanto antes esté
en la rama, menos conflicto con Sofía y Joshua (Principio VIII).

**Dos tareas no son de este integrante.** T049 y T050 tocan `controller/` y `vista/`, que según
`REPARTO_PARTE2.md` son de Joshua. Están aquí porque `FR-013` y `FR-014` no se cumplen sin ellas y
§7.3 las exige en la interfaz funcional mínima, pero el trabajo es suyo. La frontera es clara: el
servicio entrega el resultado y el informe **como datos** (T021 y T027) y la interfaz los pinta
(T049 y T050). Hay que avisarle en cuanto T021 esté en la rama, porque §7.3 le mete cuatro cosas
en la interfaz y tres dependen de otros integrantes.

---

## Notas

- `[P]` = archivos distintos, sin dependencias entre sí
- Cada tarea cita sus `FR`, que es lo que §2.5 pide para la trazabilidad de la defensa
- Confirmar que cada prueba falla antes de implementar lo que la hace pasar
- Un commit por tarea o por grupo con sentido
- T005 vuelve abstracto un método de un contrato compartido: T006, T007 y T008 tienen que entrar
  en el mismo cambio o la suite queda rota
- T028 cambia el formato de guardado: conviene hacerlo de una sola vez y con T029 al lado
