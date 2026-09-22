# CRIPTA — Distribución del equipo

Estructuras de Datos · II Ciclo 2026

| Integrante | Nombre | Bloque | Rama sugerida |
|------------|--------|--------|---------------|
| 1 | ______ | Simulación y reglas | feature/integrante-1 |
| 2 | ______ | Datos y persistencia | feature/integrante-2 |
| 3 | ______ | Interacción y operaciones | feature/integrante-3 |

## Propiedad del código

| Ubicación | Resp. | Contenido |
|-----------|-------|-----------|
| `dto/` | 1 | Entidades, estado, eventos y acción |
| `logica/mapa_cripta.py` `logica/registro_rastro.py` | 1 | Grafo y rastro |
| `logica/agenda_eventos.py` `logica/motor_juego.py` | 1 | Orden temporal y ejecución |
| `logica/reglas_combate.py` `logica/comportamiento_enemigos.py` `logica/gestor_efectos.py` | 1 | Combate, IA local y efectos |
| `logica/acciones.py` | 1 | Costos de acción |
| `logica/inventario.py` `logica/servicio_inventario.py` | 3 | Orden, cursor, objetos |
| `logica/cambios.py` `logica/historial_reversible.py` | 3 | Retroceso |
| `logica/ordenamiento.py` `logica/bitacora_pantalla.py` | 3 | Algoritmos y bitácora |
| `estructuras/monticulo_minimo.py` | 1 | Montículo propio |
| `estructuras/tabla_hash.py` | 2 | Tabla hash propia |
| `estructuras/lista_doble.py` `estructuras/cola_circular.py` | 3 | Lista doble y cola circular |
| `datos/` (excepto registro_partida y repositorio_puntajes) | 2 | API, offline, decodificador, presupuesto, almacén, guardado |
| `datos/registro_partida.py` `datos/repositorio_puntajes.py` | 3 | Log y puntajes |
| `service/` | 2/3 | Catálogo, precarga, caché, coordinación |
| `controller/` `vista/` | 3 | Controlador, replay y consola |
| `main.py` `configuracion.py` | 3 | Arranque y argumentos |
| `tests/` `benchmarks/` `docs/` | Todos | Cada uno prueba y mide su bloque |

## Contratos compartidos (acordados el Día 1)

- `contratos/cambio_reversible.py` — CambioReversible
- `contratos/fuente_datos.py` — FuenteDatos
- `contratos/tabla_hash.py` — TablaHash
- `contratos/lista_doble.py` — ListaDoble
- `contratos/agenda_eventos.py` — AgendaEventosContrato
- `contratos/motor_juego.py` — MotorJuegoContrato
- `contratos/ordenador_adaptativo.py` — OrdenadorAdaptativoContrato

## DTOs compartidos

- `dto/accion.py` — Accion y ResultadoAccion

## Stubs temporales

- `stubs/tabla_hash_dict.py` — dict como hash (Int 1 usa mientras no esté la real del Int 2)
- `stubs/lista_doble_simple.py` — lista Python (Int 2 usa mientras no esté la real del Int 3)
- `stubs/motor_falso.py` — motor que siempre aprueba (Int 3 usa mientras no esté el MotorJuego del Int 1)

## Hitos

1. **Base** — Repositorio, contratos y datos de una cripta visibles.
2. **Estructuras** — Montículo, TablaHash, ListaDoble y ColaCircular con pruebas.
3. **Primera partida** — Partida pequeña jugable de extremo a extremo.
4. **Reglas completas** — Efectos, retroceso, caché, offline.
5. **Persistencia** — Guardar, cargar y reproducir conservan resultado.
6. **Evidencia** — Benchmarks, pruebas, decisiones, README y defensa.

## Regla de colaboración

No modificar el contrato público de otro módulo sin avisar y actualizar a sus consumidores.
