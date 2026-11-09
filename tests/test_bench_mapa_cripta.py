"""Contrato de T072–T075 para el benchmark aislado de MapaCripta."""

import pytest


CAMPOS_FILA = {
    "medicion", "alternativa", "n", "carga", "semilla", "entorno",
    "calentamiento", "repeticiones", "unidad", "mediana", "p95",
    "maximo", "minimo", "muestras", "trabajo", "fixture_fuera",
}


def _filas(repeticiones=2, tamanos=(8, 16)):
    from benchmarks.mapa_cripta_integrante1 import medir_mapa_cripta

    return medir_mapa_cripta(repeticiones=repeticiones, tamanos=tamanos)


def test_esquema_separa_construccion_busqueda_y_vinculacion():
    filas = _filas()
    mediciones = {fila["medicion"] for fila in filas}
    assert {
        "mapa_construccion_indice",
        "mapa_construccion_lista_lineal_alternativa",
        "mapa_busqueda_id",
        "mapa_vinculacion_salidas",
    } <= mediciones

    assert {fila["n"] for fila in filas} == {8, 16}
    assert {fila["carga"]["salidas_por_sala"] for fila in filas} >= {1, 4}
    for fila in filas:
        assert CAMPOS_FILA <= fila.keys()
        assert fila["calentamiento"] == 1
        assert fila["repeticiones"] == len(fila["muestras"]) == 2
        assert fila["unidad"] == "ns_por_lote"
        assert 0 <= fila["minimo"] <= fila["mediana"] <= fila["maximo"]
        assert fila["minimo"] <= fila["p95"] <= fila["maximo"]
        assert fila["fixture_fuera"] is True
        assert fila["entorno"]["reloj"] == "perf_counter_ns"

    construcciones = [
        fila for fila in filas if fila["medicion"].startswith(
            "mapa_construccion_")
    ]
    por_carga = {}
    for fila in construcciones:
        clave = (fila["n"], fila["carga"]["salidas_por_sala"])
        por_carga.setdefault(clave, []).append(fila)
        assert fila["carga"]["identidad_instancias"] is True
        assert fila["memoria"]["alcance"] == (
            "contenedores_sin_instancias_compartidas")
        assert fila["memoria"]["lista_bytes"] > 0
        assert fila["memoria"]["indice_bytes"] >= 0
    for variantes in por_carga.values():
        assert len(variantes) == 2
        assert len({
            fila["carga"]["huella_orden_ids"] for fila in variantes
        }) == 1


def test_consultas_indexadas_y_lineales_usan_misma_carga_y_resultados():
    filas = [fila for fila in _filas() if fila["medicion"] == "mapa_busqueda_id"]
    por_carga = {}
    for fila in filas:
        clave = (fila["n"], fila["carga"]["consultas"])
        por_carga.setdefault(clave, []).append(fila)

    assert por_carga
    for variantes in por_carga.values():
        assert {fila["alternativa"] for fila in variantes} == {
            "tabla_hash_propia", "recorrido_lineal_benchmark"
        }
        assert len({fila["carga"]["huella_resultados"] for fila in variantes}) == 1
        assert len({fila["trabajo"]["consultas"] for fila in variantes}) == 1


def test_vinculacion_equivalente_conserva_orden_destinos_y_aliases():
    filas = [
        fila for fila in _filas()
        if fila["medicion"] == "mapa_vinculacion_salidas"
    ]
    por_carga = {}
    for fila in filas:
        clave = (fila["n"], fila["carga"]["salidas"])
        por_carga.setdefault(clave, []).append(fila)

    assert por_carga
    for variantes in por_carga.values():
        assert {fila["alternativa"] for fila in variantes} == {
            "vinculacion_indexada", "resolucion_lineal_benchmark"
        }
        assert len({fila["carga"]["huella_enlaces"] for fila in variantes}) == 1
        assert all(fila["carga"]["identidad_canonica"] for fila in variantes)
        assert len({fila["trabajo"]["salidas"] for fila in variantes}) == 1


def test_proveedor_se_conecta_por_la_interfaz_estandar(monkeypatch):
    from benchmarks import integrante3
    from benchmarks.mapa_cripta_integrante1 import PROVEEDORES

    monkeypatch.setattr(
        integrante3, "_medir_agenda_existente", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        integrante3, "_medir_ciclo_existente", lambda *args, **kwargs: [])
    informe = integrante3.ejecutar(
        repeticiones=1, tamanos=(8,), proveedores=PROVEEDORES)
    nombres = {fila["medicion"] for fila in informe["mediciones"]}
    assert {
        "mapa_construccion_indice",
        "mapa_busqueda_id",
        "mapa_vinculacion_salidas",
    } <= nombres


def test_main_bench_incluye_filas_del_mapa():
    """T049 completada: `main.py --bench` registra el proveedor del mapa de 001.

    Un benchmark que ningún punto de entrada ejecuta no cuenta como evidencia
    (Principio IX), así que la medición del índice tiene que salir por `--bench`.
    """
    from benchmarks.integrante3 import ejecutar
    from benchmarks.bench_ampliado import PROVEEDORES as ADICIONALES
    from benchmarks.integrante2 import PROVEEDORES as DATOS
    from benchmarks.mapa_cripta_integrante1 import PROVEEDORES as MAPA

    registrados = DATOS + ADICIONALES + MAPA
    for proveedor in MAPA:
        assert proveedor in registrados

    filas = ejecutar(repeticiones=1, tamanos=(8,), proveedores=registrados)["mediciones"]
    nombres = {f["medicion"] for f in filas}
    assert any(n.startswith("mapa_") for n in nombres), "--bench no mide el mapa"
