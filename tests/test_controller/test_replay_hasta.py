"""T025 (spec 004): --replay partida.log --hasta t (FR-009, FR-010, FR-011).

Se juega una partida real en cripta-01 con su partida.log automático y después se reproduce el log
con --hasta, comparando el resumen con el de historia <t> en la partida original.
"""

import os
import subprocess
import sys

import pytest

from configuracion import Configuracion, parsear_argumentos
from controller.ejecutor_replay import EjecutorReplay
from controller.resumen_historia import consultar_historia
from datos.fuente_offline import FuenteOffline
from logica.cache_catalogo import CacheCatalogo
from logica.motor_juego import MotorJuego
from service.inicializador_partida import InicializadorPartida
from service.juego_service import JuegoService
from tests.test_controller.test_historia import REALES, _controlador

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACCIONES = ["esperar", "mover NORTE", "esperar", "esperar", "esperar", "esperar", "esperar"]


@pytest.fixture
def partida(tmp_path, monkeypatch):
    controlador = _controlador(tmp_path, monkeypatch)
    for accion in ACCIONES:
        controlador.procesar_comando(accion)
    linea = controlador._servicio.obtener_linea_tiempo()
    return controlador, linea, str(controlador._servicio._ruta_registro)


def _replay():
    servicio = JuegoService(motor=MotorJuego(), fuente=FuenteOffline(REALES), cache=CacheCatalogo(25))
    servicio.conectar_inicializador(InicializadorPartida())
    replay = EjecutorReplay()
    replay.conectar_servicio(servicio)
    return replay


def test_fr009_el_resumen_es_el_mismo_que_historia(partida):
    """US4-1: mismo texto, líneas y orden que historia <t> en la partida original."""
    controlador, linea, ruta = partida
    reloj_final = controlador._servicio.obtener_estado().reloj
    for t in (0, 1, 150, reloj_final // 2, reloj_final):
        esperado = consultar_historia(linea, str(t))
        assert _replay().reproducir(ruta, hasta=t) == esperado, f"t={t}"


def test_fr010_t_posterior_al_final(partida):
    """US4-2, Apéndice B: muestra el estado final e indica que la partida terminó antes."""
    controlador, linea, ruta = partida
    reloj_final = controlador._servicio.obtener_estado().reloj
    lineas = _replay().reproducir(ruta, hasta=reloj_final + 5000)
    assert lineas[0] == f"Historia en t={reloj_final + 5000} (final de la partida)"
    assert f"Reloj: {reloj_final}" in lineas
    assert lineas[-1] == (f"La partida terminó en t={reloj_final}, antes del instante pedido "
                          f"({reloj_final + 5000}).")


def test_fr011_sin_hasta_es_el_replay_de_la_parte_i(partida):
    """US4-3: sin --hasta no imprime resumen y termina con el mismo estado."""
    controlador, _, ruta = partida
    replay = _replay()
    assert replay.reproducir(ruta) is None
    final = replay._servicio.obtener_estado()
    assert final.reloj == controlador._servicio.obtener_estado().reloj


def test_fr011_version_incompatible_se_rechaza_igual(partida, tmp_path):
    """US4-4: un log de otra versión se rechaza igual que en la Parte I."""
    _, _, ruta = partida
    with open(ruta, encoding="utf-8") as archivo:
        lineas = archivo.read().split("\n")
    lineas[0] = lineas[0].replace('"version_cripta": "', '"version_cripta": "otra-')
    otro = tmp_path / "otro.log"
    otro.write_text("\n".join(lineas), encoding="utf-8")
    with pytest.raises(ValueError, match="versiones compatibles"):
        _replay().reproducir(str(otro), hasta=0)


def test_fr009_hasta_se_valida_al_arrancar(monkeypatch):
    """--hasta exige --replay y un entero mayor o igual que 0, antes de reproducir."""
    for argumentos in (["--hasta", "10"], ["--replay", "x.log", "--hasta", "-1"],
                       ["--replay", "x.log", "--hasta", "abc"]):
        monkeypatch.setattr(sys, "argv", ["main.py"] + argumentos)
        with pytest.raises(SystemExit):
            parsear_argumentos()
    monkeypatch.setattr(sys, "argv", ["main.py", "--replay", "x.log", "--hasta", "40"])
    assert Configuracion().hasta == 40
    monkeypatch.setattr(sys, "argv", ["main.py"])
    assert Configuracion().hasta is None


def test_fr009_main_no_instancia_la_vista(partida):
    """Constitución IV: --replay --hasta imprime el resumen sin cargar pygame ni la vista."""
    _, _, ruta = partida
    # Los datos del log son los fixtures, no datos_offline/: se apunta la ruta offline ahí.
    codigo = ("import sys, configuracion\n"
              f"configuracion.RUTA_DATOS_OFFLINE = {REALES!r}\n"
              "import main\n"
              "main.main()\n"
              "assert 'vista.vista_pygame' not in sys.modules\n"
              "assert 'vista.vista_consola' not in sys.modules\n")
    entorno = dict(os.environ, PYTHONPATH=RAIZ)
    proceso = subprocess.run(
        [sys.executable, "-c", codigo, "--offline", "--replay", ruta, "--hasta", "0"],
        capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, env=entorno)
    assert proceso.returncode == 0, proceso.stderr
    assert "Historia en t=0 (antes de la acción #1)" in proceso.stdout


def test_fr015_checkpoint_cada_se_valida_al_arrancar(monkeypatch):
    """US6-2: 0, negativos o no enteros se rechazan al arrancar; un K válido llega a la config."""
    for valor in ("0", "-3", "2.5", "abc"):
        monkeypatch.setattr(sys, "argv", ["main.py", "--checkpoint-cada", valor])
        with pytest.raises(SystemExit):
            parsear_argumentos()
    monkeypatch.setattr(sys, "argv", ["main.py", "--checkpoint-cada", "25"])
    assert Configuracion().checkpoint_cada == 25


def test_fr015_el_replay_usa_el_k_pedido(partida):
    """FR-015: --checkpoint-cada también vale para --replay, y el resumen no cambia con K."""
    controlador, linea, ruta = partida
    reloj = controlador._servicio.obtener_estado().reloj
    for k in (1, 3):
        replay = _replay()
        replay._servicio.configurar_checkpoint_cada(k)
        assert replay.reproducir(ruta, hasta=reloj // 2) == consultar_historia(linea, str(reloj // 2))
        assert replay._servicio.obtener_linea_tiempo().k == k
