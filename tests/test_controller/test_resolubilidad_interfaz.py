"""T036 (spec 004): resolubilidad en la interfaz, tareas 002-T049 y 002-T050.

Verifica FR-013 y FR-014 de la spec 002 desde el controlador, con el formato de
specs/002-resolubilidad/contracts/cli-verificar.md.
"""

import os

import pytest

from controller.controlador_juego import ControladorJuego
from controller.resumen_resolubilidad import linea_inicio, lineas_informe
from datos.fuente_offline import FuenteOffline
from estructuras.tabla_hash import TablaHashImpl
from logica.cache_catalogo import CacheCatalogo
from logica.historial_reversible import HistorialReversible
from logica.motor_juego import MotorJuego
from logica.verificador_resolubilidad import InformeResolubilidad
from main import imprimir_informe
from service.inicializador_partida import InicializadorPartida
from vista.vista_consola import VistaConsola

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REALES = os.path.join(RAIZ, "tests", "fixtures", "api_real")
RESOLUBILIDAD = os.path.join(RAIZ, "tests", "fixtures", "resolubilidad")


def _ubicaciones(*pares):
    tabla = TablaHashImpl()
    for llave, sala, enemigo in pares:
        tabla.insertar(llave, (sala, enemigo))
    return tabla


INFORMES = {
    "con_solucion": InformeResolubilidad(
        True, ["itm_llave_bronce", "itm_llave_negra"], [], [], [],
        _ubicaciones(("itm_llave_bronce", 3, None), ("itm_llave_negra", 4, None))),
    "sin_solucion": InformeResolubilidad(
        False, [], ["itm_llave_negra", "itm_llave_oxido"],
        [(4, "E", "itm_llave_negra"), (5, "N", "itm_llave_negra")],
        [["itm_llave_negra"]],
        _ubicaciones(("itm_llave_negra", 12, "e-1203"), ("itm_llave_oxido", 9, None))),
    "no_verificada": InformeResolubilidad.sin_verificar(
        "no se obtuvo la ubicación de las llaves"),
}


@pytest.mark.parametrize("nombre", sorted(INFORMES))
def test_fr014_002_el_informe_completo_es_el_mismo_que_imprime_verificar(nombre, capsys):
    """FR-014 y FR-017 de la 002: el comando muestra lo mismo que --verificar."""
    imprimir_informe("cripta-07", INFORMES[nombre])
    esperado = capsys.readouterr().out.rstrip("\n").split("\n")
    assert lineas_informe("cripta-07", INFORMES[nombre]) == esperado


def test_fr013_002_tres_lineas_distinguibles_al_iniciar():
    """FR-013 y FR-019 de la 002: «no se pudo verificar» no es «sin solución»."""
    assert linea_inicio(INFORMES["con_solucion"]) == "Resolubilidad: tiene solución, 2 llaves."
    assert linea_inicio(INFORMES["sin_solucion"]) == (
        "Resolubilidad: SIN SOLUCIÓN. La partida no inicia; usa --forzar para jugarla igual.")
    assert linea_inicio(INFORMES["no_verificada"]) == (
        "Resolubilidad: no se pudo verificar. La partida no inicia; usa --forzar para jugarla igual.")


def test_fr013_002_con_forzar_la_linea_dice_que_se_juega_igual():
    linea = linea_inicio(INFORMES["sin_solucion"], forzada=True)
    assert linea == "Resolubilidad: SIN SOLUCIÓN. Se juega igual porque se usó --forzar."


def _controlador(tmp_path, monkeypatch, carpeta, forzar=False):
    monkeypatch.chdir(tmp_path)
    controlador = ControladorJuego(
        MotorJuego(), VistaConsola(), FuenteOffline(carpeta), HistorialReversible())
    controlador.configurar_arranque(0, CacheCatalogo(25), str(tmp_path))
    inicializador = InicializadorPartida()
    inicializador.forzar = forzar
    controlador.conectar_inicializador(inicializador, 0)
    return controlador


def test_fr013_002_al_iniciar_se_muestra_la_linea_con_solucion(tmp_path, monkeypatch, capsys):
    controlador = _controlador(tmp_path, monkeypatch, REALES)
    resultado = controlador.procesar_comando("cripta cripta-01")
    assert resultado.exito
    assert "Resolubilidad: tiene solución, 2 llaves." in capsys.readouterr().out


def test_fr013_002_sin_solucion_no_inicia_y_muestra_el_informe(tmp_path, monkeypatch, capsys):
    """Antes, CriptaNoResoluble no se atrapaba y la consola se cerraba."""
    controlador = _controlador(tmp_path, monkeypatch, RESOLUBILIDAD)
    resultado = controlador.procesar_comando("cripta cripta-ciclo")
    salida = capsys.readouterr().out
    assert not resultado.exito
    assert "Resolubilidad: SIN SOLUCIÓN." in salida
    assert "Cripta cripta-ciclo: NO tiene solución." in salida
    assert controlador._servicio.obtener_estado() is None


def test_fr014_002_el_comando_muestra_el_informe_y_no_cambia(tmp_path, monkeypatch, capsys):
    """FR-014 de la 002: es el de antes de empezar, igual aunque el jugador avance."""
    controlador = _controlador(tmp_path, monkeypatch, REALES)
    controlador.procesar_comando("cripta cripta-01")
    capsys.readouterr()
    estado = controlador._servicio.obtener_estado()
    reloj = estado.reloj
    resultado = controlador.procesar_comando("resolubilidad")
    primera = capsys.readouterr().out
    assert resultado.exito
    assert "Cripta cripta-01: tiene solución. 2 llaves." in primera
    assert estado.reloj == reloj
    assert estado.historial.esta_vacio()
    controlador.procesar_comando("esperar")
    capsys.readouterr()
    controlador.procesar_comando("resolubilidad")
    assert capsys.readouterr().out == primera


def test_fr014_002_sin_partida_el_comando_se_rechaza(tmp_path, monkeypatch):
    controlador = _controlador(tmp_path, monkeypatch, REALES)
    resultado = controlador.procesar_comando("resolubilidad")
    assert not resultado.exito
