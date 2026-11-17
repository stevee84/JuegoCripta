import copy
import json

import pytest

from benchmarks.extraer_resultados_terreno_cazador_integrante1 import (
    ALTERNATIVAS_POR_MEDICION,
    EvidenciaInvalida,
    extraer_informe,
    main,
)


FIXTURE = "tests/fixtures/benchmarks/main_bench_t050_minimo.json"


@pytest.fixture
def informe_minimo():
    with open(FIXTURE, encoding="utf-8") as archivo:
        return json.load(archivo)


def test_extrae_fixture_sin_transformar_filas_o_metadatos(informe_minimo):
    originales = informe_minimo["mediciones"][1:]

    resultado, grupos = extraer_informe(informe_minimo, exigir_cobertura=False)

    assert resultado["entorno"] == informe_minimo["entorno"]
    assert resultado["tamanos"] == [8, 16, 32, 64, 128, 512]
    assert resultado["mediciones"] == originales
    assert grupos == {"mapa": 1, "agenda": 2, "rutas": 1, "ciclo": 1}
    assert resultado["mediciones"][0]["memoria"] == originales[0]["memoria"]
    assert resultado["mediciones"][-1]["muestras"] == originales[-1]["muestras"]


def _fila(nombre, alternativa):
    fila = {
        "medicion": nombre,
        "alternativa": alternativa,
        "n": 32,
        "carga": {"salas": 32, "variante": nombre},
        "semilla": 2609,
        "entorno": {"reloj": "perf_counter_ns"},
        "calentamiento": 1,
        "repeticiones": 1,
        "unidad": "ns_por_lote",
        "mediana": 1,
        "p95": 1,
        "maximo": 1,
        "minimo": 1,
        "muestras": [1],
        "trabajo": {"operaciones": 1},
    }
    if nombre.startswith("rutas_") or nombre == "ciclo_real_intervalo":
        fila["escenario"] = f"fixture-{nombre}"
    if nombre == "ciclo_real_intervalo":
        fila.update({
            "unidad": "ns_por_intervalo",
            "muestras": [{"duracion_ns": 1}],
            "origen_carga": "sintetico",
            "referencia_oficial": "pendiente_publicacion_g6",
            "afirma_pr001": False,
        })
    return fila


def _informe_completo():
    filas = [
        _fila(nombre, alternativa)
        for nombre, alternativas in ALTERNATIVAS_POR_MEDICION.items()
        for alternativa in sorted(alternativas)
    ]
    return {
        "entorno": {"reloj": "perf_counter_ns"},
        "tamanos": [8, 16, 32, 64, 128, 512],
        "repeticiones": 15,
        "umbrales": {"pequeno": 16, "factor": 4},
        "mediciones": filas,
    }


def test_exige_todos_los_nombres_reales_esperados():
    informe = _informe_completo()

    resultado, grupos = extraer_informe(informe)

    esperadas = sum(len(alternativas) for alternativas in ALTERNATIVAS_POR_MEDICION.values())
    assert len(resultado["mediciones"]) == esperadas
    assert all(cantidad > 0 for cantidad in grupos.values())


def test_rechaza_informe_oficial_con_cobertura_incompleta(informe_minimo):
    with pytest.raises(EvidenciaInvalida, match="Faltan mediciones esperadas"):
        extraer_informe(informe_minimo)


def test_rechaza_informe_que_perdio_una_alternativa():
    informe = _informe_completo()
    informe["mediciones"] = [
        fila for fila in informe["mediciones"]
        if not (
            fila["medicion"] == "rutas_ac014_matriz"
            and fila["alternativa"] == "inversa_compartida_reutilizada_benchmark"
        )
    ]

    with pytest.raises(EvidenciaInvalida, match="Faltan alternativas esperadas"):
        extraer_informe(informe)


def test_cli_escribe_json_filtrado_valido(tmp_path):
    entrada = tmp_path / "completo.json"
    salida = tmp_path / "filtrado.json"
    entrada.write_text(
        json.dumps(_informe_completo(), ensure_ascii=False),
        encoding="utf-8",
    )

    codigo = main(["--entrada", str(entrada), "--salida", str(salida)])

    assert codigo == 0
    guardado = json.loads(salida.read_text(encoding="utf-8"))
    esperadas = sum(len(alternativas) for alternativas in ALTERNATIVAS_POR_MEDICION.values())
    assert len(guardado["mediciones"]) == esperadas
    assert guardado["entorno"] == {"reloj": "perf_counter_ns"}


def test_rechaza_fila_logica_duplicada():
    informe = _informe_completo()
    informe["mediciones"].append(copy.deepcopy(informe["mediciones"][0]))

    with pytest.raises(EvidenciaInvalida, match="duplicada"):
        extraer_informe(informe)


def test_rechaza_perdida_de_muestras(informe_minimo):
    informe_minimo["mediciones"][1]["repeticiones"] = 2

    with pytest.raises(EvidenciaInvalida, match="conserva 1"):
        extraer_informe(informe_minimo, exigir_cobertura=False)


def test_rechaza_alternativa_ajena_a_la_medicion(informe_minimo):
    informe_minimo["mediciones"][1]["alternativa"] = "inventada"

    with pytest.raises(EvidenciaInvalida, match="Alternativa inesperada"):
        extraer_informe(informe_minimo, exigir_cobertura=False)
