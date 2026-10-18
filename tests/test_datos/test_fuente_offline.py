import json
import os

import pytest

from datos.cliente_api import CriptaAPIError
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
        json.dumps({"contenido": [
            {"sala": 1, "dato": "a"}, {"sala": 2, "dato": "b"}
        ]}), encoding="utf-8"
    )
    (c1 / "version.txt").write_text("  v3  ", encoding="utf-8")

    # catalogo
    cat = tmp_path / "catalogo"
    cat.mkdir()
    (cat / "f1.json").write_text(json.dumps({"id": "f1", "nombre": "Ficha1"}), encoding="utf-8")
    (cat / "version.txt").write_text("v10\n", encoding="utf-8")

    return FuenteOffline(str(tmp_path))


def test_listar_criptas(fuente):
    assert fuente.listar_criptas() == [{"id": "c1", "nombre": "Cripta Uno"}]


def test_obtener_generales(fuente):
    assert fuente.obtener_generales("c1") == {"titulo": "C1"}


def test_obtener_generales_no_existe(fuente):
    with pytest.raises(CriptaAPIError, match="generales"):
        fuente.obtener_generales("inexistente")


def test_cripta_sin_paquete_explica_como_generarlo(fuente):
    with pytest.raises(CriptaAPIError, match="capturar_api"):
        fuente.obtener_generales("inexistente")


def test_obtener_pagina(fuente):
    assert fuente.obtener_pagina("c1", 1) == {"pag": 1}


def test_obtener_pagina_no_existe(fuente):
    with pytest.raises(CriptaAPIError, match="pagina_99"):
        fuente.obtener_pagina("c1", 99)


def test_obtener_contenido_filtrado(fuente):
    r = fuente.obtener_contenido("c1", [1])
    assert r == {"contenido": [{"sala": 1, "dato": "a"}]}


def test_obtener_contenido_sin_filtro(fuente):
    assert fuente.obtener_contenido("c1", []) == {"contenido": []}


def test_obtener_contenido_sala_faltante(fuente):
    with pytest.raises(CriptaAPIError, match=r"\[9\]"):
        fuente.obtener_contenido("c1", [1, 9])


def test_obtener_catalogo(fuente):
    r = fuente.obtener_catalogo(["f1", "f_no"])
    assert r == {"entidades": [{"id": "f1", "nombre": "Ficha1"}]}


def test_obtener_version_cripta(fuente):
    assert fuente.obtener_version_cripta("c1") == "v3"


def test_obtener_version_catalogo(fuente):
    assert fuente.obtener_version_catalogo() == "v10"


def test_version_cripta_no_existe(fuente):
    with pytest.raises(CriptaAPIError, match="nope"):
        fuente.obtener_version_cripta("nope")


def test_json_corrupto(fuente, tmp_path):
    (tmp_path / "c1" / "generales.json").write_text("{roto", encoding="utf-8")
    with pytest.raises(CriptaAPIError, match="JSON inválido"):
        fuente.obtener_generales("c1")


def test_presupuesto_es_parte_del_contrato_y_offline_no_gasta_red(fuente):
    """§6: --offline cambia la fuente sin preguntar por el tipo concreto."""
    from contratos.fuente_datos import usa_red
    from datos.cliente_api import ClienteAPI
    from datos.presupuesto_solicitudes import PresupuestoSolicitudes

    assert not usa_red(fuente) and fuente.presupuesto() is None
    fuente.asignar_presupuesto(PresupuestoSolicitudes())
    assert fuente.presupuesto() is None
    cliente = ClienteAPI("http://ejemplo.invalid")
    assert usa_red(cliente) and cliente.presupuesto() is None
    presupuesto = PresupuestoSolicitudes()
    cliente.asignar_presupuesto(presupuesto)
    assert cliente.presupuesto() is presupuesto
    assert not usa_red(object())
