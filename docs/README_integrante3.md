# Aportación del integrante 3 — JuegoCripta

Bloque de guardar/cargar v5 preparado sobre la rama `joshua`,
base `ee39856`. Incluye el trabajo integrado de los tres integrantes.
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
sala inicial, paginación y fichas reales en el inicializador.

`--replay` no crea la vista interactiva, pero su ejecución completa
desde el arranque también depende del inicializador.

`--bench` no crea la vista. Ejecuta las mediciones del integrante 3 y
reutiliza la medición existente de agenda y el script de ciclos de simulación,
sin modificar sus archivos. Los tiempos se reportan en ns por lote; cada
medición conserva su reloj, repeticiones y calentamiento cuando difieren.
El ciclo demo conserva las 200 muestras y los 10 calentamientos del script.
Faltan proveedores de caché, recuperación de fichas y guardado/carga, que
corresponden a sus responsables. El ejecutor acepta proveedores adicionales.

## Componentes implementados

- Lista doble propia, compatible con inventario y caché.
- Inventario con capacidad, cursor, retiro y movimiento al frente.
- Cola circular y bitácora de los últimos 20 mensajes.
- Insertion sort y Merge sort con selección adaptativa.
- Historial de cinco intervalos y cambios reversibles propios.
- Equipo, consumibles, transferencias y pergaminos.
- Controlador, consola, registro de acciones y ejecutor de replay.
- Registro local de resultados y consultas ordenadas de puntajes.
- Reconstrucción v5 y comandos guardar/cargar con fichas compatibles.

El motor integrado administra reloj, eventos y cierre del historial.
El controlador no vuelve a ejecutar las acciones ni suma tiempo aparte.

JuegoService.conectar_inventario conecta automáticamente el mismo
ServicioInventario al motor. Ambos comparten equipo, catálogo, adaptador,
historial y referencias de caché. La conexión debe hacerse antes de usar,
equipar o retroceder, y fuera de un intervalo abierto.

## Comandos

- Consultas: `estado`, `criptas`, `puntajes`, `bitacora`, `ayuda`.
- Partida: `cripta ID`, `mover DIRECCION`, `abrir DIRECCION`,
  `atacar ID`, `esperar`.
- Inventario: `recoger ID`, `soltar`, `equipar`, `siguiente`, `anterior`,
  `inventario [peso|valor|nombre]`.
- Objetos: `usar [ID]`, `retroceder [ID]`.
- Registro: `registro RUTA`, antes de la primera acción.
- Exportación parcial: `exportar_parcial RUTA`.
- Guardado/carga: `guardar RUTA`, `cargar RUTA` (comillas si hay espacios).
- Sesión: `salir`.

`guardar` utiliza el binario v5 de Steven y valida su reconstrucción antes
de reemplazar el archivo. Se guarda entre decisiones, fuera de una acción
en curso; el archivo anterior se conserva ante errores.

`cargar` restaura entidades y referencias, agenda, estado del azar,
equipo/bonos, efectos, botín, rastro, puertas, salida y sesión. El equipo
no vuelve a sumar sus bonos. Requiere las fichas de la versión guardada:
una fuente compatible (incluida FuenteOffline) o las fichas resueltas de
la partida vigente con las mismas versiones. La carga inválida no
reemplaza la partida actual. No se carga durante una acción ni con un log
activo; una partida cargada tampoco se presenta como inicio de un replay.

El historial previo al guardado se descarta por acuerdo del equipo.
`limitaciones_carga = ("historial",)`; las nuevas acciones conservan sus
inversos y pueden deshacerse con pergaminos. La bitácora de consola pertenece
a la sesión y no se serializa. Los formatos anteriores al v5 se rechazan.

`exportar_parcial` y la llamada directa anterior `ControladorJuego.guardar`
se conservan como exportaciones para inspección sin validar la reanudación.
Para guardar una partida validada desde código se usa
`JuegoService.guardar_partida`; el comando `guardar` utiliza esa misma ruta.

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
Después de conectar el servicio compartido pasaron las 662 pruebas
existentes y nuevas de la suite, incluidas tres regresiones de conexión,
equipo/retroceso y rechazos de conexión. Esto no verifica por sí solo
el arranque con datos reales ni la reanudación de partidas guardadas.
En el bloque v5 pasan 738 pruebas: incluye 24 regresiones nuevas de guardar,
cargar, continuar, azar avanzado, equipo, eventos/efectos, botín compartido,
retroceso nuevo, fuente offline, caché, archivos inválidos y registros activos.
Una expectativa anterior de la ayuda se actualiza al mensaje v5.

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

El formato binario corresponde al integrante 2 y no se modifica en este
bloque. RestauradorPartida conserva cargar/restaurar para inspección y añade
restaurar_para_reanudar(datos, catalogo). Esta entrada reconstruye las
referencias compartidas, incluyendo el botín retenido por enemigos muertos,
y entrega un estado conectado con historial vacío. JuegoService lo publica
en el mismo motor, sin repetir las reglas de inicio.

## Evidencia y pendientes

Mediciones propias: `docs/mediciones_integrante3*.json`.
Decisiones y complejidades: `docs/secciones_integrante3.md`.
Consultas LLM: `docs/PROMPTS_LLM_integrante3.md`.

Pendientes:

- Conectar el inicializador y comprobar consola/replay con datos reales.
- Si se exige historial anterior a la carga, acordar y añadir su serialización aparte.
- Coordinar ordenamientos requeridos por índices y catálogo.
- Conectar proveedores restantes de caché, recuperación de fichas y guardado/carga cuando sus responsables los entreguen.
- Completar la bitácora de prompts realmente utilizados.