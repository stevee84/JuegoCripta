import json

import pytest

from datos.repositorio_puntajes import RepositorioPuntajes


def resultado(nombre="José", acciones=20):
    return {
        "nombre_jugador": nombre,
        "cripta_id": "c1",
        "version_cripta": "v3",
        "acciones_ejecutadas": acciones,
        "enemigos_derrotados": 2,
        "tiempo_virtual_final": 1250,
        "version_catalogo": "cat1",
    }


def test_listar_sin_archivo_no_crea_persistencia(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert RepositorioPuntajes().listar() == []
    assert not (tmp_path / "puntajes.dat").exists()


def test_persistencia_entre_instancias_sin_perdida_ni_clasificacion(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    primero = resultado("José\nÑ", 50)
    segundo = resultado("Ana", 1)
    repositorio = RepositorioPuntajes()
    repositorio.registrar_resultado(primero)
    ruta = tmp_path / "puntajes.dat"
    antes = ruta.read_bytes()
    RepositorioPuntajes().registrar_resultado(segundo)

    assert ruta.read_bytes().startswith(antes)
    assert repositorio.listar() == [primero, segundo]
    assert RepositorioPuntajes().listar() == [primero, segundo]
    assert len(ruta.read_text(encoding="utf-8").splitlines()) == 2
    assert "puntaje" not in repositorio.listar()[0]


def test_cambiar_diccionarios_no_modifica_registros_guardados(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    original = resultado()
    RepositorioPuntajes().registrar_resultado(original)
    original["nombre_jugador"] = "cambiado"
    leidos = RepositorioPuntajes().listar()
    leidos[0]["acciones_ejecutadas"] = 999
    assert RepositorioPuntajes().listar() == [resultado()]


@pytest.mark.parametrize("invalido", [[], {"actor": object()}, {"tiempo": float("nan")}])
def test_resultado_no_serializable_no_dana_el_archivo(tmp_path, monkeypatch, invalido):
    monkeypatch.chdir(tmp_path)
    repositorio = RepositorioPuntajes()
    repositorio.registrar_resultado(resultado())
    ruta = tmp_path / "puntajes.dat"
    anterior = ruta.read_bytes()
    with pytest.raises((TypeError, ValueError)):
        repositorio.registrar_resultado(invalido)
    assert ruta.read_bytes() == anterior


@pytest.mark.parametrize("contenido", ['{"incompleto":\n', "[]\n"])
def test_archivo_invalido_no_se_oculta_ni_se_borra(tmp_path, monkeypatch, contenido):
    monkeypatch.chdir(tmp_path)
    ruta = tmp_path / "puntajes.dat"
    ruta.write_text(contenido, encoding="utf-8")
    anterior = ruta.read_bytes()
    with pytest.raises((ValueError, json.JSONDecodeError)):
        RepositorioPuntajes().listar()
    assert ruta.read_bytes() == anterior
