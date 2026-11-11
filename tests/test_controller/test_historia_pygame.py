"""T039 (spec 004, FR-008): historia en la vista pygame, sin ventana (SDL dummy).

El botón «Historia» abre un diálogo de texto; el resumen se muestra en un panel. Se comprueba con
eventos de teclado simulados, porque la vista no se puede usar con el ratón en una prueba.
"""

import pytest

from controller.controlador_juego import ControladorJuego
from logica.historial_reversible import HistorialReversible
from logica.motor_juego import MotorJuego
from tests.test_controller.test_historia import REALES, _controlador


@pytest.fixture
def vista(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame = pytest.importorskip("pygame", reason="pygame no está instalado; GUI omitida")
    from vista.vista_pygame import VistaPygame
    vista = VistaPygame()
    yield vista, pygame
    vista.cerrar()


def _teclas(pygame, texto, final):
    for caracter in texto:
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=0, unicode=caracter))
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=final, unicode=""))


def test_fr008_el_dialogo_devuelve_lo_escrito(vista):
    pantalla, pygame = vista
    _teclas(pygame, "#3", pygame.K_RETURN)
    assert pantalla._dialogo_texto("Historia") == "#3"
    _teclas(pygame, "40x", pygame.K_BACKSPACE)
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""))
    assert pantalla._dialogo_texto("Historia") == "40"
    _teclas(pygame, "12", pygame.K_ESCAPE)
    assert pantalla._dialogo_texto("Historia") is None


def test_fr008_el_panel_muestra_las_lineas_y_las_deja_en_la_bitacora(vista):
    pantalla, pygame = vista
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" "))
    pantalla.mostrar_lineas(["Historia en t=0", "Reloj: 0"])
    mensajes = pantalla.bitacora.obtener_mensajes()
    assert "Historia en t=0" in mensajes and "Reloj: 0" in mensajes


def test_fr008_el_boton_historia_cabe_en_el_panel(vista, tmp_path, monkeypatch):
    pantalla, _ = vista
    controlador = _controlador(tmp_path, monkeypatch)
    pantalla._construir_botones(controlador._servicio.obtener_estado())
    boton = next(b for b in pantalla._botones if b.comando == "__historia__")
    x, _, ancho, _ = boton.rect if isinstance(boton.rect, tuple) else tuple(boton.rect)
    assert x + ancho <= pantalla.PANEL_X + pantalla.PANEL_ANCHO


def test_fr008_el_controlador_usa_el_panel_si_la_vista_lo_tiene(tmp_path, monkeypatch):
    class VistaConPanel:
        def __init__(self):
            self.lineas = None

        def mostrar_lineas(self, lineas):
            self.lineas = list(lineas)

        def mostrar_mensaje(self, mensaje):
            pass

        mostrar_error = mostrar_mensaje

    controlador = _controlador(tmp_path, monkeypatch)
    panel = VistaConPanel()
    controlador._vista = panel
    assert controlador.procesar_comando("historia 0").exito
    assert panel.lineas[0] == "Historia en t=0 (antes de la acción #1)"
