# Propuesta pendiente con Steven: datos ponderados y rutas para «ir a»

**Estado**: PROPUESTA PENDIENTE DE ACUERDO. Este documento no modifica ni sustituye specs 002/003, archivos de Steven ni un contrato ya aceptado.

**Proponentes/consumidores**: Sofía ofrece cálculo de rutas; Steven ofrece adaptación de datos y la vista del mapa conocido.

## 1. Objetivo

Acordar dos fronteras:

1. entregar al modelo costos y rangos ya validados conforme a `FR-001`, `FR-002`, `FR-009` y `FR-011` de 001;
2. permitir que «ir a» reutilice el cálculo ponderado de 001 sin acceder al esqueleto completo ni al estado real de puertas que el jugador desconoce.

## Estado del código observado tras integrar `origin/Steve`

El merge aporta puntos concretos de integración, pero **no constituye aceptación** de esta propuesta y todas las casillas de la sección 7 siguen pendientes:

- `DecodificadorDatos.convertir_sala()` adapta `salidas` del API y `puertas` del guardado, pero hoy no lee ni valida `costo` y `Puerta` no lo almacena.
- `DecodificadorDatos._adaptar_contenido_externo()` resuelve la ficha antes de crear cada enemigo; hoy toma `comportamiento`, pero no valida ni materializa `rango`. `convertir_contenido()` es el camino interno usado al reconstruir.
- `InicializadorPartida._construir()` reúne todas las páginas, rechaza IDs repetidos, vincula destinos y llama a 002 antes de cargar contenido. La simetría de costos necesita el esqueleto completo y debe ocurrir antes de que 002 o el juego lo consuman; el lugar y responsable exactos se acuerdan.
- `GuardadoBinario.VERSION` es **9**. `_escribir_sala()` y `_leer_sala_datos()` no incluyen costo/rango y el lector exige versión exacta, por lo que añadirlos requiere acordar representación, nueva versión y compatibilidad.
- `RestauradorPartida._reconstruir_mapa()` reutiliza el decodificador para registros internos y `_completar_v5()` vuelve a vincular fichas. Son consumidores directos del contrato de persistencia.
- `verificador_resolubilidad.verificar()` usa destino, apertura y llaves, no pesos. Debe seguir obteniendo el mismo resultado de 002 después de incorporar costos.

## 2. Propuesta de datos entregados a 001

### Salida validada

Cada salida que llega al modelo ofrece:

- origen y destino con ID de sala entero estricto;
- costo entero estricto `>= 1`;
- costo 100 solo cuando el campo estaba ausente;
- estado actual de apertura y metadatos heredados.

`bool`, cadena, fracción y entero `<1` se rechazan. No se convierten ni sustituyen. La validación del esqueleto completo confirma que los dos sentidos tienen el mismo costo; una contradicción rechaza la cripta con un error que identifica la salida y ambos valores.

### Ficha de cazador validada

Si `comportamiento == "cazador"`, la ficha entrega `rango` con `type(rango) is int` y `rango >= 0`. Ausencia, booleano, cadena, fracción o negativo rechazan la ficha con un error que la identifica. No hay valor predeterminado.

### Responsabilidad por acordar

| Tema | Propuesta |
|---|---|
| Decodificación y mensajes | Steven, como propietario de datos, valida forma y dominio. |
| Uso en simulación | Sofía consume valores ya validados y mantiene defensas de contrato en límites públicos. |
| Simetría | validación después de reunir el esqueleto completo y antes de iniciar. |
| Persistencia | Propuesta: conservar `costo`/`rango` con la versión correspondiente, sin reinterpretarlos. El formato vigente es v9 y el cambio de esquema requiere acuerdo. |
| Pruebas | fixtures de Steven prueban rechazo; pruebas de Sofía confirman que el motor no convierte y usa los valores. |

La asignación anterior requiere aceptación explícita; hasta entonces es solo propuesta.

## 3. Propuesta de vista de grafo

El buscador de Sofía no recibe `MapaCripta` directamente. Recibe una vista de solo lectura con estas operaciones conceptuales:

```text
contiene_sala(sala_id: int) -> bool
salidas_transitables(sala_id: int) -> iterable de (destino_id: int, costo: int)
```

No se exige un nombre de clase ni una firma Python definitiva; el acuerdo debe preservar esa capacidad mínima.

### Vista para cazador

- contiene todas las salas del esqueleto;
- enumera solo puertas realmente abiertas en ese instante;
- usa costos reales;
- no consulta contenido descargado ni niebla.

### Vista para «ir a»

Steven construye la vista exclusivamente desde el mapa conocido:

- solo contiene salas exploradas permitidas por su spec;
- solo enumera salidas que el jugador recuerda abiertas;
- usa los costos conocidos/recordados por el jugador;
- nunca delega una consulta que pueda revelar salas desconocidas, una puerta real distinta de la recordada o el esqueleto completo.

La separación se comprueba con dos estados reales distintos que produzcan el mismo mapa conocido: «ir a» debe devolver la misma ruta en ambos.

## 4. Propuesta de consulta de ruta

```text
proximo_paso(vista, origen_id, objetivo_id, limite_costo=None)
    -> alcanzable, costo_total, primera_vecina_id, costo_primera_salida
```

Semántica compartida:

- minimiza suma de costos positivos;
- entre rutas mínimas elige la primera vecina de menor ID numérico;
- no muta la vista ni el juego;
- no descarga datos;
- no abre puertas;
- con límite, no examina deliberadamente más allá de la región necesaria para decidir dentro del límite.

Uso de 001: pasa `limite_costo=rango`. Uso de «ir a»: acuerda con su spec si usa límite; 001 no introduce esa regla.

## 5. Errores de contrato

- IDs no enteros, costos/rangos inválidos y referencias inexistentes se rechazan antes de buscar.
- Una vista que cambia durante una consulta no se comparte; el llamador obtiene una vista coherente del instante o repite la consulta.
- Un origen/objetivo no visible para «ir a» se resuelve según la spec 003, no según 001.

## 6. Consumidores y compatibilidad

- 001: cazador y benchmarks de rutas.
- 002: puede conservar sus propios recorridos de resolubilidad; el índice de salas mantiene orden e identidad.
- 003: «ir a» puede reutilizar el buscador mediante su vista restringida.
- guardado: persiste datos canónicos, nunca resultados de ruta.

## 7. Criterios para considerar acordado el contrato

- [ ] Steven acepta responsabilidad y ubicación de validación de costo/rango.
- [ ] Ambos acuerdan cómo identificar los dos sentidos para validar simetría.
- [ ] Ambos acuerdan la interfaz mínima de vista de grafo.
- [ ] Una prueba demuestra que «ir a» no observa información fuera del mapa conocido.
- [ ] Se identifican las firmas públicas que deben conservarse.
- [ ] El acuerdo se refleja en los planes de las partes antes de generar tareas de integración.
