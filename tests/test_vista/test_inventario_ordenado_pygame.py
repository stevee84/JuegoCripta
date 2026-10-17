"""§10.2: la vista gráfica permite consultar el inventario ordenado por peso, valor y nombre."""
from pathlib import Path

import pytest

API_REAL = Path(__file__).resolve().parents[1] / "fixtures" / "api_real"


@pytest.fixture
def partida_con_inventario(monkeypatch, tmp_path):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pytest.importorskip("pygame", reason="pygame no está instalado; GUI omitida")
    monkeypatch.chdir(tmp_path)
    from controller.controlador_juego import ControladorJuego
    from datos.fuente_offline import FuenteOffline
    from logica.cache_catalogo import CacheCatalogo
    from logica.historial_reversible import HistorialReversible
    from logica.motor_juego import MotorJuego
    from service.inicializador_partida import InicializadorPartida
    from vista.vista_pygame import VistaPygame

    vista = VistaPygame()
    control = ControladorJuego(MotorJuego(), vista, FuenteOffline(str(API_REAL)), HistorialReversible())
    control.configurar_arranque(3, CacheCatalogo(25), "partidas")
    control.conectar_inicializador(InicializadorPartida(), 3)
    for comando in ("cripta cripta-02", "recoger objeto:1:0", "mover norte", "recoger objeto:2:0",
                    "recoger objeto:2:1", "mover norte", "recoger objeto:3:0"):
        assert control.procesar_comando(comando).exito, comando
    yield vista, control
    vista.cerrar()


def _lista_dibujada(vista, estado):
    vista._dibujar_panel(estado)
    vista._construir_botones(estado)
    return [b.comando.split(" ", 1)[1] for b in vista._botones if b.comando.startswith("seleccionar ")]


@pytest.mark.parametrize("criterio", ["peso", "valor", "nombre"])
def test_cada_orden_se_muestra_sin_alterar_el_inventario_real(partida_con_inventario, criterio):
    vista, control = partida_con_inventario
    estado = control._servicio.obtener_estado()
    real = [o.id_instancia for o in estado.inventario.obtener_objetos()]
    cursor = estado.inventario.obtener_actual()

    vista._elegir_orden(control, criterio)
    mostrada = _lista_dibujada(vista, estado)

    objetos = estado.inventario.obtener_objetos()
    esperada = [o.id_instancia for o in sorted(objetos, key=lambda o: o.ficha[criterio])]
    assert mostrada == esperada and mostrada != real
    assert [o.id_instancia for o in estado.inventario.obtener_objetos()] == real
    assert estado.inventario.obtener_actual() is cursor
    from vista.vista_pygame import AZUL
    assert any(b.comando == f"__orden__:{criterio}" and b.color == AZUL for b in vista._botones)


def test_volver_al_orden_real_y_seleccionar_desde_la_vista_ordenada(partida_con_inventario):
    vista, control = partida_con_inventario
    estado = control._servicio.obtener_estado()
    real = [o.id_instancia for o in estado.inventario.obtener_objetos()]
    vista._elegir_orden(control, "valor")
    ultimo_por_valor = _lista_dibujada(vista, estado)[-1]
    assert control.procesar_comando(f"seleccionar {ultimo_por_valor}").exito
    assert estado.inventario.obtener_actual().id_instancia == ultimo_por_valor
    vista._elegir_orden(control, "real")
    assert _lista_dibujada(vista, estado) == real
