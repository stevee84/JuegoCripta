# Secciones técnicas del integrante 3

Fecha de trabajo: 2026-10-01. Datos medidos, no estimaciones, en
`mediciones_integrante3_inicial.json` (32/4) y `mediciones_integrante3.json`
(16/1, ejecutor main final). Las comparaciones numéricas de las secciones
usan `mediciones_integrante3_calibracion.json` (16/1). CPython 3.11.9,
Windows 10 build 26200, Intel Family 6 Model 154;
15 repeticiones, un calentamiento por lote, `perf_counter_ns`, semilla 123.
Unidades originales **ns por lote**, no tiempos de toda la partida.
Preparación de entradas fuera del cronómetro; sin red ni presentación.
El entorno compartido presenta ruido: medianas/minimos no prueban un óptimo
universal ni extrapolan rendimiento de red/juego completo.
Los informes conservan las corridas de calibración efectivamente ejecutadas;
las validaciones adicionales de capacidad/registros se endurecieron después
y se volvió a ejecutar `main.py --bench` sobre el árbol final. Reejecutar
para medir el entorno de la defensa.

## 4.5 Inventario y equipo

**Problema:** identidad de instancias/nodos, cursor estable, máximo por
posiciones y transferencia reversible. Cada instancia ocupa una posición;
no se impone peso total. Catálogo clasifica, nunca el texto de un ID.

**Operaciones/decisión:** reutilizar ListaDobleImpl y nodo seleccionado.
Agregar, quitar actual y mover al frente O(1); buscar ID o restaurar vecinos
por marcas O(n). Suelo utiliza la lista de Sala: localizar/reinsertar O(m).
Capacidad se comprueba antes de preparar metadatos reversibles, también
cuando el inventario lleno rechaza la acción.

Equipo reside en ServicioInventario (no campos nuevos en DTO). Dos puestos,
bonos efectivamente aplicados y jugador referenciado. Sustituir resta el bono
anterior, devuelve su ubicación a inventario, suma el nuevo y mueve el mismo
nodo. Reequipar no acumula; soltar retira el bono. Cambios guardan como máximo
dos referencias/ubicaciones, una estadística y la marca del nodo. Inversión
de soltar primero restaura capacidad/nodo y después equipo, en orden inverso.

**Alternativa medida:** retirar el frente de list Python es más rápido para
512 elementos (1.0 µs frente a 5.1 µs de nuestro retiro). Se descarta no por
una supuesta victoria de Python puro, sino por requerir estructura propia,
preservar el mismo nodo y garantizar retiro seleccionado O(1); list desplaza
referencias O(n). Medición de un retiro, no construcción/búsqueda del cursor.

**Límites:** clase/curación/campos vienen de adaptador local provisional.
Curación inmediata satura vida_max y consume la instancia; llave no consume.
Velocidad, antídoto y antorcha requieren las capacidades de simulación
enumeradas en README; rechazan antes de consumir. No se crea otro gestor.

## 4.6 Retroceso

**Problema:** revertir hasta cinco acciones cerradas sin copiar partida y
conservar cambios irreversibles de pergaminos. Historial usa los dos extremos
de la lista doble; TransaccionAccion es pila de inversos.

**Decisión/operaciones:** registrar O(1), descartar antigua O(1), revertir O(k)
más búsqueda de posiciones/transferencias de cada inverso. Acciones rechazadas
pueden descartar únicamente su intervalo vacío. El servicio devuelve cambios;
NO cierra intervalos temporales artificiales ni captura combate/RNG ajenos.

El pergamino valida historial/capacidad, retira una instancia, delega la última
transacción y permanece consumido. Costo cero, sin transacción nueva. Recoger
y soltar pergaminos se clasifican como no reversibles. Dos usos deshacen dos
transacciones distintas. Las marcas existentes de suelo/inventario sobreviven
a desapariciones irreversibles, preservando referencias y cursor válido.
Si la proyección de capacidad excede inventario_max, se rechaza antes de
consumir y se informa la ambigüedad; no se aumenta capacidad ni descartan cosas.

**Alternativa medida:** registrar 512 intervalos sintéticos con máximo cinco
cerrados: 1.4243 ms. Copiar con deepcopy un estado sintético con 512 referencias
para cada intervalo: 104.8251 ms. La alternativa también retiene solo cinco;
el costo proviene de copiar, no de una pila ilimitada. No se usa en producción.

**Límites:** los intervalos completos deben contener también eventos y cambios
de simulación. Los diccionarios descriptivos actuales no cumplen ese contrato.
No se afirma atomicidad frente a historial corrupto o inversos ajenos que
fallen a mitad de ejecución; capacidad/transferencias propias se prevalidan.
Fijaciones de caché se agregan desde inventario/equipo/historial fuera del
retroceso; liberaciones compartidas necesitan acordar propiedad del ID.

## 4.8 Bitácora

**Problema/decisión:** últimos 20 mensajes, reemplazo del más antiguo sin
crecimiento. Se reutiliza ColaCircular, interfaz agregar/obtener_mensajes.
Agregar O(1); lectura O(20), copia de referencias. Vista imprime como máximo
20 y no modifica cola/estado; efectos se muestran mediante atributos reales.

**Alternativa medida:** 512 mensajes: cola propia 0.2526 ms; list con pop(0)
y límite 20, 0.0820 ms. list es más rápida en este tamaño fijo debido a C;
no se inventa ventaja temporal. Se elige cola circular por estructura exigida,
índices constantes y comportamiento explícito al llenarse.

**Límites:** mensajes no son cambios reversibles ni operaciones de motor.
Consultar bitácora no consume tiempo y devuelve mensajes en orden de llegada.

## 4.9 Ordenamientos

**Problema:** ordenar por peso/valor/nombre sin modificar orden real/cursor.
Se construye una colección auxiliar de referencias y claves reales de fichas;
faltantes/valores inválidos se rechazan, no se inventan ceros o nombres.

**Decisión:** Insertion estable O(n + desplazamientos), peor O(n²), frente a
Merge estable O(n log n), espacio O(n). Empates conservan el orden real de
partida; no hay desempate oculto por ID. Las claves se evalúan UNA vez aun
cuando se abandona Insertion, evitando duplicar criterios costosos.

**Calibración:** en primera corrida, invertidos n=8: Insertion 6.8 µs, Merge
8.8 µs; n=32: 86.7/44.7 µs. Se reduce umbral 32 a 16 como compromiso; para
mayores tamaños se limita el intento a n desplazamientos, en lugar de 4n.
La primera corrida de casos simples desordenados favoreció el factor 1 sobre
4; ordenados no hacen desplazamientos. Se mantiene configuración revisable.

Corrida de calibración, invertidos n=512: Insertion 33.7539 ms, Merge 1.4299 ms,
adaptativo 1.8152 ms. sorted de Python: 0.0424 ms. Se descarta sorted como
implementación por exigencia de algoritmos propios, no por lentitud ficticia.
Se midieron tamaños 8/16/32/64/128/512, ordenados/casi ordenados/invertidos/
aleatorios y criterios costosos. Ver las 456 filas de cada corrida 16/1.

**Límites:** coste de resolver fichas no es red medida; fichas sintéticas ya
disponibles. Umbrales no son universales; ruido, distribución y coste de
criterio pueden cambiar la elección óptima. Se excluye presentación.

## 4.11 Replay

**Problema/decisión:** reconstrucción reproducible desde cripta/versiones/
semilla y acciones con IDs estables. JSON Lines compartido con RegistroPartida,
creación exclusiva, append de acciones exitosas. Consultas, rechazos y
operaciones de sesión no aparecen; retroceso no borra registros previos.

Se valida todo el formato antes de ejecutar: campos/tipos, líneas vacías,
claves duplicadas, cabecera y acciones disponibles. Se verifica fuente o copia
local compatible; no se sustituuyen versiones arbitrariamente. Con un log
normal activo se crea un contexto distinto; sin vista/entrada, no se escriben
logs/puntajes. IDs JSON enteros permanecen enteros, no se confunden con texto.

**Operaciones/costos:** lectura/validación O(a) registros y memoria O(a) para
validar antes de ejecutar. Resolver ID cuesta O(entidades de sala/inventario).
Comparaciones de determinismo usan estado y getstate del RNG. USAR se resuelve
por id_instancia; actualmente solo el pergamino tiene ejecución sin tiempo.

**Alternativa medida:** parsear 512 registros en memoria: JSON Lines 2.0901 ms,
arreglo JSON 0.4837 ms. Arreglo es más rápido; se descarta como log porque
append requeriría modificar el cierre/reescribir, frente a una línea por
acción. Estos tiempos miden parser, NO replay completo ni red/motor.

**Límites:** falta inicialización desde esquema confirmado y el motor no
entrega intervalos completos/inversos de todas las acciones. El historial de
una partida normal todavía no puede reproducir todos los pergaminos después
de combate/eventos. Se reportan acciones imposibles y eventos pendientes; no
se silencian. No se declara replay completo ni determinismo de eventos aún
no implementados. Escribir log y modificar estado no es una transacción de
disco+motor: fallo posterior a acción se informa y bloquea siguientes acciones.
