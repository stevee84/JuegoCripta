import pickle

import pytest

from dto.estado_partida import EstadoPartida
from dto.objeto_instancia import ObjetoInstancia
from dto.sala import Sala
from logica.inventario import Inventario
from logica.servicio_inventario import ServicioInventario


@pytest.mark.parametrize("operacion", ["equipar", "usar"])
def test_operaciones_sin_reglas_disponibles_fallan_sin_mutaciones(operacion):
    inventario = Inventario(2)
    objeto = ObjetoInstancia("opaco", "ficha-opaca")
    objeto.ubicacion = "inventario"
    inventario.agregar(objeto)
    servicio = ServicioInventario(inventario)
    estado = EstadoPartida(semilla=17)
    cursor = inventario._cursor
    antes = pickle.dumps((inventario, estado))
    # Validación de una conexión ausente; el funcionamiento se prueba aparte.
    for _ in range(2):
        resultado = servicio.usar(estado) if operacion == "usar" else servicio.equipar()
        assert not resultado.exito
        assert resultado.costo == 0
        assert resultado.cambios == []
        assert inventario._cursor is cursor
        assert pickle.dumps((inventario, estado)) == antes


def test_soltar_equipo_no_aplica_una_retirada_parcial():
    inventario = Inventario(2)
    objeto = ObjetoInstancia("opaco", "ficha-opaca")
    objeto.ubicacion = "equipado"
    inventario.agregar(objeto)
    sala = Sala("s1")
    antes = pickle.dumps((inventario, sala))
    resultado = ServicioInventario(inventario).soltar(sala)
    assert not resultado.exito
    assert resultado.costo == 0
    assert resultado.cambios == []
    assert pickle.dumps((inventario, sala)) == antes
