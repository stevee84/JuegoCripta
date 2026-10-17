import pytest

from dto.accion import Accion
from dto.actor import Enemigo, Jugador
from dto.objeto_instancia import ObjetoInstancia
from logica.cambios import CambioAtributo, CambioLista, TransaccionAccion
from tests.test_logica.test_cierre_integrante1_parte3 import (
    partida_puerta,
    pergamino,
)


def test_pergamino_botin_y_dos_retrocesos_restauran_toda_la_accion():
    motor, estado, sala, _, _ = partida_puerta()
    rollo_suelo = ObjetoInstancia(
        "rollo-suelo", "itm_pergamino_retroceso")
    rollo_suelo.ficha = {
        "id": rollo_suelo.tipo_ficha_id,
        "clase": "pergamino_retroceso",
    }
    rollo_suelo.ubicacion = sala.id_sala
    sala.objetos.append(rollo_suelo)
    rollo_inventario = pergamino(estado, "rollo-inventario")

    enemigo = Enemigo("e-botin", "Rata", 1, 1, 0, 100)
    enemigo.ficha = {
        "id": "ent-rata", "clase": "enemigo", "suelta": ["itm-botin"]}
    botin = ObjetoInstancia("botin", "itm-botin")
    botin.ficha = {"id": "itm-botin", "clase": "pocion", "cura": 1}
    botin.ubicacion = "botin_preparado"
    enemigo.botin_preparado.append(botin)
    enemigo.sala_actual = sala
    sala.enemigos.append(enemigo)

    assert motor.ejecutar_accion(Accion("ATACAR", enemigo)).exito
    assert sala.objetos == [rollo_suelo, botin]
    assert motor.ejecutar_accion(Accion("RECOGER", rollo_suelo)).exito
    assert sala.objetos == [botin]

    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito
    assert rollo_suelo.ubicacion == "consumido"
    assert sala.objetos == [botin]
    assert motor.ejecutar_accion(Accion("RETROCEDER")).exito

    assert rollo_inventario.ubicacion == "consumido"
    assert sala.objetos == []
    assert enemigo.vida == 1
    assert not enemigo.muerte_procesada
    assert estado.enemigos_derrotados == 0
    assert botin.ubicacion == "botin_preparado"


def test_transaccion_valida_todos_los_inversos_antes_de_aplicar():
    actor = Jugador("j", "Jugador", 30, 1, 0, 100)
    valores = []
    valor = object()
    transaccion = TransaccionAccion()

    cambio_lista = CambioLista(valores, 0, valor, True)
    valores.append(valor)
    transaccion.registrar(cambio_lista)
    valores.clear()  # invalida el inverso más antiguo
    transaccion.registrar(CambioAtributo(actor, "vida"))
    actor.vida = 5

    with pytest.raises(ValueError, match="ya no pertenece"):
        transaccion.revertir(None)

    assert actor.vida == 5
    assert transaccion.get_cantidad() == 2
    valores.append(valor)
    transaccion.revertir(None)
    assert actor.vida == 30
    assert valores == []
    assert transaccion.esta_vacia()
