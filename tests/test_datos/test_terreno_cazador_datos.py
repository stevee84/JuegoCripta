"""T010/T018: contrato integrado de costo, simetría y rango."""

import pytest

from datos.decodificador_datos import DecodificadorDatos
from dto.sala import Puerta
from estructuras.tabla_hash import TablaHashImpl
from service.inicializador_partida import InicializadorPartida


def _sala(salida):
    return DecodificadorDatos().convertir_sala({
        "id": 1, "nombre": "Origen", "salidas": {"N": salida},
    })


def _enemigo_cazador(rango_marker=600):
    ficha = {
        "id": "cazador", "clase": "enemigo", "nombre": "Cazador",
        "vida_max": 20, "ataque": 5, "defensa": 2, "velocidad": 100,
        "comportamiento": "cazador", "suelta": [],
    }
    if rango_marker is not ...:
        ficha["rango"] = rango_marker
    contenido = {"contenido": [{
        "sala": 1,
        "enemigos": [{"instancia": "c1", "tipo": "cazador"}],
        "objetos": [], "trampas": [],
    }]}
    return DecodificadorDatos().convertir_contenido(
        contenido, {"entidades": [ficha]}).obtener(1)["enemigos"][0]


def test_costo_ausente_es_cien_y_presente_no_se_hereda():
    assert _sala({"sala": 2}).puertas[0].costo == 100
    assert _sala({"sala": 2, "costo": 37}).puertas[0].costo == 37


@pytest.mark.parametrize("costo", [True, False, 0, -1, "100", 1.5, None])
def test_costo_presente_invalido_se_rechaza_sin_sustituir(costo):
    with pytest.raises((TypeError, ValueError), match="costo"):
        _sala({"sala": 2, "costo": costo})


def _costos(*registros):
    costos = TablaHashImpl()
    for origen, destino, costo, puerta_id in registros:
        puerta = Puerta(puerta_id, destino, "NORTE")
        puerta.costo = costo
        InicializadorPartida._registrar_costo(costos, origen, puerta)
    return costos


def test_sentido_unico_es_valido_y_par_existente_debe_ser_simetrico():
    InicializadorPartida._validar_simetria(_costos((1, 2, 40, "ida")))
    InicializadorPartida._validar_simetria(_costos(
        (1, 2, 40, "ida"), (2, 1, 40, "vuelta")))
    with pytest.raises(ValueError, match="distintos en cada sentido"):
        InicializadorPartida._validar_simetria(_costos(
            (1, 2, 40, "ida"), (2, 1, 41, "vuelta")))


def test_multiplicidad_con_costos_distintos_se_rechaza():
    with pytest.raises(ValueError, match="dos salidas"):
        _costos((1, 2, 40, "norte"), (1, 2, 41, "este"))


@pytest.mark.parametrize("rango", [0, 1, 600])
def test_rango_cazador_es_entero_mayor_o_igual_que_cero(rango):
    assert _enemigo_cazador(rango).rango == rango


@pytest.mark.parametrize("rango", [..., -1, True, "600", 600.0, None])
def test_rango_ausente_o_invalido_se_rechaza_sin_default(rango):
    with pytest.raises((TypeError, ValueError), match="rango"):
        _enemigo_cazador(rango)
