"""Selección de sprites de enemigos a partir de las fichas reales del API."""
from pathlib import Path

import pytest


pygame = pytest.importorskip("pygame", reason="pygame no está instalado; GUI omitida")

from dto.actor import Enemigo
from vista.vista_pygame import VistaPygame


def _enemigo(tipo_ficha_id, vida=10, nombre="Enemigo"):
    enemigo = Enemigo("enemigo-1", nombre, 10, 1, 1, 10)
    enemigo.tipo_ficha_id = tipo_ficha_id
    enemigo.vida = vida
    return enemigo


@pytest.fixture
def selector():
    vista = object.__new__(VistaPygame)
    for atributo in (
        "_sprite_carcelero",
        "_sprite_carcelero_muerto",
        "_sprite_sabueso",
        "_sprite_sabueso_muerto",
        "_sprite_espectro",
        "_sprite_espectro_muerto",
        "_sprite_rata",
        "_sprite_rata_muerta",
        "_sprite_guardian_oseo",
        "_sprite_guardian_muerto",
    ):
        setattr(vista, atributo, object())
    return vista


@pytest.fixture
def pantalla_dummy(monkeypatch):
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setenv("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


@pytest.mark.parametrize(
    ("tipo_ficha_id", "vida", "atributo"),
    [
        ("ent_guardian_oseo", 10, "_sprite_guardian_oseo"),
        ("ent_guardian_oseo", 0, "_sprite_guardian_muerto"),
        ("ent_rata_gigante", 10, "_sprite_rata"),
        ("ent_rata_gigante", 0, "_sprite_rata_muerta"),
        ("ent_carcelero", 10, "_sprite_carcelero"),
        ("ent_carcelero", 0, "_sprite_carcelero_muerto"),
        ("ent_sabueso", 10, "_sprite_sabueso"),
        ("ent_sabueso", 0, "_sprite_sabueso_muerto"),
        ("ent_espectro", 10, "_sprite_espectro"),
        ("ent_espectro", 0, "_sprite_espectro_muerto"),
    ],
)
def test_tipo_de_ficha_y_vida_seleccionan_el_sprite_correcto(
    selector, tipo_ficha_id, vida, atributo
):
    enemigo = _enemigo(tipo_ficha_id, vida)

    assert selector._sprite_para_enemigo(enemigo) is getattr(selector, atributo)


@pytest.mark.parametrize(
    ("nombre", "vida", "atributo"),
    [
        ("Rata gigante", 10, "_sprite_rata"),
        ("Rata gigante", 0, "_sprite_rata_muerta"),
        ("Guardián óseo", 10, "_sprite_guardian_oseo"),
        ("Guardián óseo", 0, "_sprite_guardian_muerto"),
        ("Carcelero", 10, "_sprite_carcelero"),
        ("Carcelero", 0, "_sprite_carcelero_muerto"),
        ("Sabueso", 10, "_sprite_sabueso"),
        ("Sabueso", 0, "_sprite_sabueso_muerto"),
        ("Espectro", 10, "_sprite_espectro"),
        ("Espectro", 0, "_sprite_espectro_muerto"),
    ],
)
def test_nombre_visible_selecciona_el_sprite_correspondiente(
    selector, nombre, vida, atributo
):
    enemigo = _enemigo(None, vida, nombre)

    assert selector._sprite_para_enemigo(enemigo) is getattr(selector, atributo)


@pytest.mark.parametrize(
    ("tipo_ficha_id", "atributo"),
    [
        ("ent_carcelero", "_sprite_carcelero"),
        ("ent_sabueso", "_sprite_sabueso"),
        ("ent_espectro", "_sprite_espectro"),
    ],
)
def test_id_resuelto_en_la_ficha_tambien_se_utiliza(selector, tipo_ficha_id, atributo):
    enemigo = _enemigo(None, nombre="Enemigo")
    enemigo.ficha = {"id": tipo_ficha_id, "nombre": ""}

    assert selector._sprite_para_enemigo(enemigo) is getattr(selector, atributo)


def test_recurso_faltante_conserva_el_respaldo_sin_sprite(selector):
    selector._sprite_espectro = None

    assert selector._sprite_para_enemigo(_enemigo("ent_espectro")) is None


def test_cargador_devuelve_none_si_el_archivo_no_existe(selector):
    errores = []
    selector.mostrar_error = errores.append

    assert selector._cargar_sprite("enemigo_inexistente.png") is None
    assert errores and "enemigo_inexistente.png" in errores[0]


@pytest.mark.parametrize(
    "nombre_archivo",
    [
        "Carcelero.png",
        "Carcelero_muerto.png",
        "Sabueso.png",
        "Sabueso_muerto.png",
        "Espectro.png",
        "Espectro_muerto.png",
    ],
)
def test_nuevos_recursos_cargan_con_transparencia_y_proporcion(
    selector, pantalla_dummy, nombre_archivo
):
    sprite = selector._cargar_sprite(nombre_archivo)
    ruta = Path(__file__).resolve().parents[2] / "assets" / "personajes" / nombre_archivo
    original = pygame.image.load(str(ruta))

    assert sprite is not None
    assert max(sprite.get_size()) == 72
    assert sprite.get_flags() & pygame.SRCALPHA
    ancho, alto = original.get_size()
    ancho_sprite, alto_sprite = sprite.get_size()
    assert ancho_sprite == max(1, round(ancho * min(72 / ancho, 72 / alto)))
    assert alto_sprite == max(1, round(alto * min(72 / ancho, 72 / alto)))
