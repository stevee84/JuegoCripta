# Respuesta parcial con Steven: datos ponderados y rutas para «ir a»

**Estado**: ACUERDO PARCIAL ACTUALIZADO. Steven confirmó la semántica de validación, simetría, vista conocida, recálculo por paso y casos terminales; también solicitó a Sofía el índice de `MapaCripta`. Las firmas Python, la representación exacta y la asignación de los demás archivos compartidos siguen abiertas. Steven asume la persistencia de costo/rango/mapa conocido coordinada con Joshua, pero no hay formato o versión implementados comprobados. La verificación A1 del 2026-11-09 precisiona qué resuelve el PDF oficial §3.1/§4.1 sobre costos parciales y dejó registrada, sin resolución normativa, la política de salidas sin inversa; y una propuesta coordinada v10 quedó anotada como pendiente de confirmación conjunta (M3). Este documento no modifica ni sustituye specs 002/003, archivos de Steven ni un contrato de Joshua.

**Proponentes/consumidores**: Sofía ofrece cálculo de rutas; Steven adapta los datos, construye la vista del mapa conocido y asume la persistencia de costo/rango/mapa conocido en coordinación con Joshua. Steven solicitó expresamente que Sofía implemente el índice por ID de `MapaCripta`, componente de Sofía, conservando firmas, orden e identidad. Ese acuerdo específico no autoriza a Sofía a editar clases de Steven ni fija quién modifica DTO, inicialización u otros archivos compartidos.

**Evidencia consultada el 2026-11-08**:

- checkout local `Sofia`: `3df43c63c68a33f692148b737c12b0c0a4208569`, que contiene `Steve@757d747b461cdb755705ca5cdd90391090112782` mediante la integración de Joshua;
- en esa entrega `GuardadoBinario.VERSION = 9` y no están publicados 003 ni la implementación de costo/rango/mapa conocido;
- los puntos de §§3–4 siguientes son acuerdos comunicados por Steven, pendientes de implementación salvo evidencia posterior.

## 1. Objetivo

Acordar dos fronteras:

1. entregar al modelo costos y rangos ya validados conforme a `FR-001`, `FR-002`, `FR-009` y `FR-011` de 001;
2. permitir que «ir a» use el cálculo ponderado de 001 sin acceder al esqueleto completo ni al estado real de puertas que el jugador desconoce.

## 2. Estado del código revisado

La respuesta de Steven confirma responsabilidades, pero todavía no constituye implementación local ni publicada en el hash consultado:

- `DecodificadorDatos.convertir_sala()` adapta `salidas` del API y `puertas` del guardado, pero hoy no lee ni valida `costo` y `Puerta` no lo almacena.
- `DecodificadorDatos._adaptar_contenido_externo()` resuelve la ficha antes de crear cada enemigo; hoy toma `comportamiento`, pero no valida ni materializa `rango`. `convertir_contenido()` es el camino interno usado al reconstruir.
- `InicializadorPartida._construir()` reúne todas las páginas, rechaza IDs repetidos, llama a `mapa.vincular_salidas()` y luego recorre las puertas antes de invocar a 002. Ese recorrido es el punto existente propuesto para comprobar la simetría.
- `MapaCripta` aún no publica `contiene_sala` ni `salidas_transitables`; `obtener_sala()` y el enlace actual continúan usando la lista lineal.
- `GuardadoBinario.VERSION` es **9**. `_escribir_sala()` y `_leer_sala_datos()` no incluyen costo/rango y el lector exige versión exacta.
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

Ni el PDF oficial §3.1 ni la aclaración de `spec.md` obligan expresamente a rechazar **toda** salida que no tenga sentido inverso: hablan de costo igual en ambos sentidos y de costos contradictorios. Steven tampoco confirmó esa extensión. Hasta aclararla, una ausencia de inverso se registra como pregunta pendiente y no como rechazo acordado; no requiere cambiar `spec.md` en esta revisión.

**A1 del PDF oficial — verificación del 2026-11-09 (hallazgo del análisis cruzado de Joshua sobre `Sofia@e89574de14df8a9e672ef0a62590630d37242f05`)**. El texto oficial fue extraído de `Cripta - Parte II.pdf`: §3.1 dice «Cada salida puede declarar un campo costo, entero mayor o igual que 1. Si no lo declara, su costo es 100. El costo es el mismo en ambos sentidos» y §4.1 declara `costo` por sentido de la salida. Casos:

1. **Ambos sentidos omiten `costo`**: resuelto por §3.1 de forma expresa — 100 y 100; coincide con AC-001.
2. **Un sentido declara 100 y el otro omite**: 100 frente a 100; los efectos coinciden y no hay contradicción, AC-020 no aplica.
3. **Un sentido declara un costo distinto de 100 y el otro omite** (decisión normativa del equipo, elegida en la consulta del 2026-11-09): se aplica el default 100 al lado omitido y, como el efectivo 100 difiere del valor declarado en el otro sentido, AC-020 de 001 rechaza la salida de forma descriptiva identificando ambos valores; no existe herencia del costo del lado declarado.
4. **Una salida carece de sentido inverso** (decisión normativa registrada hoy): el PDF §3.1 y §4.1 no exigen la existencia del inverso; 001 **no añade** una regla de rechazo ni aceptación, y el punto continúa como pregunta pendiente; no bloquea el índice, los benchmarks, US1 ni el cazador.

Estas aclaraciones se integran en la validación de Steven sin cambiar `spec.md` ni inventar reglas de herencia o rechazo no decididas.

Los costos ponderan movimiento y rutas, pero no cambian qué salas son alcanzables para la verificación de resolubilidad. El recorrido de 002 conserva sus reglas de puertas y llaves.

### 3.3 Capacidad mínima de la vista

Steven acepta las operaciones conceptuales:

```text
contiene_sala(sala_id)
salidas_transitables(sala_id)
```

`salidas_transitables` entrega destino y costo de las salidas permitidas por la vista. Esto confirma la capacidad, no una firma Python, protocolo, clase ni tipo de retorno definitivos.

### 3.4 Vista de «ir a» desde conocimiento del jugador

Steven construirá la vista y su prueba de independencia frente al estado real oculto. La vista:

- contiene únicamente salas exploradas;
- enumera salidas solo desde salas exploradas;
- permite rutas únicamente entre salas exploradas mediante puertas recordadas abiertas;
- usa el conocimiento recordado, nunca el estado real oculto ni el esqueleto completo.

La verificación futura construirá estados reales distintos con el mismo mapa conocido y exigirá el mismo resultado de «ir a». Este criterio está acordado, pero la prueba todavía no se ha implementado ni ejecutado.

### 3.5 Consulta por paso y casos terminales

Steven acepta que:

- cada paso de «ir a» vuelve a calcularse con origen, destino y conocimiento vigentes; no se conserva una secuencia como compromiso futuro;
- origen igual a destino produce costo total 0 y ningún paso;
- ausencia de ruta es un resultado explícito, distinguible del caso anterior;
- el buscador devuelve semánticamente un paso, no decide `ATACAR` ni `ESPERAR`.

Esto cierra la semántica, pero no fija nombres, firma Python, clase/protocolo, campos ni tipo de retorno.

## 4. Decisiones de integración todavía abiertas

### 4.1 Firma y representación

- La búsqueda minimiza la suma de costos positivos y, entre rutas mínimas, elige la primera vecina de menor ID numérico.
- Un límite de costo restringe la consulta del cazador; «ir a» no recibe reglas nuevas desde 001.
- Deben acordarse la firma Python y la representación exacta de paso, destino alcanzado y sin ruta.
- Debe asignarse de forma concreta quién edita cada archivo compartido. La responsabilidad conceptual de Steven no asigna automáticamente `dto/sala.py`, `dto/actor.py` o `service/inicializador_partida.py`. `logica/mapa_cripta.py` queda fuera de esa pregunta concreta: Steven pidió expresamente que Sofía implemente allí el índice, preservando su API, orden e identidad.

Los nombres de estados, campos y tipos de retorno no quedan fijados por esta propuesta.

### 4.2 Estrategia inicial y reutilización

La primera integración usa cálculo individual desde cero. En colaboración con 003 se medirá el costo completo de cada decisión de «ir a» frente a su límite de **5 ms**, incluyendo toda preparación auxiliar requerida por la consulta.

La reutilización de cálculos permanece como alternativa, no como requisito ni optimización asumida. Solo podrá habilitarse si:

1. demuestra equivalencia observable con el cálculo individual desde cero para origen, destino y conocimiento vigentes;
2. mide su costo completo, incluida construcción, consulta, invalidación y limpieza;
3. respeta la independencia del mapa conocido y el límite aplicable.

El mecanismo y propietario concretos de esa reutilización siguen sin acuerdo.

### 4.3 Persistencia coordinada

Steven asume la persistencia de costo, rango y mapa conocido coordinada con Joshua para incluir también la línea de tiempo. Ni 001 ni una parte reserva unilateralmente v10 u otra versión. En el hash remoto consultado el único formato real sigue siendo v9; campos, compatibilidad, archivos concretos y versión final permanecen pendientes de implementación y comprobación.

**Propuesta registrada el 2026-11-09 (M3, pendiente de confirmación conjunta)**: un formato v10 único que incorpore, en una entrega coordinada de Steven y Joshua, costo, rango, mapa conocido del jugador y línea de tiempo, manteniendo la validación de versión de P1 §4.10 para que un guardado v9 se detecte como incompatible sin migración implícita. La propuesta no constituye acuerdo: requiere confirmación conjunta, asignación de archivos concretos y prueba; T041 y T055 verificarán ese mismo formato cuando exista la entrega real.

## 5. Puntos todavía no confirmados por ambos

- firmas Python, representación exacta del resultado y asignación de los archivos compartidos de datos/rutas todavía no acordados; el índice de `MapaCripta` ya está asignado a Sofía;
- mecanismo, claves, invalidación y propietario de reutilización para «ir a»;
- compatibilidad de lectura, versión final y entrega concreta de persistencia coordinada;
- política para una salida sin sentido inverso cuando no existe contradicción entre dos costos, no definida por las fuentes consultadas; el 2026-11-09 (A1) el equipo la dejó registrada como pregunta pendiente sin regla de rechazo ni aceptación.

## 6. Consumidores y compatibilidad

- **001**: cazador, movimiento ponderado y benchmarks de rutas.
- **002**: conserva su recorrido de resolubilidad; los costos no cambian alcanzabilidad.
- **003**: consume la vista restringida construida por Steven y vuelve a pedir un paso con conocimiento vigente.
- **004/guardado**: persiste estado canónico según el acuerdo futuro; nunca resultados ni cachés de ruta.

## 7. Criterios de cierre e integración

- [x] Steven acepta implementar validación estricta de costo/rango y el default solo por ausencia.
- [x] Se acuerda identificar sentidos por origen/destino, comparar costos y detectar ambigüedad entre salidas múltiples.
- [x] Steven acepta la capacidad `contiene_sala`/`salidas_transitables`.
- [x] Steven asume la vista del mapa conocido y su futura prueba de independencia.
- [x] Se acuerda que los costos no cambian la alcanzabilidad de 002.
- [x] Steven acepta recálculo por paso, origen=destino con costo 0 sin paso y ausencia de ruta distinguible.
- [x] Steven asume persistencia de costo/rango/mapa conocido coordinada con Joshua.
- [ ] Ambos fijan firmas Python y representación exacta sin confundir «sin ruta» con «ya en destino».
- [x] Steven solicita a Sofía implementar el índice de `MapaCripta` conservando firmas, orden e identidad; el plan identifica sus consumidores reales.
- [ ] Se asignan de forma concreta los demás archivos compartidos y se aclara la política de salidas sin inversa.
- [ ] 003 y 001 demuestran equivalencia y miden el límite de 5 ms con costo completo.
- [ ] Steven y Joshua publican campos, compatibilidad y versión de guardado y se verifica el hash de la entrega.
- [ ] Implementación y pruebas futuras verifican los acuerdos; ninguna se considera realizada por este documento.
