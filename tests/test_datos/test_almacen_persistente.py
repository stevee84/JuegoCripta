import json

import pytest

from datos.almacen_persistente import AlmacenPersistente


@pytest.fixture
def almacen(tmp_path):
    return AlmacenPersistente(ruta_base=str(tmp_path / "catalogo"))


def test_guardar_y_leer(almacen):
    almacen.guardar("f1", {"nombre": "Espada"}, "v1")
    assert almacen.leer("f1") == {"nombre": "Espada"}


def test_leer_inexistente(almacen):
    assert almacen.leer("nope") is None


def test_validar_version_correcta(almacen):
    almacen.guardar("f1", {}, "v5")
    assert almacen.validar_version("f1", "v5") is True


def test_validar_version_incorrecta(almacen):
    almacen.guardar("f1", {}, "v5")
    assert almacen.validar_version("f1", "v3") is False


def test_validar_version_inexistente(almacen):
    assert almacen.validar_version("nope", "v1") is False


def test_leer_archivo_corrupto(almacen, tmp_path):
    ruta = tmp_path / "catalogo"
    ruta.mkdir(exist_ok=True)
    (ruta / "bad.json").write_text("no es json{{{", encoding="utf-8")
    assert almacen.leer("bad") is None
    # El archivo corrupto debe haberse eliminado
    assert not (ruta / "bad.json").exists()


def test_sobrescribir(almacen):
    almacen.guardar("f1", {"a": 1}, "v1")
    almacen.guardar("f1", {"a": 2}, "v2")
    assert almacen.leer("f1") == {"a": 2}
    assert almacen.validar_version("f1", "v2") is True
