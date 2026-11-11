"""Mediciones de la línea de tiempo (spec 004).

T001 (riesgo R3 del plan): cuánto cuesta deshacer las transacciones de K acciones reales,
frente a la alternativa descartada de copiar el estado completo en cada consulta.

Todavía no existe el inverso de cada cambio (llega con T004), así que «rehacer» no se puede
medir aún. Se mide deshacer y se estima rehacer con el mismo costo, porque cada inverso es la
misma clase de operación sobre el mismo dato. La comprobación exacta de rehacer queda en las
pruebas de T003.

Uso: python -m benchmarks.linea_tiempo
"""

from __future__ import annotations

import copy
import json
import random
import statistics
from time import perf_counter_ns

from datos.fuente_offline import FuenteOffline
from dto.accion import Accion
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida

RUTA_FIXTURES = "tests/fixtures/api_real"
CRIPTA_REFERENCIA = "cripta-04"
VALORES_K = (10, 50, 200)
CALENTAMIENTO = 3
REPETICIONES = 15


def _partida_larga(acciones: int, semilla: int, cripta_id: str = CRIPTA_REFERENCIA):
    """Juega una partida real sin red y devuelve el estado y una transacción por acción.

    Las acciones son esperar o moverse por una salida abierta, elegidas con un azar propio
    sembrado (determinista). El historial del pergamino solo guarda 5 transacciones, así que
    se toma cada transacción recién cerrada antes de que la descarte.
    """
    fuente = FuenteOffline(RUTA_FIXTURES)
    estado, _ = InicializadorPartida(nombre="Benchmark")(
        cripta_id, semilla, fuente, CacheCatalogo(64))
    # Solo en la medición: vida muy alta para que la partida dure miles de acciones. No cambia
    # ninguna regla; los enemigos siguen atacando y generando cambios como en una partida real.
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    elegir = random.Random(semilla)
    transacciones = []
    while len(transacciones) < acciones and estado.partida_activa:
        sala = estado.jugador.sala_actual
        abiertas = [p.direccion for p in sala.puertas
                    if p.abierta and getattr(p, "destino_sala", None) is not None
                    and getattr(p.destino_sala, "contenido_cargado", True)]
        if abiertas and elegir.random() < 0.6:
            accion = Accion("MOVER", direccion=abiertas[elegir.randrange(len(abiertas))])
        else:
            accion = Accion("ESPERAR")
        resultado = motor.ejecutar_accion(accion)
        if not resultado.exito:
            resultado = motor.ejecutar_accion(Accion("ESPERAR"))
            if not resultado.exito:
                break
        transacciones.append(estado.historial._intervalos.primero.valor)
    return estado, transacciones


def _huella(estado) -> tuple:
    """Resumen comparable del estado observable (no es una copia del estado)."""
    jugador = estado.jugador
    enemigos = []
    for sala in estado.mapa.obtener_salas():
        for enemigo in sala.enemigos:
            enemigos.append((enemigo.id_actor, enemigo.vida, sala.id_sala, enemigo.activo))
    inventario = [o.id_instancia for o in estado.inventario.obtener_objetos()]
    return (estado.reloj, estado.acciones_ejecutadas, jugador.vida,
            jugador.sala_actual.id_sala, tuple(enemigos), tuple(inventario))


def _deshacer(estado, transacciones) -> int:
    """Deshace las transacciones de la más reciente a la más antigua, cambio por cambio.

    No usa TransaccionAccion.revertir porque esa operación vacía la transacción; la línea
    de tiempo necesita conservarla (data-model: deshacer sin vaciar).
    """
    cambios = 0
    for transaccion in reversed(transacciones):
        nodo = transaccion._cambios.primero
        while nodo is not None:
            nodo.valor.deshacer(estado)
            cambios += 1
            nodo = nodo.siguiente
    return cambios


def _ms(valores_ns) -> dict:
    ordenados = list(valores_ns)
    return {"mediana_ms": statistics.median(ordenados) / 1e6,
            "maximo_ms": max(ordenados) / 1e6}


def medir_riesgo_r3(acciones: int = 600, semilla: int = 7) -> dict:
    """T001: deshacer K transacciones reales frente a copiar el estado completo."""
    estado, transacciones = _partida_larga(acciones, semilla)
    resultados = {"cripta": CRIPTA_REFERENCIA, "semilla": semilla,
                  "acciones_jugadas": len(transacciones),
                  "salas": len(estado.mapa.obtener_salas()), "por_k": []}
    for k in VALORES_K:
        if k > len(transacciones):
            resultados["por_k"].append({"k": k, "omitido": "la partida terminó antes"})
            continue
        ventana = transacciones[-k:]
        tiempos_deshacer, tiempos_copia, cantidad = [], [], 0
        for repeticion in range(CALENTAMIENTO + REPETICIONES):
            # Preparación fuera del cronómetro: una copia conjunta, como un punto de control (R2).
            base_estado, base_ventana = copy.deepcopy((estado, ventana))
            inicio = perf_counter_ns()
            cantidad = _deshacer(base_estado, base_ventana)
            fin = perf_counter_ns()
            inicio_copia = perf_counter_ns()
            copy.deepcopy((estado, ventana))
            fin_copia = perf_counter_ns()
            if repeticion >= CALENTAMIENTO:
                tiempos_deshacer.append(fin - inicio)
                tiempos_copia.append(fin_copia - inicio_copia)
        deshacer = _ms(tiempos_deshacer)
        resultados["por_k"].append({
            "k": k,
            "cambios_deshechos": cantidad,
            "deshacer": deshacer,
            "deshacer_y_rehacer_estimado_ms": 2 * deshacer["maximo_ms"],
            "copia_completa_alternativa": _ms(tiempos_copia),
        })
    resultados["comprobacion_deshacer"] = _comprobar_deshacer(semilla)
    return resultados


def _comprobar_deshacer(semilla: int, acciones: int = 60, k: int = 20) -> dict:
    """Deshacer K transacciones sobre una copia conjunta da el estado de K acciones antes."""
    # La misma semilla reproduce la misma partida: el prefijo de N − K acciones es el estado
    # esperado después de deshacer las últimas K.
    estado, transacciones = _partida_larga(acciones - k, semilla)
    esperado = _huella(estado)
    estado_final, todas = _partida_larga(acciones, semilla)
    if len(transacciones) != acciones - k or len(todas) != acciones:
        return {"k": k, "coincide": None, "motivo": "la partida terminó antes"}
    antes = _huella(estado_final)
    copia_estado, copia_ventana = copy.deepcopy((estado_final, todas[-k:]))
    _deshacer(copia_estado, copia_ventana)
    return {"k": k, "coincide": _huella(copia_estado) == esperado,
            "la_partida_original_no_cambio": _huella(estado_final) == antes}


# --- T002 y T041 a T045: mediciones conectadas a --bench (spec 004, FR-024 a FR-027) -------

import io
import os
import pickle
import tempfile
import tracemalloc

from logica.linea_tiempo import LineaTiempo

# K pedido con --checkpoint-cada; main.py lo fija antes de --bench (T031, T046).
K_CONFIGURADO = None
SIN_PUNTOS = 10 ** 9  # «sin puntos de control»: solo el punto inicial
UMBRAL_HISTORIA_MS = 50
UMBRAL_CICLO_MS = 20


class _PicklerJuego(pickle.Pickler):
    """Huella del estado del juego, igual que la de las pruebas de la línea de tiempo.

    Deja fuera lo que no es estado de la partida (historial del pergamino, cachés, línea) y
    compara por contenido la agenda, los eventos, los índices y el inventario, cuya forma
    interna cambia al deshacer y rehacer sin cambiar el juego.
    """

    FUERA = ("HistorialReversible", "TransaccionAccion", "CacheCatalogo", "LineaTiempo",
             "CargadorContenido", "_LineaMedida", "_Reparto")

    def persistent_id(self, obj):
        nombre = type(obj).__name__
        if nombre in self.FUERA:
            return ("FUERA", nombre)
        if nombre == "Inventario":
            return ("INVENTARIO", tuple((c, v) for c, v in vars(obj).items()
                                        if c not in ("_orden_frente", "historial_linea")))
        if nombre == "Evento":
            return ("EVENTO", tuple((c, v) for c, v in vars(obj).items()
                                    if c != "_indice_monticulo"))
        if nombre == "TablaHashImpl":
            claves = list(obj.claves())
            claves.sort(key=repr)
            return ("TABLA", tuple((c, obj.obtener(c)) for c in claves))
        if hasattr(obj, "recorrer") and hasattr(obj, "_monticulo"):
            eventos = [(e.id_evento, e.tiempo, e.secuencia, e.tipo, e.destinatario_id)
                       for e in obj.recorrer()]
            eventos.sort()
            return ("AGENDA", tuple(eventos))
        return None


def huella_juego(estado) -> bytes:
    flujo = io.BytesIO()
    _PicklerJuego(flujo).dump(estado)
    return flujo.getvalue()


class _LineaMedida(LineaTiempo):
    """La línea real, midiendo el tiempo de cada punto de control y su memoria por muestreo.

    El tiempo se mide sin tracemalloc, que hace la copia varias veces más lenta. La memoria se
    mide con tracemalloc sobre una copia aparte de 1 de cada ``MUESTREO`` puntos (que se
    descarta), y el total se estima multiplicando el promedio por la cantidad de puntos.
    """

    MUESTREO = 10

    def __init__(self, estado, k):
        self.bytes_muestras = []
        self.ns_puntos = []
        super().__init__(estado, k)

    @property
    def bytes_puntos(self):
        if not self.bytes_muestras:
            return 0
        return sum(self.bytes_muestras) / len(self.bytes_muestras) * len(self.puntos)

    def _punto_control(self, accion, ventana):
        inicio = perf_counter_ns()
        punto = super()._punto_control(accion, ventana)
        self.ns_puntos.append(perf_counter_ns() - inicio)
        if (len(self.ns_puntos) - 1) % self.MUESTREO == 0:
            tracemalloc.start()
            antes = tracemalloc.get_traced_memory()[0]
            muestra = super()._punto_control(accion, ventana)
            self.bytes_muestras.append(tracemalloc.get_traced_memory()[0] - antes)
            tracemalloc.stop()
            del muestra
        return punto


class _Reparto:
    """Conecta varias líneas al mismo historial: una sola partida para todos los K."""

    def __init__(self, lineas):
        self.lineas = lineas

    def registrar_accion(self, transaccion):
        for linea in self.lineas:
            linea.registrar_accion(transaccion)

    def recortar(self, cantidad):
        for linea in self.lineas:
            linea.recortar(cantidad)

    def anotar_solo_linea(self, cambio):
        for linea in self.lineas:
            linea.anotar_solo_linea(cambio)


def partida_sintetica(acciones, semilla=7, valores_k=VALORES_K, cripta_id=CRIPTA_REFERENCIA):
    """T002: partida larga determinista por semilla, sin red, con una línea por cada K.

    Usa la cripta offline más grande de los fixtures con todo su contenido cargado. Las
    acciones (moverse por una salida abierta o esperar) salen de un azar propio sembrado. El
    jugador tiene vida muy alta solo aquí, para que la partida dure miles de acciones.
    """
    fuente = FuenteOffline(RUTA_FIXTURES)
    estado, _ = InicializadorPartida(nombre="Benchmark")(
        cripta_id, semilla, fuente, CacheCatalogo(64))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    lineas = [_LineaMedida(estado, k) for k in valores_k]
    estado.historial.vincular_linea(_Reparto(lineas))
    elegir = random.Random(semilla)
    jugadas, ns_accion = [], []
    while len(jugadas) < acciones and estado.partida_activa:
        sala = estado.jugador.sala_actual
        abiertas = [p.direccion for p in sala.puertas
                    if p.abierta and getattr(p.destino_sala, "contenido_cargado", True)]
        if abiertas and elegir.random() < 0.6:
            accion = Accion("MOVER", direccion=abiertas[elegir.randrange(len(abiertas))])
        else:
            accion = Accion("ESPERAR")
        inicio = perf_counter_ns()
        resultado = motor.ejecutar_accion(accion)
        if not resultado.exito:
            accion = Accion("ESPERAR")
            resultado = motor.ejecutar_accion(accion)
            if not resultado.exito:
                break
        ns_accion.append(perf_counter_ns() - inicio)
        jugadas.append(accion)
    return estado, lineas, jugadas, ns_accion


def _ms(valor_ns):
    return round(valor_ns / 1e6, 3)


def _resumen_ms(valores_ns):
    ordenados = list(valores_ns)
    ordenados.sort()
    p95 = ordenados[min(len(ordenados) - 1, int(0.95 * len(ordenados)))]
    return {"mediana_ms": _ms(statistics.median(ordenados)), "p95_ms": _ms(p95),
            "maximo_ms": _ms(ordenados[-1]), "muestras": len(ordenados)}


def _objetivos(linea, cantidad, semilla):
    """Acciones a consultar: el peor caso (justo después de un punto) y otras al azar."""
    n = linea.cantidad_acciones()
    elegir = random.Random(semilla)
    peores = [m + 1 for m in range(0, n, linea.k)][1:6] if linea.k <= n else []
    al_azar = [elegir.randint(1, n + 1) for _ in range(cantidad)]
    return peores + al_azar


def medir_consultas(lineas, consultas=40, semilla=3):
    """T041: tiempo de historia #k (peor caso y mediana) y memoria retenida, por cada K."""
    from controller.resumen_historia import lineas_resumen

    def construir(estado):
        return lineas_resumen(estado, "x")

    filas = []
    for linea in lineas:
        cuantas = 5 if linea.k == SIN_PUNTOS else consultas
        tiempos, tocadas = [], 0
        for k in _objetivos(linea, cuantas, semilla)[:cuantas + 5]:
            linea.consultar_accion(k, construir)  # calentamiento de la misma consulta
            inicio = perf_counter_ns()
            linea.consultar_accion(k, construir)
            tiempos.append(perf_counter_ns() - inicio)
            tocadas = max(tocadas, linea.ultimas_transacciones_tocadas)
        resumen = _resumen_ms(tiempos)
        filas.append({
            "medicion": "linea_tiempo_historia",
            "k": "sin puntos de control" if linea.k == SIN_PUNTOS else linea.k,
            "acciones": linea.cantidad_acciones(),
            "puntos_de_control": len(linea.puntos),
            "memoria_puntos_mb_estimada": round(linea.bytes_puntos / 2 ** 20, 2),
            "memoria_por_punto_kb": round(linea.bytes_puntos / 1024 / len(linea.puntos), 1),
            "max_transacciones_por_consulta": tocadas,
            **resumen,
            "cumple_50ms": resumen["maximo_ms"] < UMBRAL_HISTORIA_MS,
            "crear_punto_mediana_ms": (_ms(statistics.median(linea.ns_puntos))
                                       if linea.ns_puntos else None),
        })
    return filas


def medir_costo_punto(lineas, ns_accion):
    """Riesgo de T001: la acción que crea un punto de control frente a los 20 ms por ciclo.

    Varias líneas comparten la partida, así que se suma el tiempo de una acción en la que
    ninguna crea un punto y el tiempo de crear un punto de cada K por separado.
    """
    paso = 1
    for linea in lineas:
        if linea.k != SIN_PUNTOS:
            paso = linea.k if paso == 1 else min(paso, linea.k)
    normales = [ns for m, ns in enumerate(ns_accion, 1) if m % paso]
    base = statistics.median(normales) if normales else 0
    filas = [{"medicion": "linea_tiempo_accion_sin_punto", **_resumen_ms(normales)}]
    for linea in lineas:
        if linea.k == SIN_PUNTOS or not linea.ns_puntos:
            continue
        punto = _resumen_ms(linea.ns_puntos)
        filas.append({"medicion": "linea_tiempo_accion_con_punto", "k": linea.k,
                      "crear_punto": punto,
                      "accion_con_punto_estimada_mediana_ms": round(_ms(base) + punto["mediana_ms"], 3),
                      "umbral_ciclo_ms": UMBRAL_CICLO_MS,
                      "cumple_20ms": _ms(base) + punto["maximo_ms"] < UMBRAL_CICLO_MS})
    return filas


def _reconectar_catalogo(copia, vivo):
    """Re-simular necesita las fichas: las copias no llevan el catálogo (FichaResoluble).

    El catálogo es infraestructura (caché y disco) y se excluye a propósito al copiar. Para la
    alternativa de re-simular hay que volver a conectarlo; ``historia`` no lo necesita, porque
    los nombres salen del catálogo de la partida.
    """
    catalogo = None
    for sala in vivo.mapa.obtener_salas():
        for entidad in list(sala.enemigos) + list(sala.objetos):
            catalogo = catalogo or vars(entidad).get("_catalogo_ficha")
    if catalogo is None:
        return
    entidades = [copia.jugador] + list(copia.inventario.obtener_objetos())
    for sala in copia.mapa.obtener_salas():
        entidades += list(sala.objetos) + list(sala.trampas)
        for enemigo in sala.enemigos:
            entidades.append(enemigo)
            entidades += list(enemigo.botin_preparado)
    for entidad in entidades:
        if hasattr(entidad, "conectar_catalogo") and vars(entidad).get("_ficha") is None:
            entidad.conectar_catalogo(catalogo)


def medir_adelante_atras(estado, lineas, jugadas, consultas=8, semilla=5):
    """T042 (FR-020, FR-024): reconstruir hacia atrás frente a re-simular hacia adelante.

    Re-simular solo existe aquí: copia el punto de control anterior (con su azar), vuelve a
    ejecutar las acciones con un motor nuevo y comprueba que llega al mismo estado.
    """
    filas = []
    for linea in lineas:
        if linea.k == SIN_PUNTOS:
            continue
        elegir = random.Random(semilla)
        atras, adelante, iguales = [], [], True
        for _ in range(consultas):
            k = elegir.randint(2, linea.cantidad_acciones())
            inicio = perf_counter_ns()
            esperado = linea.consultar_accion(k, huella_juego)
            atras.append(perf_counter_ns() - inicio)
            j = (k - 1) // linea.k  # punto de control anterior o igual a k − 1
            punto = linea.puntos[j]
            copia, _ = copy.deepcopy((punto.estado, punto.transacciones))
            _reconectar_catalogo(copia, estado)
            inicio = perf_counter_ns()
            motor = MotorJuego()
            motor.estado = copia
            for accion in jugadas[punto.accion:k - 1]:
                motor.ejecutar_accion(accion)
            adelante.append(perf_counter_ns() - inicio)
            iguales = iguales and huella_juego(copia) == esperado
        filas.append({"medicion": "linea_tiempo_adelante_vs_atras", "k": linea.k,
                      "hacia_atras": _resumen_ms(atras), "re_simular": _resumen_ms(adelante),
                      "mismo_estado": iguales})
    return filas


def medir_retroceso(estado, repeticiones=10):
    """T043 (FR-025): un retroceso de punta a punta frente a guardar y restaurar copias."""
    deshacer, copiar = [], []
    for _ in range(repeticiones):
        copia = copy.deepcopy(estado)
        inicio = perf_counter_ns()
        copia.historial.deshacer_ultimo(copia)
        deshacer.append(perf_counter_ns() - inicio)
        inicio = perf_counter_ns()
        copy.deepcopy(estado)  # lo que costaría guardar una copia completa por acción
        copiar.append(perf_counter_ns() - inicio)
    return [{"medicion": "retroceso_punta_a_punta",
             "incluye": "reloj, agenda, rastro, puertas, trampas, inventario y azar",
             "deshacer_transaccion": _resumen_ms(deshacer),
             "alternativa_copia_completa_por_accion": _resumen_ms(copiar)}]


def medir_replay(acciones=60, repeticiones=5, semilla=7):
    """T044 (FR-026): reproducción completa de partida.log y rechazo por versión incompatible."""
    from controller.ejecutor_replay import EjecutorReplay
    from service.juego_service import JuegoService

    def servicio():
        nuevo = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(RUTA_FIXTURES),
                             cache=CacheCatalogo(25))
        nuevo.conectar_inicializador(InicializadorPartida())
        return nuevo

    import contextlib

    with tempfile.TemporaryDirectory() as carpeta, contextlib.redirect_stdout(io.StringIO()):
        # El replay avisa por pantalla al buscar una copia local del log incompatible; aquí
        # se silencia para no mezclar texto con la salida JSON de --bench.
        original = servicio()
        original.configurar_semilla(semilla)
        estado = original.iniciar_partida("cripta-01")
        ruta = os.path.join(carpeta, "partida.log")
        original.iniciar_registro(ruta)
        elegir = random.Random(semilla)
        for _ in range(acciones):
            if not estado.partida_activa:
                break
            tipo = "ESPERAR" if elegir.random() < 0.7 else "MOVER"
            direcciones = [p.direccion for p in estado.jugador.sala_actual.puertas if p.abierta]
            if tipo == "MOVER" and direcciones:
                accion = original.resolver_accion("MOVER", direccion=direcciones[0])
            else:
                accion = original.resolver_accion("ESPERAR")
            original.ejecutar_accion(accion)
        with open(ruta, encoding="utf-8") as archivo:
            lineas = archivo.read().split("\n")
        lineas[0] = lineas[0].replace('"version_cripta": "', '"version_cripta": "otra-')
        incompatible = os.path.join(carpeta, "incompatible.log")
        with open(incompatible, "w", encoding="utf-8") as archivo:
            archivo.write("\n".join(lineas))
        completo, rechazo, rechazado = [], [], True
        for _ in range(repeticiones):
            replay = EjecutorReplay()
            replay.conectar_servicio(servicio())
            inicio = perf_counter_ns()
            replay.reproducir(ruta)
            completo.append(perf_counter_ns() - inicio)
            replay = EjecutorReplay()
            replay.conectar_servicio(servicio())
            inicio = perf_counter_ns()
            try:
                replay.reproducir(incompatible)
                rechazado = False
            except ValueError:
                pass
            rechazo.append(perf_counter_ns() - inicio)
    return [{"medicion": "replay_completo", "acciones_en_log": len(lineas) - 2,
             **_resumen_ms(completo)},
            {"medicion": "replay_version_incompatible", "rechazado": rechazado,
             **_resumen_ms(rechazo)}]


def medir_inventario(repeticiones=15, semilla=7):
    """T045 (FR-027): vista ordenada sin alterar el orden real, y rechazo con el inventario lleno."""
    from dto.objeto_instancia import ObjetoInstancia
    from logica.servicio_inventario import ServicioInventario
    from service.juego_service import JuegoService

    servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(RUTA_FIXTURES),
                            cache=CacheCatalogo(64))
    servicio.conectar_inicializador(InicializadorPartida())
    servicio.configurar_semilla(semilla)
    estado = servicio.iniciar_partida("cripta-04")
    inventario = estado.inventario
    modelos = [o for s in estado.mapa.obtener_salas() for o in s.objetos]
    i = 0
    while not inventario.esta_lleno() and modelos:
        modelo = modelos[i % len(modelos)]
        objeto = ObjetoInstancia(f"bench-{i}", modelo.tipo_ficha_id)
        catalogo = vars(modelo).get("_catalogo_ficha")
        if catalogo is not None:
            objeto.conectar_catalogo(catalogo)
        else:
            objeto.ficha = modelo.ficha
        objeto.ubicacion = "inventario"
        inventario.agregar(objeto)
        i += 1
    real = [o.id_instancia for o in inventario.obtener_objetos()]
    filas = []
    for criterio in ("peso", "valor", "nombre"):
        tiempos = []
        for _ in range(repeticiones + 1):
            inicio = perf_counter_ns()
            servicio.consultar_inventario(criterio)
            tiempos.append(perf_counter_ns() - inicio)
        filas.append({"medicion": "inventario_vista_ordenada", "criterio": criterio,
                      "objetos": len(real), **_resumen_ms(tiempos[1:]),
                      "orden_real_intacto": [o.id_instancia for o in inventario.obtener_objetos()] == real})
    sala = estado.jugador.sala_actual
    extra = ObjetoInstancia("bench-extra", modelos[0].tipo_ficha_id)
    extra.ficha = modelos[0].ficha
    extra.ubicacion = sala.id_sala
    sala.objetos.append(extra)
    tiempos, rechazado = [], True
    for _ in range(repeticiones + 1):
        inicio = perf_counter_ns()
        resultado = ServicioInventario(inventario).recoger(extra, sala)
        tiempos.append(perf_counter_ns() - inicio)
        rechazado = rechazado and not resultado.exito
    sala.objetos.remove(extra)
    filas.append({"medicion": "inventario_recoger_lleno", "objetos": len(real),
                  "rechazado": rechazado, **_resumen_ms(tiempos[1:])})
    return filas


def medir_linea_tiempo(repeticiones=15, tamanos=(), acciones=5000):
    """Proveedor para ``main.py --bench`` (T046): todas las filas de la spec 004."""
    valores = list(VALORES_K)
    if K_CONFIGURADO is not None and K_CONFIGURADO not in valores:
        valores.append(K_CONFIGURADO)
    estado, lineas, jugadas, ns_accion = partida_sintetica(acciones, valores_k=tuple(valores) + (SIN_PUNTOS,))
    filas = medir_consultas(lineas)
    filas += medir_costo_punto(lineas, ns_accion)
    filas += medir_adelante_atras(estado, lineas, jugadas)
    filas += medir_retroceso(estado, repeticiones=min(repeticiones, 10))
    filas += medir_replay()
    filas += medir_inventario(repeticiones=repeticiones)
    return filas


PROVEEDORES = (medir_linea_tiempo,)


if __name__ == "__main__":
    print(json.dumps(medir_riesgo_r3(), ensure_ascii=False, indent=2))
