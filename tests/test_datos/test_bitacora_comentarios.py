"""003 FR-020: la orden de «ir a» se anota como comentario, no como acción.

Los pasos del viaje se registran solos, porque cada uno es una acción `MOVER` del jugador. La
orden en cambio no se reproduce: repetirla ejecutaría el viaje encima de los pasos ya anotados.
Contrato con Joshua en `specs/003-niebla-y-ir-a/contracts/bitacora-comentarios.md`.
"""
import json

import pytest

from datos.registro_partida import RegistroPartida


@pytest.fixture
def log(tmp_path):
    ruta = str(tmp_path / "p.log")
    RegistroPartida().crear(ruta, "cripta-02", "v1", "v1", 0)
    return ruta


def lineas(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return [json.loads(l) for l in archivo]


def test_un_comentario_se_anexa_como_su_propio_registro(log):
    RegistroPartida().anexar_comentario(log, "ir a 5 desde 1")
    assert lineas(log)[-1] == {"registro": "comentario", "texto": "ir a 5 desde 1"}


def test_un_comentario_vacio_se_rechaza(log):
    for malo in ("", "   ", None, 7):
        with pytest.raises(ValueError):
            RegistroPartida().anexar_comentario(log, malo)
    assert len(lineas(log)) == 1, "no debe quedar nada escrito"


def test_el_texto_lo_produce_el_viaje(tmp_path):
    """Para que la consola, pygame y la reproducción anoten lo mismo."""
    from logica.mapa_conocido import MapaConocido
    from logica.viaje import Viaje
    from tests.test_logica.test_mapa_conocido import cargar_mapa

    mapa, _ = cargar_mapa("cripta-rutas")
    saber = MapaConocido()
    for id_sala in (1, 2, 4):
        saber.explorar(mapa.obtener_sala(id_sala))
    assert Viaje(saber, origen_id=1, destino_id=4).comentario() == "ir a 4 desde 1"


def test_el_lector_del_replay_ignora_los_comentarios(log):
    """El contrato ya está aplicado en `controller/ejecutor_replay.py` (Joshua, 2026-11-14).

    Antes esta prueba comprobaba que el lector todavía rechazaba los comentarios; como anunciaba
    su texto, cambió de sentido: ahora comprueba que los salta y no los cuenta como acciones.
    """
    from controller.ejecutor_replay import EjecutorReplay

    RegistroPartida().anexar_comentario(log, "ir a 5 desde 1")
    _, acciones = EjecutorReplay()._leer_log(log)
    assert all(registro["registro"] == "accion" for _, registro in acciones)
