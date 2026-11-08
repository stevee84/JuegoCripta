"""P2 §4.2: contrato de la consulta de ubicación de llaves.

Los casos salen de `specs/002-resolubilidad/contracts/consulta-llaves.md`. Lo que se
protege es que una respuesta incompleta se rechace en vez de completarse con valores por
defecto: una cripta de la que falta un dato no puede pasar por verificada.
"""
import pytest

from contratos.fuente_datos import FuenteDatos
from datos.decodificador_datos import DecodificadorDatos
from datos.fuente_offline import FuenteOffline

FIXTURES = "tests/fixtures/resolubilidad"


def _convertir(datos):
    return DecodificadorDatos().convertir_llaves(datos)


def test_el_contrato_exige_obtener_llaves():
    """Un implementador que no lo tenga no debe poder instanciarse (§4.2)."""
    class FuenteIncompleta(FuenteDatos):
        listar_criptas = obtener_generales = obtener_pagina = lambda self, *a: {}
        obtener_contenido = obtener_catalogo = lambda self, *a: {}
        obtener_version_cripta = obtener_version_catalogo = lambda self, *a: ""

    with pytest.raises(TypeError):
        FuenteIncompleta()


def test_llave_en_el_suelo_y_llave_de_enemigo():
    ubicaciones = _convertir({"llaves": [
        {"id": "itm_llave_bronce", "sala": 4},
        {"id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203"},
    ]})
    assert ubicaciones.obtener("itm_llave_bronce") == (4, None)
    assert ubicaciones.obtener("itm_llave_negra") == (12, "e-1203")


def test_sin_llaves_es_valido():
    """Una cripta sin ninguna llave no es un error."""
    assert len(_convertir({"llaves": []})) == 0


@pytest.mark.parametrize("respuesta", [
    {},
    {"llaves": None},
    {"llaves": {"id": "itm_llave_negra"}},
    {"llaves": ["itm_llave_negra"]},
    {"llaves": [{"sala": 3}]},
    {"llaves": [{"id": "", "sala": 3}]},
    {"llaves": [{"id": "itm_llave_negra"}]},
    {"llaves": [{"id": "itm_llave_negra", "sala": "tres"}]},
    {"llaves": [{"id": "itm_llave_negra", "sala": 3, "enemigo": ""}]},
    {"llaves": [{"id": "itm_llave_negra", "sala": 3, "enemigo": 17}]},
    {"llaves": [{"id": "itm_llave_negra", "sala": 3},
                {"id": "itm_llave_negra", "sala": 4}]},
])
def test_una_respuesta_mal_formada_se_rechaza(respuesta):
    with pytest.raises((ValueError, TypeError)):
        _convertir(respuesta)


def test_la_fuente_sin_conexion_lee_el_archivo_del_paquete():
    """Un dato nuevo del servicio es un archivo más del paquete, por el mismo contrato (§3.4)."""
    fuente = FuenteOffline(FIXTURES)
    ubicaciones = _convertir(fuente.obtener_llaves("cripta-enemigo"))
    assert ubicaciones.obtener("itm_llave_negra") == (2, "e-201")


def test_falta_el_archivo_de_llaves_en_el_paquete():
    """Se señala como dato ausente, no como cripta sin llaves (FR-019)."""
    from datos.cliente_api import CriptaAPIError
    with pytest.raises(CriptaAPIError):
        FuenteOffline(FIXTURES).obtener_llaves("cripta-que-no-existe")
