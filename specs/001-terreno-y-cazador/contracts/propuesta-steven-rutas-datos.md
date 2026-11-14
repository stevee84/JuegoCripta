# Respuesta parcial con Steven: datos ponderados y rutas para «ir a»

**Estado**: G1/G2 y la vista conocida están integradas en `integracion-parte2@d86819d`. Steven aceptó la firma y representación de §4.1; su entrega publica costo/rango estrictos, simetría entre sentidos existentes, persistencia v10 de costo/rango y la vista de conocimiento de 003. El equipo confirmó que una salida sin inversa es válida y enmendó FR-002 antes del código. La línea de tiempo completa también está integrada, pero la persistencia conjunta de mapa conocido y línea permanece abierta. Este documento no modifica ni sustituye specs 002/003, clases de Steven ni un contrato de Joshua.

**Proponentes/consumidores**: Sofía ofrece cálculo de rutas; Steven adapta los datos, construye la vista del mapa conocido y asume la persistencia de costo/rango/mapa conocido en coordinación con Joshua. Steven solicitó expresamente que Sofía implemente el índice por ID de `MapaCripta`, componente de Sofía, conservando firmas, orden e identidad. Ese acuerdo específico no autoriza a Sofía a editar clases de Steven ni fija quién modifica DTO, inicialización u otros archivos compartidos.

**Evidencia integrada verificada el 2026-11-09**:

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

## 2. Estado del código revisado

La entrega integrada constituye implementación local de G2:

- `DecodificadorDatos.convertir_sala()` lee/valida `costo`; `Puerta` lo materializa.
- `_adaptar_contenido_externo()` valida/materializa `rango` solo para `comportamiento == "cazador"`.
- `InicializadorPartida._construir()` valida multiplicidad y simetría después de `mapa.vincular_salidas()` y antes de 002.
- `MapaCripta` publica índice por ID; la vista de cazador se implementa en 001 sin requerir la vista conocida de 003.
- `GuardadoBinario.VERSION` es **10** e incluye costo/rango. Persistir mapa conocido y línea de tiempo completa continúa coordinado y pendiente.
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

Steven integró persistencia v10 de costo/rango en `5000d1f`. Mapa conocido y línea de tiempo ya están disponibles como estado, pero su persistencia conjunta todavía requiere la entrega coordinada con Joshua; G2 no cierra por sí sola T006/T055.

**Estado de M3**: `5000d1f` materializa v10 para costo/rango y mantiene incompatibilidad explícita con v9. Ampliar ese formato con mapa conocido y línea de tiempo completa sigue pendiente de confirmación/entrega conjunta; T041/T055 no se cierran con la parte ya integrada.

## 5. Puntos todavía no confirmados por ambos

- mecanismo, claves, invalidación y propietario de reutilización para «ir a»;
- compatibilidad y entrega conjunta de mapa conocido y línea de tiempo completa.

## 6. Consumidores y compatibilidad

- **001**: cazador, movimiento ponderado y benchmarks de rutas.
- **002**: conserva su recorrido de resolubilidad; los costos no cambian alcanzabilidad.
- **003**: consume la vista restringida construida por Steven y vuelve a pedir un paso con conocimiento vigente.
- **004/guardado**: persiste estado canónico según el acuerdo futuro; nunca resultados ni cachés de ruta.

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
- [ ] 003 y 001 demuestran equivalencia y miden el límite de 5 ms con costo completo.
- [ ] Steven y Joshua completan mapa conocido/línea de tiempo y su persistencia conjunta; costo/rango v10 ya están integrados en `5000d1f`.
- [x] T004/T052/T053 verifican vista conocida, independencia, recálculo por paso y casos terminales; la persistencia y la medición conjunta conservan sus tareas abiertas.
