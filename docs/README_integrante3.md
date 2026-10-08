# Aportación del integrante 3 — JuegoCripta

Bloque de arranque y replay preparado sobre la rama `joshua`,
base `340ba86`. Incluye la corrección de lectura de salas de Steven y
el guardado/carga v5 previamente integrado.
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

`--offline` conecta InicializadorPartida. Selecciona `cripta ID` en consola;
el paquete local debe incluir generales, todas las páginas del esqueleto,
contenido de cada sala (incluidas las vacías), fichas y archivos de versiones.
Se usan los campos de §3.3 del enunciado: sala_inicial, sala_salida,
llave_salida, inventario_max y las estadísticas declaradas en jugador.
Los números de salas, páginas y estadísticas no se fijan en el programa.
La identidad de presentación predeterminada es `jugador` / `Jugador`;
puede configurarse al construir InicializadorPartida. No sustituye datos de combate.

`--replay` conecta la misma fábrica y ejecuta sin vista ni entrada. También
EjecutorReplay.reproducir(ruta), sin servicio inyectado, utiliza el paquete
local `datos/`. Requiere las versiones exactas del log y un paquete completo.

El ClienteAPI directo sigue bloqueado para iniciar: falta que el bloque de
datos conecte el presupuesto real de solicitudes, persistencia y precarga.
No se descarga toda una cripta por HTTP sin ese control. La fábrica puede
recibir otra fuente coordinada que respete FuenteDatos y entregue el paquete
completo. No se cambiaron ClienteAPI, FuenteOffline, repositorios ni precarga.

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
- Inicializador de paquetes completos y conexión de consola/replay desde main.
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
En el bloque v5 pasaron 738 pruebas: incluye 24 regresiones nuevas de guardar,
cargar, continuar, azar avanzado, equipo, eventos/efectos, botín compartido,
retroceso nuevo, fuente offline, caché, archivos inválidos y registros activos.
Una expectativa anterior de la ayuda se actualiza al mensaje v5.
En este bloque pasan 764 pruebas, incluidas 26 nuevas de inicialización,
consola/main, replay, lotes, versiones, paquetes incompletos, identidad de
referencias y protección de la partida vigente. No se modificaron pruebas anteriores.
Además se descargó un paquete de la API real para una comprobación aislada:
cripta-01, seis salas y once fichas. Con FuenteOffline se verificaron arranque,
registro/replay determinista y guardado/carga. La comprobación no acredita
presupuesto HTTP, precarga, rendimiento en todas las criptas ni otras versiones.

## Datos y persistencia

Las fichas sintéticas y AdaptadorFichas sirven para pruebas.
El inicializador utiliza el esquema externo descrito en el enunciado.
Las pruebas sintéticas no sustituyen la comprobación de paquetes/versiones reales.

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

Estado del cierre:

- El bloque funcional propio de inventario, retroceso, ordenamientos, consola,
  puntajes, registro, replay y reconstrucción/guardado v5 está implementado y probado.
- El arranque y replay funcionan con paquetes offline completos, incluyendo
  una comprobación con datos extraídos de la API real.
- La integración HTTP completa sigue pendiente del equipo: presupuesto,
  persistencia y precarga pertenecen al integrante 2. Después de entregar esa
  fuente coordinada se debe verificar el recorrido desde main con ella.
- OrdenadorAdaptativo se utiliza en inventario, puntajes y en las listas
  auxiliares del catálogo de inicialización. Su uso en el índice del binario
  debe integrarlo su propietario; no se modifica ese archivo en este bloque.
- El ejecutor común acepta proveedores adicionales de benchmarks. Los de
  caché, recuperación de fichas y guardado/carga deben aportarlos sus responsables.
- Si se exige historial anterior a la carga, acordar su serialización aparte.
- La entrega conjunta y la defensa requieren revisar los documentos de los tres.

## Aplicación y comprobación de este bloque

Reemplazar main.py, service/juego_service.py y controller/ejecutor_replay.py.
Agregar service/inicializador_partida.py y
tests/test_service/test_inicializador_partida.py. Los documentos se actualizan
por separado. Conservar todos los demás archivos.

```bash
python -m pytest -q
git --no-pager diff --check
git status
git --no-pager diff --stat
```

Las versiones JSON de ClienteAPI se normalizan a texto dentro de JuegoService,
sin cambiar el contrato de las fuentes. El catálogo del inicializador usa
TablaHashImpl para referencias y OrdenadorAdaptativo para listas auxiliares.
Cada fuente recibe lotes de hasta diez salas/fichas. El paquete se reconstruye
antes de publicar el estado; si está incompleto se conserva la partida vigente.
Una nueva partida conecta su servicio de inventario al motor antes de aceptar
acciones, y libera las referencias de caché del inventario anterior.