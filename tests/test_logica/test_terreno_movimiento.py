"""T011: jugador, errante y rastreador cobran la salida atravesada."""

import pytest

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from logica.acciones import calcular_intervalo
from logica.inventario import Inventario
from logica.mapa_cripta import MapaCripta
from logica.motor_juego import MotorJuego


def _estado(costo=250, velocidad=100, jugador_en_destino=False):
    estado = EstadoPartida(17, "terreno")
    origen, destino, remota = Sala(1), Sala(2), Sala(3)
    puerta = Puerta("p-1-2", 2, "NORTE")
    puerta.abierta = True
    puerta.costo = costo
    origen.puertas.append(puerta)
    estado.mapa = MapaCripta()
    for sala in (origen, destino, remota):
        estado.mapa.agregar_sala(sala)
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, velocidad)
    estado.jugador.sala_actual = destino if jugador_en_destino else origen
    estado.inventario = Inventario(3)
    motor = MotorJuego()
    motor.iniciar(estado)
    return motor, estado, origen, destino, puerta


@pytest.mark.parametrize(("costo", "velocidad"), [(1, 250), (100, 100), (350, 200)])
def test_jugador_cobra_costo_de_salida_y_formula_comun(costo, velocidad):
    motor, estado, _, destino, _ = _estado(costo, velocidad)
    resultado = motor.ejecutar_accion(Accion("MOVER", direccion="NORTE"))
    assert resultado.exito
    assert resultado.costo == costo
    assert estado.jugador.sala_actual is destino
    assert estado.reloj == calcular_intervalo(costo, velocidad)


@pytest.mark.parametrize("comportamiento", ["errante", "rastreador"])
def test_enemigo_cobra_la_puerta_concreta(comportamiento):
    motor, estado, origen, destino, puerta = _estado(
        costo=275, velocidad=100, jugador_en_destino=True)
    # Evita la prioridad de ataque y deja una única vecina válida.
    estado.jugador.sala_actual = estado.mapa.obtener_sala(3)
    enemigo = Enemigo("e", "Enemigo", 20, 4, 1, 125, comportamiento)
    enemigo.activo = True
    enemigo.sala_actual = origen
    origen.enemigos.append(enemigo)
    if comportamiento == "rastreador":
        estado.registro_rastro.actualizar(destino, estado.reloj)

    notificaciones = motor._turno_enemigo(enemigo)

    assert enemigo.sala_actual is destino
    assert any(n["tipo"] == "ENEMIGO_MOVIDO" for n in notificaciones)
    evento = estado.agenda.buscar_por_actor_tipo("e", "ENEMIGO")[0]
    assert evento.tiempo == calcular_intervalo(puerta.costo, enemigo.velocidad)
