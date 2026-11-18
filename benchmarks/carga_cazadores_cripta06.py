"""Carga de §6.1 sobre cripta-06: sus 36 cazadores activos a la vez, individual frente a compartido.

Diagnóstico complementario de T051; NO es el recorrido legal que esa tarea exige. Usa los datos
reales de la cripta y el motor real, pero prepara la carga: activa a los 36 cazadores desde el inicio
y da al jugador vida muy alta para que no muera. Mide ``ejecutar_accion`` completo, sin red, sin
renderizado y sin línea de tiempo. Determinista por semilla.

    python -m benchmarks.carga_cazadores_cripta06
"""

import json
import logging
import random
import statistics
from time import perf_counter_ns

from dto.accion import Accion
from logica.motor_juego import MotorJuego
from benchmarks.linea_tiempo import (CacheCatalogo, FuenteOffline, InicializadorPartida,
                                     RUTA_FIXTURES)

CICLOS, CALENTAMIENTO, LIMITE_MS = 300, 3, 20
SALIDA = "benchmarks/resultados/carga_cazadores_cripta06.json"


def _medir(modo, compartir, semilla=7):
    estado, _ = InicializadorPartida(nombre="Carga")(
        "cripta-06", semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(256))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    if not compartir:
        motor.comportamientos.CAZADORES_SIN_COMPARTIR = 10 ** 9
    cazadores = [e for s in estado.mapa.obtener_salas() for e in s.enemigos
                 if e.comportamiento.lower() == "cazador"]
    estado.historial.iniciar_intervalo()
    for enemigo in cazadores:
        motor.activar_enemigo(enemigo)
    estado.historial.cerrar_intervalo()
    decidir, participantes = motor.comportamientos.decidir_accion, []

    def contar(enemigo, actual):
        if enemigo.comportamiento.lower() == "cazador":
            participantes.append(enemigo.id_actor)
        return decidir(enemigo, actual)

    motor.comportamientos.decidir_accion = contar
    azar = random.Random(semilla)
    tiempos, por_ciclo = [], []
    for _ in range(CICLOS + CALENTAMIENTO):
        abiertas = [p.direccion for p in estado.jugador.sala_actual.puertas if p.abierta]
        accion = (Accion("MOVER", direccion=abiertas[azar.randrange(len(abiertas))])
                  if modo == "moverse" and abiertas else Accion("ESPERAR"))
        participantes.clear()
        inicio = perf_counter_ns()
        resultado = motor.ejecutar_accion(accion)
        tiempos.append((perf_counter_ns() - inicio) / 1e6)
        por_ciclo.append(len(frozenset(participantes)))
        assert resultado.exito, resultado.mensaje
    tiempos, por_ciclo = tiempos[CALENTAMIENTO:], por_ciclo[CALENTAMIENTO:]
    orden = sorted(tiempos)
    return {
        "jugador": modo, "busqueda": "compartida" if compartir else "individual",
        "cazadores_activos": len(cazadores), "ciclos": len(tiempos),
        "ciclos_con_20_o_mas_participantes": sum(n >= 20 for n in por_ciclo),
        "participantes_mediana": statistics.median(por_ciclo),
        "mediana_ms": round(statistics.median(orden), 3),
        "p95_ms": round(orden[int(0.95 * len(orden))], 3), "maximo_ms": round(orden[-1], 3),
        "ciclos_de_20_ms_o_mas": sum(t >= LIMITE_MS for t in orden),
    }


def main():
    logging.disable(logging.CRITICAL)
    filas = [_medir(modo, compartir) for modo in ("esperar", "moverse")
             for compartir in (False, True)]
    informe = {"cripta": "cripta-06", "afirma_t051": False, "limite_ms": LIMITE_MS,
               "alcance": "carga preparada (36 activos y vida alta); no es un recorrido legal",
               "filas": filas}
    with open(SALIDA, "w", encoding="utf-8") as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=2)
    print(json.dumps(filas, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
