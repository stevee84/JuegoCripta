"""T035: copia conjunta del estado y sus transacciones con alias íntegros."""

import copy
import pickle

import pytest

from dto.accion import Accion
from logica.cache_catalogo import CacheCatalogo
from logica.cambios import CambioAtributo, CambioLista
from logica.motor_juego import MotorJuego
from logica.rutas_ponderadas import (
    EntradaFrontera,
    EtiquetaRuta,
    MetricasRuta,
    ResultadoRuta,
    VistaMapaCazador,
)
from service.juego_service import JuegoService

from tests.test_logica._cazador_us3 import estado_empates


def _transacciones(historial):
    resultado = []
    nodo = historial._intervalos.primero
    while nodo is not None:
        resultado.append(nodo.valor)
        nodo = nodo.siguiente
    return tuple(resultado)


def _cambios(transaccion):
    resultado = []
    nodo = transaccion._cambios.primero
    while nodo is not None:
        resultado.append(nodo.valor)
        nodo = nodo.siguiente
    return resultado


def _grafo_objetos(raiz):
    pendientes = [raiz]
    vistos = set()
    while pendientes:
        actual = pendientes.pop()
        identidad = id(actual)
        if identidad in vistos:
            continue
        vistos.add(identidad)
        yield actual
        if isinstance(actual, dict):
            pendientes.extend(actual.keys())
            pendientes.extend(actual.values())
        elif isinstance(actual, (list, tuple, set, frozenset)):
            pendientes.extend(actual)
        elif hasattr(actual, "__dict__"):
            pendientes.extend(vars(actual).values())


@pytest.mark.parametrize("copiar", [
    copy.deepcopy,
    lambda valor: pickle.loads(pickle.dumps(valor)),
], ids=["deepcopy", "pickle"])
def test_copia_conjunta_reenlaza_cambios_y_no_incorpora_servicios(copiar):
    estado, cazador, _ = estado_empates(activo=True)
    motor = MotorJuego()
    motor.iniciar(estado)
    assert motor.ejecutar_accion(Accion("ESPERAR")).exito
    transacciones = _transacciones(estado.historial)
    assert len(transacciones) == 1

    estado_copia, transacciones_copia = copiar((estado, transacciones))
    cazador_copia = estado_copia.mapa.obtener_sala(2).enemigos[0]
    transaccion_copia = transacciones_copia[0]

    assert estado_copia is not estado
    assert transaccion_copia is estado_copia.historial._intervalos.primero.valor
    assert cazador_copia is not cazador
    cambios = _cambios(transaccion_copia)
    cambio_sala = next(
        cambio for cambio in cambios
        if isinstance(cambio, CambioAtributo)
        and cambio.nombre == "sala_actual"
    )
    assert cambio_sala.objeto is cazador_copia
    assert cambio_sala.anterior is estado_copia.mapa.obtener_sala(4)
    listas_enemigos = [
        cambio.lista for cambio in cambios
        if isinstance(cambio, CambioLista)
        and hasattr(cambio.lista, "posicion_identidad")
    ]
    assert estado_copia.mapa.obtener_sala(4).enemigos in listas_enemigos
    assert estado_copia.mapa.obtener_sala(2).enemigos in listas_enemigos

    prohibidos = (
        MotorJuego, JuegoService, CacheCatalogo, VistaMapaCazador,
        EntradaFrontera, EtiquetaRuta, MetricasRuta, ResultadoRuta,
    )
    assert not any(isinstance(objeto, prohibidos)
                   for objeto in _grafo_objetos((estado_copia,
                                                 transacciones_copia)))
    vida_original = cazador.vida
    cazador_copia.vida -= 1
    assert cazador.vida == vida_original
