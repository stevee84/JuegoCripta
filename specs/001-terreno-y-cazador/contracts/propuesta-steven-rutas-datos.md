# Respuesta parcial con Steven: datos ponderados y rutas para «ir a»

**Estado**: G1/G2, la vista conocida y la persistencia conjunta están integradas. Steven aceptó la firma y representación de §4.1; `5000d1f` publicó costo/rango estrictos, simetría entre sentidos existentes y su persistencia v10, mientras `d1ad048` entregó el formato conjunto **v11** con mapa conocido y línea de tiempo. El equipo confirmó que una salida sin inversa es válida y enmendó FR-002 antes del código. T006/T041/T055 quedaron verificadas el 2026-11-15 sin modificar clases de Steven/Joshua ni otras especificaciones.

**Proponentes/consumidores**: Sofía ofrece cálculo de rutas; Steven adapta los datos, construye la vista del mapa conocido y asume la persistencia de costo/rango/mapa conocido en coordinación con Joshua. Steven solicitó expresamente que Sofía implemente el índice por ID de `MapaCripta`, componente de Sofía, conservando firmas, orden e identidad. Ese acuerdo específico no autoriza a Sofía a editar clases de Steven ni fija quién modifica DTO, inicialización u otros archivos compartidos.

**Evidencia histórica integrada verificada el 2026-11-09**:

- checkout local `Sofia`: `5000d1fe8af268987206827e4c524c05bd599357` (`Steve@5000d1f`);
- `dto/sala.py` publica `Puerta.costo` con default 100; `dto/actor.py` publica `Enemigo.rango`;
- `DecodificadorDatos` valida costo/rango estrictos y `InicializadorPartida` compara costos por `(origen, destino)`, acepta sentidos únicos y rechaza contradicciones entre sentidos existentes;
- `GuardadoBinario.VERSION = 10` persiste costo/rango. La validación `1204 passed, 4 subtests passed` fue comunicada por Sofía para esa integración y no se presenta aquí como ejecución de este bloque;
- `main.py --bench` registra el proveedor de mapa de T049, pero aún no los proveedores de rutas/ciclo de 001.
- `1bc5c6220a4a12f471f4e118ffdf4bf7117f2467` publica `logica/mapa_conocido.py`, `logica/viaje.py` y sus pruebas; `7a36ebe18c7c30f0f4364a2fa6f119e60285396f` completa las condiciones de parada/antorcha. Ambos son ancestros de `integracion-parte2@d86819d`.

## 1. Objetivo

Acordar dos fronteras:

1. entregar al modelo costos y rangos ya validados conforme a `FR-001`, `FR-002`, `FR-009` y `FR-011` de 001;
2. permitir que «ir a» use el cálculo ponderado de 001 sin acceder al esqueleto completo ni al estado real de puertas que el jugador desconoce.

## 2. Estado del código revisado en 2026-11-09

La entrega integrada constituye implementación local de G2:

- `DecodificadorDatos.convertir_sala()` lee/valida `costo`; `Puerta` lo materializa.
- `_adaptar_contenido_externo()` valida/materializa `rango` solo para `comportamiento == "cazador"`.
- `InicializadorPartida._construir()` valida multiplicidad y simetría después de `mapa.vincular_salidas()` y antes de 002.
- `MapaCripta` publica índice por ID; la vista de cazador se implementa en 001 sin requerir la vista conocida de 003.
- En esa revisión `GuardadoBinario.VERSION` era **10** e incluía costo/rango; mapa conocido y línea de tiempo todavía estaban pendientes. La entrega posterior vigente se registra en §4.3.
- `verificador_resolubilidad.verificar()` usa destino, apertura y llaves, no pesos. Incorporar costos no cambia su alcanzabilidad.

Steven solicitó a Sofía resolver el cuello de botella lineal mediante el índice de `MapaCripta`. No se encontró un acuerdo explícito contradictorio: la anotación previa de que era un componente compartido exigía identificar consumidores y acordar el cambio. El plan enumera esos consumidores y T007–T009/T072–T076 conservan contrato y aportan pruebas/mediciones. La solicitud no resuelve las asignaciones todavía abiertas de DTO, inicialización, vista conocida o persistencia.

## 3. Acuerdos confirmados

### 3.1 Validación de costo y rango

Steven implementará la validación estricta en su frontera de datos:

- cada costo presente debe cumplir `type(costo) is int` y `costo >= 1`;
- el único valor predeterminado es 100 y se aplica exclusivamente cuando el campo `costo` está ausente;
- un campo presente con booleano, cadena, fracción, cero o negativo se rechaza, sin conversión ni sustitución por 100;
- una ficha con `comportamiento == "cazador"` exige `type(rango) is int` y `rango >= 0`; ausencia, booleano, cadena, fracción o negativo se rechazan.

Sofía consume esos valores ya validados y conserva defensas de contrato en sus límites públicos; no vuelve a reinterpretar datos inválidos.

### 3.2 Simetría, identificación y resolubilidad

La validación de simetría se ubicará después de `mapa.vincular_salidas()`, cuando el esqueleto completo ya está reunido. Los sentidos se identifican por `(origen_id, destino_id)`, no por posición ni dirección textual. Si hay varias salidas entre el mismo par, la validación debe detectar la ambigüedad en vez de emparejarlas arbitrariamente. Una contradicción de costos rechaza la cripta de forma descriptiva antes de que 002 o el juego la consuman.

El equipo acordó aceptar una salida sin sentido inverso. La validación compara costos únicamente cuando existen ambos sentidos; no rechaza la ausencia ni crea una conexión implícita. Esta decisión quedó confirmada y registrada en FR-002 antes de implementar rutas/cazador.

**A1 del PDF oficial — verificación del 2026-11-09 (hallazgo del análisis cruzado de Joshua sobre `Sofia@e89574de14df8a9e672ef0a62590630d37242f05`)**. El texto oficial fue extraído de `Cripta - Parte II.pdf`: §3.1 dice «Cada salida puede declarar un campo costo, entero mayor o igual que 1. Si no lo declara, su costo es 100. El costo es el mismo en ambos sentidos» y §4.1 declara `costo` por sentido de la salida. Casos:

1. **Ambos sentidos omiten `costo`**: resuelto por §3.1 de forma expresa — 100 y 100; coincide con AC-001.
2. **Un sentido declara 100 y el otro omite**: 100 frente a 100; los efectos coinciden y no hay contradicción, AC-020 no aplica.
3. **Un sentido declara un costo distinto de 100 y el otro omite** (decisión normativa del equipo, elegida en la consulta del 2026-11-09): se aplica el default 100 al lado omitido y, como el efectivo 100 difiere del valor declarado en el otro sentido, AC-020 de 001 rechaza la salida de forma descriptiva identificando ambos valores; no existe herencia del costo del lado declarado.
4. **Una salida carece de sentido inverso** (decisión normativa confirmada): se acepta como conexión dirigida válida. No se rechaza ni se inventa el sentido ausente; si ambos sentidos existen, sí deben compartir costo efectivo.

Estas aclaraciones están integradas en la validación de Steven y en FR-002; no existe herencia de costo entre sentidos.

Los costos ponderan movimiento y rutas, pero no cambian qué salas son alcanzables para la verificación de resolubilidad. El recorrido de 002 conserva sus reglas de puertas y llaves.

### 3.3 Capacidad mínima de la vista

Steven acepta las operaciones conceptuales:

```text
contiene_sala(sala_id)
salidas_transitables(sala_id)
```

`salidas_transitables` entrega destino y costo de las salidas permitidas por la vista. Esto confirma la capacidad, no una firma Python, protocolo, clase ni tipo de retorno definitivos.

### 3.4 Vista de «ir a» desde conocimiento del jugador

Steven publicó la vista y su prueba de independencia frente al estado real oculto. La vista:

- contiene únicamente salas exploradas;
- enumera salidas solo desde salas exploradas;
- permite rutas únicamente entre salas exploradas mediante puertas recordadas abiertas;
- usa el conocimiento recordado, nunca el estado real oculto ni el esqueleto completo.

T052 construye dos `EstadoPartida`/`MapaCripta` reales distintos con el mismo mapa conocido, prohíbe cualquier consulta posterior al mapa real y exige el mismo paso de «ir a». También cubre recálculo al cambiar origen, destino y conocimiento. La ejecución focalizada del 2026-11-13 terminó en **10 passed in 0.29s**, sin omisiones.

### 3.5 Consulta por paso y casos terminales

Steven acepta que:

- cada paso de «ir a» vuelve a calcularse con origen, destino y conocimiento vigentes; no se conserva una secuencia como compromiso futuro;
- origen igual a destino produce costo total 0 y ningún paso;
- ausencia de ruta es un resultado explícito, distinguible del caso anterior;
- el buscador devuelve semánticamente un paso, no decide `ATACAR` ni `ESPERAR`.

La semántica y la representación están implementadas por `proximo_paso(...) -> ResultadoRuta` en `21c234248d4f9b7bcdeb3c9c299e40498a2d131a`; T053 verificó su consumo desde `VistaMapaConocido` sin reglas de ataque/espera.

## 4. Decisiones de integración todavía abiertas

### 4.1 Firma y representación aceptadas (G1)

- Firma aceptada por Steven: `proximo_paso(vista, origen_id, objetivo_id, limite_costo=None) -> ResultadoRuta`.
- `ResultadoRuta` es inmutable y publica `alcanzable`, `costo_total`, `primera_vecina_id` y `costo_primera_salida`, además de instrumentación separada conforme al plan.
- Paso disponible: `alcanzable=True`, costo positivo, vecina y costo de primera salida presentes.
- Origen igual a objetivo: `alcanzable=True`, `costo_total=0` y ningún paso/costo de primera salida.
- Ausencia de ruta (incluido un límite insuficiente): `alcanzable=False` y ningún costo/paso.
- La búsqueda minimiza la suma de costos positivos y, entre rutas mínimas, elige la primera vecina de menor ID numérico.
- `limite_costo` es inclusivo; `None` significa sin límite. IDs y límite se validan estrictamente, sin conversiones.
- El buscador solo lee las capacidades `contiene_sala(id)` y `salidas_transitables(id)` de la vista. No decide `ATACAR`/`ESPERAR`, no descarga contenido y no muta el juego.
- Sofía implementa `logica/rutas_ponderadas.py`, sus pruebas y la vista del cazador. DTO, decodificación, inicialización y guardado de Steven no se modifican.

La vista conocida de 003 está disponible en `1bc5c62` y consume este mismo protocolo. La vista de esqueleto completo del cazador permanece separada en 001.

### 4.2 Estrategia inicial y reutilización

La primera integración usa cálculo individual desde cero. En colaboración con 003 se medirá el costo completo de cada decisión de «ir a» frente a su límite de **5 ms**, incluyendo toda preparación auxiliar requerida por la consulta.

La reutilización de cálculos permanece como alternativa, no como requisito ni optimización asumida. Solo podrá habilitarse si:

1. demuestra equivalencia observable con el cálculo individual desde cero para origen, destino y conocimiento vigentes;
2. mide su costo completo, incluida construcción, consulta, invalidación y limpieza;
3. respeta la independencia del mapa conocido y el límite aplicable.

El mecanismo y propietario concretos de esa reutilización siguen sin acuerdo.

### 4.3 Persistencia coordinada

Steven integró persistencia v10 de costo/rango en `5000d1f`. **Entrega coordinada completada el 2026-11-14** en `d1ad04867c94a2637024089c1625edb9cb296807` (rama `integracion-parte2`), que cierra T006.

**Versión real: 11.** `GuardadoBinario.VERSION = 11`.

| Versión | Campos que añade | Dónde |
|---|---|---|
| 10 | `costo` de cada puerta y `rango` de cada enemigo | registros de sala, dentro de `_escribir_sala` |
| 11 | la línea de tiempo como bloque opaco: longitud (`<I`) + bytes | al final de los extras |

**El mapa conocido no tiene sección propia.** `LineaTiempo.exportar_bytes` serializa el estado vivo
completo y `mapa_conocido` no figura en su lista `INFRAESTRUCTURA`, así que el conocimiento viaja
dentro de los bytes de la línea. Una sección aparte habría guardado lo mismo dos veces. Si el
archivo no trae línea —partida de prueba—, la sección se escribe con longitud 0 y
`RestauradorPartida._completar_v11` reconstruye el mínimo: la sala donde está el jugador, porque
una sala que se está pisando no puede estar desconocida para la vista ni para «ir a».

**Archivos reales**: `datos/guardado_binario.py` (formato), `service/juego_service.py` (al cargar,
el estado de la partida es el que devuelve `LineaTiempo.importar_bytes`, porque su cola apunta a
esos objetos) y `service/restaurador_partida.py` (reanudación sin línea). La sección va al final de
los extras y no después del índice de salas porque la cabecera exige que el índice termine justo
en el final del archivo, y ese chequeo es el que detecta un archivo recortado.

**Compatibilidad**: v9 y v10 se reportan incompatibles y no se cargan a medias (`cargar` devuelve
`None`; `JuegoService.cargar_partida` lanza `ValueError` con «incompatible» y conserva la partida
vigente). Comprobado para las dos versiones.

**Estado de M3**: la propuesta pedía **un solo v10** con las cuatro cosas. No salió así: fueron dos
subidas, porque v10 ya estaba publicada y en uso cuando llegó el contrato de la línea, y un archivo
v10 circulando no puede reinterpretarse en silencio (FR-018). El resultado observable es el que M3
pedía: una sola ida y vuelta devuelve costo, rango, mapa conocido y línea.

**Verificación (T041/T055)**: `tests/test_datos/test_guardado_terreno_cazador.py`, siete pruebas que
cubren las cuatro cosas en una ida y vuelta, que el costo no se rellena con un valor por defecto,
el paquete histórico en v9 y v10, los alias de sentidos cortos del paquete real y la ausencia de
resultados de ruta en el archivo. Esta última mira los bytes crudos y no el estado reconstruido,
porque `pickle` escribe los nombres de clase en claro: si algo retuviera un `ResultadoRuta`, la
vista conocida o el viaje, aparecería. Auditoría de Sofía del 2026-11-15: **7 passed in 0.63s**
en el archivo conjunto y **144 passed in 12.09s** en persistencia, restauración, línea e
integraciones relacionadas. Las identidades canónicas están cubiertas por las regresiones del
restaurador, reanudación y línea; no fue necesario añadir pruebas.

## 5. Puntos todavía no confirmados por ambos

- mecanismo, claves, invalidación y propietario de reutilización para «ir a». T066 decidió no crear
  caché: 003 no reutiliza nada y recalcula el paso cada vez (FR-014). Si una referencia futura exige
  retener estado, el mecanismo sigue sin acordarse.

## 6. Consumidores y compatibilidad

- **001**: cazador, movimiento ponderado y benchmarks de rutas.
- **002**: conserva su recorrido de resolubilidad; los costos no cambian alcanzabilidad.
- **003**: consume la vista restringida construida por Steven y vuelve a pedir un paso con conocimiento vigente.
- **004/guardado**: v11 persiste estado canónico y línea según el acuerdo entregado; nunca resultados ni cachés de ruta.

## 7. Criterios de cierre e integración

- [x] Steven acepta implementar validación estricta de costo/rango y el default solo por ausencia.
- [x] Se acuerda identificar sentidos por origen/destino, comparar costos y detectar ambigüedad entre salidas múltiples.
- [x] Steven acepta la capacidad `contiene_sala`/`salidas_transitables`.
- [x] Steven publica la vista del mapa conocido; T052 verifica su independencia con estados reales integrados.
- [x] Se acuerda que los costos no cambian la alcanzabilidad de 002.
- [x] Steven acepta recálculo por paso, origen=destino con costo 0 sin paso y ausencia de ruta distinguible.
- [x] Steven asume persistencia de costo/rango/mapa conocido coordinada con Joshua.
- [x] Ambos fijan firma Python y `ResultadoRuta` sin confundir «sin ruta» con «ya en destino».
- [x] Steven solicita a Sofía implementar el índice de `MapaCripta` conservando firmas, orden e identidad; el plan identifica sus consumidores reales.
- [x] Sofía recibe rutas/vista del cazador y se acepta una salida sin inversa; clases de Steven permanecen fuera de su asignación.
- [ ] 003 y 001 demuestran equivalencia y miden el límite de 5 ms con costo completo. **Mitad de
  003 hecha**: `ir_a_un_paso` mide 0,229 ms de mediana con las 49 salas de la cripta publicada más
  grande y 1,887 ms en una medición aislada, las dos por debajo de los 5 ms de §6.1, y la fila está
  en `main.py --bench` vía `benchmarks.integrante2.medir_paso_ir_a`. La equivalencia la cubre
  `SC-005` en `tests/test_logica/test_viaje.py`: dos estados reales distintos con el mismo mapa
  conocido producen el mismo viaje. La mitad de 001 está cubierta por T054/T066: medición propia en
  `benchmarks/terreno_cazador_integrante1.py`, equivalencia previa, 15/15 muestras `<5 ms` con el
  mapa conocido completo de `cripta-04` y decisión de conservar el recálculo sin caché. La
  referencia oficial de PR-001/T051 sigue pendiente.
- [x] Steven y Joshua completan mapa conocido/línea de tiempo y su persistencia conjunta: v11 en `d1ad048`, verificada en T041/T055. Ver §4.3.
- [x] T004/T052/T053 verifican vista conocida, independencia, recálculo por paso y casos terminales; T054/T066 cierran la medición conjunta y la decisión sin caché. T006/T041/T055 cierran la persistencia coordinada en 001.
