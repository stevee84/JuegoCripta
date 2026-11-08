# Propuesta pendiente con Joshua: cambios reversibles y reconstrucción

**Estado**: PROPUESTA PENDIENTE DE ACUERDO. No modifica `specs/004-linea-de-tiempo`, el guardado ni archivos de Joshua.

## 1. Objetivo

Permitir que retroceso y línea de tiempo restauren exactamente el estado introducido o afectado por 001, sin copiar el estado completo por acción y sin conservar cálculos de ruta obsoletos (`FR-014`, `FR-016`; spec 004 FR-022).

## 2. Separación propuesta

### Estado canónico que sí se registra/reconstruye

- sala actual de jugador y enemigos;
- pertenencia de enemigos a las salas e identidad de instancias;
- vida, actividad y procesamiento de muerte;
- apertura de puertas y eventos de cierre automático;
- reloj virtual;
- agenda: eventos insertados, extraídos, cancelados y reprogramados;
- tiempo y secuencia de próximas acciones;
- velocidad y efectos que la modifican;
- estado de azar cuando una acción lo consume;
- costos de salida y rango como datos de la versión cargada, disponibles en checkpoints/guardado donde corresponda.

### Datos derivados que no se registran ni persisten

- fronteras de búsqueda, etiquetas y predecesores;
- tablas de distancias;
- primera vecina precalculada;
- instantáneas compartidas y métricas de rutas;
- generación/caché usada solo para detectar vigencia.

Los derivados se reconstruyen desde el estado canónico y no aparecen en resúmenes históricos.

## 3. Contrato de cambios de 001

Sofía continúa mutando mediante cambios pequeños compatibles con `CambioReversible`:

| Mutación | Inverso esperado |
|---|---|
| mover actor | restaurar listas de salas y `sala_actual` con la misma identidad |
| atacar/morir | restaurar vida, actividad, botín/listas y eventos afectados |
| abrir/cerrar puerta | restaurar `abierta` y referencias/IDs del cierre pendiente |
| programar/extraer/cancelar | insertar o retirar el mismo evento y restaurar contadores |
| reprogramar por velocidad | restaurar velocidad, tiempo y secuencia anteriores del mismo evento |
| avanzar reloj | restaurar reloj anterior |

Una acción rechazada aborta sus cambios y no se publica a la línea de tiempo.

## 4. Notificación de reconstrucción propuesta

Después de cualquiera de estas operaciones:

- `HistorialReversible.deshacer_ultimo` exitoso;
- reconstrucción de `historia` sobre un estado temporal;
- carga de checkpoint/guardado;
- recorte de línea tras pergamino;

el coordinador invoca un punto acordado equivalente a:

```text
invalidar_calculos_derivados(motivo)
```

No se fija todavía nombre ni propietario. El efecto observable es:

1. desacoplar toda instantánea de ruta anterior;
2. no modificar reloj, agenda, azar, historial o partida.log;
3. obligar a que la siguiente decisión calcule desde el estado restaurado.

La invalidación puede ser O(1) por cambio de generación, pero la memoria pendiente de liberar se mide. Para una consulta histórica sobre una copia/checkpoint, sus derivados son locales y se descartan al terminar.

## 5. Pergaminos

La línea de tiempo y 001 conservan la excepción heredada:

- el pergamino utilizado queda consumido;
- la cantidad de pergaminos no forma parte de la reversión, incluidos recogidos/soltados en el intervalo;
- el resto del estado reversible de terreno, cazadores, agenda y puertas sí vuelve al punto anterior.

001 no implementa una segunda política de inventario; consume el contrato existente y verifica el resultado de punta a punta.

## 6. Reconstrucción histórica

Propuesta para spec 004:

- los checkpoints contienen el estado canónico completo que 004 ya define, incluyendo costos/cazadores disponibles por la versión cargada;
- entre checkpoints se aplican cambios canónicos de 001 en orden;
- no se reejecutan decisiones usando cachés guardadas;
- si 004 re-simula, usa el estado de `random.Random` del checkpoint y rutas calculadas desde el estado reconstruido;
- una consulta no modifica las cachés de la partida en curso.

La representación serializable exacta de cada cambio pertenece al acuerdo de 004/guardado; 001 ofrece IDs estables y valores anteriores necesarios, sin asumir formato binario.

## 7. Pruebas conjuntas propuestas

1. Capturar estado canónico, mover/atacar/reprogramar/cerrar puerta, retroceder y comparar igualdad salvo pergaminos.
2. Desde el mismo estado posterior al retroceso, aplicar las mismas acciones en dos ejecuciones y comparar registros.
3. Calentar una instantánea de ruta, cambiar una puerta, retroceder y verificar que la siguiente decisión coincide con cálculo desde cero.
4. Reconstruir un instante con cazadores y costos, consultar sin mutar la partida actual y comprobar el resumen de 004.
5. Medir retroceso con cambios de 001 frente a copia completa, sin que los derivados inflen el historial.

## 8. Criterios para considerar acordado el contrato

- [ ] Joshua confirma qué cambios de 001 necesita serializar/reaplicar.
- [ ] Sofía confirma que todas las mutaciones canónicas pasan por el historial.
- [ ] Se acuerda el punto de invalidación después de deshacer/reconstruir/cargar.
- [ ] Se acuerda que cachés de ruta no forman parte de checkpoints ni guardado.
- [ ] Se prueba la excepción de pergaminos y la continuación determinista.
- [ ] Los planes de 001 y 004 reflejan el acuerdo antes de tareas de integración.
