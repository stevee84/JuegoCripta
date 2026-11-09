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


if __name__ == "__main__":
    print(json.dumps(medir_riesgo_r3(), ensure_ascii=False, indent=2))
