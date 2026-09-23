"""Pruebas de los stubs temporales."""

from stubs.tabla_hash_dict import DictTablaHash
from stubs.lista_doble_simple import ListaDobleSimple
from stubs.motor_falso import MotorFalso
from dto.accion import Accion, ResultadoAccion


def test_dict_tabla_hash():
    t = DictTablaHash()
    t.insertar("a", 1)
    assert t.contiene("a")
    assert t.obtener("a") == 1
    t.eliminar("a")
    assert not t.contiene("a")


def test_lista_doble_simple():
    l = ListaDobleSimple()
    n = l.insertar("x")
    assert n == "x"
    l.mover_al_frente("x")
    l.quitar_nodo("x")


def test_motor_falso():
    m = MotorFalso()
    accion = Accion(tipo="mover", direccion="N")
    r = m.ejecutar_accion(accion)
    assert r.exito is True
