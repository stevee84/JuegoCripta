"""T046 (spec 004): las mediciones de la línea de tiempo están conectadas a --bench (constitución IX).

Corre el proveedor con una partida corta y comprueba que trae cada medición de T041 a T045
(FR-024 a FR-027) y que las comprobaciones de equivalencia pasan antes de mirar tiempos.
"""

import sys

import benchmarks.linea_tiempo as bench_linea


def test_fr024_a_fr027_el_proveedor_trae_todas_las_mediciones():
    filas = bench_linea.medir_linea_tiempo(repeticiones=2, acciones=60)
    nombres = [fila["medicion"] for fila in filas]
    for esperada in ("linea_tiempo_historia", "linea_tiempo_accion_sin_punto",
                     "linea_tiempo_accion_con_punto", "linea_tiempo_adelante_vs_atras",
                     "retroceso_punta_a_punta", "replay_completo", "replay_version_incompatible",
                     "inventario_vista_ordenada", "inventario_recoger_lleno"):
        assert esperada in nombres, esperada
    historia = [f for f in filas if f["medicion"] == "linea_tiempo_historia"]
    assert [f["k"] for f in historia] == [10, 50, 200, "sin puntos de control"]
    for fila in historia:
        limite = 10 ** 9 if fila["k"] == "sin puntos de control" else fila["k"]
        assert fila["max_transacciones_por_consulta"] <= limite
        assert fila["memoria_puntos_mb_estimada"] >= 0
    for fila in filas:
        if fila["medicion"] == "linea_tiempo_adelante_vs_atras":
            assert fila["mismo_estado"], fila
        if fila["medicion"] == "inventario_vista_ordenada":
            assert fila["orden_real_intacto"], fila
        if fila["medicion"] in ("replay_version_incompatible", "inventario_recoger_lleno"):
            assert fila["rechazado"], fila


def test_fr016_main_bench_registra_el_proveedor_y_el_k(monkeypatch):
    """--bench conecta el proveedor de la 004 una sola vez y le pasa --checkpoint-cada."""
    import benchmarks.integrante3 as integrante3
    import main

    capturados = []

    def ejecutar(proveedores=()):
        capturados.extend(proveedores)
        return {}

    monkeypatch.setattr(integrante3, "ejecutar", ejecutar)
    monkeypatch.setattr(sys, "argv", ["main.py", "--bench", "--checkpoint-cada", "25"])
    main.main()
    assert capturados.count(bench_linea.medir_linea_tiempo) == 1
    assert bench_linea.K_CONFIGURADO == 25
    monkeypatch.setattr(bench_linea, "K_CONFIGURADO", None)
