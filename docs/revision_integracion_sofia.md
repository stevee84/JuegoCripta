# Revisión e integración de Sofía

Fecha: 1 de octubre de 2026.

## 1. Resultado y alcance

**349 pruebas aprobadas, 0 fallidas, 0 omitidas en la suite final.**
El escenario pequeño con clases reales funciona desde `main.py` hasta la
muerte del jugador. Se corrigieron los tres fallos reproducidos de combate
y efectos, y se integró la simulación con el historial e inventario existentes.

**La integración académica completa sigue pendiente de especificaciones.**
No están resueltos el uso/equipamiento según fichas reales, pergaminos,
velocidad, todas las reglas de efectos, victoria, arranque desde datos reales,
replay, puntajes ni la continuación determinista desde un archivo.
La demostración usa datos sintéticos identificados como tales.

## 2. Diagnóstico inicial y fuentes

- Repositorio: JuegoCripta; rama `Sofia`.
- HEAD inicial: `74d01ecb3e66360c7488249f6b05bb530f8a03e5`.
- Durante la comprobación final apareció el commit externo
  `c60677603db8afc584517a40b5ce60d86d3b6f11` (`cambios de opencode`),
  atribuido a Sofía y sincronizado con `origin/Sofia`. Ese es el HEAD final
  probado; el agente no ejecutó el commit ni el push.
- Se verificaron ruta de trabajo, rama, commit y estado del árbol antes de editar.
- Git ya marcaba numerosos archivos modificados. El diff inicial con
  `--ignore-space-at-eol` no mostraba diferencias de contenido. Se conservaron
  los archivos y modificaciones previas fuera de los cambios funcionales.
- El agente no realizó reset, limpieza, merge, rebase, commit ni push.
- No se encontró `AGENTS.md` en el repositorio ni en sus ascendentes.
- Se leyeron `EQUIPO.md`, todos los contratos, los dos informes históricos de
  integración y `docs/distribucion_cripta.pdf`.
- El PDF es una **distribución del trabajo**, no el enunciado completo. Menciona
  tablas hash, contradiciendo el acuerdo posterior del equipo y la instrucción
  de esta revisión. Se aplicó el acuerdo vigente: sin índices hash en el juego.
- La usuaria confirmó que solo está disponible esta documentación. No hay
  catálogo real, paquete de cripta ni especificación completa de formatos.
- Python usado: **3.14.4**. Dependencias instaladas desde `requirements.txt`:
  pytest y requests, en `/tmp/opencode/juegocripta-venv`.
- Suite inicial: **295 aprobadas**. Reproducciones independientes: dos derrotas
  del mismo enemigo; vida de 10 a 7 por un efecto cancelado; vida 0 con
  `partida_activa=True` tras veneno letal.

### Clasificación de hallazgos

**Errores confirmados:** muertes duplicadas, objetivos inválidos, efectos
cancelados que seguían dañando, muerte por veneno sin cierre, movimiento a
destino ausente, reloj reiniciado al iniciar, agenda vaciada sin límite,
costos arbitrarios, daño sin la variación aleatoria del PDF, dict en los
índices de escritura, set/bisect en caché y precarga.

**Integración incompleta:** ejecución/reprogramación de enemigos, registro de
rastros, transacciones del motor, controlador, servicios y consola.

**Decisiones ausentes:** fórmula y redondeo de velocidad; frecuencia de pulsos;
modificadores; ficha/categoría/ranuras del equipo; irreversibilidad; esquema de
arranque; victoria y puntaje; formato completo de guardado y registro/replay.

## 3. Etapas ejecutadas

1. Se corrigieron las validaciones, la muerte y la agenda; se añadieron deltas
   reversibles sobre el historial de Joshua.
2. Se conectaron costos base, disponibilidad, enemigos activos, movimiento,
   rastro local, efectos con tiempos explícitos, puertas y rearme de trampas.
   Verificación intermedia: **175 pruebas aprobadas** de lógica/integración/precarga.
3. Se conectaron servicios, controlador, consola y escenario sintético; se
   revisó y reconstruyó el formato binario v1. Verificación: **344 aprobadas**,
   incluyendo el arranque real por subproceso.
4. Se añadieron controles y regresiones de identidad, empates posteriores a la
   decisión, errores transaccionales e IDs de actores. Resultado final: **349**.

## 4. Trazabilidad de cambios y pruebas

Las pruebas que empiezan por `test_` se encuentran en
`tests/test_integracion_sofia.py` salvo donde se indica otro archivo.

| Archivo / método | Problema | Cambio | Prueba |
| --- | --- | --- | --- |
| `logica/motor_juego.py::_validar` | Ataques fuera de contexto o sobre objetivos inválidos | Valida partida, vida, disponibilidad, identidad y ubicación | `test_ataques_invalidos_no_mutan`, `test_objetivo_debe_ser_enemigo_vivo_local` |
| `logica/reglas_combate.py::procesar_muerte` | Contabilidad repetida; caminos de muerte diferentes | Marca idempotente, cancelación, desactivación y fin comunes | `test_muerte_unica_cancelacion_y_deshacer_repite_azar`, `test_veneno_letal_termina_y_deshace_todo_el_intervalo` |
| `logica/reglas_combate.py::atacar` | Omitía el azar documentado | `max(1, ataque + randint(0,4) - defensa)`, usando el azar de la partida | `tests/test_logica/test_reglas_combate.py::TestReglasCombate::test_atacar_reduce_vida` |
| `logica/acciones.py`, `MotorJuego.ejecutar_accion` | Costos de 1 y coordinación ausente | Costo base una vez; un intervalo por acción y sus eventos | `test_recoger_soltar_costos_cursor_y_reversion` |
| `MotorJuego.avanzar_hasta_decision` | Consumía toda la agenda | Se detiene en el evento de disponibilidad; conserva empates posteriores y eventos futuros | `test_duracion_temporal_pulsos_y_empate_siguiente_decision`, `test_empate_posterior_a_decision_se_conserva_para_siguiente_accion` |
| `logica/agenda_eventos.py`, `estructuras/monticulo_minimo.py` | Acceso al arreglo privado, IDs ambiguos, tiempos negativos | Recorrido público, generación secuencial, validación e inversas por evento | `test_agenda_reprogramacion_negativa_y_ids_duplicados_no_mutan`, `docs/diagnostico_steve.py::test_muerte_cancela_solo_eventos_del_actor` |
| `MotorJuego._aplicar_accion` | Perdía ubicación ante destino ausente | Valida antes de mover; registra sala, rastros, visitas y estadísticas | `test_movimiento_rechazado_conserva_ubicacion`, `test_movimiento_rastros_visitas_y_eventos_se_revierten_juntos` |
| `MotorJuego.activar_enemigo`, `_turno_enemigo` | IA no ejecutada por el motor | Programa actores activos, ejecuta y reprograma vivos; mantiene listas de salas | `test_enemigo_actua_y_guardian_permanece_en_sala`, `test_movimiento_rastros_visitas_y_eventos_se_revierten_juntos` |
| `logica/mapa_cripta.py`, `registro_rastro.py`, `comportamiento_enemigos.py` | Búsquedas globales por vecino; rastros futuros aceptados | Referencias de puerta a sala, rastro en sala y antigüedad `0 <= edad < 400` | `test_rastreador_solo_vecinos_accesibles_frescos_con_costo_local`, `test_rastreador_descarta_exactamente_400_y_prefiere_el_mas_reciente` |
| `logica/gestor_efectos.py` | Cancelados/reemplazados dañaban; duración contaba pulsos | Identidad exacta, vencimiento temporal, pulsos absolutos explícitos, valores/objetivos válidos | `test_evento_cancelado_o_reemplazado_no_daña`, `test_regeneracion_no_revive_y_evento_repetido_no_repite_pulso`, `test_no_se_acepta_efecto_sobre_actor_ajeno` |
| `MotorJuego._despachar`, `activar_trampa` | Faltaban puerta y trampa | Cierre, daño explícito, rearme y muerte compartida | `test_abrir_cierre_automatico_y_reversion`, `test_trampa_evento_rearme_y_muerte_compartida` |
| `logica/cambios.py`, `mutaciones.py`, `historial_reversible.py` | Descripciones confundidas con cambios; sin inversión de eventos | Deltas de atributo, dato, lista, agenda y azar; aborto del intervalo | `test_error_en_evento_revierte_dano_previo_agenda_y_secuencias`, `test_historial_rechaza_notificaciones_como_cambios` |
| `MotorJuego` + `ServicioInventario` existente | Recoger/soltar desconectados | Reutiliza servicio, retiros, nodos y cursor existentes | `test_recoger_soltar_costos_cursor_y_reversion` y suites anteriores de inventario |
| `logica/cache_catalogo.py`, `service/planificador_precarga.py` | set/bisect e inspección privada del mapa | Arreglos, búsqueda binaria manual y recorrido público | Suites de caché/precarga y `test_adaptacion_compartida.py` |
| `datos/guardado_binario.py` | Índices dict, versión no validada, truncamiento, lectura completa para una sala | Pares de offsets, límites, acceso por seek y escritura atómica; conserva v1 | `tests/test_flujo_sofia.py::test_binario_corrupto_no_lanza_error_de_struct`, `test_guardado_fallido_conserva_archivo_anterior` y suite de guardado |
| `service/partida_service.py`, `datos/decodificador_datos.py` | No reconstruía entidades ni referencias | Reconstrucción v1 para inspección con limitaciones explícitas | `tests/test_flujo_sofia.py::test_guardado_v1_reconstruye_referencias_y_reloj_sin_simular_datos_ausentes` |
| `controller/controlador_juego.py`, `service/juego_service.py`, `vista/vista_consola.py`, `main.py` | Arranque/flujo vacíos | Traducción de comandos, servicio, bitácora real y `--demo` | `tests/test_flujo_sofia.py::test_controlador_servicios_vista_y_motor_hasta_terminacion`, `test_arranque_real_demo_por_subproceso` |

## 5. Métodos antes incompletos

Implementados en el alcance verificable:

- `MotorJuego.avanzar_hasta_decision`: antes recorría sin límite; ahora procesa
  despachadores hasta disponibilidad/muerte, dentro de la transacción.
- `JuegoService.ejecutar_accion` y `iniciar_partida(cripta_id, estado=None)`:
  coordinación real cuando recibe un estado construido.
- `ControladorJuego.iniciar(estado=None)`, `procesar_comando`, `guardar`, `cargar`:
  bucle, comandos y coordinación. `cargar` rechaza v1 como continuación sin
  reemplazar la partida actual.
- `PartidaService.guardar`, `cargar`: exportación y reconstrucción v1.
- `VistaConsola.mostrar_estado`, `leer_comando`: presentación y entrada, incluido EOF.

`ServicioInventario.equipar/usar` siguen sin implementar sus reglas: el motor
rechaza esas acciones sin mutar. No se sustituyeron sus pendientes por éxitos
ficticios. Registro, replay y puntajes siguen pendientes de sus contratos de datos.

### Interpretación de TODO/pass/NotImplementedError

- Pendientes reales: `ServicioInventario.equipar/usar`, `RegistroPartida.crear/anexar_accion`,
  `RepositorioPuntajes.registrar_resultado/listar`, `EjecutorReplay.reproducir`,
  URL real en configuración y modo benchmark en `main.py`.
- Usos legítimos: cuerpo de `CriptaAPIError`; manejo de excepciones del almacén
  y repositorio de catálogo; `MotorFalso.iniciar`; clase auxiliar de estrés.
- Los `...` de contratos abstractos son interfaces, no errores de implementación.
- El TODO de acciones se resolvió usando el DTO `Accion(tipo=...)` ya compartido.

## 6. Contratos y consumidores

| Contrato | Cambio | Consumidores revisados/actualizados |
| --- | --- | --- |
| `ResultadoAccion` | Añade `notificaciones` al final; `cambios` reserva objetos reversibles. Conserva los cuatro argumentos posicionales anteriores. | Motor, servicio de inventario existente, controlador, stub y pruebas |
| `MotorJuegoContrato` | Documenta que `ejecutar_accion` ya avanza y registra; `iniciar` no reinicia reloj/azar. `avanzar_hasta_decision` devuelve notificaciones. | JuegoService, controlador, MotorFalso y pruebas. Replay aún no tiene consumidor funcional. |
| `AgendaEventosContrato` | Añade consulta, recorrido y cancelación por actor; cancelar devuelve el retirado o None. | Motor, efectos, combate y deltas de agenda |
| `CambioReversible` | Conserva `deshacer(estado)`; la transacción verifica el tipo. | Nuevos deltas y cambios de inventario existentes |
| `MapaCripta` / DTO de sala-puerta | `vincular_salidas`, vecinos admite Sala o ID, referencias a destinos y rastro por sala. | IA, motor, precarga y reconstrucción v1 |
| `GestorEfectos.aplicar` | `tiempos_pulsos=()` opcional, tiempos absolutos explícitos; `duracion` temporal. Requiere actor vivo de la partida y valor positivo. | Pruebas y futuros consumidores de fichas; todavía no hay catálogo de uso conectado. |
| `ReglasCombate.atacar` | Estado opcional para registrar deltas; azar requerido. | Motor y pruebas de combate |
| `EstadoPartida` | Historial/inventario/rastro, inicio/disponibilidad y limitaciones de carga. | Motor, servicios, controlador y demostración |
| `JuegoService.iniciar_partida` / `ControladorJuego.iniciar` | Estado opcional adicional para inyección de DTO real. Ausencia de esquema reportada explícitamente. | `main.py --demo`, pruebas de flujo |
| Guardado | Mantiene MAGIC, cabecera, registros, índice y versión 1. La salida dict sigue siendo intercambio de datos, no índice del motor. | PartidaService, pruebas originales y nuevas |

El controlador **no vuelve a registrar** `resultado.cambios` ni vuelve a sumar
`resultado.costo`: la transacción es responsabilidad del motor.

## 7. Estructuras, complejidad y reversión

- El montículo sigue siendo manual. Insertar/extraer en el montículo cuesta
  O(log E); la agenda valida IDs/prioridades linealmente, por lo que programar
  a través de ella es O(E), no O(log E). Buscar/cancelar por ID es O(E).
  Cancelar K eventos de un actor cuesta O(E + K·E) con el diseño actual.
- El recorrido público toma referencias en una tupla temporal; no copia el
  estado de los actores ni sirve de instantánea para deshacer.
- El mapa conserva un arreglo: buscar por ID es O(S). Vincular puertas cuesta
  O(P·S), una preparación fuera de cada decisión. Tras vincular, la IA recibe
  la sala directamente y revisa sus d puertas y rastros en O(d), sin búsquedas
  globales por vecino. Si se cambia la topología directamente después del
  inicio, debe invocarse `vincular_salidas()` de nuevo.
- El RegistroRastro sin mapa mantiene su API anterior por ID y búsqueda O(S).
  La simulación inicializa la variante ligada al mapa y usa referencias de Sala.
- Caché: búsqueda binaria propia O(log N); inserción en arreglo O(N); búsqueda
  de una fijación anterior a la carga O(F). Precarga usa arreglos sin set;
  la pertenencia a visitados es lineal. No se atribuyen costos de hash.
- Inventario, lista doble, historial, ordenamiento y bitácora reutilizan las
  implementaciones del equipo. La bitácora conserva su cola circular de 20.
- Antes de modificar se conservan valores/referencias anteriores. La agenda
  registra eventos insertados/retirados; no clona el montículo para deshacer.
- Al revertir se recorre la lista doble en orden inverso: vida, muerte,
  estadísticas, ubicación, visitas, rastros, reloj, agenda, efectos y azar.
  Se conserva el estado del generador con getstate/setstate; no una partida completa.
- La agenda es la autoridad para generar secuencias e IDs. El campo histórico
  `EstadoPartida.secuencia` se actualiza desde la programación del motor; no
  debe utilizarse para generar eventos por fuera de `AgendaEventos.crear_evento`.
- El límite existente de cinco transacciones sigue vigente. Un intento fallido
  se aborta sin consumir un lugar. Los diccionarios de notificaciones no entran
  en el historial.

## 8. Persistencia: alcance demostrado y bloqueo

Se conserva la versión 1 documentada y probada, sin inventar una versión nueva.
Ahora se leen entidades y referencias compartidas: jugador y enemigos apuntan
a las mismas salas que el mapa; las puertas apuntan a sus destinos existentes.
El reloj almacenado se conserva. Los muertos reconstruidos quedan identificados.

Sin embargo, **v1 no guarda inventario/cursor, agenda/secuencias, efectos,
historial, azar actual, visitas/rastros, estadísticas, victoria ni todos los
atributos de puertas**. No existe una reconstrucción fiel de información que
no se escribió. `test_formato_v1_no_puede_preservar_azar_actual` demuestra que
dos estados con distintos generadores producen los mismos bytes v1.

Por eso `PartidaService.cargar` devuelve un estado de inspección con
`reanudable=False` y `limitaciones_carga`; el motor rechaza continuarlo antes
de reemplazar el estado actual. GUARDAR informa que exporta una instantánea v1.
La reanudación del **mismo EstadoPartida en memoria** sí conserva reloj,
historial, referencias, eventos y azar; no equivale a guardar/cargar de disco.

## 9. Pruebas antiguas actualizadas y motivos

- Ataque del motor y diagnóstico de cancelación: ahora construyen una sala
  compartida y un mapa real. Antes atacaban actores sin ubicación, contradiciendo
  la validación solicitada. Se conservan sus comprobaciones de daño/cancelación.
- El evento ajeno del diagnóstico pasa de tiempo 2 a 200: está después del costo
  de ataque 100, de modo que puede verificarse que se conserva en la agenda.
- Prueba de combate y expectativa de vida del motor: daño 18 y vida 32 con
  semilla 0, conforme a la fórmula explícita del PDF; antes esperaban 15 y 35.
- Aplicación de efecto: incorpora objetivo vivo de la partida y `valor`, que
  es el campo consumido por el módulo. Antes no tenía objetivo y usaba `daño`.
- Precarga: usa MapaCripta real y arreglos para su preparación, en lugar de
  simular el almacenamiento privado con dict/set. Mantiene sus expectativas.

No se eliminaron pruebas, no se añadieron xfail ni skips y no se debilitó
ninguna expectativa para ocultar errores.

## 10. Comandos y resultados reales

Desde la raíz, con el entorno ya creado en esta revisión:

```bash
/tmp/opencode/juegocripta-venv/bin/python -m pip install -r requirements.txt
/tmp/opencode/juegocripta-venv/bin/python -m pytest -q
/tmp/opencode/juegocripta-venv/bin/python main.py --demo --semilla 7
```

En una instalación con Python y venv completos:

```bash
python -m venv .venv
# Linux:
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python main.py --demo --semilla 7
```

En PowerShell se sustituye `.venv/bin/python` por `.\.venv\Scripts\python.exe`.
En este entorno faltaban pip/ensurepip; se instaló pip desde el bootstrap
oficial de PyPA dentro del entorno externo, sin cambiar requirements.txt.

Partida mínima reproducible ejecutada:

```bash
/tmp/opencode/juegocripta-venv/bin/python main.py --demo --semilla 7 <<'EOF'
recoger moneda
soltar
mover norte
esperar
EOF
```

Resultado: tiempos **25, 50, 150 y 200**; vida **12 → 4 → 0**; cuatro acciones;
mensaje **Partida terminada**. La última espera finaliza antes de su próxima
disponibilidad porque el jugador muere en el evento enemigo del tiempo 200.

| Verificación | Resultado |
| --- | --- |
| Suite inicial | 295 aprobadas |
| Suite final | 349 aprobadas; 0 fallidas; 0 omitidas |
| Nuevas regresiones/integración | 54 casos adicionales |
| Arranque real de `main.py --demo` | Ejecutado manualmente y desde pytest; termina por muerte |
| Reproducciones históricas | Cubiertas por la suite normal y actualizadas donde contradicen requisitos |
| HTTP real/API/catálogo oficial | No ejecutado: URL y paquete real ausentes; tests HTTP usan respuestas simuladas |
| Continuación determinista desde disco | No implementada ni presentada como aprobada; v1 pierde información |
| Revisión de diff | Contenido revisado con `--ignore-space-at-eol`; sin operaciones de Git destructivas |

Git reconoce como cambios previos muchos finales CRLF. El chequeo global de
espacios, incluso admitiendo CRLF, señala espacios preexistentes del PDF,
`estructuras/lista_doble.py` y `logica/inventario.py`. Esos archivos ajenos
no se normalizaron para ocultar el estado inicial.

## 11. Pendientes concretos de coordinación

1. **Enunciado completo:** confirmar restricciones académicas que el PDF de
   reparto no enumera. La exclusión de índices hash sí fue instruida expresamente.
2. **Velocidad:** fórmula, unidades, redondeo, límites y efecto sobre eventos
   ya programados. Actualmente se aplican los costos base disponibles.
3. **Activación de enemigos:** radio/momento de activación inicial y al explorar.
   Se respetan los flags `activo` recibidos y existe activación explícita.
4. **Efectos:** fichas reales, frecuencias, pulso inicial/final, apilamiento,
   reemplazo entre tipos, velocidad, antorcha y otros modificadores. Veneno y
   regeneración aceptan tiempos explícitos estrictamente anteriores al vencimiento;
   no se inventa su periodicidad ni una fórmula de velocidad.
5. **Trampas y llaves:** daño/tipo, condición de disparo al entrar, efectos y
   forma de identificar/consumir llaves. El despachador acepta daño explícito y
   rearma; no hay disparo automático por entrar sin conocer la ficha. ABRIR
   funciona para puertas sin llave y con plazo de cierre explícito.
6. **Inventario avanzado:** esquema de fichas, categorías, ranuras, consumos y
   modificadores para usar/equipar. Recoger/soltar normales están conectados.
7. **Pergaminos/irreversibles:** clasificación por ficha y cómo conservar sus
   movimientos al deshacer acciones anteriores. El parámetro `reversible=False`
   existente del servicio se conserva; no hay clasificación automática. El
   motor no habilita RETROCEDER como acción gratuita sin pergamino. Las pruebas
   de reversión usan directamente el historial, no una regla de juego inventada.
8. **Guardado completo:** acordar versión y codificación de relaciones entre
   nodos, cambios, actores, eventos, efectos e inventario, y del estado del azar.
9. **Arranque real:** esquema de generales/páginas, jugador inicial, capacidad,
   versiones y datos de una cripta. `--demo` verifica coordinación, no ese contrato.
10. **Victoria, registro, replay, puntajes y benchmarks:** condiciones/fórmula,
    campos y formatos externos. Sus pendientes no quedan satisfechos por la demo.

## 12. Explicación para defender el bloque de Sofía

- **Una muerte tiene un único camino.** Ataque, veneno y trampa llaman al mismo
  método. La marca de muerte impide contar otra vez y también se puede deshacer.
- **El reloj salta de evento en evento.** La acción agenda cuándo puede decidir
  el jugador otra vez. El montículo selecciona menor tiempo y luego secuencia;
  al llegar a esa decisión se detiene, dejando el futuro pendiente.
- **Validar va antes de cambiar.** Si falta una puerta, un destino o un enemigo
  vivo válido, no se toca la partida ni se guarda una acción en el historial.
- **Deshacer guarda diferencias.** Se conserva la vida anterior o el evento
  retirado, no una copia del mundo. La lista doble invierte los cambios desde
  el último hasta el primero y recupera también el azar.
- **Rastrear es mirar alrededor.** Cada puerta ya referencia a su sala destino
  y cada sala guarda su rastro. Así el rastreador no busca por toda la cripta.
- **Un efecto cancelado pierde su identidad activa.** Aunque quede una referencia
  vieja a su evento, no puede volver a dañar. Duración y número de pulsos ya no
  se confunden.
- **Una prueba verde no prueba todo el juego.** Hay suite completa y flujo real
  hasta muerte, pero se documenta exactamente qué depende todavía del enunciado
  y por qué guardar solo una semilla no conserva el azar actual.
