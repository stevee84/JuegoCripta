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


def test_leer_con_version_una_sola_lectura(almacen, monkeypatch):
    """El método que usa el repositorio: versión y datos de un solo open/json.load."""
    almacen.guardar("f1", {"nombre": "Espada"}, "v1")
    aperturas = []
    abrir_real = open
    monkeypatch.setattr("builtins.open", lambda *a, **k: (aperturas.append(a[0]), abrir_real(*a, **k))[1])
    assert almacen.leer_con_version("f1") == ("v1", {"nombre": "Espada"})
    assert len(aperturas) == 1


def test_leer_con_version_inexistente(almacen):
    assert almacen.leer_con_version("nope") == (None, None)


def test_fallo_al_guardar_se_registra(almacen, caplog):
    """Un disco lleno o sin permisos no puede desaparecer en silencio."""
    import datos.almacen_persistente as modulo

    def explotar(*_a, **_k):
        raise OSError("disco lleno")

    original = modulo.os.makedirs
    modulo.os.makedirs = explotar
    try:
        with caplog.at_level("ERROR", logger="cripta"):
            almacen.guardar("f1", {}, "v1")
    finally:
        modulo.os.makedirs = original
    assert "No se pudo persistir" in caplog.text and "f1" in caplog.text


def test_ficha_corrupta_se_registra(almacen, tmp_path, caplog):
    ruta = tmp_path / "catalogo"
    ruta.mkdir(exist_ok=True)
    (ruta / "bad.json").write_text("no es json{{{", encoding="utf-8")
    with caplog.at_level("WARNING", logger="cripta"):
        assert almacen.leer("bad") is None
    assert "corrupta" in caplog.text


def test_sobrescribir(almacen):
    almacen.guardar("f1", {"a": 1}, "v1")
    almacen.guardar("f1", {"a": 2}, "v2")
    assert almacen.leer("f1") == {"a": 2}
    assert almacen.validar_version("f1", "v2") is True
