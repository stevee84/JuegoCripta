"""T016 y T038 (spec 003, §3.3): el minimapa sale del conocimiento del jugador.

El minimapa filtraba bien *qué* salas pintaba, pero el color lo sacaba de la realidad: el
estado real de cada puerta, y los enemigos, objetos y trampas de salas donde el jugador no
está. Estas pruebas fijan lo contrario, y la primera falla sobre esa versión.

Sin ventana (SDL dummy), como las demás pruebas de la vista.
"""

import pytest

from dto.actor import Enemigo, Jugador
from logica.mapa_conocido import MapaConocido
from tests.test_integracion_ir_a_001_003 import _estado_real


@pytest.fixture
def vista(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame = pytest.importorskip("pygame", reason="pygame no está instalado; GUI omitida")
    from vista.vista_pygame import VistaPygame
    pantalla = VistaPygame()
    yield pantalla, pygame
    pantalla.cerrar()


def _partida_con_puerta_que_se_cierra():
    """El jugador estuvo en 2 y volvió a 1; la puerta 2→4 se cierra sola mientras está lejos.

    Queda: 1 y 2 exploradas, 3 y 4 avistadas, 5 desconocida. Ninguna puerta visible se
    recuerda cerrada, así que el color de puerta cerrada no tiene por qué aparecer.
    """
    estado = _estado_real("cripta-cierre")
    estado.jugador = Jugador("j", "Jugador", 100, 10, 0, 100)
    estado.jugador.sala_actual = estado.mapa.obtener_sala(1)
    conocido = MapaConocido()
    for id_sala in (2, 1):
        conocido.explorar(estado.mapa.obtener_sala(id_sala))
    estado.mapa_conocido = conocido

    puerta = next(p for p in estado.mapa.obtener_sala(2).puertas if p.destino_sala_id == 4)
    assert conocido.puerta_recordada_abierta(puerta.id_puerta), "se observó abierta al entrar"
    puerta.abierta = False
    return estado, conocido, puerta


def _colores_dibujados(pantalla, pygame):
    pantalla._pantalla.fill((0, 0, 0))
    estado, conocido, puerta = _partida_con_puerta_que_se_cierra()
    pantalla._dibujar_minimapa(estado)
    colores = []
    for x in range(pantalla.MINIMAPA_X, pantalla.MINIMAPA_X + pantalla.MINIMAPA_W):
        for y in range(pantalla.MINIMAPA_Y, pantalla.MINIMAPA_Y + pantalla.MINIMAPA_H):
            color = tuple(pantalla._pantalla.get_at((x, y)))[:3]
            if color not in colores:
                colores.append(color)
    return colores, conocido, puerta


def test_fr006_la_puerta_que_se_cerro_sola_sigue_pintandose_abierta(vista):
    """El comando `mapa` la informa abierta; el minimapa la pintaba roja en la misma pantalla."""
    pantalla, pygame = vista
    colores, _, _ = _colores_dibujados(pantalla, pygame)

    assert pantalla.MINIMAPA_CERRADA not in colores, (
        "el minimapa pintó una puerta como cerrada: la única que lo está en la realidad es la "
        "que se cerró con el jugador lejos, y de esa el jugador solo puede saber lo que vio")
    assert pantalla.MINIMAPA_AVISTADA[0] in colores, "faltan las salas avistadas"
    assert pantalla.MINIMAPA_EXPLORADA[0] in colores, "faltan las salas exploradas"


def test_fr003_no_se_dibuja_la_conexion_entre_dos_salas_solo_avistadas(vista):
    """3 y 4 están avistadas; que estén conectadas el jugador no lo puede saber."""
    pantalla, _ = vista
    _, conocido, _ = _partida_con_puerta_que_se_cierra()

    assert not pantalla._arista_visible(conocido, 3, 4)
    assert not pantalla._arista_visible(conocido, 4, 3)
    # Desde una explorada hacia una avistada sí: esa puerta se observó desde dentro.
    assert pantalla._arista_visible(conocido, 2, 4)
    # Entre dos exploradas, una sola vez, desde la de identificador menor.
    assert pantalla._arista_visible(conocido, 1, 2)
    assert not pantalla._arista_visible(conocido, 2, 1)


def test_fr024_el_color_de_la_sala_no_delata_su_contenido(vista):
    """El mapa conocido no guarda contenido a propósito, así que no hay nada que pintar."""
    pantalla, _ = vista
    estado, conocido, _ = _partida_con_puerta_que_se_cierra()

    antes = pantalla._color_sala_minimapa(2, conocido, es_actual=False)
    estado.mapa.obtener_sala(2).enemigos.append(Enemigo("e", "Guardián", 10, 4, 0, 100))
    assert pantalla._color_sala_minimapa(2, conocido, es_actual=False) == antes


def test_los_tres_estados_se_distinguen_por_luminancia(vista):
    """Si solo se distinguieran por tono, el mapa no se leería en una pantalla mala.

    Fórmula estándar de luminancia relativa sobre canales normalizados.
    """
    pantalla, _ = vista

    def luminancia(color):
        rojo, verde, azul = (canal / 255 for canal in color)
        return 0.2126 * rojo + 0.7152 * verde + 0.0722 * azul

    escala = [luminancia(c) for c in ((12, 12, 18),          # fondo del panel
                                      pantalla.MINIMAPA_AVISTADA[0],
                                      pantalla.MINIMAPA_EXPLORADA[0],
                                      pantalla.MINIMAPA_ACTUAL[0])]
    for antes, despues in zip(escala, escala[1:]):
        assert despues - antes >= 0.05, (
            f"dos estados contiguos se separan solo {despues - antes:.3f} en luminancia: "
            f"{escala}")


# ── Viajar haciendo clic en el minimapa (T038, §3.4) ─────────────────────────

def test_fr010_solo_las_salas_exploradas_son_clicables(vista):
    """A una avistada no se puede viajar, así que no se puede hacer clic en ella.

    Antes «ir a» solo se alcanzaba tecleando un número en un diálogo, y pedir una avistada
    llegaba como error; ahora el minimapa no ofrece el clic.
    """
    pantalla, _ = vista
    estado, conocido, _ = _partida_con_puerta_que_se_cierra()
    pantalla._dibujar_minimapa(estado)

    clicables = [b.comando for b in pantalla._zonas_ir_a]
    assert clicables == ["ir a 2"], (
        f"explorada y no actual hay una sola, la 2; quedaron {clicables}")
    assert conocido.esta_avistada(3) and conocido.esta_avistada(4), "3 y 4 están avistadas"
    assert estado.jugador.sala_actual.id_sala == 1, "la actual no se ofrece: ya está ahí"


def test_las_zonas_no_sobreviven_a_un_dibujo_que_no_pinta_nada(vista):
    """Si no se dibuja el minimapa no puede quedar clicable lo del fotograma anterior."""
    pantalla, _ = vista
    estado, _, _ = _partida_con_puerta_que_se_cierra()
    pantalla._dibujar_minimapa(estado)
    assert pantalla._zonas_ir_a

    estado.jugador.sala_actual = None
    pantalla._dibujar_minimapa(estado)
    assert pantalla._zonas_ir_a == []


def test_las_zonas_caen_dentro_del_minimapa_y_no_bajo_el_panel(vista):
    """El panel se dibuja encima, así que un clic no puede ser ambiguo."""
    pantalla, pygame = vista
    estado, _, _ = _partida_con_puerta_que_se_cierra()
    pantalla._dibujar_minimapa(estado)

    marco = pygame.Rect(pantalla.MINIMAPA_X, pantalla.MINIMAPA_Y,
                        pantalla.MINIMAPA_W, pantalla.MINIMAPA_H)
    for zona in pantalla._zonas_ir_a:
        assert marco.contains(zona.rect), (zona.comando, tuple(zona.rect))
    assert marco.right <= pantalla.PANEL_X, "el minimapa no debe solaparse con el panel"


def test_la_leyenda_nombra_los_tres_estados_sin_meterse_bajo_el_panel(vista):
    """Sin leyenda los colores del minimapa no se pueden interpretar (FR-007).

    La fila libre está entre el cuadro de sala y la bitácora, y termina donde empieza el
    panel: si la leyenda se pasa, se dibuja debajo de la barra de botones.
    """
    pantalla, _ = vista
    estado, _, _ = _partida_con_puerta_que_se_cierra()
    pantalla._dibujar_juego(estado)      # la leyenda se dibuja con el resto, no suelta

    ancho = 15
    for etiqueta in ("#=Aqui", "#=Explorada", "#=Avistada"):
        ancho += pantalla._font.size(etiqueta)[0] + 15
    assert ancho <= pantalla.PANEL_X, (
        f"la leyenda ocupa {ancho} px y el panel empieza en {pantalla.PANEL_X}")

    y = pantalla.ALTO - pantalla.BITACORA_ALTO - 25
    for boton in pantalla._botones:
        assert not (boton.rect.top <= y <= boton.rect.bottom and boton.rect.left < ancho), (
            f"la leyenda cruza el botón {boton.texto}")
