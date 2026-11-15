"""Contrato de T072–T075 y evidencia oficial de MapaCripta."""

import json
from pathlib import Path
import sys


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


def test_main_bench_incluye_filas_del_mapa(monkeypatch):
    """T049/T072: el punto de entrada real registra una vez el proveedor.

    Un benchmark que ningún punto de entrada ejecuta no cuenta como evidencia
    (Principio IX). Se intercepta el ejecutor para no repetir las 916 mediciones.
    """
    import benchmarks.integrante3 as integrante3
    from benchmarks.mapa_cripta_integrante1 import PROVEEDORES as MAPA
    import main

    capturados = []

    def ejecutar(proveedores=()):
        capturados.extend(proveedores)
        return {"mediciones": [], "proveedores": len(proveedores)}

    monkeypatch.setattr(sys, "argv", ["main.py", "--bench"])
    monkeypatch.setattr(integrante3, "ejecutar", ejecutar)
    main.main()

    assert len(capturados) == len({id(proveedor) for proveedor in capturados}) == 25
    assert tuple(proveedor for proveedor in capturados if proveedor in MAPA) == MAPA
    assert all(capturados.count(proveedor) == 1 for proveedor in MAPA)


def test_ejecucion_oficial_t050_contiene_las_60_filas_del_mapa():
    """T072 valida la evidencia real sin volver a ejecutar el benchmark."""
    ruta = (
        Path(__file__).resolve().parents[1]
        / "benchmarks/resultados/main_bench_completo_t050.json"
    )
    informe = json.loads(ruta.read_text(encoding="utf-8"))
    filtrado = json.loads(
        (ruta.parents[1] / "resultados_terreno_cazador_integrante1.json")
        .read_text(encoding="utf-8")
    )
    nombres_mapa = {
        "mapa_construccion_indice",
        "mapa_construccion_lista_lineal_alternativa",
        "mapa_busqueda_id",
        "mapa_vinculacion_salidas",
    }
    filas = [
        fila for fila in informe["mediciones"]
        if fila["medicion"] in nombres_mapa
    ]
    filas_filtradas = [
        fila for fila in filtrado["mediciones"]
        if fila["medicion"] in nombres_mapa
    ]

    assert informe["repeticiones"] == 15
    assert filas_filtradas == filas
    assert len(filas) == 60
    assert {fila["n"] for fila in filas} == {8, 16, 32, 64, 128, 512}
    assert {
        fila["carga"]["salidas_por_sala"] for fila in filas
    } == {1, 4}
    assert {
        fila["medicion"]: {
            otra["alternativa"] for otra in filas
            if otra["medicion"] == fila["medicion"]
        }
        for fila in filas
    } == {
        "mapa_construccion_indice": {"lista_mas_tabla_hash_propia"},
        "mapa_construccion_lista_lineal_alternativa": {
            "lista_lineal_benchmark"
        },
        "mapa_busqueda_id": {
            "tabla_hash_propia", "recorrido_lineal_benchmark"
        },
        "mapa_vinculacion_salidas": {
            "vinculacion_indexada", "resolucion_lineal_benchmark"
        },
    }

    claves = [
        (
            fila["medicion"], fila["alternativa"], fila["n"],
            fila["carga"]["salidas_por_sala"],
        )
        for fila in filas
    ]
    assert len(claves) == len(set(claves)) == 60
    for fila in filas:
        assert CAMPOS_FILA <= fila.keys()
        assert fila["semilla"] == 1729
        assert fila["calentamiento"] == 1
        assert fila["repeticiones"] == len(fila["muestras"]) == 15
        assert fila["unidad"] == "ns_por_lote"
        assert fila["fixture_fuera"] is True
        muestras = sorted(fila["muestras"])
        assert fila["minimo"] == muestras[0]
        assert fila["mediana"] == muestras[7]
        assert fila["p95"] == fila["maximo"] == muestras[-1]

    construcciones = [
        fila for fila in filas
        if fila["medicion"].startswith("mapa_construccion_")
    ]
    por_carga = {}
    for fila in construcciones:
        clave = (fila["n"], fila["carga"]["salidas_por_sala"])
        por_carga.setdefault(clave, []).append(fila)
    assert len(por_carga) == 12
    for variantes in por_carga.values():
        assert len(variantes) == 2
        assert all(fila["carga"]["identidad_instancias"] for fila in variantes)
        assert len({fila["carga"]["huella_orden_ids"] for fila in variantes}) == 1
        assert all(fila["trabajo"]["altas"] == fila["n"] for fila in variantes)

    consultas = [
        fila for fila in filas if fila["medicion"] == "mapa_busqueda_id"
    ]
    por_tamano = {}
    for fila in consultas:
        por_tamano.setdefault(fila["n"], []).append(fila)
    assert len(por_tamano) == 6
    for variantes in por_tamano.values():
        assert len(variantes) == 2
        assert len({fila["carga"]["huella_resultados"] for fila in variantes}) == 1
        assert len({fila["carga"]["consultas"] for fila in variantes}) == 1
        assert all(
            fila["trabajo"]["consultas"] == fila["carga"]["consultas"]
            for fila in variantes
        )

    vinculaciones = [
        fila for fila in filas
        if fila["medicion"] == "mapa_vinculacion_salidas"
    ]
    por_carga = {}
    for fila in vinculaciones:
        clave = (fila["n"], fila["carga"]["salidas_por_sala"])
        por_carga.setdefault(clave, []).append(fila)
    assert len(por_carga) == 12
    for variantes in por_carga.values():
        assert len(variantes) == 2
        assert all(fila["carga"]["identidad_canonica"] for fila in variantes)
        assert len({fila["carga"]["huella_enlaces"] for fila in variantes}) == 1
        assert all(
            fila["trabajo"]["salidas"] == fila["carga"]["salidas"]
            for fila in variantes
        )
