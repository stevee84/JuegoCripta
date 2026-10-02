# Cierre de verificación: parte 1

Rama `Sofia`, HEAD `c054d77`. Se conservaron los cambios locales de la parte 1
y los anteriores. No se hizo commit, push, cambio de rama ni incorporación de hash.

## Fuentes y límites

Se revisaron `EQUIPO.md`, contratos de motor/agenda, DTO, decodificador, motor,
acciones, efectos de velocidad, historial y pruebas. No hay AGENTS.md ni un
enunciado completo: solo `docs/distribucion_cripta.pdf`, ya revisado, que confirma
costos base y frescura menor que 400 pero no detalla velocidad ni desempate.

Las instrucciones actuales confirman conservar velocidad, activación al entrar,
ataque prioritario y reversión. La fórmula existente en `calcular_intervalo` es
`max(1, costo * 100 // velocidad)`. Su comentario atribuye la fórmula a la sección
2.3; no se pudo contrastar esa sección con el original ausente. Se verifica y
conserva el comportamiento actual solicitado, sin afirmar una validación documental
del enunciado completo.

## Clasificación de los 20 fallos

Todos son **expectativas/preparaciones antiguas que contradicen las reglas actuales
confirmadas por la usuaria**. Ninguno de estos 20 demostró un error de implementación.
No se eliminaron pruebas ni aserciones para encubrir fallos. Los casos de otras
funcionalidades conservan sus reglas; solo se ajustó su contexto temporal/de combate.

Abreviaturas: I = `tests/test_integracion_sofia.py`; F = `tests/test_flujo_sofia.py`;
C = `tests/test_logica/test_contratos_compartidos.py` (importa el diagnóstico).

| # | Prueba | Causa y solución |
| --- | --- | --- |
| 1 | F::test_controlador_servicios_vista_y_motor_hasta_terminacion | Demo con velocidad 1: muerte en 20000, no 200. Se ajusta el reloj esperado, se mantienen muerte, acciones, historial y suelo. |
| 2 | F::test_arranque_real_demo_por_subproceso | Misma causa: salida esperada `Tiempo: 20000`. Se mantiene ejecución real y fin de partida. |
| 3 | F::test_servicio_no_consume_costo_dos_veces_y_reanuda_azar_actual | Decisiones en 10000 y 20000. Conserva comparación de azar y eventos al reanudar. |
| 4 | I::test_muerte_unica_cancelacion_y_deshacer_repite_azar | Evento en 500 se consumía antes de la decisión en 10000. La fixture pasa explícitamente a velocidad 100 y conserva todas las aserciones de cancelación, identidad, reversión y azar. |
| 5 | I::test_movimiento_rastros_visitas_y_eventos_se_revierten_juntos | Confundía costo 100 con tiempo 100 a velocidad 1. Fixture a velocidad 100; se conservan movimiento enemigo, rastros y reversión completa. |
| 6 | I::test_evento_cancelado_o_reemplazado_no_daña[False] | Un guardián se activa al iniciar y daña 6; no es daño del efecto cancelado. Fixture a velocidad 100, vida esperada 94, exactamente un ataque de 6 y ninguna noticia de veneno. |
| 7 | I::test_evento_cancelado_o_reemplazado_no_daña[True] | Misma activación; además el nuevo pulso en 150 antes caía dentro del intervalo de 10000. Con velocidad 100 la decisión queda antes del nuevo pulso. Misma verificación precisa que #6. |
| 8 | I::test_duracion_temporal_pulsos_y_empate_siguiente_decision | Ignoraba velocidad y ataques del guardián activo. Fixture a velocidad 100: vida 88, 80 y 73 (veneno 6/3/0 más ataques 6/5/7, semilla 7). Conserva duración, agenda y vencimiento. |
| 9 | I::test_enemigo_actua_y_guardian_permanece_en_sala | Esperaba próxima acción en 200 con velocidad 1. Fixture a velocidad 100; conserva ataque real, reprogramación y permanencia. |
| 10 | I::test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local[100-SEGUIR_RASTRO] | Compartía sala: debía atacar. Se coloca al jugador en la sala lejana ya creada. Conserva prohibición de búsqueda global y cierre de puerta. |
| 11 | I::test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local[499-SEGUIR_RASTRO] | Misma corrección de ubicación que #10. |
| 12 | I::test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local[500-ESPERAR] | Misma corrección de ubicación que #10; rastro futuro sigue excluido. |
| 13 | I::test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local[501-ESPERAR] | Misma corrección de ubicación que #10; rastro futuro sigue excluido. |
| 14 | I::test_rastreador_descarta_exactamente_400_y_prefiere_el_mas_reciente | Debía atacar en vez de devolver destino. Jugador en otra sala, conservando expectativas originales de frescura y destino. |
| 15 | I::test_recoger_soltar_costos_cursor_y_reversion | Costos 25 pero intervalos 2500. Fixture a velocidad 100; mantiene costos, reloj 25/50, cursor y reversión. |
| 16 | I::test_abrir_cierre_automatico_y_reversion | Abrir tardaba 5000: cierre en 75 ya había ocurrido. Fixture a velocidad 100, decisión en 50; se conservan las aserciones de cierre y reversión. |
| 17 | I::test_trampa_evento_rearme_y_muerte_compartida | Ignoraba ataque de guardián activado. Con velocidad 100: vida 84 = 100 - 10 - 6; conserva rearme, reversión y muerte. |
| 18 | I::test_empate_posterior_a_decision_se_conserva_para_siguiente_accion | El rearme en 100 ocurría antes de la decisión en 10000. Fixture a velocidad 100; se conservan las expectativas de prioridad por secuencia y evento pendiente. |
| 19 | I::test_error_en_evento_revierte_dano_previo_agenda_y_secuencias | Tras retirar el evento inválido, también ataca el guardián. Fixture a velocidad 100 y vida 91 = 100 - 3 - 6. Se mantiene el aborto completo y restauración del pulso. |
| 20 | C::test_muerte_cancela_solo_eventos_del_actor | Evento ajeno TURNO en 200 caía antes de la decisión en 10000 y no tiene despachador. Se conserva velocidad 1 y se mueve a 20000: se comprueba que queda pendiente y no se cancela. No se implementó un despachador ficticio para TURNO. |

## Justificación de las preparaciones

La fixture de I utiliza velocidad 100 explícita para conservar las ventanas de
100/50/25 sobre las que prueban esas integraciones. No se elimina la influencia
de velocidad: se añadieron pruebas independientes con velocidades 1, 100, 200 y
300 y expectativas literales 10000, 100, 50 y 33. La demo conserva velocidad 1.

Se comprueba que el enemigo de la sala inicial esté activo aunque su flag inicial
sea falso. No se silencian sus ataques para aislar efectos: se verifica el daño
real agregado y, para cancelación, la ausencia explícita de pulsos de veneno.

Las pruebas de rastreo ahora cumplen su precondición: jugador en otra sala.
Las tres prioridades de ataque compartiendo sala se prueban separadamente en
`test_rastro_parte1.py`, sin necesitar mapa ni rastro para decidir el ataque.

## Identificadores

`Sala.__init__(id_sala: str)`, `Puerta.destino_sala_id: str` y
`MapaCripta.obtener_sala(id_sala: str)` establecen cadenas como convención.
El decodificador conserva `datos["id_sala"]` sin convertirlo. Las salas reales
de las fixtures usan IDs como `S1`, `sala_inicio`, `entrada`, no números.

No se encontró enunciado que exija orden numérico. Se mantiene `<` directamente
sobre los IDs del proyecto: comparación lexicográfica, por lo que `S10 < S2`.
La prueba de empate cubre ambos órdenes de vecinos; no se usa `str(id)`, extracción
de sufijos ni ordenamiento. Esta es la convención existente, no una afirmación
de que se haya leído una regla académica ausente.

## Archivos modificados en este cierre

- `tests/test_integracion_sofia.py`: contexto de velocidad, ubicación del jugador
  en pruebas de rastreo y daño de enemigos activados.
- `tests/test_flujo_sofia.py`: reloj de la demo y reanudación con velocidad 1.
- `docs/diagnostico_steve.py`: evento ajeno verdaderamente posterior a la decisión.
- `tests/test_logica/test_rastro_parte1.py`: seis casos adicionales de intervalos,
  activación/ataque y vencimiento de velocidad con reversión.
- `docs/cierre_verificacion_parte1.md`: esta clasificación y evidencia.

No se necesitó modificar código de producción adicional al trabajo de parte 1.
Los cambios locales previos en motor y comportamiento permanecen conservados.

## Comandos y resultados

Intérprete: `/tmp/opencode/juegocripta-venv/bin/python`.

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q tests/test_integracion_sofia.py tests/test_flujo_sofia.py tests/test_logica/test_rastro_parte1.py tests/test_logica/test_velocidad.py tests/test_logica/test_agenda_eventos.py tests/test_logica/test_contratos_compartidos.py
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q
```

- Antes del cierre: **353 aprobadas, 20 fallidas**, ejecución de la parte 1.
- Pruebas relacionadas después de ajustar expectativas: **87 aprobadas**.
- Pruebas relacionadas con las seis verificaciones adicionales: **93 aprobadas**.
- Suite completa final: **379 aprobadas, 0 fallidas, sin skips ni xfail**.

## Pendientes y alcance

No quedan fallos en la suite ejecutada. Falta el texto del enunciado completo para
contrastar documentalmente su sección 2.3 y una eventual regla distinta de IDs.
RETROCEDER mediante pergamino sigue sin implementarse; la reversión se verifica
por el historial existente. No se han cambiado sus reglas, ni ampliado veneno,
regeneración, trampas, persistencia u otras funcionalidades. El informe anterior
`revision_integracion_sofia.md` es histórico: sus números preceden a los cambios
manuales de velocidad/activación y a este cierre.

La parte 2 no se inició.
