import json
import os

import pytest

from datos.fuente_offline import FuenteOffline


@pytest.fixture
def fuente(tmp_path):
    # criptas.json
    criptas = [{"id": "c1", "nombre": "Cripta Uno"}]
    (tmp_path / "criptas.json").write_text(json.dumps(criptas), encoding="utf-8")

    # cripta c1
    c1 = tmp_path / "c1"
    c1.mkdir()
    (c1 / "generales.json").write_text(json.dumps({"titulo": "C1"}), encoding="utf-8")
    (c1 / "pagina_1.json").write_text(json.dumps({"pag": 1}), encoding="utf-8")
    (c1 / "contenido.json").write_text(
        json.dumps({"s1": {"dato": "a"}, "s2": {"dato": "b"}}), encoding="utf-8"
    )
    (c1 / "version.txt").write_text("  v3  ", encoding="utf-8")

    # catalogo
    cat = tmp_path / "catalogo"
    cat.mkdir()
    (cat / "f1.json").write_text(json.dumps({"nombre": "Ficha1"}), encoding="utf-8")
    (cat / "version.txt").write_text("v10\n", encoding="utf-8")

    return FuenteOffline(str(tmp_path))


def test_listar_criptas(fuente):
    assert fuente.listar_criptas() == [{"id": "c1", "nombre": "Cripta Uno"}]


def test_obtener_generales(fuente):
    assert fuente.obtener_generales("c1") == {"titulo": "C1"}


def test_obtener_generales_no_existe(fuente):
    assert fuente.obtener_generales("inexistente") == {}


def test_obtener_pagina(fuente):
    assert fuente.obtener_pagina("c1", 1) == {"pag": 1}


def test_obtener_pagina_no_existe(fuente):
    assert fuente.obtener_pagina("c1", 99) == {}


def test_obtener_contenido_filtrado(fuente):
    r = fuente.obtener_contenido("c1", ["s1"])
    assert r == {"s1": {"dato": "a"}}


def test_obtener_contenido_sin_filtro(fuente):
    r = fuente.obtener_contenido("c1", [])
    assert r == {}


def test_obtener_catalogo(fuente):
    r = fuente.obtener_catalogo(["f1", "f_no"])
    assert "f1" in r
    assert "f_no" not in r


def test_obtener_version_cripta(fuente):
    assert fuente.obtener_version_cripta("c1") == "v3"


def test_obtener_version_catalogo(fuente):
    assert fuente.obtener_version_catalogo() == "v10"


def test_version_cripta_no_existe(fuente):
    assert fuente.obtener_version_cripta("nope") == ""
