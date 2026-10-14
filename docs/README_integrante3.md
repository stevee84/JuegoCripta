# Aportación del integrante 3 — JuegoCripta

Conexión de catálogo preparada sobre la rama `joshua`,
base `912d7c1`. Incluye la corrección de lectura de salas de Steven y
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

El arranque con ClienteAPI está conectado. JuegoService instala el contador
antes del listado de criptas, conservando cualquier contador ya proporcionado.
InicializadorPartida establece el límite declarado en generales sin borrar
intentos previos; ClienteAPI comprueba el límite y cuenta cada solicitud/reintento.
Generales aporta la versión de la cripta. La versión de catálogo se consulta
una vez durante la preparación y se reutiliza dentro de RepositorioCatalogo.
Antes de publicar el estado se vuelven a comprobar ambas versiones.

Las fichas se resuelven mediante RepositorioCatalogo.resolver_lote, en lotes
máximos de diez, incluyendo las dependencias del botín. Se reutilizan LRU y
fichas persistidas de la versión vigente. El almacén está en
`cache/catalogo/`, bajo una carpeta ya excluida de Git. Un adaptador local
impide aceptar el respaldo antiguo de disco; la memoria conserva su versión.
Si pertenece a otra versión, se utiliza una caché nueva al iniciar, conservando
la memoria y las referencias de la partida anterior hasta publicar el estado.

No se modifican repositorio, cliente HTTP, contador, caché, fuentes, DTO ni motor.
No se amplía cache-size. Se conserva la estrategia existente de reconstruir
el paquete completo: si no hay datos vigentes ni presupuesto suficiente,
el inicio se rechaza y se conserva la partida actual. Criptas mayores pueden
necesitar datos persistidos o un paquete offline completo; este bloque no
sustituye la integración general de precarga y descarga bajo demanda.

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
- Guardado/carga: `guardar [RUTA]`, `cargar [RUTA]`. Sin ruta se usa
  `partidas/partida.bin` (`Configuracion.ruta_guardado`).
- Inventario: `seleccionar ID` mueve el cursor sin consumir tiempo.
- Sesión: `salir`.

`guardar` utiliza el binario v5 de Steven y valida su reconstrucción antes
de reemplazar el archivo. Se guarda entre decisiones, fuera de una acción
en curso; el archivo anterior se conserva ante errores. Una partida ya
terminada (victoria o derrota) no se guarda.

Continuar: en pygame, si existe `partidas/partida.bin` legible, el menú
inicial ofrece "Continuar partida guardada"; en consola se indica escribir
`cargar`. Al cargar se vuelve a aplicar el `presupuesto_solicitudes` de la
cripta (§5.1) y las fichas se resuelven memoria → `cache/catalogo/` →
red, en lotes de 10 (§4.3). Si la versión de cripta o catálogo cambió, la
carga se rechaza y se vuelve al menú.

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
- El arranque y replay funcionan con paquetes completos y con la fuente HTTP
  conectada al repositorio. Se comprobó el arranque real de cripta-01: seis
  salas, nueve solicitudes frente a un límite declarado de nueve.
- La conexión de arranque HTTP utiliza repositorio, contador, caché y disco
  del integrante 2. La descarga bajo demanda y precarga general siguen
  siendo una coordinación del equipo; no se cambia el modelo de carga completa.
- OrdenadorAdaptativo se utiliza en inventario, puntajes y en las listas
  auxiliares del catálogo de inicialización. Su uso en el índice del binario
  debe integrarlo su propietario; no se modifica ese archivo en este bloque.
- El ejecutor común acepta proveedores adicionales de benchmarks. Los de
  caché, recuperación de fichas y guardado/carga deben aportarlos sus responsables.
- Si se exige historial anterior a la carga, acordar su serialización aparte.
- La entrega conjunta y la defensa requieren revisar los documentos de los tres.

## Aplicación y comprobación de este bloque

Reemplazar service/inicializador_partida.py, service/juego_service.py,
controller/ejecutor_replay.py y tests/test_service/test_inicializador_partida.py.
Agregar tests/test_service/test_conexion_catalogo_inicializador.py.
Los tres documentos del integrante 3 se actualizan por separado.
Conservar todos los demás archivos, incluidos main.py y main_pygame.py.

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

## Verificación de la conexión de catálogo

Las nuevas regresiones usan ClienteAPI, repositorio, almacén, LRU y motor
reales con transporte simulado. Comprueban arranque frío, reutilización de
disco/memoria, versiones, presupuesto insuficiente, reintentos, protección
de la partida vigente y replay. Las pruebas existentes de bloqueo HTTP se
adaptan a su conexión; faltar una ficha local puede resolverse desde memoria
vigente, por lo que ese caso se comprueba como recuperación y no como error.

Además se verificó la API real: cripta-01 inició con seis salas y nueve
solicitudes sobre presupuesto nueve. Registrar el conjunto completo ya
verificado y ejecutar esperar no hicieron consultas adicionales; guardar en
v5 también funcionó. El registro conserva la versión del conjunto que fue
cargado y verificado al inicio, aunque el servidor cambie posteriormente.
Replay exige una fuente o copia local con esas versiones y conserva el log.

Para reiniciar, cargar otros datos o reproducir sobre una fuente HTTP ya
agotada puede necesitarse un paquete offline compatible. No se reinicia
ocultamente el contador compartido ni se habilita una partida incompleta.


Verificación final del bloque: 789 pruebas aprobadas con `python -m pytest -q`,
incluidas las pruebas de API real. Se conservan arriba las cifras históricas.