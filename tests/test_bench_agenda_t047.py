"""Corrección y esquema del subbloque independiente de T047."""

import pytest

from benchmarks.terreno_cazador_integrante1 import (
    ALTERNATIVA_AGENDA,
    ALTERNATIVA_LINEAL,
    CARGAS_AGENDA,
    OPERACIONES,
    PROVEEDORES,
    PROVEEDORES_RUTAS,
    _validar_equivalencia,
    medir_agenda,
)


CAMPOS_FILA = {
    "medicion", "alternativa", "n", "carga", "semilla", "entorno",
    "calentamiento", "repeticiones", "unidad", "mediana", "p95",
    "maximo", "minimo", "muestras", "trabajo", "fixture_fuera",
    "validacion", "memoria",
}


@pytest.mark.parametrize("operacion", OPERACIONES)
def test_equivalencia_observable_antes_de_cronometrar(operacion):
    validacion = _validar_equivalencia(operacion, 64)

    assert validacion["equivalencia_observable"] is True
    assert validacion["tiempos_y_secuencias"] is True
    assert validacion["antes"]["eventos"] == 64
    assert len(validacion["antes"]["huella"]) == 64
    assert len(validacion["despues"]["huella"]) == 64
    assert len(validacion["resultado"]["huella"]) == 64


def test_reprogramar_asigna_secuencia_nueva_y_empates_respetan_secuencia():
    reprogramar = _validar_equivalencia("reprogramar", 64)
    empates = _validar_equivalencia("resolver_empates", 64)

    assert reprogramar["secuencia_nueva_reprogramar"] is True
    assert empates["orden_empates"] is True
    assert empates["resultado"]["cantidad"] == 64


def test_esquema_conserva_muestras_y_separa_memoria_de_tiempo():
    filas = medir_agenda(repeticiones=2, tamanos=(32, 64))

    assert len(filas) == 2 * len(OPERACIONES) * 2
    assert {fila["medicion"] for fila in filas} == {
        f"agenda_{operacion}" for operacion in OPERACIONES
    }
    assert {fila["alternativa"] for fila in filas} == {
        ALTERNATIVA_AGENDA, ALTERNATIVA_LINEAL
    }
    assert {fila["n"] for fila in filas} == {32, 64}
    for fila in filas:
        assert CAMPOS_FILA <= fila.keys()
        assert fila["repeticiones"] == len(fila["muestras"]) == 2
        assert fila["calentamiento"] == 1
        assert fila["unidad"] == "ns_por_lote"
        assert 0 <= fila["minimo"] <= fila["mediana"] <= fila["maximo"]
        assert fila["minimo"] <= fila["p95"] <= fila["maximo"]
        assert fila["fixture_fuera"] is True
        assert fila["validacion"]["equivalencia_observable"] is True
        assert fila["memoria"]["unidad"] == "bytes"
        assert fila["memoria"]["incluida_en_tiempo"] is False
        assert fila["memoria"]["pico_operacion"] >= 0


def test_cada_par_comparte_fixture_resultados_y_carga():
    filas = medir_agenda(repeticiones=1, tamanos=(32,))
    por_medicion = {}
    for fila in filas:
        por_medicion.setdefault(fila["medicion"], []).append(fila)

    assert len(por_medicion) == len(OPERACIONES)
    for variantes in por_medicion.values():
        assert len(variantes) == 2
        assert len({fila["carga"]["huella_fixture"] for fila in variantes}) == 1
        assert len({fila["validacion"]["antes"]["huella"] for fila in variantes}) == 1
        assert len({fila["validacion"]["despues"]["huella"] for fila in variantes}) == 1
        assert len({fila["validacion"]["resultado"]["huella"] for fila in variantes}) == 1


def test_cargas_por_defecto_son_cientos_de_eventos_y_varias_cargas():
    assert len(CARGAS_AGENDA) >= 3
    assert min(CARGAS_AGENDA) >= 100


def test_proveedor_queda_disponible_para_integracion_posterior():
    assert PROVEEDORES[0] is medir_agenda
    assert PROVEEDORES[1:] == PROVEEDORES_RUTAS


def test_no_hay_umbral_temporal_en_el_contrato():
    filas = medir_agenda(repeticiones=1, tamanos=(32,))
    assert all("umbral" not in fila for fila in filas)
