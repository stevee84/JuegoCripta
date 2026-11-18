"""P2 §3.2, §5.1 y §5.2 (AC-013, PR-001): compartir la búsqueda no cambia ninguna decisión."""

import random

from dto.accion import Accion
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.motor_juego import MotorJuego
from logica.rutas_compartidas import DistanciasAlJugador
from logica.rutas_ponderadas import VistaMapaCazador, proximo_paso
from benchmarks.linea_tiempo import (CacheCatalogo, FuenteOffline, InicializadorPartida,
                                     RUTA_FIXTURES)


def _partida(semilla=7):
    estado, _ = InicializadorPartida(nombre="Prueba")(
        "cripta-06", semilla, FuenteOffline(RUTA_FIXTURES), CacheCatalogo(256))
    estado.jugador.vida_max = estado.jugador.vida = 10 ** 9
    motor = MotorJuego()
    motor.iniciar(estado)
    return estado, motor


def _cazadores(estado):
    return [e for s in estado.mapa.obtener_salas() for e in s.enemigos
            if e.comportamiento.lower() == "cazador"]


def _desde_cero(estado, enemigo):
    return proximo_paso(VistaMapaCazador(estado.mapa), enemigo.sala_actual.id_sala,
                        estado.jugador.sala_actual.id_sala, enemigo.rango).primera_vecina_id


def test_pr001_equivale_a_calcular_desde_cero_con_puertas_que_cambian():
    estado, _ = _partida()
    azar = random.Random(11)
    compartidas = DistanciasAlJugador()
    salas = list(estado.mapa.obtener_salas())
    puertas = [p for s in salas for p in s.puertas]
    cazadores = _cazadores(estado)
    for _ in range(120):
        for puerta in azar.sample(puertas, 12):
            puerta.abierta = not puerta.abierta
        estado.jugador.sala_actual = azar.choice(salas)
        objetivo = estado.jugador.sala_actual.id_sala
        for enemigo in cazadores:
            if enemigo.sala_actual.id_sala == objetivo:
                continue
            assert compartidas.primera_vecina(estado.mapa, enemigo.sala_actual, objetivo,
                                              enemigo.rango) == _desde_cero(estado, enemigo)


def test_pr001_una_puerta_cerrada_invalida_la_tabla_en_la_consulta_siguiente():
    estado, _ = _partida()
    compartidas = DistanciasAlJugador()
    objetivo = estado.jugador.sala_actual.id_sala
    enemigo = max(_cazadores(estado), key=lambda e: e.rango)
    enemigo.rango = 10 ** 6
    primera = compartidas.primera_vecina(estado.mapa, enemigo.sala_actual, objetivo, enemigo.rango)
    assert primera == _desde_cero(estado, enemigo)
    for puerta in enemigo.sala_actual.puertas:
        if puerta.destino_sala_id == primera:
            puerta.abierta = False
    assert compartidas.primera_vecina(estado.mapa, enemigo.sala_actual, objetivo,
                                      enemigo.rango) == _desde_cero(estado, enemigo)


def test_pr001_la_partida_con_36_cazadores_decide_igual_que_desde_cero():
    estado, motor = _partida()
    estado.historial.iniciar_intervalo()
    for enemigo in _cazadores(estado):
        motor.activar_enemigo(enemigo)
    estado.historial.cerrar_intervalo()
    original = motor.comportamientos._accion_cazador
    revisadas = []

    def comparar(enemigo, actual):
        accion = original(enemigo, actual)
        assert accion.get("destino") == _desde_cero(actual, enemigo)
        revisadas.append(enemigo.id_actor)
        return accion

    motor.comportamientos._accion_cazador = comparar
    azar = random.Random(3)
    for _ in range(40):
        abiertas = [p.direccion for p in estado.jugador.sala_actual.puertas if p.abierta]
        accion = (Accion("MOVER", direccion=azar.choice(abiertas))
                  if abiertas and azar.random() < 0.5 else Accion("ESPERAR"))
        assert motor.ejecutar_accion(accion).exito
    assert len(revisadas) > 40 * ComportamientoEnemigos.CAZADORES_SIN_COMPARTIR
