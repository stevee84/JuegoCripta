"""T019/T025: buscador productivo frente al oráculo exhaustivo independiente."""

from itertools import permutations

import pytest

from logica.rutas_ponderadas import SalidaTransitable, proximo_paso

from tests.test_bench_terreno_cazador import (
    ConexionPrueba,
    ResultadoRutaPrueba,
    oraculo_rutas_simples,
)


class _VistaConexiones:
    def __init__(self, salas, conexiones):
        self._salas = tuple(salas)
        self._salidas = {}
        for conexion in conexiones:
            if conexion.abierta:
                self._salidas.setdefault(conexion.origen_id, []).append(
                    SalidaTransitable(conexion.destino_id, conexion.costo))

    def contiene_sala(self, sala_id):
        return sala_id in self._salas

    def salidas_transitables(self, sala_id):
        return tuple(self._salidas.get(sala_id, ()))


def _comparar_con_oraculo(salas, conexiones, origen, destino, limite):
    esperado, _ = oraculo_rutas_simples(
        salas, conexiones, origen_id=origen, destino_id=destino, limite=limite)
    obtenido = proximo_paso(
        _VistaConexiones(salas, conexiones), origen, destino, limite)
    if esperado.dentro_rango:
        assert obtenido.alcanzable
        assert obtenido.costo_total == esperado.costo_total
        assert obtenido.primera_vecina_id == esperado.primera_vecina_id
        assert obtenido.costo_primera_salida == esperado.costo_primer_paso
    else:
        assert obtenido.alcanzable is False
        assert (obtenido.costo_total, obtenido.primera_vecina_id,
                obtenido.costo_primera_salida) == (None, None, None)
    return obtenido


def test_prefiere_camino_de_menor_costo_aunque_tenga_mas_pasos():
    salas = (1, 2, 3, 9)
    conexiones = (
        ConexionPrueba(1, 9, 20),
        ConexionPrueba(1, 2, 3),
        ConexionPrueba(2, 3, 3),
        ConexionPrueba(3, 9, 3),
    )

    resultado, _ = oraculo_rutas_simples(
        salas, conexiones, origen_id=1, destino_id=9, limite=20)

    assert resultado == ResultadoRutaPrueba(
        "PASO", "MOVER", True, True, 9, 2, 3)
    _comparar_con_oraculo(salas, conexiones, 1, 9, 20)


def test_empate_elige_primera_vecina_menor_sin_depender_del_orden():
    salas = (1, 2, 10, 20, 99)
    conexiones = (
        ConexionPrueba(1, 10, 2),
        ConexionPrueba(10, 20, 1),
        ConexionPrueba(20, 99, 2),
        ConexionPrueba(1, 2, 4),
        ConexionPrueba(2, 99, 1),
    )
    esperado = ResultadoRutaPrueba(
        "PASO", "MOVER", True, True, 5, 2, 4)

    # Se permutan las conexiones iniciales y se invierte el resto: el desempate
    # es numérico (2 antes que 10), no léxico ni por descubrimiento.
    for primeras in permutations((conexiones[0], conexiones[3])):
        orden = primeras + tuple(reversed((
            conexiones[1], conexiones[2], conexiones[4])))
        resultado, _ = oraculo_rutas_simples(
            salas, orden, origen_id=1, destino_id=99, limite=5)
        assert resultado == esperado
        _comparar_con_oraculo(salas, orden, 1, 99, 5)


def test_puertas_cerradas_ciclos_y_destino_inaccesible():
    conexiones = (
        ConexionPrueba(1, 2, 2),
        ConexionPrueba(2, 1, 1),
        ConexionPrueba(2, 3, 2),
        ConexionPrueba(3, 2, 1),
        ConexionPrueba(3, 4, 1, abierta=False),
    )

    resultado, trabajo = oraculo_rutas_simples(
        (1, 2, 3, 4), conexiones, 1, 4, limite=100)

    assert resultado == ResultadoRutaPrueba(
        "SIN_RUTA", "SIN_PASO", False, False,
        None, None, None)
    assert trabajo.rutas_completas == 0
    _comparar_con_oraculo((1, 2, 3, 4), conexiones, 1, 4, 100)


@pytest.mark.parametrize(("limite", "estado", "accion", "dentro"), [
    (9, "PASO", "MOVER", True),
    (8, "FUERA_RANGO", "SIN_PASO", False),
    (0, "FUERA_RANGO", "SIN_PASO", False),
])
def test_rango_exacto_fuera_de_rango_y_rango_cero(
        limite, estado, accion, dentro):
    conexiones = (
        ConexionPrueba(1, 2, 4),
        ConexionPrueba(2, 3, 5),
    )

    resultado, _ = oraculo_rutas_simples(
        (1, 2, 3), conexiones, 1, 3, limite)

    assert resultado.estado == estado
    assert resultado.accion_ruta == accion
    assert resultado.alcanzable
    assert resultado.dentro_rango is dentro
    assert resultado.costo_total == 9
    assert resultado.primera_vecina_id == 2
    assert resultado.costo_primer_paso == 4
    _comparar_con_oraculo((1, 2, 3), conexiones, 1, 3, limite)
