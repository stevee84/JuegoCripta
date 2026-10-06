import pickle

import pytest

from dto.accion import Accion
from logica.historial_reversible import HistorialReversible
from tests.test_merge_joshua_sofia import iniciar, objeto


def test_conexion_automatica_equipo_y_retroceso():
    motor, servicio, estado = iniciar()
    arma = objeto("arma-conexion", {
        "id": "espada", "clase": "arma", "ataque_bonus": 4,
    })
    estado.inventario.agregar(arma)
    servicio.conectar_inventario(
        estado.inventario, {"espada": arma.ficha}
    )
    operaciones = servicio._operaciones_inventario
    assert motor._servicio_inventario is operaciones
    ataque = estado.jugador.ataque

    resultado = servicio.ejecutar_accion(Accion("EQUIPAR"))
    assert resultado.exito and resultado.costo == 50
    assert estado.reloj == 50
    assert operaciones.obtener_equipo()["arma"] is arma
    assert estado.jugador.ataque == ataque + 4

    resultado = servicio.ejecutar_accion(Accion("SOLTAR"))
    assert resultado.exito and resultado.costo == 25
    assert estado.jugador.ataque == ataque
    assert operaciones.obtener_equipo()["arma"] is None

    assert estado.historial.deshacer_ultimo(estado)
    assert operaciones.obtener_equipo()["arma"] is arma
    assert estado.jugador.ataque == ataque + 4

    assert estado.historial.deshacer_ultimo(estado)
    assert estado.jugador.ataque == ataque and estado.reloj == 0
    assert operaciones.obtener_equipo()["arma"] is None


def test_conexion_tardia_no_cambia_historial_ni_inventario():
    motor, servicio, estado = iniciar()
    anterior = motor._obtener_servicio_inventario()
    historial = estado.historial
    inventario = estado.inventario
    antes = pickle.dumps(estado)

    with pytest.raises(ValueError, match="motor ya tiene"):
        servicio.conectar_inventario(
            inventario, {}, HistorialReversible()
        )

    assert pickle.dumps(estado) == antes
    assert estado.historial is historial
    assert estado.inventario is inventario
    assert motor._servicio_inventario is anterior
    assert servicio._operaciones_inventario is None


def test_conexion_durante_accion_no_publica_otro_servicio():
    motor, servicio, estado = iniciar()
    estado.historial.iniciar_intervalo()
    antes = pickle.dumps(estado)

    with pytest.raises(ValueError, match="durante una acción"):
        servicio.conectar_inventario(estado.inventario, {})

    assert pickle.dumps(estado) == antes
    assert motor._servicio_inventario is None
    assert servicio._operaciones_inventario is None