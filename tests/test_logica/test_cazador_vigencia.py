"""T030: vigencia del cazador frente a un oráculo nuevo en cada decisión."""

import pytest

from dto.accion import Accion
from dto.actor import Enemigo
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.motor_juego import MotorJuego
from logica.mutaciones import agregar, atributo, quitar_identidad

from tests.test_logica._cazador_us3 import (
    accion_independiente,
    conectar,
    estado_empates,
)


def _comparar(estado, cazador):
    esperado = accion_independiente(estado, cazador)
    obtenido = ComportamientoEnemigos().decidir_accion(cazador, estado)
    assert obtenido == esperado
    return obtenido


def test_ac_b05_y_ac_016_apertura_y_cierre_cambian_la_decision_vigente():
    estado, cazador, salas = estado_empates()
    puerta_directa = conectar(
        salas[4], salas[1], 1, "p-4-1", abierta=False)

    assert _comparar(estado, cazador) == {"tipo": "MOVER", "destino": 2}
    puerta_directa.abierta = True
    assert _comparar(estado, cazador) == {"tipo": "MOVER", "destino": 1}
    puerta_directa.abierta = False
    assert _comparar(estado, cazador) == {"tipo": "MOVER", "destino": 2}


def test_ac_b05_cierre_automatico_real_se_observa_en_la_siguiente_consulta():
    estado, cazador, salas = estado_empates()
    puerta_directa = conectar(salas[4], salas[1], 1, "auto", abierta=True)
    puerta_directa.cierre_automatico = 25
    motor = MotorJuego()
    motor.iniciar(estado)
    evento = motor._programar(25, "CERRAR_PUERTA", puerta_directa.id_puerta,
                              puerta_directa)
    puerta_directa.evento_cierre_id = evento.id_evento
    puerta_directa.evento_cierre = evento

    assert _comparar(estado, cazador)["destino"] == 1
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    assert not puerta_directa.abierta
    assert _comparar(estado, cazador)["destino"] == 2


def test_ac_008_movimiento_real_del_jugador_actualiza_el_objetivo():
    estado, cazador, salas = estado_empates()
    regreso = conectar(salas[1], salas[10], 7, "jugador-1-10")
    motor = MotorJuego()
    motor.iniciar(estado)

    assert _comparar(estado, cazador)["destino"] == 2
    assert motor.ejecutar_accion(
        Accion("MOVER", direccion=regreso.direccion)).exito
    assert estado.jugador.sala_actual is salas[10]
    assert _comparar(estado, cazador)["destino"] == 10


def test_ac_017_velocidad_reprograma_agenda_sin_cambiar_la_ruta():
    estado, cazador, _ = estado_empates()
    motor = MotorJuego()
    motor.iniciar(estado)
    evento = estado.agenda.crear_evento(
        200, "ENEMIGO", cazador.id_actor, cazador)
    estado.historial.iniciar_intervalo()
    antes = _comparar(estado, cazador)
    motor.cambiar_velocidad(cazador, 250)
    estado.historial.cerrar_intervalo()

    assert evento.tiempo == 80
    assert evento.secuencia > 0
    assert _comparar(estado, cazador) == antes
    assert estado.historial.deshacer_ultimo(estado)
    assert (cazador.velocidad, evento.tiempo, evento.secuencia) == (100, 200, 0)
    assert _comparar(estado, cazador) == antes


@pytest.mark.parametrize("cambio", ["mover", "matar"])
def test_ac_018_otro_actor_no_invalida_ni_altera_la_decision(cambio):
    estado, cazador, salas = estado_empates()
    otro = Enemigo("otro", "Otro", 10, 1, 0, 100, "guardian")
    otro.sala_actual = salas[10]
    salas[10].enemigos.append(otro)
    estado.mapa.vincular_salidas()
    motor = MotorJuego()
    motor.iniciar(estado)
    esperada = _comparar(estado, cazador)

    estado.historial.iniciar_intervalo()
    if cambio == "mover":
        quitar_identidad(estado, salas[10].enemigos, otro)
        agregar(estado, salas[2].enemigos, otro)
        atributo(estado, otro, "sala_actual", salas[2])
    else:
        atributo(estado, otro, "vida", 0)
        motor.combate.procesar_muerte(otro, estado)
    estado.historial.cerrar_intervalo()

    assert _comparar(estado, cazador) == esperada
