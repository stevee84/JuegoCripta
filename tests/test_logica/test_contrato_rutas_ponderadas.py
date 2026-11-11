"""T022: contrato público e independencia del buscador ponderado."""

from dataclasses import FrozenInstanceError

import pytest

from dto.sala import Puerta, Sala
from logica.mapa_cripta import MapaCripta
from logica.rutas_ponderadas import (
    EntradaFrontera,
    ResultadoRuta,
    SalidaTransitable,
    VistaMapaCazador,
    proximo_paso,
)


class VistaPrueba:
    def __init__(self, conexiones):
        self._salas = set()
        self._salidas = {}
        self.consultas = []
        for origen, destino, costo in conexiones:
            self._salas.update((origen, destino))
            self._salidas.setdefault(origen, []).append(
                SalidaTransitable(destino, costo))

    def contiene_sala(self, sala_id):
        return sala_id in self._salas

    def salidas_transitables(self, sala_id):
        self.consultas.append(sala_id)
        return tuple(self._salidas.get(sala_id, ()))


def _vista():
    return VistaPrueba(((1, 2, 4), (2, 9, 5), (1, 3, 2), (3, 9, 20)))


def test_firma_resultado_inmutable_y_paso_minimo():
    resultado = proximo_paso(_vista(), 1, 9)
    assert resultado == ResultadoRuta(True, 9, 2, 4)
    with pytest.raises(FrozenInstanceError):
        resultado.costo_total = 0
    with pytest.raises(FrozenInstanceError):
        EntradaFrontera(1, 2, 2).distancia = 9


def test_origen_objetivo_y_ausencia_de_ruta_no_se_confunden():
    vista = _vista()
    assert proximo_paso(vista, 1, 1) == ResultadoRuta(True, 0, None, None)
    limitado = proximo_paso(vista, 1, 9, limite_costo=8)
    assert limitado == ResultadoRuta(False, None, None, None)


@pytest.mark.parametrize("limite", [9, 10])
def test_limite_es_inclusivo(limite):
    assert proximo_paso(_vista(), 1, 9, limite).costo_total == 9


@pytest.mark.parametrize(("origen", "objetivo", "limite"), [
    (True, 9, None), (1.0, 9, None), (1, "9", None), (1, 9, True),
    (1, 9, -1), (1, 9, 9.0),
])
def test_ids_y_limite_se_validan_sin_conversion(origen, objetivo, limite):
    with pytest.raises((TypeError, ValueError)):
        proximo_paso(_vista(), origen, objetivo, limite)


def test_no_inicializa_ni_consulta_el_exterior_del_limite():
    vista = VistaPrueba(((1, 2, 2), (2, 3, 2), (3, 4, 2), (4, 9, 2)))
    resultado = proximo_paso(vista, 1, 9, 3)
    assert not resultado.alcanzable
    assert vista.consultas == [1, 2]
    assert resultado.metricas.salas_descubiertas == 2
    assert resultado.metricas.entradas_insertadas == 2


def test_cada_llamada_recalcula_sin_estado_retenido():
    vista = _vista()
    primero = proximo_paso(vista, 1, 9)
    vista._salidas[1] = [SalidaTransitable(3, 1)]
    vista._salidas[3] = [SalidaTransitable(9, 1)]
    segundo = proximo_paso(vista, 1, 9)
    assert (primero.costo_total, primero.primera_vecina_id) == (9, 2)
    assert (segundo.costo_total, segundo.primera_vecina_id) == (2, 3)
    assert primero != segundo


def test_instrumentacion_cuenta_cerradas_sin_hacerlas_transitables():
    mapa = MapaCripta()
    origen, destino, cerrada = Sala(1), Sala(2), Sala(3)
    abierta = Puerta("abierta", 2, "NORTE")
    abierta.abierta = True
    abierta.costo = 7
    puerta_cerrada = Puerta("cerrada", 3, "SUR")
    puerta_cerrada.abierta = False
    puerta_cerrada.costo = 1
    origen.puertas.extend((abierta, puerta_cerrada))
    for sala in (origen, destino, cerrada):
        mapa.agregar_sala(sala)
    mapa.vincular_salidas()
    resultado = proximo_paso(VistaMapaCazador(mapa), 1, 2)
    assert resultado.primera_vecina_id == 2
    assert resultado.metricas.salidas_examinadas == 2
