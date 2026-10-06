from types import SimpleNamespace

import pytest

from benchmarks.integrante3 import (
    ejecutar, _medir_agenda_existente, _medir_ciclo_existente,
)


def test_ejecutor_incluye_agenda_y_simulacion_sin_salida_interactiva(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda *args: pytest.fail("No debe pedir entrada"))
    informe = ejecutar(repeticiones=1, tamanos=(4,))
    filas = {f["medicion"]: f for f in informe["mediciones"]}
    assert filas["agenda_extraer_eventos"]["n"] == 4
    ciclo = filas["ciclo_simulacion_demo"]
    assert ciclo["repeticiones"] == 200 and ciclo["calentamiento"] == 10
    assert ciclo["semilla"] == 7
    assert 0 <= ciclo["minimo"] <= ciclo["mediana"] <= ciclo["maximo"]
    assert 0 <= ciclo["ciclos_de_20ms_o_mas"] <= 200
    assert all(f["unidad"] == "ns_por_lote" for f in informe["mediciones"])
    assert capsys.readouterr().out == ""


def test_agenda_convierte_segundos_y_descarta_calentamiento(monkeypatch):
    tiempos = iter((0.9, 0.2, 0.3))
    llamadas = []

    def medir(cantidad):
        llamadas.append(cantidad)
        return cantidad, next(tiempos)

    monkeypatch.setattr("benchmarks.benchmark_agenda_integrante1.medir", medir)
    fila = _medir_agenda_existente(2, (4,))[0]
    assert llamadas == [4, 4, 4]
    assert fila["mediana"] == 250_000_000
    assert fila["minimo"] == 200_000_000


def test_ciclo_respeta_muestras_del_script_y_convierte_ms(monkeypatch, capsys):
    def ejecutar_script(ruta):
        assert ruta.endswith("prueba_rendimiento_sofia.py")
        print("Informe original")
        return {"mediciones": [1, 3, 5], "repeticion": 5,
                "estado": SimpleNamespace(semilla=77)}

    monkeypatch.setattr("runpy.run_path", ejecutar_script)
    fila = _medir_ciclo_existente(1, (4,))[0]
    assert fila["repeticiones"] == 3 and fila["calentamiento"] == 3
    assert fila["mediana"] == 3_000_000
    assert fila["minimo"] == 1_000_000 and fila["maximo"] == 5_000_000
    assert fila["semilla"] == 77 and fila["detalle_script"] == "Informe original"
    assert capsys.readouterr().out == ""


def test_agenda_no_acepta_lotes_incompletos(monkeypatch):
    monkeypatch.setattr("benchmarks.benchmark_agenda_integrante1.medir", lambda cantidad: (0, 0.1))
    with pytest.raises(ValueError, match="todos los eventos"):
        _medir_agenda_existente(1, (4,))
