"""Corrección y esquema del productor de ciclos sintéticos T048."""

import pytest

from benchmarks.benchmark_ciclo_real_integrante1 import (
    ALTERNATIVA_CICLO_CORRIENTE,
    ALTERNATIVA_CICLO_RETENIDA,
    CAZADORES_CICLO,
    FASES_CICLO_CORRIENTE,
    FASES_CICLO_RETENIDA,
    PROVEEDORES,
    _argumentos,
    _clasificar,
    _escenario_ciclo_sintetico,
    _huella_estado_ciclo,
    ejecutar,
    medir_ciclos_sinteticos,
)


@pytest.fixture(scope="module")
def filas_ciclo():
    return medir_ciclos_sinteticos(repeticiones=1, tamanos=(24,))


def test_plantillas_reales_tienen_costos_variables_salidas_dirigidas_y_cierre():
    estable = _escenario_ciclo_sintetico(24, 28, True, True)
    inestable = _escenario_ciclo_sintetico(24, 28, False, False)

    for escenario in (estable, inestable):
        estado = escenario.plantilla
        cazadores = [
            enemigo
            for sala in estado.mapa.obtener_salas()
            for enemigo in sala.enemigos
        ]
        costos = {
            puerta.costo
            for sala in estado.mapa.obtener_salas()
            for puerta in sala.puertas
        }
        assert len(cazadores) == 28
        assert all(cazador.activo for cazador in cazadores)
        assert len(costos) > 1
        assert min(costos) >= 100
        assert max(costos) <= 130

        saltos = [
            (sala.id_sala, puerta.destino_sala_id)
            for sala in estado.mapa.obtener_salas()
            for puerta in sala.puertas
            if puerta.id_puerta.startswith("salto-")
        ]
        assert saltos
        for origen, destino in saltos:
            vuelta_directa = estado.mapa.obtener_sala(destino).puertas
            assert not any(puerta.destino_sala_id == origen
                           for puerta in vuelta_directa)

    assert not any(
        evento.tipo == "CERRAR_PUERTA"
        for evento in estable.plantilla.agenda.recorrer())
    assert sum(
        evento.tipo == "CERRAR_PUERTA"
        for evento in inestable.plantilla.agenda.recorrer()) == 1


def test_plantilla_sintetica_es_determinista():
    primera = _escenario_ciclo_sintetico(24, 1, True, False)
    segunda = _escenario_ciclo_sintetico(24, 1, True, False)
    assert _huella_estado_ciclo(primera.plantilla) == _huella_estado_ciclo(
        segunda.plantilla)


def test_matriz_cubre_uno_decenas_rangos_y_puertas(filas_ciclo):
    assert len(filas_ciclo) == 16
    assert {fila["carga"]["cazadores"] for fila in filas_ciclo} == {
        1, CAZADORES_CICLO}
    assert {fila["carga"]["rango_tipo"] for fila in filas_ciclo} == {
        "pequeno", "grande"}
    assert {fila["carga"]["puertas_tipo"] for fila in filas_ciclo} == {
        "estable", "inestable"}
    assert {fila["alternativa"] for fila in filas_ciclo} == {
        ALTERNATIVA_CICLO_CORRIENTE, ALTERNATIVA_CICLO_RETENIDA}
    assert all(fila["carga"]["costos_salida_variables"] is True
               for fila in filas_ciclo)


def test_cada_muestra_es_un_ciclo_completo_y_clasifica_resultados(filas_ciclo):
    for fila in filas_ciclo:
        muestra = fila["muestras"][0]
        assert muestra["clasificacion"] == "completo"
        assert muestra["exito"] is True
        assert muestra["huella_intervalo"]
        assert fila["clasificaciones"]["completo"] == 1
        assert fila["clasificaciones"]["rechazada"] == 0
        assert fila["clasificaciones"]["muerte"] == 0
        assert fila["clasificaciones"]["victoria"] == 0
        assert fila["clasificaciones"]["incompleto"] == 0
        assert fila["clasificaciones"]["error"] == 0


def test_puerta_inestable_cierra_y_retencion_reconstruye_con_decenas(
        filas_ciclo):
    retenidas_inestables_decenas = []
    for fila in filas_ciclo:
        inestable = fila["carga"]["puertas_tipo"] == "inestable"
        assert fila["trabajo"]["eventos_puerta"] == (1 if inestable else 0)
        if (inestable
                and fila["carga"]["cazadores"] == CAZADORES_CICLO
                and fila["alternativa"] == ALTERNATIVA_CICLO_RETENIDA):
            retenidas_inestables_decenas.append(fila)
    reconstruidas = [
        fila for fila in retenidas_inestables_decenas
        if fila["trabajo"]["invalidaciones_retenidas"] >= 1
    ]
    assert reconstruidas
    for fila in reconstruidas:
        assert fila["trabajo"]["reconstrucciones_retenidas"] >= 1
        assert "puertas" in fila["trabajo"]["razones_invalidacion"]


def test_fases_auxiliares_memoria_y_equivalencia_quedan_explicitas(filas_ciclo):
    for fila in filas_ciclo:
        assert fila["validacion"]["equivalencia_observable"] is True
        assert fila["validacion"]["contadores_internos_comparados"] is False
        assert fila["memoria"]["incluida_en_tiempo"] is False
        assert fila["memoria"]["pico_intervalo"] >= 0
        if fila["alternativa"] == ALTERNATIVA_CICLO_RETENIDA:
            assert set(fila["fases"]) == set(FASES_CICLO_RETENIDA)
            assert fila["trabajo"]["construcciones_retenidas"] >= 1
            assert fila["fases"]["limpieza"]["total"] >= 0
        else:
            assert set(fila["fases"]) == set(FASES_CICLO_CORRIENTE)
            assert "construcciones_retenidas" not in fila["trabajo"]


def test_carga_sintetica_no_afirma_referencia_oficial(filas_ciclo):
    for fila in filas_ciclo:
        assert fila["origen_carga"] == "sintetico"
        assert fila["referencia_oficial"] == "pendiente_publicacion_g6"
        assert fila["afirma_pr001"] is False
        assert "umbral" not in fila


def test_resultado_nulo_se_reporta_como_ciclo_incompleto():
    assert _clasificar(None, object()) == "incompleto"


def test_proveedor_ciclo_queda_disponible_sin_registrar_main():
    assert PROVEEDORES == (medir_ciclos_sinteticos,)


def test_cripta_real_disponible_reconecta_catalogo_vivo_sin_ser_oficial():
    informe = ejecutar(_argumentos([
        "--datos-offline", "tests/fixtures/api_real",
        "--cripta", "cripta-01",
        "--muestras", "1",
        "--calentamiento", "0",
    ]))

    assert informe["origen_carga"] == "criptas_reales_disponibles"
    assert informe["referencia_oficial"] == "pendiente_publicacion_g6"
    assert informe["afirma_pr001"] is False
    assert len(informe["resultados"]) == 1
    resultado = informe["resultados"][0]
    assert resultado["cripta_id"] == "cripta-01"
    assert resultado["ciclos_completos"] == 1
    assert resultado["carga_previa"]["fichas_cargadas"] > 0
