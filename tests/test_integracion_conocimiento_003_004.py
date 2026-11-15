"""Integración 003 con 004: consultar un instante pasado devuelve el conocimiento de entonces.

`FR-022` cierra con esto: el conocimiento es estado del juego, así que la línea de tiempo lo
reconstruye al consultar el pasado. Y lo hace deshaciendo en sitio, no copiando el mapa, de modo
que lo que importa comprobar es que el conocimiento actual queda intacto después (`FR-005`).
"""
import contextlib
from pathlib import Path

import pytest

from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService

REALES = str(Path("tests/fixtures/api_real").resolve())


@pytest.fixture
def avanzada(tmp_path):
    """Una partida real con dos movimientos hechos, cada uno revelando algo."""
    with contextlib.chdir(tmp_path):
        servicio = JuegoService(MotorJuego(), FuenteOffline(REALES), CacheCatalogo(25))
        servicio.conectar_inicializador(InicializadorPartida())
        estado = servicio.iniciar_partida("cripta-01")
        for direccion in ("NORTE", "NORTE"):
            accion = servicio.resolver_accion("MOVER", direccion=direccion)
            assert servicio.ejecutar_accion(accion).exito
        return servicio, estado


def exploradas(estado):
    return sorted(estado.mapa_conocido.exploradas())


def test_consultar_una_accion_pasada_devuelve_el_conocimiento_de_entonces(avanzada):
    """FR-022: el pasado se ve como se veía, no como se ve ahora."""
    servicio, estado = avanzada
    linea = servicio.obtener_linea_tiempo()
    ahora = exploradas(estado)
    assert len(ahora) >= 3, "los dos movimientos tenían que explorar salas nuevas"

    antes_del_segundo = linea.consultar_accion(linea.cantidad_acciones(), exploradas)
    assert antes_del_segundo == ahora[:-1], (
        f"antes de la última acción el jugador conocía {antes_del_segundo} y no {ahora}")


def test_consultar_el_pasado_no_altera_el_conocimiento_actual(avanzada):
    """FR-005: la consulta deshace en sitio y vuelve a dejar todo como estaba."""
    servicio, estado = avanzada
    linea = servicio.obtener_linea_tiempo()
    ahora = exploradas(estado)
    avistadas = sorted(estado.mapa_conocido.avistadas())

    for k in range(1, linea.cantidad_acciones() + 1):
        linea.consultar_accion(k, exploradas)
    assert exploradas(estado) == ahora
    assert sorted(estado.mapa_conocido.avistadas()) == avistadas
