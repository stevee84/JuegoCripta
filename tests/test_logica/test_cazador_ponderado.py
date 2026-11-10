"""T020: prioridad de ataque y espera del cazador."""

import pytest

from dto.actor import Enemigo, Jugador
from dto.estado_partida import EstadoPartida
from dto.sala import Puerta, Sala
from logica.comportamiento_enemigos import ComportamientoEnemigos
from logica.mapa_cripta import MapaCripta


def _estado(misma_sala=False, rango=0):
    estado = EstadoPartida(31)
    origen, objetivo = Sala(1), Sala(2)
    puerta = Puerta("p", 2, "NORTE")
    puerta.abierta = True
    puerta.costo = 10
    origen.puertas.append(puerta)
    estado.mapa = MapaCripta()
    estado.mapa.agregar_sala(origen)
    estado.mapa.agregar_sala(objetivo)
    estado.mapa.vincular_salidas()
    estado.jugador = Jugador("j", "Jugador", 100, 10, 5, 100)
    estado.jugador.sala_actual = origen if misma_sala else objetivo
    cazador = Enemigo("c", "Cazador", 30, 8, 2, 100, "cazador")
    cazador.rango = rango
    cazador.sala_actual = origen
    return estado, cazador


def test_compartir_sala_ataca_antes_del_buscador_incluso_con_rango_cero(
        monkeypatch):
    estado, cazador = _estado(misma_sala=True, rango=0)

    def prohibido(*_args, **_kwargs):
        pytest.fail("Se invocó el buscador antes de priorizar ATACAR.")

    monkeypatch.setattr(
        "logica.comportamiento_enemigos.proximo_paso", prohibido)
    assert ComportamientoEnemigos().decidir_accion(cazador, estado) == {
        "tipo": "ATACAR", "objetivo": "j"}


def test_sin_ruta_dentro_del_rango_espera():
    estado, cazador = _estado(rango=9)
    assert ComportamientoEnemigos().decidir_accion(cazador, estado) == {
        "tipo": "ESPERAR"}
