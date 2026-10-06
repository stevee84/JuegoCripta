# Aportación del integrante 3 — JuegoCripta

Actualizado el 6 de octubre de 2026, sobre la rama `joshua`,
commit `5e8977a`. Incluye el trabajo integrado de los tres integrantes.
Este documento describe el estado comprobado; no declara terminado
el proyecto completo.

## Instalación

Python 3.11 o superior. Desde la carpeta principal:

```bash
python -m venv .venv
```

Activar el entorno:
- PowerShell: `.\.venv\Scripts\Activate.ps1`
- Linux: `source .venv/bin/activate`

Después:

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

## Modos disponibles

```bash
python main.py --demo --semilla 123
python main.py --offline --cache-size 25 --semilla 123
python main.py --replay partida.log --offline
python main.py --bench > mediciones.json
```

`--demo` utiliza una partida sintética con las clases reales.
No sustituye la integración con datos de la API.

El arranque desde una fuente real u offline todavía necesita conectar
un inicializador compatible. Faltan confirmar jugador inicial,
sala inicial, paginación y fichas reales. La URL de la API sigue
sin configurar.

`--replay` no crea la vista interactiva, pero su ejecución completa
desde el arranque también depende del inicializador.

`--bench` no crea la vista y actualmente ejecuta las mediciones
del integrante 3. Falta conectar las mediciones de los compañeros.

## Componentes implementados

- Lista doble propia, compatible con inventario y caché.
- Inventario con capacidad, cursor, retiro y movimiento al frente.
- Cola circular y bitácora de los últimos 20 mensajes.
- Insertion sort y Merge sort con selección adaptativa.
- Historial de cinco intervalos y cambios reversibles propios.
- Equipo, consumibles, transferencias y pergaminos.
- Controlador, consola, registro de acciones y ejecutor de replay.
- Registro local de resultados y consultas ordenadas de puntajes.

El motor integrado administra reloj, eventos y cierre del historial.
El controlador no vuelve a ejecutar las acciones ni suma tiempo aparte.

El motor ya admite equipar. Falta conectar automáticamente el mismo
ServicioInventario entre motor y JuegoService para compartir equipo,
catálogo, adaptador y referencias de caché.

## Comandos

- Consultas: `estado`, `criptas`, `puntajes`, `bitacora`, `ayuda`.
- Partida: `cripta ID`, `mover DIRECCION`, `abrir DIRECCION`,
  `atacar ID`, `esperar`.
- Inventario: `recoger ID`, `soltar`, `equipar`, `siguiente`, `anterior`,
  `inventario [peso|valor|nombre]`.
- Objetos: `usar [ID]`, `retroceder [ID]`.
- Registro: `registro RUTA`, antes de la primera acción.
- Exportación parcial: `exportar_parcial RUTA`.
- Sesión: `salir`.

`guardar` y `cargar` completos permanecen bloqueados:
el binario actual no permite reanudar toda la partida.

Costos base: mover/atacar/esperar 100; equipar/usar/abrir 50;
recoger/soltar 25; retroceder 0. El intervalo depende de la velocidad.
Los rechazos no consumen tiempo.

## Puntajes

```text
puntajes
puntajes acciones_ejecutadas
puntajes enemigos_derrotados
puntajes reloj_final
```

Sin argumento se conserva el orden de registro.
Con argumento se utiliza OrdenadorAdaptativo en orden ascendente.
Los empates conservan su orden y el archivo no se modifica.
No se inventa una fórmula de puntuación.

Se verificaron 40 pruebas de repositorio y controlador, además de
una comprobación del método nuevo y conservación de la lista original.
Esto no equivale a una validación completa de todo el proyecto.

## Datos y persistencia

Las fichas sintéticas y AdaptadorFichas sirven para pruebas.
Sus campos configurables no deben confundirse con el esquema
confirmado de la API.

RegistroPartida utiliza JSON Lines y anexado de acciones exitosas.
Las consultas y rechazos no se registran como acciones.
El retroceso no borra acciones anteriores del log.

ServicioInventario.exportar_representacion entrega capacidad,
instancias, cursor, orden, equipo y datos del historial.
Su representación todavía no constituye un guardado restaurable.

El formato binario corresponde al integrante 2. Debe acordarse
la restauración de los subsistemas antes de habilitar guardar/cargar.

## Evidencia y pendientes

Mediciones propias: `docs/mediciones_integrante3*.json`.
Decisiones y complejidades: `docs/secciones_integrante3.md`.
Consultas LLM: `docs/PROMPTS_LLM_integrante3.md`.

Pendientes:
- Compartir automáticamente ServicioInventario con el motor.
- Conectar el inicializador y comprobar consola/replay con datos reales.
- Acordar exportación/restauración del bloque propio con persistencia.
- Coordinar ordenamientos requeridos por índices y catálogo.
- Reunir los proveedores de mediciones en --bench.
- Actualizar los límites antiguos de las secciones técnicas
  y completar la bitácora de prompts realmente utilizados.