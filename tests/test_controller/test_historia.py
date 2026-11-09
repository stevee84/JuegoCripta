"""T013 y T014 (spec 004): el comando historia en la consola.

FR-005: no consume tiempo, no se registra en partida.log, no toca el historial del pergamino ni
el azar. FR-006 y FR-007: rechazos con mensaje y sin efectos. FR-008: comando de la interfaz.
"""

import os

from controller.controlador_juego import ControladorJuego
from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.historial_reversible import HistorialReversible
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from tests.test_logica.test_linea_tiempo import huella
from vista.vista_consola import VistaConsola

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REALES = os.path.join(RAIZ, "tests", "fixtures", "api_real")
ACCIONES = ["esperar", "esperar", "mover E", "esperar", "esperar", "esperar", "esperar"]


def _controlador(carpeta, monkeypatch):
    os.makedirs(carpeta, exist_ok=True)
    monkeypatch.chdir(carpeta)
    controlador = ControladorJuego(
        MotorJuego(), VistaConsola(), FuenteOffline(REALES), HistorialReversible())
    controlador.configurar_arranque(0, CacheCatalogo(25), str(carpeta))
    controlador.conectar_inicializador(InicializadorPartida(), 0)
    assert controlador.procesar_comando("cripta cripta-01").exito
    return controlador


def _log(controlador):
    ruta = controlador._servicio._ruta_registro
    with open(ruta, encoding="utf-8") as archivo:
        return archivo.read()


def test_fr006_t_futuro_se_rechaza_sin_efectos(tmp_path, monkeypatch, capsys):
    """US1-1, Apéndice B: historia <t> con t mayor que el reloj actual."""
    controlador = _controlador(tmp_path, monkeypatch)
    controlador.procesar_comando("esperar")
    estado = controlador._servicio.obtener_estado()
    antes = huella(estado)
    capsys.readouterr()
    resultado = controlador.procesar_comando(f"historia {estado.reloj + 1}")
    assert not resultado.exito
    assert f"el instante {estado.reloj + 1} es posterior al reloj actual ({estado.reloj})" \
        in resultado.mensaje
    assert huella(estado) == antes


def test_fr007_instantes_invalidos_y_sin_partida(tmp_path, monkeypatch):
    """US1-6: t no entero o negativo, y consulta sin partida."""
    controlador = _controlador(tmp_path, monkeypatch)
    for texto in ("historia -1", "historia abc", "historia 2.5"):
        resultado = controlador.procesar_comando(texto)
        assert not resultado.exito
        assert "entero mayor o igual que 0" in resultado.mensaje
    assert not controlador.procesar_comando("historia").exito
    sin_partida = ControladorJuego(
        MotorJuego(), VistaConsola(), FuenteOffline(REALES), HistorialReversible())
    resultado = sin_partida.procesar_comando("historia 0")
    assert not resultado.exito
    assert "no hay una partida iniciada" in resultado.mensaje


def test_fr004_fr008_muestra_el_resumen(tmp_path, monkeypatch, capsys):
    controlador = _controlador(tmp_path, monkeypatch)
    controlador.procesar_comando("esperar")
    capsys.readouterr()
    resultado = controlador.procesar_comando("historia 0")
    salida = capsys.readouterr().out
    assert resultado.exito
    assert "Historia en t=0 (antes de la acción #1)" in salida
    assert "Reloj: 0" in salida
    assert "Mapa conocido: no disponible" in salida


def test_fr005_historia_no_consume_tiempo_ni_se_registra(tmp_path, monkeypatch):
    """US1-3, Apéndice B: no consume tiempo, no va a partida.log, no toca el retroceso.

    Dos partidas con la misma semilla y las mismas acciones; una consulta la línea entre
    acción y acción. Al final deben ser idénticas, con el mismo partida.log.
    """
    sin = _controlador(tmp_path / "sin", monkeypatch)
    con = _controlador(tmp_path / "con", monkeypatch)
    for accion in ACCIONES:
        assert sin.procesar_comando(accion).exito == con.procesar_comando(accion).exito
        estado = con._servicio.obtener_estado()
        reloj = estado.reloj
        azar = estado.azar.getstate()
        cantidad = estado.historial.get_cantidad()
        ultima = estado.historial._intervalos.primero
        log = _log(con)
        for consulta in ("historia 0", f"historia {reloj // 2}", f"historia {reloj}"):
            assert con.procesar_comando(consulta).exito
        assert estado.reloj == reloj
        assert estado.azar.getstate() == azar
        assert estado.historial.get_cantidad() == cantidad
        assert estado.historial._intervalos.primero is ultima
        assert _log(con) == log
    assert huella(con._servicio.obtener_estado()) == huella(sin._servicio.obtener_estado())
    assert _log(con).split("\n")[1:] == _log(sin).split("\n")[1:]
