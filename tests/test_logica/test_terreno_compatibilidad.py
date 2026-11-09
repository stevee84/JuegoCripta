"""T012: compatibilidad de acciones heredadas y rechazos de movimiento."""

import pytest

from dto.accion import Accion
from dto.actor import Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from logica.acciones import calcular_intervalo, costo_base
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


@pytest.mark.parametrize(("tipo", "costo"), [
    ("ATACAR", 100),
    ("ESPERAR", 100),
    ("USAR", 50),
    ("EQUIPAR", 50),
    ("RECOGER", 25),
    ("SOLTAR", 25),
    ("ABRIR", 50),
])
@pytest.mark.parametrize("velocidad", [50, 100, 250])
def test_acciones_distintas_de_mover_conservan_costo_e_intervalo(
        tipo, costo, velocidad):
    """AC-003: terreno no cambia los costos heredados ni su fórmula."""
    assert costo_base(tipo) == costo
    assert calcular_intervalo(costo_base(tipo), velocidad) == max(
        1, costo * 100 // velocidad)


def _partida_movimiento():
    estado = EstadoPartida(23, "rechazo-terreno")
    estado.mapa = MapaCripta()
    origen, destino = Sala(1), Sala(2)
    puerta = Puerta("p-1-2", 2, "NORTE")
    puerta.abierta = True
    origen.puertas.append(puerta)
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(destino)
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = origen
    estado.inventario = Inventario(3)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, origen, destino, puerta


def _huella_rechazo(estado, puerta):
    eventos = tuple(sorted(
        (evento.id_evento, evento.tiempo, evento.secuencia, evento.tipo,
         evento.destinatario_id, id(evento.datos))
        for evento in estado.agenda.recorrer()
    ))
    return (
        estado.reloj,
        estado.secuencia,
        estado.acciones_ejecutadas,
        estado.jugador.sala_actual,
        estado.jugador.vida,
        estado.jugador.velocidad,
        estado.jugador_disponible,
        estado.evento_decision_id,
        puerta.abierta,
        puerta.destino_sala_id,
        puerta.destino_sala,
        puerta.evento_cierre_id,
        puerta.evento_cierre,
        eventos,
        estado.agenda._secuencia,
        estado.historial.get_cantidad(),
        estado.historial.hay_intervalo_abierto(),
        estado.azar.getstate(),
    )


@pytest.mark.parametrize("motivo", ["sin_salida", "cerrada", "sin_destino"])
def test_movimiento_rechazado_no_muta_actor_reloj_puerta_agenda_ni_historial(
        motivo):
    """FR-017: validar precede a cualquier mutación o consumo temporal."""
    motor, estado, origen, _, puerta = _partida_movimiento()
    direccion = "NORTE"
    if motivo == "sin_salida":
        direccion = "SUR"
    elif motivo == "cerrada":
        puerta.abierta = False
    else:
        puerta.destino_sala_id = 999

    antes = _huella_rechazo(estado, puerta)
    resultado = motor.ejecutar_accion(
        Accion("MOVER", direccion=direccion))

    assert not resultado.exito
    assert resultado.costo == 0
    assert resultado.cambios == []
    assert estado.jugador.sala_actual is origen
    assert _huella_rechazo(estado, puerta) == antes
