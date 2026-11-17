"""Despacho de cargas propias de 001 desde el ejecutor común (T049)."""

import inspect

import pytest

import benchmarks.benchmark_ciclo_real_integrante1 as ciclo
import benchmarks.terreno_cazador_integrante1 as terreno


CASOS_TERRENO = (
    ("medir_agenda_main", "medir_agenda", terreno.CARGAS_AGENDA),
    (
        "medir_agenda_ciclo_main",
        "medir_agenda_ciclo",
        terreno.CARGAS_AGENDA_CICLO,
    ),
    (
        "medir_rutas_region_main",
        "medir_rutas_region",
        terreno.CARGAS_RUTAS_REGION,
    ),
)


@pytest.mark.parametrize("adaptador,proveedor,cargas", CASOS_TERRENO)
def test_adaptador_terreno_despacha_una_vez_con_carga_propia(
        monkeypatch, adaptador, proveedor, cargas):
    llamadas = []

    def sustituto(*, repeticiones, tamanos):
        llamadas.append((repeticiones, tamanos))
        return [proveedor]

    monkeypatch.setattr(terreno, proveedor, sustituto)

    resultado = getattr(terreno, adaptador)(
        repeticiones=7,
        tamanos=(8, 16, 999),
    )

    assert resultado == [proveedor]
    assert llamadas == [(7, cargas)]


def test_adaptador_matriz_anade_t054_una_vez_con_cargas_propias(monkeypatch):
    llamadas = []

    def matriz(*, repeticiones, tamanos):
        llamadas.append(("matriz", repeticiones, tamanos))
        return ["matriz"]

    def ir_a(*, repeticiones, tamanos, incluir_publicado):
        llamadas.append(
            ("ir_a", repeticiones, tamanos, incluir_publicado))
        return ["ir_a"]

    monkeypatch.setattr(terreno, "medir_rutas_matriz", matriz)
    monkeypatch.setattr(terreno, "medir_paso_ir_a_001", ir_a)

    resultado = terreno.medir_rutas_matriz_main(
        repeticiones=7,
        tamanos=(8, 16, 999),
    )

    assert resultado == ["matriz", "ir_a"]
    assert llamadas == [
        ("matriz", 7, terreno.CARGAS_RUTAS_MATRIZ),
        ("ir_a", 7, terreno.CARGAS_IR_A, True),
    ]


def test_adaptador_ciclo_despacha_una_vez_con_32_y_64(monkeypatch):
    llamadas = []

    def sustituto(*, repeticiones, tamanos):
        llamadas.append((repeticiones, tamanos))
        return ["ciclo"]

    monkeypatch.setattr(ciclo, "medir_ciclos_sinteticos", sustituto)

    resultado = ciclo.medir_ciclos_sinteticos_main(
        repeticiones=5,
        tamanos=(8, 16, 128),
    )

    assert resultado == ["ciclo"]
    assert llamadas == [(5, ciclo.CARGAS_CICLO_SINTETICO_MAIN)]
    assert ciclo.CARGAS_CICLO_SINTETICO_MAIN == (32, 64)


def test_adaptadores_publican_la_firma_estandar_sin_duplicados():
    adaptadores = terreno.PROVEEDORES_MAIN + ciclo.PROVEEDORES_MAIN

    assert terreno.PROVEEDORES_MAIN == (
        terreno.medir_agenda_main,
        terreno.medir_agenda_ciclo_main,
        terreno.medir_rutas_region_main,
        terreno.medir_rutas_matriz_main,
    )
    assert ciclo.PROVEEDORES_MAIN == (ciclo.medir_ciclos_sinteticos_main,)
    assert len(adaptadores) == len({id(proveedor) for proveedor in adaptadores}) == 5
    assert not set(adaptadores).intersection(terreno.PROVEEDORES + ciclo.PROVEEDORES)
    for proveedor in adaptadores:
        assert tuple(inspect.signature(proveedor).parameters) == (
            "repeticiones",
            "tamanos",
        )


def test_registro_propuesto_conserva_existentes_sin_duplicados():
    from benchmarks.bench_ampliado import PROVEEDORES as adicionales
    from benchmarks.integrante2 import PROVEEDORES as existentes
    from benchmarks.linea_tiempo import PROVEEDORES as linea
    from benchmarks.mapa_cripta_integrante1 import PROVEEDORES as mapa

    registrados = (
        existentes
        + adicionales
        + mapa
        + linea
        + terreno.PROVEEDORES_MAIN
        + ciclo.PROVEEDORES_MAIN
    )

    assert len(registrados) == len({id(proveedor) for proveedor in registrados}) == 25


def test_tuplas_originales_permanecen_intactas():
    assert terreno.PROVEEDORES_AGENDA == (
        terreno.medir_agenda,
        terreno.medir_agenda_ciclo,
    )
    assert terreno.PROVEEDORES_RUTAS == (
        terreno.medir_rutas_region,
        terreno.medir_rutas_matriz,
    )
    assert terreno.PROVEEDORES == (
        terreno.PROVEEDORES_AGENDA + terreno.PROVEEDORES_RUTAS
    )
    assert ciclo.PROVEEDORES == (ciclo.medir_ciclos_sinteticos,)
