# Revisión de efectos temporales y trampas — parte 2

## Alcance y fuente

La referencia funcional es `docs/enunciado.pdf`:

- §2.3, página 5: intervalo por velocidad y reprogramación proporcional con
  secuencia nueva.
- §2.4, página 5: activación de enemigos al entrar; los iniciales en tiempo 0.
- §2.7, página 7: antídoto, antorcha y pociones con
  `modificador_velocidad`/`duracion`; `USAR` cuesta 50.
- §2.10, página 8: veneno cada 80 durante 400, regeneración cada 200,
  antorcha hasta su duración, trampas inmediatas al entrar y rearme 300 salvo
  ficha, además de cancelación de activaciones futuras.
- §2.11, páginas 8–9: reversión de acción, eventos, efectos, inventario,
  puertas y trampas sin copiar el estado completo.
- §4.1, página 13: siguiente evento por `(tiempo, secuencia)`, muerte y
  cancelación sin depender de recorrer todos los eventos pendientes.
- §4.3, página 13: una entidad debe tener su ficha resuelta antes de simularse.
- §4.10, página 15: versión e incompatibilidad del guardado binario.

## Implementación

### Veneno y antídoto

`GestorEfectos.aplicar_veneno` obtiene `daño` del registro recibido, fija duración
400 y programa pulsos absolutos en 80, 160, 240 y 320, más el vencimiento en 400.
Cada efecto conserva únicamente los IDs de sus eventos. Cancelar usa esos IDs y
la identidad del objeto de efecto evita que un evento de una aplicación anterior
produzca daño. Una reaplicación sustituye el veneno anterior del mismo actor.

El antídoto se usa desde el objeto actualmente seleccionado, exige ficha resuelta,
cancela el veneno del jugador y consume la instancia. Sin veneno activo se rechaza
sin tiempo, consumo ni historial.

### Regeneración

Al activar un enemigo, el motor consulta `ficha["regeneracion"]`. Si existe,
programa el primer pulso a `reloj + 200`; cada pulso válido programa solamente el
siguiente. Se limita por `vida_max`, no revive muertos y se cancela por la vía
común de muerte. La identidad del efecto evita duplicados al volver a una sala.
El efecto sigue al enemigo activo aunque el jugador abandone su sala.

### Antorcha y velocidad

Una antorcha válida se consume y queda representada como efecto `ANTORCHA` dentro
de `estado.efectos_activos`; su vencimiento usa la duración exacta de la ficha.

Las pociones de velocidad leen `modificador_velocidad` como delta y validan
`velocidad_actual + modificador > 0`. `GestorEfectos.aplicar_velocidad` recibe la
velocidad final y reutiliza `MotorJuego.cambiar_velocidad`. Si todavía no existe
la próxima acción —caso normal durante `USAR`— primero cambia la velocidad y el
motor programa luego el costo 50 con esa velocidad. Al vencer, la próxima acción
existente se escala con la fórmula de §2.3 y recibe una secuencia nueva.

### Trampas

Después de cambiar la sala, registrar el rastro y activar enemigos, el jugador
dispara las trampas armadas del destino. Cada trampa toma `daño` y `rearme` de su
ficha (`300` si `rearme` no aparece), se desarma y conserva el ID de su único
evento de rearme. Un evento obsoleto no puede rearmarla. Si una trampa mata al
jugador se usa `ReglasCombate.procesar_muerte`, no se programa otra acción del
jugador y no se disparan las trampas posteriores.

## Ambigüedades y convenciones

1. **Pulso exactamente al vencer:** §2.10 no establece si el extremo es
   inclusivo. Se adopta el intervalo `[inicio, vencimiento)`: en 400 vence y no
   hay quinto pulso. Hay una regresión explícita.
2. **Reaplicación de veneno:** no se define acumulación. Se mantiene un veneno por
   actor y una nueva aplicación sustituye la anterior. Esto también hace
   inequívoco el antídoto singular descrito en §2.7.
3. **Segunda antorcha:** no se define acumulación ni renovación. Se rechaza
   mientras exista una activa, sin consumir la segunda.
4. **Varios cambios temporales de velocidad:** no se define composición. Se
   conserva la restricción de uno por actor; un segundo se rechaza sin consumo.
   Así el vencimiento no elimina otro modificador temporal vigente.
5. **Varias trampas:** el PDF no fija su orden. Se usa el orden estable de
   `Sala.trampas`; solo el jugador las dispara al entrar, porque §2.10 nombra
   expresamente al jugador. Tras su muerte se detiene el recorrido.
6. **Otros efectos de trampa:** el contrato mostrado solo publica el campo
   `daño` y `rearme`; no se inventaron nombres para veneno, velocidad u otros
   efectos de trampa. Una ficha armada sin daño válido bloquea el movimiento.
7. **Iluminación:** no existía otro estado de visibilidad. La antorcha activa se
   representa con el mecanismo temporal común; no se inventó alcance visual.

## Reversión e inventario

`CambioConsumirObjeto` conserva el nodo retirado, sus vecinos, el cursor y la
ubicación; deshacer reinserta la misma instancia. Las mutaciones de vida,
velocidad, efectos, trampas, reloj, secuencias y listas usan los cambios pequeños
existentes. La agenda registra inserciones, extracciones, cancelaciones y
reprogramaciones. Un error aborta el intervalo completo.

`ServicioInventario` solo implementa en esta parte antídoto, antorcha y poción de
velocidad. Devuelve costo 50; el reloj se avanza únicamente en `MotorJuego`, por
lo que no hay doble cobro.

## Complejidad y limitaciones

- Cancelar un efecto ya no recorre toda la agenda para descubrir sus eventos.
  Recorre su pequeña lista de IDs pendientes.
- Esta revisión de parte 2 dejó como pendiente la cancelación lineal. La parte 3
  la sustituyó por índices AVL propios y posiciones actualizadas del montículo:
  cancelar `k` eventos cuesta ahora `O(k log n)` y localizar las acciones de un
  actor cuesta `O(log n + k)`, sin añadir tabla hash.
- La regeneración conserva un solo evento futuro por enemigo, por lo que su lista
  de IDs no crece con el tiempo.
- El guardado binario permanece en versión 2 y detecta versiones incompatibles,
  pero no serializa inventario completo, fichas resueltas, efectos, agenda,
  historial ni `evento_rearme_id`. La carga continúa marcada `reanudable=False`.

## Pruebas

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q tests/test_logica/test_efectos_trampas_parte2.py tests/test_logica/test_gestor_efectos.py tests/test_logica/test_velocidad.py tests/test_logica/test_servicio_inventario.py tests/test_logica/test_inventario.py tests/test_logica/test_agenda_eventos.py tests/test_logica/test_historial_reversible.py tests/test_logica/test_cambios.py tests/test_logica/test_motor_juego.py tests/test_integracion_sofia.py tests/test_logica/test_rastro_parte1.py
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q
```

- Relacionadas: **150 aprobadas**.
- Suite completa: **403 aprobadas, 0 fallidas**.

La parte 3 no se inició.
